#!/usr/bin/env python3
import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from evaluate_cts_mini import extract_pair_features, index_raw_rows
from extract_boundary_states_smoke import load_jsonl, resolve_layers
from evaluate_cts_scoring_audit import normalize_train_test


def flatten_field(entry: Dict, field: str) -> torch.Tensor:
    layer_items = sorted(entry[field].items(), key=lambda kv: int(kv[0]))
    return torch.cat([tensor.to(torch.float32) for _, tensor in layer_items], dim=0)


def aggregate_metrics(rows: List[Dict], baselines: List[str]) -> Dict[str, Dict]:
    metrics = {}
    for baseline in baselines:
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


def fit_pairwise_margin_scorer(
    train_source: torch.Tensor,
    train_variant: torch.Tensor,
    train_types: List[str],
    test_source: torch.Tensor,
    test_variant: torch.Tensor,
    hidden_dim: int = 128,
    margin: float = 1.0,
    epochs: int = 400,
    lr: float = 1e-3,
    weight_decay: float = 1e-4,
) -> Tuple[torch.Tensor, torch.Tensor]:
    train_joint = torch.cat([train_source, train_variant], dim=0)
    test_joint = torch.cat([test_source, test_variant], dim=0)
    train_joint, test_joint = normalize_train_test(train_joint, test_joint)
    train_source = train_joint[: len(train_source)]
    train_variant = train_joint[len(train_source) :]
    test_source = test_joint[: len(test_source)]
    test_variant = test_joint[len(test_source) :]

    if len(train_source) == 0:
        return torch.zeros(len(test_source), dtype=torch.float32), torch.zeros(len(test_variant), dtype=torch.float32)

    model = torch.nn.Sequential(
        torch.nn.Linear(train_source.shape[1], hidden_dim),
        torch.nn.ReLU(),
        torch.nn.Linear(hidden_dim, 1),
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)

    same_mask = torch.tensor([t == "same_semantics" for t in train_types], dtype=torch.bool)
    flip_mask = ~same_mask

    for _ in range(epochs):
        optimizer.zero_grad()
        src_scores = model(train_source).squeeze(-1)
        var_scores = model(train_variant).squeeze(-1)

        loss_terms = []
        if int(same_mask.sum().item()) > 0:
            same_diff = src_scores[same_mask] - var_scores[same_mask]
            loss_terms.append(torch.mean(same_diff ** 2))
        if int(flip_mask.sum().item()) > 0:
            flip_margin = src_scores[flip_mask] - var_scores[flip_mask]
            loss_terms.append(torch.mean(torch.nn.functional.softplus(margin - flip_margin)))

        loss = sum(loss_terms)
        loss.backward()
        optimizer.step()

    with torch.no_grad():
        return (
            torch.sigmoid(model(test_source).squeeze(-1)).cpu(),
            torch.sigmoid(model(test_variant).squeeze(-1)).cpu(),
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate CTS with pairwise margin-trained scorers.")
    parser.add_argument("--raw-jsonl", required=True)
    parser.add_argument("--cts-seed", required=True)
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--layers", default="-1,-8,-16")
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()

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

    extracted_pairs = []
    for row in cts_rows:
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
        extracted_pairs.append(
            {
                "pair_id": row["pair_id"],
                "type": row["type"],
                "source_theorem_id": theorem_id,
                "source_step_index": row["source_step_index"],
                "expected_label_change": row["expected_label_change"],
                "source": pair_features["source"],
                "variant": pair_features["variant"],
            }
        )

    group_to_indices = defaultdict(list)
    for idx, row in enumerate(extracted_pairs):
        group_to_indices[row["source_theorem_id"]].append(idx)

    baselines = ["post_pairwise_margin", "transition_pairwise_margin"]
    source_scores = {name: torch.zeros(len(extracted_pairs), dtype=torch.float32) for name in baselines}
    variant_scores = {name: torch.zeros(len(extracted_pairs), dtype=torch.float32) for name in baselines}

    for theorem_id, test_indices in group_to_indices.items():
        train_indices = [i for i, row in enumerate(extracted_pairs) if row["source_theorem_id"] != theorem_id]
        train_types = [extracted_pairs[i]["type"] for i in train_indices]

        for field, baseline_name in [("h_plus", "post_pairwise_margin"), ("delta_h", "transition_pairwise_margin")]:
            train_source = torch.stack([flatten_field(extracted_pairs[i]["source"], field) for i in train_indices], dim=0)
            train_variant = torch.stack([flatten_field(extracted_pairs[i]["variant"], field) for i in train_indices], dim=0)
            test_source = torch.stack([flatten_field(extracted_pairs[i]["source"], field) for i in test_indices], dim=0)
            test_variant = torch.stack([flatten_field(extracted_pairs[i]["variant"], field) for i in test_indices], dim=0)

            torch.manual_seed(0)
            src, var = fit_pairwise_margin_scorer(
                train_source=train_source,
                train_variant=train_variant,
                train_types=train_types,
                test_source=test_source,
                test_variant=test_variant,
            )
            source_scores[baseline_name][test_indices] = src
            variant_scores[baseline_name][test_indices] = var

    results = []
    for idx, row in enumerate(extracted_pairs):
        results.append(
            {
                "pair_id": row["pair_id"],
                "type": row["type"],
                "source_theorem_id": row["source_theorem_id"],
                "source_step_index": row["source_step_index"],
                "expected_label_change": row["expected_label_change"],
                "source_scores": {name: float(source_scores[name][idx].item()) for name in baselines},
                "variant_scores": {name: float(variant_scores[name][idx].item()) for name in baselines},
            }
        )

    output = {
        "raw_jsonl": args.raw_jsonl,
        "cts_seed": args.cts_seed,
        "model_path": args.model_path,
        "resolved_layers": resolved_layers,
        "metrics": aggregate_metrics(results, baselines),
        "pairs": results,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
