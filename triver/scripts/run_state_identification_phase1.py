from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from triver.baselines.week2 import attach_embeddings, load_oracle_frame
from triver.factorized.week2 import infer_embedding_columns, run_factorized_cv_with_samples


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run state-identification phase-1 diagnostics.")
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--embedding-npz", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--selected-predicted-baseline", required=True)
    parser.add_argument("--domain-tag", default="")
    parser.add_argument("--include-ambiguous", action="store_true")
    parser.add_argument("--group-column", default="sample_id")
    parser.add_argument("--n-splits", type=int, default=5)
    parser.add_argument("--state-mode", choices=["legacy", "s_proxy"], default="s_proxy")
    parser.add_argument("--state-head-model", choices=["linear", "pca_ridge", "pca_enet", "rf"], default="linear")
    parser.add_argument("--value-head-model", default="ridge")
    parser.add_argument(
        "--predicted-train-filter-mode",
        choices=["all", "high_determinacy"],
        default="all",
    )
    parser.add_argument("--high-det-gap-quantile", type=float, default=0.5)
    parser.add_argument("--teacher-distill-mode", choices=["none", "exact_oof_scores"], default="none")
    return parser.parse_args()


def _safe_corr(x: pd.Series, y: pd.Series, method: str) -> float:
    if len(x) < 2 or x.nunique(dropna=True) < 2 or y.nunique(dropna=True) < 2:
        return float("nan")
    return float(x.corr(y, method=method))


def summarize_overall(sample_results: pd.DataFrame) -> pd.DataFrame:
    summary = (
        sample_results.groupby("baseline", as_index=False)
        .agg(
            num_prefixes=("row_id", "count"),
            oracle_action_accuracy=("oracle_action_correct", "mean"),
            mean_action_regret=("action_regret", "mean"),
            std_action_regret=("action_regret", "std"),
            mean_chosen_utility=("chosen_utility", "mean"),
            mean_oracle_utility=("oracle_utility", "mean"),
            predicted_train_filter_mode=("predicted_train_filter_mode", "first"),
            train_filter_gap_threshold=("train_filter_gap_threshold", "mean"),
            train_filter_num_before=("train_filter_num_before", "mean"),
            train_filter_num_after=("train_filter_num_after", "mean"),
        )
        .sort_values("mean_action_regret", ascending=True)
        .reset_index(drop=True)
    )
    return summary


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


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    frame = load_oracle_frame(args.input_csv, exclude_ambiguous=not args.include_ambiguous)
    frame, q_embedding_columns = attach_embeddings(frame, args.embedding_npz, column_prefix="qemb")
    frame, s_embedding_columns = attach_embeddings(frame, args.embedding_npz, column_prefix="semb")
    q_embedding_columns = infer_embedding_columns(frame, prefix="qemb_")
    s_embedding_columns = infer_embedding_columns(frame, prefix="semb_")

    cv_results, sample_results = run_factorized_cv_with_samples(
        frame=frame,
        q_embedding_columns=q_embedding_columns,
        s_embedding_columns=s_embedding_columns,
        group_column=args.group_column,
        n_splits=args.n_splits,
        state_mode=args.state_mode,
        state_head_model=args.state_head_model,
        value_head_model=args.value_head_model,
        predicted_baselines=[args.selected_predicted_baseline],
        predicted_train_filter_mode=args.predicted_train_filter_mode,
        high_det_gap_quantile=args.high_det_gap_quantile,
        teacher_distill_mode=args.teacher_distill_mode,
    )
    overall = summarize_overall(sample_results)
    revision_harm = summarize_revision_harm(sample_results)
    calibration = summarize_compute_value_calibration(sample_results)

    if args.domain_tag:
        for frame_ in (cv_results, sample_results, overall, revision_harm, calibration):
            frame_["domain_tag"] = args.domain_tag

    cv_results.to_csv(output_dir / "cv_results.csv", index=False)
    sample_results.to_csv(output_dir / "sample_results.csv", index=False)
    overall.to_csv(output_dir / "overall_summary.csv", index=False)
    revision_harm.to_csv(output_dir / "revision_harm_summary.csv", index=False)
    calibration.to_csv(output_dir / "compute_value_calibration_summary.csv", index=False)

    with (output_dir / "run_config.json").open("w", encoding="utf-8") as handle:
        json.dump(vars(args), handle, ensure_ascii=False, indent=2)

    print(overall.to_string(index=False))


if __name__ == "__main__":
    main()
