from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Select a non-ceiling GSM8K Stage B eval slice from current artifacts.")
    parser.add_argument(
        "--selection-source",
        choices=("base_and_audit", "audit_only"),
        default="base_and_audit",
        help="Use both prior base-rollout artifacts and Stage A audit, or Stage A audit alone.",
    )
    parser.add_argument(
        "--base-fold-root",
        type=Path,
        default=ROOT / "outputs" / "math_stage_b_20260310_fold_compare",
    )
    parser.add_argument(
        "--audit-kept",
        type=Path,
        default=ROOT / "outputs" / "math_stage_a_20260310_audit06_conservative" / "stage_a_audit_kept.jsonl",
    )
    parser.add_argument("--solve-threshold", type=float, default=0.999999)
    parser.add_argument(
        "--output-path",
        type=Path,
        default=ROOT / "outputs" / "math_stage_b_20260310_gsm8k_hard_slice" / "hard_slice_summary.json",
    )
    return parser.parse_args()


def _safe_mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return mean(values)


def _load_base_rollout_means(base_fold_root: Path) -> dict[str, dict[str, float]]:
    per_example: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: {"base_original": [], "base_drop": [], "base_n_t_weighted": []}
    )
    for record_path in sorted(base_fold_root.glob("fold*/base_rollout/stage_b_rollout_records.jsonl")):
        with record_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                record = json.loads(line)
                example_id = str(record["example_id"])
                per_example[example_id]["base_original"].append(float(record["scores"]["original"]))
                per_example[example_id]["base_drop"].append(float(record["scores"]["drop"]))
                per_example[example_id]["base_n_t_weighted"].append(float(record["scores"]["n_t_weighted"]))
    return {
        example_id: {
            key: _safe_mean(values)
            for key, values in metric_map.items()
        }
        for example_id, metric_map in sorted(per_example.items())
    }


def _load_audit_means(audit_kept_path: Path) -> dict[str, dict[str, float]]:
    per_example: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: {
            "heldout_original": [],
            "heldout_drop": [],
            "heldout_n_t_weighted": [],
        }
    )
    with audit_kept_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            payload = json.loads(line)
            if not payload.get("keep", True):
                continue
            example_id = str(payload["example_id"])
            per_example[example_id]["heldout_original"].append(float(payload["heldout_scores"]["original"]))
            per_example[example_id]["heldout_drop"].append(float(payload["heldout_scores"]["drop"]))
            per_example[example_id]["heldout_n_t_weighted"].append(float(payload["heldout_scores"]["n_t_weighted"]))
    return {
        example_id: {
            key: _safe_mean(values)
            for key, values in metric_map.items()
        }
        for example_id, metric_map in sorted(per_example.items())
    }


def main() -> None:
    args = parse_args()
    audit_means = _load_audit_means(args.audit_kept)
    selected_rows: list[dict[str, object]] = []
    shared_example_ids: list[str] = []
    if args.selection_source == "base_and_audit":
        base_means = _load_base_rollout_means(args.base_fold_root)
        shared_example_ids = sorted(set(base_means) & set(audit_means))
        for example_id in shared_example_ids:
            merged = {
                "example_id": example_id,
                **base_means[example_id],
                **audit_means[example_id],
            }
            reasons: list[str] = []
            if merged["base_original"] < args.solve_threshold:
                reasons.append("base_original_below_threshold")
            if merged["base_drop"] < args.solve_threshold:
                reasons.append("base_drop_below_threshold")
            if merged["heldout_original"] < args.solve_threshold:
                reasons.append("heldout_original_below_threshold")
            if merged["heldout_drop"] < args.solve_threshold:
                reasons.append("heldout_drop_below_threshold")
            if not reasons:
                continue
            merged["selection_reasons"] = reasons
            selected_rows.append(merged)
    else:
        for example_id, audit_row in sorted(audit_means.items()):
            merged = {"example_id": example_id, **audit_row}
            reasons: list[str] = []
            if merged["heldout_original"] < args.solve_threshold:
                reasons.append("heldout_original_below_threshold")
            if merged["heldout_drop"] < args.solve_threshold:
                reasons.append("heldout_drop_below_threshold")
            if not reasons:
                continue
            merged["selection_reasons"] = reasons
            selected_rows.append(merged)

    summary = {
        "selection_source": args.selection_source,
        "base_fold_root": str(args.base_fold_root),
        "audit_kept": str(args.audit_kept),
        "solve_threshold": args.solve_threshold,
        "selection_rule": (
            "Select examples whose mean base-rollout original/drop solve or mean Stage-A heldout "
            "original/drop solve falls below solve_threshold."
            if args.selection_source == "base_and_audit"
            else "Select examples whose mean Stage-A heldout original/drop solve falls below solve_threshold."
        ),
        "num_shared_examples": len(shared_example_ids) if args.selection_source == "base_and_audit" else None,
        "num_audit_examples": len(audit_means),
        "num_selected_examples": len(selected_rows),
        "eval_example_ids": [row["example_id"] for row in selected_rows],
        "examples": selected_rows,
    }
    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    args.output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"wrote {args.output_path}")


if __name__ == "__main__":
    main()
