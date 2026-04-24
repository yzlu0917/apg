from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from civic_prm.audit import load_records
from civic_prm.baselines import compute_verifier_metrics
from civic_prm.calibration import compute_calibration_metrics
from civic_prm.default_paths import DEFAULT_BASE_BENCHMARK_DATASET
from civic_prm.downstream import compute_selection_metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a benchmark-v3-specific robustness and model-comparison summary."
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_BASE_BENCHMARK_DATASET,
    )
    parser.add_argument(
        "--baseline-artifact",
        type=Path,
        default=Path("artifacts/baselines/week2_baselines_benchmark_v3_midset.json"),
    )
    parser.add_argument(
        "--reranker-artifact",
        type=Path,
        default=Path("artifacts/week4/qwen3_reranker_8b_benchmark_v3_midset.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/benchmark_v3/benchmark_v3_robustness_summary.json"),
    )
    parser.add_argument("--attacker-top-fraction", type=float, default=0.25)
    parser.add_argument("--attacker-min-count", type=int, default=8)
    return parser.parse_args()


def _sanitize_utility(metrics: dict) -> dict:
    return {key: value for key, value in metrics.items() if key != "quartet_rows"}


def _quartet_rows(rows: list[dict]) -> list[dict]:
    return compute_selection_metrics(rows)["quartet_rows"]


def _summarize_top_roles(rows: list[dict]) -> dict:
    counter = Counter()
    for quartet_row in _quartet_rows(rows):
        role = f"{quartet_row['top_process_variant']}_{quartet_row['top_answer_variant']}"
        counter[role] += 1
    total = sum(counter.values())
    return {
        "counts": dict(counter),
        "rates": {
            key: round(value / total, 4)
            for key, value in sorted(counter.items())
        }
        if total
        else {},
    }


def _word_count(text: str) -> int:
    return len(text.split())


def _verbalizer_family(verbalizer_id: str) -> str:
    match = re.search(r"(v\d+)(?:_.*)?$", verbalizer_id)
    return match.group(1) if match else verbalizer_id


