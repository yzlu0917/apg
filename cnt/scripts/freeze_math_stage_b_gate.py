from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Freeze a fixed Stage B gate manifest and derive a complementary recipe-dev pool."
    )
    parser.add_argument(
        "--strict-gate-summary",
        type=Path,
        default=ROOT / "outputs" / "math_stage_b_20260311_gsm8k_hard_slice_audit08_mixed" / "hard_slice_summary.json",
    )
    parser.add_argument(
        "--audit-kept",
        type=Path,
        default=ROOT / "outputs" / "math_stage_a_20260311_audit08_conservative_merged112" / "stage_a_audit_kept.jsonl",
    )
    parser.add_argument(
        "--week2-exit-summary",
        type=Path,
        default=ROOT / "outputs" / "math_stage_a_20260311_audit08_conservative_merged112" / "stage_a_audit_summary.json",
    )
    parser.add_argument(
        "--compare-base-rollout-root",
        type=Path,
        default=ROOT
        / "outputs"
        / "math_stage_b_20260311_gsm8k_hard_compare_signal03_merged112"
        / "hard_audit08_mixed_lc120"
        / "base_rollout",
    )
    parser.add_argument(
        "--label",
        default="audit08_strict29",
        help="Stable label for the frozen final-test gate and derived dev pool.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "outputs" / "math_stage_b_20260315_gate_bundle_audit08_strict29",
    )
    return parser.parse_args()


def _safe_mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return mean(values)


def _load_audit_means(audit_kept_path: Path) -> dict[str, dict[str, float]]:
    per_example: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: {
            "train_original": [],
            "train_drop": [],
            "train_paraphrase_gap": [],
            "train_n_t_weighted": [],
            "heldout_original": [],
            "heldout_drop": [],
            "heldout_paraphrase_gap": [],
            "heldout_n_t_weighted": [],
        }
    )
    with audit_kept_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            payload = json.loads(line)
            if not payload.get("keep", True):
                continue
            example_id = str(payload["example_id"])
            per_example[example_id]["train_original"].append(float(payload["train_scores"]["original"]))
            per_example[example_id]["train_drop"].append(float(payload["train_scores"]["drop"]))
            per_example[example_id]["train_paraphrase_gap"].append(float(payload["train_scores"]["paraphrase_gap"]))
            per_example[example_id]["train_n_t_weighted"].append(float(payload["train_scores"]["n_t_weighted"]))
            per_example[example_id]["heldout_original"].append(float(payload["heldout_scores"]["original"]))
            per_example[example_id]["heldout_drop"].append(float(payload["heldout_scores"]["drop"]))
            per_example[example_id]["heldout_paraphrase_gap"].append(float(payload["heldout_scores"]["paraphrase_gap"]))
            per_example[example_id]["heldout_n_t_weighted"].append(float(payload["heldout_scores"]["n_t_weighted"]))
    return {
        example_id: {metric: _safe_mean(values) for metric, values in metrics.items()}
        for example_id, metrics in sorted(per_example.items())
    }


def _write_filtered_audit_rows(
    *,
    source_path: Path,
    output_path: Path,
    keep_example_ids: set[str],
) -> int:
    kept = 0
    with source_path.open("r", encoding="utf-8") as src, output_path.open("w", encoding="utf-8") as dst:
        for line in src:
            payload = json.loads(line)
            if not payload.get("keep", True):
                continue
            if str(payload["example_id"]) not in keep_example_ids:
                continue
            dst.write(json.dumps(payload, ensure_ascii=True) + "\n")
            kept += 1
    return kept


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
        example_id: {metric: _safe_mean(values) for metric, values in metrics.items()}
        for example_id, metrics in sorted(per_example.items())
    }


