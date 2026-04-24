from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from triver.baselines.week2 import (
    DEFAULT_FEATURE_COLUMNS,
    attach_embeddings,
    load_oracle_frame,
    run_group_cv_with_samples,
)
from triver.factorized.week2 import infer_embedding_columns, run_factorized_cv_with_samples


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute Week-2 budget-axis evaluation artifacts.")
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--embedding-npz", required=True, help="Embedding NPZ for factorized controller evaluation.")
    parser.add_argument("--include-ambiguous", action="store_true")
    parser.add_argument("--group-column", default="sample_id")
    parser.add_argument("--n-splits", type=int, default=5)
    parser.add_argument("--state-mode", choices=["legacy", "s_proxy"], default="s_proxy")
    parser.add_argument("--state-head-model", choices=["linear", "pca_ridge", "pca_enet", "rf"], default="linear")
    parser.add_argument("--value-head-model", default="ridge")
    parser.add_argument(
        "--selected-predicted-baseline",
        default="factorized_predicted_state_train_exact_plus_oof",
        help="Predicted-state factorized baseline to surface in the main frontier tables.",
    )
    parser.add_argument(
        "--domain-tag",
        default="",
        help="Optional tag written into outputs to distinguish linear/arithmetic runs.",
    )
    parser.add_argument(
        "--maintext-only",
        action="store_true",
        help="Only evaluate the exact-state upper bound and the selected deployable predicted-state factorized baseline.",
    )
    return parser.parse_args()


def summarize_by_budget(sample_results: pd.DataFrame) -> pd.DataFrame:
    summary = (
        sample_results.groupby(["baseline", "budget_tokens"], as_index=False)
        .agg(
            num_prefixes=("row_id", "count"),
            oracle_action_accuracy=("oracle_action_correct", "mean"),
            mean_action_regret=("action_regret", "mean"),
            std_action_regret=("action_regret", "std"),
            mean_chosen_utility=("chosen_utility", "mean"),
            std_chosen_utility=("chosen_utility", "std"),
            mean_oracle_utility=("oracle_utility", "mean"),
        )
        .sort_values(["baseline", "budget_tokens"], ascending=[True, True])
        .reset_index(drop=True)
    )
    return summary


def select_main_samples(sample_results: pd.DataFrame, selected_predicted_baseline: str) -> pd.DataFrame:
    main_baselines = [
        "ordered_scalar_mu",
        "learned_1d_linear",
        "direct_policy",
        "factorized_exact_state",
        selected_predicted_baseline,
    ]
    main_samples = sample_results.loc[sample_results["baseline"].isin(main_baselines)].copy()
    main_samples["baseline"] = main_samples["baseline"].replace(
        {selected_predicted_baseline: "factorized_predicted_state_selected"}
    )
    return main_samples.reset_index(drop=True)


def _summarize_revision_harm_group(group: pd.DataFrame) -> dict[str, float | int]:
    revise_mask = group["predicted_action"] == "revise_1"
    harmful_mask = revise_mask & (group["oracle_action"] == "continue")
    helpful_mask = revise_mask & (group["oracle_action"] == "revise_1")
    num_prefixes = int(len(group))
    num_revise = int(revise_mask.sum())
    num_harmful = int(harmful_mask.sum())
    num_helpful = int(helpful_mask.sum())
    harm_gap = (
        (group.loc[harmful_mask, "continue_utility"] - group.loc[harmful_mask, "revise_utility"]).to_numpy(dtype=float)
        if num_harmful > 0
        else np.array([], dtype=float)
    )
    return {
        "num_prefixes": num_prefixes,
        "num_revise_predictions": num_revise,
        "revise_rate": float(num_revise / num_prefixes) if num_prefixes > 0 else np.nan,
        "num_harmful_revises": num_harmful,
        "revision_harm_rate_overall": float(num_harmful / num_prefixes) if num_prefixes > 0 else np.nan,
        "revision_harm_rate_among_revise": float(num_harmful / num_revise) if num_revise > 0 else np.nan,
        "num_helpful_revises": num_helpful,
        "helpful_revise_rate_among_revise": float(num_helpful / num_revise) if num_revise > 0 else np.nan,
        "mean_revision_harm_gap": float(harm_gap.mean()) if harm_gap.size else np.nan,
    }


def summarize_revision_harm(sample_results: pd.DataFrame) -> pd.DataFrame:
    records = []
    for baseline, group in sample_results.groupby("baseline", sort=True):
        row = {"baseline": baseline}
        row.update(_summarize_revision_harm_group(group))
        records.append(row)
    return pd.DataFrame(records).sort_values("revision_harm_rate_overall", ascending=True).reset_index(drop=True)


