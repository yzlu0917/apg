from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from civic_prm.audit import load_records
from civic_prm.baselines import compute_verifier_metrics, score_baseline, train_bce_head, train_repair_head
from civic_prm.default_paths import DEFAULT_BASE_BENCHMARK_DATASET
from civic_prm.downstream import compute_selection_metrics
from civic_prm.frozen_backbone import encode_texts, load_encoder
from civic_prm.metrics import binary_accuracy, binary_auroc
from civic_prm.splits import build_quartet_split_map
from civic_prm.text_views import build_view_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a minimal dual-head disentangled verifier and evaluate on an OOD generated slice."
    )
    parser.add_argument(
        "--train-dataset",
        type=Path,
        default=DEFAULT_BASE_BENCHMARK_DATASET,
    )
    parser.add_argument(
        "--eval-dataset",
        type=Path,
        default=Path("data/generated/craft_core_hard_model_generated_full_hybrid_counterfactual_v2_natural.jsonl"),
    )
    parser.add_argument(
        "--model-root",
        type=Path,
        default=Path("/cephfs/shared/hf_cache/hub/models--Qwen--Qwen3-1.7B/snapshots"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/generated/model_generated_full_hybrid_counterfactual_v2_natural_dual_head.json"),
    )
    parser.add_argument(
        "--feature-cache-dir",
        type=Path,
        default=Path("artifacts/generated/full_hybrid_dual_head_features_v1"),
    )
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument(
        "--process-lambda-grid",
        type=float,
        nargs="+",
        default=[0.1, 0.25, 0.5, 1.0, 2.0],
    )
    parser.add_argument(
        "--alpha-grid",
        type=float,
        nargs="+",
        default=[0.0, 0.1, 0.25, 0.5, 1.0, 2.0],
    )
    return parser.parse_args()


def _load_or_extract_features(
    records: list[dict],
    view_name: str,
    tokenizer,
    model,
    cache_path: Path,
    batch_size: int,
    max_length: int,
) -> torch.Tensor:
    if cache_path.exists():
        payload = torch.load(cache_path)
        if payload.get("trace_ids") == [record["trace_id"] for record in records]:
            return payload["features"]
    texts = [build_view_text(record, view_name=view_name) for record in records]
    features = encode_texts(texts, tokenizer=tokenizer, model=model, batch_size=batch_size, max_length=max_length)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"trace_ids": [record["trace_id"] for record in records], "features": features}, cache_path)
    return features


def _slice_train_val(records: list[dict], split_map: dict[str, str]):
    train_records = [record for record in records if split_map[record["quartet_id"]] == "train"]
    val_records = [record for record in records if split_map[record["quartet_id"]] == "val"]
    return train_records, val_records


def _process_labels(records: list[dict]) -> torch.Tensor:
    return torch.tensor([float(record["is_valid_process"]) for record in records], dtype=torch.float32)


def _answer_labels(records: list[dict]) -> torch.Tensor:
    return torch.tensor([float(record["answer_is_correct"]) for record in records], dtype=torch.float32)


def _selection_metric(
    process_metrics: dict,
    total_metrics: dict,
    utility_metrics: dict,
) -> float:
    return (
        process_metrics["amcd"]
        - process_metrics["ass_total"]
        + utility_metrics["selection_gain_at4"]
        - utility_metrics["exploitability_rate"]
        + 0.05 * total_metrics["ordinary_auroc"]
    )


def _combine_rows(process_rows: list[dict], consistency_rows: list[dict], alpha: float) -> list[dict]:
    combined = []
    for process_row, consistency_row in zip(process_rows, consistency_rows, strict=True):
        if process_row["trace_id"] != consistency_row["trace_id"]:
            raise ValueError("trace ordering mismatch between process and consistency rows")
        total_logit = process_row["logit"] + alpha * consistency_row["logit"]
        total_score = torch.sigmoid(torch.tensor(total_logit)).item()
        combined.append(
            {
                **process_row,
                "logit": round(float(total_logit), 6),
                "score": round(float(total_score), 6),
            }
        )
    return combined


def _answer_head_metrics(rows: list[dict], records: list[dict]) -> dict:
    labels = [int(record["answer_is_correct"]) for record in records]
    scores = [row["score"] for row in rows]
    preds = [int(score >= 0.5) for score in scores]
    return {
        "answer_accuracy": round(binary_accuracy(labels, preds), 4),
        "answer_auroc": round(binary_auroc(labels, scores), 4),
    }


