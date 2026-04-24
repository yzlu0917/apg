#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from toolshift import DescriptionGroundedAgent, LexicalShortcutAgent, OracleAgent, evaluate_agent, load_seed_suite
from toolshift.eval import dump_json, nos_at_coverage


def _fmt_metric(value) -> str:
    if value is None:
        return "na"
    return f"{value:.3f}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the ToolShift seed benchmark pilot.")
    parser.add_argument("--benchmark", default="data/seed_benchmark.json")
    parser.add_argument("--output-dir", default="artifacts/seed_pilot")
    args = parser.parse_args()

    suite = load_seed_suite(args.benchmark)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    agents = [OracleAgent(), LexicalShortcutAgent(), DescriptionGroundedAgent()]
    all_records = {}
    summaries = {}
    for agent in agents:
        records, summary = evaluate_agent(agent, suite)
        all_records[agent.name] = [record.to_dict(suite.tool_lookup) for record in records]
        summaries[agent.name] = summary

    matched_coverage = min(
        summaries[agent.name]["metrics"]["negative_coverage"]
        for agent in agents
    )
    for agent in agents:
        records, _ = evaluate_agent(agent, suite)
        summaries[agent.name]["metrics"]["NOS@matched_negative_coverage"] = nos_at_coverage(records, matched_coverage)

    dump_json(str(output_dir / "summary.json"), summaries)
    dump_json(str(output_dir / "records.json"), all_records)
    print(f"Matched negative coverage: {matched_coverage:.3f}")
    print("agent\tCAA\tCAA+\tNOS\tPOC\tcoverage")
    for agent in agents:
        metrics = summaries[agent.name]["metrics"]
        print(
            f"{agent.name}\t"
            f"{_fmt_metric(metrics['CAA_overall'])}\t"
            f"{_fmt_metric(metrics['CAA_positive'])}\t"
            f"{_fmt_metric(metrics['NOS'])}\t"
            f"{_fmt_metric(metrics['POC'])}\t"
            f"{_fmt_metric(metrics['coverage'])}"
        )


if __name__ == "__main__":
    main()
