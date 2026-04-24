#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def load_rows(path: Path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def main():
    parser = argparse.ArgumentParser(description="Apply explicit adjudication overrides to a state-first oracle panel.")
    parser.add_argument("--base-oracle", required=True)
    parser.add_argument("--overrides", required=True, help="JSON file mapping state_id -> candidate_index -> {progress_tier, oracle_rationale}")
    parser.add_argument("--output", required=True)
    parser.add_argument("--oracle-source", default="manual_consensus_v0")
    args = parser.parse_args()

    rows = load_rows(Path(args.base_oracle))
    overrides = json.loads(Path(args.overrides).read_text(encoding="utf-8"))

    for row in rows:
        row["oracle_source"] = args.oracle_source
        state_overrides = overrides.get(row["state_id"], {})
        for candidate in row["candidates"]:
            key = str(candidate["candidate_index"])
            if key in state_overrides:
                patch = state_overrides[key]
                candidate["progress_tier"] = patch["progress_tier"]
                candidate["oracle_rationale"] = patch["oracle_rationale"]

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "num_states": len(rows)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
