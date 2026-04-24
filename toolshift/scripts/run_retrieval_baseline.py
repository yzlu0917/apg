#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from toolshift import DocumentRetrievalRerankAgent, evaluate_agent, load_seed_suite
from toolshift.eval import dump_json


def _fmt_metric(value) -> str:
    if value is None:
        return "na"
    return f"{value:.3f}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the document-retrieval baseline on any ToolShift-compatible benchmark.")
    parser.add_argument("--benchmark", default="data/real_evolution_benchmark.json")
    parser.add_argument("--output-dir", default="artifacts/doc_retrieval_baseline")
    parser.add_argument("--name", default="doc_retrieval_rerank")
    args = parser.parse_args()

    suite = load_seed_suite(args.benchmark)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    agent = DocumentRetrievalRerankAgent(name=args.name)
    records, summary = evaluate_agent(agent, suite)

    dump_json(str(output_dir / "summary.json"), summary)
    dump_json(str(output_dir / "records.json"), [record.to_dict(suite.tool_lookup) for record in records])

    metrics = summary["metrics"]
    print("agent\tCAA\tCAA_clean\tCAA+\tNOS\tPOC\tcoverage")
    print(
        f"{agent.name}\t"
        f"{_fmt_metric(metrics['CAA_overall'])}\t"
        f"{_fmt_metric(metrics['CAA_clean'])}\t"
        f"{_fmt_metric(metrics['CAA_positive'])}\t"
        f"{_fmt_metric(metrics['NOS'])}\t"
        f"{_fmt_metric(metrics['POC'])}\t"
        f"{_fmt_metric(metrics['coverage'])}"
    )


if __name__ == "__main__":
    main()
