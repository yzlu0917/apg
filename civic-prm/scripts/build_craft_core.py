from __future__ import annotations

import argparse
import json
from pathlib import Path

from civic_prm.generator import (
    build_week1_dataset,
    export_blind_audit_sample,
    save_dataset,
    summarize_dataset,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the Week 1 CRAFT-Core pilot dataset.")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--per-domain", type=int, default=12)
    parser.add_argument(
        "--difficulty",
        choices=["standard", "hard", "hard_blindfix", "hard_blindfix_v2", "hard_blindfix_v3", "hard_blindfix_v4"],
        default="standard",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/generated/craft_core_week1.jsonl"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("artifacts/audit/craft_core_summary.json"),
    )
    parser.add_argument(
        "--blind-audit-output",
        type=Path,
        default=Path("artifacts/audit/blind_audit_packet.md"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = build_week1_dataset(
        seed=args.seed,
        per_domain=args.per_domain,
        difficulty=args.difficulty,
    )
    save_dataset(records, args.output)
    summary = summarize_dataset(records)
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    export_blind_audit_sample(records, args.blind_audit_output)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
