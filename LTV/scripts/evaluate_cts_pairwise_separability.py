#!/usr/bin/env python3
import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from evaluate_cts_mini import extract_pair_features, index_raw_rows
from evaluate_cts_scoring_audit import normalize_train_test
from extract_boundary_states_smoke import load_jsonl, resolve_layers
from run_object_gate_baselines import auroc_score, brier_score


def flatten_field(entry: Dict, field: str) -> torch.Tensor:
    layer_items = sorted(entry[field].items(), key=lambda kv: int(kv[0]))
    return torch.cat([tensor.to(torch.float32) for _, tensor in layer_items], dim=0)


def fit_linear_diff_probe(
    x_train: torch.Tensor,
    y_train: torch.Tensor,
    x_test: torch.Tensor,
    epochs: int = 400,
    lr: float = 0.05,
    weight_decay: float = 1e-3,
) -> torch.Tensor:
    if int(y_train.sum().item()) == 0 or int(y_train.sum().item()) == len(y_train):
        prior = y_train.float().mean().clamp(1e-4, 1 - 1e-4)
        return torch.full((len(x_test),), float(prior.item()), dtype=torch.float32)

    mean = x_train.mean(dim=0, keepdim=True)
    std = x_train.std(dim=0, keepdim=True)
    std = torch.where(std < 1e-6, torch.ones_like(std), std)
    x_train = (x_train - mean) / std
    x_test = (x_test - mean) / std

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
        return torch.sigmoid(model(x_test).squeeze(-1)).cpu()


def fit_centroid_diff_scorer(
    x_train: torch.Tensor,
    y_train: torch.Tensor,
    x_test: torch.Tensor,
) -> torch.Tensor:
    x_train, x_test = normalize_train_test(x_train, x_test)
    pos = x_train[y_train == 1]
    neg = x_train[y_train == 0]
    if len(pos) == 0 or len(neg) == 0:
        prior = y_train.float().mean().clamp(1e-4, 1 - 1e-4)
        return torch.full((len(x_test),), float(prior.item()), dtype=torch.float32)
    pos_centroid = pos.mean(dim=0, keepdim=True)
    neg_centroid = neg.mean(dim=0, keepdim=True)
    pos_dist = torch.norm(x_test - pos_centroid, dim=1)
    neg_dist = torch.norm(x_test - neg_centroid, dim=1)
    return torch.sigmoid(neg_dist - pos_dist).cpu()


def pair_metrics(y_true: torch.Tensor, y_prob: torch.Tensor) -> Dict[str, float]:
    preds = (y_prob >= 0.5).long()
    same_mask = y_true == 0
    flip_mask = y_true == 1
    return {
        "auroc": auroc_score(y_true, y_prob),
        "accuracy": float((preds == y_true).float().mean().item()),
        "brier": brier_score(y_true, y_prob),
        "num_same_pairs": int(same_mask.sum().item()),
        "num_flip_pairs": int(flip_mask.sum().item()),
        "same_mean_prob": float(y_prob[same_mask].mean().item()) if int(same_mask.sum().item()) > 0 else None,
        "flip_mean_prob": float(y_prob[flip_mask].mean().item()) if int(flip_mask.sum().item()) > 0 else None,
        "same_flip_gap": float(y_prob[flip_mask].mean().item() - y_prob[same_mask].mean().item()) if int(same_mask.sum().item()) > 0 and int(flip_mask.sum().item()) > 0 else None,
    }


