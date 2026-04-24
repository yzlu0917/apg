from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from civic_prm.audit import load_records
from civic_prm.processbench import mask_answer_surface
from civic_prm.schema import TraceExample


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a prefix-level ProcessBench benchmark.")
    parser.add_argument(
        "--source-dataset",
        type=Path,
        default=Path("data/external/processbench_eval_all.jsonl"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/external/processbench_prefix_eval_all.jsonl"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("artifacts/external_datasets/processbench_prefix_eval_all_summary.json"),
    )
    return parser.parse_args()


def build_prefix_records(source_records: list[dict]) -> list[TraceExample]:
    prefix_records: list[TraceExample] = []
    for record in source_records:
        first_incorrect_step = record["metadata"].get("first_incorrect_step")
        source_trace_id = record["trace_id"]
        for prefix_end in range(1, len(record["step_texts"]) + 1):
            prefix_steps = list(record["step_texts"][:prefix_end])
            masked_steps = [mask_answer_surface(step) for step in prefix_steps]
            includes_error = (
                isinstance(first_incorrect_step, int)
                and first_incorrect_step >= 0
                and (prefix_end - 1) >= first_incorrect_step
            )
            prefix_records.append(
                TraceExample(
                    trace_id=f"{source_trace_id}::prefix_{prefix_end:02d}",
                    quartet_id=source_trace_id,
                    problem_id=record["problem_id"],
                    domain=record["domain"],
                    verbalizer_id=f"{record['verbalizer_id']}_prefix",
                    audited_locus=prefix_end - 1,
                    counterfactual_role="prefix",
                    process_variant="invalid" if includes_error else "valid",
                    answer_variant=record["answer_variant"],
                    is_valid_process=not includes_error,
                    answer_is_correct=record["answer_is_correct"],
                    problem_text=record["problem_text"],
                    step_texts=prefix_steps,
                    final_answer_line="",
                    masked_answer_line="",
                    trace_text="\n".join(prefix_steps),
                    masked_trace_text="\n".join(masked_steps),
                    metadata={
                        **record["metadata"],
                        "source_trace_id": source_trace_id,
                        "source_verbalizer_id": record["verbalizer_id"],
                        "source_prefix_length": prefix_end,
                        "source_num_steps": len(record["step_texts"]),
                    },
                )
            )
    return prefix_records


def save_records(records: list[TraceExample], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record.to_record(), ensure_ascii=False) + "\n")


def summarize_records(records: list[TraceExample]) -> dict:
    by_domain = Counter(record.domain for record in records)
    by_validity = Counter(str(record.is_valid_process) for record in records)
    by_answer = Counter(str(record.answer_is_correct) for record in records)
    source_groups = {record.metadata["source_trace_id"] for record in records}
    return {
        "num_records": len(records),
        "num_source_traces": len(source_groups),
        "domains": dict(by_domain),
        "is_valid_process": dict(by_validity),
        "answer_is_correct": dict(by_answer),
        "avg_prefix_length": round(sum(len(record.step_texts) for record in records) / len(records), 4) if records else 0.0,
    }


def main() -> None:
    args = parse_args()
    source_records = load_records(args.source_dataset)
    prefix_records = build_prefix_records(source_records)
    save_records(prefix_records, args.output)
    summary = summarize_records(prefix_records)
    summary.update(
        {
            "source_dataset": str(args.source_dataset),
            "output_path": str(args.output),
        }
    )
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
