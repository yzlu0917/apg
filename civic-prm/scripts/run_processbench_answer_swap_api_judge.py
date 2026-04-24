from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from civic_prm.api_judge import APIJudgeClient, append_row, load_api_config, load_existing_rows
from civic_prm.audit import load_records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run visible vs masked API-judge scoring on a ProcessBench answer-swap pilot.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("data/external/processbench_answer_swap_pilot.jsonl"),
    )
    parser.add_argument(
        "--cache-output",
        type=Path,
        default=Path("artifacts/external_datasets/processbench_answer_swap_api_rows.jsonl"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("artifacts/external_datasets/processbench_answer_swap_api_summary.json"),
    )
    return parser.parse_args()


def _normalized_score(row: dict) -> float:
    score = float(row["score"])
    return score / 100.0 if score > 1.0 else score


def summarize_ass(rows: list[dict]) -> dict:
    grouped: dict[tuple[str, bool], dict[str, dict]] = defaultdict(dict)
    usage = {
        "prompt_tokens": sum(row.get("usage", {}).get("prompt_tokens", 0) for row in rows),
        "completion_tokens": sum(row.get("usage", {}).get("completion_tokens", 0) for row in rows),
        "total_tokens": sum(row.get("usage", {}).get("total_tokens", 0) for row in rows),
        "num_calls": len(rows),
    }
    for row in rows:
        source_trace_id = str(row.get("source_trace_id") or row.get("metadata", {}).get("source_trace_id") or row["trace_id"])
        swap_group = str(row.get("swap_group") or row.get("metadata", {}).get("swap_group") or "unknown")
        grouped[(source_trace_id, bool(row["answer_visible"]))][swap_group] = row

    def aggregate(view_rows: list[tuple[dict, dict]]) -> dict:
        if not view_rows:
            return {
                "num_pairs": 0,
                "mean_abs_delta": None,
                "mean_signed_delta": None,
                "observed_higher_rate": None,
                "mean_observed_score": None,
                "mean_swapped_score": None,
                "by_domain": {},
                "by_process_variant": {},
                "by_source_answer_variant": {},
            }

        abs_deltas = []
        signed_deltas = []
        observed_scores = []
        swapped_scores = []
        observed_higher = []
        by_domain: dict[str, list[float]] = defaultdict(list)
        by_process_variant: dict[str, list[float]] = defaultdict(list)
        by_source_answer_variant: dict[str, list[float]] = defaultdict(list)
        for observed, swapped in view_rows:
            observed_score = _normalized_score(observed)
            swapped_score = _normalized_score(swapped)
            delta = swapped_score - observed_score
            abs_delta = abs(delta)
            abs_deltas.append(abs_delta)
            signed_deltas.append(delta)
            observed_scores.append(observed_score)
            swapped_scores.append(swapped_score)
            observed_higher.append(int(observed_score > swapped_score))
            by_domain[str(observed["domain"])].append(abs_delta)
            by_process_variant[str(observed["process_variant"])].append(abs_delta)
            by_source_answer_variant[str(observed["answer_variant"])].append(abs_delta)

        return {
            "num_pairs": len(view_rows),
            "mean_abs_delta": round(sum(abs_deltas) / len(abs_deltas), 4),
            "mean_signed_delta": round(sum(signed_deltas) / len(signed_deltas), 4),
            "observed_higher_rate": round(sum(observed_higher) / len(observed_higher), 4),
            "mean_observed_score": round(sum(observed_scores) / len(observed_scores), 4),
            "mean_swapped_score": round(sum(swapped_scores) / len(swapped_scores), 4),
            "by_domain": {
                key: round(sum(values) / len(values), 4)
                for key, values in sorted(by_domain.items())
            },
            "by_process_variant": {
                key: round(sum(values) / len(values), 4)
                for key, values in sorted(by_process_variant.items())
            },
            "by_source_answer_variant": {
                key: round(sum(values) / len(values), 4)
                for key, values in sorted(by_source_answer_variant.items())
            },
        }

    visible_pairs: list[tuple[dict, dict]] = []
    masked_pairs: list[tuple[dict, dict]] = []
    for (_, answer_visible), pair in grouped.items():
        if "observed" not in pair or "swapped" not in pair:
            continue
        if answer_visible:
            visible_pairs.append((pair["observed"], pair["swapped"]))
        else:
            masked_pairs.append((pair["observed"], pair["swapped"]))

    visible_summary = aggregate(visible_pairs)
    masked_summary = aggregate(masked_pairs)
    ass_gap = None
    if visible_summary["mean_abs_delta"] is not None and masked_summary["mean_abs_delta"] is not None:
        ass_gap = round(visible_summary["mean_abs_delta"] - masked_summary["mean_abs_delta"], 4)

    return {
        "visible": visible_summary,
        "masked": masked_summary,
        "ass_gap_visible_minus_masked": ass_gap,
        "usage": usage,
    }


def main() -> None:
    args = parse_args()
    config = load_api_config()
    records = load_records(args.dataset)

    existing_rows = load_existing_rows(args.cache_output)
    done_keys = {(row["trace_id"], row["answer_visible"]) for row in existing_rows}

    client = APIJudgeClient(**config)
    for answer_visible in [True, False]:
        for record in records:
            key = (record["trace_id"], answer_visible)
            if key in done_keys:
                continue
            row = client.score_record(record, answer_visible=answer_visible)
            row["source_trace_id"] = str(record.get("metadata", {}).get("source_trace_id", record["trace_id"]))
            row["swap_group"] = str(record.get("metadata", {}).get("swap_group", "unknown"))
            append_row(args.cache_output, row)
            existing_rows.append(row)
            done_keys.add(key)

    summary = {
        "config": {
            "dataset": str(args.dataset),
            "num_records": len(records),
        },
        "ass": summarize_ass(existing_rows),
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
