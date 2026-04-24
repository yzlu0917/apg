#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare ToolShift evaluation record files by transform and shift kind.")
    parser.add_argument("records", nargs="+", help="Paths to records.json files")
    args = parser.parse_args()

    for record_path in args.records:
        payload = json.loads(Path(record_path).read_text())
        if isinstance(payload, dict):
            raise ValueError("Expected a list of records, not a keyed dictionary.")
        print(f"\n== {record_path} ==")
        _print_summary(payload, "shift_kind")
        _print_summary(payload, "transform_name")


def _print_summary(records: list[dict], field: str) -> None:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        grouped[record[field]].append(record)
    print(f"-- by {field} --")
    print("bucket\tcount\tCAA\tcoverage")
    for bucket in sorted(grouped):
        bucket_records = grouped[bucket]
        caa = _mean(item["admissible"] for item in bucket_records)
        coverage = _mean(item["predicted_action"]["control"] != "abstain" for item in bucket_records)
        print(f"{bucket}\t{len(bucket_records)}\t{caa:.3f}\t{coverage:.3f}")


def _mean(values) -> float:
    items = list(values)
    if not items:
        return 0.0
    return sum(float(item) for item in items) / len(items)


if __name__ == "__main__":
    main()
