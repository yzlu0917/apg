from __future__ import annotations

import argparse
import json
from pathlib import Path

from civic_prm.api_judge import append_row, load_api_config, load_existing_rows
from civic_prm.audit import load_records
from civic_prm.processbench_counterfactuals import (
    APIProcessBenchRepairClient,
    build_observed_record,
    build_repaired_record,
    extract_answer_span,
    save_records,
    select_invalid_correct_maskable_examples,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build answer-matched repair pairs from ProcessBench invalid-correct traces.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("data/external/processbench_eval_all.jsonl"),
    )
    parser.add_argument("--per-domain", type=int, default=5)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--min-audited-locus", type=int, default=1)
    parser.add_argument("--cache-only", action="store_true")
    parser.add_argument("--trace-id", dest="trace_ids", action="append", default=None)
    parser.add_argument(
        "--generation-cache-output",
        type=Path,
        default=Path("artifacts/external_datasets/processbench_repair_generation_rows.jsonl"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/external/processbench_repair_pilot.jsonl"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("artifacts/external_datasets/processbench_repair_pilot_summary.json"),
    )
    return parser.parse_args()


def summarize_dataset(records: list[dict]) -> dict:
    domains: dict[str, int] = {}
    repair_groups: dict[str, int] = {}
    process_variants: dict[str, int] = {}
    for record in records:
        domains[record["domain"]] = domains.get(record["domain"], 0) + 1
        repair_group = str(record.get("metadata", {}).get("repair_group", "unknown"))
        repair_groups[repair_group] = repair_groups.get(repair_group, 0) + 1
        process_variants[record["process_variant"]] = process_variants.get(record["process_variant"], 0) + 1
    return {
        "num_records": len(records),
        "domains": domains,
        "repair_groups": repair_groups,
        "process_variants": process_variants,
    }


def summarize_generation_cache(rows: list[dict]) -> dict:
    return {
        "num_generated_repairs": len(rows),
        "prompt_tokens": sum(row.get("usage", {}).get("prompt_tokens", 0) for row in rows),
        "completion_tokens": sum(row.get("usage", {}).get("completion_tokens", 0) for row in rows),
        "total_tokens": sum(row.get("usage", {}).get("total_tokens", 0) for row in rows),
    }


def main() -> None:
    args = parse_args()
    records = load_records(args.dataset)
    if args.trace_ids:
        trace_id_set = set(args.trace_ids)
        selected = [
            record
            for record in records
            if str(record["trace_id"]) in trace_id_set
            and record["process_variant"] == "invalid"
            and record["answer_variant"] == "correct"
            and extract_answer_span(record) is not None
            and int(record["audited_locus"]) >= args.min_audited_locus
        ]
    else:
        selected = [
            record
            for record in select_invalid_correct_maskable_examples(records, per_domain=args.per_domain * 4, seed=args.seed)
            if int(record["audited_locus"]) >= args.min_audited_locus
        ]
        trimmed: list[dict] = []
        by_domain: dict[str, int] = {}
        for record in selected:
            domain = str(record["domain"])
            count = by_domain.get(domain, 0)
            if count >= args.per_domain:
                continue
            trimmed.append(record)
            by_domain[domain] = count + 1
        selected = trimmed

    existing_rows = load_existing_rows(args.generation_cache_output)
    generation_by_source = {row["source_trace_id"]: row for row in existing_rows}
    client = APIProcessBenchRepairClient(**load_api_config()) if not args.cache_only else None

    failures: list[dict] = []
    if not args.cache_only:
        for record in selected:
            source_trace_id = str(record["trace_id"])
            if source_trace_id in generation_by_source:
                continue
            source_answer_span = extract_answer_span(record)
            if source_answer_span is None:
                failures.append({"trace_id": source_trace_id, "domain": record["domain"], "reason": "unmaskable_record"})
                continue
            try:
                generation = client.generate_repaired_steps(record, source_answer_span)
            except Exception as error:
                failures.append({"trace_id": source_trace_id, "domain": record["domain"], "reason": str(error)})
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
            if args.cache_only and source_trace_id not in generation_by_source:
                failures.append({"trace_id": source_trace_id, "domain": record["domain"], "reason": "missing_cached_repair"})
            continue
        observed = build_observed_record(record, source_answer_span)
        observed["metadata"] = {
            **dict(observed.get("metadata", {})),
            "repair_group": "observed",
        }
        paired_records.append(observed)
        paired_records.append(
            build_repaired_record(
                record,
                repaired_steps=[str(step) for step in generation["repaired_steps"]],
                source_answer_span=source_answer_span,
            )
        )

    save_records(paired_records, args.output)
    summary = {
        "config": {
            "dataset": str(args.dataset),
            "per_domain": args.per_domain,
            "seed": args.seed,
            "min_audited_locus": args.min_audited_locus,
            "cache_only": args.cache_only,
            "trace_ids": args.trace_ids,
        },
        "selection": {
            "num_selected_sources": len(selected),
            "num_successful_pairs": len(paired_records) // 2,
            "num_failed_sources": len(selected) - len(paired_records) // 2,
        },
        "dataset": summarize_dataset(paired_records),
        "generation_usage": summarize_generation_cache(existing_rows),
        "failures": failures,
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
