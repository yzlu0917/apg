#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Dict, List


DEFAULT_LAKE = "/root/.elan/bin/lake"
DEFAULT_REPL_ROOT = "/root/mathlib4-4.15.0/repl"
DEFAULT_MINIF2F = "/root/mathlib4-4.15.0/lean_test/data/minif2f.jsonl"
DEFAULT_PUTNAM_DIR = "/root/mathlib4-4.15.0/Putnam/Putnam"


MINIF2F_NAMES = [
    "imo_1965_p2",
    "imo_1969_p2",
    "imo_1981_p6",
]

PUTNAM_FILES = [
    "putnam_1976_b5_sol.lean",
    "putnam_1993_a4_sol.lean",
    "putnam_2013_b4_sol.lean",
]


def load_jsonl(path: Path) -> List[Dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def dump_jsonl(path: Path, rows: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


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


def initial_goals_for_header(header_cmd: str, repl_root: Path, lake_bin: str) -> Dict:
    cmd = header_cmd.rstrip()
    if cmd.endswith(":= by"):
        cmd = cmd[:-5].rstrip() + " := sorry"
    stdin_text = json.dumps({"cmd": cmd}, ensure_ascii=False) + "\n"
    result = subprocess.run(
        [lake_bin, "exe", "repl"],
        cwd=repl_root,
        input=stdin_text,
        text=True,
        capture_output=True,
        check=False,
    )
    responses = split_json_blocks(result.stdout) if result.stdout.strip() else []
    messages = []
    goals = []
    status = "empty_output"
    if responses:
        init = responses[0]
        messages.extend(init.get("messages", []))
        sorries = init.get("sorries", [])
        if sorries:
            goals = as_goal_list(sorries[0].get("goal"))
            status = "ok" if goals else "no_goals"
        else:
            status = "missing_context"
    return {
        "returncode": result.returncode,
        "stderr": result.stderr,
        "messages": messages,
        "before_goals": goals,
        "status": status,
    }


def build_minif2f_rows(minif2f_path: Path) -> List[Dict]:
    rows = []
    by_name = {row["statement"]["name"]: row for row in load_jsonl(minif2f_path)}
    for name in MINIF2F_NAMES:
        row = by_name[name]
        stmt = row["statement"]
        header_lines = []
        for line in stmt["header"].splitlines():
            stripped = line.strip()
            if stripped.startswith("open "):
                continue
            header_lines.append(line)
        main_one_line = re.sub(r"\s+", " ", stmt["main"]).strip()
        header = "\n".join(header_lines).rstrip() + "\n\n" + main_one_line
        rows.append(
            {
                "state_id": f"{name}__step0",
                "theorem_id": name,
                "step_index": 0,
                "header": header,
                "prefix_steps": [],
                "gold_tactic": "",
                "notes": f"harder pilot from minif2f_test: {name}",
                "seed_source": "minif2f_test_step0_harder_v0",
                "oracle_label_status": "pending",
                "candidate_generation_status": "pending",
                "source_type": "minif2f_test",
            }
        )
    return rows


def extract_putnam_header(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    prelude: List[str] = []
    theorem_lines: List[str] = []
    in_theorem = False
    for line in lines:
        stripped = line.strip()
        if not in_theorem:
            if stripped.startswith("import ") or stripped.startswith("open "):
                prelude.append(line)
            if stripped.startswith("theorem "):
                in_theorem = True
                theorem_lines.append(line)
                if ":= by" in stripped:
                    break
        else:
            theorem_lines.append(line)
            if ":= by" in stripped:
                break
    if not theorem_lines:
        raise ValueError(f"Could not extract theorem header from {path}")
    theorem_one_line = re.sub(r"\s+", " ", " ".join(theorem_lines)).strip()
    return "\n".join([*prelude, "", theorem_one_line]).strip()


def build_putnam_rows(putnam_dir: Path) -> List[Dict]:
    rows = []
    for filename in PUTNAM_FILES:
        path = putnam_dir / filename
        theorem_id = filename.replace("_sol.lean", "")
        rows.append(
            {
                "state_id": f"{theorem_id}__step0",
                "theorem_id": theorem_id,
                "step_index": 0,
                "header": extract_putnam_header(path),
                "prefix_steps": [],
                "gold_tactic": "",
                "notes": f"harder pilot from Putnam theorem statement: {filename}",
                "seed_source": "putnam_step0_harder_v0",
                "oracle_label_status": "pending",
                "candidate_generation_status": "pending",
                "source_type": "putnam_statement",
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a harder state-first seed panel from Putnam/minif2f theorem statements.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--minif2f-path", default=DEFAULT_MINIF2F)
    parser.add_argument("--putnam-dir", default=DEFAULT_PUTNAM_DIR)
    parser.add_argument("--repl-root", default=DEFAULT_REPL_ROOT)
    parser.add_argument("--lake-bin", default=DEFAULT_LAKE)
    args = parser.parse_args()

    rows = build_putnam_rows(Path(args.putnam_dir)) + build_minif2f_rows(Path(args.minif2f_path))

    replayable = 0
    for row in rows:
        probe = initial_goals_for_header(row["header"], Path(args.repl_root), args.lake_bin)
        row["before_goals"] = probe["before_goals"]
        row["header_probe_status"] = probe["status"]
        row["header_probe_messages"] = probe["messages"]
        row["header_probe_stderr"] = probe["stderr"]
        if probe["status"] == "ok":
            replayable += 1

    dump_jsonl(Path(args.output), rows)

    summary = {
        "num_seed_states": len(rows),
        "num_replayable_initial_states": replayable,
        "num_putnam_states": sum(1 for r in rows if r["source_type"] == "putnam_statement"),
        "num_minif2f_states": sum(1 for r in rows if r["source_type"] == "minif2f_test"),
        "state_status": [
            {
                "state_id": r["state_id"],
                "source_type": r["source_type"],
                "header_probe_status": r["header_probe_status"],
                "num_before_goals": len(r.get("before_goals", [])),
            }
            for r in rows
        ],
    }
    summary_path = Path(args.summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
