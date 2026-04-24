#!/usr/bin/env python3
"""Probe how far the numeric training signal transfers across rule families."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import torch


def affine(a: int, b: int):
    return lambda x: a * x + b


def quadratic(c: int):
    return lambda x: x * x + c


def triangular(c: int):
    return lambda x: (x * (x + 1)) // 2 + c


def alternating(scale: int):
    return lambda x: x * scale if x % 2 == 0 else -x * scale


FAMILY_SPECS = {
    "affine": {
        "builder": affine,
        "params": [(a, b) for a in [1, 2, 3, 4] for b in [-1, 0, 2, 4, 6]],
    },
    "quadratic": {
        "builder": quadratic,
        "params": [(c,) for c in [-1, 0, 1, 3, 5, 7, 9]],
    },
    "triangular": {
        "builder": triangular,
        "params": [(c,) for c in [0, 1, 2, 3, 4, 5, 6]],
    },
    "alternating": {
        "builder": alternating,
        "params": [(scale,) for scale in [1, 2, 3, 4, 5, 6]],
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slices", required=True, type=Path)
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    return parser.parse_args()


def make_task(name: str, fn, params: Tuple[int, ...], idx: int) -> Dict[str, object]:
    solver = fn(*params)
    return {
        "task_id": f"{name}_{idx:04d}",
        "family": name,
        "params": list(params),
        "visible_tests": [[1, solver(1)], [2, solver(2)], [3, solver(3)]],
        "hidden_tests": [[4, solver(4)], [5, solver(5)]],
    }


def build_dataset(families: Sequence[str], repeats: int = 24) -> List[Dict[str, object]]:
    tasks: List[Dict[str, object]] = []
    idx = 1
    for _ in range(repeats):
        for family in families:
            spec = FAMILY_SPECS[family]
            for params in spec["params"]:
                tasks.append(make_task(family, spec["builder"], params, idx))
                idx += 1
    random.shuffle(tasks)
    return tasks


def features(task: Dict[str, object]) -> torch.Tensor:
    visible = task["visible_tests"]
    y1, y2, y3 = [pair[1] for pair in visible]
    diffs = [y2 - y1, y3 - y2]
    return torch.tensor([y1, y2, y3, diffs[0], diffs[1]], dtype=torch.float32)


def targets(task: Dict[str, object]) -> torch.Tensor:
    hidden = task["hidden_tests"]
    return torch.tensor([hidden[0][1], hidden[1][1]], dtype=torch.float32)


class SolverNet(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(5, 32),
            torch.nn.ReLU(),
            torch.nn.Linear(32, 32),
            torch.nn.ReLU(),
            torch.nn.Linear(32, 2),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def train_model(train_tasks: Sequence[Dict[str, object]]) -> Tuple[SolverNet, List[float]]:
    xs = torch.stack([features(task) for task in train_tasks])
    ys = torch.stack([targets(task) for task in train_tasks])
    model = SolverNet()
    opt = torch.optim.Adam(model.parameters(), lr=1e-2)
    loss_fn = torch.nn.MSELoss()
    losses: List[float] = []
    for _ in range(1000):
        opt.zero_grad()
        pred = model(xs)
        loss = loss_fn(pred, ys)
        loss.backward()
        opt.step()
        losses.append(float(loss.item()))
    return model, losses


def eval_model(model: SolverNet, tasks: Sequence[Dict[str, object]]) -> Dict[str, float]:
    xs = torch.stack([features(task) for task in tasks])
    with torch.no_grad():
        preds = model(xs).round().to(torch.int64)
    exact = 0
    for pred, task in zip(preds.tolist(), tasks):
        hidden = [pair[1] for pair in task["hidden_tests"]]
        if pred == hidden:
            exact += 1
    return {
        "tasks": len(tasks),
        "exact_hidden_match_rate": round(exact / len(tasks), 3),
    }


def family_from_task_id(task_id: str) -> str:
    return task_id.split("_", 1)[0]


def load_frozen_tasks(artifact_path: Path) -> Dict[str, Dict[str, object]]:
    artifact = json.loads(artifact_path.read_text())
    numeric_tasks: Dict[str, Dict[str, object]] = {}
    for task in artifact["tasks"]:
        example = task["attempts"][0]["scores"]
        numeric_tasks[task["task_id"]] = {
            "task_id": task["task_id"],
            "family": family_from_task_id(task["task_id"]),
            "visible_tests": [[item["input"], item["expected"]] for item in example["visible_results"]],
            "hidden_tests": [[item["input"], item["expected"]] for item in example["hidden_results"]],
        }
    return numeric_tasks


def select_frozen_tasks(
    lookup: Dict[str, Dict[str, object]], task_ids: Sequence[str]
) -> List[Dict[str, object]]:
    return [lookup[task_id] for task_id in task_ids if task_id in lookup]


def baseline_visible_exact(tasks: Sequence[Dict[str, Any]]) -> Dict[str, float]:
    exact = 0
    for task in tasks:
        best = max(task["attempts"], key=lambda attempt: float(attempt["scores"]["visible_score"]))
        hidden = best["scores"]["hidden_results"]
        ok = all(item.get("pass", False) for item in hidden)
        exact += 1 if ok else 0
    return {
        "tasks": len(tasks),
        "exact_hidden_match_rate": round(exact / len(tasks), 3),
    }


def summarize_regime(
    train_families: Sequence[str],
    slices: Dict[str, Any],
    artifact: Dict[str, Any],
    frozen_lookup: Dict[str, Dict[str, object]],
) -> Dict[str, Any]:
    dataset = build_dataset(train_families)
    split = int(0.8 * len(dataset))
    train_tasks = dataset[:split]
    val_tasks = dataset[split:]
    model, losses = train_model(train_tasks)

    dev_ids = slices["families"]["exploit_code_large"]["dev_task_ids"]
    final_ids = slices["families"]["exploit_code_large"]["final_task_ids"]
    dev_tasks = select_frozen_tasks(frozen_lookup, dev_ids)
    final_tasks = select_frozen_tasks(frozen_lookup, final_ids)

    dev_runs = [task for task in artifact["tasks"] if task["task_id"] in set(dev_ids)]
    final_runs = [task for task in artifact["tasks"] if task["task_id"] in set(final_ids)]

    return {
        "train_families": list(train_families),
        "train_tasks": len(train_tasks),
        "val_tasks": len(val_tasks),
        "final_train_loss": round(losses[-1], 6),
        "validation": eval_model(model, val_tasks),
        "frozen_dev": eval_model(model, dev_tasks),
        "frozen_final": eval_model(model, final_tasks),
        "baseline_visible_dev": baseline_visible_exact(dev_runs),
        "baseline_visible_final": baseline_visible_exact(final_runs),
    }


def main() -> None:
    args = parse_args()
    random.seed(7)
    torch.manual_seed(7)

    slices = json.loads(args.slices.read_text())
    artifact = json.loads(args.artifact.read_text())
    frozen_lookup = load_frozen_tasks(args.artifact)

    payload = {
        "all_family_train": summarize_regime(
            ["affine", "quadratic", "triangular", "alternating"],
            slices,
            artifact,
            frozen_lookup,
        ),
        "dev_family_only_train": summarize_regime(
            ["affine", "quadratic"],
            slices,
            artifact,
            frozen_lookup,
        ),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
