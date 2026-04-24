from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from civic_prm.api_judge import APIJudgeClient, append_row, load_api_config, load_existing_rows
from civic_prm.audit import load_records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run visible vs masked API-judge scoring on a ProcessBench repair pilot.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("data/external/processbench_repair_pilot.jsonl"),
    )
    parser.add_argument(
        "--cache-output",
        type=Path,
        default=Path("artifacts/external_datasets/processbench_repair_api_rows.jsonl"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("artifacts/external_datasets/processbench_repair_api_summary.json"),
    )
    return parser.parse_args()


def _normalized_score(row: dict) -> float:
    score = float(row["score"])
    return score / 100.0 if score > 1.0 else score


def summarize_local_amcd(rows: list[dict]) -> dict:
    grouped: dict[tuple[str, bool], dict[str, dict]] = defaultdict(dict)
    usage = {
        "prompt_tokens": sum(row.get("usage", {}).get("prompt_tokens", 0) for row in rows),
        "completion_tokens": sum(row.get("usage", {}).get("completion_tokens", 0) for row in rows),
        "total_tokens": sum(row.get("usage", {}).get("total_tokens", 0) for row in rows),
        "num_calls": len(rows),
    }
    for row in rows:
        source_trace_id = str(row.get("source_trace_id") or row["trace_id"])
        repair_group = str(row.get("repair_group") or "unknown")
        grouped[(source_trace_id, bool(row["answer_visible"]))][repair_group] = row

    def aggregate(view_rows: list[tuple[dict, dict]]) -> dict:
        if not view_rows:
            return {
                "num_pairs": 0,
                "local_amcd": None,
                "mean_signed_delta": None,
                "mean_abs_delta": None,
                "mean_observed_score": None,
                "mean_repaired_score": None,
                "by_domain": {},
            }
        wins = []
        signed_deltas = []
        abs_deltas = []
        observed_scores = []
        repaired_scores = []
        by_domain: dict[str, list[int]] = defaultdict(list)
        by_process_variant: dict[str, list[int]] = defaultdict(list)
        for observed, repaired in view_rows:
            observed_score = _normalized_score(observed)
            repaired_score = _normalized_score(repaired)
            delta = repaired_score - observed_score
            wins.append(int(repaired_score > observed_score))
            signed_deltas.append(delta)
            abs_deltas.append(abs(delta))
            observed_scores.append(observed_score)
            repaired_scores.append(repaired_score)
            by_domain[str(observed["domain"])].append(int(repaired_score > observed_score))
            by_process_variant[str(observed["process_variant"])].append(int(repaired_score > observed_score))
        return {
            "num_pairs": len(view_rows),
            "local_amcd": round(sum(wins) / len(wins), 4),
            "mean_signed_delta": round(sum(signed_deltas) / len(signed_deltas), 4),
            "mean_abs_delta": round(sum(abs_deltas) / len(abs_deltas), 4),
            "mean_observed_score": round(sum(observed_scores) / len(observed_scores), 4),
            "mean_repaired_score": round(sum(repaired_scores) / len(repaired_scores), 4),
            "by_domain": {
                key: round(sum(values) / len(values), 4)
                for key, values in sorted(by_domain.items())
            },
            "by_process_variant": {
                key: round(sum(values) / len(values), 4)
                for key, values in sorted(by_process_variant.items())
            },
        }

    visible_pairs: list[tuple[dict, dict]] = []
    masked_pairs: list[tuple[dict, dict]] = []
    for (_, answer_visible), pair in grouped.items():
        if "observed" not in pair or "repaired" not in pair:
            continue
        if answer_visible:
            visible_pairs.append((pair["observed"], pair["repaired"]))
        else:
            masked_pairs.append((pair["observed"], pair["repaired"]))

    visible_summary = aggregate(visible_pairs)
    masked_summary = aggregate(masked_pairs)
    amcd_gap = None
    if visible_summary["local_amcd"] is not None and masked_summary["local_amcd"] is not None:
        amcd_gap = round(visible_summary["local_amcd"] - masked_summary["local_amcd"], 4)
    return {
        "visible": visible_summary,
        "masked": masked_summary,
        "local_amcd_gap_visible_minus_masked": amcd_gap,
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
            row["repair_group"] = str(record.get("metadata", {}).get("repair_group", "unknown"))
            append_row(args.cache_output, row)
            existing_rows.append(row)
            done_keys.add(key)

    summary = {
        "config": {
            "dataset": str(args.dataset),
            "num_records": len(records),
        },
        "local_amcd": summarize_local_amcd(existing_rows),
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
