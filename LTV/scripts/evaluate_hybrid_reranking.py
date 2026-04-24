#!/usr/bin/env python3
import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from extract_boundary_states_smoke import load_jsonl, resolve_layers
from train_state_first_progress_scorer import (
    TIER_TO_ORDINAL,
    apply_scorer,
    build_candidate_dataset,
    extract_candidate_states,
    fit_scorer,
    load_state_index,
)


def ndcg_at_all(ordinals: List[int], scores: List[float]) -> float:
    def dcg(items):
        total = 0.0
        for rank, gain in enumerate(items, start=1):
            total += (2 ** gain - 1) / math.log2(rank + 1)
        return total

    pred_order = [o for _, o in sorted(zip(scores, ordinals), key=lambda x: x[0], reverse=True)]
    ideal_order = sorted(ordinals, reverse=True)
    ideal = dcg(ideal_order)
    return 1.0 if ideal == 0 else dcg(pred_order) / ideal


def load_trust_probs(path: Path, key: str) -> Dict[str, float]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    return {row["state_id"]: float(row[key]) for row in obj["trust_prediction"]["state_rows"]}


def build_judge_rankings(rows: List[Dict]) -> Dict[str, Dict[int, float]]:
    by_state = defaultdict(lambda: defaultdict(float))
    counts = defaultdict(lambda: defaultdict(int))
    for row in rows:
        sid = row["state_id"]
        a = int(row["candidate_a_index"])
        b = int(row["candidate_b_index"])
        pa = float(row["judge_prob_A"]) + 0.5 * float(row["judge_prob_equivalent"])
        pb = float(row["judge_prob_B"]) + 0.5 * float(row["judge_prob_equivalent"])
        by_state[sid][a] += pa
        by_state[sid][b] += pb
        counts[sid][a] += 1
        counts[sid][b] += 1
    out = {}
    for sid, score_map in by_state.items():
        out[sid] = {idx: score_map[idx] / max(1, counts[sid][idx]) for idx in score_map}
    return out


def collect_oracle_rows(paths: List[str]) -> List[Dict]:
    rows = []
    for path in paths:
        rows.extend(load_jsonl(Path(path)))
    return rows


def collect_replay_index(generated_paths: List[str], replayed_paths: List[str]) -> Dict[str, Dict]:
    merged = {}
    for gp, rp in zip(generated_paths, replayed_paths):
        merged.update(load_state_index(Path(gp), Path(rp)))
    return merged


