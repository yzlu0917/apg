#!/usr/bin/env python3
"""Structured decoder probe for the semantic-v2 exploit family.

This is not a generic learner. It is a bounded upper-bound style probe:
given a finite rule library, recover the rule label from visible I/O and
measure whether semantic-v2 conversion is bottlenecked by the decoder rather
than the family itself.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Sequence


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
    return parser.parse_args()


def load_eval_tasks(artifact_path: Path) -> List[Dict[str, object]]:
    artifact = json.loads(artifact_path.read_text())
    tasks: List[Dict[str, object]] = []
    for task in artifact["tasks"]:
        example = task["attempts"][0]["scores"]
        tasks.append(
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
    return tasks


def visible_baseline(artifact_path: Path) -> Dict[str, float]:
    artifact = json.loads(artifact_path.read_text())
    exact = 0
    for task in artifact["tasks"]:
        best = max(task["attempts"], key=lambda attempt: float(attempt["scores"]["visible_score"]))
        hidden = best["scores"]["hidden_results"]
        exact += 1 if all(item.get("pass", False) for item in hidden) else 0
    return {"tasks": len(artifact["tasks"]), "exact_hidden_match_rate": round(exact / len(artifact["tasks"]), 3)}


def candidate_labels(include_v2: bool) -> List[str]:
    labels: List[str] = []
    for family, spec in LEGACY_SPECS.items():
        labels.extend(f"{family}|{param}" for param in spec["params"])
    if include_v2:
        for family, spec in V2_SPECS.items():
            labels.extend(f"{family}|{param}" for param in spec["params"])
    return labels


def apply_label(label: str, text: str) -> str:
    family, param = label.split("|", 1)
    if family in LEGACY_SPECS:
        return LEGACY_SPECS[family]["fn"](param, text)
    return V2_SPECS[family]["fn"](param, text)


def consistent_labels(task: Dict[str, object], labels: Sequence[str]) -> List[str]:
    matches = []
    for label in labels:
        ok = True
        for inp, expected in task["visible_tests"]:
            if apply_label(label, str(inp)) != str(expected):
                ok = False
                break
        if ok:
            matches.append(label)
    return matches


def summarize(tasks: Sequence[Dict[str, object]], include_v2: bool) -> Dict[str, Any]:
    labels = candidate_labels(include_v2=include_v2)
    exact = 0
    ambiguities = 0
    no_match = 0
    predictions = []
    for task in tasks:
        matches = consistent_labels(task, labels)
        if not matches:
            no_match += 1
            predictions.append({"task_id": task["task_id"], "matches": [], "ok": False})
            continue
        if len(matches) > 1:
            ambiguities += 1
        chosen = matches[0]
        pred_outputs = [apply_label(chosen, item[0]) for item in task["hidden_tests"]]
        gold_outputs = [item[1] for item in task["hidden_tests"]]
        ok = pred_outputs == gold_outputs
        exact += 1 if ok else 0
        predictions.append({"task_id": task["task_id"], "matches": matches, "chosen": chosen, "ok": ok})
    return {
        "candidate_labels": len(labels),
        "tasks": len(tasks),
        "exact_hidden_match_rate": round(exact / len(tasks), 3),
        "tasks_with_no_match": no_match,
        "tasks_with_multiple_matches": ambiguities,
        "predictions": predictions,
    }


def main() -> None:
    args = parse_args()
    tasks = load_eval_tasks(args.artifact)
    payload = {
        "legacy_only_library": summarize(tasks, include_v2=False),
        "legacy_plus_v2_library": summarize(tasks, include_v2=True),
        "visible_attempt_baseline": visible_baseline(args.artifact),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
