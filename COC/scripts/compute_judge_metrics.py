#!/usr/bin/env python
import argparse
import json
from collections import defaultdict
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-files", nargs="+", required=True)
    parser.add_argument("--output-file", required=True)
    return parser.parse_args()


def summarize(rows):
    total = len(rows)
    correct = sum(1 for r in rows if r["judge_correct"])
    family_stats = defaultdict(lambda: {"total": 0, "correct": 0})
    for row in rows:
        fam = family_stats[row["family"]]
        fam["total"] += 1
        fam["correct"] += int(row["judge_correct"])

    family_accuracy = {}
    family_miss = {}
    for family, stats in family_stats.items():
        acc = stats["correct"] / stats["total"]
        family_accuracy[family] = acc
        family_miss[family] = 1.0 - acc

    coc = sum(family_accuracy.values()) / len(family_accuracy) if family_accuracy else 0.0
    worst_family = max(family_miss, key=family_miss.get) if family_miss else None
    return {
        "judge_model": rows[0]["judge_model"] if rows else "",
        "judge_style": rows[0]["judge_style"] if rows else "",
        "overall_accuracy": correct / total if total else 0.0,
        "total": total,
        "correct": correct,
        "family_accuracy": family_accuracy,
        "family_miss": family_miss,
        "coc_uniform_active_families": coc,
        "worst_family": worst_family,
        "worst_family_miss": family_miss.get(worst_family, 0.0) if worst_family else 0.0,
    }


def main():
    args = parse_args()
    summaries = []
    for path in args.input_files:
        rows = [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]
        summaries.append(summarize(rows))

    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summaries, ensure_ascii=False, indent=2))
    print(json.dumps(summaries, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
