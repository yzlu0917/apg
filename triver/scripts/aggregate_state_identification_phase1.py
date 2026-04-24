from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate state-identification phase-1 runs.")
    parser.add_argument("--run-dir", action="append", required=True, help="Phase-1 run directory. Repeat this flag.")
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    overall_frames = []
    revision_frames = []
    calibration_frames = []
    configs = []
    for run_dir_text in args.run_dir:
        run_dir = Path(run_dir_text)
        with (run_dir / "run_config.json").open("r", encoding="utf-8") as handle:
            config = json.load(handle)
        configs.append(config)
        overall = pd.read_csv(run_dir / "overall_summary.csv")
        revision = pd.read_csv(run_dir / "revision_harm_summary.csv")
        calibration = pd.read_csv(run_dir / "compute_value_calibration_summary.csv")
        for frame in (overall, revision, calibration):
            frame["run_name"] = run_dir.name
            frame["domain_tag"] = config.get("domain_tag", "")
            frame["value_head_model"] = config.get("value_head_model", "")
            frame["predicted_train_filter_mode"] = config.get("predicted_train_filter_mode", "all")
            frame["teacher_distill_mode"] = config.get("teacher_distill_mode", "none")
            frame["selected_predicted_baseline"] = config.get("selected_predicted_baseline", "")
        overall_frames.append(overall)
        revision_frames.append(revision)
        calibration_frames.append(calibration)

    overall_frame = pd.concat(overall_frames, ignore_index=True)
    revision_frame = pd.concat(revision_frames, ignore_index=True)
    calibration_frame = pd.concat(calibration_frames, ignore_index=True)

    predicted_overall = overall_frame.loc[overall_frame["baseline"] != "factorized_exact_state"].copy()
    predicted_revision = revision_frame.loc[revision_frame["baseline"] != "factorized_exact_state"].copy()
    predicted_calibration = calibration_frame.loc[calibration_frame["baseline"] != "factorized_exact_state"].copy()

    overall_domain_summary = (
        predicted_overall.groupby(
            ["domain_tag", "value_head_model", "predicted_train_filter_mode", "teacher_distill_mode", "baseline"],
            as_index=False,
        )
        .agg(
            mean_action_regret=("mean_action_regret", "mean"),
            oracle_action_accuracy=("oracle_action_accuracy", "mean"),
            mean_chosen_utility=("mean_chosen_utility", "mean"),
            train_filter_gap_threshold=("train_filter_gap_threshold", "mean"),
            train_filter_num_after=("train_filter_num_after", "mean"),
            num_runs=("run_name", "count"),
        )
        .sort_values(["domain_tag", "mean_action_regret"], ascending=[True, True])
        .reset_index(drop=True)
    )
    revision_domain_summary = (
        predicted_revision.groupby(
            ["domain_tag", "value_head_model", "predicted_train_filter_mode", "teacher_distill_mode", "baseline"],
            as_index=False,
        )
        .agg(
            revision_harm_rate_overall=("revision_harm_rate_overall", "mean"),
            revise_rate=("revise_rate", "mean"),
            mean_revision_harm_gap=("mean_revision_harm_gap", "mean"),
            num_runs=("run_name", "count"),
        )
        .sort_values(["domain_tag", "revision_harm_rate_overall"], ascending=[True, True])
        .reset_index(drop=True)
    )
    calibration_domain_summary = (
        predicted_calibration.groupby(
            ["domain_tag", "value_head_model", "predicted_train_filter_mode", "teacher_distill_mode", "baseline"],
            as_index=False,
        )
        .agg(
            spearman_rho=("spearman_rho", "mean"),
            utility_scale_rmse=("utility_scale_rmse", "mean"),
            num_runs=("run_name", "count"),
        )
        .sort_values(["domain_tag", "spearman_rho"], ascending=[True, False])
        .reset_index(drop=True)
    )

    overall_frame.to_csv(output_dir / "overall_per_run.csv", index=False)
    revision_frame.to_csv(output_dir / "revision_harm_per_run.csv", index=False)
    calibration_frame.to_csv(output_dir / "compute_value_calibration_per_run.csv", index=False)
    overall_domain_summary.to_csv(output_dir / "overall_by_domain.csv", index=False)
    revision_domain_summary.to_csv(output_dir / "revision_harm_by_domain.csv", index=False)
    calibration_domain_summary.to_csv(output_dir / "compute_value_calibration_by_domain.csv", index=False)

    with (output_dir / "run_manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(configs, handle, ensure_ascii=False, indent=2)

    print(overall_domain_summary.to_string(index=False))


if __name__ == "__main__":
    main()