def main() -> None:
    args = parse_args()
    torch.manual_seed(args.seed)
    train_records = load_records(args.train_dataset)
    eval_records = load_records(args.eval_dataset)
    split_map = build_quartet_split_map(train_records, seed=args.seed)
    train_rows, val_rows = _slice_train_val(train_records, split_map)

    tokenizer, model = load_encoder(args.model_root)
    visible_train = _load_or_extract_features(
        train_rows,
        "visible",
        tokenizer,
        model,
        args.feature_cache_dir / "train_visible.pt",
        args.batch_size,
        args.max_length,
    )
    visible_val = _load_or_extract_features(
        val_rows,
        "visible",
        tokenizer,
        model,
        args.feature_cache_dir / "val_visible.pt",
        args.batch_size,
        args.max_length,
    )
    visible_eval = _load_or_extract_features(
        eval_records,
        "visible",
        tokenizer,
        model,
        args.feature_cache_dir / "eval_visible.pt",
        args.batch_size,
        args.max_length,
    )

    torch.manual_seed(args.seed)
    consistency_head = train_bce_head(
        train_features=visible_train,
        train_labels=_answer_labels(train_rows),
        val_features=visible_val,
        val_labels=_answer_labels(val_rows),
    )
    consistency_val_rows = score_baseline(
        model=consistency_head,
        train_features=visible_train,
        eval_features=visible_val,
        eval_records=val_rows,
    )
    consistency_eval_rows = score_baseline(
        model=consistency_head,
        train_features=visible_train,
        eval_features=visible_eval,
        eval_records=eval_records,
    )

    best_payload = None
    search_rows = []
    for lambda_cond_swap in args.process_lambda_grid:
        torch.manual_seed(args.seed)
        process_head = train_repair_head(
            train_features=visible_train,
            train_records=train_rows,
            train_labels=_process_labels(train_rows),
            val_features=visible_val,
            val_records=val_rows,
            val_labels=_process_labels(val_rows),
            lambda_local_pair=0.0,
            lambda_cond_swap=lambda_cond_swap,
        )
        process_val_rows = score_baseline(
            model=process_head,
            train_features=visible_train,
            eval_features=visible_val,
            eval_records=val_rows,
        )
        process_val_metrics = compute_verifier_metrics(process_val_rows)
        for alpha in args.alpha_grid:
            total_val_rows = _combine_rows(process_val_rows, consistency_val_rows, alpha=alpha)
            total_val_metrics = compute_verifier_metrics(total_val_rows)
            utility_val = compute_selection_metrics(total_val_rows)
            selection = _selection_metric(process_val_metrics, total_val_metrics, utility_val)
            candidate_row = {
                "lambda_cond_swap": lambda_cond_swap,
                "alpha": alpha,
                "selection_metric": round(selection, 4),
                "process_val_metrics": process_val_metrics,
                "total_val_metrics": total_val_metrics,
                "utility_val": {
                    key: value for key, value in utility_val.items() if key != "quartet_rows"
                },
            }
            search_rows.append(candidate_row)
            if best_payload is None or selection > best_payload["selection_metric"]:
                best_payload = {
                    "selection_metric": selection,
                    "process_head": process_head,
                    "lambda_cond_swap": lambda_cond_swap,
                    "alpha": alpha,
                    "process_val_rows": process_val_rows,
                    "process_val_metrics": process_val_metrics,
                    "total_val_rows": total_val_rows,
                    "total_val_metrics": total_val_metrics,
                    "utility_val": utility_val,
                }

    assert best_payload is not None
    process_eval_rows = score_baseline(
        model=best_payload["process_head"],
        train_features=visible_train,
        eval_features=visible_eval,
        eval_records=eval_records,
    )
    total_eval_rows = _combine_rows(
        process_eval_rows,
        consistency_eval_rows,
        alpha=best_payload["alpha"],
    )
    process_eval_metrics = compute_verifier_metrics(process_eval_rows)
    total_eval_metrics = compute_verifier_metrics(total_eval_rows)
    utility_eval = compute_selection_metrics(total_eval_rows)

    outputs = {
        "config": {
            "train_dataset": str(args.train_dataset),
            "eval_dataset": str(args.eval_dataset),
            "model_root": str(args.model_root),
            "seed": args.seed,
            "process_lambda_grid": args.process_lambda_grid,
            "alpha_grid": args.alpha_grid,
        },
        "selected_hparams": {
            "lambda_cond_swap": best_payload["lambda_cond_swap"],
            "alpha": best_payload["alpha"],
        },
        "selection_metric": round(best_payload["selection_metric"], 4),
        "consistency_head_val_metrics": _answer_head_metrics(consistency_val_rows, val_rows),
        "consistency_head_eval_metrics": _answer_head_metrics(consistency_eval_rows, eval_records),
        "process_val_metrics": best_payload["process_val_metrics"],
        "total_val_metrics": best_payload["total_val_metrics"],
        "utility_val": {key: value for key, value in best_payload["utility_val"].items() if key != "quartet_rows"},
        "process_metrics": process_eval_metrics,
        "total_metrics": total_eval_metrics,
        "utility_eval": {key: value for key, value in utility_eval.items() if key != "quartet_rows"},
        "search_rows": search_rows,
        "process_test_rows": process_eval_rows,
        "consistency_test_rows": consistency_eval_rows,
        "total_test_rows": total_eval_rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(outputs, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "selected_hparams": outputs["selected_hparams"],
                "process_metrics": outputs["process_metrics"],
                "total_metrics": outputs["total_metrics"],
                "utility_eval": outputs["utility_eval"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
