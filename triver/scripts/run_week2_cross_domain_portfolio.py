from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from sklearn.model_selection import GroupKFold

from triver.baselines.week2 import attach_embeddings, evaluate_policy, load_oracle_frame
from triver.factorized.week2 import (
    fit_conditional_lowrank_pairwise_error_calibrated_bundle,
    fit_joint_pairwise_gate,
    infer_embedding_columns,
    prepare_factorized_split_states,
    predict_actions,
    run_factorized_cv,
    summarize_factorized_results,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run pooled shared-vs-specialist Week-2 factorized experiment.")
    parser.add_argument("--arithmetic-input-csv", required=True)
    parser.add_argument("--arithmetic-embedding-npz", required=True)
    parser.add_argument("--linear-input-csv", required=True)
    parser.add_argument("--linear-embedding-npz", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--group-column", default="sample_id")
    parser.add_argument("--n-splits", type=int, default=5)
    parser.add_argument("--include-env-feature", action="store_true")
    parser.add_argument("--state-mode", choices=["legacy", "s_proxy"], default="s_proxy")
    parser.add_argument("--state-head-model", choices=["linear", "pca_ridge", "pca_enet", "rf"], default="pca_enet")
    parser.add_argument(
        "--shared-value-head-model",
        default="uncertainty_conditional_lowrank_heteroscedastic_interaction",
        choices=[
            "uncertainty_conditional_lowrank_heteroscedastic_interaction",
            "conditional_lowrank_pairwise_error_calibrated",
            "conditional_lowrank_capped_pairwise_error_calibrated",
            "conditional_lowrank_banded_pairwise_error_calibrated",
            "conditional_lowrank_clustered_pairwise_error_calibrated",
            "joint_pairwise_gate",
        ],
    )
    parser.add_argument(
        "--linear-specialist-model",
        default="joint_pairwise_gate",
        choices=["joint_pairwise_gate"],
    )
    parser.add_argument(
        "--arithmetic-specialist-model",
        default="conditional_lowrank_pairwise_error_calibrated",
        choices=["conditional_lowrank_pairwise_error_calibrated"],
    )
    return parser.parse_args()


def _load_domain_frame(
    input_csv: str,
    embedding_npz: str,
    domain_name: str,
    group_column: str,
    include_env_feature: bool,
) -> tuple[pd.DataFrame, list[str], list[str]]:
    frame = load_oracle_frame(input_csv, exclude_ambiguous=True)
    frame[group_column] = frame[group_column].astype(str).map(lambda value: f"{domain_name}:{value}")
    frame["env"] = domain_name
    if include_env_feature:
        frame["env_is_linear"] = 1.0 if domain_name == "linear_equations" else 0.0
    frame, q_embedding_columns = attach_embeddings(frame, embedding_npz, column_prefix="qemb")
    frame, s_embedding_columns = attach_embeddings(frame, embedding_npz, column_prefix="semb")
    q_embedding_columns = infer_embedding_columns(frame, prefix="qemb_")
    s_embedding_columns = infer_embedding_columns(frame, prefix="semb_")
    return frame, q_embedding_columns, s_embedding_columns


def _specialist_predictions(
    train_frame: pd.DataFrame,
    test_frame: pd.DataFrame,
    q_embedding_columns: list[str],
    s_embedding_columns: list[str],
    state_mode: str,
    state_head_model: str,
    group_column: str,
    env_name: str,
    specialist_model: str,
) -> tuple[list[str], list[str]]:
    split = prepare_factorized_split_states(
        train_frame=train_frame,
        test_frame=test_frame,
        q_embedding_columns=q_embedding_columns,
        s_embedding_columns=s_embedding_columns,
        state_mode=state_mode,
        state_head_model=state_head_model,
        value_head_model=specialist_model,
        group_column=group_column,
    )

    if env_name == "linear_equations" and specialist_model == "joint_pairwise_gate":
        bundle = fit_joint_pairwise_gate(
            train_exact_state=split["train_exact_state"],
            train_predicted_state=split["train_state"],
            calibration_state=split["train_oof_state"],
            state_mode=state_mode,
        )
        exact_actions = predict_actions(
            bundle.regressors["exact_bundle"],
            split["test_exact_state"],
            bundle.metadata["exact_feature_columns"],
        )
        predicted_actions = predict_actions(
            bundle,
            split["test_state"],
            bundle.metadata["predicted_feature_columns"],
        )
        return exact_actions, predicted_actions

    if env_name == "arithmetic" and specialist_model == "conditional_lowrank_pairwise_error_calibrated":
        bundle = fit_conditional_lowrank_pairwise_error_calibrated_bundle(
            train_exact_state=split["train_exact_state"],
            calibration_state=split["train_oof_state"],
            state_mode=state_mode,
        )
        exact_actions = predict_actions(
            bundle.regressors["base_bundle"],
            split["test_exact_state"],
            bundle.metadata["base_feature_columns"],
        )
        predicted_actions = predict_actions(
            bundle,
            split["test_state"],
            bundle.metadata["risk_feature_columns"],
        )
        return exact_actions, predicted_actions

    raise ValueError(f"Unsupported specialist configuration: {env_name=} {specialist_model=}")


def run_specialist_portfolio_cv(
    merged_frame: pd.DataFrame,
    q_embedding_columns: list[str],
    s_embedding_columns: list[str],
    group_column: str,
    n_splits: int,
    state_mode: str,
    state_head_model: str,
    arithmetic_specialist_model: str,
    linear_specialist_model: str,
) -> pd.DataFrame:
    unique_groups = merged_frame[group_column].nunique()
    effective_splits = min(n_splits, unique_groups)
    if effective_splits < 2:
        raise ValueError("Need at least 2 groups for cross-validation")

    splitter = GroupKFold(n_splits=effective_splits)
    records: list[dict[str, float | int | str]] = []
    for fold_index, (train_index, test_index) in enumerate(
        splitter.split(merged_frame, groups=merged_frame[group_column]),
        start=1,
    ):
        train_frame = merged_frame.iloc[train_index].reset_index(drop=True)
        test_frame = merged_frame.iloc[test_index].reset_index(drop=True)

        exact_actions_all: list[str] = []
        predicted_actions_all: list[str] = []
        ordered_test_parts: list[pd.DataFrame] = []
        for env_name, specialist_model in [
            ("arithmetic", arithmetic_specialist_model),
            ("linear_equations", linear_specialist_model),
        ]:
            train_env = train_frame.loc[train_frame["env"] == env_name].reset_index(drop=True)
            test_env = test_frame.loc[test_frame["env"] == env_name].reset_index(drop=True)
            if len(test_env) == 0:
                continue
            exact_actions, predicted_actions = _specialist_predictions(
                train_frame=train_env,
                test_frame=test_env,
                q_embedding_columns=q_embedding_columns,
                s_embedding_columns=s_embedding_columns,
                state_mode=state_mode,
                state_head_model=state_head_model,
                group_column=group_column,
                env_name=env_name,
                specialist_model=specialist_model,
            )
            exact_actions_all.extend(exact_actions)
            predicted_actions_all.extend(predicted_actions)
            ordered_test_parts.append(test_env)

        ordered_test_frame = pd.concat(ordered_test_parts, ignore_index=True)
        exact_metrics = evaluate_policy(ordered_test_frame, exact_actions_all)
        predicted_metrics = evaluate_policy(ordered_test_frame, predicted_actions_all)
        records.append(
            {
                "baseline": "specialist_portfolio_exact_state",
                "fold": fold_index,
                "num_train": len(train_frame),
                "num_test": len(ordered_test_frame),
                **exact_metrics,
            }
        )
        records.append(
            {
                "baseline": "specialist_portfolio_predicted_state",
                "fold": fold_index,
                "num_train": len(train_frame),
                "num_test": len(ordered_test_frame),
                **predicted_metrics,
            }
        )
    return pd.DataFrame(records)


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    arithmetic_frame, arithmetic_q_cols, arithmetic_s_cols = _load_domain_frame(
        args.arithmetic_input_csv,
        args.arithmetic_embedding_npz,
        "arithmetic",
        args.group_column,
        args.include_env_feature,
    )
    linear_frame, linear_q_cols, linear_s_cols = _load_domain_frame(
        args.linear_input_csv,
        args.linear_embedding_npz,
        "linear_equations",
        args.group_column,
        args.include_env_feature,
    )
    if arithmetic_q_cols != linear_q_cols or arithmetic_s_cols != linear_s_cols:
        raise ValueError("Embedding column layouts must match across domains for pooled experiments")

    merged_frame = pd.concat([arithmetic_frame, linear_frame], ignore_index=True)
    q_embedding_columns = arithmetic_q_cols
    s_embedding_columns = arithmetic_s_cols

    shared_results = run_factorized_cv(
        frame=merged_frame,
        q_embedding_columns=q_embedding_columns,
        s_embedding_columns=s_embedding_columns,
        group_column=args.group_column,
        n_splits=args.n_splits,
        state_mode=args.state_mode,
        state_head_model=args.state_head_model,
        value_head_model=args.shared_value_head_model,
    )
    shared_summary = summarize_factorized_results(shared_results)
    shared_summary["env_conditioning"] = "enabled" if args.include_env_feature else "disabled"

    portfolio_results = run_specialist_portfolio_cv(
        merged_frame=merged_frame,
        q_embedding_columns=q_embedding_columns,
        s_embedding_columns=s_embedding_columns,
        group_column=args.group_column,
        n_splits=args.n_splits,
        state_mode=args.state_mode,
        state_head_model=args.state_head_model,
        arithmetic_specialist_model=args.arithmetic_specialist_model,
        linear_specialist_model=args.linear_specialist_model,
    )
    portfolio_summary = (
        portfolio_results.groupby("baseline", as_index=False)[
            ["oracle_action_accuracy", "mean_action_regret", "mean_chosen_utility"]
        ]
        .mean()
        .sort_values("mean_action_regret", ascending=True)
        .reset_index(drop=True)
    )
    portfolio_summary["shared_value_head_model"] = args.shared_value_head_model
    portfolio_summary["portfolio_arithmetic_model"] = args.arithmetic_specialist_model
    portfolio_summary["portfolio_linear_model"] = args.linear_specialist_model
    portfolio_summary["env_conditioning"] = "enabled" if args.include_env_feature else "disabled"

    combined_summary = pd.concat(
        [
            shared_summary.assign(
                controller_family="shared",
                env_conditioning="enabled" if args.include_env_feature else "disabled",
            ),
            portfolio_summary.assign(controller_family="specialist_portfolio"),
        ],
        ignore_index=True,
        sort=False,
    ).sort_values("mean_action_regret", ascending=True).reset_index(drop=True)

    shared_results.to_csv(output_dir / "shared_cv_results.csv", index=False)
    shared_summary.to_csv(output_dir / "shared_summary.csv", index=False)
    portfolio_results.to_csv(output_dir / "portfolio_cv_results.csv", index=False)
    portfolio_summary.to_csv(output_dir / "portfolio_summary.csv", index=False)
    combined_summary.to_csv(output_dir / "combined_summary.csv", index=False)

    payload = {
        "shared_value_head_model": args.shared_value_head_model,
        "portfolio_arithmetic_model": args.arithmetic_specialist_model,
        "portfolio_linear_model": args.linear_specialist_model,
        "env_conditioning": args.include_env_feature,
        "combined_summary": combined_summary.to_dict(orient="records"),
    }
    with (output_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)

    print(combined_summary.to_string(index=False))


if __name__ == "__main__":
    main()
