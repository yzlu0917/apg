#!/usr/bin/env python3
import argparse
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import torch


def load_features(path: Path) -> List[Dict]:
    return torch.load(path)


def read_jsonl(path: Path) -> List[Dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def tokenize(text: str) -> List[str]:
    return re.findall(r"\w+|[^\w\s]", text.lower())


def build_text_vocabulary(step_texts: List[str], min_freq: int = 1) -> Dict[str, int]:
    counter = Counter()
    for text in step_texts:
        counter.update(tokenize(text))
    vocab = {}
    for token, freq in sorted(counter.items()):
        if freq >= min_freq:
            vocab[token] = len(vocab)
    return vocab


def vectorize_text(step_texts: List[str], vocab: Dict[str, int]) -> torch.Tensor:
    x = torch.zeros((len(step_texts), len(vocab)), dtype=torch.float32)
    for i, text in enumerate(step_texts):
        counts = Counter(tokenize(text))
        for token, value in counts.items():
            if token in vocab:
                x[i, vocab[token]] = float(value)
    return x


def tensor_from_entries(entries: List[Dict], field: str) -> torch.Tensor:
    rows = []
    for entry in entries:
        layer_items = sorted(entry[field].items(), key=lambda kv: int(kv[0]))
        rows.append(torch.cat([tensor.to(torch.float32) for _, tensor in layer_items], dim=0))
    return torch.stack(rows, dim=0)


def concat_fields(entries: List[Dict], fields: List[str]) -> torch.Tensor:
    parts = [tensor_from_entries(entries, field) for field in fields]
    return torch.cat(parts, dim=1)


def auroc_score(y_true: torch.Tensor, y_score: torch.Tensor) -> float:
    pos = y_score[y_true == 1]
    neg = y_score[y_true == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    wins = 0.0
    for p in pos:
        wins += float((p > neg).sum().item())
        wins += 0.5 * float((p == neg).sum().item())
    return wins / (len(pos) * len(neg))


def brier_score(y_true: torch.Tensor, y_prob: torch.Tensor) -> float:
    return float(torch.mean((y_prob - y_true.float()) ** 2).item())


def fit_linear_probe(
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


def grouped_cv_predictions(features: torch.Tensor, labels: torch.Tensor, groups: List[str]) -> torch.Tensor:
    group_to_indices = defaultdict(list)
    for idx, group in enumerate(groups):
        group_to_indices[group].append(idx)

    predictions = torch.zeros(len(labels), dtype=torch.float32)
    for group, test_indices in group_to_indices.items():
        train_indices = [i for i, g in enumerate(groups) if g != group]
        x_train = features[train_indices]
        y_train = labels[train_indices]
        x_test = features[test_indices]
        predictions[test_indices] = fit_linear_probe(x_train, y_train, x_test)
    return predictions


def earliest_fail_localization(entries: List[Dict], probs: torch.Tensor) -> float:
    grouped = defaultdict(list)
    for idx, entry in enumerate(entries):
        grouped[entry["theorem_id"]].append((entry["step_index"], entry["local_sound"], float(probs[idx].item())))

    total = 0
    correct = 0
    for theorem_id, rows in grouped.items():
        if all(label == 1 for _, label, _ in rows):
            continue
        total += 1
        rows = sorted(rows, key=lambda x: x[0])
        true_earliest = min(step_idx for step_idx, label, _ in rows if label == 0)
        predicted_earliest = min(rows, key=lambda x: x[2])[0]
        if true_earliest == predicted_earliest:
            correct += 1
    return float("nan") if total == 0 else correct / total


def main() -> None:
    parser = argparse.ArgumentParser(description="Run first-pass Object gate baselines.")
    parser.add_argument("--features", required=True, help="Path to boundary_states.pt")
    parser.add_argument("--raw-jsonl", required=True, help="Path to the corresponding raw jsonl slice")
    parser.add_argument("--output", required=True, help="Path to the result json")
    args = parser.parse_args()

    feature_entries = load_features(Path(args.features))
    raw_rows = read_jsonl(Path(args.raw_jsonl))
    step_text_map = {}
    for row in raw_rows:
        for step_index, step_text in enumerate(row["steps"]):
            step_text_map[(row["theorem_id"], step_index)] = step_text

    labels = torch.tensor([entry["local_sound"] for entry in feature_entries], dtype=torch.long)
    groups = [entry["theorem_id"] for entry in feature_entries]
    step_texts = [step_text_map[(entry["theorem_id"], entry["step_index"])] for entry in feature_entries]

    vocab = build_text_vocabulary(step_texts)
    feature_sets = {
        "text_only": vectorize_text(step_texts, vocab),
        "pre_state_only": tensor_from_entries(feature_entries, "h_minus"),
        "post_state_only": tensor_from_entries(feature_entries, "h_plus"),
        "transition_only": tensor_from_entries(feature_entries, "delta_h"),
        "concat_all": concat_fields(feature_entries, ["h_minus", "h_plus", "delta_h"]),
    }

    results = {}
    for name, feats in feature_sets.items():
        probs = grouped_cv_predictions(feats, labels, groups)
        preds = (probs >= 0.5).long()
        results[name] = {
            "num_examples": len(feature_entries),
            "num_theorems": len(set(groups)),
            "positive_steps": int(labels.sum().item()),
            "negative_steps": int((labels == 0).sum().item()),
            "feature_dim": int(feats.shape[1]),
            "auroc": auroc_score(labels, probs),
            "accuracy": float((preds == labels).float().mean().item()),
            "brier": brier_score(labels, probs),
            "earliest_fail_localization": earliest_fail_localization(feature_entries, probs),
        }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
