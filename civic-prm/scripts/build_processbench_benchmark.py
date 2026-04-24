from __future__ import annotations

import argparse
import json
from pathlib import Path

from civic_prm.processbench import (
    build_processbench_records,
    save_processbench_records,
    summarize_processbench_records,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a normalized ProcessBench evaluation dataset.")
    parser.add_argument("--split", type=str, default="all")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/external/processbench_eval_all.jsonl"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("artifacts/external_datasets/processbench_eval_all_summary.json"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = build_processbench_records(split_name=args.split, limit=args.limit)
    save_processbench_records(records, args.output)
    summary = summarize_processbench_records(records)
    summary.update(
        {
            "split": args.split,
            "limit": args.limit,
            "output_path": str(args.output),
        }
    )
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
