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

from cnt_research.math.stage_a_audit import filter_stage_a_records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply a train-side conservative filter to aligned Stage A records.")
    parser.add_argument(
        "--train-records",
        type=Path,
        default=ROOT / "outputs" / "math_stage_a_20260310_run10_swapfix_merged16" / "stage_a_math_records.jsonl",
    )
    parser.add_argument(
        "--heldout-records",
        type=Path,
        default=ROOT / "outputs" / "math_stage_a_20260310_run11_qwen3_4b_swapfix_merged16" / "stage_a_math_records.jsonl",
    )
    parser.add_argument("--train-min-original-solve", type=float, default=None)
    parser.add_argument("--train-max-paraphrase-gap", type=float, default=None)
    parser.add_argument("--train-min-weighted-n", type=float, default=None)
    parser.add_argument("--train-max-swap-solve", type=float, default=None)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "outputs" / "math_stage_a_20260310_filter01",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = filter_stage_a_records(
        train_records_path=args.train_records,
        heldout_records_path=args.heldout_records,
        output_dir=args.output_dir,
        train_min_original_solve=args.train_min_original_solve,
        train_max_paraphrase_gap=args.train_max_paraphrase_gap,
        train_min_weighted_n=args.train_min_weighted_n,
        train_max_swap_solve=args.train_max_swap_solve,
    )
    print(f"wrote {args.output_dir / 'filter_summary.json'}")
    print(f"wrote {args.output_dir / 'filtered_train_records.jsonl'}")
    print(f"wrote {args.output_dir / 'filtered_heldout_records.jsonl'}")
    print(f"wrote {args.output_dir / 'filtered_manifest.jsonl'}")
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
