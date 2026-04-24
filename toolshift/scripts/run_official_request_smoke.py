#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from toolshift import load_seed_suite
from toolshift.eval import dump_json
from toolshift.official_request_smoke import load_benchmark_payload, run_official_request_smoke


def _render_markdown(benchmark_path: str, summary: dict) -> str:
    lines = [
        "# Official Request Smoke",
        "",
        f"- Benchmark: `{benchmark_path}`",
        f"- count: `{summary['count']}`",
        f"- pass_rate: `{summary['pass_rate']:.3f}`",
        f"- emit_expected_pass_rate: `{summary['emit_expected_pass_rate']:.3f}`",
        f"- block_expected_pass_rate: `{summary['block_expected_pass_rate']:.3f}`",
        f"- emit_rate: `{summary['emit_rate']:.3f}`",
        "",
        "## By Provider",
        "",
        "| Provider | Count | Pass | Emit |",
        "| --- | ---: | ---: | ---: |",
    ]
    for provider, provider_summary in summary["provider_summary"].items():
        lines.append(
            f"| `{provider}` | {provider_summary['count']} | "
            f"{provider_summary['pass_rate']:.3f} | {provider_summary['emit_rate']:.3f} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run docs-backed official request smoke checks for a ToolShift benchmark.")
    parser.add_argument("--benchmark", default="data/real_evolution_benchmark.json")
    parser.add_argument("--output-dir", default="artifacts/real_evolution_official_request_smoke")
    args = parser.parse_args()

    suite = load_seed_suite(args.benchmark)
    benchmark_payload = load_benchmark_payload(args.benchmark)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    records, summary = run_official_request_smoke(suite=suite, benchmark_payload=benchmark_payload)
    dump_json(str(output_dir / "records.json"), [record.to_dict() for record in records])
    dump_json(str(output_dir / "summary.json"), summary)
    (output_dir / "summary.md").write_text(_render_markdown(args.benchmark, summary), encoding="utf-8")

    print(
        "count\tpass_rate\temit_expected\tblock_expected\temit_rate",
        flush=True,
    )
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
