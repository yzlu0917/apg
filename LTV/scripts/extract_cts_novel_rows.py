#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

from build_cts_auto_panel import load_jsonl, make_row_from_api


def dedupe_key(row: Dict) -> Tuple[str, int, str, str]:
    return (
        row["source_theorem_id"],
        int(row["source_step_index"]),
        row["type"],
        row["variant_step"],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract only novel CTS rows from API outputs.")
    parser.add_argument("--reference-panel", required=True)
    parser.add_argument("--api-jsonl", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    reference_rows = load_jsonl(Path(args.reference_panel))
    seen = {dedupe_key(row) for row in reference_rows}

    novel_rows: List[Dict] = []
    for path in args.api_jsonl:
        for api_row in load_jsonl(Path(path)):
            for row_type in ["same_semantics", "semantic_flip"]:
                row = make_row_from_api(api_row, row_type)
                key = dedupe_key(row)
                if key in seen:
                    continue
                seen.add(key)
                novel_rows.append(row)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for row in novel_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = {
        "reference_rows": len(reference_rows),
        "novel_rows": len(novel_rows),
        "same_pairs": sum(1 for row in novel_rows if row["type"] == "same_semantics"),
        "flip_pairs": sum(1 for row in novel_rows if row["type"] == "semantic_flip"),
        "output": str(output_path),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
