from __future__ import annotations

import argparse
import gc
import json
from pathlib import Path

import torch

from cnt_research.math.countertrace_mini import DEFAULT_QWEN3_1P7B
from cnt_research.math.stage_b import build_stage_b_dataset, evaluate_stage_b_rollout, train_stage_b_model


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a base/control/CNT split comparison for Stage B.")
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
        "--success-trace-path",
        type=Path,
        default=ROOT / "outputs" / "countertrace_mini_math_20260310_merged01" / "math_success_traces.jsonl",
    )
    parser.add_argument(
        "--data-path",
        type=Path,
        default=ROOT / "data" / "gsm8k" / "test.jsonl",
    )
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_QWEN3_1P7B)
    parser.add_argument("--split-seed", type=int, required=True)
    parser.add_argument("--eval-examples", type=int, default=4)
    parser.add_argument("--train-gpu", default="cuda:0")
    parser.add_argument("--eval-gpu", default="cuda:1")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--learning-rate", type=float, default=1e-6)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--grad-accum-steps", type=int, default=4)
    parser.add_argument("--lambda-n", type=float, default=24.0)
    parser.add_argument("--lambda-inv", type=float, default=8.0)
    parser.add_argument("--lambda-protect", type=float, default=0.0)
    parser.add_argument("--lambda-bundle-rank", type=float, default=0.0)
    parser.add_argument("--lambda-bundle-equiv", type=float, default=0.0)
    parser.add_argument("--pref-margin-target", type=float, default=0.0)
    parser.add_argument("--pref-step-multiplier", type=float, default=1.0)
    parser.add_argument("--pref-rollout-multiplier", type=float, default=1.0)
    parser.add_argument("--pref-anchor-multiplier", type=float, default=1.0)
    parser.add_argument("--pair-completion-mode", choices=("same", "step", "rollout", "step_and_rollout"), default="rollout")
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
    parser.add_argument("--max-length", type=int, default=1536)
    parser.add_argument("--continuation-max-new-tokens", type=int, default=120)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "outputs" / "math_stage_b_20260310_split_compare",
    )
    return parser.parse_args()


def _cleanup_cuda() -> None:
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def _rollout_view(summary: dict) -> dict:
    return {
        "mean_original_solve": summary["mean_original_solve"],
        "mean_drop_solve": summary["mean_drop_solve"],
        "mean_paraphrase_solve": summary["mean_paraphrase_solve"],
        "mean_swap_solve": summary["mean_swap_solve"],
        "mean_n_t": summary["mean_n_t"],
        "mean_n_t_weighted": summary["mean_n_t_weighted"],
        "mean_paraphrase_gap": summary["mean_paraphrase_gap"],
        "positive_n_fraction": summary["positive_n_fraction"],
    }


