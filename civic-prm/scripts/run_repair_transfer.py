from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from civic_prm.audit import load_records
from civic_prm.baselines import (
    compute_verifier_metrics,
    mine_hard_negative_indices,
    score_baseline,
    train_bce_head,
    train_pairwise_head,
    train_repair_head,
)
from civic_prm.default_paths import DEFAULT_BASE_BENCHMARK_DATASET
from civic_prm.frozen_backbone import encode_texts, load_encoder
from civic_prm.splits import build_quartet_split_map
from civic_prm.text_views import build_view_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train minimal repair variants on synthetic hard data and evaluate on an OOD generated slice."
    )
    parser.add_argument(
        "--train-dataset",
        type=Path,
        default=DEFAULT_BASE_BENCHMARK_DATASET,
    )
    parser.add_argument(
        "--eval-dataset",
        type=Path,
        default=Path("data/generated/craft_core_hard_model_generated_full_hybrid_counterfactual_v2.jsonl"),
    )
    parser.add_argument(
        "--model-root",
        type=Path,
        default=Path("/cephfs/shared/hf_cache/hub/models--Qwen--Qwen3-1.7B/snapshots"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/generated/model_generated_full_hybrid_counterfactual_v2_repair.json"),
    )
    parser.add_argument(
        "--feature-cache-dir",
        type=Path,
        default=Path("artifacts/generated/full_hybrid_repair_features_v1"),
    )
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument(
        "--lambda-grid",
        type=float,
        nargs="+",
        default=[0.1, 0.25, 0.5, 1.0, 2.0],
    )
    parser.add_argument("--hard-neg-top-fraction", type=float, default=0.25)
    parser.add_argument("--hard-neg-min-count", type=int, default=8)
    parser.add_argument("--blocksworld-focus-fraction", type=float, default=0.5)
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
    ordinary_auroc = metrics["ordinary_auroc"]
    amcd = metrics["amcd"]
    ass_total = metrics["ass_total"]
    ordinary_auroc = 0.5 if ordinary_auroc != ordinary_auroc else ordinary_auroc
    amcd = 0.0 if amcd != amcd else amcd
    ass_total = 0.0 if ass_total != ass_total else ass_total
    return amcd - ass_total + 0.05 * ordinary_auroc


def _run_baseline(
    objective: str,
    view_name: str,
    train_features: torch.Tensor,
    train_records: list[dict],
    val_features: torch.Tensor,
    val_records: list[dict],
    eval_features: torch.Tensor,
    eval_records: list[dict],
    seed: int,
) -> dict:
    torch.manual_seed(seed)
    if objective == "bce":
        model_head = train_bce_head(
            train_features=train_features,
            train_labels=_labels(train_records),
            val_features=val_features,
            val_labels=_labels(val_records),
        )
    elif objective == "pairwise":
        model_head = train_pairwise_head(
            train_features=train_features,
            train_records=train_records,
            val_features=val_features,
            val_records=val_records,
        )
    else:
        raise ValueError(f"unsupported objective: {objective}")

    eval_rows = score_baseline(
        model=model_head,
        train_features=train_features,
        eval_features=eval_features,
        eval_records=eval_records,
    )
    return {
        "view_name": view_name,
        "objective": objective,
        "metrics": compute_verifier_metrics(eval_rows),
        "test_rows": eval_rows,
    }


def _fit_repair_variant(
    variant_name: str,
    train_features: torch.Tensor,
    train_records: list[dict],
    val_features: torch.Tensor,
    val_records: list[dict],
    eval_features: torch.Tensor,
    eval_records: list[dict],
    lambda_grid: list[float],
    hard_neg_indices: list[int],
    hard_neg_summary: dict,
    seed: int,
) -> dict:
    if variant_name == "visible_local_pair":
        candidates = [
            {"lambda_local_pair": value, "lambda_cond_swap": 0.0, "lambda_hard_neg": 0.0}
            for value in lambda_grid
        ]
    elif variant_name == "visible_cond_swap":
        candidates = [
            {"lambda_local_pair": 0.0, "lambda_cond_swap": value, "lambda_hard_neg": 0.0}
            for value in lambda_grid
        ]
    elif variant_name == "visible_joint_repair":
        candidates = [
            {"lambda_local_pair": local_value, "lambda_cond_swap": swap_value, "lambda_hard_neg": 0.0}
            for local_value in lambda_grid
            for swap_value in lambda_grid
        ]
    elif variant_name == "visible_hard_neg":
        candidates = [
            {"lambda_local_pair": 0.0, "lambda_cond_swap": 0.0, "lambda_hard_neg": value}
            for value in lambda_grid
        ]
    elif variant_name == "visible_cond_swap_hard_neg":
        candidates = [
            {"lambda_local_pair": 0.0, "lambda_cond_swap": swap_value, "lambda_hard_neg": hard_neg_value}
            for swap_value in lambda_grid
            for hard_neg_value in lambda_grid
        ]
    elif variant_name == "visible_cond_swap_hard_neg_balanced":
        candidates = [
            {"lambda_local_pair": 0.0, "lambda_cond_swap": swap_value, "lambda_hard_neg": hard_neg_value}
            for swap_value in lambda_grid
            for hard_neg_value in lambda_grid
        ]
    elif variant_name == "visible_cond_swap_hard_neg_blocksworld_focus":
        candidates = [
            {"lambda_local_pair": 0.0, "lambda_cond_swap": swap_value, "lambda_hard_neg": hard_neg_value}
            for swap_value in lambda_grid
            for hard_neg_value in lambda_grid
        ]
    else:
        raise ValueError(f"unsupported repair variant: {variant_name}")

    train_labels = _labels(train_records)
    val_labels = _labels(val_records)
    best_payload = None
    search_rows = []
    for candidate in candidates:
        torch.manual_seed(seed)
        model_head = train_repair_head(
            train_features=train_features,
            train_records=train_records,
            train_labels=train_labels,
            val_features=val_features,
            val_records=val_records,
            val_labels=val_labels,
            lambda_local_pair=candidate["lambda_local_pair"],
            lambda_cond_swap=candidate["lambda_cond_swap"],
            lambda_hard_neg=candidate["lambda_hard_neg"],
            hard_neg_indices=hard_neg_indices,
        )
        val_rows = score_baseline(
            model=model_head,
            train_features=train_features,
            eval_features=val_features,
            eval_records=val_records,
        )
        val_metrics = compute_verifier_metrics(val_rows)
        selection = _selection_metric(val_metrics)
        candidate_row = {
            "lambda_local_pair": candidate["lambda_local_pair"],
            "lambda_cond_swap": candidate["lambda_cond_swap"],
            "lambda_hard_neg": candidate["lambda_hard_neg"],
            "selection_metric": round(selection, 4),
            "val_metrics": val_metrics,
        }
        search_rows.append(candidate_row)
        if best_payload is None or selection > best_payload["selection_metric"]:
            best_payload = {
                "selection_metric": selection,
                "model_head": model_head,
                "candidate": candidate,
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
        "view_name": "visible",
        "objective": "repair",
        "selected_hparams": best_payload["candidate"],
        "selected_val_metrics": best_payload["val_metrics"],
        "hard_neg_summary": hard_neg_summary if best_payload["candidate"]["lambda_hard_neg"] > 0 else None,
        "grid_search": search_rows,
        "metrics": compute_verifier_metrics(eval_rows),
        "test_rows": eval_rows,
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
    masked_train = _load_or_extract_features(
        train_rows,
        "masked",
        tokenizer,
        model,
        args.feature_cache_dir / "train_masked.pt",
        args.batch_size,
        args.max_length,
    )
    masked_val = _load_or_extract_features(
        val_rows,
        "masked",
        tokenizer,
        model,
        args.feature_cache_dir / "val_masked.pt",
        args.batch_size,
        args.max_length,
    )
    masked_eval = _load_or_extract_features(
        eval_records,
        "masked",
        tokenizer,
        model,
        args.feature_cache_dir / "eval_masked.pt",
        args.batch_size,
        args.max_length,
    )

    outputs = {
        "config": {
            "train_dataset": str(args.train_dataset),
            "eval_dataset": str(args.eval_dataset),
            "model_root": str(args.model_root),
            "seed": args.seed,
            "lambda_grid": args.lambda_grid,
            "hard_neg_top_fraction": args.hard_neg_top_fraction,
            "hard_neg_min_count": args.hard_neg_min_count,
            "blocksworld_focus_fraction": args.blocksworld_focus_fraction,
        },
        "baselines": {},
        "hard_neg_mining": {},
        "repair_variants": {},
    }
    torch.manual_seed(args.seed)
    visible_bce_head = train_bce_head(
        train_features=visible_train,
        train_labels=_labels(train_rows),
        val_features=visible_val,
        val_labels=_labels(val_rows),
    )
    visible_bce_rows = score_baseline(
        model=visible_bce_head,
        train_features=visible_train,
        eval_features=visible_eval,
        eval_records=eval_records,
    )
    outputs["baselines"]["visible_bce"] = {
        "view_name": "visible",
        "objective": "bce",
        "metrics": compute_verifier_metrics(visible_bce_rows),
        "test_rows": visible_bce_rows,
    }
    hard_neg_profiles = {}
    hard_neg_profiles["global"] = mine_hard_negative_indices(
        model=visible_bce_head,
        train_features=visible_train,
        train_records=train_rows,
        top_fraction=args.hard_neg_top_fraction,
        min_count=args.hard_neg_min_count,
    )
    hard_neg_profiles["domain_balanced"] = mine_hard_negative_indices(
        model=visible_bce_head,
        train_features=visible_train,
        train_records=train_rows,
        top_fraction=args.hard_neg_top_fraction,
        min_count=args.hard_neg_min_count,
        strategy="domain_balanced",
    )
    hard_neg_profiles["blocksworld_focus"] = mine_hard_negative_indices(
        model=visible_bce_head,
        train_features=visible_train,
        train_records=train_rows,
        top_fraction=args.hard_neg_top_fraction,
        min_count=args.hard_neg_min_count,
        strategy="focus_domain",
        focus_domain="blocksworld",
        focus_fraction=args.blocksworld_focus_fraction,
    )
    outputs["hard_neg_mining"] = {
        profile_name: summary for profile_name, (_, summary) in hard_neg_profiles.items()
    }
    outputs["baselines"]["masked_bce"] = _run_baseline(
        objective="bce",
        view_name="masked",
        train_features=masked_train,
        train_records=train_rows,
        val_features=masked_val,
        val_records=val_rows,
        eval_features=masked_eval,
        eval_records=eval_records,
        seed=args.seed,
    )
    outputs["baselines"]["pairwise_visible"] = _run_baseline(
        objective="pairwise",
        view_name="visible",
        train_features=visible_train,
        train_records=train_rows,
        val_features=visible_val,
        val_records=val_rows,
        eval_features=visible_eval,
        eval_records=eval_records,
        seed=args.seed,
    )

    variant_specs = [
        ("visible_local_pair", None),
        ("visible_cond_swap", None),
        ("visible_joint_repair", None),
        ("visible_hard_neg", "global"),
        ("visible_cond_swap_hard_neg", "global"),
        ("visible_cond_swap_hard_neg_balanced", "domain_balanced"),
        ("visible_cond_swap_hard_neg_blocksworld_focus", "blocksworld_focus"),
    ]
    for variant_name, mining_profile in variant_specs:
        if mining_profile is None:
            hard_neg_indices = []
            hard_neg_summary = {}
        else:
            hard_neg_indices, hard_neg_summary = hard_neg_profiles[mining_profile]
        outputs["repair_variants"][variant_name] = _fit_repair_variant(
            variant_name=variant_name,
            train_features=visible_train,
            train_records=train_rows,
            val_features=visible_val,
            val_records=val_rows,
            eval_features=visible_eval,
            eval_records=eval_records,
            lambda_grid=args.lambda_grid,
            hard_neg_indices=hard_neg_indices,
            hard_neg_summary=hard_neg_summary,
            seed=args.seed,
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(outputs, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "baselines": {name: payload["metrics"] for name, payload in outputs["baselines"].items()},
                "repair_variants": {
                    name: {
                        "selected_hparams": payload["selected_hparams"],
                        "metrics": payload["metrics"],
                    }
                    for name, payload in outputs["repair_variants"].items()
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
