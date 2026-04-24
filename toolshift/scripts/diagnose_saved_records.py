#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from toolshift import load_seed_suite
from toolshift.diagnostics import summarize_serialized_records
from toolshift.eval import dump_json


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Factorize saved eval records into control/tool/argument error buckets.")
    parser.add_argument("--records", required=True, help="Path to saved records.json.")
    parser.add_argument("--benchmark", required=True, help="Benchmark JSON used to produce the records.")
    parser.add_argument("--output-dir", required=True, help="Directory for diagnostic summaries.")
    parser.add_argument("--regime", action="append", dest="regimes", help="Optional regime filter. Repeatable.")
    parser.add_argument("--method", action="append", dest="methods", help="Optional method filter. Repeatable.")
    parser.add_argument("--max-examples-per-bucket", type=int, default=3, help="Representative failure examples per bucket.")
    return parser.parse_args()


def _iter_selected_payload(payload: dict[str, Any], regimes: list[str] | None, methods: list[str] | None):
    regime_names = regimes or sorted(payload)
    for regime_name in regime_names:
        regime_payload = payload[regime_name]
        method_names = methods or sorted(regime_payload)
        for method_name in method_names:
            yield regime_name, method_name, regime_payload[method_name]


def _render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Saved Record Diagnostics",
        "",
        f"- Records: `{summary['records_path']}`",
        f"- Benchmark: `{summary['benchmark_path']}`",
        "",
    ]
    for regime_name, regime_payload in summary["regimes"].items():
        lines.extend([f"## {regime_name}", ""])
        for method_name, method_payload in regime_payload.items():
            aggregate = method_payload["aggregate"]
            lines.extend(
                [
                    f"### {method_name}",
                    "",
                    f"- count: `{aggregate['count']}`",
                    f"- admissible_rate: `{aggregate['admissible_rate']:.3f}`",
                    f"- execute_rate: `{aggregate['execute_rate']:.3f}`",
                    f"- ask_clarification_rate: `{aggregate['ask_clarification_rate']:.3f}`",
                    f"- abstain_rate: `{aggregate['abstain_rate']:.3f}`",
                    f"- group_counts: `{json.dumps(aggregate['group_counts'], sort_keys=True)}`",
                    f"- bucket_counts: `{json.dumps(aggregate['bucket_counts'], sort_keys=True)}`",
                    "",
                ]
            )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = _parse_args()
    records_path = Path(args.records)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    suite = load_seed_suite(args.benchmark)
    case_to_family = {case.case_id: case.primary_action.tool_id or "none" for case in suite.cases}
    payload = json.loads(records_path.read_text(encoding="utf-8"))

    summaries: dict[str, Any] = {
        "records_path": str(records_path),
        "benchmark_path": str(Path(args.benchmark)),
        "regimes": {},
    }
    for regime_name, method_name, method_payload in _iter_selected_payload(payload, args.regimes, args.methods):
        per_seed = {}
        aggregate_records: list[dict[str, Any]] = []
        for seed_name, records in sorted(method_payload.items()):
            per_seed[seed_name] = summarize_serialized_records(
                records,
                case_to_family=case_to_family,
                max_examples_per_bucket=args.max_examples_per_bucket,
            )
            aggregate_records.extend(records)
        summaries["regimes"].setdefault(regime_name, {})[method_name] = {
            "per_seed": per_seed,
            "aggregate": summarize_serialized_records(
                aggregate_records,
                case_to_family=case_to_family,
                max_examples_per_bucket=args.max_examples_per_bucket,
            ),
        }

    dump_json(str(output_dir / "summary.json"), summaries)
    (output_dir / "summary.md").write_text(_render_markdown(summaries), encoding="utf-8")

    for regime_name, regime_payload in summaries["regimes"].items():
        for method_name, method_payload in regime_payload.items():
            aggregate = method_payload["aggregate"]
            print(
                f"[{regime_name}] {method_name} "
                f"admissible={aggregate['admissible_rate']:.3f} "
                f"execute_rate={aggregate['execute_rate']:.3f} "
                f"group_counts={json.dumps(aggregate['group_counts'], sort_keys=True)}",
                flush=True,
            )


if __name__ == "__main__":
    main()
