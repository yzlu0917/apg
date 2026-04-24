from __future__ import annotations

import argparse
import json
from pathlib import Path

from cnt_research.math.countertrace_mini import DEFAULT_QWEN3_1P7B
from cnt_research.math.stage_b import evaluate_stage_b_rollout


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a Stage B model by rerunning Stage A-style continuations on the kept prefixes.")
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
        "--dataset-summary",
        type=Path,
        default=ROOT / "outputs" / "math_stage_b_20260310_dataset01" / "stage_b_dataset_summary.json",
    )
    parser.add_argument(
        "--data-path",
        type=Path,
        default=ROOT / "data" / "gsm8k" / "test.jsonl",
    )
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_QWEN3_1P7B)
    parser.add_argument("--gpu", default="cuda:0")
    parser.add_argument("--split", choices=("train", "eval", "all"), default="eval")
    parser.add_argument("--continuation-max-new-tokens", type=int, default=220)
    parser.add_argument("--styles", nargs="+", default=None)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "outputs" / "math_stage_b_20260310_rollout_eval_base",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = evaluate_stage_b_rollout(
        train_records_path=args.train_records,
        audit_kept_path=args.audit_kept,
        dataset_summary_path=args.dataset_summary,
        data_path=args.data_path,
        output_dir=args.output_dir,
        model_dir=args.model_dir,
        device=args.gpu,
        split=args.split,
        continuation_max_new_tokens=args.continuation_max_new_tokens,
        styles=tuple(args.styles) if args.styles else None,
    )
    print(json.dumps(result["summary"], indent=2))
    print(f"wrote {args.output_dir / 'stage_b_rollout_summary.json'}")
    print(f"wrote {args.output_dir / 'stage_b_rollout_records.jsonl'}")


if __name__ == "__main__":
    main()
