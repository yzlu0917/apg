from __future__ import annotations

import argparse
import json
from pathlib import Path

from civic_prm.blind_audit import render_blind_audit_report, score_blind_audit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score one or more blind-audit reviewer CSV files against the hidden answer key.")
    parser.add_argument("--answer-key", type=Path, required=True)
    parser.add_argument("--responses", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = score_blind_audit(args.answer_key, args.responses)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if args.markdown_output is not None:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_blind_audit_report(summary), encoding="utf-8")
    print(json.dumps(summary["pooled_summary"], indent=2))


if __name__ == "__main__":
    main()
