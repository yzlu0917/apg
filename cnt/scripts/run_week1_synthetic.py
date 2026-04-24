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

from cnt_research.synthetic.benchmark import run_synthetic_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the CNT Week-1 synthetic benchmark.")
    parser.add_argument("--num-instances", type=int, default=48)
    parser.add_argument("--sigma", type=float, default=0.35)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "week1")
    args = parser.parse_args()

    result = run_synthetic_benchmark(num_instances=args.num_instances, sigma=args.sigma)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.output_dir / "synthetic_summary.json"
    rows_path = args.output_dir / "synthetic_rows.jsonl"
    summary_path.write_text(json.dumps(result["summary"], indent=2, ensure_ascii=True) + "\n")
    with rows_path.open("w", encoding="utf-8") as handle:
        for row in result["rows"]:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")
    print(f"wrote {summary_path}")
    print(f"wrote {rows_path}")
    print(json.dumps(result["summary"], indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
