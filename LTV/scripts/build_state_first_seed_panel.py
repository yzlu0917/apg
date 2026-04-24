#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def dump_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a state-first before-state seed panel from replayed Lean states.")
    parser.add_argument("--replay-bucket", required=True)
    parser.add_argument("--lean-raw", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    replay_rows = load_jsonl(Path(args.replay_bucket))
    lean_rows = {row["theorem_id"]: row for row in load_jsonl(Path(args.lean_raw))}

    seen = set()
    seed_rows = []
    for row in replay_rows:
        if row["source"]["replay_status"] != "ok":
            continue
        before_goals = row.get("before_goals") or row["source"].get("before_goals") or []
        if not before_goals:
            continue
        dedupe_key = (row["theorem_id"], tuple(before_goals))
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        theorem = lean_rows[row["theorem_id"]]
        state_id = f"{row['theorem_id']}__step{row['step_index']}"
        seed_rows.append(
            {
                "state_id": state_id,
                "theorem_id": row["theorem_id"],
                "step_index": row["step_index"],
                "header": theorem["header"],
                "prefix_steps": row["prefix_steps"],
                "before_goals": before_goals,
                "gold_tactic": row["source"]["tactic"],
                "notes": theorem.get("notes"),
                "seed_source": "round41_replay_ok_source",
                "candidate_generation_status": "pending",
                "oracle_label_status": "pending",
            }
        )

    dump_jsonl(Path(args.output), seed_rows)
    summary = {
        "num_seed_states": len(seed_rows),
        "unique_theorems": len({row["theorem_id"] for row in seed_rows}),
        "max_step_index": max((row["step_index"] for row in seed_rows), default=None),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
