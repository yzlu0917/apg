from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from civic_prm.audit import load_records
from civic_prm.deployment_eval import DeploymentAPIJudge, compute_swap_metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run external deployment-style judge on model-generated traces.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("data/generated/craft_core_hard_model_generated.jsonl"),
    )
    parser.add_argument(
        "--cache-output",
        type=Path,
        default=Path("artifacts/generated/generated_api_judge_rows.jsonl"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("artifacts/generated/generated_api_judge_summary.json"),
    )
    return parser.parse_args()


def _load_cache(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _append(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    args = parse_args()
    records = load_records(args.dataset)
    judge = DeploymentAPIJudge(
        base_url=os.environ["ARK_BASE_URL"],
        model=os.environ["ARK_MODEL_ENDPOINT"],
        api_key=os.environ["ARK_API_KEY"],
    )
    rows = _load_cache(args.cache_output)
    done = {(row["trace_id"], row["answer_visible"]) for row in rows}
    for answer_visible in [True, False]:
        for record in records:
            key = (record["trace_id"], answer_visible)
            if key in done:
                continue
            row = judge.score_record(record, answer_visible=answer_visible)
            _append(args.cache_output, row)
            rows.append(row)
            done.add(key)
    summary = {
        "visible": compute_swap_metrics([row for row in rows if row["answer_visible"]]),
        "masked": compute_swap_metrics([row for row in rows if not row["answer_visible"]]),
        "usage": {
            "prompt_tokens": sum(row.get("usage", {}).get("prompt_tokens", 0) for row in rows),
            "completion_tokens": sum(row.get("usage", {}).get("completion_tokens", 0) for row in rows),
            "total_tokens": sum(row.get("usage", {}).get("total_tokens", 0) for row in rows),
            "num_calls": len(rows),
        },
        "rows": rows,
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"visible": summary["visible"], "masked": summary["masked"], "usage": summary["usage"]}, indent=2))


if __name__ == "__main__":
    main()
