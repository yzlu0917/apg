from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate repeated cross-domain router summaries across seeds/runs."
    )
    parser.add_argument(
        "--summary",
        action="append",
        required=True,
        help="Summary spec in the form label=/path/to/router_summary.csv. Repeatable.",
    )
    parser.add_argument(
        "--output-csv",
        required=True,
        help="Path for the aggregated mean/std summary CSV.",
    )
    parser.add_argument(
        "--per-run-csv",
        required=True,
        help="Path for the concatenated per-run baseline table.",
    )
    return parser.parse_args()


def parse_summary_spec(spec: str) -> tuple[str, Path]:
    if "=" not in spec:
        raise ValueError(f"Invalid --summary spec {spec!r}; expected label=/path/to/file.csv")
    label, raw_path = spec.split("=", 1)
    label = label.strip()
    path = Path(raw_path).expanduser().resolve()
    if not label:
        raise ValueError(f"Invalid --summary spec {spec!r}; empty label")
    if not path.exists():
        raise FileNotFoundError(f"Summary file not found: {path}")
    return label, path


def load_summary(label: str, path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["experiment"] = label
    return frame


def build_aggregate(per_run: pd.DataFrame) -> pd.DataFrame:
    grouped = per_run.groupby(["env_conditioning", "baseline"], as_index=False)
    aggregate = grouped.agg(
        runs=("experiment", "nunique"),
        regret_mean=("mean_action_regret", "mean"),
        regret_std=("mean_action_regret", "std"),
        regret_min=("mean_action_regret", "min"),
        regret_max=("mean_action_regret", "max"),
        accuracy_mean=("oracle_action_accuracy", "mean"),
        accuracy_std=("oracle_action_accuracy", "std"),
        chosen_utility_mean=("mean_chosen_utility", "mean"),
        chosen_utility_std=("mean_chosen_utility", "std"),
    )
    aggregate["regret_std"] = aggregate["regret_std"].fillna(0.0)
    aggregate["accuracy_std"] = aggregate["accuracy_std"].fillna(0.0)
    aggregate["chosen_utility_std"] = aggregate["chosen_utility_std"].fillna(0.0)
    aggregate = aggregate.sort_values(
        by=["env_conditioning", "regret_mean", "baseline"],
        ascending=[True, True, True],
    ).reset_index(drop=True)
    return aggregate


def main() -> None:
    args = parse_args()
    frames = []
    for spec in args.summary:
        label, path = parse_summary_spec(spec)
        frames.append(load_summary(label, path))

    per_run = pd.concat(frames, ignore_index=True)
    per_run = per_run.sort_values(
        by=["env_conditioning", "baseline", "experiment"],
        ascending=[True, True, True],
    ).reset_index(drop=True)
    aggregate = build_aggregate(per_run)

    per_run_path = Path(args.per_run_csv)
    per_run_path.parent.mkdir(parents=True, exist_ok=True)
    aggregate_path = Path(args.output_csv)
    aggregate_path.parent.mkdir(parents=True, exist_ok=True)

    per_run.to_csv(per_run_path, index=False)
    aggregate.to_csv(aggregate_path, index=False)


if __name__ == "__main__":
    main()
