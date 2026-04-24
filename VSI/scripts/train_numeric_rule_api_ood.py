#!/usr/bin/env python3
"""Evaluate training transfer on an API-backed OOD exploit family."""

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


def cubic(offset: int):
    return lambda x: x * x * x + offset


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

OOD_FAMILIES = {
    "cubic": {
        "builder": cubic,
        "params": [(c,) for c in [0, 1, 2, 4, 6, 8]],
    },
    "piecewise_jump": {
        "builder": piecewise_jump,
        "params": [(offset, slope) for offset in [0, 1, 2, 4, 6] for slope in [2, 3, 4]],
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
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


def build_dataset(include_ood: bool, repeats: int = 24) -> List[Dict[str, object]]:
    tasks: List[Dict[str, object]] = []
    idx = 1
    for _ in range(repeats):
        for family_name, spec in LEGACY_FAMILIES.items():
            for params in spec["params"]:
                tasks.append(make_task(family_name, spec["builder"], params, idx))
                idx += 1
        if include_ood:
            for family_name, spec in OOD_FAMILIES.items():
                for params in spec["params"]:
                    tasks.append(make_task(family_name, spec["builder"], params, idx))
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


def load_eval_tasks(artifact_path: Path) -> List[Dict[str, object]]:
    artifact = json.loads(artifact_path.read_text())
    tasks: List[Dict[str, object]] = []
    for task in artifact["tasks"]:
        example = task["attempts"][0]["scores"]
        tasks.append(
            {
                "task_id": task["task_id"],
                "family": task["task_id"].split("_", 1)[0],
                "visible_tests": [
                    [item["input"], item["expected"]] for item in example["visible_results"]
                ],
                "hidden_tests": [
                    [item["input"], item["expected"]] for item in example["hidden_results"]
                ],
            }
        )
    return tasks


def visible_baseline(artifact_path: Path) -> Dict[str, float]:
    artifact = json.loads(artifact_path.read_text())
    exact = 0
    for task in artifact["tasks"]:
        best = max(task["attempts"], key=lambda attempt: float(attempt["scores"]["visible_score"]))
        hidden = best["scores"]["hidden_results"]
        ok = all(item.get("pass", False) for item in hidden)
        exact += 1 if ok else 0
    return {
        "tasks": len(artifact["tasks"]),
        "exact_hidden_match_rate": round(exact / len(artifact["tasks"]), 3),
    }


def summarize_regime(include_ood: bool, eval_tasks: Sequence[Dict[str, object]]) -> Dict[str, Any]:
    dataset = build_dataset(include_ood=include_ood)
    split = int(0.8 * len(dataset))
    train_tasks = dataset[:split]
    val_tasks = dataset[split:]
    model, losses = train_model(train_tasks)
    return {
        "include_ood": include_ood,
        "train_tasks": len(train_tasks),
        "val_tasks": len(val_tasks),
        "final_train_loss": round(losses[-1], 6),
        "validation": eval_model(model, val_tasks),
        "api_ood_eval": eval_model(model, eval_tasks),
    }


def main() -> None:
    args = parse_args()
    random.seed(7)
    torch.manual_seed(7)

    eval_tasks = load_eval_tasks(args.artifact)
    payload = {
        "legacy_only_train": summarize_regime(include_ood=False, eval_tasks=eval_tasks),
        "legacy_plus_ood_train": summarize_regime(include_ood=True, eval_tasks=eval_tasks),
        "visible_attempt_baseline": visible_baseline(args.artifact),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
