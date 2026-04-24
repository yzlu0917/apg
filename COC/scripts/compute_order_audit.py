#!/usr/bin/env python
import argparse
import json
from collections import Counter
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--original-file", required=True)
    parser.add_argument("--swapped-file", required=True)
    parser.add_argument("--output-file", required=True)
    return parser.parse_args()


def expected_swap(verdict: str) -> str:
    if verdict == "A":
        return "B"
    if verdict == "B":
        return "A"
    return verdict


def base_item_id(swapped_id: str) -> str:
    suffix = "__swapped"
    return swapped_id[:-len(suffix)] if swapped_id.endswith(suffix) else swapped_id


def main():
    args = parse_args()
    original_rows = [json.loads(x) for x in Path(args.original_file).read_text().splitlines() if x.strip()]
    swapped_rows = [json.loads(x) for x in Path(args.swapped_file).read_text().splitlines() if x.strip()]
    orig_map = {row["item_id"]: row for row in original_rows}
    summary = {
        "judge_model": original_rows[0]["judge_model"] if original_rows else "",
        "judge_style": original_rows[0]["judge_style"] if original_rows else "",
        "total_pairs": 0,
        "expected_swap_match": 0,
        "tie_items": 0,
        "tie_stable": 0,
        "tie_broke_to_A_or_B": Counter(),
        "non_tie_items": 0,
        "non_tie_flip_correct": 0,
        "details": [],
    }

    for swapped in swapped_rows:
        base_id = base_item_id(swapped["item_id"])
        orig = orig_map[base_id]
        summary["total_pairs"] += 1
        expected = expected_swap(orig["judge_verdict"])
        matches = swapped["judge_verdict"] == expected
        summary["expected_swap_match"] += int(matches)

        detail = {
            "item_id": base_id,
            "family": orig["family"],
            "orig_verdict": orig["judge_verdict"],
            "swapped_verdict": swapped["judge_verdict"],
            "expected_swapped_verdict": expected,
            "matches_expected_swap": matches,
            "gold_label": orig["gold_label"],
        }
        summary["details"].append(detail)

        if orig["gold_label"] == "tie":
            summary["tie_items"] += 1
            if orig["judge_verdict"] == "tie" and swapped["judge_verdict"] == "tie":
                summary["tie_stable"] += 1
            else:
                summary["tie_broke_to_A_or_B"][f"{orig['judge_verdict']}->{swapped['judge_verdict']}"] += 1
        else:
            summary["non_tie_items"] += 1
            if matches:
                summary["non_tie_flip_correct"] += 1

    summary["expected_swap_rate"] = summary["expected_swap_match"] / summary["total_pairs"] if summary["total_pairs"] else 0.0
    summary["tie_stability_rate"] = summary["tie_stable"] / summary["tie_items"] if summary["tie_items"] else 0.0
    summary["non_tie_flip_rate"] = summary["non_tie_flip_correct"] / summary["non_tie_items"] if summary["non_tie_items"] else 0.0
    summary["tie_broke_to_A_or_B"] = dict(summary["tie_broke_to_A_or_B"])

    out = Path(args.output_file)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
