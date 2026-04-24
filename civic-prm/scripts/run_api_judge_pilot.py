from __future__ import annotations

import argparse
import json
from pathlib import Path

from civic_prm.api_judge import (
    APIJudgeClient,
    append_row,
    load_api_config,
    load_existing_rows,
    summarize_api_judge,
)
from civic_prm.audit import load_records
from civic_prm.default_paths import DEFAULT_BASE_BENCHMARK_DATASET


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run an external API judge pilot on selected quartets.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_BASE_BENCHMARK_DATASET,
    )
    parser.add_argument("--max-quartets", type=int, default=6)
    parser.add_argument(
        "--cache-output",
        type=Path,
        default=Path("artifacts/api_judge/api_judge_pilot_rows.jsonl"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("artifacts/api_judge/api_judge_pilot_summary.json"),
    )
    return parser.parse_args()


def select_quartets(records: list[dict], max_quartets: int) -> list[str]:
    by_domain: dict[str, set[str]] = {}
    for record in records:
        by_domain.setdefault(record["domain"], set()).add(record["quartet_id"])
    ordered_domains = sorted(by_domain)
    ordered_quartets = {domain: sorted(quartet_ids) for domain, quartet_ids in by_domain.items()}
    quartet_ids = []
    cursor = 0
    while len(quartet_ids) < max_quartets:
        added = False
        for domain in ordered_domains:
            domain_quartets = ordered_quartets[domain]
            if cursor < len(domain_quartets):
                quartet_ids.append(domain_quartets[cursor])
                added = True
                if len(quartet_ids) == max_quartets:
                    break
        if not added:
            break
        cursor += 1
    return quartet_ids


def main() -> None:
    args = parse_args()
    config = load_api_config()
    records = load_records(args.dataset)
    selected_quartets = select_quartets(records, args.max_quartets)
    selected_records = [record for record in records if record["quartet_id"] in selected_quartets]

    existing_rows = load_existing_rows(args.cache_output)
    done_keys = {(row["trace_id"], row["answer_visible"]) for row in existing_rows}

    client = APIJudgeClient(**config)
    for answer_visible in [True, False]:
        for record in selected_records:
            key = (record["trace_id"], answer_visible)
            if key in done_keys:
                continue
            row = client.score_record(record, answer_visible=answer_visible)
            append_row(args.cache_output, row)
            existing_rows.append(row)
            done_keys.add(key)

    summary = summarize_api_judge(existing_rows)
    summary["selected_quartets"] = selected_quartets
    summary["api_budget_note"] = {
        "num_requested_calls": len(selected_records) * 2,
        "actual_calls": summary["usage"]["num_calls"],
        "scope": "pilot only",
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "selected_quartets": selected_quartets,
                "visible": summary["visible"],
                "masked": summary["masked"],
                "usage": summary["usage"],
                "api_budget_note": summary["api_budget_note"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
