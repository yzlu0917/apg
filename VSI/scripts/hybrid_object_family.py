#!/usr/bin/env python3
"""Run the hybrid object bootstrap across a small family of problems."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any, Dict, List

from hybrid_object_gate import run_hybrid_bootstrap


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    return parser.parse_args()


def aggregate_usage(runs: List[Dict[str, Any]]) -> Dict[str, int]:
    usage = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    for run in runs:
        for record in run["summary"].get("api_usage_records", []):
            usage["calls"] += 1
            usage["prompt_tokens"] += int(record.get("prompt_tokens", 0))
            usage["completion_tokens"] += int(record.get("completion_tokens", 0))
            usage["total_tokens"] += int(record.get("total_tokens", 0))
    return usage


def main() -> None:
    args = parse_args()
    config = json.loads(args.config.read_text())
    problems = config.pop("problems")

    runs = []
    for idx, problem in enumerate(problems, start=1):
        run_config = copy.deepcopy(config)
        run_config["problem"] = problem
        result = run_hybrid_bootstrap(run_config)
        result["problem_id"] = idx
        runs.append(result)

    avg_ambiguity = round(
        sum(run["rewrite_phase"]["surface_ambiguity_score"] for run in runs) / len(runs), 3
    )
    avg_semantic_ambiguity = round(
        sum(run["rewrite_phase"]["semantic_ambiguity_score"] for run in runs) / len(runs), 3
    )
    avg_disagreement = round(
        sum(run["rewrite_phase"]["judge_disagreement"] for run in runs) / len(runs), 3
    )
    max_exploitability = round(
        max(run["exploit_phase"]["exploitability_score"] for run in runs), 3
    )

    payload = {
        "provider": config.get("provider", "local"),
        "num_problems": len(runs),
        "aggregate": {
            "avg_surface_ambiguity": avg_ambiguity,
            "avg_semantic_ambiguity": avg_semantic_ambiguity,
            "avg_judge_disagreement": avg_disagreement,
            "max_exploitability": max_exploitability,
            "object_signal_alive_rate": round(
                sum(1 for run in runs if run["summary"]["object_signal_alive"]) / len(runs),
                3,
            ),
            "api_usage": aggregate_usage(runs),
        },
        "runs": runs,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")

    print(json.dumps(payload["aggregate"], indent=2))


if __name__ == "__main__":
    main()
