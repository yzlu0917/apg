from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

import torch

from civic_prm.audit import load_records
from civic_prm.baselines import (
    compute_verifier_metrics,
    score_baseline,
    train_bce_head,
    train_pairwise_head,
    train_repair_head,
)
from civic_prm.default_paths import DEFAULT_BASE_BENCHMARK_DATASET
from civic_prm.downstream import compute_selection_metrics
from civic_prm.frozen_backbone import encode_texts, load_encoder
from civic_prm.splits import build_quartet_split_map
from civic_prm.text_views import build_view_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Week 6 seed reproduction and paired bootstrap CI on the main comparison set."
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
        "--reranker-artifact",
        type=Path,
        default=Path("artifacts/week4/qwen3_reranker_8b_full_hybrid_natural.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/week6/week6_reproduction.json"),
    )
    parser.add_argument(
        "--feature-cache-dir",
        type=Path,
        default=Path("artifacts/week6/features"),
    )
    parser.add_argument("--seed-list", type=int, nargs="+", default=[17, 23, 31])
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--bootstrap-samples", type=int, default=2000)
    parser.add_argument("--bootstrap-seed", type=int, default=123)
    parser.add_argument("--lambda-grid", type=float, nargs="+", default=[0.1, 0.25, 0.5, 1.0, 2.0])
    return parser.parse_args()


def _labels(records: list[dict]) -> torch.Tensor:
    return torch.tensor([float(record["is_valid_process"]) for record in records], dtype=torch.float32)


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


def _selection_metric(metrics: dict) -> float:
    ordinary_auroc = 0.5 if math.isnan(metrics["ordinary_auroc"]) else metrics["ordinary_auroc"]
    amcd = 0.0 if math.isnan(metrics["amcd"]) else metrics["amcd"]
    ass_total = 0.0 if math.isnan(metrics["ass_total"]) else metrics["ass_total"]
    return amcd - ass_total + 0.05 * ordinary_auroc


def _sanitize_utility(metrics: dict) -> dict:
    return {key: value for key, value in metrics.items() if key != "quartet_rows"}


def _fit_cond_swap(
    train_features: torch.Tensor,
    train_records: list[dict],
    val_features: torch.Tensor,
    val_records: list[dict],
    eval_features: torch.Tensor,
    eval_records: list[dict],
    lambda_grid: list[float],
    seed: int,
) -> dict:
    train_labels = _labels(train_records)
    val_labels = _labels(val_records)
    best_payload = None
    search_rows = []
    for lambda_cond_swap in lambda_grid:
        torch.manual_seed(seed)
        model_head = train_repair_head(
            train_features=train_features,
            train_records=train_records,
            train_labels=train_labels,
            val_features=val_features,
            val_records=val_records,
            val_labels=val_labels,
            lambda_local_pair=0.0,
            lambda_cond_swap=lambda_cond_swap,
        )
        val_rows = score_baseline(
            model=model_head,
            train_features=train_features,
            eval_features=val_features,
            eval_records=val_records,
        )
        val_metrics = compute_verifier_metrics(val_rows)
        selection = _selection_metric(val_metrics)
        search_rows.append(
            {
                "lambda_cond_swap": lambda_cond_swap,
                "selection_metric": round(selection, 4),
                "val_metrics": val_metrics,
            }
        )
        if best_payload is None or selection > best_payload["selection_metric"]:
            best_payload = {
                "selection_metric": selection,
                "model_head": model_head,
                "lambda_cond_swap": lambda_cond_swap,
                "val_metrics": val_metrics,
            }
    assert best_payload is not None
    eval_rows = score_baseline(
        model=best_payload["model_head"],
        train_features=train_features,
        eval_features=eval_features,
        eval_records=eval_records,
    )
    return {
        "selected_lambda_cond_swap": best_payload["lambda_cond_swap"],
        "selected_val_metrics": best_payload["val_metrics"],
        "grid_search": search_rows,
        "rows": eval_rows,
        "metrics": compute_verifier_metrics(eval_rows),
        "utility": _sanitize_utility(compute_selection_metrics(eval_rows)),
    }


def _average_rows(row_sets: list[list[dict]]) -> list[dict]:
    if not row_sets:
        return []
    base = row_sets[0]
    for row_set in row_sets[1:]:
        if [row["trace_id"] for row in row_set] != [row["trace_id"] for row in base]:
            raise ValueError("row sets do not share the same trace_id order")
    averaged = []
    for index in range(len(base)):
        template = dict(base[index])
        template["score"] = sum(row_set[index]["score"] for row_set in row_sets) / len(row_sets)
        if "logit" in template:
            template["logit"] = sum(row_set[index].get("logit", 0.0) for row_set in row_sets) / len(row_sets)
        averaged.append(template)
    return averaged


def _metric_value(rows: list[dict], metric_name: str) -> float:
    if metric_name in {"ordinary_auroc", "amcd", "ass_total"}:
        return compute_verifier_metrics(rows)[metric_name]
    utility = compute_selection_metrics(rows)
    return utility[metric_name]


