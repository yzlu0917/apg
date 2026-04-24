from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from civic_prm.audit import load_records
from civic_prm.calibration import compute_calibration_metrics
from civic_prm.metrics import binary_accuracy
from civic_prm.processbench_eval import compute_processbench_metrics
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
        description="Run ProcessBench whole-trace reranker evaluation on a grouped test split."
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("data/external/processbench_eval_all.jsonl"),
    )
    parser.add_argument(
        "--model-root",
        type=Path,
        default=Path("/cephfs/shared/hf_cache/hub/Qwen3-Reranker-8B"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/external_datasets/processbench_reranker_8b.json"),
    )
    parser.add_argument(
        "--rows-output",
        type=Path,
        default=None,
        help="Optional JSONL path for per-trace scores. Defaults to <output stem>_rows.jsonl.",
    )
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--max-length", type=int, default=2048)
    parser.add_argument("--ece-bins", type=int, default=10)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--instruction", type=str, default=DEFAULT_RERANK_INSTRUCTION)
    return parser.parse_args()


def _group_id(record: dict) -> str:
    metadata = record.get("metadata", {})
    return str(
        metadata.get("source_trace_id")
        or metadata.get("source_example_id")
        or record["trace_id"]
    )


def _attach_group_splits(records: list[dict], seed: int) -> list[dict]:
    groups_by_domain: dict[str, list[str]] = defaultdict(list)
    seen: set[str] = set()
    for record in records:
        group_id = _group_id(record)
        if group_id in seen:
            continue
        seen.add(group_id)
        groups_by_domain[record["domain"]].append(group_id)

    rng = random.Random(seed)
    group_to_split: dict[str, str] = {}
    for domain, group_ids in groups_by_domain.items():
        group_ids = sorted(group_ids)
        rng.shuffle(group_ids)
        total = len(group_ids)
        train_cut = max(1, int(round(total * 0.7)))
        val_cut = max(train_cut + 1, int(round(total * 0.85)))
        for index, group_id in enumerate(group_ids):
            if index < train_cut:
                split = "train"
            elif index < val_cut:
                split = "val"
            else:
                split = "test"
            group_to_split[group_id] = split

    enriched = []
    for record in records:
        cloned = dict(record)
        cloned["_group_id"] = _group_id(record)
        cloned["split"] = group_to_split[cloned["_group_id"]]
        enriched.append(cloned)
    return enriched


def _split_summary(records: list[dict]) -> dict[str, int]:
    return dict(Counter(record["split"] for record in records))


def _accuracy_at_threshold(rows: list[dict], threshold: float) -> float:
    gold = [int(row["gold_valid"]) for row in rows]
    preds = [int(float(row["score"]) >= threshold) for row in rows]
    return binary_accuracy(gold, preds)


def _best_accuracy_threshold(rows: list[dict]) -> tuple[float, float]:
    candidates = sorted({0.0, 1.0, *[float(row["score"]) for row in rows]})
    best_threshold = 0.5
    best_accuracy = -1.0
    for threshold in candidates:
        accuracy = _accuracy_at_threshold(rows, threshold)
        if accuracy > best_accuracy or (accuracy == best_accuracy and abs(threshold - 0.5) < abs(best_threshold - 0.5)):
            best_threshold = threshold
            best_accuracy = accuracy
    return best_threshold, best_accuracy


def _threshold_summary(val_rows: list[dict], test_rows: list[dict]) -> dict:
    threshold, val_accuracy = _best_accuracy_threshold(val_rows)
    return {
        "selected_on": "val",
        "criterion": "ordinary_accuracy",
        "threshold": round(threshold, 4),
        "val_accuracy": round(val_accuracy, 4),
        "test_accuracy_at_selected_threshold": round(_accuracy_at_threshold(test_rows, threshold), 4),
        "test_accuracy_at_default_threshold": round(_accuracy_at_threshold(test_rows, 0.5), 4),
    }


def _collect_rows(records: list[dict], scores: list[float], answer_visible: bool) -> list[dict]:
    view_name = "visible" if answer_visible else "masked"
    rows = []
    for record, score in zip(records, scores, strict=True):
        rows.append(
            {
                "trace_id": record["trace_id"],
                "problem_id": record["problem_id"],
                "domain": record["domain"],
                "split": record["split"],
                "process_variant": record["process_variant"],
                "answer_variant": record["answer_variant"],
                "gold_valid": int(record["is_valid_process"]),
                "score": float(score),
                "view": view_name,
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
    rows = _collect_rows(records, scores, answer_visible=answer_visible)
    val_rows = [row for row in rows if row["split"] == "val"]
    test_rows = [row for row in rows if row["split"] == "test"]
    return {
        "num_pairs": len(pairs),
        "metrics": compute_processbench_metrics(test_rows),
        "calibration": compute_calibration_metrics(test_rows, num_bins=ece_bins),
        "val_metrics": compute_processbench_metrics(val_rows),
        "val_calibration": compute_calibration_metrics(val_rows, num_bins=ece_bins),
        "threshold_analysis": _threshold_summary(val_rows, test_rows),
        "rows": rows,
    }


def _default_rows_output(output: Path) -> Path:
    return output.with_name(f"{output.stem}_rows.jsonl")


def _write_rows(rows_output: Path, outputs: dict) -> None:
    rows_output.parent.mkdir(parents=True, exist_ok=True)
    with rows_output.open("w", encoding="utf-8") as handle:
        for view_name in ["visible", "masked"]:
            for row in outputs["views"][view_name]["rows"]:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    args = parse_args()
    rows_output = args.rows_output or _default_rows_output(args.output)

    records = _attach_group_splits(load_records(args.dataset), seed=args.seed)
    scored_records = [record for record in records if record["split"] in {"val", "test"}]

    tokenizer, model = load_qwen_reranker(args.model_root)
    outputs = {
        "config": {
            "dataset": str(args.dataset),
            "model_root": str(args.model_root),
            "instruction": args.instruction,
            "batch_size": args.batch_size,
            "max_length": args.max_length,
            "ece_bins": args.ece_bins,
            "seed": args.seed,
            "num_records": len(records),
            "num_scored_records": len(scored_records),
            "rows_output": str(rows_output),
        },
        "split_summary": _split_summary(records),
        "views": {
            "visible": _score_view(
                records=scored_records,
                answer_visible=True,
                instruction=args.instruction,
                tokenizer=tokenizer,
                model=model,
                batch_size=args.batch_size,
                max_length=args.max_length,
                ece_bins=args.ece_bins,
            ),
            "masked": _score_view(
                records=scored_records,
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

    _write_rows(rows_output, outputs)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(outputs, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                view_name: {
                    "metrics": payload["metrics"],
                    "calibration": payload["calibration"],
                    "threshold_analysis": payload["threshold_analysis"],
                }
                for view_name, payload in outputs["views"].items()
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
