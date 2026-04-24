#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path
from typing import Dict, List


DEFAULT_LAKE = "/root/.elan/bin/lake"
DEFAULT_REPL_RELATIVE = "../repl/.lake/build/bin/repl"


def load_jsonl(path: Path) -> List[Dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def split_json_blocks(text: str) -> List[Dict]:
    blocks = []
    for chunk in text.strip().split("\n\n"):
        chunk = chunk.strip()
        if chunk:
            blocks.append(json.loads(chunk))
    return blocks


def as_goal_list(value) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value]
    return [str(value)]


def replay_candidate(row: Dict, tactic: str, lake_bin: str, repl_relative: str) -> Dict:
    blocks = [
        {"path": row["source_file"], "allTactics": True},
        {"tactic": tactic, "proofState": row["proof_state"]},
    ]
    stdin_text = "\n\n".join(json.dumps(block, ensure_ascii=False) for block in blocks) + "\n"
    result = subprocess.run(
        [lake_bin, "env", repl_relative],
        cwd=row["project_root"],
        input=stdin_text,
        text=True,
        capture_output=True,
        check=False,
    )

    out = {
        "returncode": result.returncode,
        "stderr": result.stderr,
        "before_goals": [],
        "after_goals": [],
        "replay_status": "unknown",
        "messages": [],
        "tactic": tactic,
    }
    responses = split_json_blocks(result.stdout) if result.stdout.strip() else []
    if not responses:
        out["replay_status"] = "empty_output"
        return out

    init = responses[0]
    sorries = init.get("sorries", [])
    target = None
    for sorry in sorries:
        if sorry.get("proofState") == row["proof_state"]:
            target = sorry
            break
    if target is None:
        out["messages"].extend(init.get("messages", []))
        out["replay_status"] = "missing_context"
        return out

    out["before_goals"] = as_goal_list(target.get("goal"))
    out["messages"].extend(init.get("messages", []))
    if len(responses) < 2:
        out["replay_status"] = "missing_candidate_response"
        return out

    cand = responses[1]
    out["messages"].extend(cand.get("messages", []))
    has_error = any(m.get("severity") == "error" for m in cand.get("messages", []))
    if "proofState" in cand:
        out["after_goals"] = as_goal_list(cand.get("goals"))
        out["replay_status"] = "lean_error" if has_error else "ok"
    else:
        message = cand.get("message")
        if message is not None:
            out["messages"].append({"severity": "error", "data": message})
        out["replay_status"] = "lean_error"
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay API-generated candidates on Putnam file-mode proof states.")
    parser.add_argument("--generated", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--lake-bin", default=DEFAULT_LAKE)
    parser.add_argument("--repl-relative", default=DEFAULT_REPL_RELATIVE)
    args = parser.parse_args()

    rows = load_jsonl(Path(args.generated))
    out_rows = []
    replay_ok = 0
    replay_err = 0

    for row in rows:
        replayed = []
        for tactic in row["generated_candidates"]:
            rec = replay_candidate(row, tactic, args.lake_bin, args.repl_relative)
            replayed.append(rec)
            if rec["replay_status"] == "ok":
                replay_ok += 1
            else:
                replay_err += 1
        out_rows.append(
            {
                "state_id": row["state_id"],
                "theorem_id": row["theorem_id"],
                "before_goals": row["before_goals"],
                "source_file": row["source_file"],
                "project_root": row["project_root"],
                "proof_state": row["proof_state"],
                "generated_candidates": replayed,
                "api_provenance": row.get("api_provenance"),
            }
        )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for row in out_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = {
        "num_states": len(out_rows),
        "num_generated_candidates": sum(len(r["generated_candidates"]) for r in out_rows),
        "num_replay_ok": replay_ok,
        "num_replay_error": replay_err,
    }
    summary_path = Path(args.summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
