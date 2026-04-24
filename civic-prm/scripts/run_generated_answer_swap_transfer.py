from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from civic_prm.audit import load_records
from civic_prm.baselines import score_baseline, train_bce_head
from civic_prm.default_paths import DEFAULT_BASE_BENCHMARK_DATASET
from civic_prm.deployment_eval import compute_swap_metrics
from civic_prm.frozen_backbone import encode_texts, load_encoder
from civic_prm.splits import build_quartet_split_map
from civic_prm.text_views import build_view_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score model-generated traces with trained visible/masked heads.")
    parser.add_argument(
        "--train-dataset",
        type=Path,
        default=DEFAULT_BASE_BENCHMARK_DATASET,
    )
    parser.add_argument(
        "--eval-dataset",
        type=Path,
        default=Path("data/generated/craft_core_hard_model_generated.jsonl"),
    )
    parser.add_argument(
        "--model-root",
        type=Path,
        default=Path("/cephfs/shared/hf_cache/hub/models--Qwen--Qwen3-1.7B/snapshots"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/generated/generated_answer_swap_transfer.json"),
    )
    parser.add_argument(
        "--feature-cache-dir",
        type=Path,
        default=Path("artifacts/generated/features"),
    )
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-length", type=int, default=512)
    return parser.parse_args()


def _labels(records: list[dict]) -> torch.Tensor:
    return torch.tensor([float(record["is_valid_process"]) for record in records], dtype=torch.float32)


def _load_or_extract(records, view_name, tokenizer, model, path, batch_size, max_length):
    if path.exists():
        payload = torch.load(path)
        if payload.get("trace_ids") == [record["trace_id"] for record in records]:
            return payload["features"]
    texts = [build_view_text(record, view_name=view_name) for record in records]
    features = encode_texts(texts, tokenizer=tokenizer, model=model, batch_size=batch_size, max_length=max_length)
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"trace_ids": [record["trace_id"] for record in records], "features": features}, path)
    return features


def main() -> None:
    args = parse_args()
    torch.manual_seed(args.seed)
    train_records = load_records(args.train_dataset)
    eval_records = load_records(args.eval_dataset)
    split_map = build_quartet_split_map(train_records, seed=args.seed)
    train_rows = [record for record in train_records if split_map[record["quartet_id"]] == "train"]
    val_rows = [record for record in train_records if split_map[record["quartet_id"]] == "val"]
    tokenizer, model = load_encoder(args.model_root)

    outputs = {"baselines": {}}
    for view_name in ["visible", "masked"]:
        train_features = _load_or_extract(
            train_rows, view_name, tokenizer, model, args.feature_cache_dir / f"train_{view_name}.pt", args.batch_size, args.max_length
        )
        val_features = _load_or_extract(
            val_rows, view_name, tokenizer, model, args.feature_cache_dir / f"val_{view_name}.pt", args.batch_size, args.max_length
        )
        eval_features = _load_or_extract(
            eval_records, view_name, tokenizer, model, args.feature_cache_dir / f"eval_{view_name}.pt", args.batch_size, args.max_length
        )
        model_head = train_bce_head(
            train_features=train_features,
            train_labels=_labels(train_rows),
            val_features=val_features,
            val_labels=_labels(val_rows),
        )
        scored_rows = score_baseline(
            model=model_head,
            train_features=train_features,
            eval_features=eval_features,
            eval_records=[
                {
                    **record,
                    "is_valid_process": record["answer_is_correct"],
                    "process_variant": record["answer_variant"],
                }
                for record in eval_records
            ],
        )
        for row, record in zip(scored_rows, eval_records, strict=True):
            row["swap_group_id"] = record["swap_group_id"]
            row["answer_variant"] = record["answer_variant"]
            row["answer_is_correct"] = record["answer_is_correct"]
            row["answer_visible"] = view_name == "visible"
        outputs["baselines"][f"{view_name}_bce"] = {
            "metrics": compute_swap_metrics(scored_rows),
            "rows": scored_rows,
        }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(outputs, indent=2), encoding="utf-8")
    print(json.dumps({name: payload["metrics"] for name, payload in outputs["baselines"].items()}, indent=2))


if __name__ == "__main__":
    main()
