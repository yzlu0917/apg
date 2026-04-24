#!/usr/bin/env python3
"""Non-arithmetic ambiguity family based on string transformation traces."""

from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path
from typing import Any, Dict, List

from hybrid_object_gate import build_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    return parser.parse_args()


def build_rewrite_prompt(task: Dict[str, Any], n: int) -> str:
    num_steps = len(task["canonical_trace"])
    return (
        "/no_think\n"
        f"Produce {n} distinct correct step-by-step traces for the task below. "
        "Use different wording styles, but keep the same transformation semantics. "
        f"Use exactly {num_steps} steps. Each step must contain exactly one `=> RESULT` segment. "
        "Do not add intro lines, summary lines, or standalone `=> RESULT` lines. "
        "Return strict JSON only with key `candidates`, where each candidate has keys "
        "`steps` (list of strings) and `final_answer` (string).\n\n"
        f"Task: {task['instruction']}\n"
    )


def extract_state(step: str) -> str:
    if "=>" not in step:
        return ""
    return step.split("=>", 1)[1].strip().strip("'\"")


def exact_surface_ok(candidate: Dict[str, Any], canonical_trace: List[str]) -> bool:
    return candidate.get("steps", []) == canonical_trace


def semantic_ok(candidate: Dict[str, Any], canonical_trace: List[str]) -> bool:
    steps = candidate.get("steps", [])
    if len(steps) != len(canonical_trace):
        return False
    return [extract_state(step) for step in steps] == [
        extract_state(step) for step in canonical_trace
    ]


def final_ok(candidate: Dict[str, Any], final_answer: str) -> bool:
    return str(candidate.get("final_answer", "")).strip() == final_answer


def maybe_get_candidates(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    candidates = payload.get("candidates")
    if isinstance(candidates, list):
        return candidates
    raise ValueError(f"Unexpected payload: {payload}")


def aggregate_usage(records: List[Dict[str, Any]]) -> Dict[str, int]:
    usage = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    for record in records:
        if "_usage" not in record:
            continue
        usage["calls"] += 1
        usage["prompt_tokens"] += int(record["_usage"].get("prompt_tokens", 0))
        usage["completion_tokens"] += int(record["_usage"].get("completion_tokens", 0))
        usage["total_tokens"] += int(record["_usage"].get("total_tokens", 0))
    return usage


def main() -> None:
    args = parse_args()
    config = json.loads(args.config.read_text())
    tasks = config.pop("tasks")
    model = build_model(config)
    system_prompt = (
        "Return valid JSON only. Do not use markdown fences. "
        "Do not output explanations before or after the JSON object."
    )

    runs = []
    payloads = []
    for task in tasks:
        payload = model.generate_json(
            system_prompt=system_prompt,
            user_prompt=build_rewrite_prompt(task, int(config["num_rewrite_candidates"])),
            temperature=float(config["temperature"]),
            top_p=float(config["top_p"]),
            max_new_tokens=int(config["max_new_tokens"]),
        )
        payloads.append(payload)
        candidates = maybe_get_candidates(payload)
        for candidate in candidates:
            candidate["correct"] = final_ok(candidate, task["final_answer"])
            candidate["surface_rejected"] = candidate["correct"] and not exact_surface_ok(
                candidate, task["canonical_trace"]
            )
            candidate["semantic_rejected"] = candidate["correct"] and not semantic_ok(
                candidate, task["canonical_trace"]
            )
        correct = [candidate for candidate in candidates if candidate["correct"]]
        surface_ambiguity = round(
            sum(candidate["surface_rejected"] for candidate in correct) / len(correct), 3
        ) if correct else 0.0
        semantic_ambiguity = round(
            sum(candidate["semantic_rejected"] for candidate in correct) / len(correct), 3
        ) if correct else 0.0
        runs.append(
            {
                "task_id": task["task_id"],
                "instruction": task["instruction"],
                "canonical_trace": task["canonical_trace"],
                "final_answer": task["final_answer"],
                "candidates": candidates,
                "surface_ambiguity": surface_ambiguity,
                "semantic_ambiguity": semantic_ambiguity,
            }
        )

    payload = {
        "provider": config.get("provider", "local"),
        "aggregate": {
            "avg_surface_ambiguity": round(
                sum(run["surface_ambiguity"] for run in runs) / len(runs), 3
            ),
            "avg_semantic_ambiguity": round(
                sum(run["semantic_ambiguity"] for run in runs) / len(runs), 3
            ),
            "tasks_with_surface_ambiguity": sum(1 for run in runs if run["surface_ambiguity"] > 0),
            "tasks_with_semantic_ambiguity": sum(1 for run in runs if run["semantic_ambiguity"] > 0),
            "api_usage": aggregate_usage(payloads),
        },
        "runs": runs,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload["aggregate"], indent=2))


if __name__ == "__main__":
    main()
