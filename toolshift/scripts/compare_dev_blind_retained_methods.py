#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from toolshift.eval import dump_json
from toolshift.panel_review import (
    compute_metric_deltas,
    extract_blind_family_metrics,
    extract_method_metrics,
    lowest_family_by_metric,
)


METRIC_NAMES: tuple[str, ...] = (
    "CAA_overall",
    "CAA_clean",
    "CAA_positive",
    "NOS",
    "POC",
    "coverage",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare retained methods between dev panel and frozen blind review.")
    parser.add_argument(
        "--dev-summary",
        default="artifacts/real_evolution_family_holdout_clause_localization_capability_v1/summary.json",
    )
    parser.add_argument(
        "--blind-summary",
        default="artifacts/real_evolution_blind_review_v1/summary.json",
    )
    parser.add_argument("--dev-regime", default="family_holdout_cv")
    parser.add_argument(
        "--methods",
        nargs="+",
        default=["semantic_embedding_capability_gate", "semantic_clause_localization_capability_gate"],
    )
    parser.add_argument("--output-dir", default="artifacts/real_evolution_dev_vs_blind_v1")
    return parser.parse_args()


def _fmt(value: float | None) -> str:
    if value is None:
        return "na"
    return f"{value:.3f}"


def _render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Dev vs Blind Retained Methods",
        "",
        f"- dev summary: `{summary['config']['dev_summary']}`",
        f"- blind summary: `{summary['config']['blind_summary']}`",
        f"- methods: `{', '.join(summary['config']['methods'])}`",
        "",
        "| Method | Dev CAA | Blind CAA | dCAA | Dev CAA+ | Blind CAA+ | dCAA+ | Dev NOS | Blind NOS | dNOS | Dev POC | Blind POC | dPOC |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for method in summary["config"]["methods"]:
        dev_metrics = summary["methods"][method]["dev_metrics"]
        blind_metrics = summary["methods"][method]["blind_metrics"]
        deltas = summary["methods"][method]["blind_minus_dev"]
        lines.append(
            f"| `{method}` | {_fmt(dev_metrics['CAA_overall'])} | {_fmt(blind_metrics['CAA_overall'])} | {_fmt(deltas['CAA_overall'])} | "
            f"{_fmt(dev_metrics['CAA_positive'])} | {_fmt(blind_metrics['CAA_positive'])} | {_fmt(deltas['CAA_positive'])} | "
            f"{_fmt(dev_metrics['NOS'])} | {_fmt(blind_metrics['NOS'])} | {_fmt(deltas['NOS'])} | "
            f"{_fmt(dev_metrics['POC'])} | {_fmt(blind_metrics['POC'])} | {_fmt(deltas['POC'])} |"
        )
    lines.append("")
    for method in summary["config"]["methods"]:
        hardest_nos = summary["methods"][method]["lowest_blind_families"]["NOS"]
        hardest_positive = summary["methods"][method]["lowest_blind_families"]["CAA_positive"]
        lines.extend(
            [
                f"## `{method}`",
                "",
                f"- lowest blind `NOS` family: `{hardest_nos['family_id']} ({_fmt(hardest_nos['value'])})`",
                f"- lowest blind `CAA+` family: `{hardest_positive['family_id']} ({_fmt(hardest_positive['value'])})`",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    args = _parse_args()
    dev_summary = json.loads(Path(args.dev_summary).read_text(encoding="utf-8"))
    blind_summary = json.loads(Path(args.blind_summary).read_text(encoding="utf-8"))

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_payload: dict[str, Any] = {
        "config": {
            "dev_summary": args.dev_summary,
            "blind_summary": args.blind_summary,
            "dev_regime": args.dev_regime,
            "methods": args.methods,
        },
        "methods": {},
    }

    for method in args.methods:
        dev_metrics = extract_method_metrics(dev_summary, method=method, regime=args.dev_regime)
        blind_metrics = extract_method_metrics(blind_summary, method=method)
        blind_family_metrics = extract_blind_family_metrics(blind_summary, method=method)
        lowest_blind_families = {}
        for metric_name in ("NOS", "CAA_positive", "CAA_overall"):
            result = lowest_family_by_metric(blind_family_metrics, metric_name)
            if result is None:
                lowest_blind_families[metric_name] = None
                continue
            family_id, value = result
            lowest_blind_families[metric_name] = {"family_id": family_id, "value": value}
        summary_payload["methods"][method] = {
            "dev_metrics": dev_metrics,
            "blind_metrics": blind_metrics,
            "blind_minus_dev": compute_metric_deltas(dev_metrics, blind_metrics, metric_names=METRIC_NAMES),
            "lowest_blind_families": lowest_blind_families,
            "blind_family_metrics": blind_family_metrics,
        }

    dump_json(str(output_dir / "summary.json"), summary_payload)
    (output_dir / "summary.md").write_text(_render_markdown(summary_payload) + "\n", encoding="utf-8")

    print("method\tdev_CAA\tblind_CAA\tdCAA\tdev_NOS\tblind_NOS\tdNOS")
    for method in args.methods:
        payload = summary_payload["methods"][method]
        print(
            f"{method}\t"
            f"{_fmt(payload['dev_metrics']['CAA_overall'])}\t"
            f"{_fmt(payload['blind_metrics']['CAA_overall'])}\t"
            f"{_fmt(payload['blind_minus_dev']['CAA_overall'])}\t"
            f"{_fmt(payload['dev_metrics']['NOS'])}\t"
            f"{_fmt(payload['blind_metrics']['NOS'])}\t"
            f"{_fmt(payload['blind_minus_dev']['NOS'])}"
        )


if __name__ == "__main__":
    main()