def fisher_ratio(x: torch.Tensor, y: torch.Tensor) -> float:
    pos = x[y == 1]
    neg = x[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    pos_mean = pos.mean(dim=0)
    neg_mean = neg.mean(dim=0)
    between = torch.sum((pos_mean - neg_mean) ** 2)
    pos_cov = torch.mean(torch.sum((pos - pos_mean) ** 2, dim=1)) if len(pos) > 0 else torch.tensor(0.0)
    neg_cov = torch.mean(torch.sum((neg - neg_mean) ** 2, dim=1)) if len(neg) > 0 else torch.tensor(0.0)
    denom = pos_cov + neg_cov
    if float(denom.item()) < 1e-8:
        return float("inf")
    return float((between / denom).item())


def loo_knn_accuracy(x: torch.Tensor, y: torch.Tensor) -> float:
    if len(x) <= 1:
        return float("nan")
    x = torch.nn.functional.normalize(x, dim=1)
    sims = x @ x.T
    sims.fill_diagonal_(-1e9)
    nn_idx = sims.argmax(dim=1)
    preds = y[nn_idx]
    return float((preds == y).float().mean().item())


def geometry_metrics(x: torch.Tensor, y: torch.Tensor) -> Dict[str, float]:
    x_norm = torch.nn.functional.normalize(x, dim=1)
    pos = x_norm[y == 1]
    neg = x_norm[y == 0]
    pos_mean = pos.mean(dim=0) if len(pos) > 0 else torch.zeros(x.shape[1])
    neg_mean = neg.mean(dim=0) if len(neg) > 0 else torch.zeros(x.shape[1])
    return {
        "flip_centroid_norm": float(torch.norm(pos_mean).item()),
        "same_centroid_norm": float(torch.norm(neg_mean).item()),
        "centroid_gap": float(torch.norm(pos_mean - neg_mean).item()),
        "fisher_ratio": fisher_ratio(x, y),
        "loo_1nn_acc": loo_knn_accuracy(x, y),
    }


def family_slices(rows: List[Dict], baseline: str, annotated_panel: List[Dict]) -> Dict[str, Dict[str, float]]:
    ann = {row["pair_id_clean"]: row for row in annotated_panel}
    same_groups = defaultdict(list)
    flip_groups = defaultdict(list)
    for row in rows:
        pair_id = row["pair_id"]
        if pair_id not in ann:
            continue
        score = row["pair_scores"][baseline]
        meta = ann[pair_id]
        if row["type"] == "same_semantics":
            fam = meta.get("same_family", "unknown")
            same_groups[fam].append(score)
        else:
            fam = meta.get("flip_family", "unknown")
            flip_groups[fam].append(score)
    return {
        "same": {k: float(sum(v) / len(v)) for k, v in sorted(same_groups.items())},
        "flip": {k: float(sum(v) / len(v)) for k, v in sorted(flip_groups.items())},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate low-complexity pairwise separability on CTS.")
    parser.add_argument("--raw-jsonl", required=True)
    parser.add_argument("--cts-seed", required=True)
    parser.add_argument("--annotated-panel", required=True)
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--layers", default="-1,-8,-16")
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()

    raw_rows = load_jsonl(Path(args.raw_jsonl))
    cts_rows = load_jsonl(Path(args.cts_seed))
    annotated_panel = load_jsonl(Path(args.annotated_panel))
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
                "label": 1 if row["type"] == "semantic_flip" else 0,
                "source_theorem_id": theorem_id,
                "source_step_index": row["source_step_index"],
                "source": pair_features["source"],
                "variant": pair_features["variant"],
            }
        )

    labels = torch.tensor([row["label"] for row in extracted_pairs], dtype=torch.long)
    groups = [row["source_theorem_id"] for row in extracted_pairs]
    group_to_indices = defaultdict(list)
    for idx, group in enumerate(groups):
        group_to_indices[group].append(idx)

    field_to_baselines = {
        "h_plus": ["post_linear_sep", "post_centroid_sep"],
        "delta_h": ["transition_linear_sep", "transition_centroid_sep"],
    }
    pair_scores = {name: torch.zeros(len(extracted_pairs), dtype=torch.float32) for names in field_to_baselines.values() for name in names}

    geometry = {}
    for field in field_to_baselines:
        x = torch.stack([flatten_field(row["source"], field) - flatten_field(row["variant"], field) for row in extracted_pairs], dim=0)
        geometry[field] = geometry_metrics(x, labels)

    for theorem_id, test_indices in group_to_indices.items():
        train_indices = [i for i in range(len(extracted_pairs)) if groups[i] != theorem_id]
        y_train = labels[train_indices]
        for field, baselines in field_to_baselines.items():
            x_train = torch.stack([
                flatten_field(extracted_pairs[i]["source"], field) - flatten_field(extracted_pairs[i]["variant"], field)
                for i in train_indices
            ], dim=0)
            x_test = torch.stack([
                flatten_field(extracted_pairs[i]["source"], field) - flatten_field(extracted_pairs[i]["variant"], field)
                for i in test_indices
            ], dim=0)
            torch.manual_seed(0)
            pair_scores[baselines[0]][test_indices] = fit_linear_diff_probe(x_train, y_train, x_test)
            pair_scores[baselines[1]][test_indices] = fit_centroid_diff_scorer(x_train, y_train, x_test)

    metrics = {}
    rows = []
    for name, probs in pair_scores.items():
        metrics[name] = pair_metrics(labels, probs)
    for idx, row in enumerate(extracted_pairs):
        rows.append(
            {
                "pair_id": row["pair_id"],
                "type": row["type"],
                "label": row["label"],
                "source_theorem_id": row["source_theorem_id"],
                "source_step_index": row["source_step_index"],
                "pair_scores": {name: float(pair_scores[name][idx].item()) for name in pair_scores},
            }
        )

    family = {name: family_slices(rows, name, annotated_panel) for name in pair_scores}

    output = {
        "raw_jsonl": args.raw_jsonl,
        "cts_seed": args.cts_seed,
        "annotated_panel": args.annotated_panel,
        "model_path": args.model_path,
        "resolved_layers": resolved_layers,
        "task_definition": {
            "pair_label_1": "semantic_flip (pair has real progress difference)",
            "pair_label_0": "same_semantics (pair should have no progress difference)",
            "pair_representation": "phi(source) - phi(variant)",
        },
        "metrics": metrics,
        "geometry": geometry,
        "family": family,
        "pairs": rows,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
