#!/usr/bin/env python3
"""Train a tiny model to infer numeric hidden rules from visible examples.

This is a materially different conversion class from routing/filtering:
we train a model that maps visible test pairs directly to hidden outputs.
"""

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


FAMILIES = [
    ("affine", affine, [(1, 0), (1, 2), (2, 1), (2, 3), (3, 1), (3, 4)]),
    ("quadratic", quadratic, [(-1,), (0,), (1,), (3,), (5,), (7,)]),
    ("triangular", triangular, [(0,), (1,), (2,), (3,), (4,), (5,)]),
    ("alternating", alternating, [(1,), (2,), (3,), (4,), (5,), (6,)]),
]


def make_task(name: str, fn, params: Tuple[int, ...], idx: int) -> Dict[str, object]:
    solver = fn(*params)
    visible = [[1, solver(1)], [2, solver(2)], [3, solver(3)]]
    hidden = [[4, solver(4)], [5, solver(5)]]
    return {
        "task_id": f"{name}_{idx:04d}",
        "family": name,
        "params": params,
        "visible_tests": visible,
        "hidden_tests": hidden,
    }


def build_dataset(repeats: int = 40) -> List[Dict[str, object]]:
    tasks: List[Dict[str, object]] = []
    idx = 1
    for _ in range(repeats):
        for name, fn, params_list in FAMILIES:
            for params in params_list:
                tasks.append(make_task(name, fn, params, idx))
                idx += 1
    random.shuffle(tasks)
    return tasks


def features(task: Dict[str, object]) -> torch.Tensor:
    visible = task["visible_tests"]
    # input: outputs for x=1,2,3 plus pairwise differences
    y1, y2, y3 = [pair[1] for pair in visible]
    diffs = [y2 - y1, y3 - y2]
    feats = torch.tensor([y1, y2, y3, diffs[0], diffs[1]], dtype=torch.float32)
    return feats


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


def eval_frozen_numeric(tasks: Sequence[Dict[str, object]], frozen_ids: Sequence[str], model: SolverNet) -> Dict[str, float]:
    selected = [task for task in tasks if task["task_id"] in set(frozen_ids)]
    return eval_model(model, selected)


def load_frozen_numeric_tasks() -> Dict[str, List[Dict[str, object]]]:
    artifact = json.loads(Path("artifacts/object_gate/exploit_code_tasks_large_api.json").read_text())
    numeric_tasks = []
    for task in artifact["tasks"]:
        if task["task_id"] == "string_wrap":
            continue
        example = task["attempts"][0]["scores"]
        numeric_tasks.append(
            {
                "task_id": task["task_id"],
                "visible_tests": [
                    [item["input"], item["expected"]] for item in example["visible_results"]
                ],
                "hidden_tests": [
                    [item["input"], item["expected"]] for item in example["hidden_results"]
                ],
            }
        )
    return {task["task_id"]: task for task in numeric_tasks}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slices", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    random.seed(7)
    torch.manual_seed(7)

    dataset = build_dataset()
    split = int(0.8 * len(dataset))
    train_tasks = dataset[:split]
    val_tasks = dataset[split:]

    model, losses = train_model(train_tasks)
    val_summary = eval_model(model, val_tasks)

    slices = json.loads(args.slices.read_text())
    exploit = slices["families"]["exploit_code_large"]
    frozen_ids = exploit["dev_task_ids"] + exploit["final_task_ids"]
    frozen_lookup = load_frozen_numeric_tasks()
    frozen_tasks = [frozen_lookup[task_id] for task_id in frozen_ids if task_id in frozen_lookup]
    frozen_summary = eval_model(model, frozen_tasks)

    payload = {
        "train_tasks": len(train_tasks),
        "val_tasks": len(val_tasks),
        "final_train_loss": round(losses[-1], 6),
        "validation": val_summary,
        "frozen_numeric_subset": frozen_summary,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
