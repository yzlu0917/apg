#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from toolshift import load_seed_suite
from toolshift.panel_stability import (
    BOOTSTRAP_METRICS,
    aggregate_seed_metrics,
    build_case_group_maps,
    cluster_bootstrap_metrics,
    leave_one_group_out_metrics,
)
from toolshift.reliability import load_flat_eval_records, load_nested_eval_records


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run family/vendor bootstrap and leave-one-out stability analysis.")
    parser.add_argument("--benchmark", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--bootstrap-replicates", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--flat-record", action="append", default=[], help="Flat record spec NAME=PATH")
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


def _fmt(value: float | None) -> str:
    if value is None:
        return "na"
    return f"{value:.3f}"


def _render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Panel Stability",
        "",
        f"- benchmark: `{summary['config']['benchmark']}`",
        f"- bootstrap_replicates: `{summary['config']['bootstrap_replicates']}`",
        "",
    ]
    for method, payload in summary["methods"].items():
        lines.append(f"## `{method}`")
        lines.append("")
        lines.append("| Metric | Point | Family CI | Vendor CI |")
        lines.append("| --- | ---: | ---: | ---: |")
        for metric_name in BOOTSTRAP_METRICS:
            point = payload["point_metrics"].get(metric_name)
            family_ci = payload["family_bootstrap"].get(metric_name, {})
            vendor_ci = payload["vendor_bootstrap"].get(metric_name, {})
            lines.append(
                f"| `{metric_name}` | {_fmt(point)} | "
                f"[{_fmt(family_ci.get('lo'))}, {_fmt(family_ci.get('hi'))}] | "
                f"[{_fmt(vendor_ci.get('lo'))}, {_fmt(vendor_ci.get('hi'))}] |"
            )
        lines.append("")
        lines.append("| Leave-one-family-out | CAA | CAA+ | NOS | POC |")
        lines.append("| --- | ---: | ---: | ---: | ---: |")
        for group, metrics in payload["leave_one_family_out"].items():
            lines.append(
                f"| `{group}` | {_fmt(metrics['CAA_overall'])} | {_fmt(metrics['CAA_positive'])} | "
                f"{_fmt(metrics['NOS'])} | {_fmt(metrics['POC'])} |"
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

    group_maps = build_case_group_maps(payload)
    summary: dict[str, Any] = {
        "config": {
            "benchmark": args.benchmark,
            "bootstrap_replicates": args.bootstrap_replicates,
            "seed": args.seed,
            "methods": list(method_seed_records),
        },
        "methods": {},
    }

    for method_name, seed_records in method_seed_records.items():
        summary["methods"][method_name] = {
            "point_metrics": aggregate_seed_metrics(seed_records, suite),
            "family_bootstrap": cluster_bootstrap_metrics(
                seed_records,
                suite,
                case_to_group=group_maps["family"],
                replicates=args.bootstrap_replicates,
                seed=args.seed,
            ),
            "vendor_bootstrap": cluster_bootstrap_metrics(
                seed_records,
                suite,
                case_to_group=group_maps["vendor"],
                replicates=args.bootstrap_replicates,
                seed=args.seed + 1,
            ),
            "leave_one_family_out": leave_one_group_out_metrics(
                seed_records,
                suite,
                case_to_group=group_maps["family"],
            ),
            "leave_one_vendor_out": leave_one_group_out_metrics(
                seed_records,
                suite,
                case_to_group=group_maps["vendor"],
            ),
        }

    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output_dir / "summary.md").write_text(_render_markdown(summary) + "\n", encoding="utf-8")

    print("method\tCAA\tCAA+\tNOS\tPOC\tfamily_NOS_CI\tvendor_NOS_CI")
    for method_name, payload in summary["methods"].items():
        point = payload["point_metrics"]
        family_ci = payload["family_bootstrap"]["NOS"]
        vendor_ci = payload["vendor_bootstrap"]["NOS"]
        print(
            f"{method_name}\t{_fmt(point['CAA_overall'])}\t{_fmt(point['CAA_positive'])}\t{_fmt(point['NOS'])}\t"
            f"{_fmt(point['POC'])}\t[{_fmt(family_ci['lo'])},{_fmt(family_ci['hi'])}]\t"
            f"[{_fmt(vendor_ci['lo'])},{_fmt(vendor_ci['hi'])}]"
        )


if __name__ == "__main__":
    main()
