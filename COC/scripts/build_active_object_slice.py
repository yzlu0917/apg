#!/usr/bin/env python
import argparse
import json
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-files", nargs="+", required=True)
    parser.add_argument("--output-file", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    rows = []
    for path in args.input_files:
        for line in Path(path).read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row["family"] not in {"style_flip", "substance_flip"}:
                continue
            if row.get("reviewer_decision") != "pass":
                continue
            if not row.get("verifier_gold_consistent", False):
                continue
            rows.append(row)

    seen = set()
    deduped = []
    for row in rows:
        key = row["item_id"]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)

    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as f:
        for row in deduped:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