def score_state_rows(state_rows: List[Dict], score_getter) -> Dict:
    top1_hits = 0
    top2_hits = 0
    ndcgs = []
    mean_selected = []
    state_out = []
    for row in state_rows:
        candidates = row["candidates"]
        scored = []
        for cand in candidates:
            score = float(score_getter(row["state_id"], int(cand["candidate_index"])))
            scored.append((cand, score))
        ranked = sorted(scored, key=lambda x: x[1], reverse=True)
        ordinals = [TIER_TO_ORDINAL[c["progress_tier"]] for c, _ in ranked]
        max_ordinal = max(ordinals)
        top1_hits += int(ordinals[0] == max_ordinal)
        top2_hits += int(any(o == max_ordinal for o in ordinals[:2]))
        ndcgs.append(ndcg_at_all([TIER_TO_ORDINAL[c["progress_tier"]] for c, _ in scored], [s for _, s in scored]))
        mean_selected.append(ordinals[0])
        state_out.append(
            {
                "state_id": row["state_id"],
                "top1_candidate_index": ranked[0][0]["candidate_index"],
                "top1_tier": ranked[0][0]["progress_tier"],
                "top1_is_max_tier": ordinals[0] == max_ordinal,
                "top2_has_max_tier": any(o == max_ordinal for o in ordinals[:2]),
                "ndcg": ndcgs[-1],
                "candidates": [
                    {
                        "candidate_index": cand["candidate_index"],
                        "tier": cand["progress_tier"],
                        "score": score,
                        "tactic": cand["tactic"],
                    }
                    for cand, score in ranked
                ],
            }
        )
    return {
        "num_states": len(state_rows),
        "top1_max_tier_hit_rate": top1_hits / len(state_rows) if state_rows else None,
        "top2_max_tier_hit_rate": top2_hits / len(state_rows) if state_rows else None,
        "mean_ndcg": sum(ndcgs) / len(ndcgs) if ndcgs else None,
        "mean_top1_ordinal": sum(mean_selected) / len(mean_selected) if mean_selected else None,
        "state_rows": state_out,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate latent/judge/hybrid reranking on mixed state-first panels.")
    parser.add_argument("--easy-oracle", required=True)
    parser.add_argument("--easy-generated", required=True)
    parser.add_argument("--easy-replayed", required=True)
    parser.add_argument("--easy-judge-rows", required=True)
    parser.add_argument("--putnam-oracle", required=True)
    parser.add_argument("--putnam-generated", required=True)
    parser.add_argument("--putnam-replayed", required=True)
    parser.add_argument("--putnam-judge-rows", required=True)
    parser.add_argument("--trust-json", required=True)
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--layers", default="-1,-8,-16")
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()

    oracle_rows = collect_oracle_rows([args.easy_oracle, args.putnam_oracle])
    replay_index = collect_replay_index(
        [args.easy_generated, args.putnam_generated],
        [args.easy_replayed, args.putnam_replayed],
    )
    judge_rows = load_jsonl(Path(args.easy_judge_rows)) + load_jsonl(Path(args.putnam_judge_rows))
    judge_rankings = build_judge_rankings(judge_rows)
    linear_trust = load_trust_probs(Path(args.trust_json), "linear_trust_prob")
    centroid_trust = load_trust_probs(Path(args.trust_json), "centroid_trust_prob")

    tokenizer = AutoTokenizer.from_pretrained(args.model_path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
        low_cpu_mem_usage=True,
    )
    model.to(args.device)
    model.eval()

    requested_layers = [int(x) for x in args.layers.split(",") if x]
    resolved_layers = resolve_layers(requested_layers, int(model.config.num_hidden_layers))

    candidate_vectors = {}
    for row in oracle_rows:
        candidate_vectors[row["state_id"]] = extract_candidate_states(
            model,
            tokenizer,
            replay_index[row["state_id"]],
            resolved_layers,
            args.device,
        )
    candidates = build_candidate_dataset(oracle_rows, replay_index, candidate_vectors)
    state_ids = sorted(set(c["state_id"] for c in candidates))

    latent_rankings = {}
    for holdout in state_ids:
        train = [c for c in candidates if c["state_id"] != holdout]
        test = [c for c in candidates if c["state_id"] == holdout]
        scorer, mean, std = fit_scorer(train, "linear")
        scores = apply_scorer(scorer, mean, std, test).tolist()
        latent_rankings[holdout] = {
            int(c["candidate_index"]): float(s) for c, s in zip(test, scores)
        }

    def latent_score(state_id: str, candidate_index: int) -> float:
        return latent_rankings[state_id][candidate_index]

    def judge_score(state_id: str, candidate_index: int) -> float:
        return judge_rankings[state_id][candidate_index]

    def baseline_score(state_id: str, candidate_index: int) -> float:
        return -float(candidate_index)

    def hard_gate_score_linear(state_id: str, candidate_index: int) -> float:
        trust = linear_trust[state_id]
        return latent_score(state_id, candidate_index) if trust >= 0.5 else judge_score(state_id, candidate_index)

    def soft_gate_score_linear(state_id: str, candidate_index: int) -> float:
        trust = linear_trust[state_id]
        return trust * latent_score(state_id, candidate_index) + (1.0 - trust) * judge_score(state_id, candidate_index)

    def hard_gate_score_centroid(state_id: str, candidate_index: int) -> float:
        trust = centroid_trust[state_id]
        return latent_score(state_id, candidate_index) if trust >= 0.5 else judge_score(state_id, candidate_index)

    def soft_gate_score_centroid(state_id: str, candidate_index: int) -> float:
        trust = centroid_trust[state_id]
        return trust * latent_score(state_id, candidate_index) + (1.0 - trust) * judge_score(state_id, candidate_index)

    evaluations = {
        "baseline_index_order": score_state_rows(oracle_rows, baseline_score),
        "latent_only": score_state_rows(oracle_rows, latent_score),
        "judge_only": score_state_rows(oracle_rows, judge_score),
        "hybrid_hard_gate_linear": score_state_rows(oracle_rows, hard_gate_score_linear),
        "hybrid_soft_gate_linear": score_state_rows(oracle_rows, soft_gate_score_linear),
        "hybrid_hard_gate_centroid": score_state_rows(oracle_rows, hard_gate_score_centroid),
        "hybrid_soft_gate_centroid": score_state_rows(oracle_rows, soft_gate_score_centroid),
    }

    output = {
        "easy_oracle": args.easy_oracle,
        "putnam_oracle": args.putnam_oracle,
        "model_path": args.model_path,
        "resolved_layers": resolved_layers,
        "num_states": len(oracle_rows),
        "num_candidates": len(candidates),
        "trust_json": args.trust_json,
        "methods": evaluations,
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    preview = {
        name: {
            "top1_max_tier_hit_rate": vals["top1_max_tier_hit_rate"],
            "top2_max_tier_hit_rate": vals["top2_max_tier_hit_rate"],
            "mean_ndcg": vals["mean_ndcg"],
            "mean_top1_ordinal": vals["mean_top1_ordinal"],
        }
        for name, vals in evaluations.items()
    }
    print(json.dumps({"output": str(out), "methods": preview}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