def summarize_revision_harm_by_budget(sample_results: pd.DataFrame) -> pd.DataFrame:
    records = []
    for (baseline, budget_tokens), group in sample_results.groupby(["baseline", "budget_tokens"], sort=True):
        row = {"baseline": baseline, "budget_tokens": budget_tokens}
        row.update(_summarize_revision_harm_group(group))
        records.append(row)
    return pd.DataFrame(records).sort_values(["baseline", "budget_tokens"]).reset_index(drop=True)


def _safe_corr(x: pd.Series, y: pd.Series, method: str) -> float:
    if len(x) < 2 or x.nunique(dropna=True) < 2 or y.nunique(dropna=True) < 2:
        return float("nan")
    return float(x.corr(y, method=method))


def summarize_compute_value_calibration(sample_results: pd.DataFrame) -> pd.DataFrame:
    frame = sample_results.copy()
    frame = frame.loc[frame["predicted_proxy_value"].notna()].copy()
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "baseline",
                "proxy_type",
                "proxy_is_utility_scale",
                "num_prefixes",
                "mean_predicted_proxy",
                "mean_true_compute_value",
                "spearman_rho",
                "pearson_r",
                "utility_scale_rmse",
            ]
        )
    frame["true_compute_value"] = np.maximum(
        frame["continue_utility"].to_numpy(dtype=float),
        frame["revise_utility"].to_numpy(dtype=float),
    ) - frame["abstain_utility"].to_numpy(dtype=float)

    records = []
    for baseline, group in frame.groupby("baseline", sort=True):
        predicted = group["predicted_proxy_value"].astype(float)
        true_value = group["true_compute_value"].astype(float)
        proxy_type = group["predicted_proxy_type"].mode().iloc[0] if group["predicted_proxy_type"].notna().any() else ""
        proxy_is_utility_scale = bool(group["predicted_proxy_is_utility_scale"].fillna(0).astype(int).max())
        rmse = (
            float(np.sqrt(np.mean(np.square(predicted.to_numpy(dtype=float) - true_value.to_numpy(dtype=float)))))
            if proxy_is_utility_scale
            else np.nan
        )
        records.append(
            {
                "baseline": baseline,
                "proxy_type": proxy_type,
                "proxy_is_utility_scale": int(proxy_is_utility_scale),
                "num_prefixes": int(len(group)),
                "mean_predicted_proxy": float(predicted.mean()),
                "mean_true_compute_value": float(true_value.mean()),
                "spearman_rho": _safe_corr(predicted, true_value, method="spearman"),
                "pearson_r": _safe_corr(predicted, true_value, method="pearson"),
                "utility_scale_rmse": rmse,
            }
        )
    return pd.DataFrame(records).sort_values(["baseline"]).reset_index(drop=True)


