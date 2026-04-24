#!/usr/bin/env python3

import argparse
import json
from collections import defaultdict
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_jsonl")
    parser.add_argument(
        "--source-jsonl",
        help="Optional separate source bank for shuffle controls. Defaults to input_jsonl.",
    )
    parser.add_argument("--output-jsonl", required=True)
    parser.add_argument("--summary-json", required=True)
    return parser.parse_args()


def load_records(path: Path):
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def word_count(text: str) -> int:
    return len(text.split()) if text else 0


def similarity_score(target, source):
    score = 0
    if target["domain"] == source["domain"]:
        score += 100
    if target["gold_fail_span"]["kind"] == source["gold_fail_span"]["kind"]:
        score += 20
    if target["checker"]["type"] == source["checker"]["type"]:
        score += 20
    score -= abs(word_count(target["gold_fail_span"]["text"]) - word_count(source["gold_fail_span"]["text"]))
    score -= abs(word_count(target["gold_repair_suffix"]) - word_count(source["gold_repair_suffix"]))
    score -= abs(word_count(target["question"]) - word_count(source["question"])) * 0.1
    return score


def build_controls(records, source_records):
    revise_records = [r for r in records if r["gold_action"] == "revise"]
    source_revise_records = [r for r in source_records if r["gold_action"] == "revise"]
    by_domain = defaultdict(list)
    for record in source_revise_records:
        by_domain[record["domain"]].append(record)

    controls = []
    summary = {
        "total_pairs": len({r["pair_id"] for r in records}),
        "total_revise_records": len(revise_records),
        "same_domain_controls": 0,
        "cross_domain_controls": 0,
        "unmatched_domains": {},
    }

    all_revise = sorted(source_revise_records, key=lambda r: (r["domain"], r["pair_id"]))

    for record in sorted(revise_records, key=lambda r: (r["domain"], r["pair_id"])):
        domain_pool = [x for x in by_domain[record["domain"]] if x["pair_id"] != record["pair_id"]]
        if domain_pool:
            source = max(domain_pool, key=lambda x: similarity_score(record, x))
            shuffle_type = "same_domain_matched_shuffle"
            summary["same_domain_controls"] += 1
        else:
            global_pool = [x for x in all_revise if x["pair_id"] != record["pair_id"]]
            if not global_pool:
                source = None
            else:
                source = max(global_pool, key=lambda x: similarity_score(record, x))
            if source is None:
                summary["unmatched_domains"].setdefault(record["domain"], 0)
                summary["unmatched_domains"][record["domain"]] += 1
                continue
            shuffle_type = "cross_domain_fallback_shuffle"
            summary["cross_domain_controls"] += 1

        control = {
            "control_id": f"{record['pair_id']}__shuffle",
            "target_pair_id": record["pair_id"],
            "target_domain": record["domain"],
            "target_question": record["question"],
            "control_type": shuffle_type,
            "source_pair_id": source["pair_id"],
            "source_domain": source["domain"],
            "source_fail_span": source["gold_fail_span"],
            "source_repair_suffix": source["gold_repair_suffix"],
            "source_notes": source["notes"],
            "matching_score": similarity_score(record, source),
            "target_checker": record["checker"],
            "target_expected_final_answer": record["expected_final_answer"],
            "rationale": (
                "Use verifier-like content from a different revise example while "
                "keeping the target question and checker fixed."
            ),
        }
        controls.append(control)

    summary["controls_written"] = len(controls)
    return controls, summary


def main():
    args = parse_args()
    records = load_records(Path(args.input_jsonl))
    source_records = load_records(Path(args.source_jsonl)) if args.source_jsonl else records
    controls, summary = build_controls(records, source_records)

    output_path = Path(args.output_jsonl)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for record in controls:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    summary_path = Path(args.summary_json)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"wrote {len(controls)} controls to {output_path}")
    print(f"wrote summary to {summary_path}")


if __name__ == "__main__":
    main()
