from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from civic_prm.api_judge import APIJudgeClient, append_row, load_api_config, load_existing_rows
from civic_prm.audit import load_records
from civic_prm.processbench_eval import compute_processbench_metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a visible vs masked API-judge pilot on ProcessBench-style records.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("data/external/processbench_eval_all.jsonl"),
    )
    parser.add_argument("--per-domain", type=int, default=12)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument(
        "--cache-output",
        type=Path,
        default=Path("artifacts/external_datasets/processbench_api_judge_rows.jsonl"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("artifacts/external_datasets/processbench_api_judge_summary.json"),
    )
    return parser.parse_args()


def select_examples(records: list[dict], per_domain: int, seed: int) -> list[dict]:
    by_domain: dict[str, list[dict]] = {}
    for record in records:
        by_domain.setdefault(record["domain"], []).append(record)
    selected: list[dict] = []
    rng = random.Random(seed)
    for domain in sorted(by_domain):
        buckets: dict[tuple[str, str], list[dict]] = {}
        for record in by_domain[domain]:
            key = (record["process_variant"], record["answer_variant"])
            buckets.setdefault(key, []).append(record)
        for rows in buckets.values():
            rows.sort(key=lambda row: row["trace_id"])
            rng.shuffle(rows)
        bucket_keys = sorted(buckets)
        domain_selected: list[dict] = []
        cursor = 0
        while len(domain_selected) < per_domain:
            added = False
            for key in bucket_keys:
                rows = buckets[key]
                if cursor < len(rows):
                    domain_selected.append(rows[cursor])
                    added = True
                    if len(domain_selected) >= per_domain:
                        break
            if not added:
                break
            cursor += 1
        selected.extend(domain_selected)
    return selected


def summarize_rows(rows: list[dict]) -> dict:
    visible_rows = [row for row in rows if row["answer_visible"]]
    masked_rows = [row for row in rows if not row["answer_visible"]]
    return {
        "visible": compute_processbench_metrics(visible_rows),
        "masked": compute_processbench_metrics(masked_rows),
        "usage": {
            "prompt_tokens": sum(row.get("usage", {}).get("prompt_tokens", 0) for row in rows),
            "completion_tokens": sum(row.get("usage", {}).get("completion_tokens", 0) for row in rows),
            "total_tokens": sum(row.get("usage", {}).get("total_tokens", 0) for row in rows),
            "num_calls": len(rows),
        },
    }


def main() -> None:
    args = parse_args()
    config = load_api_config()
    records = load_records(args.dataset)
    selected = select_examples(records, per_domain=args.per_domain, seed=args.seed)

    existing_rows = load_existing_rows(args.cache_output)
    done_keys = {(row["trace_id"], row["answer_visible"]) for row in existing_rows}

    client = APIJudgeClient(**config)
    for answer_visible in [True, False]:
        for record in selected:
            key = (record["trace_id"], answer_visible)
            if key in done_keys:
                continue
            row = client.score_record(record, answer_visible=answer_visible)
            append_row(args.cache_output, row)
            existing_rows.append(row)
            done_keys.add(key)

    summary = summarize_rows(existing_rows)
    summary["config"] = {
        "dataset": str(args.dataset),
        "per_domain": args.per_domain,
        "seed": args.seed,
        "num_selected_examples": len(selected),
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
