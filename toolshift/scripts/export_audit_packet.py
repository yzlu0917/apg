#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from toolshift import load_seed_suite


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a transform audit packet for ToolShift.")
    parser.add_argument("--benchmark", default="data/seed_benchmark.json")
    parser.add_argument("--output", default="artifacts/audit/transform_validity.jsonl")
    args = parser.parse_args()

    suite = load_seed_suite(args.benchmark)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as handle:
        for example in suite.examples:
            payload = {
                "case_id": example.case.case_id,
                "request": example.case.request,
                "view_id": example.schema_view.view_id,
                "transform_name": example.schema_view.transform_name,
                "shift_kind": example.schema_view.shift_kind.value,
                "notes": example.schema_view.notes,
                "expected_actions": [action.to_dict() for action in example.admissible_actions],
                "tools": [tool.to_dict() for tool in example.schema_view.tools],
            }
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    print(output_path)


if __name__ == "__main__":
    main()

