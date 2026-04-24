from __future__ import annotations

import argparse
import json
from pathlib import Path

from cnt_research.math.countertrace_mini import DEFAULT_QWEN3_1P7B
from cnt_research.math.stage_b import train_stage_b_model


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the first matched Stage B CNT training pilot.")
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=ROOT / "outputs" / "math_stage_b_20260310_dataset01",
    )
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_QWEN3_1P7B)
    parser.add_argument("--gpu", default="cuda:0")
    parser.add_argument("--epochs", type=int, default=4)
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
    parser.add_argument("--weight-field", choices=("weight_raw", "weight_normalized"), default="weight_raw")
    parser.add_argument("--max-length", type=int, default=1024)
    parser.add_argument("--generation-max-new-tokens", type=int, default=48)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "outputs" / "math_stage_b_20260310_run01",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = train_stage_b_model(
        dataset_dir=args.dataset_dir,
        output_dir=args.output_dir,
        model_dir=args.model_dir,
        device=args.gpu,
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
        weight_field=args.weight_field,
        max_length=args.max_length,
        generation_max_new_tokens=args.generation_max_new_tokens,
        seed=args.seed,
    )
    print(json.dumps(summary, indent=2))
    print(f"wrote {args.output_dir / 'stage_b_training_summary.json'}")
    print(f"wrote {args.output_dir / 'train_log.jsonl'}")
    print(f"wrote {args.output_dir / 'model'}")


if __name__ == "__main__":
    main()
