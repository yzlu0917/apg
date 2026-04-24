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

from cnt_research.math.countertrace_mini import DEFAULT_QWEN3_1P7B
from cnt_research.math.stage_a import run_math_stage_a_pilot


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Stage A necessity pilot on CounterTrace-mini(math).")
    parser.add_argument(
        "--success-trace-path",
        type=Path,
        default=ROOT / "outputs" / "countertrace_mini_math_20260309_run01" / "math_success_traces.jsonl",
    )
    parser.add_argument("--max-traces", type=int, default=4)
    parser.add_argument("--trace-offset", type=int, default=0)
    parser.add_argument("--max-candidates-per-trace", type=int, default=3)
    parser.add_argument("--continuation-max-new-tokens", type=int, default=220)
    parser.add_argument("--edit-max-new-tokens", type=int, default=64)
    parser.add_argument("--stability-sigma", type=float, default=0.25)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--gpu", type=str, default="cuda:0")
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_QWEN3_1P7B)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "outputs" / "math_stage_a_20260309_run01",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_math_stage_a_pilot(
        success_trace_path=args.success_trace_path,
        output_dir=args.output_dir,
        model_dir=args.model_dir,
        device=args.gpu,
        max_traces=args.max_traces,
        trace_offset=args.trace_offset,
        max_candidates_per_trace=args.max_candidates_per_trace,
        continuation_max_new_tokens=args.continuation_max_new_tokens,
        edit_max_new_tokens=args.edit_max_new_tokens,
        stability_sigma=args.stability_sigma,
        resume=args.resume,
    )
    print(f"wrote {args.output_dir / 'stage_a_math_summary.json'}")
    print(f"wrote {args.output_dir / 'stage_a_math_records.jsonl'}")
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
