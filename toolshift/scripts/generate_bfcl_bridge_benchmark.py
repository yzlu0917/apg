#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from toolshift.bfcl_bridge import build_bfcl_bridge_payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a TOOLSHIFT-compatible bridge benchmark from BFCL v4 categories.")
    parser.add_argument("--output-benchmark", default="data/bfcl_bridge_benchmark.json")
    parser.add_argument("--output-audit", default="data/bfcl_bridge_audit.json")
    parser.add_argument("--output-audit-md", default="history/bfcl_bridge_audit.md")
    args = parser.parse_args()

    benchmark_payload, audit_payload, audit_markdown = build_bfcl_bridge_payload()

    benchmark_path = Path(args.output_benchmark)
    audit_path = Path(args.output_audit)
    audit_markdown_path = Path(args.output_audit_md)

    benchmark_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_markdown_path.parent.mkdir(parents=True, exist_ok=True)

    benchmark_path.write_text(json.dumps(benchmark_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    audit_path.write_text(json.dumps(audit_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    audit_markdown_path.write_text(audit_markdown + "\n", encoding="utf-8")

    metadata = benchmark_payload["metadata"]
    print(
        "Wrote BFCL bridge benchmark with "
        f"{len(benchmark_payload['cases'])} cases / {len(benchmark_payload['tools'])} tools "
        f"across {len(metadata['selected_counts'])} categories to {benchmark_path}"
    )


if __name__ == "__main__":
    main()
