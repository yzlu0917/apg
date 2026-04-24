from __future__ import annotations

import argparse
import json
from pathlib import Path

from civic_prm.default_paths import DEFAULT_BASE_BENCHMARK_DATASET
from civic_prm.generator import export_blind_audit_sample, load_dataset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a balanced blind-audit packet from an existing dataset.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_BASE_BENCHMARK_DATASET,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/audit/blind_audit_hard_v2.md"),
    )
    parser.add_argument(
        "--answer-key-output",
        type=Path,
        default=Path("artifacts/audit/blind_audit_hard_v2_key.json"),
    )
    parser.add_argument(
        "--response-form-output",
        type=Path,
        default=Path("artifacts/audit/blind_audit_hard_v2_form.csv"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("artifacts/audit/blind_audit_hard_v2_summary.json"),
    )
    parser.add_argument("--sample-quartets", type=int, default=9)
    parser.add_argument("--seed", type=int, default=17)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = load_dataset(args.dataset)
    summary = export_blind_audit_sample(
        records,
        output_path=args.output,
        sample_quartets=args.sample_quartets,
        seed=args.seed,
        answer_key_output_path=args.answer_key_output,
        response_form_output_path=args.response_form_output,
    )
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
