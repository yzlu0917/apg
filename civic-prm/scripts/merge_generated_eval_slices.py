from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge generated evaluation slices with optional domain filtering.")
    parser.add_argument("--base-dataset", type=Path, required=True)
    parser.add_argument(
        "--keep-domains",
        nargs="*",
        default=None,
        help="Domains to keep from the base dataset. If omitted, keep all rows.",
    )
    parser.add_argument(
        "--append-dataset",
        type=Path,
        action="append",
        default=[],
        help="Additional dataset(s) to append in order.",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    return parser.parse_args()


def load_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    args = parse_args()
    merged = []
    base_rows = load_rows(args.base_dataset)
    if args.keep_domains:
        domain_filter = set(args.keep_domains)
        base_rows = [row for row in base_rows if row["domain"] in domain_filter]
    merged.extend(base_rows)
    for append_path in args.append_dataset:
        merged.extend(load_rows(append_path))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row in merged:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    domains = {}
    for row in merged:
        domains[row["domain"]] = domains.get(row["domain"], 0) + 1
    summary = {
        "base_dataset": str(args.base_dataset),
        "keep_domains": args.keep_domains,
        "append_datasets": [str(path) for path in args.append_dataset],
        "num_rows": len(merged),
        "num_quartets": len({row["quartet_id"] for row in merged}),
        "domains": domains,
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