def _paired_bootstrap(
    rows_a: list[dict],
    rows_b: list[dict],
    metric_name: str,
    num_samples: int,
    seed: int,
) -> dict:
    grouped_a = {}
    grouped_b = {}
    for row in rows_a:
        grouped_a.setdefault(row["quartet_id"], []).append(row)
    for row in rows_b:
        grouped_b.setdefault(row["quartet_id"], []).append(row)
    quartet_ids = sorted(set(grouped_a) & set(grouped_b))
    rng = random.Random(seed)
    diffs = []
    for _ in range(num_samples):
        sampled_ids = [rng.choice(quartet_ids) for _ in quartet_ids]
        sampled_a = []
        sampled_b = []
        for quartet_id in sampled_ids:
            sampled_a.extend(grouped_a[quartet_id])
            sampled_b.extend(grouped_b[quartet_id])
        diffs.append(_metric_value(sampled_a, metric_name) - _metric_value(sampled_b, metric_name))
    diffs.sort()
    low_index = int(0.025 * len(diffs))
    high_index = int(0.975 * len(diffs))
    observed = _metric_value(rows_a, metric_name) - _metric_value(rows_b, metric_name)
    return {
        "metric": metric_name,
        "observed_diff": round(observed, 4),
        "ci_low": round(diffs[low_index], 4),
        "ci_high": round(diffs[min(high_index, len(diffs) - 1)], 4),
        "bootstrap_win_rate": round(sum(diff > 0 for diff in diffs) / len(diffs), 4),
    }


def _load_reranker_rows(path: Path, view_name: str) -> list[dict]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    return obj["views"][view_name]["rows"]


