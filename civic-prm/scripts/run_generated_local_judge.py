from __future__ import annotations

import argparse
import json
from pathlib import Path

from civic_prm.audit import load_records
from civic_prm.deployment_eval import compute_swap_metrics, load_local_judge, score_local_record


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local deployment-style judge on model-generated traces.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("data/generated/craft_core_hard_model_generated.jsonl"),
    )
    parser.add_argument(
        "--model-root",
        type=Path,
        default=Path("/cephfs/shared/hf_cache/hub/models--Qwen--Qwen3-1.7B/snapshots"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/generated/generated_local_judge.json"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = load_records(args.dataset)
    tokenizer, model = load_local_judge(args.model_root)
    rows = []
    for answer_visible in [True, False]:
        for record in records:
            rows.append(score_local_record(tokenizer, model, record, answer_visible=answer_visible))
    summary = {
        "visible": compute_swap_metrics([row for row in rows if row["answer_visible"]]),
        "masked": compute_swap_metrics([row for row in rows if not row["answer_visible"]]),
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"visible": summary["visible"], "masked": summary["masked"]}, indent=2))


if __name__ == "__main__":
    main()
