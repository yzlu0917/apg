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


def build_state_method_maps(result_json: Dict) -> Tuple[Dict[str, Dict[str, Dict[int, float]]], Dict[str, Dict[int, str]]]:
    methods = {}
    tier_maps: Dict[str, Dict[int, str]] = {}
    for method_name, payload in result_json["methods"].items():
        by_state = {}
        for row in payload["state_rows"]:
            sid = row["state_id"]
            by_state[sid] = {int(c["candidate_index"]): float(c["score"]) for c in row["candidates"]}
            tier_maps.setdefault(sid, {int(c["candidate_index"]): str(c["tier"]) for c in row["candidates"]})
        methods[method_name] = by_state
    return methods, tier_maps


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


def evaluate_subset_metrics(
    subset: List[Tuple[int, str, float]],
) -> Dict[str, float]:
    ranked = sorted(subset, key=lambda x: x[2], reverse=True)
    tiers = [tier for _, tier, _ in ranked]
    ordinals = [TIER_TO_ORDINAL[t] for t in tiers]
    max_ordinal = max(ordinals)
    max_is_solved = any(t == "solved" for t in tiers)
    return {
        "top1_max_tier_hit": 1.0 if ordinals[0] == max_ordinal else 0.0,
        "top1_solved_hit": 1.0 if tiers[0] == "solved" else 0.0,
        "top2_max_tier_hit": 1.0 if any(o == max_ordinal for o in ordinals[:2]) else 0.0,
        "top2_solved_hit": 1.0 if any(t == "solved" for t in tiers[:2]) else 0.0,
        "ndcg": ndcg_from_subset(subset),
        "top1_ordinal": float(ordinals[0]),
        "any_solved_in_subset": 1.0 if max_is_solved else 0.0,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate budgeted k-candidate reranking from round61 scores.")
    parser.add_argument("--result-json", required=True)
    parser.add_argument("--trust-json", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--k-values", default="4,6")
    parser.add_argument(
        "--methods",
        default="baseline_index_order,latent_only,judge_only,hybrid_hard_gate_centroid",
        help="Comma-separated method names from result-json",
    )
    args = parser.parse_args()

    result_json = load_json(Path(args.result_json))
    method_maps, tier_maps = build_state_method_maps(result_json)
    centroid_trust = load_centroid_trust(Path(args.trust_json))

    ks = [int(x) for x in args.k_values.split(",") if x]
    selected_methods = [x for x in args.methods.split(",") if x]

    output = {
        "source_result_json": args.result_json,
        "trust_json": args.trust_json,
        "num_states": result_json["num_states"],
        "num_candidates": result_json["num_candidates"],
        "k_values": ks,
        "methods": {},
    }

    for k in ks:
        per_method = {}
        for method_name in selected_methods:
            totals = {
                "num_subset_rows": 0,
                "top1_max_tier_hit": 0.0,
                "top1_solved_hit": 0.0,
                "top2_max_tier_hit": 0.0,
                "top2_solved_hit": 0.0,
                "ndcg": 0.0,
                "top1_ordinal": 0.0,
                "subset_with_any_solved": 0.0,
                "judge_pair_calls": 0.0,
            }
            state_rows = []
            for state_id, score_map in method_maps[method_name].items():
                candidate_indices = sorted(score_map.keys())
                if len(candidate_indices) < k:
                    continue
                combos = list(itertools.combinations(candidate_indices, k))
                judge_pairs = math.comb(k, 2)
                use_judge = False
                if method_name == "judge_only":
                    use_judge = True
                elif method_name == "hybrid_hard_gate_centroid":
                    use_judge = centroid_trust[state_id] < 0.5

                state_acc = {
                    "state_id": state_id,
                    "num_subsets": len(combos),
                    "mean_top1_max_tier_hit": 0.0,
                    "mean_top1_solved_hit": 0.0,
                    "mean_ndcg": 0.0,
                    "mean_judge_pair_calls": float(judge_pairs if use_judge else 0.0),
                }
                for combo in combos:
                    subset = [(idx, tier_maps[state_id][idx], score_map[idx]) for idx in combo]
                    metrics = evaluate_subset_metrics(subset)
                    totals["num_subset_rows"] += 1
                    totals["top1_max_tier_hit"] += metrics["top1_max_tier_hit"]
                    totals["top1_solved_hit"] += metrics["top1_solved_hit"]
                    totals["top2_max_tier_hit"] += metrics["top2_max_tier_hit"]
                    totals["top2_solved_hit"] += metrics["top2_solved_hit"]
                    totals["ndcg"] += metrics["ndcg"]
                    totals["top1_ordinal"] += metrics["top1_ordinal"]
                    totals["subset_with_any_solved"] += metrics["any_solved_in_subset"]
                    totals["judge_pair_calls"] += judge_pairs if use_judge else 0.0

                    state_acc["mean_top1_max_tier_hit"] += metrics["top1_max_tier_hit"]
                    state_acc["mean_top1_solved_hit"] += metrics["top1_solved_hit"]
                    state_acc["mean_ndcg"] += metrics["ndcg"]

                denom = len(combos)
                state_acc["mean_top1_max_tier_hit"] /= denom
                state_acc["mean_top1_solved_hit"] /= denom
                state_acc["mean_ndcg"] /= denom
                state_rows.append(state_acc)

            denom = max(1, totals["num_subset_rows"])
            summary = {
                "k": k,
                "num_subset_rows": totals["num_subset_rows"],
                "top1_max_tier_hit_rate": totals["top1_max_tier_hit"] / denom,
                "top1_solved_hit_rate": totals["top1_solved_hit"] / denom,
                "top2_max_tier_hit_rate": totals["top2_max_tier_hit"] / denom,
                "top2_solved_hit_rate": totals["top2_solved_hit"] / denom,
                "subset_with_any_solved_rate": totals["subset_with_any_solved"] / denom,
                "mean_ndcg": totals["ndcg"] / denom,
                "mean_top1_ordinal": totals["top1_ordinal"] / denom,
                "mean_judge_pair_calls": totals["judge_pair_calls"] / denom,
                "state_rows": state_rows,
            }
            per_method[method_name] = summary

        judge_cost = per_method["judge_only"]["mean_judge_pair_calls"] if "judge_only" in per_method else None
        if judge_cost is not None and judge_cost > 0:
            for method_name, summary in per_method.items():
                summary["judge_cost_ratio_vs_judge_only"] = summary["mean_judge_pair_calls"] / judge_cost
                summary["judge_cost_saving_vs_judge_only"] = 1.0 - summary["judge_cost_ratio_vs_judge_only"]
        output["methods"][str(k)] = per_method

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    preview = {}
    for k, method_map in output["methods"].items():
        preview[k] = {
            method: {
                "top1_max_tier_hit_rate": vals["top1_max_tier_hit_rate"],
                "top1_solved_hit_rate": vals["top1_solved_hit_rate"],
                "mean_ndcg": vals["mean_ndcg"],
                "mean_judge_pair_calls": vals["mean_judge_pair_calls"],
                "judge_cost_ratio_vs_judge_only": vals.get("judge_cost_ratio_vs_judge_only"),
            }
            for method, vals in method_map.items()
        }
    print(json.dumps({"output": str(out), "preview": preview}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
