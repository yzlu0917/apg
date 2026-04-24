#!/usr/bin/env python3
import argparse
import itertools
import json
import math
from pathlib import Path
from typing import Dict, List, Tuple

from train_state_first_progress_scorer import TIER_TO_ORDINAL


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def is_putnam_state(state_id: str) -> bool:
    return (
        state_id.startswith("putnam_")
        or "putnam" in state_id
        or "coeff_" in state_id
        or "finite_" in state_id
    )


def build_state_method_maps(result_json: Dict) -> Dict[str, Dict[str, List[Dict]]]:
    methods = {}
    for method_name, payload in result_json["methods"].items():
        by_state = {}
        for row in payload["state_rows"]:
            by_state[row["state_id"]] = row["candidates"]
        methods[method_name] = by_state
    return methods


def load_centroid_trust(path: Path) -> Dict[str, float]:
    obj = load_json(path)
    return {row["state_id"]: float(row["centroid_trust_prob"]) for row in obj["trust_prediction"]["state_rows"]}


def ndcg_from_subset(subset: List[Tuple[int, str, float]]) -> float:
    def dcg(ordinals: List[int]) -> float:
        total = 0.0
        for rank, gain in enumerate(ordinals, start=1):
            total += (2 ** gain - 1) / math.log2(rank + 1)
        return total

    pred_order = [TIER_TO_ORDINAL[tier] for _, tier, _ in sorted(subset, key=lambda x: x[2], reverse=True)]
    ideal_order = sorted([TIER_TO_ORDINAL[tier] for _, tier, _ in subset], reverse=True)
    ideal = dcg(ideal_order)
    return 1.0 if ideal == 0 else dcg(pred_order) / ideal


def subset_metrics(subset: List[Tuple[int, str, float]]) -> Dict[str, float]:
    ranked = sorted(subset, key=lambda x: x[2], reverse=True)
    tiers = [tier for _, tier, _ in ranked]
    ordinals = [TIER_TO_ORDINAL[t] for t in tiers]
    max_ordinal = max(ordinals)
    return {
        "top1_max_tier_hit": 1.0 if ordinals[0] == max_ordinal else 0.0,
        "top1_solved_hit": 1.0 if tiers[0] == "solved" else 0.0,
        "top2_max_tier_hit": 1.0 if any(o == max_ordinal for o in ordinals[:2]) else 0.0,
        "top2_solved_hit": 1.0 if any(t == "solved" for t in tiers[:2]) else 0.0,
        "ndcg": ndcg_from_subset(subset),
        "top1_ordinal": float(ordinals[0]),
        "subset_with_any_solved": 1.0 if any(t == "solved" for t in tiers) else 0.0,
    }


def aggregate_state_rows(
    state_rows: List[Dict],
    k: int,
    method_name: str,
    trust: Dict[str, float],
    split: str,
) -> Dict:
    kept_rows = []
    for row in state_rows:
        sid = row["state_id"]
        if split == "putnam" and not is_putnam_state(sid):
            continue
        if split == "easy" and is_putnam_state(sid):
            continue
        if len(row["candidates"]) < k:
            continue
        kept_rows.append(row)

    per_state = []
    for row in kept_rows:
        sid = row["state_id"]
        combos = list(itertools.combinations(row["candidates"], k))
        use_judge = method_name == "judge_only" or (
            method_name == "hybrid_hard_gate_centroid" and trust[sid] < 0.5
        )
        judge_pairs = math.comb(k, 2) if use_judge else 0.0
        sums = {
            "top1_max_tier_hit": 0.0,
            "top1_solved_hit": 0.0,
            "top2_max_tier_hit": 0.0,
            "top2_solved_hit": 0.0,
            "ndcg": 0.0,
            "top1_ordinal": 0.0,
            "subset_with_any_solved": 0.0,
        }
        for combo in combos:
            subset = [(int(c["candidate_index"]), str(c["tier"]), float(c["score"])) for c in combo]
            m = subset_metrics(subset)
            for key in sums:
                sums[key] += m[key]
        denom = len(combos)
        per_state.append(
            {
                "state_id": sid,
                "num_candidates": len(row["candidates"]),
                "num_subsets": denom,
                "mean_top1_max_tier_hit": sums["top1_max_tier_hit"] / denom,
                "mean_top1_solved_hit": sums["top1_solved_hit"] / denom,
                "mean_top2_max_tier_hit": sums["top2_max_tier_hit"] / denom,
                "mean_top2_solved_hit": sums["top2_solved_hit"] / denom,
                "mean_ndcg": sums["ndcg"] / denom,
                "mean_top1_ordinal": sums["top1_ordinal"] / denom,
                "subset_with_any_solved_rate": sums["subset_with_any_solved"] / denom,
                "mean_judge_pair_calls": judge_pairs,
            }
        )

    macro = {}
    if per_state:
        keys = [
            "mean_top1_max_tier_hit",
            "mean_top1_solved_hit",
            "mean_top2_max_tier_hit",
            "mean_top2_solved_hit",
            "mean_ndcg",
            "mean_top1_ordinal",
            "subset_with_any_solved_rate",
            "mean_judge_pair_calls",
        ]
        for key in keys:
            macro[key] = sum(r[key] for r in per_state) / len(per_state)
    else:
        for key in [
            "mean_top1_max_tier_hit",
            "mean_top1_solved_hit",
            "mean_top2_max_tier_hit",
            "mean_top2_solved_hit",
            "mean_ndcg",
            "mean_top1_ordinal",
            "subset_with_any_solved_rate",
            "mean_judge_pair_calls",
        ]:
            macro[key] = None

    return {
        "split": split,
        "k": k,
        "num_states": len(per_state),
        "state_rows": per_state,
        "macro": macro,
    }


def main():
    parser = argparse.ArgumentParser(description="State-balanced stratified budgeted reranking evaluation.")
    parser.add_argument("--result-json", required=True)
    parser.add_argument("--trust-json", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--k-values", default="3,4")
    parser.add_argument("--methods", default="latent_only,judge_only,hybrid_hard_gate_centroid")
    parser.add_argument("--splits", default="putnam,easy")
    args = parser.parse_args()

    result_json = load_json(Path(args.result_json))
    method_maps = build_state_method_maps(result_json)
    trust = load_centroid_trust(Path(args.trust_json))
    ks = [int(x) for x in args.k_values.split(",") if x]
    methods = [x for x in args.methods.split(",") if x]
    splits = [x for x in args.splits.split(",") if x]

    output = {
        "source_result_json": args.result_json,
        "trust_json": args.trust_json,
        "k_values": ks,
        "methods": {},
    }
    for method_name in methods:
        output["methods"][method_name] = {}
        state_rows = [{"state_id": sid, "candidates": cands} for sid, cands in method_maps[method_name].items()]
        for split in splits:
            output["methods"][method_name][split] = {}
            for k in ks:
                block = aggregate_state_rows(state_rows, k, method_name, trust, split)
                output["methods"][method_name][split][str(k)] = block

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    preview = {}
    for method_name, split_map in output["methods"].items():
        preview[method_name] = {}
        for split, k_map in split_map.items():
            preview[method_name][split] = {}
            for k, block in k_map.items():
                preview[method_name][split][k] = block["macro"]
    print(json.dumps({"output": str(out), "preview": preview}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
