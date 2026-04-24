#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from toolshift import load_seed_suite
from toolshift.eval import dump_json
from toolshift.execution_sanity import run_execution_sanity


def _render_markdown(benchmark_path: str, summary: dict) -> str:
    lines = [
        "# Execution Sanity",
        "",
        f"- Benchmark: `{benchmark_path}`",
        f"- count: `{summary['count']}`",
        f"- pass_rate: `{summary['pass_rate']:.3f}`",
        f"- execute_expected_pass_rate: `{summary['execute_expected_pass_rate']:.3f}`",
        f"- negative_guard_pass_rate: `{summary['negative_guard_pass_rate']:.3f}`",
        f"- positive_equivalence_rate: `{summary['positive_equivalence_rate']:.3f}`",
        "",
        "## By Transform",
        "",
        "| Transform | Count | Pass | Execute | Satisfied |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for transform_name, transform_summary in summary["by_transform"].items():
        lines.append(
            f"| `{transform_name}` | {transform_summary['count']} | "
            f"{transform_summary['pass_rate']:.3f} | {transform_summary['execute_rate']:.3f} | {transform_summary['satisfied_rate']:.3f} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run deterministic execution-level sanity checks for a ToolShift benchmark.")
    parser.add_argument("--benchmark", default="data/real_evolution_benchmark.json")
    parser.add_argument("--output-dir", default="artifacts/real_evolution_execution_sanity")
    args = parser.parse_args()

    suite = load_seed_suite(args.benchmark)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    records, summary = run_execution_sanity(suite)
    dump_json(str(output_dir / "records.json"), [record.to_dict() for record in records])
    dump_json(str(output_dir / "summary.json"), summary)
    (output_dir / "summary.md").write_text(_render_markdown(args.benchmark, summary), encoding="utf-8")

    print(
        "count\tpass_rate\texec_pass\tnegative_guard\tpositive_equivalence",
        flush=True,
    )
    print(
        f"{summary['count']}\t"
        f"{summary['pass_rate']:.3f}\t"
        f"{summary['execute_expected_pass_rate']:.3f}\t"
        f"{summary['negative_guard_pass_rate']:.3f}\t"
        f"{summary['positive_equivalence_rate']:.3f}",
        flush=True,
    )


if __name__ == "__main__":
    main()
