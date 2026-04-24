from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from civic_prm.audit import load_records
from civic_prm.default_paths import DEFAULT_BASE_BENCHMARK_DATASET
from civic_prm.generator import save_dataset, summarize_dataset
from civic_prm.naturalize import (
    build_naturalized_example,
    heuristic_naturalize_record,
    load_naturalizer,
    naturalize_record,
)
from civic_prm.splits import build_quartet_split_map


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a naturalized test slice from the hard synthetic benchmark.")
    parser.add_argument(
        "--source-dataset",
        type=Path,
        default=DEFAULT_BASE_BENCHMARK_DATASET,
    )
    parser.add_argument(
        "--model-root",
        type=Path,
        default=Path("/cephfs/shared/hf_cache/hub/models--Qwen--Qwen3-1.7B/snapshots"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/generated/craft_core_hard_natural_test.jsonl"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("artifacts/natural/craft_core_hard_natural_test_summary.json"),
    )
    parser.add_argument(
        "--cache-output",
        type=Path,
        default=Path("artifacts/natural/naturalization_rows.jsonl"),
    )
    parser.add_argument("--split-seed", type=int, default=17)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument(
        "--use-all-records",
        action="store_true",
        help="Naturalize every record from source-dataset instead of only the synthetic test split.",
    )
    return parser.parse_args()


def load_cached_rows(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    rows = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            payload = json.loads(line)
            naturalizer_name = payload.get("naturalizer_name")
            if naturalizer_name is None:
                naturalizer_name = "heuristic-fallback" if payload.get("raw_response") == "[heuristic_fallback]" else "qwen3-1.7b"
            rows[payload["source_trace_id"]] = payload
            rows[payload["source_trace_id"]]["naturalizer_name"] = naturalizer_name
    return rows


def append_cache_row(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    args = parse_args()
    source_records = load_records(args.source_dataset)
    if args.use_all_records:
        selected_records = source_records
        selection_mode = "all_records"
    else:
        split_map = build_quartet_split_map(source_records, seed=args.split_seed)
        selected_records = [record for record in source_records if split_map[record["quartet_id"]] == "test"]
        selection_mode = "synthetic_test_only"
    cached_rows = load_cached_rows(args.cache_output)

    tokenizer, model = load_naturalizer(args.model_root)
    naturalized_examples = []
    for record in selected_records:
        cached = cached_rows.get(record["trace_id"])
        rewrite = None
        if cached is not None:
            rewrite = {
                "problem_text": cached["problem_text"],
                "step_texts": cached["step_texts"],
                "raw_response": cached.get("raw_response", ""),
                "naturalizer_name": cached.get("naturalizer_name", "qwen3-1.7b"),
            }
        else:
            last_error = None
            for _ in range(args.max_retries):
                try:
                    rewrite = naturalize_record(tokenizer, model, record)
                    append_cache_row(
                        args.cache_output,
                        {
                            "source_trace_id": record["trace_id"],
                            "problem_text": rewrite["problem_text"],
                            "step_texts": rewrite["step_texts"],
                            "raw_response": rewrite["raw_response"],
                            "naturalizer_name": rewrite.get("naturalizer_name", "qwen3-1.7b"),
                        },
                    )
                    break
                except Exception as error:  # noqa: BLE001
                    last_error = error
            if rewrite is None:
                rewrite = heuristic_naturalize_record(record)
                append_cache_row(
                    args.cache_output,
                    {
                        "source_trace_id": record["trace_id"],
                        "problem_text": rewrite["problem_text"],
                        "step_texts": rewrite["step_texts"],
                        "raw_response": rewrite["raw_response"],
                        "naturalizer_name": rewrite.get("naturalizer_name", "heuristic-fallback"),
                    },
                )
        naturalized_examples.append(
            build_naturalized_example(
                record=record,
                rewrite=rewrite,
                naturalizer_name=rewrite.get("naturalizer_name", "qwen3-1.7b"),
            )
        )

    save_dataset(naturalized_examples, args.output)
    summary = summarize_dataset(naturalized_examples)
    summary["source_dataset"] = str(args.source_dataset)
    summary["selection_mode"] = selection_mode
    summary["num_selected_records"] = len(selected_records)
    summary["naturalizers"] = dict(
        Counter(example.metadata.get("naturalizer_name", "unknown") for example in naturalized_examples)
    )
    summary["problem_rewrites_changed"] = sum(
        int(example.problem_text != record["problem_text"])
        for example, record in zip(naturalized_examples, selected_records, strict=True)
    )
    summary["step_rewrites_changed"] = sum(
        int(example.step_texts != record["step_texts"])
        for example, record in zip(naturalized_examples, selected_records, strict=True)
    )
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
