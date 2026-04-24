from __future__ import annotations

import argparse
import json
from pathlib import Path

from cnt_research.math.stage_b import rescore_stage_b_rollout_records


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rescore an existing Stage B rollout records file with the current verdict logic.")
    parser.add_argument("--records-path", type=Path, required=True)
    parser.add_argument(
        "--data-path",
        type=Path,
        default=ROOT / "data" / "gsm8k" / "test.jsonl",
    )
    parser.add_argument("--styles", nargs="+", default=None)
    parser.add_argument("--stability-sigma", type=float, default=0.25)
    parser.add_argument("--summary-path", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = rescore_stage_b_rollout_records(
        records_path=args.records_path,
        data_path=args.data_path,
        output_dir=args.output_dir,
        stability_sigma=args.stability_sigma,
        styles=tuple(args.styles) if args.styles else None,
        summary_path=args.summary_path,
    )
    print(json.dumps(result["summary"], indent=2))
    print(f"wrote {args.output_dir / 'stage_b_rollout_summary.json'}")
    print(f"wrote {args.output_dir / 'stage_b_rollout_records.jsonl'}")


if __name__ == "__main__":
    main()
