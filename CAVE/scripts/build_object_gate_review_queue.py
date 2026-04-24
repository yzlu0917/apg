#!/usr/bin/env python3

import argparse
import json
from collections import defaultdict
from pathlib import Path


REVIEW_QUESTIONS = [
    ("label_clear", "Is the gold action objectively defensible from the checker?"),
    ("localizable", "Is the fail span local enough for suffix-style repair?"),
    ("repair_plausible", "Is the proposed repair suffix plausible and minimal?"),
    ("not_plain_correctness", "Does this test verifier-mediated action rather than only answer correctness?"),
]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_jsonl")
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--output-jsonl")
    return parser.parse_args()


def load_records(path: Path):
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def build_markdown(records):
    grouped = defaultdict(list)
    for record in records:
        grouped[record["pair_id"]].append(record)

    lines = [
        "# Object Gate Review Queue",
        "",
        f"Pairs: {len(grouped)}",
        "",
        "Review each pair against the checklist below.",
        "",
        "## Checklist",
        "",
    ]
    for key, prompt in REVIEW_QUESTIONS:
        lines.append(f"- `{key}`: {prompt}")

    for pair_id in sorted(grouped):
        items = sorted(grouped[pair_id], key=lambda x: x["gold_action"])
        lines.extend(["", f"## {pair_id}", ""])
        for item in items:
            lines.extend(
                [
                    f"### {item['id']}",
                    "",
                    f"- Domain: `{item['domain']}`",
                    f"- Action: `{item['gold_action']}`",
                    f"- Question: {item['question']}",
                    f"- Fail span: `{item['gold_fail_span']['text']}`",
                    f"- Repair suffix: {item['gold_repair_suffix'] or '(empty)' }",
                    f"- Checker: `{item['checker']['type']}` / `{item['checker']['reference']}`",
                    f"- Notes: {item['notes']}",
                    "",
                ]
            )
        lines.extend(
            [
                "Reviewer verdict:",
                "",
                "- `label_clear`: pending",
                "- `localizable`: pending",
                "- `repair_plausible`: pending",
                "- `not_plain_correctness`: pending",
                "- Notes: ",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def enrich_records(records):
    for record in records:
        record.setdefault("review_status", "pending")
        record.setdefault(
            "review_checks",
            {key: "pending" for key, _ in REVIEW_QUESTIONS},
        )
    return records


def main():
    args = parse_args()
    records = load_records(Path(args.input_jsonl))
    md = build_markdown(records)
    output_md = Path(args.output_md)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(md, encoding="utf-8")

    if args.output_jsonl:
        enriched = enrich_records(records)
        output_jsonl = Path(args.output_jsonl)
        output_jsonl.parent.mkdir(parents=True, exist_ok=True)
        with output_jsonl.open("w", encoding="utf-8") as handle:
            for record in enriched:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"wrote review markdown to {output_md}")
    if args.output_jsonl:
        print(f"wrote review jsonl to {args.output_jsonl}")


if __name__ == "__main__":
    main()
