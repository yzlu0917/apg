#!/usr/bin/env python3

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize intervention rollout ordering statistics.")
    parser.add_argument("rollout_file", help="Rollout JSONL file to summarize.")
    parser.add_argument(
        "--compare",
        help="Optional second rollout JSONL file. If set, report matched-group deltas versus the main file.",
    )
    return parser.parse_args()


def parse_group_key(intervention_id: str, family: str) -> tuple[str, str, str, str]:
    source_rollout, prompt_id, step_id, _variant = intervention_id.split("::")
    return source_rollout, prompt_id, step_id, family


def load_rollout(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def build_group_summary(rows: list[dict]) -> dict:
    groups: dict[tuple[str, str, str, str], dict] = {}
    for row in rows:
        key = parse_group_key(row["intervention_id"], row["family"])
        group = groups.setdefault(
            key,
            {
                "scores": {},
                "final_present": {},
                "backend_used": row["backend_used"],
            },
        )
        group["scores"][row["variant_type"]] = row["score"]
        group["final_present"][row["variant_type"]] = row["final_present"]
    return groups


def aggregate(rows: list[dict]) -> dict:
    groups = build_group_summary(rows)
    strict = 0
    weak = 0
    for group in groups.values():
        scores = group["scores"]
        delete = scores["delete"]
        paraphrase = scores["paraphrase"]
        distractor = scores["distractor"]
        if paraphrase > distractor > delete:
            strict += 1
        if paraphrase >= distractor >= delete and paraphrase > delete:
            weak += 1
    return {
        "row_count": len(rows),
        "group_count": len(groups),
        "final_present_count": sum(1 for row in rows if row["final_present"]),
        "nonzero_score_count": sum(1 for row in rows if row["score"] > 0),
        "strict_order_count": strict,
        "weak_order_count": weak,
        "groups": groups,
    }


def summarize(path: Path) -> dict:
    rows = load_rollout(path)
    summary = aggregate(rows)
    summary["path"] = str(path.relative_to(ROOT))
    return summary


def matched_group_delta(base: dict, compare: dict) -> list[dict]:
    shared_keys = sorted(set(base["groups"]).intersection(compare["groups"]))
    deltas = []
    for key in shared_keys:
        left = base["groups"][key]["scores"]
        right = compare["groups"][key]["scores"]
        deltas.append(
            {
                "group": key,
                "base_scores": left,
                "compare_scores": right,
                "delta_paraphrase_minus_delete": (left["paraphrase"] - left["delete"])
                - (right["paraphrase"] - right["delete"]),
                "delta_paraphrase_minus_distractor": (left["paraphrase"] - left["distractor"])
                - (right["paraphrase"] - right["distractor"]),
            }
        )
    return deltas


def main() -> None:
    args = parse_args()
    rollout_path = (ROOT / args.rollout_file).resolve()
    summary = summarize(rollout_path)

    output = {
        "path": summary["path"],
        "row_count": summary["row_count"],
        "group_count": summary["group_count"],
        "final_present_count": summary["final_present_count"],
        "nonzero_score_count": summary["nonzero_score_count"],
        "strict_order_count": summary["strict_order_count"],
        "weak_order_count": summary["weak_order_count"],
        "groups": [
            {
                "group": key,
                "backend_used": summary["groups"][key]["backend_used"],
                "scores": summary["groups"][key]["scores"],
            }
            for key in sorted(summary["groups"])
        ],
    }

    if args.compare:
        compare_path = (ROOT / args.compare).resolve()
        compare_summary = summarize(compare_path)
        output["compare_against"] = compare_summary["path"]
        output["shared_group_count"] = len(
            set(summary["groups"]).intersection(compare_summary["groups"])
        )
        output["matched_group_deltas"] = matched_group_delta(summary, compare_summary)

    print(json.dumps(output, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
