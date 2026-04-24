from __future__ import annotations

import argparse
import json
from pathlib import Path

from civic_prm.audit import load_records, run_artifact_audit, save_audit_summary
from civic_prm.default_paths import DEFAULT_BASE_BENCHMARK_DATASET


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run artifact audit baselines for the Week 1 dataset.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_BASE_BENCHMARK_DATASET,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/audit/artifact_audit_summary.json"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = load_records(args.dataset)
    summary = run_artifact_audit(records)
    save_audit_summary(summary, args.output)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
