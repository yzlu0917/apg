#!/usr/bin/env python
import argparse
import json
from pathlib import Path


def swap_gold(label: str) -> str:
    if label == "A":
        return "B"
    if label == "B":
        return "A"
    return label


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output-file", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    rows = [json.loads(x) for x in Path(args.input_file).read_text().splitlines() if x.strip()]
    swapped = []
    for row in rows:
        new_row = dict(row)
        new_row["item_id"] = row["item_id"] + "__swapped"
        new_row["answer_a"] = row["answer_b"]
        new_row["answer_b"] = row["answer_a"]
        new_row["gold_label"] = swap_gold(row["gold_label"])
        if "verifier_preferred_label" in new_row:
            new_row["verifier_preferred_label"] = swap_gold(row["verifier_preferred_label"])
        swapped.append(new_row)

    out = Path(args.output_file)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as f:
        for row in swapped:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
