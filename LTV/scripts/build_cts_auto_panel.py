#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Tuple


def load_jsonl(path: Path) -> List[Dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def dedupe_key(row: Dict) -> Tuple[str, int, str, str]:
    return (
        row["source_theorem_id"],
        int(row["source_step_index"]),
        row["type"],
        row["variant_step"],
    )


def make_row_from_api(row: Dict, row_type: str) -> Dict:
    variant_key = "same_semantics" if row_type == "same_semantics" else "semantic_flip"
    note_key = "same_rationale" if row_type == "same_semantics" else "flip_rationale"
    prompt_mode = row["api_provenance"].get("prompt_mode", "unknown")
    pair_source_id = row["pair_source_id"]
    suffix = "same" if row_type == "same_semantics" else "flip"
    variant_hash = hashlib.sha1(row[variant_key].encode("utf-8")).hexdigest()[:8]
    pair_id = f"{pair_source_id}__{prompt_mode}__{suffix}__{variant_hash}"
    return {
        "pair_id": pair_id,
        "type": row_type,
        "source_theorem_id": row["source_theorem_id"],
        "source_step_index": int(row["source_step_index"]),
        "source_step": row["source_step"],
        "variant_step": row[variant_key],
        "expected_label_change": 0 if row_type == "same_semantics" else 1,
        "notes": row.get(note_key, ""),
        "provenance": f"api_{prompt_mode}",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a larger CTS auto panel from manual seed + API outputs.")
    parser.add_argument("--manual-panel", required=True)
    parser.add_argument("--api-jsonl", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    manual_rows = load_jsonl(Path(args.manual_panel))
    api_rows = []
    for path in args.api_jsonl:
        api_rows.extend(load_jsonl(Path(path)))

    combined = list(manual_rows)
    seen = {dedupe_key(row) for row in manual_rows}

    for api_row in api_rows:
        for row_type in ["same_semantics", "semantic_flip"]:
            row = make_row_from_api(api_row, row_type)
            key = dedupe_key(row)
            if key in seen:
                continue
            seen.add(key)
            combined.append(row)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for row in combined:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = {
        "manual_rows": len(manual_rows),
        "api_rows": len(api_rows),
        "combined_rows": len(combined),
        "same_pairs": sum(1 for row in combined if row["type"] == "same_semantics"),
        "flip_pairs": sum(1 for row in combined if row["type"] == "semantic_flip"),
        "output": str(output_path),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
