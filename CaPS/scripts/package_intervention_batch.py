#!/usr/bin/env python3

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Package generated intervention candidates into rollout-ready variants.")
    parser.add_argument(
        "--input",
        default="artifacts/object_gate/interventions/generated_candidates_v0.jsonl",
        help="Input JSONL with generated candidates.",
    )
    parser.add_argument(
        "--output",
        default="artifacts/object_gate/interventions/micro_batch_v0.jsonl",
        help="Output JSONL for rollout-ready micro-batch variants.",
    )
    return parser.parse_args()


def split_lines(text: str | None) -> list[str]:
    if not text:
        return []
    return [line.strip() for line in text.splitlines() if line.strip()]


def source_tag(source_rollout_file: str) -> str:
    stem = Path(source_rollout_file).stem
    return stem.replace(".", "_")


def load_rollout_row(source_rollout_file: str, prompt_id: str) -> dict:
    path = ROOT / source_rollout_file
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row["prompt_id"] == prompt_id:
                return row
    raise KeyError(f"Prompt {prompt_id} not found in {source_rollout_file}")


def replace_step(lines: list[str], step_index: int, replacement: str) -> list[str]:
    updated = list(lines)
    updated[step_index] = replacement
    return updated


def build_variant_records(candidate: dict, source_row: dict) -> list[dict]:
    original_lines = split_lines(source_row["reasoning"])
    step_index = candidate["step_index"]
    src_tag = source_tag(candidate["source_rollout_file"])
    variants = []

    delete_lines = candidate["delete_variant"]["reasoning_lines_after_delete"]
    variants.append(
        {
            "intervention_id": f"{src_tag}::{candidate['prompt_id']}::step{step_index}::delete",
            "variant_type": "delete",
            "variant_step_text": None,
            "reasoning_lines": delete_lines,
        }
    )

    for variant_type, key in [
        ("paraphrase", "paraphrase_candidates"),
        ("distractor", "distractor_candidates"),
    ]:
        for idx, text in enumerate(candidate[key]):
            variants.append(
                {
                    "intervention_id": f"{src_tag}::{candidate['prompt_id']}::step{step_index}::{variant_type}{idx}",
                    "variant_type": variant_type,
                    "variant_step_text": text,
                    "reasoning_lines": replace_step(original_lines, step_index, text),
                }
            )

    packaged = []
    for variant in variants:
        packaged.append(
            {
                "prompt_id": candidate["prompt_id"],
                "family": candidate["family"],
                "difficulty_stratum": candidate["difficulty_stratum"],
                "backend": candidate["backend"],
                "source_rollout_file": candidate["source_rollout_file"],
                "source_score": candidate["score"],
                "trace_readiness": candidate["trace_readiness"],
                "step_index": step_index,
                "step_text": candidate["step_text"],
                "selection_reason": candidate["selection_reason"],
                "intervention_id": variant["intervention_id"],
                "variant_type": variant["variant_type"],
                "variant_step_text": variant["variant_step_text"],
                "reasoning_lines": variant["reasoning_lines"],
                "final_target": source_row["final"],
                "remaining_budget_policy": candidate["remaining_budget_policy"],
                "continuation_count": candidate["continuation_count"],
                "needs_review": variant["variant_type"] == "distractor",
                "status": "packaged_for_rollout",
            }
        )
    return packaged


def main() -> None:
    args = parse_args()
    input_path = ROOT / args.input
    output_path = ROOT / args.output

    rows = [json.loads(line) for line in input_path.open("r", encoding="utf-8")]
    packaged = []
    for candidate in rows:
        source_row = load_rollout_row(candidate["source_rollout_file"], candidate["prompt_id"])
        packaged.extend(build_variant_records(candidate, source_row))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in packaged:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")

    summary = {
        "output": str(output_path.relative_to(ROOT)),
        "candidate_sources": len(rows),
        "variant_count": len(packaged),
        "delete_count": sum(1 for row in packaged if row["variant_type"] == "delete"),
        "paraphrase_count": sum(1 for row in packaged if row["variant_type"] == "paraphrase"),
        "distractor_count": sum(1 for row in packaged if row["variant_type"] == "distractor"),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
