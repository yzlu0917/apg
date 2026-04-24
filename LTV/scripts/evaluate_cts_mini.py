#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from extract_boundary_states_smoke import (
    build_prefix,
    encode_last_token_states,
    load_jsonl,
    resolve_layers,
)
from run_object_gate_baselines import (
    build_text_vocabulary,
    concat_fields,
    fit_linear_probe,
    tensor_from_entries,
    vectorize_text,
)


def index_raw_rows(rows: List[Dict]) -> Dict[str, Dict]:
    return {row["theorem_id"]: row for row in rows}


def extract_pair_features(
    model,
    tokenizer,
    row: Dict,
    step_index: int,
    variant_step: str,
    resolved_layers: List[int],
    device: str,
) -> Dict[str, Dict]:
    header = row["header"]
    steps = row["steps"]

    before_text = build_prefix(header, steps, step_index)
    source_after_steps = list(steps)
    variant_after_steps = list(steps)
    variant_after_steps[step_index] = variant_step

    source_after_text = build_prefix(header, source_after_steps, step_index + 1)
    variant_after_text = build_prefix(header, variant_after_steps, step_index + 1)

    before = encode_last_token_states(model, tokenizer, before_text, resolved_layers, device)
    source_after = encode_last_token_states(model, tokenizer, source_after_text, resolved_layers, device)
    variant_after = encode_last_token_states(model, tokenizer, variant_after_text, resolved_layers, device)

    def make_entry(step_text: str, after_obj: Dict) -> Dict:
        h_minus = before["states"]
        h_plus = after_obj["states"]
        delta_h = {layer: (h_plus[layer] - h_minus[layer]) for layer in h_minus}
        return {
            "step_text": step_text,
            "h_minus": h_minus,
            "h_plus": h_plus,
            "delta_h": delta_h,
            "header_token_count": before["seq_len"],
            "after_token_count": after_obj["seq_len"],
        }

    return {
        "source": make_entry(steps[step_index], source_after),
        "variant": make_entry(variant_step, variant_after),
    }


def build_training_tensors(feature_entries: List[Dict], held_out_theorem: str) -> Tuple[List[Dict], torch.Tensor, List[str], List[str]]:
    train_entries = [entry for entry in feature_entries if entry["theorem_id"] != held_out_theorem]
    labels = torch.tensor([entry["local_sound"] for entry in train_entries], dtype=torch.long)
    groups = [entry["theorem_id"] for entry in train_entries]
    step_texts = [entry["step_text"] for entry in train_entries]
    return train_entries, labels, groups, step_texts


def score_text_pair(
    train_step_texts: List[str],
    train_labels: torch.Tensor,
    source_text: str,
    variant_text: str,
) -> Tuple[float, float]:
    vocab = build_text_vocabulary(train_step_texts)
    train_x = vectorize_text(train_step_texts, vocab)
    test_x = vectorize_text([source_text, variant_text], vocab)
    probs = fit_linear_probe(train_x, train_labels, test_x)
    return float(probs[0].item()), float(probs[1].item())


def score_latent_pair(
    train_entries: List[Dict],
    train_labels: torch.Tensor,
    pair_features: Dict[str, Dict],
    field: str,
) -> Tuple[float, float]:
    train_x = tensor_from_entries(train_entries, field)
    test_x = tensor_from_entries(
        [
            {field: pair_features["source"][field]},
            {field: pair_features["variant"][field]},
        ],
        field,
    )
    probs = fit_linear_probe(train_x, train_labels, test_x)
    return float(probs[0].item()), float(probs[1].item())


def score_concat_pair(
    train_entries: List[Dict],
    train_labels: torch.Tensor,
    pair_features: Dict[str, Dict],
    fields: List[str],
) -> Tuple[float, float]:
    train_x = concat_fields(train_entries, fields)
    test_entries = []
    for name in ["source", "variant"]:
        entry = {field: pair_features[name][field] for field in fields}
        test_entries.append(entry)
    test_parts = [tensor_from_entries(test_entries, field) for field in fields]
    test_x = torch.cat(test_parts, dim=1)
    probs = fit_linear_probe(train_x, train_labels, test_x)
    return float(probs[0].item()), float(probs[1].item())


