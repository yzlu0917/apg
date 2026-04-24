#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Dict, List

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from evaluate_cts_mini import extract_pair_features, index_raw_rows
from extract_boundary_states_smoke import load_jsonl, resolve_layers


def flatten_field(entry: Dict, field: str) -> torch.Tensor:
    layer_items = sorted(entry[field].items(), key=lambda kv: int(kv[0]))
    return torch.cat([tensor.to(torch.float32) for _, tensor in layer_items], dim=0)


def normalize_rows(x: torch.Tensor) -> torch.Tensor:
    return torch.nn.functional.normalize(x, dim=1)


def normalize_vec(x: torch.Tensor) -> torch.Tensor:
    return torch.nn.functional.normalize(x.unsqueeze(0), dim=1)[0]


def vector_cos(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.dot(a, b).item())


def gather_training_matrix(entries: List[Dict], field: str, theorem_id: str) -> Dict[str, torch.Tensor]:
    train_entries = [entry for entry in entries if entry["theorem_id"] != theorem_id]
    pos_entries = [entry for entry in train_entries if int(entry["local_sound"]) == 1]
    neg_entries = [entry for entry in train_entries if int(entry["local_sound"]) == 0]

    pos_x = normalize_rows(torch.stack([flatten_field(entry, field) for entry in pos_entries], dim=0))
    neg_x = normalize_rows(torch.stack([flatten_field(entry, field) for entry in neg_entries], dim=0))

    pos_centroid = normalize_vec(pos_x.mean(dim=0))
    neg_centroid = normalize_vec(neg_x.mean(dim=0))

    return {
        "pos_x": pos_x,
        "neg_x": neg_x,
        "pos_entries": pos_entries,
        "neg_entries": neg_entries,
        "pos_centroid": pos_centroid,
        "neg_centroid": neg_centroid,
    }


def nearest_entry(query: torch.Tensor, matrix: torch.Tensor, entries: List[Dict]) -> Dict:
    sims = torch.mv(matrix, query)
    best_idx = int(torch.argmax(sims).item())
    entry = entries[best_idx]
    return {
        "theorem_id": entry["theorem_id"],
        "step_index": int(entry["step_index"]),
        "step_text": entry["step_text"],
        "local_sound": int(entry["local_sound"]),
        "cosine": float(sims[best_idx].item()),
    }


def compute_geometry(
    source_vec: torch.Tensor,
    variant_vec: torch.Tensor,
    train_geom: Dict[str, torch.Tensor],
) -> Dict:
    src = normalize_vec(source_vec)
    var = normalize_vec(variant_vec)
    pos_centroid = train_geom["pos_centroid"]
    neg_centroid = train_geom["neg_centroid"]

    src_pos = vector_cos(src, pos_centroid)
    src_neg = vector_cos(src, neg_centroid)
    var_pos = vector_cos(var, pos_centroid)
    var_neg = vector_cos(var, neg_centroid)

    return {
        "source_variant_cosine": vector_cos(src, var),
        "source_pos_centroid_cosine": src_pos,
        "source_neg_centroid_cosine": src_neg,
        "variant_pos_centroid_cosine": var_pos,
        "variant_neg_centroid_cosine": var_neg,
        "source_margin": src_pos - src_neg,
        "variant_margin": var_pos - var_neg,
        "margin_drop": (src_pos - src_neg) - (var_pos - var_neg),
        "source_nearest_positive": nearest_entry(src, train_geom["pos_x"], train_geom["pos_entries"]),
        "source_nearest_negative": nearest_entry(src, train_geom["neg_x"], train_geom["neg_entries"]),
        "variant_nearest_positive": nearest_entry(var, train_geom["pos_x"], train_geom["pos_entries"]),
        "variant_nearest_negative": nearest_entry(var, train_geom["neg_x"], train_geom["neg_entries"]),
    }


def find_pair_score(pair_scores: List[Dict], pair_id: str) -> Dict:
    return next(pair for pair in pair_scores if pair["pair_id"] == pair_id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze CTS slice geometry for specific pair ids.")
    parser.add_argument("--train-features", required=True)
    parser.add_argument("--raw-jsonl", required=True)
    parser.add_argument("--cts-panel", required=True)
    parser.add_argument("--eval-json", required=True)
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--pair-id", action="append", dest="pair_ids", required=True)
    parser.add_argument("--layers", default="-1,-8,-16")
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    feature_entries = torch.load(args.train_features, map_location="cpu")
    raw_rows = load_jsonl(Path(args.raw_jsonl))
    raw_index = index_raw_rows(raw_rows)
    panel_rows = load_jsonl(Path(args.cts_panel))
    panel_map = {row["pair_id"]: row for row in panel_rows}
    eval_data = json.load(open(args.eval_json, "r", encoding="utf-8"))

    tokenizer = AutoTokenizer.from_pretrained(args.model_path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        dtype=torch.bfloat16,
        trust_remote_code=True,
        low_cpu_mem_usage=True,
    )
    model.to(args.device)
    model.eval()

    requested_layers = [int(x) for x in args.layers.split(",") if x]
    resolved_layers = resolve_layers(requested_layers, int(model.config.num_hidden_layers))

    results = []
    for pair_id in args.pair_ids:
        row = panel_map[pair_id]
        theorem_id = row["source_theorem_id"]
        raw_row = raw_index[theorem_id]
        pair_features = extract_pair_features(
            model=model,
            tokenizer=tokenizer,
            row=raw_row,
            step_index=row["source_step_index"],
            variant_step=row["variant_step"],
            resolved_layers=resolved_layers,
            device=args.device,
        )
        eval_pair = find_pair_score(eval_data["pairs"], pair_id)

        field_report = {}
        for field in ["h_plus", "delta_h"]:
            train_geom = gather_training_matrix(feature_entries, field, theorem_id)
            field_report[field] = compute_geometry(
                source_vec=flatten_field(pair_features["source"], field),
                variant_vec=flatten_field(pair_features["variant"], field),
                train_geom=train_geom,
            )

        results.append(
            {
                "pair_id": pair_id,
                "source_theorem_id": theorem_id,
                "source_step_index": int(row["source_step_index"]),
                "type": row["type"],
                "flip_family": row.get("flip_family"),
                "flip_subfamily": row.get("flip_subfamily"),
                "source_step": row.get("source_step"),
                "variant_step": row.get("variant_step"),
                "eval_source_scores": eval_pair["source_scores"],
                "eval_variant_scores": eval_pair["variant_scores"],
                "geometry": field_report,
            }
        )

    output = {
        "train_features": args.train_features,
        "raw_jsonl": args.raw_jsonl,
        "cts_panel": args.cts_panel,
        "eval_json": args.eval_json,
        "model_path": args.model_path,
        "resolved_layers": resolved_layers,
        "pair_ids": args.pair_ids,
        "results": results,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
