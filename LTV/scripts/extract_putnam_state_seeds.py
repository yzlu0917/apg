#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


DEFAULT_LAKE = "/root/.elan/bin/lake"
DEFAULT_PUTNAM_PROJECT_ROOT = "/root/mathlib4-4.15.0/Putnam"
DEFAULT_REPL_RELATIVE = "../repl/.lake/build/bin/repl"
DEFAULT_FILES = [
    "Putnam/putnam_1976_b5_sol.lean",
    "Putnam/putnam_1993_a4_sol.lean",
    "Putnam/putnam_2013_b4_sol.lean",
]


@dataclass
class DeclBlock:
    name: str
    kind: str
    start_line: int
    header: str


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


def parse_decl_blocks(lines: List[str]) -> List[DeclBlock]:
    blocks: List[DeclBlock] = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        match = re.match(r"^(theorem|lemma)\s+([A-Za-z0-9_'.]+)", stripped)
        if not match:
            i += 1
            continue
        kind = match.group(1)
        name = match.group(2)
        start = i + 1
        header_lines = [lines[i]]
        i += 1
        while i < len(lines):
            header_lines.append(lines[i])
            if ":= by" in lines[i]:
                break
            i += 1
        blocks.append(
            DeclBlock(
                name=name,
                kind=kind,
                start_line=start,
                header="\n".join(header_lines).rstrip(),
            )
        )
        i += 1
    return blocks


def latest_decl_for_line(blocks: List[DeclBlock], line_no: int) -> DeclBlock:
    candidates = [b for b in blocks if b.start_line <= line_no]
    if not candidates:
        raise ValueError(f"No declaration found before line {line_no}")
    return candidates[-1]


def context_snippet(lines: List[str], line_no: int, radius: int = 4) -> str:
    start = max(0, line_no - 1 - radius)
    end = min(len(lines), line_no - 1 + radius + 1)
    out = []
    for idx in range(start, end):
        marker = ">>" if idx + 1 == line_no else "  "
        out.append(f"{marker} {idx + 1:03d}: {lines[idx]}")
    return "\n".join(out)


def run_file_mode(path: Path, project_root: Path, lake_bin: str, repl_relative: str) -> Dict:
    stdin_text = json.dumps({"path": str(path), "allTactics": True}, ensure_ascii=False) + "\n"
    result = subprocess.run(
        [lake_bin, "env", repl_relative],
        cwd=project_root,
        input=stdin_text,
        text=True,
        capture_output=True,
        check=False,
    )
    responses = split_json_blocks(result.stdout) if result.stdout.strip() else []
    payload = responses[0] if responses else {}
    return {
        "returncode": result.returncode,
        "stderr": result.stderr,
        "payload": payload,
    }


def dump_jsonl(path: Path, rows: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract harder Putnam state-first seeds via project-aware REPL file mode.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--project-root", default=DEFAULT_PUTNAM_PROJECT_ROOT)
    parser.add_argument("--lake-bin", default=DEFAULT_LAKE)
    parser.add_argument("--repl-relative", default=DEFAULT_REPL_RELATIVE)
    parser.add_argument("--files", nargs="*", default=DEFAULT_FILES)
    args = parser.parse_args()

    project_root = Path(args.project_root)
    rows: List[Dict] = []
    status_rows: List[Dict] = []

    for rel_path in args.files:
        path = project_root / rel_path
        lines = path.read_text(encoding="utf-8").splitlines()
        decl_blocks = parse_decl_blocks(lines)
        result = run_file_mode(path, project_root, args.lake_bin, args.repl_relative)
        payload = result["payload"]
        sorries = payload.get("sorries", [])
        tactics = payload.get("tactics", [])
        status_rows.append(
            {
                "file": str(path),
                "returncode": result["returncode"],
                "num_sorries": len(sorries),
                "num_tactics": len(tactics),
            }
        )
        for sorry_idx, sorry in enumerate(sorries):
            line_no = sorry["pos"]["line"]
            decl = latest_decl_for_line(decl_blocks, line_no)
            goals = as_goal_list(sorry.get("goal"))
            rows.append(
                {
                    "state_id": f"{decl.name}__sorry{sorry_idx}",
                    "theorem_id": decl.name,
                    "decl_name": decl.name,
                    "decl_kind": decl.kind,
                    "step_index": sorry_idx,
                    "header": decl.header,
                    "prefix_steps": [],
                    "before_goals": goals,
                    "gold_tactic": "",
                    "notes": f"Putnam harder state extracted from {path.name}:{line_no}",
                    "seed_source": "putnam_file_mode_sorry_v0",
                    "candidate_generation_status": "pending",
                    "oracle_label_status": "pending",
                    "source_type": "putnam_file_mode",
                    "source_file": str(path),
                    "project_root": str(project_root),
                    "proof_state": sorry.get("proofState"),
                    "sorry_position": sorry.get("pos"),
                    "context_snippet": context_snippet(lines, line_no),
                    "file_mode_env": payload.get("env"),
                }
            )

    dump_jsonl(Path(args.output), rows)
    summary = {
        "num_seed_states": len(rows),
        "num_files": len(args.files),
        "files": status_rows,
        "num_nonempty_goal_states": sum(1 for row in rows if row["before_goals"]),
    }
    summary_path = Path(args.summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
