from __future__ import annotations

import argparse
import json
from pathlib import Path

from civic_prm.generated_counterfactuals import (
    build_generated_counterfactual_dataset,
    write_rejection_log,
)
from civic_prm.generator import save_dataset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build an auditable counterfactual slice from model-generated traces."
    )
    parser.add_argument(
        "--source-dataset",
        type=Path,
        default=Path("data/generated/craft_core_hard_model_generated.jsonl"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/generated/craft_core_hard_model_generated_counterfactual.jsonl"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("artifacts/generated/model_generated_counterfactual_summary.json"),
    )
    parser.add_argument(
        "--rejections-output",
        type=Path,
        default=Path("artifacts/generated/model_generated_counterfactual_rejections.jsonl"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records, summary, rejections = build_generated_counterfactual_dataset(args.source_dataset)
    save_dataset(records, args.output)
    write_rejection_log(rejections, args.rejections_output)
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