def main() -> None:
    args = parse_args()
    root_dir = args.output_root / f"seed{args.split_seed:02d}"
    dataset_dir = root_dir / "dataset"
    base_eval_dir = root_dir / "base_rollout"
    control_dir = root_dir / "control_sftonly"
    control_eval_dir = root_dir / "control_rollout"
    cnt_dir = root_dir / "cnt"
    cnt_eval_dir = root_dir / "cnt_rollout"
    root_dir.mkdir(parents=True, exist_ok=True)

    dataset_result = build_stage_b_dataset(
        train_records_path=args.train_records,
        audit_kept_path=args.audit_kept,
        output_dir=dataset_dir,
        eval_examples=args.eval_examples,
        split_seed=args.split_seed,
        weight_source="train",
        completion_mode="rollout",
        pair_completion_mode=args.pair_completion_mode,
        anchor_mode=args.anchor_mode,
        anchor_pair_mode=args.anchor_pair_mode,
        protect_mode=args.protect_mode,
        bundle_mode=args.bundle_mode,
        equiv_weight_mode=args.equiv_weight_mode,
        drop_sft_filter=args.drop_sft_filter,
        rollout_style="locked_careful",
        success_trace_path=args.success_trace_path,
        chosen_source="success_trace",
    )
    _cleanup_cuda()

    base_rollout = evaluate_stage_b_rollout(
        train_records_path=args.train_records,
        audit_kept_path=args.audit_kept,
        dataset_summary_path=dataset_dir / "stage_b_dataset_summary.json",
        data_path=args.data_path,
        output_dir=base_eval_dir,
        model_dir=args.model_dir,
        device=args.eval_gpu,
        split="eval",
        continuation_max_new_tokens=args.continuation_max_new_tokens,
        styles=("locked_careful",),
    )
    _cleanup_cuda()

    control_training = train_stage_b_model(
        dataset_dir=dataset_dir,
        output_dir=control_dir,
        model_dir=args.model_dir,
        device=args.train_gpu,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        grad_accum_steps=args.grad_accum_steps,
        lambda_n=0.0,
        lambda_inv=0.0,
        lambda_protect=0.0,
        lambda_bundle_rank=0.0,
        lambda_bundle_equiv=0.0,
        pref_margin_target=args.pref_margin_target,
        pref_step_multiplier=args.pref_step_multiplier,
        pref_rollout_multiplier=args.pref_rollout_multiplier,
        pref_anchor_multiplier=args.pref_anchor_multiplier,
        weight_field="weight_raw",
        max_length=args.max_length,
        generation_max_new_tokens=48,
        seed=args.split_seed,
    )
    _cleanup_cuda()

    control_rollout = evaluate_stage_b_rollout(
        train_records_path=args.train_records,
        audit_kept_path=args.audit_kept,
        dataset_summary_path=dataset_dir / "stage_b_dataset_summary.json",
        data_path=args.data_path,
        output_dir=control_eval_dir,
        model_dir=control_dir / "model",
        device=args.eval_gpu,
        split="eval",
        continuation_max_new_tokens=args.continuation_max_new_tokens,
        styles=("locked_careful",),
    )
    _cleanup_cuda()

    cnt_training = train_stage_b_model(
        dataset_dir=dataset_dir,
        output_dir=cnt_dir,
        model_dir=args.model_dir,
        device=args.train_gpu,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        grad_accum_steps=args.grad_accum_steps,
        lambda_n=args.lambda_n,
        lambda_inv=args.lambda_inv,
        lambda_protect=args.lambda_protect,
        lambda_bundle_rank=args.lambda_bundle_rank,
        lambda_bundle_equiv=args.lambda_bundle_equiv,
        pref_margin_target=args.pref_margin_target,
        pref_step_multiplier=args.pref_step_multiplier,
        pref_rollout_multiplier=args.pref_rollout_multiplier,
        pref_anchor_multiplier=args.pref_anchor_multiplier,
        weight_field="weight_raw",
        max_length=args.max_length,
        generation_max_new_tokens=48,
        seed=args.split_seed,
    )
    _cleanup_cuda()

    cnt_rollout = evaluate_stage_b_rollout(
        train_records_path=args.train_records,
        audit_kept_path=args.audit_kept,
        dataset_summary_path=dataset_dir / "stage_b_dataset_summary.json",
        data_path=args.data_path,
        output_dir=cnt_eval_dir,
        model_dir=cnt_dir / "model",
        device=args.eval_gpu,
        split="eval",
        continuation_max_new_tokens=args.continuation_max_new_tokens,
        styles=("locked_careful",),
    )
    _cleanup_cuda()

    summary = {
        "split_seed": args.split_seed,
        "dataset_dir": str(dataset_dir),
        "eval_example_ids": dataset_result["summary"]["eval_example_ids"],
        "config": {
            "epochs": args.epochs,
            "learning_rate": args.learning_rate,
            "weight_decay": args.weight_decay,
            "grad_accum_steps": args.grad_accum_steps,
            "lambda_n": args.lambda_n,
            "lambda_inv": args.lambda_inv,
            "lambda_protect": args.lambda_protect,
            "lambda_bundle_rank": args.lambda_bundle_rank,
            "lambda_bundle_equiv": args.lambda_bundle_equiv,
            "pref_margin_target": args.pref_margin_target,
            "pref_step_multiplier": args.pref_step_multiplier,
            "pref_rollout_multiplier": args.pref_rollout_multiplier,
            "pref_anchor_multiplier": args.pref_anchor_multiplier,
            "pair_completion_mode": args.pair_completion_mode,
            "anchor_mode": args.anchor_mode,
            "anchor_pair_mode": args.anchor_pair_mode,
            "protect_mode": args.protect_mode,
            "bundle_mode": args.bundle_mode,
            "drop_sft_filter": args.drop_sft_filter,
            "max_length": args.max_length,
            "continuation_max_new_tokens": args.continuation_max_new_tokens,
        },
        "base_rollout": _rollout_view(base_rollout["summary"]),
        "control_rollout": _rollout_view(control_rollout["summary"]),
        "cnt_rollout": _rollout_view(cnt_rollout["summary"]),
        "control_after_eval": control_training["after_metrics"]["eval"],
        "cnt_after_eval": cnt_training["after_metrics"]["eval"],
    }
    summary["delta_cnt_minus_control_rollout"] = {
        key: summary["cnt_rollout"][key] - summary["control_rollout"][key]
        for key in summary["cnt_rollout"]
    }
    summary["delta_cnt_minus_control_offline"] = {
        key: summary["cnt_after_eval"][key] - summary["control_after_eval"][key]
        for key in summary["cnt_after_eval"]
        if isinstance(summary["cnt_after_eval"][key], (int, float))
    }
    (root_dir / "comparison_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"wrote {root_dir / 'comparison_summary.json'}")


if __name__ == "__main__":
    main()
