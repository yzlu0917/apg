from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate cross-domain Week-2 budget-axis artifacts.")
    parser.add_argument("--linear-dir", required=True)
    parser.add_argument("--arithmetic-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def load_domain_artifacts(
    run_dir: Path,
) -> tuple[str, str, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    with (run_dir / "budget_eval_summary.json").open("r", encoding="utf-8") as handle:
        summary = json.load(handle)
    domain_tag = str(summary.get("domain_tag", "")).strip() or run_dir.name
    selected_predicted_baseline = str(summary.get("selected_predicted_baseline", "")).strip()

    budget_main = pd.read_csv(run_dir / "budget_summary_main.csv")
    sample_results = pd.read_csv(run_dir / "combined_sample_results.csv")
    revision_harm = pd.read_csv(run_dir / "revision_harm_summary.csv")
    revision_harm_budget = pd.read_csv(run_dir / "revision_harm_at_budget.csv")
    calibration_summary = pd.read_csv(run_dir / "compute_value_calibration_summary.csv")
    calibration_bins = pd.read_csv(run_dir / "compute_value_calibration_bins.csv")
    budget_main["domain_tag"] = domain_tag
    sample_results["domain_tag"] = domain_tag
    revision_harm["domain_tag"] = domain_tag
    revision_harm_budget["domain_tag"] = domain_tag
    calibration_summary["domain_tag"] = domain_tag
    calibration_bins["domain_tag"] = domain_tag
    return (
        domain_tag,
        selected_predicted_baseline,
        budget_main,
        sample_results,
        revision_harm,
        revision_harm_budget,
        calibration_summary,
        calibration_bins,
    )


def build_domain_overall(sample_results: pd.DataFrame) -> pd.DataFrame:
    overall = (
        sample_results.groupby(["domain_tag", "baseline"], as_index=False)
        .agg(
            num_prefixes=("row_id", "count"),
            mean_budget_tokens=("budget_tokens", "mean"),
            oracle_action_accuracy=("oracle_action_correct", "mean"),
            mean_action_regret=("action_regret", "mean"),
            std_action_regret=("action_regret", "std"),
            mean_chosen_utility=("chosen_utility", "mean"),
            std_chosen_utility=("chosen_utility", "std"),
            mean_oracle_utility=("oracle_utility", "mean"),
        )
        .sort_values(["domain_tag", "mean_action_regret", "baseline"], ascending=[True, True, True])
        .reset_index(drop=True)
    )
    return overall


def build_domain_overall_main(sample_results: pd.DataFrame, selected_predicted_baseline: str) -> pd.DataFrame:
    main_baselines = [
        "ordered_scalar_mu",
        "learned_1d_linear",
        "direct_policy",
        "factorized_exact_state",
        selected_predicted_baseline,
    ]
    main = sample_results.loc[sample_results["baseline"].isin(main_baselines)].copy()
    main["baseline"] = main["baseline"].replace(
        {selected_predicted_baseline: "factorized_predicted_state_selected"}
    )
    overall_main = build_domain_overall(main)
    return overall_main


def build_budget_winners(budget_main: pd.DataFrame) -> pd.DataFrame:
    winner_rows = []
    grouped = budget_main.groupby(["domain_tag", "budget_tokens"], sort=True)
    for (domain_tag, budget_tokens), group in grouped:
        ordered = group.sort_values(
            ["mean_action_regret", "oracle_action_accuracy", "baseline"],
            ascending=[True, False, True],
        ).reset_index(drop=True)
        best = ordered.iloc[0].copy()
        best["best_baseline"] = best["baseline"]
        ties = group.loc[group["mean_action_regret"] == best["mean_action_regret"], "baseline"].tolist()
        best["tied_baselines"] = "|".join(sorted(ties))
        winner_rows.append(best)
    winners = pd.DataFrame(winner_rows)
    keep_columns = [
        "domain_tag",
        "budget_tokens",
        "best_baseline",
        "tied_baselines",
        "num_prefixes",
        "oracle_action_accuracy",
        "mean_action_regret",
        "mean_chosen_utility",
        "mean_oracle_utility",
    ]
    winners = winners[keep_columns].sort_values(["domain_tag", "budget_tokens"]).reset_index(drop=True)
    return winners


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    budget_frames = []
    sample_frames = []
    overall_main_frames = []
    revision_harm_frames = []
    revision_harm_budget_frames = []
    calibration_summary_frames = []
    calibration_bins_frames = []
    domains = []
    for run_dir in [Path(args.linear_dir), Path(args.arithmetic_dir)]:
        (
            domain_tag,
            selected_predicted_baseline,
            budget_main,
            sample_results,
            revision_harm,
            revision_harm_budget,
            calibration_summary,
            calibration_bins,
        ) = load_domain_artifacts(run_dir)
        domains.append(
            {
                "domain_tag": domain_tag,
                "run_dir": str(run_dir),
                "selected_predicted_baseline": selected_predicted_baseline,
            }
        )
        budget_frames.append(budget_main)
        sample_frames.append(sample_results)
        overall_main_frames.append(build_domain_overall_main(sample_results, selected_predicted_baseline))
        revision_harm_frames.append(revision_harm)
        revision_harm_budget_frames.append(revision_harm_budget)
        calibration_summary_frames.append(calibration_summary)
        calibration_bins_frames.append(calibration_bins)

    budget_comparison = pd.concat(budget_frames, ignore_index=True, sort=False)
    budget_comparison = budget_comparison.sort_values(
        ["domain_tag", "baseline", "budget_tokens"], ascending=[True, True, True]
    ).reset_index(drop=True)
    budget_comparison.to_csv(output_dir / "budget_axis_domain_comparison.csv", index=False)

    action_regret = budget_comparison[
        ["domain_tag", "baseline", "budget_tokens", "num_prefixes", "mean_action_regret", "std_action_regret"]
    ].copy()
    action_regret.to_csv(output_dir / "action_regret_at_budget_by_domain.csv", index=False)

    frontier = budget_comparison[
        [
            "domain_tag",
            "baseline",
            "budget_tokens",
            "num_prefixes",
            "oracle_action_accuracy",
            "mean_chosen_utility",
            "std_chosen_utility",
            "mean_oracle_utility",
        ]
    ].copy()
    frontier.to_csv(output_dir / "equal_token_frontier_by_domain.csv", index=False)

    all_samples = pd.concat(sample_frames, ignore_index=True, sort=False)
    domain_overall = build_domain_overall(all_samples)
    domain_overall.to_csv(output_dir / "budget_axis_domain_overall.csv", index=False)

    domain_overall_main = pd.concat(overall_main_frames, ignore_index=True, sort=False)
    domain_overall_main = domain_overall_main.sort_values(
        ["domain_tag", "mean_action_regret", "baseline"], ascending=[True, True, True]
    ).reset_index(drop=True)
    domain_overall_main.to_csv(output_dir / "budget_axis_domain_overall_main.csv", index=False)

    revision_harm_by_domain = pd.concat(revision_harm_frames, ignore_index=True, sort=False)
    revision_harm_by_domain = revision_harm_by_domain.sort_values(
        ["domain_tag", "revision_harm_rate_overall", "baseline"], ascending=[True, True, True]
    ).reset_index(drop=True)
    revision_harm_by_domain.to_csv(output_dir / "revision_harm_by_domain.csv", index=False)

    revision_harm_at_budget_by_domain = pd.concat(revision_harm_budget_frames, ignore_index=True, sort=False)
    revision_harm_at_budget_by_domain = revision_harm_at_budget_by_domain.sort_values(
        ["domain_tag", "baseline", "budget_tokens"], ascending=[True, True, True]
    ).reset_index(drop=True)
    revision_harm_at_budget_by_domain.to_csv(output_dir / "revision_harm_at_budget_by_domain.csv", index=False)

    calibration_summary_by_domain = pd.concat(calibration_summary_frames, ignore_index=True, sort=False)
    calibration_summary_by_domain = calibration_summary_by_domain.sort_values(
        ["domain_tag", "baseline"], ascending=[True, True]
    ).reset_index(drop=True)
    calibration_summary_by_domain.to_csv(output_dir / "compute_value_calibration_summary_by_domain.csv", index=False)

    calibration_bins_by_domain = pd.concat(calibration_bins_frames, ignore_index=True, sort=False)
    calibration_bins_by_domain = calibration_bins_by_domain.sort_values(
        ["domain_tag", "baseline", "calibration_bin"], ascending=[True, True, True]
    ).reset_index(drop=True)
    calibration_bins_by_domain.to_csv(output_dir / "compute_value_calibration_bins_by_domain.csv", index=False)

    budget_winners = build_budget_winners(budget_comparison)
    budget_winners.to_csv(output_dir / "budget_axis_domain_budget_winners.csv", index=False)

    summary_payload = {
        "domains": domains,
        "num_domain_budget_rows": int(len(budget_comparison)),
        "num_domain_overall_rows": int(len(domain_overall)),
        "num_domain_overall_main_rows": int(len(domain_overall_main)),
        "num_revision_harm_rows": int(len(revision_harm_by_domain)),
        "num_calibration_summary_rows": int(len(calibration_summary_by_domain)),
        "num_budget_winner_rows": int(len(budget_winners)),
    }
    with (output_dir / "budget_axis_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary_payload, handle, ensure_ascii=False, indent=2)

    print(domain_overall_main.to_string(index=False))


if __name__ == "__main__":
    main()
