from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from civic_prm.audit import load_records
from civic_prm.baselines import compute_verifier_metrics, score_baseline, train_bce_head, train_pairwise_head
from civic_prm.default_paths import DEFAULT_BASE_BENCHMARK_DATASET
from civic_prm.frozen_backbone import encode_texts, load_encoder
from civic_prm.splits import build_quartet_split_map
from civic_prm.text_views import build_view_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train on synthetic hard data and evaluate on a naturalized test slice.")
    parser.add_argument(
        "--train-dataset",
        type=Path,
        default=DEFAULT_BASE_BENCHMARK_DATASET,
    )
    parser.add_argument(
        "--eval-dataset",
        type=Path,
        default=Path("data/generated/craft_core_hard_natural_test.jsonl"),
    )
    parser.add_argument(
        "--model-root",
        type=Path,
        default=Path("/cephfs/shared/hf_cache/hub/models--Qwen--Qwen3-1.7B/snapshots"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/natural/natural_transfer_baselines.json"),
    )
    parser.add_argument(
        "--feature-cache-dir",
        type=Path,
        default=Path("artifacts/natural/features"),
    )
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--seed", type=int, default=17)
    return parser.parse_args()


def _labels(records: list[dict]) -> torch.Tensor:
    return torch.tensor([float(record["is_valid_process"]) for record in records], dtype=torch.float32)


def _load_or_extract_features(records, view_name, tokenizer, model, cache_path, batch_size, max_length):
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


def main() -> None:
    args = parse_args()
    torch.manual_seed(args.seed)
    train_records = load_records(args.train_dataset)
    eval_records = load_records(args.eval_dataset)
    split_map = build_quartet_split_map(train_records, seed=args.seed)
    train_rows, val_rows = _slice_train_val(train_records, split_map)

    tokenizer, model = load_encoder(args.model_root)
    baseline_specs = [
        ("step_only_bce", "step_only", "bce"),
        ("visible_bce", "visible", "bce"),
        ("masked_bce", "masked", "bce"),
        ("pairwise_visible", "visible", "pairwise"),
    ]
    outputs = {
        "config": {
            "train_dataset": str(args.train_dataset),
            "eval_dataset": str(args.eval_dataset),
            "model_root": str(args.model_root),
            "seed": args.seed,
        },
        "baselines": {},
    }

    for baseline_name, view_name, objective in baseline_specs:
        train_features = _load_or_extract_features(
            train_rows,
            view_name,
            tokenizer,
            model,
            args.feature_cache_dir / f"train_{view_name}.pt",
            args.batch_size,
            args.max_length,
        )
        val_features = _load_or_extract_features(
            val_rows,
            view_name,
            tokenizer,
            model,
            args.feature_cache_dir / f"val_{view_name}.pt",
            args.batch_size,
            args.max_length,
        )
        eval_features = _load_or_extract_features(
            eval_records,
            view_name,
            tokenizer,
            model,
            args.feature_cache_dir / f"eval_{view_name}.pt",
            args.batch_size,
            args.max_length,
        )

        torch.manual_seed(args.seed)
        if objective == "bce":
            model_head = train_bce_head(
                train_features=train_features,
                train_labels=_labels(train_rows),
                val_features=val_features,
                val_labels=_labels(val_rows),
            )
        else:
            model_head = train_pairwise_head(
                train_features=train_features,
                train_records=train_rows,
                val_features=val_features,
                val_records=val_rows,
            )

        test_rows = score_baseline(
            model=model_head,
            train_features=train_features,
            eval_features=eval_features,
            eval_records=eval_records,
        )
        outputs["baselines"][baseline_name] = {
            "view_name": view_name,
            "objective": objective,
            "metrics": compute_verifier_metrics(test_rows),
            "test_rows": test_rows,
        }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(outputs, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {name: payload["metrics"] for name, payload in outputs["baselines"].items()},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
