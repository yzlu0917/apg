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

from cnt_research.math.stage_a_audit import audit_stage_a_runs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit train-side vs held-out Stage A records.")
    parser.add_argument(
        "--train-records",
        type=Path,
        default=ROOT / "outputs" / "math_stage_a_20260309_run02" / "stage_a_math_records.jsonl",
    )
    parser.add_argument(
        "--heldout-records",
        type=Path,
        default=ROOT / "outputs" / "math_stage_a_20260309_run03_qwen3_4b" / "stage_a_math_records.jsonl",
    )
    parser.add_argument("--min-weighted-n", type=float, default=0.0)
    parser.add_argument("--min-original-solve", type=float, default=2.0 / 3.0)
    parser.add_argument("--max-paraphrase-gap", type=float, default=1.0 / 3.0)
    parser.add_argument("--max-swap-solve", type=float, default=1.0 / 3.0)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "outputs" / "math_stage_a_20260309_audit01",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = audit_stage_a_runs(
        train_records_path=args.train_records,
        heldout_records_path=args.heldout_records,
        output_dir=args.output_dir,
        min_weighted_n=args.min_weighted_n,
        min_original_solve=args.min_original_solve,
        max_paraphrase_gap=args.max_paraphrase_gap,
        max_swap_solve=args.max_swap_solve,
    )
    print(f"wrote {args.output_dir / 'stage_a_audit_summary.json'}")
    print(f"wrote {args.output_dir / 'stage_a_audit_records.jsonl'}")
    print(f"wrote {args.output_dir / 'stage_a_audit_kept.jsonl'}")
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
