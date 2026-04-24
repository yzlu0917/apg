#!/usr/bin/env python3

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROLLOUT_DIR = ROOT / "artifacts" / "object_gate" / "rollouts"
INTERVENTION_DIR = ROOT / "artifacts" / "object_gate" / "interventions"


MOVE_LINE_RE = re.compile(r"^Move disk \d+ from Peg \d+ to Peg \d+$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Draft intervention templates from rollout JSONL files.")
    parser.add_argument(
        "--input-rollouts",
        default="",
        help="Optional comma-separated rollout JSONL paths. Defaults to the original preferred rollout set.",
    )
    parser.add_argument(
        "--output",
        default="artifacts/object_gate/interventions/draft_candidates_v0.jsonl",
        help="Output drafted-candidate JSONL.",
    )
    return parser.parse_args()


def split_lines(text: str | None) -> list[str]:
    if not text:
        return []
    return [line.strip() for line in text.splitlines() if line.strip()]


def normalized(line: str) -> str:
    return " ".join(line.lower().split())


def compute_overlap_ratio(reasoning_lines: list[str], final_lines: list[str]) -> float:
    if not reasoning_lines or not final_lines:
        return 0.0
    reasoning_set = {normalized(line) for line in reasoning_lines}
    final_set = {normalized(line) for line in final_lines}
    overlap = reasoning_set & final_set
    return len(overlap) / max(1, len(reasoning_set))


def looks_like_final_format(reasoning_lines: list[str], final_lines: list[str]) -> bool:
    if reasoning_lines and all(MOVE_LINE_RE.match(line) for line in reasoning_lines):
        return True
    if final_lines and reasoning_lines and reasoning_lines == final_lines:
        return True
    return False


def trace_readiness(row: dict) -> tuple[str, float]:
    reasoning_lines = split_lines(row.get("reasoning"))
    final_lines = split_lines(row.get("final"))
    overlap_ratio = compute_overlap_ratio(reasoning_lines, final_lines)
    if looks_like_final_format(reasoning_lines, final_lines) or overlap_ratio >= 0.6:
        return "review_needed", overlap_ratio
    return "ready", overlap_ratio


def select_candidate_indices(lines: list[str]) -> list[int]:
    if not lines:
        return []
    if len(lines) == 1:
        return [0]
    indices = [0, len(lines) - 1]
    if normalized(lines[indices[0]]) == normalized(lines[indices[1]]):
        return [indices[0]]
    return indices


def draft_records_for_row(source_file: Path, row: dict) -> list[dict]:
    reasoning_lines = split_lines(row.get("reasoning"))
    final_lines = split_lines(row.get("final"))
    readiness, overlap_ratio = trace_readiness(row)
    candidate_indices = select_candidate_indices(reasoning_lines)

    records = []
    for idx in candidate_indices:
        step_text = reasoning_lines[idx]
        if len(reasoning_lines) == 1:
            selection_reason = "only_segmented_step"
        elif idx == 0:
            selection_reason = "first_step"
        else:
            selection_reason = "last_step"

        delete_variant = [line for j, line in enumerate(reasoning_lines) if j != idx]

        record = {
            "source_rollout_file": str(source_file.relative_to(ROOT)),
            "prompt_id": row["prompt_id"],
            "family": row["family"],
            "difficulty_stratum": row["difficulty_stratum"],
            "backend": row["backend"],
            "score": row["score"],
            "segmentation_version": "line_split_v0",
            "candidate_selection_version": "first_last_v0",
            "trace_readiness": readiness,
            "reasoning_final_overlap_ratio": overlap_ratio,
            "num_segmented_steps": len(reasoning_lines),
            "step_index": idx,
            "step_text": step_text,
            "selection_reason": selection_reason,
            "delete_variant": {
                "reasoning_lines_after_delete": delete_variant
            },
            "paraphrase_candidates": [],
            "distractor_candidates": [],
            "remaining_budget_policy": "same_max_tokens_as_source_trace",
            "continuation_count": 2,
            "status": "drafted",
            "notes": [],
        }
        records.append(record)

    return records


def resolve_rollout_files(input_rollouts: str) -> list[Path]:
    if input_rollouts:
        return [ROOT / item.strip() for item in input_rollouts.split(",") if item.strip()]
    return [
        ROLLOUT_DIR / "api_highdep_calibration_001.jsonl",
        ROLLOUT_DIR / "dev_trace_smoke_006.jsonl",
        ROLLOUT_DIR / "dev_mixed_smoke_batch_000.jsonl",
    ]


def iter_source_rows(rollout_files: list[Path]) -> list[tuple[Path, dict]]:
    rows: list[tuple[Path, dict]] = []
    for path in rollout_files:
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                if row.get("format_ok"):
                    rows.append((path, row))
    return rows


def main() -> None:
    args = parse_args()
    output_path = ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rollout_files = resolve_rollout_files(args.input_rollouts)

    drafted = []
    for path, row in iter_source_rows(rollout_files):
        drafted.extend(draft_records_for_row(path, row))

    with output_path.open("w", encoding="utf-8") as handle:
        for record in drafted:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")

    summary = {
        "output": str(output_path.relative_to(ROOT)),
        "candidate_count": len(drafted),
        "ready_count": sum(1 for record in drafted if record["trace_readiness"] == "ready"),
        "review_needed_count": sum(1 for record in drafted if record["trace_readiness"] != "ready"),
        "families": sorted({record["family"] for record in drafted}),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
