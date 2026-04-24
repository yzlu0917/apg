#!/usr/bin/env python
import argparse
import json
from collections import defaultdict
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--original-files", nargs="+", required=True)
    parser.add_argument("--swapped-files", nargs="+", required=True)
    parser.add_argument("--output-file", required=True)
    return parser.parse_args()


def base_item_id(item_id: str) -> str:
    suffix = "__swapped"
    return item_id[:-len(suffix)] if item_id.endswith(suffix) else item_id


def summarize_pairs(pairs):
    total_pairs = len(pairs)
    directional_correct = sum(p["orig_correct"] + p["swapped_correct"] for p in pairs)
    strict_correct = sum(1 for p in pairs if p["pair_strict_correct"])
    family_stats = defaultdict(
        lambda: {
            "pairs": 0,
            "directional_correct": 0,
            "strict_correct": 0,
            "tie_pairs": 0,
            "tie_strict_correct": 0,
            "non_tie_pairs": 0,
            "non_tie_strict_correct": 0,
        }
    )
    label_stats = defaultdict(lambda: {"pairs": 0, "directional_correct": 0, "strict_correct": 0})
    pair_breakdown = {
        "both_correct": 0,
        "one_correct": 0,
        "both_wrong": 0,
    }

    for pair in pairs:
        if pair["orig_correct"] and pair["swapped_correct"]:
            pair_breakdown["both_correct"] += 1
        elif pair["orig_correct"] or pair["swapped_correct"]:
            pair_breakdown["one_correct"] += 1
        else:
            pair_breakdown["both_wrong"] += 1

        family = family_stats[pair["family"]]
        family["pairs"] += 1
        family["directional_correct"] += pair["orig_correct"] + pair["swapped_correct"]
        family["strict_correct"] += int(pair["pair_strict_correct"])
        if pair["gold_label"] == "tie":
            family["tie_pairs"] += 1
            family["tie_strict_correct"] += int(pair["pair_strict_correct"])
        else:
            family["non_tie_pairs"] += 1
            family["non_tie_strict_correct"] += int(pair["pair_strict_correct"])

        label_key = pair["gold_label"]
        label = label_stats[label_key]
        label["pairs"] += 1
        label["directional_correct"] += pair["orig_correct"] + pair["swapped_correct"]
        label["strict_correct"] += int(pair["pair_strict_correct"])

    family_directional_accuracy = {}
    family_pair_strict_accuracy = {}
    family_pair_strict_miss = {}
    family_tie_pair_strict_accuracy = {}
    family_non_tie_pair_strict_accuracy = {}
    for family_name, stats in family_stats.items():
        family_directional_accuracy[family_name] = stats["directional_correct"] / (2 * stats["pairs"])
        strict_acc = stats["strict_correct"] / stats["pairs"]
        family_pair_strict_accuracy[family_name] = strict_acc
        family_pair_strict_miss[family_name] = 1.0 - strict_acc
        if stats["tie_pairs"]:
            family_tie_pair_strict_accuracy[family_name] = stats["tie_strict_correct"] / stats["tie_pairs"]
        if stats["non_tie_pairs"]:
            family_non_tie_pair_strict_accuracy[family_name] = (
                stats["non_tie_strict_correct"] / stats["non_tie_pairs"]
            )

    label_directional_accuracy = {}
    label_pair_strict_accuracy = {}
    for label_key, stats in label_stats.items():
        label_directional_accuracy[label_key] = stats["directional_correct"] / (2 * stats["pairs"])
        label_pair_strict_accuracy[label_key] = stats["strict_correct"] / stats["pairs"]

    worst_family = max(family_pair_strict_miss, key=family_pair_strict_miss.get) if family_pair_strict_miss else None
    return {
        "judge_model": pairs[0]["judge_model"] if pairs else "",
        "judge_style": pairs[0]["judge_style"] if pairs else "",
        "total_pairs": total_pairs,
        "directional_total": 2 * total_pairs,
        "directional_correct": directional_correct,
        "balanced_directional_accuracy": directional_correct / (2 * total_pairs) if total_pairs else 0.0,
        "pair_strict_correct": strict_correct,
        "pair_strict_accuracy": strict_correct / total_pairs if total_pairs else 0.0,
        "pair_breakdown": pair_breakdown,
        "family_directional_accuracy": family_directional_accuracy,
        "family_pair_strict_accuracy": family_pair_strict_accuracy,
        "family_pair_strict_miss": family_pair_strict_miss,
        "family_tie_pair_strict_accuracy": family_tie_pair_strict_accuracy,
        "family_non_tie_pair_strict_accuracy": family_non_tie_pair_strict_accuracy,
        "balanced_coc_directional": (
            sum(family_directional_accuracy.values()) / len(family_directional_accuracy)
            if family_directional_accuracy
            else 0.0
        ),
        "balanced_coc_pair_strict": (
            sum(family_pair_strict_accuracy.values()) / len(family_pair_strict_accuracy)
            if family_pair_strict_accuracy
            else 0.0
        ),
        "worst_family_pair_strict": worst_family,
        "worst_family_pair_strict_miss": family_pair_strict_miss.get(worst_family, 0.0) if worst_family else 0.0,
        "label_directional_accuracy": label_directional_accuracy,
        "label_pair_strict_accuracy": label_pair_strict_accuracy,
    }


def build_summary(original_path: Path, swapped_path: Path):
    original_rows = [json.loads(x) for x in original_path.read_text().splitlines() if x.strip()]
    swapped_rows = [json.loads(x) for x in swapped_path.read_text().splitlines() if x.strip()]
    original_map = {row["item_id"]: row for row in original_rows}
    pairs = []

    for swapped in swapped_rows:
        item_id = base_item_id(swapped["item_id"])
        if item_id not in original_map:
            raise KeyError(f"missing original row for swapped item {swapped['item_id']}")
        orig = original_map[item_id]
        if orig["family"] != swapped["family"]:
            raise ValueError(f"family mismatch for {item_id}")
        pairs.append(
            {
                "item_id": item_id,
                "family": orig["family"],
                "gold_label": orig["gold_label"],
                "orig_correct": int(orig["judge_correct"]),
                "swapped_correct": int(swapped["judge_correct"]),
                "pair_strict_correct": bool(orig["judge_correct"] and swapped["judge_correct"]),
                "orig_verdict": orig["judge_verdict"],
                "swapped_verdict": swapped["judge_verdict"],
                "judge_model": orig["judge_model"],
                "judge_style": orig["judge_style"],
            }
        )

    summary = summarize_pairs(pairs)
    summary["original_file"] = str(original_path)
    summary["swapped_file"] = str(swapped_path)
    summary["pairs"] = pairs
    return summary


def main():
    args = parse_args()
    if len(args.original_files) != len(args.swapped_files):
        raise ValueError("original-files and swapped-files must have the same length")

    summaries = []
    for original_file, swapped_file in zip(args.original_files, args.swapped_files):
        summaries.append(build_summary(Path(original_file), Path(swapped_file)))

    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summaries, ensure_ascii=False, indent=2))
    print(json.dumps(summaries, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
