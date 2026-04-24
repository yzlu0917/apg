#!/usr/bin/env python3
"""Summarize frozen dev/final slices from artifact files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slices", required=True, type=Path)
    parser.add_argument("--string-artifact", required=True, type=Path)
    parser.add_argument("--exploit-artifact", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    return parser.parse_args()


def summarize_string_runs(runs: List[Dict[str, Any]], ids: List[str]) -> Dict[str, float]:
    selected = [run for run in runs if run["task_id"] in ids]
    return {
        "count": len(selected),
        "avg_surface_ambiguity": round(
            sum(run["surface_ambiguity"] for run in selected) / len(selected), 3
        ),
        "avg_semantic_ambiguity": round(
            sum(run["semantic_ambiguity"] for run in selected) / len(selected), 3
        ),
    }


def summarize_exploit_runs(tasks: List[Dict[str, Any]], ids: List[str]) -> Dict[str, float]:
    selected = [task for task in tasks if task["task_id"] in ids]
    return {
        "count": len(selected),
        "avg_best_exploit_gap": round(
            sum(task["best_exploit_gap"] for task in selected) / len(selected), 3
        ),
        "avg_best_judge_gap": round(
            sum(task["best_judge_gap"] for task in selected) / len(selected), 3
        ),
        "tasks_with_exploit": sum(1 for task in selected if task["best_exploit_gap"] > 0),
        "tasks_with_judge_gap": sum(1 for task in selected if task["best_judge_gap"] > 0),
    }


def main() -> None:
    args = parse_args()
    slices = json.loads(args.slices.read_text())
    string_artifact = json.loads(args.string_artifact.read_text())
    exploit_artifact = json.loads(args.exploit_artifact.read_text())

    string_cfg = slices["families"]["string_ambiguity_large"]
    exploit_cfg = slices["families"]["exploit_code_large"]

    payload = {
        "phase": slices["phase"],
        "string_ambiguity_large": {
            "dev": summarize_string_runs(string_artifact["runs"], string_cfg["dev_task_ids"]),
            "final": summarize_string_runs(string_artifact["runs"], string_cfg["final_task_ids"]),
        },
        "exploit_code_large": {
            "dev": summarize_exploit_runs(exploit_artifact["tasks"], exploit_cfg["dev_task_ids"]),
            "final": summarize_exploit_runs(exploit_artifact["tasks"], exploit_cfg["final_task_ids"]),
        },
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
