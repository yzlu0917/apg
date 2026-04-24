#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path


DEFAULT_LAKE = "/root/.elan/bin/lake"
DEFAULT_REPL_ROOT = "/root/mathlib4-4.15.0/repl"


def split_json_blocks(text: str) -> list[dict]:
    blocks = []
    for chunk in text.strip().split("\n\n"):
        chunk = chunk.strip()
        if chunk:
            blocks.append(json.loads(chunk))
    return blocks


def as_goal_list(payload: dict, *, field: str) -> list[str]:
    if field not in payload or payload[field] is None:
        return []
    value = payload[field]
    if isinstance(value, list):
        return [str(x) for x in value]
    return [str(value)]


def build_repl_stdin(spec: dict) -> str:
    blocks = [json.dumps({"cmd": spec["header_cmd"]}, ensure_ascii=False)]
    proof_state = 0
    for tactic in spec["tactics"]:
        blocks.append(json.dumps({"tactic": tactic, "proofState": proof_state}, ensure_ascii=False))
        proof_state += 1
    return "\n\n".join(blocks) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a minimal Lean replay/extraction smoke pass.")
    parser.add_argument("--input", required=True, help="JSON spec with header_cmd and tactics.")
    parser.add_argument("--output", required=True, help="Path to write structured extraction artifact JSON.")
    parser.add_argument("--raw-output", required=True, help="Path to write raw REPL stdout.")
    parser.add_argument("--repl-root", default=DEFAULT_REPL_ROOT)
    parser.add_argument("--lake-bin", default=DEFAULT_LAKE)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    raw_output_path = Path(args.raw_output)
    repl_root = Path(args.repl_root)

    spec = json.loads(input_path.read_text(encoding="utf-8"))
    stdin_text = build_repl_stdin(spec)

    result = subprocess.run(
        [args.lake_bin, "exe", "repl"],
        cwd=repl_root,
        input=stdin_text,
        text=True,
        capture_output=True,
        check=False,
    )

    raw_output_path.parent.mkdir(parents=True, exist_ok=True)
    raw_output_path.write_text(result.stdout, encoding="utf-8")
    responses = split_json_blocks(result.stdout) if result.stdout.strip() else []

    extraction = {
        "input_path": str(input_path),
        "theorem_id": spec["theorem_id"],
        "header_cmd": spec["header_cmd"],
        "repl_root": str(repl_root),
        "lake_bin": args.lake_bin,
        "returncode": result.returncode,
        "stderr": result.stderr,
        "initial_env": None,
        "initial_proof_state": None,
        "initial_goals": [],
        "steps": [],
        "final_goals": [],
        "replay_status": "unknown",
    }

    if not responses:
        extraction["replay_status"] = "empty_output"
    else:
        init = responses[0]
        extraction["initial_env"] = init.get("env")
        sorries = init.get("sorries", [])
        if sorries:
            first = sorries[0]
            extraction["initial_proof_state"] = first.get("proofState")
            extraction["initial_goals"] = as_goal_list(first, field="goal")

        before_proof_state = extraction["initial_proof_state"]
        before_goals = list(extraction["initial_goals"])

        for idx, tactic in enumerate(spec["tactics"]):
            response = responses[idx + 1] if idx + 1 < len(responses) else {}
            after_proof_state = response.get("proofState")
            after_goals = as_goal_list(response, field="goals")
            extraction["steps"].append(
                {
                    "step_index": idx,
                    "tactic": tactic,
                    "before_proof_state": before_proof_state,
                    "before_goals": before_goals,
                    "after_proof_state": after_proof_state,
                    "after_goals": after_goals,
                    "replay_status": "ok" if after_proof_state is not None else "missing_response",
                }
            )
            before_proof_state = after_proof_state
            before_goals = after_goals

        extraction["final_goals"] = before_goals
        extraction["replay_status"] = "ok" if result.returncode == 0 and len(before_goals) == 0 else "incomplete"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(extraction, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(extraction, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
