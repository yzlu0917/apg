from __future__ import annotations

import argparse
import gc
import json
from pathlib import Path
import random
import shutil

import torch

from cnt_research.math.countertrace_mini import DEFAULT_QWEN3_1P7B
from cnt_research.math.stage_b import build_stage_b_dataset, evaluate_stage_b_rollout, train_stage_b_model


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a disjoint-fold Stage B base/control/CNT comparison.")
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
    parser.add_argument("--fold-index", type=int)
    parser.add_argument("--num-folds", type=int, default=4)
    parser.add_argument("--fold-seed", type=int, default=17)
    parser.add_argument("--eval-example-ids-path", type=Path)
    parser.add_argument("--run-name")
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
    parser.add_argument("--weight-source", choices=("train", "heldout", "min"), default="train")
    parser.add_argument("--weight-field", choices=("weight_raw", "weight_normalized"), default="weight_raw")
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
    parser.add_argument("--reuse-base-rollout-from", type=Path)
    parser.set_defaults(include_drop_sft=True)
    parser.add_argument("--include-drop-sft", action="store_true", dest="include_drop_sft")
    parser.add_argument("--no-include-drop-sft", action="store_false", dest="include_drop_sft")
    parser.add_argument("--max-length", type=int, default=1536)
    parser.add_argument("--continuation-max-new-tokens", type=int, default=120)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "outputs" / "math_stage_b_20260310_fold_compare",
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


def _load_unique_example_ids(audit_kept_path: Path) -> list[str]:
    example_ids: set[str] = set()
    with audit_kept_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            payload = json.loads(line)
            if payload.get("keep", True):
                example_ids.add(payload["example_id"])
    return sorted(example_ids)


def _select_fold_ids(example_ids: list[str], num_folds: int, fold_index: int, fold_seed: int) -> list[str]:
    if num_folds <= 1:
        raise ValueError("num_folds must be >= 2")
    if fold_index < 0 or fold_index >= num_folds:
        raise ValueError(f"fold_index must be in [0, {num_folds - 1}]")
    shuffled = list(example_ids)
    random.Random(fold_seed).shuffle(shuffled)
    fold_sizes = [len(shuffled) // num_folds] * num_folds
    for index in range(len(shuffled) % num_folds):
        fold_sizes[index] += 1
    start = sum(fold_sizes[:fold_index])
    end = start + fold_sizes[fold_index]
    return sorted(shuffled[start:end])


def _load_eval_example_ids(path: Path, valid_example_ids: list[str]) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        eval_example_ids = payload.get("eval_example_ids")
        if eval_example_ids is None:
            eval_example_ids = payload.get("dev_example_ids")
    else:
        eval_example_ids = payload
    if not isinstance(eval_example_ids, list) or not eval_example_ids:
        raise ValueError(f"Expected a non-empty eval_example_ids or dev_example_ids list in {path}")
    valid_id_set = set(valid_example_ids)
    missing = sorted(example_id for example_id in eval_example_ids if example_id not in valid_id_set)
    if missing:
        raise ValueError(f"Explicit eval ids missing from audit-kept pool: {missing[:3]}")
    return sorted(str(example_id) for example_id in eval_example_ids)


def _load_or_reuse_base_rollout(reuse_from: Path, output_dir: Path) -> dict:
    summary_path = reuse_from / "stage_b_rollout_summary.json"
    records_path = reuse_from / "stage_b_rollout_records.jsonl"
    if not summary_path.exists():
        raise FileNotFoundError(f"Missing base rollout summary at {summary_path}")
    if not records_path.exists():
        raise FileNotFoundError(f"Missing base rollout records at {records_path}")
    output_dir.mkdir(parents=True, exist_ok=True)
    if summary_path.resolve() != (output_dir / "stage_b_rollout_summary.json").resolve():
        shutil.copy2(summary_path, output_dir / "stage_b_rollout_summary.json")
    if records_path.resolve() != (output_dir / "stage_b_rollout_records.jsonl").resolve():
        shutil.copy2(records_path, output_dir / "stage_b_rollout_records.jsonl")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    return {"summary": summary}


def main() -> None:
    args = parse_args()
    unique_example_ids = _load_unique_example_ids(args.audit_kept)
    seed_offset = args.fold_index if args.fold_index is not None else 0
    if args.eval_example_ids_path is not None:
        eval_example_ids = _load_eval_example_ids(args.eval_example_ids_path, unique_example_ids)
        root_name = args.run_name or args.eval_example_ids_path.stem
        selection_mode = "explicit_eval_ids"
    else:
        if args.fold_index is None:
            raise ValueError("--fold-index is required when --eval-example-ids-path is not provided.")
        eval_example_ids = _select_fold_ids(
            example_ids=unique_example_ids,
            num_folds=args.num_folds,
            fold_index=args.fold_index,
            fold_seed=args.fold_seed,
        )
        root_name = f"fold{args.fold_index:02d}"
        selection_mode = "fold"

    root_dir = args.output_root / root_name
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
        eval_examples=len(eval_example_ids),
        split_seed=args.fold_seed,
        weight_source=args.weight_source,
        completion_mode="rollout",
        pair_completion_mode=args.pair_completion_mode,
        anchor_mode=args.anchor_mode,
        anchor_pair_mode=args.anchor_pair_mode,
        protect_mode=args.protect_mode,
        bundle_mode=args.bundle_mode,
        equiv_weight_mode=args.equiv_weight_mode,
        drop_sft_filter=args.drop_sft_filter,
        include_drop_sft=args.include_drop_sft,
        rollout_style="locked_careful",
        success_trace_path=args.success_trace_path,
        chosen_source="success_trace",
        eval_example_ids=eval_example_ids,
    )
    _cleanup_cuda()

    if args.reuse_base_rollout_from is not None:
        base_rollout = _load_or_reuse_base_rollout(args.reuse_base_rollout_from, base_eval_dir)
    else:
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
        weight_field=args.weight_field,
        pref_margin_target=args.pref_margin_target,
        pref_step_multiplier=args.pref_step_multiplier,
        pref_rollout_multiplier=args.pref_rollout_multiplier,
        pref_anchor_multiplier=args.pref_anchor_multiplier,
        max_length=args.max_length,
        generation_max_new_tokens=48,
        seed=args.fold_seed + seed_offset,
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
        weight_field=args.weight_field,
        pref_margin_target=args.pref_margin_target,
        pref_step_multiplier=args.pref_step_multiplier,
        pref_rollout_multiplier=args.pref_rollout_multiplier,
        pref_anchor_multiplier=args.pref_anchor_multiplier,
        max_length=args.max_length,
        generation_max_new_tokens=48,
        seed=args.fold_seed + seed_offset,
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
        "fold_index": args.fold_index,
        "num_folds": args.num_folds,
        "fold_seed": args.fold_seed,
        "selection_mode": selection_mode,
        "run_name": root_name,
        "eval_example_ids_path": str(args.eval_example_ids_path) if args.eval_example_ids_path is not None else None,
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
            "weight_source": args.weight_source,
            "weight_field": args.weight_field,
            "pair_completion_mode": args.pair_completion_mode,
            "anchor_mode": args.anchor_mode,
            "anchor_pair_mode": args.anchor_pair_mode,
            "protect_mode": args.protect_mode,
            "bundle_mode": args.bundle_mode,
            "equiv_weight_mode": args.equiv_weight_mode,
            "drop_sft_filter": args.drop_sft_filter,
            "reuse_base_rollout_from": str(args.reuse_base_rollout_from) if args.reuse_base_rollout_from else None,
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
