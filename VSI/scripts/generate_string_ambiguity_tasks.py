#!/usr/bin/env python3
"""Generate a larger non-arithmetic ambiguity family config."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List


TEMPLATES = [
    {
        "task_id": "reverse_wrap",
        "instruction": "Start from the string `{s}`. First reverse it, then wrap it in square brackets.",
        "canonical_trace": [
            "reverse {s} => {r}",
            "wrap {r} in [] => [{r}]",
        ],
        "final_answer": "[{r}]",
    },
    {
        "task_id": "upper_suffix",
        "instruction": "Start from the string `{s}`. First uppercase it, then append `!`.",
        "canonical_trace": [
            "uppercase {s} => {u}",
            "append ! to {u} => {u}!",
        ],
        "final_answer": "{u}!",
    },
    {
        "task_id": "duplicate_prefix",
        "instruction": "Start from the string `{s}`. First duplicate the string, then prefix it with `#`.",
        "canonical_trace": [
            "duplicate {s} => {d}",
            "prefix # to {d} => #{d}",
        ],
        "final_answer": "#{d}",
    },
]

SEEDS = [
    "code",
    "mix",
    "ab",
    "trace",
    "lens",
    "vsi",
    "logic",
    "audit",
    "proto",
    "delta",
    "map",
    "gate",
]


def build_task(template: Dict[str, object], seed: str, idx: int) -> Dict[str, object]:
    values = {
        "s": seed,
        "r": seed[::-1],
        "u": seed.upper(),
        "d": seed * 2,
    }
    return {
        "task_id": f"{template['task_id']}_{idx:02d}",
        "instruction": str(template["instruction"]).format(**values),
        "canonical_trace": [step.format(**values) for step in template["canonical_trace"]],
        "final_answer": str(template["final_answer"]).format(**values),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tasks: List[Dict[str, object]] = []
    idx = 1
    for template, seed in zip(TEMPLATES * 4, SEEDS):
        tasks.append(build_task(template, seed, idx))
        idx += 1

    payload = {
        "provider": "openai_compat",
        "temperature": 0.7,
        "top_p": 0.8,
        "max_new_tokens": 320,
        "num_rewrite_candidates": 3,
        "api": {
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "model": "ep-20251213141929-gk2jb",
            "api_key_env": "VSI_API_KEY",
            "timeout_seconds": 120,
        },
        "tasks": tasks,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"num_tasks": len(tasks), "out": str(args.out)}, indent=2))


if __name__ == "__main__":
    main()

