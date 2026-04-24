from __future__ import annotations

import argparse
import json
from pathlib import Path

from triver.baselines.week2 import (
    DEFAULT_FEATURE_COLUMNS,
    attach_embeddings,
    load_oracle_frame,
    run_group_cv,
    summarize_cv_results,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run TriVer Week-2 baseline comparisons.")
    parser.add_argument("--input-csv", required=True, help="Oracle record CSV from Week-1 pipeline.")
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory to save CV results and summary.",
    )
    parser.add_argument(
        "--embedding-npz",
        default="",
        help="Optional prefix hidden-state embeddings produced by extract_prefix_hidden_states.py.",
    )
    parser.add_argument(
        "--include-ambiguous",
        action="store_true",
        help="Include ambiguous prefixes. Default is to exclude them.",
    )
    parser.add_argument("--group-column", default="sample_id")
    parser.add_argument("--n-splits", type=int, default=5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    frame = load_oracle_frame(args.input_csv, exclude_ambiguous=not args.include_ambiguous)
    feature_columns = list(DEFAULT_FEATURE_COLUMNS)
    baseline_suffix = ""
    if args.embedding_npz:
        frame, embedding_columns = attach_embeddings(frame, args.embedding_npz)
        feature_columns.extend(embedding_columns)
        baseline_suffix = "_repr"
    results = run_group_cv(
        frame=frame,
        feature_columns=feature_columns,
        group_column=args.group_column,
        n_splits=args.n_splits,
        baseline_suffix=baseline_suffix,
    )
    summary = summarize_cv_results(results)

    results.to_csv(output_dir / "cv_results.csv", index=False)
    summary.to_csv(output_dir / "summary.csv", index=False)
    with (output_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary.to_dict(orient="records"), handle, ensure_ascii=False, indent=2)

    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
