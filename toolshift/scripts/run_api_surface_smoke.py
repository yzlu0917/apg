#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from toolshift import load_seed_suite
from toolshift.api_surface_smoke import run_api_surface_smoke
from toolshift.eval import dump_json
from toolshift.official_request_smoke import load_benchmark_payload


def _render_markdown(benchmark_path: str, summary: dict) -> str:
    lines = [
        "# API Surface Smoke",
        "",
        f"- Benchmark: `{benchmark_path}`",
        f"- count: `{summary['count']}`",
        f"- pass_rate: `{summary['pass_rate']:.3f}`",
        f"- emit_expected_pass_rate: `{summary['emit_expected_pass_rate']:.3f}`",
        f"- block_expected_pass_rate: `{summary['block_expected_pass_rate']:.3f}`",
        f"- emit_rate: `{summary['emit_rate']:.3f}`",
        "",
        "## By Kind",
        "",
        "| Kind | Count | Pass | Emit |",
        "| --- | ---: | ---: | ---: |",
    ]
    for kind, payload in summary["by_kind"].items():
        lines.append(f"| `{kind}` | {payload['count']} | {payload['pass_rate']:.3f} | {payload['emit_rate']:.3f} |")
    lines.extend(
        [
            "",
            "## By Provider",
            "",
            "| Provider | Count | Pass | Emit |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for provider, payload in summary["by_provider"].items():
        lines.append(f"| `{provider}` | {payload['count']} | {payload['pass_rate']:.3f} | {payload['emit_rate']:.3f} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run spec-backed API surface smoke checks for a ToolShift benchmark.")
    parser.add_argument("--benchmark", default="data/real_evolution_benchmark.json")
    parser.add_argument("--output-dir", default="artifacts/real_evolution_api_surface_smoke")
    args = parser.parse_args()

    suite = load_seed_suite(args.benchmark)
    benchmark_payload = load_benchmark_payload(args.benchmark)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    records, summary = run_api_surface_smoke(suite=suite, benchmark_payload=benchmark_payload)
    dump_json(str(output_dir / "records.json"), [record.to_dict() for record in records])
    dump_json(str(output_dir / "summary.json"), summary)
    (output_dir / "summary.md").write_text(_render_markdown(args.benchmark, summary), encoding="utf-8")

    print("count\tpass_rate\temit_expected\tblock_expected\temit_rate", flush=True)
    print(
        f"{summary['count']}\t"
        f"{summary['pass_rate']:.3f}\t"
        f"{summary['emit_expected_pass_rate']:.3f}\t"
        f"{summary['block_expected_pass_rate']:.3f}\t"
        f"{summary['emit_rate']:.3f}",
        flush=True,
    )


if __name__ == "__main__":
    main()