def main() -> None:
    args = parse_args()
    gate_summary = json.loads(args.strict_gate_summary.read_text(encoding="utf-8"))
    audit_means = _load_audit_means(args.audit_kept)
    base_means = _load_base_rollout_means(Path(gate_summary["base_fold_root"]))

    gate_eval_ids = [str(example_id) for example_id in gate_summary["eval_example_ids"]]
    gate_eval_id_set = set(gate_eval_ids)
    audit_example_ids = sorted(audit_means)
    dev_example_ids = [example_id for example_id in audit_example_ids if example_id not in gate_eval_id_set]

    strict_manifest = {
        "manifest_type": "stage_b_final_test_gate",
        "label": args.label,
        "role": "final_test",
        "strict_gate_summary_path": str(args.strict_gate_summary),
        "week2_exit_summary_path": str(args.week2_exit_summary),
        "audit_kept_path": str(args.audit_kept),
        "selection_source": gate_summary["selection_source"],
        "selection_rule": gate_summary["selection_rule"],
        "solve_threshold": gate_summary["solve_threshold"],
        "selection_base_fold_root": gate_summary["base_fold_root"],
        "fixed_compare_base_rollout_root": str(args.compare_base_rollout_root),
        "num_audit_examples": gate_summary["num_audit_examples"],
        "num_gate_examples": len(gate_eval_ids),
        "eval_example_ids": gate_eval_ids,
        "guidance": [
            "Use this gate only for final-style Week 3 evaluation.",
            "Do not use these eval ids for broad recipe search or repeated dev-side sweep.",
            "If the gate definition changes, create a new manifest instead of mutating this one.",
        ],
    }

    dev_examples = []
    for example_id in dev_example_ids:
        row = {
            "example_id": example_id,
            **base_means.get(example_id, {}),
            **audit_means.get(example_id, {}),
        }
        row["min_original_across_views"] = min(
            row.get("base_original", 1.0),
            row.get("heldout_original", 1.0),
        )
        row["min_drop_across_views"] = min(
            row.get("base_drop", 1.0),
            row.get("heldout_drop", 1.0),
        )
        row["max_weighted_n_t_across_views"] = max(
            row.get("base_n_t_weighted", 0.0),
            row.get("heldout_n_t_weighted", 0.0),
        )
        dev_examples.append(row)

    dev_summary = {
        "manifest_type": "stage_b_recipe_dev_pool",
        "label": f"{args.label}_recipe_dev",
        "role": "recipe_dev",
        "derived_from_strict_gate_manifest": "strict_gate_manifest.json",
        "strict_gate_summary_path": str(args.strict_gate_summary),
        "audit_kept_path": str(args.audit_kept),
        "selection_policy": "Complement of the frozen final-test gate within the audit08 kept-example pool.",
        "ordering_rule": "sorted(example_id)",
        "num_total_audit_examples": len(audit_example_ids),
        "num_gate_examples": len(gate_eval_ids),
        "num_dev_examples": len(dev_example_ids),
        "dev_example_ids": dev_example_ids,
        "examples": dev_examples,
        "guidance": [
            "Use this pool for recipe development and ablation selection.",
            "After choosing a recipe on this dev pool, return to strict_gate_manifest.json for final confirmation.",
        ],
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    strict_path = args.output_dir / "strict_gate_manifest.json"
    dev_path = args.output_dir / "recipe_dev_slice_summary.json"
    dev_audit_path = args.output_dir / "recipe_dev_audit_kept.jsonl"
    strict_path.write_text(json.dumps(strict_manifest, indent=2), encoding="utf-8")
    dev_path.write_text(json.dumps(dev_summary, indent=2), encoding="utf-8")
    kept_rows = _write_filtered_audit_rows(
        source_path=args.audit_kept,
        output_path=dev_audit_path,
        keep_example_ids=set(dev_example_ids),
    )
    print(json.dumps({"strict_gate_manifest": strict_manifest, "recipe_dev_slice": dev_summary}, indent=2))
    print(f"wrote {strict_path}")
    print(f"wrote {dev_path}")
    print(f"wrote {dev_audit_path} with {kept_rows} rows")


if __name__ == "__main__":
    main()
