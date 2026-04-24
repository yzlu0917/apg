#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from toolshift import load_seed_suite
from toolshift.eval import dump_json
from toolshift.fixed_panel_compare import (
    build_view_metadata,
    compare_methods,
    flatten_method_records,
    render_markdown,
    summarize_seeds,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare fixed-panel methods on saved matched-budget records.")
    parser.add_argument("--records", required=True, help="Path to records.json from run_matched_budget_pilot.py.")
    parser.add_argument("--benchmark", required=True, help="Benchmark JSON used to produce the records.")
    parser.add_argument("--regime", default="family_holdout_cv", help="Regime name inside records.json.")
    parser.add_argument("--methods", nargs="+", help="Methods to compare. Defaults to all methods in the regime.")
    parser.add_argument("--output-dir", required=True, help="Directory for comparison artifacts.")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    records_path = Path(args.records)
    payload = json.loads(records_path.read_text(encoding="utf-8"))
    regime_payload = payload[args.regime]
    methods = args.methods or sorted(regime_payload)
    if len(methods) < 2:
        raise ValueError("Need at least two methods to compare.")

    suite = load_seed_suite(args.benchmark)
    view_metadata = build_view_metadata(suite)

    method_records = {
        method: flatten_method_records(payload, regime=args.regime, method=method, view_metadata=view_metadata)
        for method in methods
    }
    method_summaries = {method: summarize_seeds(records) for method, records in method_records.items()}

    baseline_method = methods[0]
    comparisons: dict[str, Any] = {}
    for candidate_method in methods[1:]:
        comparison_name = f"{candidate_method} vs {baseline_method}"
        comparisons[comparison_name] = compare_methods(method_records[baseline_method], method_records[candidate_method])

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "records_path": str(records_path),
        "benchmark_path": str(Path(args.benchmark)),
        "regime": args.regime,
        "methods": methods,
        "method_summaries": method_summaries,
        "comparisons": comparisons,
    }
    dump_json(str(output_dir / "summary.json"), summary)
    (output_dir / "summary.md").write_text(
        render_markdown(
            records_path=str(records_path),
            benchmark_path=str(Path(args.benchmark)),
            regime=args.regime,
            methods=methods,
            method_summaries=method_summaries,
            comparisons=comparisons,
        ),
        encoding="utf-8",
    )

    print("method\tCAA\tCAA+\tNOS\tPOC\tcoverage")
    for method in methods:
        metrics = method_summaries[method]["metrics_mean"]
        print(
            f"{method}\t"
            f"{_fmt(metrics['CAA_overall'])}\t"
            f"{_fmt(metrics['CAA_positive'])}\t"
            f"{_fmt(metrics['NOS'])}\t"
            f"{_fmt(metrics['POC'])}\t"
            f"{_fmt(metrics['coverage'])}"
        )
    for comparison_name, comparison in comparisons.items():
        print(
            f"{comparison_name}: "
            f"improved_pairs={comparison['improved_pair_count']} "
            f"regressed_pairs={comparison['regressed_pair_count']} "
            f"strictly_fixed_views={comparison['strictly_fixed_views']}"
        )


def _fmt(value: float | None) -> str:
    if value is None:
        return "na"
    return f"{value:.3f}"


if __name__ == "__main__":
    main()