def build_compute_value_calibration_bins(sample_results: pd.DataFrame, num_bins: int = 5) -> pd.DataFrame:
    frame = sample_results.copy()
    frame = frame.loc[frame["predicted_proxy_value"].notna()].copy()
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "baseline",
                "calibration_bin",
                "num_prefixes",
                "mean_predicted_proxy",
                "mean_true_compute_value",
                "mean_action_regret",
            ]
        )
    frame["true_compute_value"] = np.maximum(
        frame["continue_utility"].to_numpy(dtype=float),
        frame["revise_utility"].to_numpy(dtype=float),
    ) - frame["abstain_utility"].to_numpy(dtype=float)

    records = []
    for baseline, group in frame.groupby("baseline", sort=True):
        proxy = group["predicted_proxy_value"].astype(float)
        effective_bins = int(min(num_bins, max(proxy.nunique(dropna=True), 1)))
        if effective_bins < 2:
            bin_codes = pd.Series(np.zeros(len(group), dtype=int), index=group.index)
        else:
            bin_codes = pd.qcut(proxy.rank(method="first"), q=effective_bins, labels=False, duplicates="drop")
        grouped = group.assign(calibration_bin=bin_codes.astype(int)).groupby("calibration_bin", sort=True)
        for calibration_bin, bin_group in grouped:
            records.append(
                {
                    "baseline": baseline,
                    "calibration_bin": int(calibration_bin),
                    "num_prefixes": int(len(bin_group)),
                    "mean_predicted_proxy": float(bin_group["predicted_proxy_value"].mean()),
                    "mean_true_compute_value": float(bin_group["true_compute_value"].mean()),
                    "mean_action_regret": float(bin_group["action_regret"].mean()),
                }
            )
    return pd.DataFrame(records).sort_values(["baseline", "calibration_bin"]).reset_index(drop=True)


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    frame = load_oracle_frame(args.input_csv, exclude_ambiguous=not args.include_ambiguous)

    baseline_results, baseline_samples = run_group_cv_with_samples(
        frame=frame,
        feature_columns=list(DEFAULT_FEATURE_COLUMNS),
        group_column=args.group_column,
        n_splits=args.n_splits,
    )

    factorized_frame, q_embedding_columns = attach_embeddings(frame, args.embedding_npz, column_prefix="qemb")
    factorized_frame, s_embedding_columns = attach_embeddings(
        factorized_frame, args.embedding_npz, column_prefix="semb"
    )
    q_embedding_columns = infer_embedding_columns(factorized_frame, prefix="qemb_")
    s_embedding_columns = infer_embedding_columns(factorized_frame, prefix="semb_")
    factorized_results, factorized_samples = run_factorized_cv_with_samples(
        frame=factorized_frame,
        q_embedding_columns=q_embedding_columns,
        s_embedding_columns=s_embedding_columns,
        group_column=args.group_column,
        n_splits=args.n_splits,
        state_mode=args.state_mode,
        state_head_model=args.state_head_model,
        value_head_model=args.value_head_model,
        predicted_baselines=[args.selected_predicted_baseline] if args.maintext_only else None,
    )

    baseline_results.to_csv(output_dir / "baseline_cv_results.csv", index=False)
    baseline_samples.to_csv(output_dir / "baseline_sample_results.csv", index=False)
    factorized_results.to_csv(output_dir / "factorized_cv_results.csv", index=False)
    factorized_samples.to_csv(output_dir / "factorized_sample_results.csv", index=False)

    all_results = pd.concat([baseline_results, factorized_results], ignore_index=True, sort=False)
    all_samples = pd.concat([baseline_samples, factorized_samples], ignore_index=True, sort=False)
    if args.domain_tag:
        all_results["domain_tag"] = args.domain_tag
        all_samples["domain_tag"] = args.domain_tag
    all_results.to_csv(output_dir / "combined_cv_results.csv", index=False)
    all_samples.to_csv(output_dir / "combined_sample_results.csv", index=False)

    main_samples = select_main_samples(all_samples, args.selected_predicted_baseline)
    if args.domain_tag:
        main_samples["domain_tag"] = args.domain_tag
    main_samples.to_csv(output_dir / "combined_sample_results_main.csv", index=False)

    budget_summary = summarize_by_budget(all_samples)
    budget_summary.to_csv(output_dir / "budget_summary_all.csv", index=False)

    main_baselines = [
        "ordered_scalar_mu",
        "learned_1d_linear",
        "direct_policy",
        "factorized_exact_state",
        args.selected_predicted_baseline,
    ]
    main_budget = budget_summary.loc[budget_summary["baseline"].isin(main_baselines)].copy()
    main_budget["baseline"] = main_budget["baseline"].replace(
        {args.selected_predicted_baseline: "factorized_predicted_state_selected"}
    )
    main_budget = main_budget.sort_values(["baseline", "budget_tokens"], ascending=[True, True]).reset_index(drop=True)
    main_budget.to_csv(output_dir / "budget_summary_main.csv", index=False)

    action_regret = main_budget[
        ["baseline", "budget_tokens", "num_prefixes", "mean_action_regret", "std_action_regret"]
    ].copy()
    action_regret.to_csv(output_dir / "action_regret_at_budget.csv", index=False)

    frontier = main_budget[
        [
            "baseline",
            "budget_tokens",
            "num_prefixes",
            "oracle_action_accuracy",
            "mean_chosen_utility",
            "std_chosen_utility",
            "mean_oracle_utility",
        ]
    ].copy()
    frontier.to_csv(output_dir / "equal_token_frontier.csv", index=False)

    revision_harm_summary = summarize_revision_harm(main_samples)
    revision_harm_summary.to_csv(output_dir / "revision_harm_summary.csv", index=False)

    revision_harm_by_budget = summarize_revision_harm_by_budget(main_samples)
    revision_harm_by_budget.to_csv(output_dir / "revision_harm_at_budget.csv", index=False)

    compute_value_calibration = summarize_compute_value_calibration(main_samples)
    compute_value_calibration.to_csv(output_dir / "compute_value_calibration_summary.csv", index=False)

    compute_value_calibration_bins = build_compute_value_calibration_bins(main_samples)
    compute_value_calibration_bins.to_csv(output_dir / "compute_value_calibration_bins.csv", index=False)

    with (output_dir / "run_config.json").open("w", encoding="utf-8") as handle:
        json.dump(vars(args), handle, ensure_ascii=False, indent=2)

    summary_payload = {
        "domain_tag": args.domain_tag,
        "selected_predicted_baseline": args.selected_predicted_baseline,
        "baselines_in_main_budget": sorted(main_budget["baseline"].unique().tolist()),
        "num_budget_rows": int(len(main_budget)),
        "num_main_sample_rows": int(len(main_samples)),
    }
    with (output_dir / "budget_eval_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary_payload, handle, ensure_ascii=False, indent=2)

    print(main_budget.to_string(index=False))


if __name__ == "__main__":
    main()
