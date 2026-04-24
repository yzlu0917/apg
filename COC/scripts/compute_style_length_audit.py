#!/usr/bin/env python
import argparse
import json
from collections import Counter
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--original-slice", required=True)
    parser.add_argument("--swapped-slice", required=True)
    parser.add_argument("--original-eval", required=True)
    parser.add_argument("--swapped-eval", required=True)
    parser.add_argument("--output-file", required=True)
    return parser.parse_args()


def read_jsonl(path: str):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def base_item_id(item_id: str) -> str:
    suffix = "__swapped"
    return item_id[:-len(suffix)] if item_id.endswith(suffix) else item_id


def longer_label(row):
    len_a = len(row["answer_a"])
    len_b = len(row["answer_b"])
    if len_a > len_b:
        return "A", len_a, len_b
    if len_b > len_a:
        return "B", len_a, len_b
    return "tie", len_a, len_b


def directional_bucket(verdict: str, longer: str) -> str:
    if verdict == "tie":
        return "tie"
    if longer == "tie":
        return "equal_length_non_tie"
    if verdict == longer:
        return "longer"
    return "shorter"


def main():
    args = parse_args()
    original_slice = {row["item_id"]: row for row in read_jsonl(args.original_slice) if row["family"] == "style_flip"}
    swapped_slice = {row["item_id"]: row for row in read_jsonl(args.swapped_slice) if row["family"] == "style_flip"}
    original_eval = [row for row in read_jsonl(args.original_eval) if row["family"] == "style_flip"]
    swapped_eval = [row for row in read_jsonl(args.swapped_eval) if row["family"] == "style_flip"]

    pair_map = {}
    directional_counts = Counter()
    length_gaps = []

    for row in original_eval:
        item_id = row["item_id"]
        slice_row = original_slice[item_id]
        longer, len_a, len_b = longer_label(slice_row)
        bucket = directional_bucket(row["judge_verdict"], longer)
        directional_counts[bucket] += 1
        length_gaps.append(abs(len_a - len_b))
        pair_map[item_id] = {
            "item_id": item_id,
            "source_task_id": slice_row["source_task_id"],
            "domain": slice_row["domain"],
            "orig_verdict": row["judge_verdict"],
            "orig_longer_label": longer,
            "orig_len_a": len_a,
            "orig_len_b": len_b,
            "orig_bucket": bucket,
        }

    for row in swapped_eval:
        item_id = base_item_id(row["item_id"])
        slice_row = swapped_slice[row["item_id"]]
        longer, len_a, len_b = longer_label(slice_row)
        bucket = directional_bucket(row["judge_verdict"], longer)
        directional_counts[bucket] += 1
        length_gaps.append(abs(len_a - len_b))
        pair_map[item_id].update(
            {
                "swapped_verdict": row["judge_verdict"],
                "swapped_longer_label": longer,
                "swapped_len_a": len_a,
                "swapped_len_b": len_b,
                "swapped_bucket": bucket,
            }
        )

    pair_breakdown = Counter()
    details = []
    for pair in pair_map.values():
        combo = f"{pair['orig_bucket']}+{pair['swapped_bucket']}"
        pair_breakdown[combo] += 1
        details.append(pair)

    total_directional = sum(directional_counts.values())
    non_tie_decisions = directional_counts["longer"] + directional_counts["shorter"] + directional_counts["equal_length_non_tie"]
    choose_longer_rate = directional_counts["longer"] / non_tie_decisions if non_tie_decisions else 0.0
    choose_shorter_rate = directional_counts["shorter"] / non_tie_decisions if non_tie_decisions else 0.0
    tie_rate = directional_counts["tie"] / total_directional if total_directional else 0.0

    summary = {
        "judge_model": original_eval[0]["judge_model"] if original_eval else "",
        "judge_style": original_eval[0]["judge_style"] if original_eval else "",
        "total_style_pairs": len(pair_map),
        "total_directional_decisions": total_directional,
        "directional_counts": dict(directional_counts),
        "tie_rate": tie_rate,
        "non_tie_decisions": non_tie_decisions,
        "choose_longer_rate_among_non_tie": choose_longer_rate,
        "choose_shorter_rate_among_non_tie": choose_shorter_rate,
        "avg_abs_char_gap": sum(length_gaps) / len(length_gaps) if length_gaps else 0.0,
        "pair_breakdown": dict(pair_breakdown),
        "details": sorted(details, key=lambda x: x["item_id"]),
    }

    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
