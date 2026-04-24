#!/usr/bin/env python3
import argparse
import json
import os
import time
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Tuple

import requests


TIER_TO_ORDINAL = {
    "solved": 3,
    "strong_partial": 2,
    "weak_partial": 1,
    "neutral": 0,
    "uncertain": None,
}


def load_jsonl(path: Path) -> List[Dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_state_index(generated_path: Path, replayed_path: Path) -> Dict[str, Dict]:
    generated_rows = {row["state_id"]: row for row in load_jsonl(generated_path)}
    replayed_rows = {row["state_id"]: row for row in load_jsonl(replayed_path)}
    merged = {}
    for state_id, replayed in replayed_rows.items():
        generated = generated_rows[state_id]
        merged[state_id] = {
            **replayed,
            "header": generated["header"],
            "prefix_steps": generated["prefix_steps"],
        }
    return merged


def derive_gap_rows(oracle_rows: List[Dict], replay_index: Dict[str, Dict]) -> List[Dict]:
    rows = []
    for row in oracle_rows:
        state_id = row["state_id"]
        replay_row = replay_index[state_id]
        for a, b in combinations(row["candidates"], 2):
            oa = TIER_TO_ORDINAL[a["progress_tier"]]
            ob = TIER_TO_ORDINAL[b["progress_tier"]]
            if oa is None or ob is None:
                continue
            relation = "equivalent" if oa == ob else "ordered"
            better = None
            worse = None
            if oa != ob:
                better, worse = (a, b) if oa > ob else (b, a)
            rows.append(
                {
                    "state_id": state_id,
                    "theorem_id": replay_row["theorem_id"],
                    "before_goals": replay_row["before_goals"],
                    "header": replay_row["header"],
                    "relation": relation,
                    "label_gap": 1 if relation == "ordered" else 0,
                    "candidate_a_index": a["candidate_index"],
                    "candidate_b_index": b["candidate_index"],
                    "candidate_a_tier": a["progress_tier"],
                    "candidate_b_tier": b["progress_tier"],
                    "preferred_candidate_index": None if better is None else better["candidate_index"],
                    "nonpreferred_candidate_index": None if worse is None else worse["candidate_index"],
                }
            )
    return rows


def candidate_lookup(replay_row: Dict) -> Dict[int, Dict]:
    return {idx: cand for idx, cand in enumerate(replay_row["generated_candidates"])}


def make_messages(pair_row: Dict, replay_row: Dict) -> List[Dict]:
    cand_by_idx = candidate_lookup(replay_row)
    cand_a = cand_by_idx[pair_row["candidate_a_index"]]
    cand_b = cand_by_idx[pair_row["candidate_b_index"]]
    system = (
        "You are judging relative proof progress for Lean theorem proving. "
        "Both candidate tactics are already replayable in Lean. "
        "Compare only how much progress each candidate makes toward completing the proof from the shared before-state. "
        "Ignore stylistic elegance unless it clearly changes proof progress. "
        "Return only valid JSON."
    )
    payload = {
        "state_id": pair_row["state_id"],
        "theorem_id": pair_row["theorem_id"],
        "header": pair_row["header"],
        "before_goals": pair_row["before_goals"],
        "candidate_A": {
            "candidate_index": pair_row["candidate_a_index"],
            "tactic": cand_a["tactic"],
            "after_goals": cand_a["after_goals"],
        },
        "candidate_B": {
            "candidate_index": pair_row["candidate_b_index"],
            "tactic": cand_b["tactic"],
            "after_goals": cand_b["after_goals"],
        },
    }
    user = (
        "Compare candidate A and candidate B under the shared Lean before-state.\n\n"
        "Return JSON with keys:\n"
        "- choice: one of \"A\", \"B\", \"equivalent\"\n"
        "- prob_A: float in [0,1]\n"
        "- prob_B: float in [0,1]\n"
        "- prob_equivalent: float in [0,1]\n"
        "- rationale: short string\n\n"
        "The three probabilities should sum to 1.\n\n"
        f"Context:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def call_api(base_url: str, api_key: str, model: str, messages: List[Dict], temperature: float) -> Dict:
    url = base_url.rstrip("/") + "/chat/completions"
    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        },
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json()


def normalize_probs(parsed: Dict) -> Tuple[float, float, float]:
    pa = float(parsed.get("prob_A", 0.0))
    pb = float(parsed.get("prob_B", 0.0))
    pe = float(parsed.get("prob_equivalent", 0.0))
    total = pa + pb + pe
    if total <= 0:
        return 1 / 3, 1 / 3, 1 / 3
    return pa / total, pb / total, pe / total


def rankdata(values: List[float]) -> List[float]:
    order = sorted(enumerate(values), key=lambda x: x[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and order[j + 1][1] == order[i][1]:
            j += 1
        avg_rank = (i + j + 2) / 2.0
        for k in range(i, j + 1):
            ranks[order[k][0]] = avg_rank
        i = j + 1
    return ranks


def binary_auroc(labels: List[int], scores: List[float]) -> float:
    pos = [s for y, s in zip(labels, scores) if y == 1]
    neg = [s for y, s in zip(labels, scores) if y == 0]
    if not pos or not neg:
        return float("nan")
    wins = 0.0
    total = 0
    for p in pos:
        for n in neg:
            total += 1
            if p > n:
                wins += 1.0
            elif p == n:
                wins += 0.5
    return wins / total


def binary_accuracy(labels: List[int], scores: List[float], threshold: float = 0.5) -> float:
    preds = [1 if s >= threshold else 0 for s in scores]
    return sum(int(y == p) for y, p in zip(labels, preds)) / len(labels) if labels else float("nan")


def main() -> None:
    parser = argparse.ArgumentParser(description="Judge state-first pairwise progress using external API.")
    parser.add_argument("--oracle", required=True)
    parser.add_argument("--generated", required=True)
    parser.add_argument("--replayed", required=True)
    parser.add_argument("--rows-output", required=True)
    parser.add_argument("--summary-output", required=True)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--sleep-seconds", type=float, default=0.2)
    args = parser.parse_args()

    base_url = os.environ["LTV_API_BASE_URL"]
    api_key = os.environ["LTV_API_KEY"]
    model = os.environ["LTV_API_MODEL"]

    oracle_rows = load_jsonl(Path(args.oracle))
    replay_index = load_state_index(Path(args.generated), Path(args.replayed))
    pair_rows = derive_gap_rows(oracle_rows, replay_index)

    judged_rows = []
    for idx, row in enumerate(pair_rows):
        messages = make_messages(row, replay_index[row["state_id"]])
        response = call_api(base_url, api_key, model, messages, args.temperature)
        content = response["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        prob_a, prob_b, prob_eq = normalize_probs(parsed)
        preferred = row["preferred_candidate_index"]
        if preferred is None:
            direction_label = None
            direction_score = None
        else:
            direction_label = 1 if preferred == row["candidate_a_index"] else 0
            direction_score = prob_a / (prob_a + prob_b) if (prob_a + prob_b) > 0 else 0.5
        judged_rows.append(
            {
                **row,
                "judge_choice": parsed.get("choice", ""),
                "judge_prob_A": prob_a,
                "judge_prob_B": prob_b,
                "judge_prob_equivalent": prob_eq,
                "judge_gap_score": 1.0 - prob_eq,
                "direction_label": direction_label,
                "judge_direction_score": direction_score,
                "judge_rationale": parsed.get("rationale", ""),
                "api_usage": response.get("usage", {}),
            }
        )
        print(json.dumps({"idx": idx, "state_id": row["state_id"], "choice": parsed.get("choice", ""), "usage": response.get("usage", {})}, ensure_ascii=False))
        time.sleep(args.sleep_seconds)

    rows_output = Path(args.rows_output)
    rows_output.parent.mkdir(parents=True, exist_ok=True)
    with rows_output.open("w", encoding="utf-8") as f:
        for row in judged_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    gap_labels = [row["label_gap"] for row in judged_rows]
    gap_scores = [row["judge_gap_score"] for row in judged_rows]
    direction_rows = [row for row in judged_rows if row["direction_label"] is not None]
    direction_labels = [row["direction_label"] for row in direction_rows]
    direction_scores = [row["judge_direction_score"] for row in direction_rows]

    summary = {
        "oracle": args.oracle,
        "generated": args.generated,
        "replayed": args.replayed,
        "rows_output": args.rows_output,
        "model": model,
        "base_url": base_url,
        "temperature": args.temperature,
        "batch_stats": {
            "num_states": len(oracle_rows),
            "num_gap_pairs": len(judged_rows),
            "num_gap_ordered": int(sum(gap_labels)),
            "num_gap_equivalent": int(sum(1 for y in gap_labels if y == 0)),
            "num_direction_examples": len(direction_rows),
        },
        "gap_metrics": {
            "auroc": binary_auroc(gap_labels, gap_scores),
            "accuracy": binary_accuracy(gap_labels, gap_scores),
            "positive_mean_prob": sum(s for y, s in zip(gap_labels, gap_scores) if y == 1) / max(1, sum(gap_labels)),
            "negative_mean_prob": sum(s for y, s in zip(gap_labels, gap_scores) if y == 0) / max(1, sum(1 for y in gap_labels if y == 0)),
            "mean_gap": (
                (sum(s for y, s in zip(gap_labels, gap_scores) if y == 1) / max(1, sum(gap_labels)))
                - (sum(s for y, s in zip(gap_labels, gap_scores) if y == 0) / max(1, sum(1 for y in gap_labels if y == 0)))
            ),
        },
        "direction_metrics": {
            "auroc": binary_auroc(direction_labels, direction_scores),
            "accuracy": binary_accuracy(direction_labels, direction_scores),
            "positive_mean_prob": sum(s for y, s in zip(direction_labels, direction_scores) if y == 1) / max(1, sum(direction_labels)),
            "negative_mean_prob": sum(s for y, s in zip(direction_labels, direction_scores) if y == 0) / max(1, sum(1 for y in direction_labels if y == 0)),
            "mean_gap": (
                (sum(s for y, s in zip(direction_labels, direction_scores) if y == 1) / max(1, sum(direction_labels)))
                - (sum(s for y, s in zip(direction_labels, direction_scores) if y == 0) / max(1, sum(1 for y in direction_labels if y == 0)))
            ),
        },
    }

    summary_output = Path(args.summary_output)
    summary_output.parent.mkdir(parents=True, exist_ok=True)
    summary_output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
