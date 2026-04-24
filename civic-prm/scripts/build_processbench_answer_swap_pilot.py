from __future__ import annotations

import argparse
import json
from pathlib import Path

from civic_prm.api_judge import append_row, load_api_config, load_existing_rows
from civic_prm.audit import load_records
from civic_prm.processbench_counterfactuals import (
    APIAnswerSwapClient,
    build_observed_record,
    build_swapped_record,
    extract_answer_span,
    save_records,
    select_maskable_examples,
    summarize_swap_dataset,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an answer-only swap pilot on ProcessBench records.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("data/external/processbench_eval_all.jsonl"),
    )
    parser.add_argument("--per-domain", type=int, default=8)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument(
        "--generation-cache-output",
        type=Path,
        default=Path("artifacts/external_datasets/processbench_answer_swap_generation_rows.jsonl"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/external/processbench_answer_swap_pilot.jsonl"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("artifacts/external_datasets/processbench_answer_swap_pilot_summary.json"),
    )
    return parser.parse_args()


def summarize_generation_cache(rows: list[dict]) -> dict:
    return {
        "num_generated_swaps": len(rows),
        "prompt_tokens": sum(row.get("usage", {}).get("prompt_tokens", 0) for row in rows),
        "completion_tokens": sum(row.get("usage", {}).get("completion_tokens", 0) for row in rows),
        "total_tokens": sum(row.get("usage", {}).get("total_tokens", 0) for row in rows),
    }


def main() -> None:
    args = parse_args()
    config = load_api_config()
    records = load_records(args.dataset)
    selected = select_maskable_examples(records, per_domain=args.per_domain, seed=args.seed)

    existing_rows = load_existing_rows(args.generation_cache_output)
    generation_by_source = {row["source_trace_id"]: row for row in existing_rows}

    client = APIAnswerSwapClient(**config)
    failures: list[dict] = []
    for record in selected:
        source_trace_id = str(record["trace_id"])
        if source_trace_id in generation_by_source:
            continue
        source_answer_span = extract_answer_span(record)
        if source_answer_span is None:
            failures.append(
                {
                    "trace_id": source_trace_id,
                    "domain": record["domain"],
                    "reason": "unmaskable_record",
                }
            )
            continue
        try:
            generation = client.generate_swapped_answer(record, source_answer_span)
        except Exception as error:
            failures.append(
                {
                    "trace_id": source_trace_id,
                    "domain": record["domain"],
                    "reason": str(error),
                }
            )
            continue
        append_row(args.generation_cache_output, generation)
        existing_rows.append(generation)
        generation_by_source[source_trace_id] = generation

    paired_records: list[dict] = []
    for record in selected:
        source_trace_id = str(record["trace_id"])
        generation = generation_by_source.get(source_trace_id)
        source_answer_span = extract_answer_span(record)
        if generation is None or source_answer_span is None:
            continue
        paired_records.append(build_observed_record(record, source_answer_span))
        paired_records.append(
            build_swapped_record(
                record,
                swapped_answer_text=str(generation["swapped_answer_span"]),
                source_answer_span=source_answer_span,
            )
        )

    save_records(paired_records, args.output)
    summary = {
        "config": {
            "dataset": str(args.dataset),
            "per_domain": args.per_domain,
            "seed": args.seed,
        },
        "selection": {
            "num_selected_sources": len(selected),
            "num_successful_pairs": len(paired_records) // 2,
            "num_failed_sources": len(selected) - len(paired_records) // 2,
        },
        "dataset": summarize_swap_dataset(paired_records),
        "generation_usage": summarize_generation_cache(existing_rows),
        "failures": failures,
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
