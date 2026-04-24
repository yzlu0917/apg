from __future__ import annotations

import argparse
import json
from pathlib import Path

from cnt_research.math.stage_b import build_stage_b_dataset


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build matched Stage B training data from the conservative audit keep-set.")
    parser.add_argument(
        "--train-records",
        type=Path,
        default=ROOT / "outputs" / "math_stage_a_20260310_filter01_conservative" / "filtered_train_records.jsonl",
    )
    parser.add_argument(
        "--audit-kept",
        type=Path,
        default=ROOT / "outputs" / "math_stage_a_20260310_audit06_conservative" / "stage_a_audit_kept.jsonl",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "outputs" / "math_stage_b_20260310_dataset01",
    )
    parser.add_argument("--eval-examples", type=int, default=4)
    parser.add_argument("--split-seed", type=int, default=17)
    parser.add_argument("--weight-source", choices=("train", "heldout", "min"), default="train")
    parser.add_argument("--completion-mode", choices=("step", "rollout"), default="step")
    parser.add_argument("--pair-completion-mode", choices=("same", "step", "rollout", "step_and_rollout"), default="same")
    parser.add_argument("--anchor-mode", choices=("none", "original_rollout"), default="none")
    parser.add_argument(
        "--anchor-pair-mode",
        choices=("none", "original_truncated_pref", "original_counterfactual_pref"),
        default="none",
    )
    parser.add_argument("--protect-mode", choices=("none", "original_over_drop_hinge"), default="none")
    parser.add_argument("--bundle-mode", choices=("none", "original_drop_paraphrase"), default="none")
    parser.add_argument("--equiv-weight-mode", choices=("match", "uniform"), default="match")
    parser.add_argument(
        "--drop-sft-filter",
        choices=("none", "one_side_positive", "both_sides_positive"),
        default="none",
    )
    parser.set_defaults(include_drop_sft=True)
    parser.add_argument("--include-drop-sft", action="store_true", dest="include_drop_sft")
    parser.add_argument("--no-include-drop-sft", action="store_false", dest="include_drop_sft")
    parser.add_argument("--rollout-style", choices=("locked", "locked_careful", "locked_minimal"), default="locked_careful")
    parser.add_argument(
        "--success-trace-path",
        type=Path,
        default=ROOT / "outputs" / "countertrace_mini_math_20260310_merged01" / "math_success_traces.jsonl",
    )
    parser.add_argument("--chosen-source", choices=("stage_a_original", "success_trace"), default="stage_a_original")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = build_stage_b_dataset(
        train_records_path=args.train_records,
        audit_kept_path=args.audit_kept,
        output_dir=args.output_dir,
        eval_examples=args.eval_examples,
        split_seed=args.split_seed,
        weight_source=args.weight_source,
        completion_mode=args.completion_mode,
        pair_completion_mode=args.pair_completion_mode,
        anchor_mode=args.anchor_mode,
        anchor_pair_mode=args.anchor_pair_mode,
        protect_mode=args.protect_mode,
        bundle_mode=args.bundle_mode,
        equiv_weight_mode=args.equiv_weight_mode,
        drop_sft_filter=args.drop_sft_filter,
        include_drop_sft=args.include_drop_sft,
        rollout_style=args.rollout_style,
        success_trace_path=args.success_trace_path,
        chosen_source=args.chosen_source,
    )
    print(json.dumps(result["summary"], indent=2))
    print(f"wrote {args.output_dir / 'train_rows.jsonl'}")
    print(f"wrote {args.output_dir / 'eval_rows.jsonl'}")
    print(f"wrote {args.output_dir / 'stage_b_dataset_summary.json'}")


if __name__ == "__main__":
    main()