def main() -> None:
    args = parse_args()
    train_records = load_records(args.train_dataset)
    eval_records = load_records(args.eval_dataset)

    tokenizer, encoder = load_encoder(args.model_root)
    view_records = {
        "visible": {
            "train_features": _load_or_extract_features(
                train_records,
                "visible",
                tokenizer,
                encoder,
                args.feature_cache_dir / "train_visible.pt",
                args.batch_size,
                args.max_length,
            ),
            "eval_features": _load_or_extract_features(
                eval_records,
                "visible",
                tokenizer,
                encoder,
                args.feature_cache_dir / "eval_visible.pt",
                args.batch_size,
                args.max_length,
            ),
        },
        "masked": {
            "train_features": _load_or_extract_features(
                train_records,
                "masked",
                tokenizer,
                encoder,
                args.feature_cache_dir / "train_masked.pt",
                args.batch_size,
                args.max_length,
            ),
            "eval_features": _load_or_extract_features(
                eval_records,
                "masked",
                tokenizer,
                encoder,
                args.feature_cache_dir / "eval_masked.pt",
                args.batch_size,
                args.max_length,
            ),
        },
    }

    seed_runs = []
    model_rows_by_seed = {
        "visible_bce": [],
        "masked_bce": [],
        "pairwise_visible": [],
        "visible_cond_swap": [],
    }

    for seed in args.seed_list:
        split_map = build_quartet_split_map(train_records, seed=seed)
        train_rows, val_rows = _slice_train_val(train_records, split_map)

        visible_train_indices = [index for index, record in enumerate(train_records) if split_map[record["quartet_id"]] == "train"]
        visible_val_indices = [index for index, record in enumerate(train_records) if split_map[record["quartet_id"]] == "val"]
        masked_train_indices = visible_train_indices
        masked_val_indices = visible_val_indices

        visible_train_features = view_records["visible"]["train_features"][visible_train_indices]
        visible_val_features = view_records["visible"]["train_features"][visible_val_indices]
        visible_eval_features = view_records["visible"]["eval_features"]

        masked_train_features = view_records["masked"]["train_features"][masked_train_indices]
        masked_val_features = view_records["masked"]["train_features"][masked_val_indices]
        masked_eval_features = view_records["masked"]["eval_features"]

        torch.manual_seed(seed)
        visible_bce_head = train_bce_head(
            train_features=visible_train_features,
            train_labels=_labels(train_rows),
            val_features=visible_val_features,
            val_labels=_labels(val_rows),
        )
        visible_bce_rows = score_baseline(
            model=visible_bce_head,
            train_features=visible_train_features,
            eval_features=visible_eval_features,
            eval_records=eval_records,
        )

        torch.manual_seed(seed)
        masked_bce_head = train_bce_head(
            train_features=masked_train_features,
            train_labels=_labels(train_rows),
            val_features=masked_val_features,
            val_labels=_labels(val_rows),
        )
        masked_bce_rows = score_baseline(
            model=masked_bce_head,
            train_features=masked_train_features,
            eval_features=masked_eval_features,
            eval_records=eval_records,
        )

        torch.manual_seed(seed)
        pairwise_head = train_pairwise_head(
            train_features=visible_train_features,
            train_records=train_rows,
            val_features=visible_val_features,
            val_records=val_rows,
        )
        pairwise_rows = score_baseline(
            model=pairwise_head,
            train_features=visible_train_features,
            eval_features=visible_eval_features,
            eval_records=eval_records,
        )

        cond_swap_payload = _fit_cond_swap(
            train_features=visible_train_features,
            train_records=train_rows,
            val_features=visible_val_features,
            val_records=val_rows,
            eval_features=visible_eval_features,
            eval_records=eval_records,
            lambda_grid=args.lambda_grid,
            seed=seed,
        )

        seed_payload = {
            "seed": seed,
            "models": {
                "visible_bce": {
                    "metrics": compute_verifier_metrics(visible_bce_rows),
                    "utility": _sanitize_utility(compute_selection_metrics(visible_bce_rows)),
                },
                "masked_bce": {
                    "metrics": compute_verifier_metrics(masked_bce_rows),
                    "utility": _sanitize_utility(compute_selection_metrics(masked_bce_rows)),
                },
                "pairwise_visible": {
                    "metrics": compute_verifier_metrics(pairwise_rows),
                    "utility": _sanitize_utility(compute_selection_metrics(pairwise_rows)),
                },
                "visible_cond_swap": {
                    "selected_lambda_cond_swap": cond_swap_payload["selected_lambda_cond_swap"],
                    "selected_val_metrics": cond_swap_payload["selected_val_metrics"],
                    "metrics": cond_swap_payload["metrics"],
                    "utility": cond_swap_payload["utility"],
                },
            },
        }
        seed_runs.append(seed_payload)
        model_rows_by_seed["visible_bce"].append(visible_bce_rows)
        model_rows_by_seed["masked_bce"].append(masked_bce_rows)
        model_rows_by_seed["pairwise_visible"].append(pairwise_rows)
        model_rows_by_seed["visible_cond_swap"].append(cond_swap_payload["rows"])

    aggregated_models = {}
    for model_name, row_sets in model_rows_by_seed.items():
        averaged_rows = _average_rows(row_sets)
        aggregated_models[model_name] = {
            "seed_metrics": [
                {
                    "seed": run["seed"],
                    "metrics": run["models"][model_name]["metrics"],
                    "utility": run["models"][model_name]["utility"],
                    **(
                        {"selected_lambda_cond_swap": run["models"][model_name]["selected_lambda_cond_swap"]}
                        if model_name == "visible_cond_swap"
                        else {}
                    ),
                }
                for run in seed_runs
            ],
            "mean_rows": averaged_rows,
            "mean_metrics": compute_verifier_metrics(averaged_rows),
            "mean_utility": _sanitize_utility(compute_selection_metrics(averaged_rows)),
        }

    reranker_models = {
        "reranker8_visible": {
            "mean_rows": _load_reranker_rows(args.reranker_artifact, "visible"),
        },
        "reranker8_masked": {
            "mean_rows": _load_reranker_rows(args.reranker_artifact, "masked"),
        },
    }
    for model_name, payload in reranker_models.items():
        payload["mean_metrics"] = compute_verifier_metrics(payload["mean_rows"])
        payload["mean_utility"] = _sanitize_utility(compute_selection_metrics(payload["mean_rows"]))

    comparisons = [
        ("reranker8_masked", "reranker8_visible"),
        ("reranker8_masked", "visible_bce"),
        ("reranker8_masked", "masked_bce"),
        ("reranker8_masked", "pairwise_visible"),
        ("reranker8_masked", "visible_cond_swap"),
    ]
    metric_names = ["ordinary_auroc", "amcd", "ass_total", "selection_gain_at4", "exploitability_rate"]
    comparison_payload = {}
    all_models = {**aggregated_models, **reranker_models}
    for left_name, right_name in comparisons:
        comparison_key = f"{left_name}__vs__{right_name}"
        comparison_payload[comparison_key] = {}
        for metric_name in metric_names:
            comparison_payload[comparison_key][metric_name] = _paired_bootstrap(
                all_models[left_name]["mean_rows"],
                all_models[right_name]["mean_rows"],
                metric_name=metric_name,
                num_samples=args.bootstrap_samples,
                seed=args.bootstrap_seed,
            )

    output = {
        "config": {
            "train_dataset": str(args.train_dataset),
            "eval_dataset": str(args.eval_dataset),
            "model_root": str(args.model_root),
            "reranker_artifact": str(args.reranker_artifact),
            "seed_list": args.seed_list,
            "bootstrap_samples": args.bootstrap_samples,
            "bootstrap_seed": args.bootstrap_seed,
        },
        "seed_runs": seed_runs,
        "aggregated_models": {
            name: {
                key: value
                for key, value in payload.items()
                if key != "mean_rows"
            }
            for name, payload in aggregated_models.items()
        },
        "reranker_models": {
            name: {
                key: value
                for key, value in payload.items()
                if key != "mean_rows"
            }
            for name, payload in reranker_models.items()
        },
        "paired_bootstrap": comparison_payload,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "aggregated_models": {
                    name: {
                        "ordinary_auroc": payload["mean_metrics"]["ordinary_auroc"],
                        "amcd": payload["mean_metrics"]["amcd"],
                        "ass_total": payload["mean_metrics"]["ass_total"],
                        "selection_gain_at4": payload["mean_utility"]["selection_gain_at4"],
                        "exploitability_rate": payload["mean_utility"]["exploitability_rate"],
                    }
                    for name, payload in {**aggregated_models, **reranker_models}.items()
                }
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
