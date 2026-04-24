#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from toolshift.api_bank_import import build_api_bank_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(description="Import a public API-Bank subset into a TOOLSHIFT-compatible benchmark.")
    parser.add_argument("--output-benchmark", default="data/api_bank_toolshift_benchmark.json")
    parser.add_argument("--output-audit", default="history/api_bank_import_audit.md")
    args = parser.parse_args()

    benchmark_path = Path(args.output_benchmark)
    benchmark_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path = Path(args.output_audit)
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    payload, audit_markdown = build_api_bank_benchmark()
    benchmark_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    audit_path.write_text(audit_markdown, encoding="utf-8")

    print(f"Wrote benchmark to {benchmark_path}")
    print(f"Wrote audit to {audit_path}")
    print(
        "Imported "
        f"{payload['metadata']['case_count']} cases, "
        f"{payload['metadata']['tool_count']} tools, "
        f"{len(payload['metadata']['family_tags'])} family tags."
    )


if __name__ == "__main__":
    main()
