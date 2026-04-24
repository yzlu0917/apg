#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cnt_research.math.countertrace_mini import (
    DEFAULT_QWEN3_1P7B,
    collect_countertrace_mini_math,
    download_gsm8k,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run CounterTrace-mini(math) collection on GSM8K.")
    parser.add_argument("--split", type=str, default="test")
    parser.add_argument("--max-examples", type=int, default=24)
    parser.add_argument("--target-successes", type=int, default=6)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--gpu", type=str, default="cuda:0")
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data" / "gsm8k")
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=DEFAULT_QWEN3_1P7B,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "outputs" / "countertrace_mini_math_20260309_run01",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_path = download_gsm8k(args.data_dir, split=args.split)
    result = collect_countertrace_mini_math(
        data_path=data_path,
        output_dir=args.output_dir,
        model_dir=args.model_dir,
        device=args.gpu,
        split=args.split,
        max_examples=args.max_examples,
        target_successes=args.target_successes,
        max_new_tokens=args.max_new_tokens,
        seed=args.seed,
    )
    print(f"wrote {args.output_dir / 'math_summary.json'}")
    print(f"wrote {args.output_dir / 'math_traces.jsonl'}")
    print(f"wrote {args.output_dir / 'math_success_traces.jsonl'}")
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
