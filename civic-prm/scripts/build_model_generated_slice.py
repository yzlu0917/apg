from __future__ import annotations

import argparse
import json
from pathlib import Path

from civic_prm.default_paths import DEFAULT_BASE_BENCHMARK_DATASET
from civic_prm.generated_traces import (
    build_generated_records,
    generation_passes_audit,
    generate_trace_sample,
    load_generator,
    load_problem_specs,
    summarize_generated_rows,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a small model-generated trace slice from held-out hard problems.")
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
    parser.add_argument("--samples-per-problem", type=int, default=3)
    parser.add_argument("--max-retries", type=int, default=8)
    parser.add_argument(
        "--domains",
        nargs="*",
        default=None,
        help="Optional domain filter, for example: --domains graph_path blocksworld",
    )
    parser.add_argument(
        "--require-auditable-original",
        action="store_true",
        help="Retry generation until the original trace passes the deterministic audit gate.",
    )
    parser.add_argument(
        "--use-blocksworld-scaffold",
        action="store_true",
        help="Use stepwise legal-state scaffolding for blocksworld generation.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/generated/craft_core_hard_model_generated.jsonl"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("artifacts/generated/model_generated_summary.json"),
    )
    parser.add_argument(
        "--cache-output",
        type=Path,
        default=Path("artifacts/generated/model_generated_rows.jsonl"),
    )
    parser.add_argument(
        "--attempt-log-output",
        type=Path,
        default=Path("artifacts/generated/model_generated_attempts.jsonl"),
    )
    return parser.parse_args()


def load_cached_rows(path: Path) -> dict[str, list[dict]]:
    if not path.exists():
        return {}
    grouped: dict[str, list[dict]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        grouped.setdefault(row["swap_group_id"], []).append(row)
    return grouped


def append_rows(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def append_attempt(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    args = parse_args()
    specs = load_problem_specs(args.source_dataset)
    if args.domains:
        domain_filter = set(args.domains)
        specs = [spec for spec in specs if spec["domain"] in domain_filter]
    tokenizer, model = load_generator(args.model_root)
    cached = load_cached_rows(args.cache_output)

    all_rows: list[dict] = []
    attempted = 0
    accepted = 0
    failed_groups: list[dict] = []
    for spec in specs:
        for sample_index in range(args.samples_per_problem):
            swap_group_id = f"{spec['quartet_id']}-gen-{sample_index:02d}"
            existing = cached.get(swap_group_id)
            if existing is not None:
                all_rows.extend(existing)
                accepted += 1
                continue
            generation = None
            last_error = None
            last_rejection_reason = None
            for attempt_index in range(args.max_retries):
                attempted += 1
                try:
                    if args.use_blocksworld_scaffold:
                        candidate = generate_trace_sample(
                            tokenizer,
                            model,
                            spec,
                            use_blocksworld_scaffold=True,
                        )
                    else:
                        candidate = generate_trace_sample(tokenizer, model, spec)
                    passes_audit, rejection_reason = generation_passes_audit(spec, sample_index, candidate)
                    append_attempt(
                        args.attempt_log_output,
                        {
                            "swap_group_id": swap_group_id,
                            "problem_id": spec["problem_id"],
                            "domain": spec["domain"],
                            "attempt_index": attempt_index,
                            "accepted": passes_audit or not args.require_auditable_original,
                            "rejection_reason": rejection_reason,
                            "final_answer_line": candidate["final_answer_line"],
                            "step_texts": candidate["steps"],
                            "used_blocksworld_scaffold": args.use_blocksworld_scaffold and spec["domain"] == "blocksworld",
                        },
                    )
                    if args.require_auditable_original and not passes_audit:
                        last_rejection_reason = rejection_reason
                        continue
                    generation = candidate
                    break
                except Exception as error:  # noqa: BLE001
                    last_error = error
            if generation is None:
                failed_groups.append(
                    {
                        "swap_group_id": swap_group_id,
                        "problem_id": spec["problem_id"],
                        "domain": spec["domain"],
                        "last_error": str(last_error) if last_error is not None else None,
                        "last_rejection_reason": last_rejection_reason,
                    }
                )
                continue
            rows = build_generated_records(spec, sample_index, generation)
            append_rows(args.cache_output, rows)
            all_rows.extend(rows)
            accepted += 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row in all_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = summarize_generated_rows(all_rows)
    summary.update(
        {
            "source_dataset": str(args.source_dataset),
            "samples_per_problem": args.samples_per_problem,
            "require_auditable_original": args.require_auditable_original,
            "use_blocksworld_scaffold": args.use_blocksworld_scaffold,
            "generation_attempts": attempted,
            "accepted_swap_groups": accepted,
            "failed_swap_groups": failed_groups,
            "num_failed_swap_groups": len(failed_groups),
        }
    )
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
