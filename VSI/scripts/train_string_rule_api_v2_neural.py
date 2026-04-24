#!/usr/bin/env python3
"""Stronger learned decoder for semantic-v2 via char-level sequence classification."""

from __future__ import annotations

import argparse
import json
import random
import string
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import torch


ALPHABET = string.ascii_lowercase + string.ascii_uppercase + "!*_-:+[]#@%<>?{}|=;"
PAD = 0
UNK = 1
MAX_SEQ_LEN = 160


def reverse_suffix(token: str, text: str) -> str:
    return text[::-1] + token


def upper_wrap(token: str, text: str) -> str:
    return f"{token}{text.upper()}{token}"


def duplicate_prefix(token: str, text: str) -> str:
    return f"{token}{text}{text}"


def odd_even_join(token: str, text: str) -> str:
    even = text[::2]
    odd = text[1::2]
    return f"{even}{token}{odd}"


def half_swap(token: str, text: str) -> str:
    split = (len(text) + 1) // 2
    left = text[:split]
    right = text[split:]
    return f"{right}{token}{left}"


LEGACY_SPECS: Dict[str, Dict[str, Any]] = {
    "reverse_suffix": {"params": ["!", "?", "#"], "fn": reverse_suffix},
    "upper_wrap": {"params": ["[", "<", "{"], "fn": upper_wrap},
    "duplicate_prefix": {"params": ["pre_", "tag-", "id:"], "fn": duplicate_prefix},
}

