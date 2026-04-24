#!/usr/bin/env python3

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


ALLOWED_DOMAINS = {"sym", "code", "plan"}
ALLOWED_ACTIONS = {"keep", "revise", "abstain"}


def load_records(path: Path):
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"line {line_no}: invalid JSON: {exc}") from exc
            record["_line_no"] = line_no
            records.append(record)
    if not records:
        raise ValueError("seed file is empty")
    return records


def validate_record(record):
    required = [
        "id",
        "pair_id",
        "domain",
        "question",
        "initial_trace",
        "gold_fail_span",
        "gold_action",
        "gold_repair_suffix",
        "expected_final_answer",
        "checker",
        "utility_delta",
        "notes",
    ]
    missing = [key for key in required if key not in record]
    if missing:
        raise ValueError(
            f"line {record['_line_no']}: missing required fields: {', '.join(missing)}"
        )

    if record["domain"] not in ALLOWED_DOMAINS:
        raise ValueError(
            f"line {record['_line_no']}: invalid domain {record['domain']!r}"
        )
    if record["gold_action"] not in ALLOWED_ACTIONS:
        raise ValueError(
            f"line {record['_line_no']}: invalid gold_action {record['gold_action']!r}"
        )

    span = record["gold_fail_span"]
    if not isinstance(span, dict) or "text" not in span or "kind" not in span:
        raise ValueError(
            f"line {record['_line_no']}: gold_fail_span must contain text and kind"
        )

    checker = record["checker"]
    if not isinstance(checker, dict) or "type" not in checker or "reference" not in checker:
        raise ValueError(
            f"line {record['_line_no']}: checker must contain type and reference"
        )

    utility = record["utility_delta"]
    if not isinstance(utility, dict):
        raise ValueError(f"line {record['_line_no']}: utility_delta must be an object")
    for action in ALLOWED_ACTIONS:
        if action not in utility:
            raise ValueError(
                f"line {record['_line_no']}: utility_delta missing key {action!r}"
            )

    if record["gold_action"] == "keep":
        if span["text"] != "":
            raise ValueError(
                f"line {record['_line_no']}: keep example should have empty fail span text"
            )
        if record["gold_repair_suffix"] != "":
            raise ValueError(
                f"line {record['_line_no']}: keep example should have empty repair suffix"
            )

    if record["gold_action"] == "revise":
        if span["text"] == "":
            raise ValueError(
                f"line {record['_line_no']}: revise example requires non-empty fail span text"
            )
        if record["gold_repair_suffix"] == "":
            raise ValueError(
                f"line {record['_line_no']}: revise example requires non-empty repair suffix"
            )


def validate_pairs(records):
    by_pair = defaultdict(list)
    for record in records:
        by_pair[record["pair_id"]].append(record)

    for pair_id, items in by_pair.items():
        if len(items) != 2:
            raise ValueError(f"pair {pair_id!r} must contain exactly 2 records")
        actions = sorted(item["gold_action"] for item in items)
        if actions != ["keep", "revise"]:
            raise ValueError(
                f"pair {pair_id!r} must contain exactly one keep and one revise example"
            )
        questions = {item["question"] for item in items}
        domains = {item["domain"] for item in items}
        if len(questions) != 1:
            raise ValueError(f"pair {pair_id!r} must share the same question")
        if len(domains) != 1:
            raise ValueError(f"pair {pair_id!r} must share the same domain")


def main(argv):
    if len(argv) != 2:
        print("usage: validate_object_gate_seed.py <seed.jsonl>", file=sys.stderr)
        return 2

    path = Path(argv[1])
    if not path.is_file():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    try:
        records = load_records(path)
        for record in records:
            validate_record(record)
        validate_pairs(records)
    except ValueError as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 1

    domain_counts = Counter(record["domain"] for record in records)
    action_counts = Counter(record["gold_action"] for record in records)
    pair_ids = sorted({record["pair_id"] for record in records})

    print("validation ok")
    print(f"records: {len(records)}")
    print(f"pairs: {len(pair_ids)}")
    print(f"domains: {dict(sorted(domain_counts.items()))}")
    print(f"actions: {dict(sorted(action_counts.items()))}")
    print(f"pair_ids: {pair_ids}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
