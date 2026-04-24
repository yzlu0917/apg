#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from toolshift import load_seed_suite
from toolshift.protocol_reliability import POLICY_VARIANTS, apply_policy_variant, summarize_benchmark_protocol, summarize_protocol_records
from toolshift.reliability import load_flat_eval_records, load_nested_eval_records


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit protocol structure and split sensitivity for a ToolShift benchmark.")
    parser.add_argument("--benchmark", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--flat-record",
        action="append",
        default=[],
        help="Flat record spec NAME=PATH",
    )
    parser.add_argument(
        "--nested-record",
        action="append",
        default=[],
        help="Nested blind-review record spec NAME=PATH:INNER_METHOD",
    )
    return parser.parse_args()


def _parse_flat_spec(spec: str) -> tuple[str, str]:
    if "=" not in spec:
        raise ValueError(f"invalid flat record spec: {spec}")
    name, path = spec.split("=", 1)
    return name, path


def _parse_nested_spec(spec: str) -> tuple[str, str, str]:
    if "=" not in spec or ":" not in spec:
        raise ValueError(f"invalid nested record spec: {spec}")
    name, remainder = spec.split("=", 1)
    path, method = remainder.rsplit(":", 1)
    return name, path, method


def _fmt(value: float | int | None) -> str:
    if value is None:
        return "na"
    if isinstance(value, int):
        return str(value)
    return f"{value:.3f}"


def _render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Protocol Reliability",
        "",
        f"- benchmark: `{summary['config']['benchmark']}`",
        f"- methods: `{', '.join(summary['config']['methods']) if summary['config']['methods'] else 'none'}`",
        "",
        "## Structure",
        "",
        f"- counts: `{json.dumps(summary['structure']['counts'], sort_keys=True)}`",
        f"- family_counts: `{json.dumps(summary['structure']['family_counts'], sort_keys=True)}`",
        f"- vendor_counts: `{json.dumps(summary['structure']['vendor_counts'], sort_keys=True)}`",
        f"- action_size_histogram: `{json.dumps(summary['structure']['action_size_histogram'], sort_keys=True)}`",
        f"- control_signature_histogram: `{json.dumps(summary['structure']['control_signature_histogram'], sort_keys=True)}`",
        f"- multi_action_view_fraction: `{_fmt(summary['structure']['multi_action_view_fraction'])}`",
        f"- multi_action_negative_fraction: `{_fmt(summary['structure']['multi_action_negative_fraction'])}`",
        f"- case_source_summary: `{json.dumps(summary['structure']['case_source_summary'], sort_keys=True)}`",
        "",
    ]
    for variant, variant_payload in summary["policy_variants"].items():
        lines.append(f"## `{variant}`")
        lines.append("")
        lines.append(
            f"- variant_details: `{json.dumps(variant_payload['variant_details'], sort_keys=True)}`"
        )
        if not variant_payload["methods"]:
            lines.append("")
            continue
        lines.append("")
        lines.append("| Method | CAA | CAA+ | NOS | POC | Coverage | Core | Ambiguous |")
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
        for method, method_payload in variant_payload["methods"].items():
            metrics = method_payload["summary"]["metrics"]
            counts = method_payload["summary"]["counts"]
            lines.append(
                f"| `{method}` | {_fmt(metrics['CAA_overall'])} | {_fmt(metrics['CAA_positive'])} | "
                f"{_fmt(metrics['NOS'])} | {_fmt(metrics['POC'])} | {_fmt(metrics['coverage'])} | "
                f"{counts['core']} | {counts['ambiguous']} |"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = _parse_args()
    suite = load_seed_suite(args.benchmark)
    payload = json.loads(Path(args.benchmark).read_text(encoding="utf-8"))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    method_seed_records: dict[str, dict[str, list[Any]]] = {}
    for spec in args.flat_record:
        name, path = _parse_flat_spec(spec)
        method_seed_records[name] = {"seed_0": load_flat_eval_records(path)}
    for spec in args.nested_record:
        name, path, method = _parse_nested_spec(spec)
        method_seed_records[name] = load_nested_eval_records(path, method)

    summary: dict[str, Any] = {
        "config": {
            "benchmark": args.benchmark,
            "methods": list(method_seed_records),
        },
        "structure": summarize_benchmark_protocol(payload),
        "policy_variants": {},
    }

    for variant in POLICY_VARIANTS:
        variant_payload: dict[str, Any] = {
            "variant_details": {},
            "methods": {},
        }
        for method_name, seed_records in method_seed_records.items():
            seed_summaries: dict[str, Any] = {}
            variant_details = None
            for seed_name, records in seed_records.items():
                variant_records, details = apply_policy_variant(suite, records, variant=variant)
                variant_details = details
                seed_summaries[seed_name] = summarize_protocol_records(variant_records, suite.tool_lookup)
            variant_payload["variant_details"] = variant_details or {}
            if seed_summaries:
                first_seed = next(iter(seed_summaries))
                metrics_keys = seed_summaries[first_seed]["metrics"].keys()
                aggregate_metrics = {}
                for key in metrics_keys:
                    values = [seed_payload["metrics"][key] for seed_payload in seed_summaries.values()]
                    if any(value is None for value in values):
                        aggregate_metrics[key] = None
                    else:
                        aggregate_metrics[key] = sum(float(value) for value in values) / len(values)
                aggregate_counts = {}
                for key in seed_summaries[first_seed]["counts"]:
                    aggregate_counts[key] = int(
                        round(sum(seed_payload["counts"][key] for seed_payload in seed_summaries.values()) / len(seed_summaries))
                    )
                variant_payload["methods"][method_name] = {
                    "per_seed": seed_summaries,
                    "summary": {
                        "metrics": aggregate_metrics,
                        "counts": aggregate_counts,
                    },
                }
        summary["policy_variants"][variant] = variant_payload

    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output_dir / "summary.md").write_text(_render_markdown(summary) + "\n", encoding="utf-8")

    print("variant\tmethod\tCAA\tCAA+\tNOS\tPOC\tcoverage")
    for variant, variant_payload in summary["policy_variants"].items():
        for method, method_payload in variant_payload["methods"].items():
            metrics = method_payload["summary"]["metrics"]
            print(
                f"{variant}\t{method}\t{_fmt(metrics['CAA_overall'])}\t{_fmt(metrics['CAA_positive'])}\t"
                f"{_fmt(metrics['NOS'])}\t{_fmt(metrics['POC'])}\t{_fmt(metrics['coverage'])}"
            )


if __name__ == "__main__":
    main()