V2_SPECS: Dict[str, Dict[str, Any]] = {
    "odd_even_join": {"params": ["::", "--", "++"], "fn": odd_even_join},
    "half_swap": {"params": ["#", "@", "%"], "fn": half_swap},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--repeats", type=int, default=40)
    parser.add_argument("--epochs", type=int, default=300)
    return parser.parse_args()


def rand_word(rng: random.Random, min_len: int = 5, max_len: int = 9) -> str:
    return "".join(rng.choice(string.ascii_lowercase) for _ in range(rng.randint(min_len, max_len)))


def build_task(family: str, param: str, fn, rng: random.Random, idx: int) -> Dict[str, object]:
    visible_inputs = [rand_word(rng) for _ in range(3)]
    hidden_inputs = [rand_word(rng) for _ in range(2)]
    return {
        "task_id": f"{family}_{idx:05d}",
        "label": f"{family}|{param}",
        "visible_tests": [[item, fn(param, item)] for item in visible_inputs],
        "hidden_tests": [[item, fn(param, item)] for item in hidden_inputs],
    }


def build_dataset(include_v2: bool, repeats: int, seed: int = 7) -> Tuple[List[Dict[str, object]], List[str]]:
    rng = random.Random(seed)
    specs = dict(LEGACY_SPECS)
    if include_v2:
        specs.update(V2_SPECS)
    tasks: List[Dict[str, object]] = []
    labels: List[str] = []
    idx = 1
    for _ in range(repeats):
        for family, spec in specs.items():
            for param in spec["params"]:
                labels.append(f"{family}|{param}")
                tasks.append(build_task(family, param, spec["fn"], rng, idx))
                idx += 1
    random.shuffle(tasks)
    return tasks, sorted(set(labels))


def vocab() -> Dict[str, int]:
    return {ch: idx + 2 for idx, ch in enumerate(ALPHABET)}


def serialize_examples(task: Dict[str, object]) -> str:
    parts = []
    for inp, out in task["visible_tests"]:
        parts.append(f"IN={inp};OUT={out}")
    return "|".join(parts)


def encode_text(text: str, stoi: Dict[str, int], max_len: int = MAX_SEQ_LEN) -> torch.Tensor:
    vec = torch.full((max_len,), PAD, dtype=torch.long)
    for idx, ch in enumerate(text[:max_len]):
        vec[idx] = stoi.get(ch, UNK)
    return vec


def make_batch(tasks: Sequence[Dict[str, object]], label_to_idx: Dict[str, int], stoi: Dict[str, int]) -> Tuple[torch.Tensor, torch.Tensor]:
    xs = torch.stack([encode_text(serialize_examples(task), stoi) for task in tasks])
    ys = torch.tensor([label_to_idx[str(task["label"])] for task in tasks], dtype=torch.int64)
    return xs, ys


class CharCNN(torch.nn.Module):
    def __init__(self, vocab_size: int, n_labels: int) -> None:
        super().__init__()
        self.embed = torch.nn.Embedding(vocab_size, 32, padding_idx=PAD)
        self.conv3 = torch.nn.Conv1d(32, 64, kernel_size=3, padding=1)
        self.conv5 = torch.nn.Conv1d(32, 64, kernel_size=5, padding=2)
        self.proj = torch.nn.Sequential(
            torch.nn.Linear(128, 96),
            torch.nn.ReLU(),
            torch.nn.Linear(96, n_labels),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        emb = self.embed(x).transpose(1, 2)
        h3 = torch.relu(self.conv3(emb))
        h5 = torch.relu(self.conv5(emb))
        pooled3 = torch.max(h3, dim=2).values
        pooled5 = torch.max(h5, dim=2).values
        return self.proj(torch.cat([pooled3, pooled5], dim=1))


def train_model(
    tasks: Sequence[Dict[str, object]],
    labels: Sequence[str],
    epochs: int,
) -> Tuple[CharCNN, Dict[str, int], Dict[str, int], List[float]]:
    label_to_idx = {label: idx for idx, label in enumerate(labels)}
    stoi = vocab()
    xs, ys = make_batch(tasks, label_to_idx, stoi)
    model = CharCNN(vocab_size=max(stoi.values()) + 1, n_labels=len(labels))
    opt = torch.optim.AdamW(model.parameters(), lr=3e-3, weight_decay=1e-3)
    loss_fn = torch.nn.CrossEntropyLoss()
    losses: List[float] = []
    for _ in range(epochs):
        opt.zero_grad()
        logits = model(xs)
        loss = loss_fn(logits, ys)
        loss.backward()
        opt.step()
        losses.append(float(loss.item()))
    return model, label_to_idx, stoi, losses


def predict_label(model: CharCNN, task: Dict[str, object], labels: Sequence[str], stoi: Dict[str, int]) -> str:
    x = encode_text(serialize_examples(task), stoi).unsqueeze(0)
    with torch.no_grad():
        logits = model(x)[0]
        idx = int(torch.argmax(logits).item())
    return labels[idx]


def apply_label(label: str, text: str) -> str:
    family, param = label.split("|", 1)
    if family in LEGACY_SPECS:
        return LEGACY_SPECS[family]["fn"](param, text)
    return V2_SPECS[family]["fn"](param, text)


def eval_model(model: CharCNN, tasks: Sequence[Dict[str, object]], labels: Sequence[str], stoi: Dict[str, int]) -> Dict[str, float]:
    exact = 0
    for task in tasks:
        predicted = predict_label(model, task, labels, stoi)
        pred_outputs = [apply_label(predicted, item[0]) for item in task["hidden_tests"]]
        gold_outputs = [item[1] for item in task["hidden_tests"]]
        if pred_outputs == gold_outputs:
            exact += 1
    return {"tasks": len(tasks), "exact_hidden_match_rate": round(exact / len(tasks), 3)}


def load_eval_tasks(artifact_path: Path) -> List[Dict[str, object]]:
    artifact = json.loads(artifact_path.read_text())
    tasks: List[Dict[str, object]] = []
    for task in artifact["tasks"]:
        example = task["attempts"][0]["scores"]
        tasks.append(
            {
                "task_id": task["task_id"],
                "visible_tests": [[item["input"], item["expected"]] for item in example["visible_results"]],
                "hidden_tests": [[item["input"], item["expected"]] for item in example["hidden_results"]],
            }
        )
    return tasks


def visible_baseline(artifact_path: Path) -> Dict[str, float]:
    artifact = json.loads(artifact_path.read_text())
    exact = 0
    for task in artifact["tasks"]:
        best = max(task["attempts"], key=lambda attempt: float(attempt["scores"]["visible_score"]))
        hidden = best["scores"]["hidden_results"]
        exact += 1 if all(item.get("pass", False) for item in hidden) else 0
    return {"tasks": len(artifact["tasks"]), "exact_hidden_match_rate": round(exact / len(artifact["tasks"]), 3)}


def summarize_regime(include_v2: bool, eval_tasks: Sequence[Dict[str, object]], repeats: int, epochs: int) -> Dict[str, Any]:
    dataset, labels = build_dataset(include_v2=include_v2, repeats=repeats)
    split = int(0.8 * len(dataset))
    train_tasks = dataset[:split]
    val_tasks = dataset[split:]
    model, _, stoi, losses = train_model(train_tasks, labels, epochs=epochs)
    return {
        "include_v2": include_v2,
        "label_space": len(labels),
        "train_tasks": len(train_tasks),
        "val_tasks": len(val_tasks),
        "final_train_loss": round(losses[-1], 6),
        "validation": eval_model(model, val_tasks, labels, stoi),
        "api_v2_eval": eval_model(model, eval_tasks, labels, stoi),
    }


def main() -> None:
    args = parse_args()
    random.seed(7)
    torch.manual_seed(7)
    eval_tasks = load_eval_tasks(args.artifact)
    payload = {
        "legacy_only_neural": summarize_regime(include_v2=False, eval_tasks=eval_tasks, repeats=args.repeats, epochs=args.epochs),
        "legacy_plus_v2_neural": summarize_regime(include_v2=True, eval_tasks=eval_tasks, repeats=args.repeats, epochs=args.epochs),
        "visible_attempt_baseline": visible_baseline(args.artifact),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
