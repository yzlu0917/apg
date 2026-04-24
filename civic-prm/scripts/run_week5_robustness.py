from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

from civic_prm.audit import load_records
from civic_prm.baselines import compute_verifier_metrics
from civic_prm.default_paths import DEFAULT_BASE_BENCHMARK_DATASET
from civic_prm.downstream import compute_selection_metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Week 5 robustness analyses: transfer, multi-attacker transfer, and worst-group slices."
    )
    parser.add_argument(
        "--hard-dataset",
        type=Path,
        default=DEFAULT_BASE_BENCHMARK_DATASET,
    )
    parser.add_argument(
        "--structured-dataset",
        type=Path,
        default=Path("data/generated/craft_core_hard_model_generated_full_hybrid_counterfactual_v2.jsonl"),
    )
    parser.add_argument(
        "--natural-dataset",
        type=Path,
        default=Path("data/generated/craft_core_hard_model_generated_full_hybrid_counterfactual_v2_natural.jsonl"),
    )
    parser.add_argument(
        "--hard-reranker-artifact",
        type=Path,
        default=Path("artifacts/week5/qwen3_reranker_8b_hard.json"),
    )
    parser.add_argument(
        "--structured-reranker-artifact",
        type=Path,
        default=Path("artifacts/week4/qwen3_reranker_8b_full_hybrid_structured.json"),
    )
    parser.add_argument(
        "--natural-reranker-artifact",
        type=Path,
        default=Path("artifacts/week4/qwen3_reranker_8b_full_hybrid_natural.json"),
    )
    parser.add_argument(
        "--natural-baseline-artifact",
        type=Path,
        default=Path("artifacts/generated/model_generated_full_hybrid_counterfactual_v2_natural_repair_targeted_hardneg.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/week5/week5_robustness.json"),
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
        } if total else {},
    }


def _word_count(text: str) -> int:
    return len(text.split())


def _verbalizer_family(verbalizer_id: str) -> str:
    match = re.search(r"(v\d+)$", verbalizer_id)
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


def _annotate_rows(rows: list[dict], records_by_trace_id: dict[str, dict], quartet_length_bucket: dict[str, str]) -> list[dict]:
    annotated = []
    for row in rows:
        record = records_by_trace_id[row["trace_id"]]
        enriched = dict(row)
        enriched["counterfactual_role"] = record["counterfactual_role"]
        enriched["verbalizer_family"] = _verbalizer_family(record["verbalizer_id"])
        enriched["length_bucket"] = quartet_length_bucket[record["quartet_id"]]
        enriched["difficulty_bucket"] = record["metadata"].get("difficulty", "unknown")
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
            "top_role_distribution": _summarize_top_roles(group_rows),
        }
    return summary


def _select_top_invalid_trace_ids(rows: list[dict], top_fraction: float, min_count: int) -> list[str]:
    invalid_rows = [row for row in rows if row["gold_valid"] == 0]
    invalid_rows.sort(key=lambda row: row["score"], reverse=True)
    target_count = max(min_count, int(round(len(invalid_rows) * top_fraction)))
    target_count = min(len(invalid_rows), target_count)
    return [row["trace_id"] for row in invalid_rows[:target_count]]


