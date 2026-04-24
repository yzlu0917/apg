#!/usr/bin/env python
import argparse
import json
from collections import Counter
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-file", required=True)
    return parser.parse_args()


def classify_issue(row):
    issues = []
    decision = row.get("reviewer_decision")
    valid = row.get("review_family_valid")
    family = row.get("family")
    gold = row.get("gold_label")
    pref = row.get("review_preferred_answer_should_be")

    if valid is True and decision == "fail":
        issues.append("review_contradiction_valid_but_fail")
    if family in {"substance_flip", "reasoning_fluff"} and gold != "A":
        issues.append("hard_constraint_gold_not_A")
    if family == "style_flip" and gold != "tie":
        issues.append("hard_constraint_gold_not_tie")
    if family == "style_flip" and valid is True and decision == "pass" and pref not in {"tie", None}:
        issues.append("review_pref_not_tie")
    if family in {"substance_flip", "reasoning_fluff"} and valid is True and decision == "pass" and pref not in {"A", None}:
        issues.append("review_pref_not_A")
    return issues


def main():
    args = parse_args()
    rows = [json.loads(x) for x in Path(args.input_file).read_text().splitlines() if x.strip()]
    counts = Counter()
    details = []
    for row in rows:
        issues = classify_issue(row)
        if issues:
            for issue in issues:
                counts[issue] += 1
            details.append({"item_id": row["item_id"], "issues": issues})

    print(f"records={len(rows)}")
    print(f"flagged={len(details)}")
    for issue, count in sorted(counts.items()):
        print(f"{issue}={count}")
    if details:
        print("details:")
        for entry in details:
            print(json.dumps(entry, ensure_ascii=False))


if __name__ == "__main__":
    main()
