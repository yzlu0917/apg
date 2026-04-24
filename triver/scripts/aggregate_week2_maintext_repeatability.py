from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate multi-run main-text repeatability artifacts.")
    parser.add_argument(
        "--run",
        action="append",
        required=True,
        help="Run spec in the form label=/path/to/budget_eval_dir",
    )
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def _parse_run_spec(spec: str) -> tuple[str, Path]:
    if "=" not in spec:
        raise ValueError(f"Invalid --run spec: {spec}")
    label, raw_path = spec.split("=", 1)
    return label, Path(raw_path)


def _load_run_dir(run_label: str, run_dir: Path) -> pd.DataFrame:
    summary = json.loads((run_dir / "budget_eval_summary.json").read_text(encoding="utf-8"))
    domain_tag = str(summary["domain_tag"])

    sample = pd.read_csv(run_dir / "combined_sample_results_main.csv")
    overall = (
        sample.groupby("baseline", as_index=False)
        .agg(
            num_prefixes=("row_id", "count"),
            mean_budget_tokens=("budget_tokens", "mean"),
            oracle_action_accuracy=("oracle_action_correct", "mean"),
            mean_action_regret=("action_regret", "mean"),
            std_action_regret=("action_regret", "std"),
            mean_chosen_utility=("chosen_utility", "mean"),
            mean_oracle_utility=("oracle_utility", "mean"),
        )
    )

    revision_harm = pd.read_csv(run_dir / "revision_harm_summary.csv")
    calibration = pd.read_csv(run_dir / "compute_value_calibration_summary.csv")

    merged = overall.merge(
        revision_harm[
            [
                "baseline",
                "num_revise_predictions",
                "revise_rate",
                "num_harmful_revises",
                "revision_harm_rate_overall",
                "revision_harm_rate_among_revise",
                "num_helpful_revises",
                "helpful_revise_rate_among_revise",
                "mean_revision_harm_gap",
            ]
        ],
        on="baseline",
        how="left",
        validate="one_to_one",
    ).merge(
        calibration[
            [
                "baseline",
                "proxy_type",
                "proxy_is_utility_scale",
                "spearman_rho",
                "pearson_r",
                "utility_scale_rmse",
            ]
        ],
        on="baseline",
        how="left",
        validate="one_to_one",
    )
    merged["run_label"] = run_label
    merged["domain_tag"] = domain_tag
    return merged


def _build_summary(per_run: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        per_run.groupby(["domain_tag", "baseline"], as_index=False)
        .agg(
            num_runs=("run_label", "count"),
            mean_action_regret_mean=("mean_action_regret", "mean"),
            mean_action_regret_std=("mean_action_regret", "std"),
            oracle_action_accuracy_mean=("oracle_action_accuracy", "mean"),
            oracle_action_accuracy_std=("oracle_action_accuracy", "std"),
            revision_harm_rate_overall_mean=("revision_harm_rate_overall", "mean"),
            revision_harm_rate_overall_std=("revision_harm_rate_overall", "std"),
            revise_rate_mean=("revise_rate", "mean"),
            revise_rate_std=("revise_rate", "std"),
            calibration_spearman_mean=("spearman_rho", "mean"),
            calibration_spearman_std=("spearman_rho", "std"),
            utility_scale_rmse_mean=("utility_scale_rmse", "mean"),
            utility_scale_rmse_std=("utility_scale_rmse", "std"),
        )
        .sort_values(["domain_tag", "mean_action_regret_mean", "baseline"], ascending=[True, True, True])
        .reset_index(drop=True)
    )
    return grouped


def _build_best_by_run(per_run: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (domain_tag, run_label), group in per_run.groupby(["domain_tag", "run_label"], sort=True):
        ordered = group.sort_values(
            ["mean_action_regret", "oracle_action_accuracy", "baseline"],
            ascending=[True, False, True],
        ).reset_index(drop=True)
        best = ordered.iloc[0].copy()
        ties = group.loc[group["mean_action_regret"] == best["mean_action_regret"], "baseline"].tolist()
        rows.append(
            {
                "domain_tag": domain_tag,
                "run_label": run_label,
                "best_baseline": best["baseline"],
                "tied_baselines": "|".join(sorted(ties)),
                "mean_action_regret": best["mean_action_regret"],
                "oracle_action_accuracy": best["oracle_action_accuracy"],
                "revision_harm_rate_overall": best.get("revision_harm_rate_overall", np.nan),
                "calibration_spearman": best.get("spearman_rho", np.nan),
            }
        )
    return pd.DataFrame(rows).sort_values(["domain_tag", "run_label"]).reset_index(drop=True)


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    per_run_frames = []
    run_specs = []
    for spec in args.run:
        run_label, run_dir = _parse_run_spec(spec)
        per_run_frames.append(_load_run_dir(run_label, run_dir))
        run_specs.append({"run_label": run_label, "run_dir": str(run_dir)})

    per_run = pd.concat(per_run_frames, ignore_index=True, sort=False)
    per_run = per_run.sort_values(["domain_tag", "run_label", "mean_action_regret", "baseline"]).reset_index(drop=True)
    per_run.to_csv(output_dir / "within_domain_repeatability_per_run.csv", index=False)

    summary = _build_summary(per_run)
    summary.to_csv(output_dir / "within_domain_repeatability_summary.csv", index=False)

    best_by_run = _build_best_by_run(per_run)
    best_by_run.to_csv(output_dir / "within_domain_repeatability_best_by_run.csv", index=False)

    win_counts = (
        best_by_run.groupby(["domain_tag", "best_baseline"], as_index=False)
        .size()
        .rename(columns={"size": "num_run_wins"})
        .sort_values(["domain_tag", "num_run_wins", "best_baseline"], ascending=[True, False, True])
        .reset_index(drop=True)
    )
    win_counts.to_csv(output_dir / "within_domain_repeatability_win_counts.csv", index=False)

    payload = {
        "runs": run_specs,
        "num_per_run_rows": int(len(per_run)),
        "num_summary_rows": int(len(summary)),
        "num_best_rows": int(len(best_by_run)),
    }
    with (output_dir / "within_domain_repeatability_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)

    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
