from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import torch

from civic_prm.audit import load_records
from civic_prm.baselines import (
    compute_verifier_metrics,
    score_baseline,
    train_bce_head,
    train_pairwise_head,
)
from civic_prm.default_paths import DEFAULT_BASE_BENCHMARK_DATASET
from civic_prm.frozen_backbone import encode_texts, load_encoder
from civic_prm.splits import build_quartet_split_map, extract_verbalizer_slot, list_verbalizer_slots
from civic_prm.text_views import build_view_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Week 2 frozen-backbone baselines.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_BASE_BENCHMARK_DATASET,
    )
    parser.add_argument(
        "--model-root",
        type=Path,
        default=Path("/cephfs/shared/hf_cache/hub/models--Qwen--Qwen3-1.7B/snapshots"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/baselines/week2_baselines.json"),
    )
    parser.add_argument(
        "--feature-cache-dir",
        type=Path,
        default=Path("artifacts/features"),
    )
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--seed", type=int, default=17)
    return parser.parse_args()


def _attach_splits(records: list[dict], split_map: dict[str, str]) -> list[dict]:
    enriched = []
    for record in records:
        cloned = dict(record)
        cloned["split"] = split_map[record["quartet_id"]]
        enriched.append(cloned)
    return enriched


def _load_or_extract_features(
    records: list[dict],
    view_name: str,
    tokenizer,
    model,
    cache_dir: Path,
    batch_size: int,
    max_length: int,
) -> torch.Tensor:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{view_name}_features.pt"
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


def _run_single_baseline(
    baseline_name: str,
    view_name: str,
    objective: str,
    features: torch.Tensor,
    train_records: list[dict],
    val_records: list[dict],
    test_records: list[dict],
    seed: int,
) -> dict:
    train_indices = [record["_row_index"] for record in train_records]
    val_indices = [record["_row_index"] for record in val_records]
    test_indices = [record["_row_index"] for record in test_records]

    train_features = features[train_indices]
    val_features = features[val_indices]
    test_features = features[test_indices]

    torch.manual_seed(seed)
    if objective == "bce":
        model_head = train_bce_head(
            train_features=train_features,
            train_labels=_labels(train_records),
            val_features=val_features,
            val_labels=_labels(val_records),
        )
    else:
        model_head = train_pairwise_head(
            train_features=train_features,
            train_records=train_records,
            val_features=val_features,
            val_records=val_records,
        )

    test_rows = score_baseline(
        model=model_head,
        train_features=train_features,
        eval_features=test_features,
        eval_records=test_records,
    )
    return {
        "view_name": view_name,
        "objective": objective,
        "metrics": compute_verifier_metrics(test_rows),
        "test_rows": test_rows,
    }


def _round_nested(value):
    if isinstance(value, float):
        return round(value, 4)
    if isinstance(value, dict):
        return {key: _round_nested(val) for key, val in value.items()}
    return value


def _mean_dict(dicts: list[dict]) -> dict:
    if not dicts:
        return {}
    result = {}
    keys = set()
    for item in dicts:
        keys.update(item.keys())
    for key in keys:
        values = [item[key] for item in dicts if key in item]
        if not values:
            continue
        first = values[0]
        if isinstance(first, dict):
            result[key] = _mean_dict(values)
        elif isinstance(first, (int, float)):
            result[key] = sum(values) / len(values)
        else:
            result[key] = first
    return _round_nested(result)


def main() -> None:
    args = parse_args()
    raw_records = load_records(args.dataset)
    split_map = build_quartet_split_map(raw_records, seed=args.seed)
    records = _attach_splits(raw_records, split_map)
    for index, record in enumerate(records):
        record["_row_index"] = index
        record["verbalizer_slot"] = extract_verbalizer_slot(record["verbalizer_id"])

    tokenizer, model = load_encoder(args.model_root)
    feature_sets = {}
    for view_name in ["visible", "masked", "step_only"]:
        feature_sets[view_name] = _load_or_extract_features(
            records,
            view_name=view_name,
            tokenizer=tokenizer,
            model=model,
            cache_dir=args.feature_cache_dir,
            batch_size=args.batch_size,
            max_length=args.max_length,
        )

    split_summary = Counter(record["split"] for record in records)
    quartet_summary = Counter(split_map.values())
    outputs = {
        "config": {
            "dataset": str(args.dataset),
            "model_root": str(args.model_root),
            "batch_size": args.batch_size,
            "max_length": args.max_length,
            "seed": args.seed,
        },
        "split_summary": dict(split_summary),
        "quartet_split_summary": dict(quartet_summary),
        "protocols": {},
    }

    baseline_specs = [
        ("step_only_bce", "step_only", "bce"),
        ("visible_bce", "visible", "bce"),
        ("masked_bce", "masked", "bce"),
        ("pairwise_visible", "visible", "pairwise"),
    ]

    quartet_protocol = {"baselines": {}}
    for baseline_name, view_name, objective in baseline_specs:
        _, train_records = _slice_split(feature_sets[view_name], records, "train")
        _, val_records = _slice_split(feature_sets[view_name], records, "val")
        _, test_records = _slice_split(feature_sets[view_name], records, "test")
        quartet_protocol["baselines"][baseline_name] = _run_single_baseline(
            baseline_name=baseline_name,
            view_name=view_name,
            objective=objective,
            features=feature_sets[view_name],
            train_records=train_records,
            val_records=val_records,
            test_records=test_records,
            seed=args.seed,
        )
    outputs["protocols"]["quartet"] = quartet_protocol

    holdout_protocol = {
        "holdout_slots": {},
        "baselines": {},
    }
    verbalizer_slots = list_verbalizer_slots(records)
    for slot_index, holdout_slot in enumerate(verbalizer_slots):
        slot_payload = {"baselines": {}}
        train_records = [
            record for record in records
            if record["split"] == "train" and record["verbalizer_slot"] != holdout_slot
        ]
        val_records = [
            record for record in records
            if record["split"] == "val" and record["verbalizer_slot"] != holdout_slot
        ]
        test_records = [
            record for record in records
            if record["split"] == "test" and record["verbalizer_slot"] == holdout_slot
        ]
        slot_payload["split_summary"] = {
            "train": len(train_records),
            "val": len(val_records),
            "test": len(test_records),
        }
        for baseline_name, view_name, objective in baseline_specs:
            slot_payload["baselines"][baseline_name] = _run_single_baseline(
                baseline_name=baseline_name,
                view_name=view_name,
                objective=objective,
                features=feature_sets[view_name],
                train_records=train_records,
                val_records=val_records,
                test_records=test_records,
                seed=args.seed + slot_index + 1,
            )
        holdout_protocol["holdout_slots"][holdout_slot] = slot_payload

    for baseline_name, _, _ in baseline_specs:
        holdout_protocol["baselines"][baseline_name] = {
            "metrics": _mean_dict(
                [
                    holdout_protocol["holdout_slots"][slot]["baselines"][baseline_name]["metrics"]
                    for slot in verbalizer_slots
                ]
            )
        }
    outputs["protocols"]["verbalizer_holdout"] = holdout_protocol

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(outputs, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "split_summary": outputs["split_summary"],
                "quartet_split_summary": outputs["quartet_split_summary"],
                "protocols": {
                    protocol_name: {
                        "baselines": {
                            name: payload["metrics"]
                            for name, payload in protocol_payload["baselines"].items()
                        }
                    }
                    for protocol_name, protocol_payload in outputs["protocols"].items()
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
