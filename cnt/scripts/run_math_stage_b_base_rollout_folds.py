from __future__ import annotations

import argparse
import gc
import json
from pathlib import Path
import random

import torch

from cnt_research.math.countertrace_mini import DEFAULT_QWEN3_1P7B
from cnt_research.math.stage_b import build_stage_b_dataset, evaluate_stage_b_rollout


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run disjoint-fold base-rollout evaluation over the Stage B conservative core.")
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
    parser.add_argument("--num-folds", type=int, default=4)
    parser.add_argument("--fold-seed", type=int, default=17)
    parser.add_argument("--gpu", default="cuda:0")
    parser.add_argument("--continuation-max-new-tokens", type=int, default=120)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "outputs" / "math_stage_b_20260310_base_rollout_folds",
    )
    return parser.parse_args()


def _cleanup_cuda() -> None:
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def _load_unique_example_ids(audit_kept_path: Path) -> list[str]:
    example_ids: set[str] = set()
    with audit_kept_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            payload = json.loads(line)
            if payload.get("keep", True):
                example_ids.add(str(payload["example_id"]))
    return sorted(example_ids)


def _select_fold_ids(example_ids: list[str], num_folds: int, fold_index: int, fold_seed: int) -> list[str]:
    shuffled = list(example_ids)
    random.Random(fold_seed).shuffle(shuffled)
    fold_sizes = [len(shuffled) // num_folds] * num_folds
    for index in range(len(shuffled) % num_folds):
        fold_sizes[index] += 1
    start = sum(fold_sizes[:fold_index])
    end = start + fold_sizes[fold_index]
    return sorted(shuffled[start:end])


def main() -> None:
    args = parse_args()
    unique_example_ids = _load_unique_example_ids(args.audit_kept)
    root_dir = args.output_root
    root_dir.mkdir(parents=True, exist_ok=True)

    fold_summaries = []
    all_eval_ids: list[str] = []
    for fold_index in range(args.num_folds):
        eval_example_ids = _select_fold_ids(
            example_ids=unique_example_ids,
            num_folds=args.num_folds,
            fold_index=fold_index,
            fold_seed=args.fold_seed,
        )
        all_eval_ids.extend(eval_example_ids)
        fold_dir = root_dir / f"fold{fold_index:02d}"
        dataset_dir = fold_dir / "dataset"
        base_rollout_dir = fold_dir / "base_rollout"
        dataset_result = build_stage_b_dataset(
            train_records_path=args.train_records,
            audit_kept_path=args.audit_kept,
            output_dir=dataset_dir,
            eval_examples=len(eval_example_ids),
            split_seed=args.fold_seed,
            weight_source="heldout",
            completion_mode="rollout",
            pair_completion_mode="rollout",
            anchor_mode="original_rollout",
            rollout_style="locked_careful",
            success_trace_path=args.success_trace_path,
            chosen_source="success_trace",
            eval_example_ids=eval_example_ids,
        )
        base_rollout = evaluate_stage_b_rollout(
            train_records_path=args.train_records,
            audit_kept_path=args.audit_kept,
            dataset_summary_path=dataset_dir / "stage_b_dataset_summary.json",
            data_path=args.data_path,
            output_dir=base_rollout_dir,
            model_dir=args.model_dir,
            device=args.gpu,
            split="eval",
            continuation_max_new_tokens=args.continuation_max_new_tokens,
            styles=("locked_careful",),
        )
        fold_summaries.append(
            {
                "fold_index": fold_index,
                "eval_example_ids": dataset_result["summary"]["eval_example_ids"],
                "num_eval_examples": len(dataset_result["summary"]["eval_example_ids"]),
                "base_rollout": {
                    key: base_rollout["summary"][key]
                    for key in (
                        "mean_original_solve",
                        "mean_drop_solve",
                        "mean_paraphrase_solve",
                        "mean_swap_solve",
                        "mean_n_t",
                        "mean_n_t_weighted",
                        "mean_paraphrase_gap",
                        "positive_n_fraction",
                    )
                },
            }
        )
        _cleanup_cuda()

    summary = {
        "train_records": str(args.train_records),
        "audit_kept": str(args.audit_kept),
        "success_trace_path": str(args.success_trace_path),
        "model_dir": str(args.model_dir),
        "gpu": args.gpu,
        "num_folds": args.num_folds,
        "fold_seed": args.fold_seed,
        "continuation_max_new_tokens": args.continuation_max_new_tokens,
        "num_unique_eval_examples": len(set(all_eval_ids)),
        "all_eval_ids_disjoint": len(set(all_eval_ids)) == len(all_eval_ids),
        "folds": fold_summaries,
    }
    (root_dir / "base_rollout_folds_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"wrote {root_dir / 'base_rollout_folds_summary.json'}")


if __name__ == "__main__":
    main()
