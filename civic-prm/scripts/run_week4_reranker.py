from __future__ import annotations

import argparse
import json
from pathlib import Path

from civic_prm.audit import load_records
from civic_prm.baselines import compute_verifier_metrics
from civic_prm.calibration import compute_calibration_metrics
from civic_prm.downstream import compute_selection_metrics
from civic_prm.reranker import (
    DEFAULT_RERANK_INSTRUCTION,
    build_reranker_document,
    build_reranker_query,
    format_reranker_pair,
    load_qwen_reranker,
    score_reranker_pairs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Week 4 Qwen3 reranker evaluation with verifier, utility, and calibration metrics."
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("data/generated/craft_core_hard_model_generated_full_hybrid_counterfactual_v2_natural.jsonl"),
    )
    parser.add_argument(
        "--model-root",
        type=Path,
        default=Path("/cephfs/shared/hf_cache/hub/Qwen3-Reranker-8B"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/week4/qwen3_reranker_8b_natural_full_hybrid.json"),
    )
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--max-length", type=int, default=2048)
    parser.add_argument("--ece-bins", type=int, default=10)
    parser.add_argument("--instruction", type=str, default=DEFAULT_RERANK_INSTRUCTION)
    parser.add_argument("--max-quartets", type=int, default=None)
    return parser.parse_args()


def _limit_quartets(records: list[dict], max_quartets: int | None) -> list[dict]:
    if max_quartets is None:
        return records
    kept_quartets = []
    seen = set()
    for record in records:
        quartet_id = record["quartet_id"]
        if quartet_id not in seen:
            if len(seen) >= max_quartets:
                break
            seen.add(quartet_id)
            kept_quartets.append(quartet_id)
    return [record for record in records if record["quartet_id"] in set(kept_quartets)]


def _collect_rows(records: list[dict], scores: list[float]) -> list[dict]:
    rows = []
    for record, score in zip(records, scores, strict=True):
        rows.append(
            {
                "trace_id": record["trace_id"],
                "quartet_id": record["quartet_id"],
                "domain": record["domain"],
                "verbalizer_id": record["verbalizer_id"],
                "process_variant": record["process_variant"],
                "answer_variant": record["answer_variant"],
                "gold_valid": int(record["is_valid_process"]),
                "score": float(score),
            }
        )
    return rows


def _score_view(
    records: list[dict],
    answer_visible: bool,
    instruction: str,
    tokenizer,
    model,
    batch_size: int,
    max_length: int,
    ece_bins: int,
) -> dict:
    pairs = [
        format_reranker_pair(
            instruction=instruction,
            query=build_reranker_query(record),
            document=build_reranker_document(record, answer_visible=answer_visible),
        )
        for record in records
    ]
    scores = score_reranker_pairs(
        pairs,
        tokenizer=tokenizer,
        model=model,
        batch_size=batch_size,
        max_length=max_length,
    )
    rows = _collect_rows(records, scores)
    verifier_metrics = compute_verifier_metrics(rows)
    utility_metrics = compute_selection_metrics(rows)
    calibration_metrics = compute_calibration_metrics(rows, num_bins=ece_bins)
    return {
        "num_pairs": len(pairs),
        "metrics": verifier_metrics,
        "utility": utility_metrics,
        "calibration": calibration_metrics,
        "rows": rows,
    }


def main() -> None:
    args = parse_args()
    records = _limit_quartets(load_records(args.dataset), max_quartets=args.max_quartets)
    tokenizer, model = load_qwen_reranker(args.model_root)

    outputs = {
        "config": {
            "dataset": str(args.dataset),
            "model_root": str(args.model_root),
            "instruction": args.instruction,
            "batch_size": args.batch_size,
            "max_length": args.max_length,
            "ece_bins": args.ece_bins,
            "max_quartets": args.max_quartets,
            "num_records": len(records),
            "num_quartets": len({record["quartet_id"] for record in records}),
        },
        "views": {
            "visible": _score_view(
                records=records,
                answer_visible=True,
                instruction=args.instruction,
                tokenizer=tokenizer,
                model=model,
                batch_size=args.batch_size,
                max_length=args.max_length,
                ece_bins=args.ece_bins,
            ),
            "masked": _score_view(
                records=records,
                answer_visible=False,
                instruction=args.instruction,
                tokenizer=tokenizer,
                model=model,
                batch_size=args.batch_size,
                max_length=args.max_length,
                ece_bins=args.ece_bins,
            ),
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(outputs, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                view_name: {
                    "metrics": payload["metrics"],
                    "utility": {
                        key: value
                        for key, value in payload["utility"].items()
                        if key != "quartet_rows"
                    },
                    "calibration": payload["calibration"],
                }
                for view_name, payload in outputs["views"].items()
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
