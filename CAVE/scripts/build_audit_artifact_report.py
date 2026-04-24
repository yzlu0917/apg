#!/usr/bin/env python3

import argparse
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_jsonl")
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--output-json", required=True)
    return parser.parse_args()


def load_records(path: Path):
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def text_len(value: str) -> int:
    return len(value.split()) if value else 0


def build_report(records):
    pairs = defaultdict(list)
    for record in records:
        pairs[record["pair_id"]].append(record)

    per_pair = []
    domains = Counter()
    risk_counts = Counter()

    for pair_id, items in sorted(pairs.items()):
        keep = next(item for item in items if item["gold_action"] == "keep")
        revise = next(item for item in items if item["gold_action"] == "revise")
        domains[keep["domain"]] += 1

        fail_span_words = text_len(revise["gold_fail_span"]["text"])
        repair_words = text_len(revise["gold_repair_suffix"])
        trace_len_gap = abs(text_len(keep["initial_trace"]) - text_len(revise["initial_trace"]))

        risks = []
        if fail_span_words <= 2:
            risks.append("tiny_fail_span")
        if repair_words <= 3:
            risks.append("tiny_repair_suffix")
        if trace_len_gap >= 8:
            risks.append("large_trace_length_gap")
        if keep["gold_fail_span"]["text"] != "":
            risks.append("keep_has_nonempty_fail_span")

        for risk in risks:
            risk_counts[risk] += 1

        per_pair.append(
            {
                "pair_id": pair_id,
                "domain": keep["domain"],
                "fail_span_words": fail_span_words,
                "repair_suffix_words": repair_words,
                "trace_len_gap_words": trace_len_gap,
                "risks": risks,
            }
        )

    report = {
        "pair_count": len(per_pair),
        "domains": dict(domains),
        "risk_counts": dict(risk_counts),
        "median_fail_span_words": statistics.median(x["fail_span_words"] for x in per_pair),
        "median_repair_suffix_words": statistics.median(x["repair_suffix_words"] for x in per_pair),
        "median_trace_len_gap_words": statistics.median(x["trace_len_gap_words"] for x in per_pair),
        "pairs": per_pair,
    }
    return report


def render_markdown(report):
    lines = [
        "# Audit Artifact Report",
        "",
        f"- Pair count: {report['pair_count']}",
        f"- Domains: {report['domains']}",
        f"- Risk counts: {report['risk_counts']}",
        f"- Median fail-span words: {report['median_fail_span_words']}",
        f"- Median repair-suffix words: {report['median_repair_suffix_words']}",
        f"- Median trace-length gap words: {report['median_trace_len_gap_words']}",
        "",
        "## Pair Summary",
        "",
    ]
    for pair in report["pairs"]:
        lines.extend(
            [
                f"- `{pair['pair_id']}` ({pair['domain']}): "
                f"fail_span_words={pair['fail_span_words']}, "
                f"repair_suffix_words={pair['repair_suffix_words']}, "
                f"trace_len_gap_words={pair['trace_len_gap_words']}, "
                f"risks={pair['risks'] or ['none']}",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def main():
    args = parse_args()
    report = build_report(load_records(Path(args.input_jsonl)))

    output_md = Path(args.output_md)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(render_markdown(report), encoding="utf-8")

    output_json = Path(args.output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"wrote markdown report to {output_md}")
    print(f"wrote json report to {output_json}")


if __name__ == "__main__":
    main()