def _transfer_slice_summary(
    hard_rows: list[dict],
    structured_rows: list[dict],
    natural_rows: list[dict],
) -> dict:
    hard_metrics = compute_verifier_metrics(hard_rows)
    hard_utility = _sanitize_utility(compute_selection_metrics(hard_rows))
    structured_metrics = compute_verifier_metrics(structured_rows)
    structured_utility = _sanitize_utility(compute_selection_metrics(structured_rows))
    natural_metrics = compute_verifier_metrics(natural_rows)
    natural_utility = _sanitize_utility(compute_selection_metrics(natural_rows))
    return {
        "hard": {
            "metrics": hard_metrics,
            "utility": hard_utility,
        },
        "structured_generated": {
            "metrics": structured_metrics,
            "utility": structured_utility,
        },
        "naturalized_generated": {
            "metrics": natural_metrics,
            "utility": natural_utility,
        },
        "drops_from_hard": {
            "structured": {
                "ordinary_auroc": round(structured_metrics["ordinary_auroc"] - hard_metrics["ordinary_auroc"], 4),
                "amcd": round(structured_metrics["amcd"] - hard_metrics["amcd"], 4),
                "ass_total": round(structured_metrics["ass_total"] - hard_metrics["ass_total"], 4),
                "selection_gain_at4": round(structured_utility["selection_gain_at4"] - hard_utility["selection_gain_at4"], 4),
                "exploitability_rate": round(structured_utility["exploitability_rate"] - hard_utility["exploitability_rate"], 4),
            },
            "naturalized": {
                "ordinary_auroc": round(natural_metrics["ordinary_auroc"] - hard_metrics["ordinary_auroc"], 4),
                "amcd": round(natural_metrics["amcd"] - hard_metrics["amcd"], 4),
                "ass_total": round(natural_metrics["ass_total"] - hard_metrics["ass_total"], 4),
                "selection_gain_at4": round(natural_utility["selection_gain_at4"] - hard_utility["selection_gain_at4"], 4),
                "exploitability_rate": round(natural_utility["exploitability_rate"] - hard_utility["exploitability_rate"], 4),
            },
        },
    }


def _attack_transfer_summary(
    target_rows: list[dict],
    attacker_trace_ids: list[str],
) -> dict:
    target_by_trace_id = {row["trace_id"]: row for row in target_rows}
    target_by_pair = {
        (row["quartet_id"], row["answer_variant"], row["process_variant"]): row
        for row in target_rows
    }
    quartet_max = {}
    for row in target_rows:
        quartet_max[row["quartet_id"]] = max(quartet_max.get(row["quartet_id"], -math.inf), row["score"])

    attacked_rows = [target_by_trace_id[trace_id] for trace_id in attacker_trace_ids]
    attacked_quartets = {row["quartet_id"] for row in attacked_rows}
    attacked_all_rows = [row for row in target_rows if row["quartet_id"] in attacked_quartets]

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


def _load_rows_from_baseline_artifact(path: Path, section: str, name: str) -> list[dict]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    return obj[section][name]["test_rows"]


