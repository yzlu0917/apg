#!/usr/bin/env python3

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "object_gate.json"


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    artifact_root = ROOT / config["artifacts"]["root"]
    subdirs = [
        artifact_root,
        ROOT / config["artifacts"]["samples_dir"],
        ROOT / config["artifacts"]["interventions_dir"],
        ROOT / config["artifacts"]["rollouts_dir"],
        ROOT / config["artifacts"]["analysis_dir"],
    ]

    for path in subdirs:
        path.mkdir(parents=True, exist_ok=True)

    run_state_path = artifact_root / "run_state.json"
    manifest_template_path = artifact_root / "manifest.template.json"

    if not run_state_path.exists():
        run_state = {
            "phase": config["phase"],
            "status": "ready_for_day1_execution",
            "date_initialized": config["date_frozen"],
            "task_source_status": config["task_source"]["primary_status"],
            "family_names_frozen": config["task_source"]["family_names_frozen"],
            "next_actions": [
                "Connect the primary task source in the infer environment.",
                "Freeze exact family names in configs/object_gate.json.",
                "Create the first prompt manifest in artifacts/object_gate/samples/."
            ]
        }
        run_state_path.write_text(
            json.dumps(run_state, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )

    if not manifest_template_path.exists():
        manifest_template = {
            "prompt_id": "replace-me",
            "slice": "dev",
            "family": "freeze-after-task-source-is-connected",
            "difficulty_stratum": "high_dependency_or_shallow",
            "seed": 1729,
            "model_tier": config["environment"]["default_model_tier"],
            "trace_budget": config["budgets"]["traces_per_prompt"],
            "candidate_steps": [],
            "notes": "Template only. Fill after the task source is connected."
        }
        manifest_template_path.write_text(
            json.dumps(manifest_template, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )

    summary = {
        "config": str(CONFIG_PATH.relative_to(ROOT)),
        "artifact_root": str(artifact_root.relative_to(ROOT)),
        "run_state": str(run_state_path.relative_to(ROOT)),
        "manifest_template": str(manifest_template_path.relative_to(ROOT)),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
