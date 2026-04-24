#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from cnt_research.math.countertrace_mini import merge_countertrace_mini_runs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge multiple CounterTrace-mini(math) runs.")
    parser.add_argument("input_dirs", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = merge_countertrace_mini_runs(input_dirs=args.input_dirs, output_dir=args.output_dir)
    print(f"wrote {args.output_dir / 'math_summary.json'}")
    print(f"wrote {args.output_dir / 'math_traces.jsonl'}")
    print(f"wrote {args.output_dir / 'math_success_traces.jsonl'}")
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
