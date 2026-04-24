from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

import torch

from civic_prm.audit import load_records
from civic_prm.baselines import score_baseline, train_bce_head
from civic_prm.frozen_backbone import encode_texts, load_encoder
from civic_prm.processbench_eval import compute_processbench_metrics, compute_processbench_prefix_metrics
from civic_prm.text_views import build_view_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run frozen-backbone baselines on ProcessBench trace and prefix benchmarks.")
    parser.add_argument("--trace-dataset", type=Path, default=Path("data/external/processbench_eval_all.jsonl"))
    parser.add_argument("--prefix-dataset", type=Path, default=Path("data/external/processbench_prefix_eval_all.jsonl"))
    parser.add_argument(
        "--model-root",
        type=Path,
        default=Path("/cephfs/shared/hf_cache/hub/models--Qwen--Qwen3-1.7B/snapshots"),
    )
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--prefix-source-limit-per-domain", type=int, default=200)
    parser.add_argument("--feature-cache-dir", type=Path, default=Path("artifacts/features_processbench"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/external_datasets/processbench_frozen_baselines.json"),
    )
    return parser.parse_args()


def _group_id(record: dict) -> str:
    return str(record.get("metadata", {}).get("source_trace_id") or record.get("metadata", {}).get("source_example_id") or record["trace_id"])


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


def _limit_prefix_records(records: list[dict], per_domain: int | None, seed: int) -> list[dict]:
    if per_domain is None:
        return records
    rng = random.Random(seed)
    groups_by_domain: dict[str, list[str]] = defaultdict(list)
    group_to_records: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        group_id = _group_id(record)
        if group_id not in group_to_records:
            groups_by_domain[record["domain"]].append(group_id)
        group_to_records[group_id].append(record)
    selected_records: list[dict] = []
    for domain in sorted(groups_by_domain):
        group_ids = sorted(groups_by_domain[domain])
        rng.shuffle(group_ids)
        for group_id in group_ids[:per_domain]:
            selected_records.extend(group_to_records[group_id])
    return selected_records


def _load_or_extract_features(
    records: list[dict],
    dataset_tag: str,
    view_name: str,
    tokenizer,
    model,
    cache_dir: Path,
    batch_size: int,
    max_length: int,
) -> torch.Tensor:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{dataset_tag}_{view_name}_features.pt"
    if cache_path.exists():
        payload = torch.load(cache_path)
        if payload.get("trace_ids") == [record["trace_id"] for record in records]:
            return payload["features"]
    texts = [build_view_text(record, view_name=view_name) for record in records]
    features = encode_texts(
        texts,
        tokenizer=tokenizer,
        model=model,
        batch_size=batch_size,
        max_length=max_length,
    )
    torch.save(
        {
            "dataset_tag": dataset_tag,
            "view_name": view_name,
            "trace_ids": [record["trace_id"] for record in records],
            "features": features,
        },
        cache_path,
    )
    return features


def _slice_split(features: torch.Tensor, records: list[dict], split_name: str):
    indices = [index for index, record in enumerate(records) if record["split"] == split_name]
    selected_features = features[indices]
    selected_records = [records[index] for index in indices]
    return selected_features, selected_records


def _labels(records: list[dict]) -> torch.Tensor:
    return torch.tensor([float(record["is_valid_process"]) for record in records], dtype=torch.float32)


def _run_single_bce(
    dataset_name: str,
    view_name: str,
    features: torch.Tensor,
    records: list[dict],
    seed: int,
) -> dict:
    train_features, train_records = _slice_split(features, records, "train")
    val_features, val_records = _slice_split(features, records, "val")
    test_features, test_records = _slice_split(features, records, "test")

    torch.manual_seed(seed)
    model_head = train_bce_head(
        train_features=train_features,
        train_labels=_labels(train_records),
        val_features=val_features,
        val_labels=_labels(val_records),
    )
    test_rows = score_baseline(
        model=model_head,
        train_features=train_features,
        eval_features=test_features,
        eval_records=test_records,
    )
    by_trace_id = {record["trace_id"]: record for record in test_records}
    enriched_rows = []
    for row in test_rows:
        record = by_trace_id[row["trace_id"]]
        enriched_rows.append(
            {
                **row,
                "source_trace_id": record.get("metadata", {}).get("source_trace_id"),
                "source_prefix_length": record.get("metadata", {}).get("source_prefix_length"),
                "first_incorrect_step": record.get("metadata", {}).get("first_incorrect_step"),
            }
        )
    metrics = (
        compute_processbench_prefix_metrics(enriched_rows)
        if dataset_name == "prefix"
        else compute_processbench_metrics(enriched_rows)
    )
    return {
        "view_name": view_name,
        "metrics": metrics,
        "num_train": len(train_records),
        "num_val": len(val_records),
        "num_test": len(test_records),
    }


def _split_summary(records: list[dict]) -> dict[str, int]:
    return dict(Counter(record["split"] for record in records))


def main() -> None:
    args = parse_args()
    trace_records = _attach_group_splits(load_records(args.trace_dataset), seed=args.seed)
    prefix_records = load_records(args.prefix_dataset)
    prefix_records = _limit_prefix_records(
        prefix_records,
        per_domain=args.prefix_source_limit_per_domain,
        seed=args.seed,
    )
    prefix_records = _attach_group_splits(prefix_records, seed=args.seed)

    tokenizer, model = load_encoder(args.model_root)

    trace_outputs = {}
    prefix_outputs = {}
    for dataset_name, records, output_map in [
        ("trace", trace_records, trace_outputs),
        ("prefix", prefix_records, prefix_outputs),
    ]:
        for view_name in ["visible", "masked", "step_only"]:
            features = _load_or_extract_features(
                records=records,
                dataset_tag=f"processbench_{dataset_name}",
                view_name=view_name,
                tokenizer=tokenizer,
                model=model,
                cache_dir=args.feature_cache_dir,
                batch_size=args.batch_size,
                max_length=args.max_length,
            )
            output_map[view_name] = _run_single_bce(
                dataset_name=dataset_name,
                view_name=view_name,
                features=features,
                records=records,
                seed=args.seed,
            )

    summary = {
        "config": {
            "trace_dataset": str(args.trace_dataset),
            "prefix_dataset": str(args.prefix_dataset),
            "model_root": str(args.model_root),
            "batch_size": args.batch_size,
            "max_length": args.max_length,
            "seed": args.seed,
            "prefix_source_limit_per_domain": args.prefix_source_limit_per_domain,
        },
        "trace_split_summary": _split_summary(trace_records),
        "prefix_split_summary": _split_summary(prefix_records),
        "trace": trace_outputs,
        "prefix": prefix_outputs,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
