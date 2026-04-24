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


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the project-owned Lean REPL smoke test.")
    parser.add_argument("--input", required=True, help="Path to blank-line-separated JSON REPL commands.")
    parser.add_argument("--output", required=True, help="Path to write raw REPL stdout.")
    parser.add_argument("--summary", required=True, help="Path to write parsed smoke summary JSON.")
    parser.add_argument("--repl-root", default=DEFAULT_REPL_ROOT)
    parser.add_argument("--lake-bin", default=DEFAULT_LAKE)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    summary_path = Path(args.summary)
    repl_root = Path(args.repl_root)

    stdin_text = input_path.read_text(encoding="utf-8")
    result = subprocess.run(
        [args.lake_bin, "exe", "repl"],
        cwd=repl_root,
        input=stdin_text,
        text=True,
        capture_output=True,
        check=False,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.stdout, encoding="utf-8")

    responses = split_json_blocks(result.stdout) if result.stdout.strip() else []
    final_payload = responses[-1] if responses else {}
    final_goals = final_payload.get("goals", [])
    summary = {
        "input_path": str(input_path),
        "repl_root": str(repl_root),
        "lake_bin": args.lake_bin,
        "returncode": result.returncode,
        "num_responses": len(responses),
        "num_sorry_responses": sum(1 for r in responses if "sorries" in r),
        "proof_states_returned": [r.get("proofState") for r in responses if "proofState" in r],
        "final_goals_count": len(final_goals),
        "final_goals": final_goals,
        "stderr": result.stderr,
    }

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
