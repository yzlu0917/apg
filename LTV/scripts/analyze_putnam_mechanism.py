#!/usr/bin/env python3
import argparse
import json
import math
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Dict, List

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from evaluate_state_first_pairwise_separability import (
    TIER_TO_ORDINAL,
    extract_candidate_states,
    flatten_states,
    load_state_index,
)
from extract_boundary_states_smoke import load_jsonl, resolve_layers


def safe_mean(values: List[float]) -> float:
    return float(sum(values) / len(values)) if values else float("nan")


def safe_std(values: List[float]) -> float:
    if len(values) <= 1:
        return 0.0
    mean = safe_mean(values)
    return float((sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5)


def entropy_from_counts(counts: Counter) -> float:
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    ent = 0.0
    for value in counts.values():
        p = value / total
        ent -= p * math.log(p + 1e-12)
    return float(ent)


def whitespace_token_count(text: str) -> int:
    return len(text.split())


def tactic_family(tactic: str) -> str:
    text = tactic.strip()
    if not text:
        return ""
    token = text.split()[0]
    return token.rstrip(";")


def correct_direction_prob(row: Dict) -> float:
    score = float(row["judge_direction_score"])
    return score if int(row["direction_label"]) == 1 else 1.0 - score


def correct_gap_prob(row: Dict) -> float:
    score = float(row["judge_gap_score"])
    return score if int(row["label_gap"]) == 1 else 1.0 - score


def build_state_features(oracle_rows: List[Dict], replay_index: Dict[str, Dict], judge_rows: List[Dict]) -> Dict[str, Dict]:
    judge_by_state = defaultdict(list)
    for row in judge_rows:
        judge_by_state[row["state_id"]].append(row)

    features = {}
    for row in oracle_rows:
        state_id = row["state_id"]
        replay_row = replay_index[state_id]
        before_text = "\n".join(replay_row["before_goals"])
        before_goal_count = len(replay_row["before_goals"])

        tier_counts = Counter(c["progress_tier"] for c in row["candidates"])
        family_counts = Counter(tactic_family(c["tactic"]) for c in row["candidates"])
        ordinal_values = [TIER_TO_ORDINAL[c["progress_tier"]] for c in row["candidates"] if TIER_TO_ORDINAL[c["progress_tier"]] is not None]
        after_goal_counts = [len(c["after_goals"]) for c in replay_row["generated_candidates"] if c["replay_status"] == "ok"]
        after_goal_chars = [len("\n".join(c["after_goals"])) for c in replay_row["generated_candidates"] if c["replay_status"] == "ok"]
        after_goal_tokens = [whitespace_token_count("\n".join(c["after_goals"])) for c in replay_row["generated_candidates"] if c["replay_status"] == "ok"]

        ordered_rows = [r for r in judge_by_state[state_id] if r["relation"] == "ordered"]
        equivalent_rows = [r for r in judge_by_state[state_id] if r["relation"] == "equivalent"]
        tier_gap_counts = Counter()
        for r in ordered_rows:
            gap = abs(TIER_TO_ORDINAL[r["candidate_a_tier"]] - TIER_TO_ORDINAL[r["candidate_b_tier"]])
            tier_gap_counts[str(gap)] += 1

        features[state_id] = {
            "state_id": state_id,
            "theorem_id": replay_row["theorem_id"],
            "before_goal_chars": len(before_text),
            "before_goal_lines": len(before_text.splitlines()),
            "before_goal_tokens": whitespace_token_count(before_text),
            "before_goal_count": before_goal_count,
            "num_candidates": len(row["candidates"]),
            "num_distinct_tiers": len(tier_counts),
            "tier_counts": dict(tier_counts),
            "tier_entropy": entropy_from_counts(tier_counts),
            "tier_span": (max(ordinal_values) - min(ordinal_values)) if ordinal_values else 0,
            "has_solved_candidate": "solved" in tier_counts,
            "ordered_pairs": len(ordered_rows),
            "equivalent_pairs": len(equivalent_rows),
            "num_tactic_families": len(family_counts),
            "tactic_family_counts": dict(family_counts),
            "tactic_family_entropy": entropy_from_counts(family_counts),
            "avg_after_goal_count": safe_mean(after_goal_counts),
            "std_after_goal_count": safe_std(after_goal_counts),
            "avg_after_goal_delta_count": safe_mean([count - before_goal_count for count in after_goal_counts]),
            "avg_after_goal_chars": safe_mean(after_goal_chars),
            "std_after_goal_chars": safe_std(after_goal_chars),
            "avg_after_goal_tokens": safe_mean(after_goal_tokens),
            "std_after_goal_tokens": safe_std(after_goal_tokens),
            "judge_gap_accuracy": safe_mean([int((float(r["judge_gap_score"]) >= 0.5) == bool(r["label_gap"])) for r in judge_by_state[state_id]]),
            "judge_gap_correct_prob": safe_mean([correct_gap_prob(r) for r in judge_by_state[state_id]]),
            "judge_direction_accuracy": safe_mean([int(correct_direction_prob(r) >= 0.5) for r in ordered_rows]),
            "judge_direction_correct_prob": safe_mean([correct_direction_prob(r) for r in ordered_rows]),
            "judge_equivalent_prob": safe_mean([float(r["judge_prob_equivalent"]) for r in equivalent_rows]),
            "judge_tier_gap_counts": dict(tier_gap_counts),
        }
    return features


def ordered_diff_rows(oracle_rows: List[Dict]) -> Dict[str, List[Dict]]:
    output = defaultdict(list)
    for row in oracle_rows:
        state_id = row["state_id"]
        for a, b in combinations(row["candidates"], 2):
            oa = TIER_TO_ORDINAL[a["progress_tier"]]
            ob = TIER_TO_ORDINAL[b["progress_tier"]]
            if oa is None or ob is None or oa == ob:
                continue
            better, worse = (a, b) if oa > ob else (b, a)
            output[state_id].append(
                {
                    "better_candidate_index": better["candidate_index"],
                    "worse_candidate_index": worse["candidate_index"],
                    "tier_gap": TIER_TO_ORDINAL[better["progress_tier"]] - TIER_TO_ORDINAL[worse["progress_tier"]],
                    "better_tier": better["progress_tier"],
                    "worse_tier": worse["progress_tier"],
                }
            )
    return output


def compute_prototype_stats(oracle_rows: List[Dict], state_vectors: Dict[str, Dict[str, Dict[str, torch.Tensor]]]) -> Dict:
    pair_rows = ordered_diff_rows(oracle_rows)
    state_diff_vectors = {}
    state_prototypes = {}
    for state_id, rows in pair_rows.items():
        diffs = []
        for row in rows:
            vecs = state_vectors[state_id]
            better = flatten_states(vecs[str(row["better_candidate_index"])]["h_plus"])
            worse = flatten_states(vecs[str(row["worse_candidate_index"])]["h_plus"])
            diffs.append(better - worse)
        if diffs:
            stacked = torch.stack(diffs, dim=0)
            state_diff_vectors[state_id] = stacked
            proto = stacked.mean(dim=0)
            state_prototypes[state_id] = torch.nn.functional.normalize(proto, dim=0)

    pairwise_cosines = []
    matrix_rows = []
    state_ids = sorted(state_prototypes)
    for sid in state_ids:
        row = {"state_id": sid}
        for tid in state_ids:
            cos = float(torch.dot(state_prototypes[sid], state_prototypes[tid]).item())
            row[tid] = cos
            if sid < tid:
                pairwise_cosines.append(cos)
        matrix_rows.append(row)

    per_state = []
    for sid in state_ids:
        own_proto = state_prototypes[sid]
        own_diffs = state_diff_vectors[sid]
        own_align = torch.nn.functional.cosine_similarity(own_diffs, own_proto.unsqueeze(0), dim=1)
        other_protos = [state_prototypes[oid] for oid in state_ids if oid != sid]
        if other_protos:
            global_proto = torch.nn.functional.normalize(torch.stack(other_protos, dim=0).mean(dim=0), dim=0)
            global_align = torch.nn.functional.cosine_similarity(own_diffs, global_proto.unsqueeze(0), dim=1)
        else:
            global_proto = own_proto
            global_align = own_align
        per_state.append(
            {
                "state_id": sid,
                "num_ordered_pairs": int(own_diffs.shape[0]),
                "prototype_norm": float(torch.norm(own_diffs.mean(dim=0)).item()),
                "within_mean_cos": float(own_align.mean().item()),
                "within_min_cos": float(own_align.min().item()),
                "within_std_cos": float(own_align.std().item()) if own_align.numel() > 1 else 0.0,
                "global_mean_cos": float(global_align.mean().item()),
                "global_min_cos": float(global_align.min().item()),
                "global_std_cos": float(global_align.std().item()) if global_align.numel() > 1 else 0.0,
                "locality_gain": float((own_align.mean() - global_align.mean()).item()),
            }
        )

    return {
        "state_rows": per_state,
        "prototype_cosine_matrix": matrix_rows,
        "prototype_offdiag_mean_cos": safe_mean(pairwise_cosines),
        "prototype_offdiag_std_cos": safe_std(pairwise_cosines),
        "prototype_offdiag_min_cos": min(pairwise_cosines) if pairwise_cosines else float("nan"),
        "prototype_offdiag_max_cos": max(pairwise_cosines) if pairwise_cosines else float("nan"),
    }


def attach_locality(features: Dict[str, Dict], locality_json: Dict) -> None:
    for task_key, prefix in [("gap_task", "gap"), ("direction_task", "direction")]:
        cross = {row["state_id"]: row["linear"] for row in locality_json[task_key]["state_rows_cross"]}
        within = {row["state_id"]: row["linear"] for row in locality_json[task_key]["state_rows_within"]}
        for state_id, record in features.items():
            cross_row = cross.get(state_id, {})
            within_row = within.get(state_id, {})
            record[f"{prefix}_cross_auroc"] = cross_row.get("auroc")
            record[f"{prefix}_within_auroc"] = within_row.get("auroc")
            if cross_row.get("auroc") is None or within_row.get("auroc") is None:
                record[f"{prefix}_locality_gain"] = None
            else:
                record[f"{prefix}_locality_gain"] = within_row["auroc"] - cross_row["auroc"]


def compute_judge_global_patterns(judge_rows: List[Dict]) -> Dict:
    ordered = [r for r in judge_rows if r["relation"] == "ordered"]
    equivalent = [r for r in judge_rows if r["relation"] == "equivalent"]
    tier_gap_buckets = defaultdict(list)
    for row in ordered:
        gap = abs(TIER_TO_ORDINAL[row["candidate_a_tier"]] - TIER_TO_ORDINAL[row["candidate_b_tier"]])
        tier_gap_buckets[str(gap)].append(correct_direction_prob(row))
    return {
        "num_states": len({r["state_id"] for r in judge_rows}),
        "mean_gap_correct_prob": safe_mean([correct_gap_prob(r) for r in judge_rows]),
        "mean_direction_correct_prob": safe_mean([correct_direction_prob(r) for r in ordered]),
        "mean_equivalent_prob": safe_mean([float(r["judge_prob_equivalent"]) for r in equivalent]),
        "direction_correct_prob_by_tier_gap": {gap: safe_mean(vals) for gap, vals in sorted(tier_gap_buckets.items())},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze Putnam local latent geometry vs external judge alignment.")
    parser.add_argument("--oracle", required=True)
    parser.add_argument("--generated", required=True)
    parser.add_argument("--replayed", required=True)
    parser.add_argument("--judge-rows", required=True)
    parser.add_argument("--locality-json", required=True)
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--layers", default="-1,-8,-16")
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()

    oracle_rows = load_jsonl(Path(args.oracle))
    replay_index = load_state_index(Path(args.generated), Path(args.replayed))
    judge_rows = load_jsonl(Path(args.judge_rows))
    locality_json = json.loads(Path(args.locality_json).read_text(encoding="utf-8"))

    features = build_state_features(oracle_rows, replay_index, judge_rows)
    attach_locality(features, locality_json)

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

    state_vectors = {}
    for row in oracle_rows:
        replay_row = replay_index[row["state_id"]]
        vecs, _ = extract_candidate_states(model, tokenizer, replay_row, resolved_layers, args.device)
        state_vectors[row["state_id"]] = vecs

    prototype_stats = compute_prototype_stats(oracle_rows, state_vectors)
    for row in prototype_stats["state_rows"]:
        features[row["state_id"]].update({
            "prototype_norm": row["prototype_norm"],
            "prototype_within_mean_cos": row["within_mean_cos"],
            "prototype_global_mean_cos": row["global_mean_cos"],
            "prototype_locality_gain": row["locality_gain"],
        })

    output = {
        "oracle": args.oracle,
        "generated": args.generated,
        "replayed": args.replayed,
        "judge_rows": args.judge_rows,
        "locality_json": args.locality_json,
        "model_path": args.model_path,
        "resolved_layers": resolved_layers,
        "state_rows": [features[sid] for sid in sorted(features)],
        "judge_global_patterns": compute_judge_global_patterns(judge_rows),
        "prototype_stats": prototype_stats,
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(out),
                "num_states": len(output["state_rows"]),
                "prototype_offdiag_mean_cos": output["prototype_stats"]["prototype_offdiag_mean_cos"],
                "judge_direction_mean_correct_prob": output["judge_global_patterns"]["mean_direction_correct_prob"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
