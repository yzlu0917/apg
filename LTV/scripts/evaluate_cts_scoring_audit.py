#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from evaluate_cts_mini import (
    build_training_tensors,
    extract_pair_features,
    index_raw_rows,
)
from extract_boundary_states_smoke import load_jsonl, resolve_layers
from run_object_gate_baselines import tensor_from_entries


def normalize_train_test(x_train: torch.Tensor, x_test: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
    mean = x_train.mean(dim=0, keepdim=True)
    std = x_train.std(dim=0, keepdim=True)
    std = torch.where(std < 1e-6, torch.ones_like(std), std)
    return (x_train - mean) / std, (x_test - mean) / std


def fit_linear_probe_with_details(
    x_train: torch.Tensor,
    y_train: torch.Tensor,
    x_test: torch.Tensor,
    epochs: int = 400,
    lr: float = 0.05,
    weight_decay: float = 1e-3,
) -> Dict[str, torch.Tensor]:
    x_train, x_test = normalize_train_test(x_train, x_test)

    if int(y_train.sum().item()) == 0 or int(y_train.sum().item()) == len(y_train):
        prior = y_train.float().mean().clamp(1e-4, 1 - 1e-4)
        probs = torch.full((len(x_test),), float(prior.item()), dtype=torch.float32)
        logits = torch.logit(probs.clamp(1e-6, 1 - 1e-6))
        return {
            "probs": probs,
            "logits": logits,
            "logits_z": torch.zeros_like(logits),
        }

    model = torch.nn.Linear(x_train.shape[1], 1)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    loss_fn = torch.nn.BCEWithLogitsLoss()

    for _ in range(epochs):
        optimizer.zero_grad()
        logits = model(x_train).squeeze(-1)
        loss = loss_fn(logits, y_train.float())
        loss.backward()
        optimizer.step()

    with torch.no_grad():
        train_logits = model(x_train).squeeze(-1)
        test_logits = model(x_test).squeeze(-1).cpu()
        train_std = train_logits.std().item()
        train_std = 1.0 if train_std < 1e-6 else train_std
        return {
            "probs": torch.sigmoid(test_logits).cpu(),
            "logits": test_logits,
            "logits_z": (test_logits / train_std).cpu(),
        }


def fit_mlp_probe(
    x_train: torch.Tensor,
    y_train: torch.Tensor,
    x_test: torch.Tensor,
    hidden_dim: int = 128,
    epochs: int = 500,
    lr: float = 1e-3,
    weight_decay: float = 1e-4,
) -> torch.Tensor:
    x_train, x_test = normalize_train_test(x_train, x_test)

    if int(y_train.sum().item()) == 0 or int(y_train.sum().item()) == len(y_train):
        prior = y_train.float().mean().clamp(1e-4, 1 - 1e-4)
        return torch.full((len(x_test),), float(prior.item()), dtype=torch.float32)

    model = torch.nn.Sequential(
        torch.nn.Linear(x_train.shape[1], hidden_dim),
        torch.nn.ReLU(),
        torch.nn.Linear(hidden_dim, 1),
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    loss_fn = torch.nn.BCEWithLogitsLoss()

    for _ in range(epochs):
        optimizer.zero_grad()
        logits = model(x_train).squeeze(-1)
        loss = loss_fn(logits, y_train.float())
        loss.backward()
        optimizer.step()

    with torch.no_grad():
        return torch.sigmoid(model(x_test).squeeze(-1)).cpu()


def centroid_cosine_scores(
    x_train: torch.Tensor,
    y_train: torch.Tensor,
    x_test: torch.Tensor,
) -> torch.Tensor:
    x_train, x_test = normalize_train_test(x_train, x_test)

    pos = x_train[y_train == 1]
    neg = x_train[y_train == 0]
    if len(pos) == 0 or len(neg) == 0:
        return torch.zeros(len(x_test), dtype=torch.float32)

    pos_centroid = pos.mean(dim=0, keepdim=True)
    neg_centroid = neg.mean(dim=0, keepdim=True)

    pos_norm = torch.nn.functional.normalize(pos_centroid, dim=1)
    neg_norm = torch.nn.functional.normalize(neg_centroid, dim=1)
    test_norm = torch.nn.functional.normalize(x_test, dim=1)

    pos_sim = torch.matmul(test_norm, pos_norm.t()).squeeze(-1)
    neg_sim = torch.matmul(test_norm, neg_norm.t()).squeeze(-1)
    return (pos_sim - neg_sim).cpu()


def aggregate_metrics(rows: List[Dict], baseline_names: List[str]) -> Dict[str, Dict]:
    metrics = {}
    for baseline in baseline_names:
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


def score_representation(
    train_entries: List[Dict],
    train_labels: torch.Tensor,
    pair_features: Dict[str, Dict],
    field: str,
) -> Dict[str, Tuple[float, float]]:
    train_x = tensor_from_entries(train_entries, field)
    test_x = tensor_from_entries(
        [
            {field: pair_features["source"][field]},
            {field: pair_features["variant"][field]},
        ],
        field,
    )

    linear = fit_linear_probe_with_details(train_x, train_labels, test_x)
    mlp = fit_mlp_probe(train_x, train_labels, test_x)
    centroid = centroid_cosine_scores(train_x, train_labels, test_x)

    return {
        "linear_prob": (float(linear["probs"][0].item()), float(linear["probs"][1].item())),
        "linear_logit_z": (float(linear["logits_z"][0].item()), float(linear["logits_z"][1].item())),
        "mlp_prob": (float(mlp[0].item()), float(mlp[1].item())),
        "centroid_cosine": (float(centroid[0].item()), float(centroid[1].item())),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Scoring audit on a fixed CTS panel.")
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

    baseline_names = [
        "post_linear_prob",
        "post_linear_logit_z",
        "post_mlp_prob",
        "post_centroid_cosine",
        "transition_linear_prob",
        "transition_linear_logit_z",
        "transition_mlp_prob",
        "transition_centroid_cosine",
    ]

    results = []
    for row in cts_rows:
        theorem_id = row["source_theorem_id"]
        raw_row = raw_index[theorem_id]
        train_entries, train_labels, _, _ = build_training_tensors(feature_entries, theorem_id)
        pair_features = extract_pair_features(
            model=model,
            tokenizer=tokenizer,
            row=raw_row,
            step_index=row["source_step_index"],
            variant_step=row["variant_step"],
            resolved_layers=resolved_layers,
            device=args.device,
        )

        post_scores = score_representation(train_entries, train_labels, pair_features, "h_plus")
        trans_scores = score_representation(train_entries, train_labels, pair_features, "delta_h")

        source_scores = {}
        variant_scores = {}
        for scorer_name, (s, v) in post_scores.items():
            source_scores[f"post_{scorer_name}"] = s
            variant_scores[f"post_{scorer_name}"] = v
        for scorer_name, (s, v) in trans_scores.items():
            source_scores[f"transition_{scorer_name}"] = s
            variant_scores[f"transition_{scorer_name}"] = v

        results.append(
            {
                "pair_id": row["pair_id"],
                "type": row["type"],
                "source_theorem_id": theorem_id,
                "source_step_index": row["source_step_index"],
                "expected_label_change": row["expected_label_change"],
                "source_scores": source_scores,
                "variant_scores": variant_scores,
            }
        )

    output = {
        "train_features": args.train_features,
        "raw_jsonl": args.raw_jsonl,
        "cts_seed": args.cts_seed,
        "model_path": args.model_path,
        "resolved_layers": resolved_layers,
        "metrics": aggregate_metrics(results, baseline_names),
        "pairs": results,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