def aggregate_metrics(rows: List[Dict]) -> Dict[str, Dict]:
    metrics = {}
    for baseline in ["text_only", "pre_state_only", "post_state_only", "transition_only", "concat_all"]:
        same_gaps = [
            abs(row["source_scores"][baseline] - row["variant_scores"][baseline])
            for row in rows
            if row["type"] == "same_semantics"
        ]
        flip_diffs = [
            row["source_scores"][baseline] - row["variant_scores"][baseline]
            for row in rows
            if row["type"] == "semantic_flip"
        ]
        metrics[baseline] = {
            "num_same_pairs": len(same_gaps),
            "num_flip_pairs": len(flip_diffs),
            "invariance_gap": None if not same_gaps else float(sum(same_gaps) / len(same_gaps)),
            "semantic_sensitivity": None if not flip_diffs else float(sum(flip_diffs) / len(flip_diffs)),
        }
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate CTS-mini using first-pass probes.")
    parser.add_argument("--train-features", required=True)
    parser.add_argument("--raw-jsonl", required=True)
    parser.add_argument("--cts-seed", required=True)
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--layers", default="-1,-8,-16")
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()

    feature_entries = torch.load(args.train_features)
    raw_rows = load_jsonl(Path(args.raw_jsonl))
    cts_rows = load_jsonl(Path(args.cts_seed))
    raw_index = index_raw_rows(raw_rows)

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
    for row in cts_rows:
        theorem_id = row["source_theorem_id"]
        raw_row = raw_index[theorem_id]
        train_entries, train_labels, _, train_step_texts = build_training_tensors(feature_entries, theorem_id)
        pair_features = extract_pair_features(
            model=model,
            tokenizer=tokenizer,
            row=raw_row,
            step_index=row["source_step_index"],
            variant_step=row["variant_step"],
            resolved_layers=resolved_layers,
            device=args.device,
        )

        text_source, text_variant = score_text_pair(
            train_step_texts=train_step_texts,
            train_labels=train_labels,
            source_text=pair_features["source"]["step_text"],
            variant_text=pair_features["variant"]["step_text"],
        )
        post_source, post_variant = score_latent_pair(
            train_entries=train_entries,
            train_labels=train_labels,
            pair_features=pair_features,
            field="h_plus",
        )
        pre_source, pre_variant = score_latent_pair(
            train_entries=train_entries,
            train_labels=train_labels,
            pair_features=pair_features,
            field="h_minus",
        )
        trans_source, trans_variant = score_latent_pair(
            train_entries=train_entries,
            train_labels=train_labels,
            pair_features=pair_features,
            field="delta_h",
        )
        concat_source, concat_variant = score_concat_pair(
            train_entries=train_entries,
            train_labels=train_labels,
            pair_features=pair_features,
            fields=["h_minus", "h_plus", "delta_h"],
        )

        results.append(
            {
                "pair_id": row["pair_id"],
                "type": row["type"],
                "source_theorem_id": theorem_id,
                "source_step_index": row["source_step_index"],
                "expected_label_change": row["expected_label_change"],
                "source_scores": {
                    "text_only": text_source,
                    "pre_state_only": pre_source,
                    "post_state_only": post_source,
                    "transition_only": trans_source,
                    "concat_all": concat_source,
                },
                "variant_scores": {
                    "text_only": text_variant,
                    "pre_state_only": pre_variant,
                    "post_state_only": post_variant,
                    "transition_only": trans_variant,
                    "concat_all": concat_variant,
                },
                "header_token_count": pair_features["source"]["header_token_count"],
                "source_after_token_count": pair_features["source"]["after_token_count"],
                "variant_after_token_count": pair_features["variant"]["after_token_count"],
            }
        )

    output = {
        "train_features": args.train_features,
        "raw_jsonl": args.raw_jsonl,
        "cts_seed": args.cts_seed,
        "model_path": args.model_path,
        "resolved_layers": resolved_layers,
        "metrics": aggregate_metrics(results),
        "pairs": results,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