def _build_quartet_length_buckets(records: list[dict]) -> dict[str, str]:
    quartet_lengths = []
    by_quartet = defaultdict(list)
    for record in records:
        by_quartet[record["quartet_id"]].append(_word_count(record["trace_text"]))
    for quartet_id, lengths in by_quartet.items():
        quartet_lengths.append((quartet_id, sum(lengths) / len(lengths)))
    ordered = sorted(length for _, length in quartet_lengths)
    low_cut = ordered[len(ordered) // 3]
    high_cut = ordered[(2 * len(ordered)) // 3]
    buckets = {}
    for quartet_id, avg_length in quartet_lengths:
        if avg_length <= low_cut:
            bucket = "short"
        elif avg_length <= high_cut:
            bucket = "medium"
        else:
            bucket = "long"
        buckets[quartet_id] = bucket
    return buckets


def _annotate_rows(
    rows: list[dict],
    records_by_trace_id: dict[str, dict],
    quartet_length_bucket: dict[str, str],
) -> list[dict]:
    annotated = []
    for row in rows:
        record = records_by_trace_id[row["trace_id"]]
        enriched = dict(row)
        enriched["counterfactual_role"] = record["counterfactual_role"]
        enriched["verbalizer_family"] = _verbalizer_family(record["verbalizer_id"])
        enriched["length_bucket"] = quartet_length_bucket[record["quartet_id"]]
        enriched["difficulty_bucket"] = record.get("metadata", {}).get("difficulty", "unknown")
        annotated.append(enriched)
    return annotated


def _group_summary(rows: list[dict], group_key: str) -> dict[str, dict]:
    grouped = defaultdict(list)
    for row in rows:
        grouped[row[group_key]].append(row)
    summary = {}
    for key, group_rows in sorted(grouped.items(), key=lambda item: str(item[0])):
        summary[str(key)] = {
            "num_traces": len(group_rows),
            "num_quartets": len({row["quartet_id"] for row in group_rows}),
            "metrics": compute_verifier_metrics(group_rows),
            "utility": _sanitize_utility(compute_selection_metrics(group_rows)),
            "calibration": compute_calibration_metrics(group_rows),
            "top_role_distribution": _summarize_top_roles(group_rows),
        }
    return summary


def _select_top_invalid_trace_ids(rows: list[dict], top_fraction: float, min_count: int) -> list[str]:
    invalid_rows = [row for row in rows if row["gold_valid"] == 0]
    invalid_rows.sort(key=lambda row: row["score"], reverse=True)
    target_count = max(min_count, int(round(len(invalid_rows) * top_fraction)))
    target_count = min(len(invalid_rows), target_count)
    return [row["trace_id"] for row in invalid_rows[:target_count]]


def _attack_transfer_summary(target_rows: list[dict], attacker_trace_ids: list[str]) -> dict:
    target_by_trace_id = {row["trace_id"]: row for row in target_rows}
    target_by_pair = {
        (row["quartet_id"], row["answer_variant"], row["process_variant"]): row
        for row in target_rows
    }
    quartet_max = {}
    for row in target_rows:
        quartet_max[row["quartet_id"]] = max(quartet_max.get(row["quartet_id"], float("-inf")), row["score"])

    attacked_rows = [target_by_trace_id[trace_id] for trace_id in attacker_trace_ids if trace_id in target_by_trace_id]
    attacked_quartets = {row["quartet_id"] for row in attacked_rows}
    attacked_all_rows = [row for row in target_rows if row["quartet_id"] in attacked_quartets]
    if not attacked_rows:
        return {
            "num_selected_invalids": 0,
            "num_attacked_quartets": 0,
            "selected_domains": {},
            "selected_roles": {},
            "mean_target_score": 0.0,
            "pairwise_attack_win_rate": 0.0,
            "quartet_top_attack_rate": 0.0,
            "mean_margin_vs_matched_valid": 0.0,
            "attacked_quartet_utility": _sanitize_utility(compute_selection_metrics([])),
        }

    pairwise_wins = []
    quartet_top_hits = []
    margins = []
    for invalid_row in attacked_rows:
        matched_valid = target_by_pair[(invalid_row["quartet_id"], invalid_row["answer_variant"], "valid")]
        if invalid_row["score"] > matched_valid["score"]:
            pairwise_wins.append(1.0)
        elif invalid_row["score"] == matched_valid["score"]:
            pairwise_wins.append(0.5)
        else:
            pairwise_wins.append(0.0)
        quartet_top_hits.append(float(invalid_row["score"] == quartet_max[invalid_row["quartet_id"]]))
        margins.append(invalid_row["score"] - matched_valid["score"])

    utility = _sanitize_utility(compute_selection_metrics(attacked_all_rows))
    return {
        "num_selected_invalids": len(attacked_rows),
        "num_attacked_quartets": len(attacked_quartets),
        "selected_domains": dict(Counter(row["domain"] for row in attacked_rows)),
        "selected_roles": dict(Counter(row["counterfactual_role"] for row in attacked_rows)),
        "mean_target_score": round(sum(row["score"] for row in attacked_rows) / len(attacked_rows), 4),
        "pairwise_attack_win_rate": round(sum(pairwise_wins) / len(pairwise_wins), 4),
        "quartet_top_attack_rate": round(sum(quartet_top_hits) / len(quartet_top_hits), 4),
        "mean_margin_vs_matched_valid": round(sum(margins) / len(margins), 4),
        "attacked_quartet_utility": utility,
    }


def _load_rows_from_reranker_artifact(path: Path, view_name: str) -> list[dict]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    return obj["views"][view_name]["rows"]


def _load_rows_from_baseline_artifact(path: Path, name: str) -> list[dict]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    return obj["protocols"]["quartet"]["baselines"][name]["test_rows"]


def _model_summary(rows: list[dict]) -> dict:
    return {
        "metrics": compute_verifier_metrics(rows),
        "utility": _sanitize_utility(compute_selection_metrics(rows)),
        "calibration": compute_calibration_metrics(rows),
        "top_role_distribution": _summarize_top_roles(rows),
    }


def main() -> None:
    args = parse_args()

    records = load_records(args.dataset)
    by_trace = {record["trace_id"]: record for record in records}
    quartet_length = _build_quartet_length_buckets(records)

    reranker_visible = _annotate_rows(
        _load_rows_from_reranker_artifact(args.reranker_artifact, "visible"),
        by_trace,
        quartet_length,
    )
    reranker_masked = _annotate_rows(
        _load_rows_from_reranker_artifact(args.reranker_artifact, "masked"),
        by_trace,
        quartet_length,
    )

    baseline_names = ["step_only_bce", "visible_bce", "masked_bce", "pairwise_visible"]
    models = {
        "reranker8_visible": reranker_visible,
        "reranker8_masked": reranker_masked,
    }
    for model_name in baseline_names:
        models[model_name] = _annotate_rows(
            _load_rows_from_baseline_artifact(args.baseline_artifact, model_name),
            by_trace,
            quartet_length,
        )

    model_summary = {name: _model_summary(rows) for name, rows in models.items()}

    worst_group = {
        name: {
            "by_domain": _group_summary(rows, "domain"),
            "by_verbalizer_family": _group_summary(rows, "verbalizer_family"),
            "by_length_bucket": _group_summary(rows, "length_bucket"),
        }
        for name, rows in models.items()
    }

    attacker_sets = {}
    for attacker_name in ["reranker8_visible", "visible_bce", "pairwise_visible"]:
        attacker_sets[attacker_name] = _select_top_invalid_trace_ids(
            models[attacker_name],
            top_fraction=args.attacker_top_fraction,
            min_count=args.attacker_min_count,
        )
    mixed = []
    for attacker_name in ["reranker8_visible", "visible_bce", "pairwise_visible"]:
        mixed.extend(attacker_sets[attacker_name])
    attacker_sets["mixed_visible_ensemble"] = sorted(set(mixed))

    multi_attacker_transfer = {}
    for target_name in ["reranker8_masked", "reranker8_visible", "masked_bce", "visible_bce"]:
        target_summary = {}
        for attacker_name, attack_trace_ids in attacker_sets.items():
            target_summary[attacker_name] = _attack_transfer_summary(models[target_name], attack_trace_ids)
        multi_attacker_transfer[target_name] = target_summary

    output = {
        "config": {
            "dataset": str(args.dataset),
            "baseline_artifact": str(args.baseline_artifact),
            "reranker_artifact": str(args.reranker_artifact),
            "attacker_top_fraction": args.attacker_top_fraction,
            "attacker_min_count": args.attacker_min_count,
            "num_records": len(records),
            "num_quartets": len({record["quartet_id"] for record in records}),
        },
        "model_summary": model_summary,
        "worst_group": worst_group,
        "multi_attacker_transfer": multi_attacker_transfer,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "model_summary": {
                    name: {
                        "ordinary_auroc": payload["metrics"]["ordinary_auroc"],
                        "amcd": payload["metrics"]["amcd"],
                        "ass_total": payload["metrics"]["ass_total"],
                        "selection_gain_at4": payload["utility"]["selection_gain_at4"],
                        "exploitability_rate": payload["utility"]["exploitability_rate"],
                    }
                    for name, payload in model_summary.items()
                }
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
