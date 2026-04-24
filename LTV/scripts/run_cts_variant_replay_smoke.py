#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path


DEFAULT_LAKE = "/root/.elan/bin/lake"
DEFAULT_REPL_ROOT = "/root/mathlib4-4.15.0/repl"


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def split_json_blocks(text: str) -> list[dict]:
    blocks = []
    for chunk in text.strip().split("\n\n"):
        chunk = chunk.strip()
        if chunk:
            blocks.append(json.loads(chunk))
    return blocks


def as_goal_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value]
    return [str(value)]


def build_prefix_command(header: str, prefix_steps: list[str]) -> str:
    lines = [header]
    lines.extend(prefix_steps)
    lines.append("  sorry")
    return "\n".join(lines)


def run_repl_command(command: str, tactic: str, repl_root: Path, lake_bin: str) -> tuple[int, str, str]:
    blocks = [
        {"cmd": command},
        {"tactic": tactic, "proofState": 0},
    ]
    stdin_text = "\n\n".join(json.dumps(b, ensure_ascii=False) for b in blocks) + "\n"
    result = subprocess.run(
        [lake_bin, "exe", "repl"],
        cwd=repl_root,
        input=stdin_text,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode, result.stdout, result.stderr


def replay_candidate(
    *,
    header: str,
    prefix_steps: list[str],
    tactic: str,
    repl_root: Path,
    lake_bin: str,
) -> dict:
    command = build_prefix_command(header, prefix_steps)
    returncode, stdout, stderr = run_repl_command(command, tactic, repl_root, lake_bin)
    responses = split_json_blocks(stdout) if stdout.strip() else []

    out = {
        "returncode": returncode,
        "stderr": stderr,
        "raw_num_responses": len(responses),
        "parser_status": "unknown",
        "before_goals": [],
        "after_goals": [],
        "before_proof_state": None,
        "after_proof_state": None,
        "messages": [],
        "replay_status": "unknown",
    }

    if not responses:
        out["parser_status"] = "empty_output"
        out["replay_status"] = "empty_output"
        return out

    init = responses[0]
    sorries = init.get("sorries", [])
    out["messages"].extend(init.get("messages", []))
    if not sorries:
        out["parser_status"] = "missing_sorry"
        out["replay_status"] = "missing_context"
        return out

    first = sorries[0]
    out["before_proof_state"] = first.get("proofState")
    out["before_goals"] = as_goal_list(first.get("goal"))
    out["parser_status"] = "ok"

    if len(responses) < 2:
        out["replay_status"] = "missing_candidate_response"
        return out

    cand = responses[1]
    candidate_messages = cand.get("messages", [])
    has_error_message = any(m.get("severity") == "error" for m in candidate_messages)
    if "proofState" in cand:
        out["after_proof_state"] = cand.get("proofState")
        out["after_goals"] = as_goal_list(cand.get("goals"))
        out["messages"].extend(candidate_messages)
        out["replay_status"] = "lean_error" if has_error_message else "ok"
    else:
        message = cand.get("message")
        if message is not None:
            out["messages"].append({"severity": "error", "data": message})
        out["replay_status"] = "lean_error"

    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay a smoke subset of CTS source/variant candidates against Lean.")
    parser.add_argument("--cts-panel", required=True)
    parser.add_argument("--lean-raw", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--max-pairs", type=int, default=8)
    parser.add_argument("--repl-root", default=DEFAULT_REPL_ROOT)
    parser.add_argument("--lake-bin", default=DEFAULT_LAKE)
    args = parser.parse_args()

    cts_rows = load_jsonl(Path(args.cts_panel))
    lean_rows = {row["theorem_id"]: row for row in load_jsonl(Path(args.lean_raw))}
    repl_root = Path(args.repl_root)

    selected = cts_rows[: args.max_pairs]
    out_rows = []
    for row in selected:
        theorem = lean_rows.get(row["theorem_id"])
        if theorem is None:
            out_rows.append(
                {
                    "pair_id": row["pair_id"],
                    "theorem_id": row["theorem_id"],
                    "step_index": row["step_index"],
                    "pair_type": row.get("pair_label"),
                    "shared_pre_state_status": "missing_context",
                }
            )
            continue

        prefix_steps = theorem["steps"][: row["step_index"]]
        source = replay_candidate(
            header=theorem["header"],
            prefix_steps=prefix_steps,
            tactic=row["source_candidate"]["step_text"],
            repl_root=repl_root,
            lake_bin=args.lake_bin,
        )
        variant = replay_candidate(
            header=theorem["header"],
            prefix_steps=prefix_steps,
            tactic=row["variant_candidate"]["step_text"],
            repl_root=repl_root,
            lake_bin=args.lake_bin,
        )

        shared_before_ok = source["before_goals"] == variant["before_goals"] and source["before_goals"] != []
        out_rows.append(
            {
                "pair_id": row["pair_id"],
                "theorem_id": row["theorem_id"],
                "step_index": row["step_index"],
                "pair_type": row.get("pair_label"),
                "shared_pre_state_status": "ok" if shared_before_ok else "mismatch",
                "before_goals": source["before_goals"],
                "prefix_steps": prefix_steps,
                "source": {
                    "tactic": row["source_candidate"]["step_text"],
                    **source,
                },
                "variant": {
                    "tactic": row["variant_candidate"]["step_text"],
                    **variant,
                },
            }
        )

    summary = {
        "cts_panel": args.cts_panel,
        "lean_raw": args.lean_raw,
        "max_pairs": args.max_pairs,
        "num_pairs_attempted": len(selected),
        "num_pairs_written": len(out_rows),
        "shared_pre_state_ok": sum(r.get("shared_pre_state_status") == "ok" for r in out_rows),
        "source_replay_ok": sum(r.get("source", {}).get("replay_status") == "ok" for r in out_rows),
        "variant_replay_ok": sum(r.get("variant", {}).get("replay_status") == "ok" for r in out_rows),
        "variant_lean_error": sum(r.get("variant", {}).get("replay_status") == "lean_error" for r in out_rows),
        "missing_context": sum(r.get("shared_pre_state_status") == "missing_context" for r in out_rows),
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for row in out_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary_path = Path(args.summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
