from __future__ import annotations

import argparse
import json
from pathlib import Path

from civic_prm.external_datasets import (
    get_processbench_splits,
    load_processbench_records,
    load_prm800k_records,
    save_external_dataset,
    summarize_external_dataset,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import and normalize external step-level datasets.")
    parser.add_argument("--dataset", choices=["processbench", "prm800k"], required=True)
    parser.add_argument("--split", type=str, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--streaming", action="store_true")
    parser.add_argument("--list-splits", action="store_true")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--summary-output", type=Path, default=None)
    return parser.parse_args()


def _default_output_path(dataset_name: str, split_name: str, limit: int | None) -> Path:
    suffix = f"_sample{limit}" if limit is not None else ""
    return Path(f"data/external/{dataset_name}_{split_name}{suffix}.jsonl")


def _default_summary_output_path(dataset_name: str, split_name: str, limit: int | None) -> Path:
    suffix = f"_sample{limit}" if limit is not None else ""
    return Path(f"artifacts/external_datasets/{dataset_name}_{split_name}{suffix}_summary.json")


def main() -> None:
    args = parse_args()
    split_name = args.split
    if args.dataset == "processbench":
        if args.list_splits:
            print("\n".join(get_processbench_splits()))
            return
        if split_name is None:
            split_name = "all"
        records = load_processbench_records(split_name=split_name, limit=args.limit)
    else:
        if args.list_splits:
            print("train\ntest")
            return
        if split_name is None:
            split_name = "train"
        records = load_prm800k_records(
            split_name=split_name,
            limit=args.limit,
            streaming=args.streaming or args.limit is not None,
        )

    output_path = args.output or _default_output_path(args.dataset, split_name, args.limit)
    summary_output_path = args.summary_output or _default_summary_output_path(args.dataset, split_name, args.limit)

    save_external_dataset(records, output_path)
    summary = summarize_external_dataset(records)
    summary.update(
        {
            "dataset": args.dataset,
            "split": split_name,
            "limit": args.limit,
            "output_path": str(output_path),
        }
    )
    summary_output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