def main() -> None:
    args = parse_args()

    hard_records = load_records(args.hard_dataset)
    structured_records = load_records(args.structured_dataset)
    natural_records = load_records(args.natural_dataset)

    hard_quartet_length = _build_quartet_length_buckets(hard_records)
    natural_quartet_length = _build_quartet_length_buckets(natural_records)

    hard_by_trace = {record["trace_id"]: record for record in hard_records}
    natural_by_trace = {record["trace_id"]: record for record in natural_records}
    structured_by_trace = {record["trace_id"]: record for record in structured_records}

    reranker_hard_visible = _annotate_rows(
        _load_rows_from_reranker_artifact(args.hard_reranker_artifact, "visible"),
        hard_by_trace,
        hard_quartet_length,
    )
    reranker_hard_masked = _annotate_rows(
        _load_rows_from_reranker_artifact(args.hard_reranker_artifact, "masked"),
        hard_by_trace,
        hard_quartet_length,
    )
    reranker_structured_visible = _annotate_rows(
        _load_rows_from_reranker_artifact(args.structured_reranker_artifact, "visible"),
        structured_by_trace,
        _build_quartet_length_buckets(structured_records),
    )
    reranker_structured_masked = _annotate_rows(
        _load_rows_from_reranker_artifact(args.structured_reranker_artifact, "masked"),
        structured_by_trace,
        _build_quartet_length_buckets(structured_records),
    )
    reranker_natural_visible = _annotate_rows(
        _load_rows_from_reranker_artifact(args.natural_reranker_artifact, "visible"),
        natural_by_trace,
        natural_quartet_length,
    )
    reranker_natural_masked = _annotate_rows(
        _load_rows_from_reranker_artifact(args.natural_reranker_artifact, "masked"),
        natural_by_trace,
        natural_quartet_length,
    )

    baseline_specs = {
        "visible_bce": ("baselines", "visible_bce"),
        "masked_bce": ("baselines", "masked_bce"),
        "pairwise_visible": ("baselines", "pairwise_visible"),
        "visible_cond_swap": ("repair_variants", "visible_cond_swap"),
    }
    natural_models = {
        "reranker8_visible": reranker_natural_visible,
        "reranker8_masked": reranker_natural_masked,
    }
    for model_name, (section, entry_name) in baseline_specs.items():
        natural_models[model_name] = _annotate_rows(
            _load_rows_from_baseline_artifact(args.natural_baseline_artifact, section, entry_name),
            natural_by_trace,
            natural_quartet_length,
        )

    transfer_summary = {
        "reranker8_visible": _transfer_slice_summary(
            reranker_hard_visible,
            reranker_structured_visible,
            reranker_natural_visible,
        ),
        "reranker8_masked": _transfer_slice_summary(
            reranker_hard_masked,
            reranker_structured_masked,
            reranker_natural_masked,
        ),
    }

    worst_group = {
        "hard_reranker8_visible": {
            "by_domain": _group_summary(reranker_hard_visible, "domain"),
            "by_verbalizer_family": _group_summary(reranker_hard_visible, "verbalizer_family"),
            "by_length_bucket": _group_summary(reranker_hard_visible, "length_bucket"),
        },
        "hard_reranker8_masked": {
            "by_domain": _group_summary(reranker_hard_masked, "domain"),
            "by_verbalizer_family": _group_summary(reranker_hard_masked, "verbalizer_family"),
            "by_length_bucket": _group_summary(reranker_hard_masked, "length_bucket"),
        },
        "natural_reranker8_visible": {
            "by_domain": _group_summary(reranker_natural_visible, "domain"),
            "by_length_bucket": _group_summary(reranker_natural_visible, "length_bucket"),
        },
        "natural_reranker8_masked": {
            "by_domain": _group_summary(reranker_natural_masked, "domain"),
            "by_length_bucket": _group_summary(reranker_natural_masked, "length_bucket"),
        },
    }

    attacker_sets = {}
    for attacker_name in ["reranker8_visible", "visible_bce", "pairwise_visible"]:
        attacker_sets[attacker_name] = _select_top_invalid_trace_ids(
            natural_models[attacker_name],
            top_fraction=args.attacker_top_fraction,
            min_count=args.attacker_min_count,
        )
    mixed = []
    for attacker_name in ["reranker8_visible", "visible_bce", "pairwise_visible"]:
        mixed.extend(attacker_sets[attacker_name])
    attacker_sets["mixed_visible_ensemble"] = sorted(set(mixed))
    for target_name, rows in natural_models.items():
        attacker_sets[f"self::{target_name}"] = _select_top_invalid_trace_ids(
            rows,
            top_fraction=args.attacker_top_fraction,
            min_count=args.attacker_min_count,
        )

    multi_attacker_transfer = {}
    for target_name, target_rows in natural_models.items():
        target_summary = {}
        for attacker_name, attack_trace_ids in attacker_sets.items():
            target_summary[attacker_name] = _attack_transfer_summary(target_rows, attack_trace_ids)
        multi_attacker_transfer[target_name] = target_summary

    output = {
        "config": {
            "hard_dataset": str(args.hard_dataset),
            "structured_dataset": str(args.structured_dataset),
            "natural_dataset": str(args.natural_dataset),
            "hard_reranker_artifact": str(args.hard_reranker_artifact),
            "structured_reranker_artifact": str(args.structured_reranker_artifact),
            "natural_reranker_artifact": str(args.natural_reranker_artifact),
            "natural_baseline_artifact": str(args.natural_baseline_artifact),
            "attacker_top_fraction": args.attacker_top_fraction,
            "attacker_min_count": args.attacker_min_count,
        },
        "transfer_summary": transfer_summary,
        "worst_group": worst_group,
        "multi_attacker_transfer": multi_attacker_transfer,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "transfer_summary": {
                    name: {
                        split: {
                            "ordinary_auroc": payload["metrics"]["ordinary_auroc"],
                            "amcd": payload["metrics"]["amcd"],
                            "ass_total": payload["metrics"]["ass_total"],
                            "selection_gain_at4": payload["utility"]["selection_gain_at4"],
                            "exploitability_rate": payload["utility"]["exploitability_rate"],
                        }
                        for split, payload in summary.items()
                        if split in {"hard", "structured_generated", "naturalized_generated"}
                    }
                    for name, summary in transfer_summary.items()
                }
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
