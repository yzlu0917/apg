#!/usr/bin/env python3
"""Evaluate coverage-vs-shift on the semantic-v2 API-backed exploit family."""

from __future__ import annotations

import argparse
import json
import random
import string
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import torch


ALPHABET = string.ascii_lowercase + "!*_-:+[]#@%"


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

OOD_SPECS: Dict[str, Dict[str, Any]] = {
    "odd_even_join": {"params": ["::", "--", "++"], "fn": odd_even_join},
    "half_swap": {"params": ["#", "@", "%"], "fn": half_swap},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    return parser.parse_args()


def rand_word(rng: random.Random, min_len: int = 5, max_len: int = 8) -> str:
    letters = string.ascii_lowercase
    return "".join(rng.choice(letters) for _ in range(rng.randint(min_len, max_len)))


def build_task(family: str, param: str, fn, rng: random.Random, idx: int) -> Dict[str, object]:
    visible_inputs = [rand_word(rng) for _ in range(3)]
    hidden_inputs = [rand_word(rng) for _ in range(2)]
    return {
        "task_id": f"{family}_{idx:04d}",
        "label": f"{family}|{param}",
        "visible_tests": [[item, fn(param, item)] for item in visible_inputs],
        "hidden_tests": [[item, fn(param, item)] for item in hidden_inputs],
    }


def build_dataset(include_ood: bool, repeats: int = 20, seed: int = 7) -> Tuple[List[Dict[str, object]], List[str]]:
    rng = random.Random(seed)
    specs = dict(LEGACY_SPECS)
    if include_ood:
        specs.update(OOD_SPECS)
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


def encode_text(text: str, max_len: int = 20) -> torch.Tensor:
    vocab = {ch: i + 1 for i, ch in enumerate(ALPHABET)}
    vec = torch.zeros(max_len, dtype=torch.float32)
    for i, ch in enumerate(text[:max_len]):
        vec[i] = vocab.get(ch, 0)
    return vec / float(len(vocab) + 1)


def features(task: Dict[str, object]) -> torch.Tensor:
    visible = task["visible_tests"]
    parts: List[torch.Tensor] = []
    for inp, out in visible:
        parts.append(encode_text(str(inp)))
        parts.append(encode_text(str(out)))
    return torch.cat(parts)


def train_model(train_tasks: Sequence[Dict[str, object]], labels: Sequence[str]):
    label_to_idx = {label: idx for idx, label in enumerate(labels)}
    xs = torch.stack([features(task) for task in train_tasks])
    ys = torch.tensor([label_to_idx[str(task["label"])] for task in train_tasks], dtype=torch.int64)
    model = torch.nn.Sequential(
        torch.nn.Linear(xs.shape[1], 160),
        torch.nn.ReLU(),
        torch.nn.Linear(160, len(labels)),
    )
    opt = torch.optim.Adam(model.parameters(), lr=1e-2)
    loss_fn = torch.nn.CrossEntropyLoss()
    losses: List[float] = []
    for _ in range(600):
        opt.zero_grad()
        logits = model(xs)
        loss = loss_fn(logits, ys)
        loss.backward()
        opt.step()
        losses.append(float(loss.item()))
    return model, labels, losses


def predict_label(model: torch.nn.Module, task: Dict[str, object], labels: Sequence[str]) -> str:
    with torch.no_grad():
        logits = model(features(task).unsqueeze(0))[0]
        idx = int(torch.argmax(logits).item())
    return labels[idx]


def apply_label(label: str, text: str) -> str:
    family, param = label.split("|", 1)
    if family in LEGACY_SPECS:
        return LEGACY_SPECS[family]["fn"](param, text)
    return OOD_SPECS[family]["fn"](param, text)


def eval_model(model: torch.nn.Module, tasks: Sequence[Dict[str, object]], labels: Sequence[str]) -> Dict[str, float]:
    exact = 0
    for task in tasks:
        predicted = predict_label(model, task, labels)
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


def summarize_regime(include_ood: bool, eval_tasks: Sequence[Dict[str, object]]) -> Dict[str, Any]:
    dataset, labels = build_dataset(include_ood=include_ood)
    split = int(0.8 * len(dataset))
    train_tasks = dataset[:split]
    val_tasks = dataset[split:]
    model, labels, losses = train_model(train_tasks, labels)
    return {
        "include_ood": include_ood,
        "label_space": len(labels),
        "train_tasks": len(train_tasks),
        "val_tasks": len(val_tasks),
        "final_train_loss": round(losses[-1], 6),
        "validation": eval_model(model, val_tasks, labels),
        "api_v2_eval": eval_model(model, eval_tasks, labels),
    }


def main() -> None:
    args = parse_args()
    random.seed(7)
    torch.manual_seed(7)
    eval_tasks = load_eval_tasks(args.artifact)
    payload = {
        "legacy_only_train": summarize_regime(include_ood=False, eval_tasks=eval_tasks),
        "legacy_plus_v2_train": summarize_regime(include_ood=True, eval_tasks=eval_tasks),
        "visible_attempt_baseline": visible_baseline(args.artifact),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
