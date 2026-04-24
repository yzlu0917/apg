#!/usr/bin/env python3
"""Minimal conversion protocol on the string ambiguity family.

Use the frozen dev split to learn whether each template should use a cheap
surface verifier or a more expensive semantic verifier, then evaluate on the
frozen final split.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--slices", required=True, type=Path)
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    return parser.parse_args()


def template_name(task_id: str) -> str:
    return task_id.rsplit("_", 1)[0]


def surface_accept(run: Dict[str, Any]) -> float:
    candidates = run["candidates"]
    if any(candidate["correct"] and not candidate["surface_rejected"] for candidate in candidates):
        return 1.0
    return 0.0


def semantic_accept(run: Dict[str, Any]) -> float:
    candidates = run["candidates"]
    if any(candidate["correct"] and not candidate["semantic_rejected"] for candidate in candidates):
        return 1.0
    return 0.0


def strategy_outcome(
    run: Dict[str, Any],
    strategy: str,
    route_templates: Dict[str, str],
    surface_cost: float,
    semantic_cost: float,
) -> Dict[str, float]:
    if strategy == "always_surface":
        return {"utility": surface_accept(run), "cost": surface_cost}
    if strategy == "always_semantic":
        return {"utility": semantic_accept(run), "cost": semantic_cost}
    if strategy == "routed":
        choice = route_templates[template_name(run["task_id"])]
        if choice == "semantic":
            return {"utility": semantic_accept(run), "cost": semantic_cost}
        return {"utility": surface_accept(run), "cost": surface_cost}
    raise ValueError(f"Unknown strategy: {strategy}")


def summarize_strategy(
    runs: List[Dict[str, Any]],
    strategy: str,
    route_templates: Dict[str, str],
    surface_cost: float,
    semantic_cost: float,
) -> Dict[str, float]:
    outcomes = [
        strategy_outcome(run, strategy, route_templates, surface_cost, semantic_cost)
        for run in runs
    ]
    total_utility = sum(item["utility"] for item in outcomes)
    total_cost = sum(item["cost"] for item in outcomes)
    return {
        "tasks": len(runs),
        "accepted_correct": round(total_utility, 3),
        "total_cost": round(total_cost, 3),
        "utility_per_cost": round(total_utility / total_cost, 3) if total_cost else 0.0,
    }


def main() -> None:
    args = parse_args()
    config = json.loads(args.config.read_text())
    slices = json.loads(args.slices.read_text())
    artifact = json.loads(args.artifact.read_text())

    dev_ids = set(slices["families"]["string_ambiguity_large"]["dev_task_ids"])
    final_ids = set(slices["families"]["string_ambiguity_large"]["final_task_ids"])

    dev_runs = [run for run in artifact["runs"] if run["task_id"] in dev_ids]
    final_runs = [run for run in artifact["runs"] if run["task_id"] in final_ids]

    dev_by_template: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for run in dev_runs:
        dev_by_template[template_name(run["task_id"])].append(run)

    route_templates: Dict[str, str] = {}
    template_stats: Dict[str, Dict[str, float]] = {}
    for name, runs in dev_by_template.items():
        surface_gain = sum(surface_accept(run) for run in runs) / len(runs)
        semantic_gain = sum(semantic_accept(run) for run in runs) / len(runs)
        gain_delta = semantic_gain - surface_gain
        choice = (
            "semantic"
            if gain_delta >= float(config["route_gain_threshold"])
            else "surface"
        )
        route_templates[name] = choice
        template_stats[name] = {
            "dev_surface_accept": round(surface_gain, 3),
            "dev_semantic_accept": round(semantic_gain, 3),
            "gain_delta": round(gain_delta, 3),
            "chosen_verifier": choice,
        }

    payload = {
        "template_routing": template_stats,
        "final_results": {
            "always_surface": summarize_strategy(
                final_runs,
                "always_surface",
                route_templates,
                float(config["surface_cost"]),
                float(config["semantic_cost"]),
            ),
            "always_semantic": summarize_strategy(
                final_runs,
                "always_semantic",
                route_templates,
                float(config["surface_cost"]),
                float(config["semantic_cost"]),
            ),
            "routed": summarize_strategy(
                final_runs,
                "routed",
                route_templates,
                float(config["surface_cost"]),
                float(config["semantic_cost"]),
            ),
        },
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
