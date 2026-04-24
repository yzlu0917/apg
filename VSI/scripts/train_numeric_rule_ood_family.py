#!/usr/bin/env python3
"""Test training transfer on a structurally different held-out numeric family."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import torch


def affine(a: int, b: int):
    return lambda x: a * x + b


def quadratic(c: int):
    return lambda x: x * x + c


def triangular(c: int):
    return lambda x: (x * (x + 1)) // 2 + c


def alternating(scale: int):
    return lambda x: x * scale if x % 2 == 0 else -x * scale


def piecewise_jump(offset: int, slope: int):
    def solve(x: int) -> int:
        if x <= 2:
            return x + offset
        return slope * x + offset

    return solve


LEGACY_FAMILIES = {
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

PIECEWISE_TRAIN_PARAMS = [(offset, slope) for offset in [0, 2, 4] for slope in [2, 3]]
PIECEWISE_EVAL_PARAMS = [(offset, slope) for offset in [1, 3, 5] for slope in [2, 4]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
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


def build_dataset(repeats: int, include_piecewise: bool) -> List[Dict[str, object]]:
    tasks: List[Dict[str, object]] = []
    idx = 1
    for _ in range(repeats):
        for family_name, spec in LEGACY_FAMILIES.items():
            for params in spec["params"]:
                tasks.append(make_task(family_name, spec["builder"], params, idx))
                idx += 1
        if include_piecewise:
            for params in PIECEWISE_TRAIN_PARAMS:
                tasks.append(make_task("piecewise_jump", piecewise_jump, params, idx))
                idx += 1
    random.shuffle(tasks)
    return tasks


def build_piecewise_eval_tasks() -> List[Dict[str, object]]:
    tasks: List[Dict[str, object]] = []
    idx = 1
    for params in PIECEWISE_EVAL_PARAMS:
        tasks.append(make_task("piecewise_jump_eval", piecewise_jump, params, idx))
        idx += 1
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


def quadratic_extrapolation(task: Dict[str, object]) -> List[int]:
    visible = task["visible_tests"]
    y1, y2, y3 = [pair[1] for pair in visible]
    d1 = y2 - y1
    d2 = y3 - y2
    second = d2 - d1
    y4 = y3 + d2 + second
    y5 = y4 + d2 + 2 * second
    return [y4, y5]


def quadratic_baseline(tasks: Sequence[Dict[str, object]]) -> Dict[str, float]:
    exact = 0
    for task in tasks:
        pred = quadratic_extrapolation(task)
        hidden = [pair[1] for pair in task["hidden_tests"]]
        if pred == hidden:
            exact += 1
    return {
        "tasks": len(tasks),
        "exact_hidden_match_rate": round(exact / len(tasks), 3),
    }


def lookup_baseline(tasks: Sequence[Dict[str, object]]) -> Dict[str, float]:
    return {
        "tasks": len(tasks),
        "exact_hidden_match_rate": 0.0,
    }


def summarize_regime(include_piecewise: bool) -> Dict[str, object]:
    dataset = build_dataset(repeats=24, include_piecewise=include_piecewise)
    split = int(0.8 * len(dataset))
    train_tasks = dataset[:split]
    val_tasks = dataset[split:]
    model, losses = train_model(train_tasks)
    eval_tasks = build_piecewise_eval_tasks()
    return {
        "include_piecewise": include_piecewise,
        "train_tasks": len(train_tasks),
        "val_tasks": len(val_tasks),
        "final_train_loss": round(losses[-1], 6),
        "validation": eval_model(model, val_tasks),
        "heldout_piecewise_eval": eval_model(model, eval_tasks),
    }


def main() -> None:
    args = parse_args()
    random.seed(7)
    torch.manual_seed(7)

    eval_tasks = build_piecewise_eval_tasks()
    payload = {
        "legacy_only_train": summarize_regime(include_piecewise=False),
        "legacy_plus_piecewise_train": summarize_regime(include_piecewise=True),
        "quadratic_extrapolation_baseline": quadratic_baseline(eval_tasks),
        "visible_lookup_baseline": lookup_baseline(eval_tasks),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
