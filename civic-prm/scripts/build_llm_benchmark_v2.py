from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from civic_prm.api_judge import APIJudgeClient, load_api_config
from civic_prm.api_rewrite import rewrite_record_with_api
from civic_prm.generator import load_dataset, save_dataset
from civic_prm.schema import TraceExample


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an API-assisted benchmark v2 surface-realized slice.")
    parser.add_argument(
        "--source-dataset",
        type=Path,
        default=Path("data/generated/craft_core_hard_blindfix_v1.jsonl"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/generated/craft_core_hard_llm_v2_pilot.jsonl"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("artifacts/generated/craft_core_hard_llm_v2_pilot_summary.json"),
    )
    parser.add_argument(
        "--cache-output",
        type=Path,
        default=Path("artifacts/generated/craft_core_hard_llm_v2_pilot_rows.jsonl"),
    )
    parser.add_argument("--quartets-per-domain", type=int, default=3)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--max-retries", type=int, default=3)
    return parser.parse_args()


def select_quartets(records: list[TraceExample], quartets_per_domain: int, seed: int) -> list[str]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for quartet_id in sorted({record.quartet_id for record in records}):
        domain = next(record.domain for record in records if record.quartet_id == quartet_id)
        grouped[domain].append(quartet_id)
    rng = random.Random(seed)
    selected: list[str] = []
    for domain in sorted(grouped):
        candidates = list(grouped[domain])
        rng.shuffle(candidates)
        selected.extend(sorted(candidates[:quartets_per_domain]))
    return selected


def load_cached_rows(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    rows = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        rows[row["trace_id"]] = row
    return rows


def append_cached_row(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    args = parse_args()
    records = load_dataset(args.source_dataset)
    selected_quartets = set(select_quartets(records, args.quartets_per_domain, args.seed))
    target_records = [record for record in records if record.quartet_id in selected_quartets]
    cached_rows = load_cached_rows(args.cache_output)

    config = load_api_config()
    client = APIJudgeClient(
        base_url=config["base_url"],
        model=config["model"],
        api_key=config["api_key"],
        max_retries=args.max_retries,
    )

    rewritten_records: list[TraceExample] = []
    usage_totals = Counter()
    failed_rows: list[dict] = []
    for index, record in enumerate(target_records, start=1):
        cache_row = cached_rows.get(record.trace_id)
        if cache_row is None:
            try:
                rewrite = rewrite_record_with_api(
                    client,
                    record.to_record(),
                    temperature=args.temperature,
                )
            except Exception as error:  # noqa: BLE001
                failed_rows.append(
                    {
                        "trace_id": record.trace_id,
                        "quartet_id": record.quartet_id,
                        "domain": record.domain,
                        "error": str(error),
                    }
                )
                print(
                    f"[llm-v2] failed {index}/{len(target_records)} {record.trace_id}: {error}",
                    flush=True,
                )
                continue
            cache_row = {
                "trace_id": record.trace_id,
                "quartet_id": record.quartet_id,
                "domain": record.domain,
                "problem_text": rewrite["problem_text"],
                "step_texts": rewrite["step_texts"],
                "usage": rewrite["usage"],
                "raw_response": rewrite["raw_response"],
                "rewriter_name": rewrite["rewriter_name"],
                "api_calls": rewrite.get("api_calls", 1),
            }
            append_cached_row(args.cache_output, cache_row)
            print(
                f"[llm-v2] rewrote {index}/{len(target_records)} {record.trace_id}",
                flush=True,
            )
        elif index % 10 == 0:
            print(
                f"[llm-v2] reused cache {index}/{len(target_records)} {record.trace_id}",
                flush=True,
            )
        usage = cache_row.get("usage", {})
        usage_totals["prompt_tokens"] += usage.get("prompt_tokens", 0)
        usage_totals["completion_tokens"] += usage.get("completion_tokens", 0)
        usage_totals["total_tokens"] += usage.get("total_tokens", 0)
        usage_totals["num_calls"] += cache_row.get("api_calls", 1)
        metadata = dict(record.metadata)
        metadata.update(
            {
                "llm_surface_v2": True,
                "surface_rewriter_name": cache_row.get("rewriter_name", "ark-llm-v2"),
                "source_trace_id": record.trace_id,
            }
        )
        rewritten_records.append(
            TraceExample(
                trace_id=f"{record.trace_id}-llmv2",
                quartet_id=record.quartet_id,
                problem_id=record.problem_id,
                domain=record.domain,
                verbalizer_id=f"{record.verbalizer_id}_llmv2",
                audited_locus=record.audited_locus,
                counterfactual_role=record.counterfactual_role,
                process_variant=record.process_variant,
                answer_variant=record.answer_variant,
                is_valid_process=record.is_valid_process,
                answer_is_correct=record.answer_is_correct,
                problem_text=cache_row["problem_text"],
                step_texts=cache_row["step_texts"],
                final_answer_line=record.final_answer_line,
                masked_answer_line=record.masked_answer_line,
                trace_text="\n".join(cache_row["step_texts"] + [record.final_answer_line]),
                masked_trace_text="\n".join(cache_row["step_texts"] + [record.masked_answer_line]),
                metadata=metadata,
            )
        )

    save_dataset(rewritten_records, args.output)
    summary = {
        "source_dataset": str(args.source_dataset),
        "output_dataset": str(args.output),
        "num_source_traces": len(target_records),
        "num_rewritten_traces": len(rewritten_records),
        "num_failed_traces": len(failed_rows),
        "quartets_per_domain": args.quartets_per_domain,
        "selected_quartets": sorted(selected_quartets),
        "domains": dict(Counter(record.domain for record in rewritten_records)),
        "usage": dict(usage_totals),
        "failed_rows": failed_rows,
        "temperature": args.temperature,
        "seed": args.seed,
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
