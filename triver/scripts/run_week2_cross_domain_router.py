from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from triver.baselines.week2 import ACTIONS, UTILITY_COLUMNS, attach_embeddings, evaluate_policy, load_oracle_frame
from triver.factorized.week2 import (
    fit_conditional_lowrank_pairwise_error_calibrated_bundle,
    fit_joint_pairwise_gate,
    infer_embedding_columns,
    predict_actions,
    prepare_factorized_split_states,
    score_action_values,
    state_mode_feature_columns,
    state_uncertainty_columns,
)


@dataclass(frozen=True)
class ConstantRouter:
    label: int

    def predict(self, features: pd.DataFrame) -> np.ndarray:
        return np.full(len(features), self.label, dtype=int)

    def predict_proba(self, features: pd.DataFrame) -> np.ndarray:
        probs = np.full(len(features), float(self.label), dtype=float)
        return np.column_stack([1.0 - probs, probs])


@dataclass(frozen=True)
class ConstantRegressor:
    value: float

    def predict(self, features: pd.DataFrame) -> np.ndarray:
        return np.full(len(features), self.value, dtype=float)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run pooled cross-domain expert-router experiment.")
    parser.add_argument("--arithmetic-input-csv", required=True)
    parser.add_argument("--arithmetic-embedding-npz", required=True)
    parser.add_argument("--linear-input-csv", required=True)
    parser.add_argument("--linear-embedding-npz", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--group-column", default="sample_id")
    parser.add_argument("--n-splits", type=int, default=5)
    parser.add_argument("--state-mode", choices=["legacy", "s_proxy"], default="s_proxy")
    parser.add_argument("--state-head-model", choices=["linear", "pca_ridge", "pca_enet", "rf"], default="pca_enet")
    parser.add_argument("--include-env-feature", action="store_true")
    parser.add_argument(
        "--router-cache-dir",
        default=None,
        help="Optional directory for fold-level router feature caches. Intended for repeated same-family sweeps.",
    )
    parser.add_argument(
        "--router-family-mode",
        choices=["full", "rf_highcap_only"],
        default="full",
        help="Run the full router comparison table or only the rf_high_capacity family baselines.",
    )
    parser.add_argument(
        "--arithmetic-specialist-model",
        default="conditional_lowrank_pairwise_error_calibrated",
        choices=["conditional_lowrank_pairwise_error_calibrated"],
    )
    parser.add_argument(
        "--linear-specialist-model",
        default="joint_pairwise_gate",
        choices=["joint_pairwise_gate"],
    )
    return parser.parse_args()


def _load_domain_frame(
    input_csv: str,
    embedding_npz: str,
    domain_name: str,
    group_column: str,
) -> tuple[pd.DataFrame, list[str], list[str]]:
    frame = load_oracle_frame(input_csv, exclude_ambiguous=True)
    frame[group_column] = frame[group_column].astype(str).map(lambda value: f"{domain_name}:{value}")
    frame["env"] = domain_name
    frame["env_is_linear"] = 1.0 if domain_name == "linear_equations" else 0.0
    frame, q_embedding_columns = attach_embeddings(frame, embedding_npz, column_prefix="qemb")
    frame, s_embedding_columns = attach_embeddings(frame, embedding_npz, column_prefix="semb")
    q_embedding_columns = infer_embedding_columns(frame, prefix="qemb_")
    s_embedding_columns = infer_embedding_columns(frame, prefix="semb_")
    return frame, q_embedding_columns, s_embedding_columns


def _fit_and_apply_specialist(
    train_frame: pd.DataFrame,
    eval_frame: pd.DataFrame,
    q_embedding_columns: list[str],
    s_embedding_columns: list[str],
    state_mode: str,
    state_head_model: str,
    group_column: str,
    env_name: str,
    specialist_model: str,
) -> tuple[pd.DataFrame, list[str], np.ndarray]:
    split = prepare_factorized_split_states(
        train_frame=train_frame,
        test_frame=eval_frame,
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
        score_matrix = score_action_values(
            bundle,
            split["test_state"],
            bundle.metadata["predicted_feature_columns"],
        )
        actions = predict_actions(
            bundle,
            split["test_state"],
            bundle.metadata["predicted_feature_columns"],
        )
        return split["test_state"], actions, score_matrix

    if env_name == "arithmetic" and specialist_model == "conditional_lowrank_pairwise_error_calibrated":
        bundle = fit_conditional_lowrank_pairwise_error_calibrated_bundle(
            train_exact_state=split["train_exact_state"],
            calibration_state=split["train_oof_state"],
            state_mode=state_mode,
        )
        score_matrix = score_action_values(
            bundle,
            split["test_state"],
            bundle.metadata["risk_feature_columns"],
        )
        actions = predict_actions(
            bundle,
            split["test_state"],
            bundle.metadata["risk_feature_columns"],
        )
        return split["test_state"], actions, score_matrix

    raise ValueError(f"Unsupported specialist configuration: {env_name=} {specialist_model=}")


def _chosen_utilities(frame: pd.DataFrame, actions: list[str]) -> np.ndarray:
    return np.array(
        [frame.iloc[index][UTILITY_COLUMNS[action]] for index, action in enumerate(actions)],
        dtype=float,
    )


def _router_feature_frame(
    base_frame: pd.DataFrame,
    arithmetic_state: pd.DataFrame,
    linear_state: pd.DataFrame,
    arithmetic_actions: list[str],
    linear_actions: list[str],
    arithmetic_scores: np.ndarray,
    linear_scores: np.ndarray,
    state_mode: str,
    include_env_feature: bool,
) -> pd.DataFrame:
    pred_columns = state_mode_feature_columns(state_mode)[1]
    uncertainty_columns = state_uncertainty_columns(state_mode)
    feature_frame = pd.DataFrame(index=base_frame.index)

    for column in ["budget_tokens", "prefix_length", "is_perturbed"]:
        if column in base_frame.columns:
            feature_frame[column] = base_frame[column].astype(float)
    if include_env_feature and "env_is_linear" in base_frame.columns:
        feature_frame["env_is_linear"] = base_frame["env_is_linear"].astype(float)

    for column in pred_columns + uncertainty_columns:
        if column in arithmetic_state.columns:
            feature_frame[f"arith_{column}"] = arithmetic_state[column].astype(float)
        if column in linear_state.columns:
            feature_frame[f"linear_{column}"] = linear_state[column].astype(float)

    def _attach_score_features(prefix: str, score_matrix: np.ndarray) -> None:
        for action_index, action_name in enumerate(ACTIONS):
            feature_frame[f"{prefix}_{action_name}_score"] = score_matrix[:, action_index]
        sorted_scores = np.sort(score_matrix, axis=1)
        feature_frame[f"{prefix}_score_gap"] = sorted_scores[:, -1] - sorted_scores[:, -2]
        feature_frame[f"{prefix}_score_max"] = sorted_scores[:, -1]
        feature_frame[f"{prefix}_score_min"] = sorted_scores[:, 0]

    _attach_score_features("arith", arithmetic_scores)
    _attach_score_features("linear", linear_scores)
    arithmetic_best = arithmetic_scores.argmax(axis=1)
    linear_best = linear_scores.argmax(axis=1)
    feature_frame["expert_best_disagree"] = (arithmetic_best != linear_best).astype(float)
    feature_frame["linear_best_margin_over_arith"] = linear_scores.max(axis=1) - arithmetic_scores.max(axis=1)

    feature_frame["experts_agree"] = (np.asarray(arithmetic_actions) == np.asarray(linear_actions)).astype(float)
    feature_frame["arithmetic_action"] = arithmetic_actions
    feature_frame["linear_action"] = linear_actions
    feature_frame = pd.get_dummies(
        feature_frame,
        columns=["arithmetic_action", "linear_action"],
        dtype=float,
    )
    return feature_frame.fillna(0.0)


def _fit_router(
    router_x: pd.DataFrame,
    router_y: np.ndarray,
    sample_weight: np.ndarray | None = None,
) -> tuple[object, list[str]]:
    router_x = router_x.fillna(0.0)
    feature_columns = list(router_x.columns)
    if np.unique(router_y).size < 2:
        return ConstantRouter(int(router_y[0])), feature_columns
    if sample_weight is not None:
        positive_weight = sample_weight > 1e-12
        weighted_classes = np.unique(router_y[positive_weight])
        if weighted_classes.size < 2:
            if weighted_classes.size == 0:
                return ConstantRouter(int(np.bincount(router_y.astype(int)).argmax())), feature_columns
            return ConstantRouter(int(weighted_classes[0])), feature_columns
    router = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("logreg", LogisticRegression(max_iter=4000, class_weight="balanced", C=0.5)),
        ]
    )
    if sample_weight is None:
        router.fit(router_x, router_y)
    else:
        router.fit(router_x, router_y, logreg__sample_weight=sample_weight)
    return router, feature_columns


def _fit_rf_router(
    router_x: pd.DataFrame,
    router_y: np.ndarray,
    sample_weight: np.ndarray | None = None,
) -> tuple[object, list[str]]:
    router_x = router_x.fillna(0.0)
    feature_columns = list(router_x.columns)
    if np.unique(router_y).size < 2:
        return ConstantRouter(int(router_y[0])), feature_columns
    if sample_weight is not None:
        positive_weight = sample_weight > 1e-12
        weighted_classes = np.unique(router_y[positive_weight])
        if weighted_classes.size < 2:
            if weighted_classes.size == 0:
                return ConstantRouter(int(np.bincount(router_y.astype(int)).argmax())), feature_columns
            return ConstantRouter(int(weighted_classes[0])), feature_columns
    router = RandomForestClassifier(
        n_estimators=256,
        max_depth=6,
        min_samples_leaf=3,
        class_weight="balanced_subsample",
        random_state=0,
        n_jobs=-1,
    )
    if sample_weight is None:
        router.fit(router_x, router_y)
    else:
        router.fit(router_x, router_y, sample_weight=sample_weight)
    return router, feature_columns


def _fit_rf_router_high_capacity(
    router_x: pd.DataFrame,
    router_y: np.ndarray,
    sample_weight: np.ndarray | None = None,
) -> tuple[object, list[str]]:
    router_x = router_x.fillna(0.0)
    feature_columns = list(router_x.columns)
    if np.unique(router_y).size < 2:
        return ConstantRouter(int(router_y[0])), feature_columns
    if sample_weight is not None:
        positive_weight = sample_weight > 1e-12
        weighted_classes = np.unique(router_y[positive_weight])
        if weighted_classes.size < 2:
            if weighted_classes.size == 0:
                return ConstantRouter(int(np.bincount(router_y.astype(int)).argmax())), feature_columns
            return ConstantRouter(int(weighted_classes[0])), feature_columns
    router = RandomForestClassifier(
        n_estimators=512,
        max_depth=None,
        min_samples_split=4,
        min_samples_leaf=2,
        max_features="sqrt",
        criterion="log_loss",
        class_weight="balanced_subsample",
        random_state=0,
        n_jobs=-1,
    )
    if sample_weight is None:
        router.fit(router_x, router_y)
    else:
        router.fit(router_x, router_y, sample_weight=sample_weight)
    return router, feature_columns


def _fit_rf_router_high_capacity_extra_trees(
    router_x: pd.DataFrame,
    router_y: np.ndarray,
    sample_weight: np.ndarray | None = None,
) -> tuple[object, list[str]]:
    router_x = router_x.fillna(0.0)
    feature_columns = list(router_x.columns)
    if np.unique(router_y).size < 2:
        return ConstantRouter(int(router_y[0])), feature_columns
    if sample_weight is not None:
        positive_weight = sample_weight > 1e-12
        weighted_classes = np.unique(router_y[positive_weight])
        if weighted_classes.size < 2:
            if weighted_classes.size == 0:
                return ConstantRouter(int(np.bincount(router_y.astype(int)).argmax())), feature_columns
            return ConstantRouter(int(weighted_classes[0])), feature_columns
    router = ExtraTreesClassifier(
        n_estimators=768,
        max_depth=None,
        min_samples_split=4,
        min_samples_leaf=2,
        max_features="sqrt",
        criterion="log_loss",
        class_weight="balanced",
        random_state=0,
        n_jobs=-1,
    )
    if sample_weight is None:
        router.fit(router_x, router_y)
    else:
        router.fit(router_x, router_y, sample_weight=sample_weight)
    return router, feature_columns


def _fit_rf_router_high_capacity_extra_trees_full_features(
    router_x: pd.DataFrame,
    router_y: np.ndarray,
    sample_weight: np.ndarray | None = None,
) -> tuple[object, list[str]]:
    router_x = router_x.fillna(0.0)
    feature_columns = list(router_x.columns)
    if np.unique(router_y).size < 2:
        return ConstantRouter(int(router_y[0])), feature_columns
    if sample_weight is not None:
        positive_weight = sample_weight > 1e-12
        weighted_classes = np.unique(router_y[positive_weight])
        if weighted_classes.size < 2:
            if weighted_classes.size == 0:
                return ConstantRouter(int(np.bincount(router_y.astype(int)).argmax())), feature_columns
            return ConstantRouter(int(weighted_classes[0])), feature_columns
    router = ExtraTreesClassifier(
        n_estimators=768,
        max_depth=None,
        min_samples_split=4,
        min_samples_leaf=2,
        max_features=None,
        criterion="log_loss",
        class_weight="balanced",
        random_state=0,
        n_jobs=-1,
    )
    if sample_weight is None:
        router.fit(router_x, router_y)
    else:
        router.fit(router_x, router_y, sample_weight=sample_weight)
    return router, feature_columns


def _fit_gap_regressor(
    router_x: pd.DataFrame,
    utility_gap: np.ndarray,
) -> tuple[object, list[str]]:
    router_x = router_x.fillna(0.0)
    feature_columns = list(router_x.columns)
    if np.allclose(utility_gap, utility_gap[0]):
        return ConstantRegressor(float(utility_gap[0])), feature_columns
    regressor = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("ridge", Ridge(alpha=1.0)),
        ]
    )
    regressor.fit(router_x, utility_gap)
    return regressor, feature_columns


def _fit_rf_gap_regressor(
    router_x: pd.DataFrame,
    utility_gap: np.ndarray,
) -> tuple[object, list[str]]:
    router_x = router_x.fillna(0.0)
    feature_columns = list(router_x.columns)
    if np.allclose(utility_gap, utility_gap[0]):
        return ConstantRegressor(float(utility_gap[0])), feature_columns
    regressor = RandomForestRegressor(
        n_estimators=256,
        max_depth=6,
        min_samples_leaf=3,
        random_state=0,
        n_jobs=-1,
    )
    regressor.fit(router_x, utility_gap)
    return regressor, feature_columns


def _fit_expert_utility_regressors(
    router_x: pd.DataFrame,
    arithmetic_utility: np.ndarray,
    linear_utility: np.ndarray,
) -> tuple[tuple[object, object], list[str]]:
    arithmetic_regressor, feature_columns = _fit_gap_regressor(router_x, arithmetic_utility)
    linear_regressor, _ = _fit_gap_regressor(router_x, linear_utility)
    return (arithmetic_regressor, linear_regressor), feature_columns


def _fit_rf_expert_utility_regressors(
    router_x: pd.DataFrame,
    arithmetic_utility: np.ndarray,
    linear_utility: np.ndarray,
) -> tuple[tuple[object, object], list[str]]:
    arithmetic_regressor, feature_columns = _fit_rf_gap_regressor(router_x, arithmetic_utility)
    linear_regressor, _ = _fit_rf_gap_regressor(router_x, linear_utility)
    return (arithmetic_regressor, linear_regressor), feature_columns


def _router_probabilities(
    router: object,
    router_columns: list[str],
    router_x: pd.DataFrame,
) -> np.ndarray:
    aligned_x = router_x.reindex(columns=router_columns, fill_value=0.0).fillna(0.0)
    if hasattr(router, "predict_proba"):
        return router.predict_proba(aligned_x)[:, 1]
    return router.predict(aligned_x).astype(float)


def _regression_predictions(
    regressor: object,
    feature_columns: list[str],
    router_x: pd.DataFrame,
) -> np.ndarray:
    aligned_x = router_x.reindex(columns=feature_columns, fill_value=0.0).fillna(0.0)
    return regressor.predict(aligned_x).astype(float)


def _direct_utility_actions(
    arithmetic_regressor: object,
    linear_regressor: object,
    feature_columns: list[str],
    router_x: pd.DataFrame,
    arithmetic_actions: list[str],
    linear_actions: list[str],
) -> tuple[list[str], np.ndarray, np.ndarray]:
    arithmetic_pred = _regression_predictions(arithmetic_regressor, feature_columns, router_x)
    linear_pred = _regression_predictions(linear_regressor, feature_columns, router_x)
    actions = [
        linear_actions[index] if float(linear_pred[index]) >= float(arithmetic_pred[index]) else arithmetic_actions[index]
        for index in range(len(router_x))
    ]
    return actions, arithmetic_pred, linear_pred


def _route_actions(
    router: object,
    router_columns: list[str],
    router_x: pd.DataFrame,
    arithmetic_actions: list[str],
    linear_actions: list[str],
) -> list[str]:
    aligned_x = router_x.reindex(columns=router_columns, fill_value=0.0).fillna(0.0)
    choice = router.predict(aligned_x)
    return [
        linear_actions[index] if int(choice[index]) == 1 else arithmetic_actions[index]
        for index in range(len(choice))
    ]


def _build_env_override_labels(
    frame: pd.DataFrame,
    arithmetic_utility: np.ndarray,
    linear_utility: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    default_is_linear = frame["env_is_linear"].astype(int).to_numpy()
    default_utility = np.where(default_is_linear == 1, linear_utility, arithmetic_utility)
    alt_utility = np.where(default_is_linear == 1, arithmetic_utility, linear_utility)
    gain = alt_utility - default_utility
    return (gain > 0).astype(int), gain, default_utility, alt_utility


def _build_oracle_router_labels(
    frame: pd.DataFrame,
    arithmetic_utility: np.ndarray,
    linear_utility: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    label = (linear_utility > arithmetic_utility).astype(int)
    ties = np.isclose(linear_utility, arithmetic_utility)
    label[ties] = frame.loc[ties, "env_is_linear"].astype(int).to_numpy()
    margin = np.abs(linear_utility - arithmetic_utility)
    return label, margin


def _select_override_threshold(
    override_prob: np.ndarray,
    default_utility: np.ndarray,
    alt_utility: np.ndarray,
) -> float:
    thresholds = [0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.1]
    best_threshold = 1.1
    best_utility = float(np.mean(default_utility))
    for threshold in thresholds:
        chosen = np.where(override_prob >= threshold, alt_utility, default_utility)
        chosen_mean = float(np.mean(chosen))
        if chosen_mean > best_utility + 1e-12:
            best_utility = chosen_mean
            best_threshold = threshold
    return best_threshold


def _select_gap_override_threshold(
    gap_prediction: np.ndarray,
    default_is_linear: np.ndarray,
    default_utility: np.ndarray,
    alt_utility: np.ndarray,
) -> float:
    abs_gap = np.abs(gap_prediction)
    quantiles = np.quantile(abs_gap, [0.0, 0.5, 0.75, 0.9, 0.95, 0.99])
    thresholds = sorted({float(np.round(value, 6)) for value in quantiles} | {0.0})
    best_threshold = 0.0
    best_utility = float(np.mean(default_utility))
    for threshold in thresholds:
        choose_alt = np.where(default_is_linear == 1, gap_prediction <= -threshold, gap_prediction >= threshold)
        chosen = np.where(choose_alt, alt_utility, default_utility)
        chosen_mean = float(np.mean(chosen))
        if chosen_mean > best_utility + 1e-12:
            best_utility = chosen_mean
            best_threshold = threshold
    return best_threshold


def _build_router_training_set(
    train_frame: pd.DataFrame,
    q_embedding_columns: list[str],
    s_embedding_columns: list[str],
    group_column: str,
    state_mode: str,
    state_head_model: str,
    include_env_feature: bool,
    arithmetic_specialist_model: str,
    linear_specialist_model: str,
) -> tuple[
    pd.DataFrame,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    unique_groups = train_frame[group_column].nunique()
    effective_splits = min(4, unique_groups)
    if effective_splits < 2:
        train_eval = train_frame.reset_index(drop=True)
        arithmetic_train = train_frame.loc[train_frame["env"] == "arithmetic"].reset_index(drop=True)
        linear_train = train_frame.loc[train_frame["env"] == "linear_equations"].reset_index(drop=True)
        arithmetic_state, arithmetic_actions, arithmetic_scores = _fit_and_apply_specialist(
            train_frame=arithmetic_train,
            eval_frame=train_eval,
            q_embedding_columns=q_embedding_columns,
            s_embedding_columns=s_embedding_columns,
            state_mode=state_mode,
            state_head_model=state_head_model,
            group_column=group_column,
            env_name="arithmetic",
            specialist_model=arithmetic_specialist_model,
        )
        linear_state, linear_actions, linear_scores = _fit_and_apply_specialist(
            train_frame=linear_train,
            eval_frame=train_eval,
            q_embedding_columns=q_embedding_columns,
            s_embedding_columns=s_embedding_columns,
            state_mode=state_mode,
            state_head_model=state_head_model,
            group_column=group_column,
            env_name="linear_equations",
            specialist_model=linear_specialist_model,
        )
        router_x = _router_feature_frame(
            base_frame=train_eval,
            arithmetic_state=arithmetic_state,
            linear_state=linear_state,
            arithmetic_actions=arithmetic_actions,
            linear_actions=linear_actions,
            arithmetic_scores=arithmetic_scores,
            linear_scores=linear_scores,
            state_mode=state_mode,
            include_env_feature=include_env_feature,
        )
        arithmetic_utility = _chosen_utilities(train_eval, arithmetic_actions)
        linear_utility = _chosen_utilities(train_eval, linear_actions)
        router_y, router_margin = _build_oracle_router_labels(
            frame=train_eval,
            arithmetic_utility=arithmetic_utility,
            linear_utility=linear_utility,
        )
        override_y, override_gain, default_utility, alt_utility = _build_env_override_labels(
            frame=train_eval,
            arithmetic_utility=arithmetic_utility,
            linear_utility=linear_utility,
        )
        default_is_linear = train_eval["env_is_linear"].astype(int).to_numpy()
        utility_gap = linear_utility - arithmetic_utility
        return (
            router_x,
            router_y,
            router_margin,
            utility_gap,
            arithmetic_utility,
            linear_utility,
            override_y,
            default_utility,
            alt_utility,
            default_is_linear,
        )

    splitter = GroupKFold(n_splits=effective_splits)
    router_parts: list[pd.DataFrame] = []
    labels: list[np.ndarray] = []
    margins: list[np.ndarray] = []
    override_labels: list[np.ndarray] = []
    default_is_linear_parts: list[np.ndarray] = []
    for inner_train_index, inner_valid_index in splitter.split(train_frame, groups=train_frame[group_column]):
        inner_train = train_frame.iloc[inner_train_index].reset_index(drop=True)
        inner_valid = train_frame.iloc[inner_valid_index].reset_index(drop=True)
        arithmetic_train = inner_train.loc[inner_train["env"] == "arithmetic"].reset_index(drop=True)
        linear_train = inner_train.loc[inner_train["env"] == "linear_equations"].reset_index(drop=True)
        arithmetic_state, arithmetic_actions, arithmetic_scores = _fit_and_apply_specialist(
            train_frame=arithmetic_train,
            eval_frame=inner_valid,
            q_embedding_columns=q_embedding_columns,
            s_embedding_columns=s_embedding_columns,
            state_mode=state_mode,
            state_head_model=state_head_model,
            group_column=group_column,
            env_name="arithmetic",
            specialist_model=arithmetic_specialist_model,
        )
        linear_state, linear_actions, linear_scores = _fit_and_apply_specialist(
            train_frame=linear_train,
            eval_frame=inner_valid,
            q_embedding_columns=q_embedding_columns,
            s_embedding_columns=s_embedding_columns,
            state_mode=state_mode,
            state_head_model=state_head_model,
            group_column=group_column,
            env_name="linear_equations",
            specialist_model=linear_specialist_model,
        )
        router_parts.append(
            _router_feature_frame(
                base_frame=inner_valid,
                arithmetic_state=arithmetic_state,
                linear_state=linear_state,
                arithmetic_actions=arithmetic_actions,
                linear_actions=linear_actions,
                arithmetic_scores=arithmetic_scores,
                linear_scores=linear_scores,
                state_mode=state_mode,
                include_env_feature=include_env_feature,
            )
        )
        arithmetic_utility = _chosen_utilities(inner_valid, arithmetic_actions)
        linear_utility = _chosen_utilities(inner_valid, linear_actions)
        label, margin = _build_oracle_router_labels(
            frame=inner_valid,
            arithmetic_utility=arithmetic_utility,
            linear_utility=linear_utility,
        )
        labels.append(label)
        margins.append(margin)
        override_label, override_gain, default_utility, alt_utility = _build_env_override_labels(
            frame=inner_valid,
            arithmetic_utility=arithmetic_utility,
            linear_utility=linear_utility,
        )
        override_labels.append(np.column_stack([override_label, default_utility, alt_utility]))
        default_is_linear_parts.append(inner_valid["env_is_linear"].astype(int).to_numpy())
    router_x = pd.concat(router_parts, ignore_index=True)
    router_y = np.concatenate(labels, axis=0)
    router_margin = np.concatenate(margins, axis=0)
    override_stack = np.concatenate(override_labels, axis=0)
    override_y = override_stack[:, 0].astype(int)
    default_utility = override_stack[:, 1].astype(float)
    alt_utility = override_stack[:, 2].astype(float)
    default_is_linear = np.concatenate(default_is_linear_parts, axis=0)
    utility_gap = np.where(router_y == 1, router_margin, -router_margin)
    utility_gap[np.isclose(router_margin, 0.0)] = 0.0
    arithmetic_utility = np.where(router_y == 1, 0.0, 0.0)
    linear_utility = np.where(router_y == 1, 0.0, 0.0)
    row_offset = 0
    for part in router_parts:
        part_len = len(part)
        # Reconstruct specialist utilities from signed gap and oracle margin labels collected above.
        # The actual utility arrays are assembled below in the same order as router_parts.
        row_offset += part_len
    # Build the expert-utility targets directly from the OOF specialist utilities gathered above.
    arithmetic_utility_parts: list[np.ndarray] = []
    linear_utility_parts: list[np.ndarray] = []
    for inner_train_index, inner_valid_index in splitter.split(train_frame, groups=train_frame[group_column]):
        inner_train = train_frame.iloc[inner_train_index].reset_index(drop=True)
        inner_valid = train_frame.iloc[inner_valid_index].reset_index(drop=True)
        arithmetic_train = inner_train.loc[inner_train["env"] == "arithmetic"].reset_index(drop=True)
        linear_train = inner_train.loc[inner_train["env"] == "linear_equations"].reset_index(drop=True)
        _, arithmetic_actions, _ = _fit_and_apply_specialist(
            train_frame=arithmetic_train,
            eval_frame=inner_valid,
            q_embedding_columns=q_embedding_columns,
            s_embedding_columns=s_embedding_columns,
            state_mode=state_mode,
            state_head_model=state_head_model,
            group_column=group_column,
            env_name="arithmetic",
            specialist_model=arithmetic_specialist_model,
        )
        _, linear_actions, _ = _fit_and_apply_specialist(
            train_frame=linear_train,
            eval_frame=inner_valid,
            q_embedding_columns=q_embedding_columns,
            s_embedding_columns=s_embedding_columns,
            state_mode=state_mode,
            state_head_model=state_head_model,
            group_column=group_column,
            env_name="linear_equations",
            specialist_model=linear_specialist_model,
        )
        arithmetic_utility_parts.append(_chosen_utilities(inner_valid, arithmetic_actions))
        linear_utility_parts.append(_chosen_utilities(inner_valid, linear_actions))
    arithmetic_utility = np.concatenate(arithmetic_utility_parts, axis=0)
    linear_utility = np.concatenate(linear_utility_parts, axis=0)
    return (
        router_x,
        router_y,
        router_margin,
        utility_gap,
        arithmetic_utility,
        linear_utility,
        override_y,
        default_utility,
        alt_utility,
        default_is_linear,
    )


def run_router_cv(
    merged_frame: pd.DataFrame,
    q_embedding_columns: list[str],
    s_embedding_columns: list[str],
    group_column: str,
    n_splits: int,
    state_mode: str,
    state_head_model: str,
    include_env_feature: bool,
    arithmetic_specialist_model: str,
    linear_specialist_model: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    unique_groups = merged_frame[group_column].nunique()
    effective_splits = min(n_splits, unique_groups)
    if effective_splits < 2:
        raise ValueError("Need at least 2 groups for cross-validation")

    splitter = GroupKFold(n_splits=effective_splits)
    records: list[dict[str, float | int | str]] = []
    sample_records: list[dict[str, float | int | str]] = []
    for fold_index, (train_index, test_index) in enumerate(
        splitter.split(merged_frame, groups=merged_frame[group_column]),
        start=1,
    ):
        train_frame = merged_frame.iloc[train_index].reset_index(drop=True)
        test_frame = merged_frame.iloc[test_index].reset_index(drop=True)

        (
            router_x,
            router_y,
            router_margin,
            utility_gap_train,
            arithmetic_utility_train,
            linear_utility_train,
            override_y,
            default_utility_train,
            alt_utility_train,
            default_is_linear_train,
        ) = _build_router_training_set(
            train_frame=train_frame,
            q_embedding_columns=q_embedding_columns,
            s_embedding_columns=s_embedding_columns,
            group_column=group_column,
            state_mode=state_mode,
            state_head_model=state_head_model,
            include_env_feature=include_env_feature,
            arithmetic_specialist_model=arithmetic_specialist_model,
            linear_specialist_model=linear_specialist_model,
        )
        router_model, router_columns = _fit_router(router_x, router_y)
        rf_router_model, rf_router_columns = _fit_rf_router(router_x, router_y)
        rf_highcap_router_model, rf_highcap_router_columns = _fit_rf_router_high_capacity(router_x, router_y)
        gap_router_model, gap_router_columns = _fit_gap_regressor(
            router_x,
            utility_gap_train,
        )
        rf_gap_router_model, rf_gap_router_columns = _fit_rf_gap_regressor(
            router_x,
            utility_gap_train,
        )
        direct_utility_models, direct_utility_columns = _fit_expert_utility_regressors(
            router_x,
            arithmetic_utility_train,
            linear_utility_train,
        )
        rf_direct_utility_models, rf_direct_utility_columns = _fit_rf_expert_utility_regressors(
            router_x,
            arithmetic_utility_train,
            linear_utility_train,
        )
        gap_router_pred_train = _regression_predictions(
            gap_router_model,
            gap_router_columns,
            router_x,
        )
        rf_gap_router_pred_train = _regression_predictions(
            rf_gap_router_model,
            rf_gap_router_columns,
            router_x,
        )
        gap_fallback_threshold = _select_gap_override_threshold(
            gap_router_pred_train,
            default_is_linear_train,
            default_utility_train,
            alt_utility_train,
        )
        rf_gap_fallback_threshold = _select_gap_override_threshold(
            rf_gap_router_pred_train,
            default_is_linear_train,
            default_utility_train,
            alt_utility_train,
        )
        rf_router_prob_train = _router_probabilities(
            rf_router_model,
            rf_router_columns,
            router_x,
        )
        rf_fallback_conf_train = np.where(
            default_is_linear_train == 1,
            1.0 - rf_router_prob_train,
            rf_router_prob_train,
        )
        rf_specialist_fallback_threshold = _select_override_threshold(
            rf_fallback_conf_train,
            default_utility_train,
            alt_utility_train,
        )
        margin_router_weight = np.maximum(router_margin, 0.0)
        soft_margin_router_weight = 1.0 + margin_router_weight
        margin_router_model, margin_router_columns = _fit_router(
            router_x,
            router_y,
            sample_weight=margin_router_weight,
        )
        rf_highcap_margin_router_model, rf_highcap_margin_router_columns = _fit_rf_router_high_capacity(
            router_x,
            router_y,
            sample_weight=margin_router_weight,
        )
        rf_highcap_soft_margin_router_model, rf_highcap_soft_margin_router_columns = _fit_rf_router_high_capacity(
            router_x,
            router_y,
            sample_weight=soft_margin_router_weight,
        )
        margin_router_prob_train = _router_probabilities(
            margin_router_model,
            margin_router_columns,
            router_x,
        )
        margin_override_conf_train = np.where(
            default_is_linear_train == 1,
            1.0 - margin_router_prob_train,
            margin_router_prob_train,
        )
        margin_fallback_threshold = _select_override_threshold(
            margin_override_conf_train,
            default_utility_train,
            alt_utility_train,
        )
        override_model, override_columns = _fit_router(router_x, override_y)
        sparse_override_weight = np.where(
            override_y == 1,
            1.0 + np.maximum(alt_utility_train - default_utility_train, 0.0),
            0.25,
        )
        sparse_override_model, sparse_override_columns = _fit_router(
            router_x,
            override_y,
            sample_weight=sparse_override_weight,
        )
        sparse_override_threshold = _select_override_threshold(
            _router_probabilities(sparse_override_model, sparse_override_columns, router_x),
            default_utility_train,
            alt_utility_train,
        )

        arithmetic_train = train_frame.loc[train_frame["env"] == "arithmetic"].reset_index(drop=True)
        linear_train = train_frame.loc[train_frame["env"] == "linear_equations"].reset_index(drop=True)
        arithmetic_state, arithmetic_actions, arithmetic_scores = _fit_and_apply_specialist(
            train_frame=arithmetic_train,
            eval_frame=test_frame,
            q_embedding_columns=q_embedding_columns,
            s_embedding_columns=s_embedding_columns,
            state_mode=state_mode,
            state_head_model=state_head_model,
            group_column=group_column,
            env_name="arithmetic",
            specialist_model=arithmetic_specialist_model,
        )
        linear_state, linear_actions, linear_scores = _fit_and_apply_specialist(
            train_frame=linear_train,
            eval_frame=test_frame,
            q_embedding_columns=q_embedding_columns,
            s_embedding_columns=s_embedding_columns,
            state_mode=state_mode,
            state_head_model=state_head_model,
            group_column=group_column,
            env_name="linear_equations",
            specialist_model=linear_specialist_model,
        )
        test_router_x = _router_feature_frame(
            base_frame=test_frame,
            arithmetic_state=arithmetic_state,
            linear_state=linear_state,
            arithmetic_actions=arithmetic_actions,
            linear_actions=linear_actions,
            arithmetic_scores=arithmetic_scores,
            linear_scores=linear_scores,
            state_mode=state_mode,
            include_env_feature=include_env_feature,
        )
        routed_actions = _route_actions(
            router=router_model,
            router_columns=router_columns,
            router_x=test_router_x,
            arithmetic_actions=arithmetic_actions,
            linear_actions=linear_actions,
        )
        rf_routed_actions = _route_actions(
            router=rf_router_model,
            router_columns=rf_router_columns,
            router_x=test_router_x,
            arithmetic_actions=arithmetic_actions,
            linear_actions=linear_actions,
        )
        rf_highcap_routed_actions = _route_actions(
            router=rf_highcap_router_model,
            router_columns=rf_highcap_router_columns,
            router_x=test_router_x,
            arithmetic_actions=arithmetic_actions,
            linear_actions=linear_actions,
        )
        rf_highcap_margin_routed_actions = _route_actions(
            router=rf_highcap_margin_router_model,
            router_columns=rf_highcap_margin_router_columns,
            router_x=test_router_x,
            arithmetic_actions=arithmetic_actions,
            linear_actions=linear_actions,
        )
        rf_highcap_soft_margin_routed_actions = _route_actions(
            router=rf_highcap_soft_margin_router_model,
            router_columns=rf_highcap_soft_margin_router_columns,
            router_x=test_router_x,
            arithmetic_actions=arithmetic_actions,
            linear_actions=linear_actions,
        )
        gap_router_pred = _regression_predictions(
            gap_router_model,
            gap_router_columns,
            test_router_x,
        )
        rf_gap_router_pred = _regression_predictions(
            rf_gap_router_model,
            rf_gap_router_columns,
            test_router_x,
        )
        gap_routed_actions = [
            linear_actions[index] if float(gap_router_pred[index]) >= 0.0 else arithmetic_actions[index]
            for index in range(len(test_frame))
        ]
        rf_gap_routed_actions = [
            linear_actions[index] if float(rf_gap_router_pred[index]) >= 0.0 else arithmetic_actions[index]
            for index in range(len(test_frame))
        ]
        direct_utility_actions, direct_arith_pred, direct_linear_pred = _direct_utility_actions(
            arithmetic_regressor=direct_utility_models[0],
            linear_regressor=direct_utility_models[1],
            feature_columns=direct_utility_columns,
            router_x=test_router_x,
            arithmetic_actions=arithmetic_actions,
            linear_actions=linear_actions,
        )
        rf_direct_utility_actions, rf_direct_arith_pred, rf_direct_linear_pred = _direct_utility_actions(
            arithmetic_regressor=rf_direct_utility_models[0],
            linear_regressor=rf_direct_utility_models[1],
            feature_columns=rf_direct_utility_columns,
            router_x=test_router_x,
            arithmetic_actions=arithmetic_actions,
            linear_actions=linear_actions,
        )
        margin_routed_actions = _route_actions(
            router=margin_router_model,
            router_columns=margin_router_columns,
            router_x=test_router_x,
            arithmetic_actions=arithmetic_actions,
            linear_actions=linear_actions,
        )
        hard_portfolio_actions = [
            linear_actions[index] if test_frame.iloc[index]["env"] == "linear_equations" else arithmetic_actions[index]
            for index in range(len(test_frame))
        ]
        rf_router_prob = _router_probabilities(
            rf_router_model,
            rf_router_columns,
            test_router_x,
        )
        rf_fallback_conf = np.where(
            test_frame["env_is_linear"].astype(int).to_numpy() == 1,
            1.0 - rf_router_prob,
            rf_router_prob,
        )
        margin_router_prob = _router_probabilities(
            margin_router_model,
            margin_router_columns,
            test_router_x,
        )
        margin_fallback_conf = np.where(
            test_frame["env_is_linear"].astype(int).to_numpy() == 1,
            1.0 - margin_router_prob,
            margin_router_prob,
        )
        margin_fallback_actions = []
        rf_specialist_fallback_actions = []
        gap_fallback_actions = []
        rf_gap_fallback_actions = []
        override_flip = override_model.predict(
            test_router_x.reindex(columns=override_columns, fill_value=0.0).fillna(0.0)
        )
        override_actions = []
        sparse_override_prob = _router_probabilities(
            sparse_override_model,
            sparse_override_columns,
            test_router_x,
        )
        sparse_override_actions = []
        for index in range(len(test_frame)):
            default_action = hard_portfolio_actions[index]
            alt_action = arithmetic_actions[index] if test_frame.iloc[index]["env"] == "linear_equations" else linear_actions[index]
            rf_specialist_fallback_actions.append(
                alt_action
                if float(rf_fallback_conf[index]) >= rf_specialist_fallback_threshold
                else default_action
            )
            gap_fallback_actions.append(
                alt_action
                if (
                    float(gap_router_pred[index]) <= -gap_fallback_threshold
                    if test_frame.iloc[index]["env"] == "linear_equations"
                    else float(gap_router_pred[index]) >= gap_fallback_threshold
                )
                else default_action
            )
            rf_gap_fallback_actions.append(
                alt_action
                if (
                    float(rf_gap_router_pred[index]) <= -rf_gap_fallback_threshold
                    if test_frame.iloc[index]["env"] == "linear_equations"
                    else float(rf_gap_router_pred[index]) >= rf_gap_fallback_threshold
                )
                else default_action
            )
            margin_fallback_actions.append(
                alt_action if float(margin_fallback_conf[index]) >= margin_fallback_threshold else default_action
            )
            override_actions.append(alt_action if int(override_flip[index]) == 1 else default_action)
            sparse_override_actions.append(
                alt_action if float(sparse_override_prob[index]) >= sparse_override_threshold else default_action
            )
        always_arithmetic_metrics = evaluate_policy(test_frame, arithmetic_actions)
        always_linear_metrics = evaluate_policy(test_frame, linear_actions)
        hard_portfolio_metrics = evaluate_policy(test_frame, hard_portfolio_actions)
        learned_router_metrics = evaluate_policy(test_frame, routed_actions)
        rf_router_metrics = evaluate_policy(test_frame, rf_routed_actions)
        rf_highcap_router_metrics = evaluate_policy(test_frame, rf_highcap_routed_actions)
        rf_highcap_margin_router_metrics = evaluate_policy(test_frame, rf_highcap_margin_routed_actions)
        rf_highcap_soft_margin_router_metrics = evaluate_policy(test_frame, rf_highcap_soft_margin_routed_actions)
        rf_specialist_fallback_metrics = evaluate_policy(test_frame, rf_specialist_fallback_actions)
        gap_router_metrics = evaluate_policy(test_frame, gap_routed_actions)
        gap_fallback_metrics = evaluate_policy(test_frame, gap_fallback_actions)
        rf_gap_router_metrics = evaluate_policy(test_frame, rf_gap_routed_actions)
        rf_gap_fallback_metrics = evaluate_policy(test_frame, rf_gap_fallback_actions)
        direct_utility_metrics = evaluate_policy(test_frame, direct_utility_actions)
        rf_direct_utility_metrics = evaluate_policy(test_frame, rf_direct_utility_actions)
        margin_router_metrics = evaluate_policy(test_frame, margin_routed_actions)
        margin_fallback_metrics = evaluate_policy(test_frame, margin_fallback_actions)
        override_router_metrics = evaluate_policy(test_frame, override_actions)
        sparse_override_metrics = evaluate_policy(test_frame, sparse_override_actions)
        arithmetic_utility = _chosen_utilities(test_frame, arithmetic_actions)
        linear_utility = _chosen_utilities(test_frame, linear_actions)
        hard_utility = _chosen_utilities(test_frame, hard_portfolio_actions)
        learned_utility = _chosen_utilities(test_frame, routed_actions)
        rf_router_utility = _chosen_utilities(test_frame, rf_routed_actions)
        rf_highcap_router_utility = _chosen_utilities(test_frame, rf_highcap_routed_actions)
        rf_highcap_margin_router_utility = _chosen_utilities(test_frame, rf_highcap_margin_routed_actions)
        rf_highcap_soft_margin_router_utility = _chosen_utilities(test_frame, rf_highcap_soft_margin_routed_actions)
        rf_specialist_fallback_utility = _chosen_utilities(test_frame, rf_specialist_fallback_actions)
        gap_router_utility = _chosen_utilities(test_frame, gap_routed_actions)
        gap_fallback_utility = _chosen_utilities(test_frame, gap_fallback_actions)
        rf_gap_router_utility = _chosen_utilities(test_frame, rf_gap_routed_actions)
        rf_gap_fallback_utility = _chosen_utilities(test_frame, rf_gap_fallback_actions)
        direct_utility_router_utility = _chosen_utilities(test_frame, direct_utility_actions)
        rf_direct_utility_router_utility = _chosen_utilities(test_frame, rf_direct_utility_actions)
        margin_router_utility = _chosen_utilities(test_frame, margin_routed_actions)
        margin_fallback_utility = _chosen_utilities(test_frame, margin_fallback_actions)
        override_utility = _chosen_utilities(test_frame, override_actions)
        sparse_override_utility = _chosen_utilities(test_frame, sparse_override_actions)
        oracle_prefers_linear = linear_utility > arithmetic_utility
        oracle_is_tie = np.isclose(linear_utility, arithmetic_utility)
        oracle_actions = []
        oracle_utility = np.maximum(arithmetic_utility, linear_utility)
        for index in range(len(test_frame)):
            if oracle_is_tie[index]:
                oracle_actions.append(hard_portfolio_actions[index])
            elif oracle_prefers_linear[index]:
                oracle_actions.append(linear_actions[index])
            else:
                oracle_actions.append(arithmetic_actions[index])
        oracle_metrics = evaluate_policy(test_frame, oracle_actions)

        records.append(
            {
                "baseline": "always_arithmetic_specialist",
                "fold": fold_index,
                "num_train": len(train_frame),
                "num_test": len(test_frame),
                **always_arithmetic_metrics,
            }
        )
        records.append(
            {
                "baseline": "always_linear_specialist",
                "fold": fold_index,
                "num_train": len(train_frame),
                "num_test": len(test_frame),
                **always_linear_metrics,
            }
        )
        records.append(
            {
                "baseline": "hard_specialist_portfolio_predicted_state",
                "fold": fold_index,
                "num_train": len(train_frame),
                "num_test": len(test_frame),
                **hard_portfolio_metrics,
            }
        )
        records.append(
            {
                "baseline": "learned_specialist_router_predicted_state",
                "fold": fold_index,
                "num_train": len(train_frame),
                "num_test": len(test_frame),
                **learned_router_metrics,
            }
        )
        records.append(
            {
                "baseline": "rf_specialist_router_predicted_state",
                "fold": fold_index,
                "num_train": len(train_frame),
                "num_test": len(test_frame),
                **rf_router_metrics,
            }
        )
        records.append(
            {
                "baseline": "rf_high_capacity_specialist_router_predicted_state",
                "fold": fold_index,
                "num_train": len(train_frame),
                "num_test": len(test_frame),
                **rf_highcap_router_metrics,
            }
        )
        records.append(
            {
                "baseline": "rf_high_capacity_margin_specialist_router_predicted_state",
                "fold": fold_index,
                "num_train": len(train_frame),
                "num_test": len(test_frame),
                **rf_highcap_margin_router_metrics,
            }
        )
        records.append(
            {
                "baseline": "rf_high_capacity_soft_margin_specialist_router_predicted_state",
                "fold": fold_index,
                "num_train": len(train_frame),
                "num_test": len(test_frame),
                **rf_highcap_soft_margin_router_metrics,
            }
        )
        records.append(
            {
                "baseline": "rf_specialist_fallback_router_predicted_state",
                "fold": fold_index,
                "num_train": len(train_frame),
                "num_test": len(test_frame),
                **rf_specialist_fallback_metrics,
            }
        )
        records.append(
            {
                "baseline": "utility_gap_specialist_router_predicted_state",
                "fold": fold_index,
                "num_train": len(train_frame),
                "num_test": len(test_frame),
                **gap_router_metrics,
            }
        )
        records.append(
            {
                "baseline": "utility_gap_fallback_specialist_router_predicted_state",
                "fold": fold_index,
                "num_train": len(train_frame),
                "num_test": len(test_frame),
                **gap_fallback_metrics,
            }
        )
        records.append(
            {
                "baseline": "rf_utility_gap_specialist_router_predicted_state",
                "fold": fold_index,
                "num_train": len(train_frame),
                "num_test": len(test_frame),
                **rf_gap_router_metrics,
            }
        )
        records.append(
            {
                "baseline": "rf_utility_gap_fallback_specialist_router_predicted_state",
                "fold": fold_index,
                "num_train": len(train_frame),
                "num_test": len(test_frame),
                **rf_gap_fallback_metrics,
            }
        )
        records.append(
            {
                "baseline": "direct_utility_specialist_router_predicted_state",
                "fold": fold_index,
                "num_train": len(train_frame),
                "num_test": len(test_frame),
                **direct_utility_metrics,
            }
        )
        records.append(
            {
                "baseline": "rf_direct_utility_specialist_router_predicted_state",
                "fold": fold_index,
                "num_train": len(train_frame),
                "num_test": len(test_frame),
                **rf_direct_utility_metrics,
            }
        )
        records.append(
            {
                "baseline": "margin_weighted_specialist_router_predicted_state",
                "fold": fold_index,
                "num_train": len(train_frame),
                "num_test": len(test_frame),
                **margin_router_metrics,
            }
        )
        records.append(
            {
                "baseline": "margin_fallback_specialist_router_predicted_state",
                "fold": fold_index,
                "num_train": len(train_frame),
                "num_test": len(test_frame),
                **margin_fallback_metrics,
            }
        )
        records.append(
            {
                "baseline": "env_override_specialist_router_predicted_state",
                "fold": fold_index,
                "num_train": len(train_frame),
                "num_test": len(test_frame),
                **override_router_metrics,
            }
        )
        records.append(
            {
                "baseline": "oracle_expert_selector_predicted_state",
                "fold": fold_index,
                "num_train": len(train_frame),
                "num_test": len(test_frame),
                **oracle_metrics,
            }
        )
        records.append(
            {
                "baseline": "sparse_override_specialist_router_predicted_state",
                "fold": fold_index,
                "num_train": len(train_frame),
                "num_test": len(test_frame),
                **sparse_override_metrics,
            }
        )
        for index in range(len(test_frame)):
            sample_records.append(
                {
                    "fold": fold_index,
                    "sample_id": str(test_frame.iloc[index][group_column]),
                    "env": str(test_frame.iloc[index]["env"]),
                    "oracle_prefers_linear": int(oracle_prefers_linear[index]),
                    "oracle_is_tie": int(oracle_is_tie[index]),
                    "oracle_margin": float(abs(linear_utility[index] - arithmetic_utility[index])),
                    "arithmetic_action": arithmetic_actions[index],
                    "linear_action": linear_actions[index],
                    "hard_action": hard_portfolio_actions[index],
                    "learned_router_action": routed_actions[index],
                    "rf_router_action": rf_routed_actions[index],
                    "rf_highcap_router_action": rf_highcap_routed_actions[index],
                    "rf_highcap_margin_router_action": rf_highcap_margin_routed_actions[index],
                    "rf_highcap_soft_margin_router_action": rf_highcap_soft_margin_routed_actions[index],
                    "rf_specialist_fallback_action": rf_specialist_fallback_actions[index],
                    "gap_router_action": gap_routed_actions[index],
                    "gap_fallback_action": gap_fallback_actions[index],
                    "rf_gap_router_action": rf_gap_routed_actions[index],
                    "rf_gap_fallback_action": rf_gap_fallback_actions[index],
                    "direct_utility_router_action": direct_utility_actions[index],
                    "rf_direct_utility_router_action": rf_direct_utility_actions[index],
                    "margin_router_action": margin_routed_actions[index],
                    "margin_fallback_action": margin_fallback_actions[index],
                    "override_router_action": override_actions[index],
                    "sparse_override_router_action": sparse_override_actions[index],
                    "oracle_action": oracle_actions[index],
                    "arithmetic_utility": float(arithmetic_utility[index]),
                    "linear_utility": float(linear_utility[index]),
                    "hard_utility": float(hard_utility[index]),
                    "learned_router_utility": float(learned_utility[index]),
                    "rf_router_utility": float(rf_router_utility[index]),
                    "rf_highcap_router_utility": float(rf_highcap_router_utility[index]),
                    "rf_highcap_margin_router_utility": float(rf_highcap_margin_router_utility[index]),
                    "rf_highcap_soft_margin_router_utility": float(rf_highcap_soft_margin_router_utility[index]),
                    "rf_specialist_fallback_utility": float(rf_specialist_fallback_utility[index]),
                    "gap_router_utility": float(gap_router_utility[index]),
                    "gap_fallback_utility": float(gap_fallback_utility[index]),
                    "rf_gap_router_utility": float(rf_gap_router_utility[index]),
                    "rf_gap_fallback_utility": float(rf_gap_fallback_utility[index]),
                    "direct_utility_router_utility": float(direct_utility_router_utility[index]),
                    "rf_direct_utility_router_utility": float(rf_direct_utility_router_utility[index]),
                    "margin_router_utility": float(margin_router_utility[index]),
                    "margin_fallback_utility": float(margin_fallback_utility[index]),
                    "override_router_utility": float(override_utility[index]),
                    "sparse_override_router_utility": float(sparse_override_utility[index]),
                    "oracle_utility": float(oracle_utility[index]),
                    "hard_matches_oracle": int(hard_portfolio_actions[index] == oracle_actions[index]),
                    "learned_router_matches_oracle": int(routed_actions[index] == oracle_actions[index]),
                    "rf_router_matches_oracle": int(rf_routed_actions[index] == oracle_actions[index]),
                    "rf_highcap_router_matches_oracle": int(
                        rf_highcap_routed_actions[index] == oracle_actions[index]
                    ),
                    "rf_highcap_margin_router_matches_oracle": int(
                        rf_highcap_margin_routed_actions[index] == oracle_actions[index]
                    ),
                    "rf_highcap_soft_margin_router_matches_oracle": int(
                        rf_highcap_soft_margin_routed_actions[index] == oracle_actions[index]
                    ),
                    "rf_specialist_fallback_matches_oracle": int(
                        rf_specialist_fallback_actions[index] == oracle_actions[index]
                    ),
                    "gap_router_matches_oracle": int(gap_routed_actions[index] == oracle_actions[index]),
                    "gap_fallback_matches_oracle": int(gap_fallback_actions[index] == oracle_actions[index]),
                    "rf_gap_router_matches_oracle": int(rf_gap_routed_actions[index] == oracle_actions[index]),
                    "rf_gap_fallback_matches_oracle": int(rf_gap_fallback_actions[index] == oracle_actions[index]),
                    "direct_utility_router_matches_oracle": int(
                        direct_utility_actions[index] == oracle_actions[index]
                    ),
                    "rf_direct_utility_router_matches_oracle": int(
                        rf_direct_utility_actions[index] == oracle_actions[index]
                    ),
                    "margin_router_matches_oracle": int(margin_routed_actions[index] == oracle_actions[index]),
                    "margin_fallback_matches_oracle": int(margin_fallback_actions[index] == oracle_actions[index]),
                    "override_router_matches_oracle": int(override_actions[index] == oracle_actions[index]),
                    "sparse_override_router_matches_oracle": int(
                        sparse_override_actions[index] == oracle_actions[index]
                    ),
                    "gap_fallback_threshold": float(gap_fallback_threshold),
                    "rf_specialist_fallback_threshold": float(rf_specialist_fallback_threshold),
                    "rf_router_prob": float(rf_router_prob[index]),
                    "rf_fallback_conf": float(rf_fallback_conf[index]),
                    "gap_router_pred": float(gap_router_pred[index]),
                    "rf_gap_fallback_threshold": float(rf_gap_fallback_threshold),
                    "rf_gap_router_pred": float(rf_gap_router_pred[index]),
                    "direct_utility_router_arithmetic_pred": float(direct_arith_pred[index]),
                    "direct_utility_router_linear_pred": float(direct_linear_pred[index]),
                    "rf_direct_utility_router_arithmetic_pred": float(rf_direct_arith_pred[index]),
                    "rf_direct_utility_router_linear_pred": float(rf_direct_linear_pred[index]),
                    "margin_fallback_threshold": float(margin_fallback_threshold),
                    "margin_router_prob": float(margin_router_prob[index]),
                    "margin_fallback_conf": float(margin_fallback_conf[index]),
                    "sparse_override_threshold": float(sparse_override_threshold),
                    "sparse_override_prob": float(sparse_override_prob[index]),
                }
            )
    return pd.DataFrame(records), pd.DataFrame(sample_records)


def run_rf_highcap_family_cv(
    merged_frame: pd.DataFrame,
    q_embedding_columns: list[str],
    s_embedding_columns: list[str],
    group_column: str,
    n_splits: int,
    state_mode: str,
    state_head_model: str,
    include_env_feature: bool,
    arithmetic_specialist_model: str,
    linear_specialist_model: str,
    router_cache_dir: Path | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    unique_groups = merged_frame[group_column].nunique()
    effective_splits = min(n_splits, unique_groups)
    if effective_splits < 2:
        raise ValueError("Need at least 2 groups for cross-validation")

    splitter = GroupKFold(n_splits=effective_splits)
    records: list[dict[str, float | int | str]] = []
    sample_records: list[dict[str, float | int | str]] = []
    for fold_index, (train_index, test_index) in enumerate(
        splitter.split(merged_frame, groups=merged_frame[group_column]),
        start=1,
    ):
        train_frame = merged_frame.iloc[train_index].reset_index(drop=True)
        test_frame = merged_frame.iloc[test_index].reset_index(drop=True)
        cache_payload = (
            _load_rf_highcap_fold_cache(router_cache_dir, fold_index) if router_cache_dir is not None else None
        )
        if cache_payload is None:
            (
                router_x,
                router_y,
                router_margin,
                _utility_gap_train,
                _arithmetic_utility_train,
                _linear_utility_train,
                _override_y,
                _default_utility_train,
                _alt_utility_train,
                _default_is_linear_train,
            ) = _build_router_training_set(
                train_frame=train_frame,
                q_embedding_columns=q_embedding_columns,
                s_embedding_columns=s_embedding_columns,
                group_column=group_column,
                state_mode=state_mode,
                state_head_model=state_head_model,
                include_env_feature=include_env_feature,
                arithmetic_specialist_model=arithmetic_specialist_model,
                linear_specialist_model=linear_specialist_model,
            )
            arithmetic_train = train_frame.loc[train_frame["env"] == "arithmetic"].reset_index(drop=True)
            linear_train = train_frame.loc[train_frame["env"] == "linear_equations"].reset_index(drop=True)
            arithmetic_state, arithmetic_actions, arithmetic_scores = _fit_and_apply_specialist(
                train_frame=arithmetic_train,
                eval_frame=test_frame,
                q_embedding_columns=q_embedding_columns,
                s_embedding_columns=s_embedding_columns,
                state_mode=state_mode,
                state_head_model=state_head_model,
                group_column=group_column,
                env_name="arithmetic",
                specialist_model=arithmetic_specialist_model,
            )
            linear_state, linear_actions, linear_scores = _fit_and_apply_specialist(
                train_frame=linear_train,
                eval_frame=test_frame,
                q_embedding_columns=q_embedding_columns,
                s_embedding_columns=s_embedding_columns,
                state_mode=state_mode,
                state_head_model=state_head_model,
                group_column=group_column,
                env_name="linear_equations",
                specialist_model=linear_specialist_model,
            )
            test_router_x = _router_feature_frame(
                base_frame=test_frame,
                arithmetic_state=arithmetic_state,
                linear_state=linear_state,
                arithmetic_actions=arithmetic_actions,
                linear_actions=linear_actions,
                arithmetic_scores=arithmetic_scores,
                linear_scores=linear_scores,
                state_mode=state_mode,
                include_env_feature=include_env_feature,
            )
            hard_portfolio_actions = [
                linear_actions[index] if test_frame.iloc[index]["env"] == "linear_equations" else arithmetic_actions[index]
                for index in range(len(test_frame))
            ]
            arithmetic_utility = _chosen_utilities(test_frame, arithmetic_actions)
            linear_utility = _chosen_utilities(test_frame, linear_actions)
            hard_utility = _chosen_utilities(test_frame, hard_portfolio_actions)
            oracle_prefers_linear = linear_utility > arithmetic_utility
            oracle_is_tie = np.isclose(linear_utility, arithmetic_utility)
            oracle_actions = []
            oracle_utility = np.maximum(arithmetic_utility, linear_utility)
            for index in range(len(test_frame)):
                if oracle_is_tie[index]:
                    oracle_actions.append(hard_portfolio_actions[index])
                elif oracle_prefers_linear[index]:
                    oracle_actions.append(linear_actions[index])
                else:
                    oracle_actions.append(arithmetic_actions[index])

            train_targets = pd.DataFrame(
                {
                    "router_y": router_y.astype(int),
                    "router_margin": router_margin.astype(float),
                }
            )
            test_support = test_frame[
                [group_column, "env", "env_is_linear", "oracle_action", *UTILITY_COLUMNS.values()]
            ].copy()
            test_support["arithmetic_action"] = arithmetic_actions
            test_support["linear_action"] = linear_actions
            test_support["hard_action"] = hard_portfolio_actions
            test_support["oracle_prefers_linear"] = oracle_prefers_linear.astype(int)
            test_support["oracle_is_tie"] = oracle_is_tie.astype(int)
            test_support["oracle_margin"] = np.abs(linear_utility - arithmetic_utility)
            test_support["arithmetic_utility_eval"] = arithmetic_utility
            test_support["linear_utility_eval"] = linear_utility
            test_support["hard_utility"] = hard_utility
            test_support["oracle_utility"] = oracle_utility

            if router_cache_dir is not None:
                _save_rf_highcap_fold_cache(
                    cache_dir=router_cache_dir,
                    fold_index=fold_index,
                    train_router_x=router_x,
                    train_targets=train_targets,
                    test_router_x=test_router_x,
                    test_support=test_support,
                )
        else:
            router_x = cache_payload["train_router_x"]
            train_targets = cache_payload["train_targets"]
            test_router_x = cache_payload["test_router_x"]
            test_support = cache_payload["test_support"].reset_index(drop=True)
            router_y = train_targets["router_y"].to_numpy(dtype=int)
            router_margin = train_targets["router_margin"].to_numpy(dtype=float)

        margin_router_weight = np.maximum(router_margin, 0.0)
        soft_margin_router_weight = 1.0 + margin_router_weight

        rf_router_model, rf_router_columns = _fit_rf_router(router_x, router_y)
        rf_highcap_router_model, rf_highcap_router_columns = _fit_rf_router_high_capacity(router_x, router_y)
        rf_highcap_extratrees_router_model, rf_highcap_extratrees_router_columns = (
            _fit_rf_router_high_capacity_extra_trees(router_x, router_y)
        )
        (
            rf_highcap_extratrees_fullfeat_router_model,
            rf_highcap_extratrees_fullfeat_router_columns,
        ) = _fit_rf_router_high_capacity_extra_trees_full_features(router_x, router_y)
        rf_highcap_margin_router_model, rf_highcap_margin_router_columns = _fit_rf_router_high_capacity(
            router_x,
            router_y,
            sample_weight=margin_router_weight,
        )
        rf_highcap_soft_margin_router_model, rf_highcap_soft_margin_router_columns = _fit_rf_router_high_capacity(
            router_x,
            router_y,
            sample_weight=soft_margin_router_weight,
        )

        arithmetic_actions = test_support["arithmetic_action"].tolist()
        linear_actions = test_support["linear_action"].tolist()
        hard_portfolio_actions = test_support["hard_action"].tolist()
        oracle_actions = test_support["oracle_action"].tolist()
        oracle_prefers_linear = test_support["oracle_prefers_linear"].to_numpy(dtype=int).astype(bool)
        oracle_is_tie = test_support["oracle_is_tie"].to_numpy(dtype=int).astype(bool)
        arithmetic_utility = test_support["arithmetic_utility_eval"].to_numpy(dtype=float)
        linear_utility = test_support["linear_utility_eval"].to_numpy(dtype=float)
        hard_utility = test_support["hard_utility"].to_numpy(dtype=float)
        oracle_utility = test_support["oracle_utility"].to_numpy(dtype=float)

        rf_routed_actions = _route_actions(
            router=rf_router_model,
            router_columns=rf_router_columns,
            router_x=test_router_x,
            arithmetic_actions=arithmetic_actions,
            linear_actions=linear_actions,
        )
        rf_highcap_routed_actions = _route_actions(
            router=rf_highcap_router_model,
            router_columns=rf_highcap_router_columns,
            router_x=test_router_x,
            arithmetic_actions=arithmetic_actions,
            linear_actions=linear_actions,
        )
        rf_highcap_extratrees_routed_actions = _route_actions(
            router=rf_highcap_extratrees_router_model,
            router_columns=rf_highcap_extratrees_router_columns,
            router_x=test_router_x,
            arithmetic_actions=arithmetic_actions,
            linear_actions=linear_actions,
        )
        rf_highcap_extratrees_fullfeat_routed_actions = _route_actions(
            router=rf_highcap_extratrees_fullfeat_router_model,
            router_columns=rf_highcap_extratrees_fullfeat_router_columns,
            router_x=test_router_x,
            arithmetic_actions=arithmetic_actions,
            linear_actions=linear_actions,
        )
        rf_highcap_margin_routed_actions = _route_actions(
            router=rf_highcap_margin_router_model,
            router_columns=rf_highcap_margin_router_columns,
            router_x=test_router_x,
            arithmetic_actions=arithmetic_actions,
            linear_actions=linear_actions,
        )
        rf_highcap_soft_margin_routed_actions = _route_actions(
            router=rf_highcap_soft_margin_router_model,
            router_columns=rf_highcap_soft_margin_router_columns,
            router_x=test_router_x,
            arithmetic_actions=arithmetic_actions,
            linear_actions=linear_actions,
        )

        hard_portfolio_metrics = evaluate_policy(test_support, hard_portfolio_actions)
        rf_router_metrics = evaluate_policy(test_support, rf_routed_actions)
        rf_highcap_router_metrics = evaluate_policy(test_support, rf_highcap_routed_actions)
        rf_highcap_extratrees_router_metrics = evaluate_policy(test_support, rf_highcap_extratrees_routed_actions)
        rf_highcap_extratrees_fullfeat_router_metrics = evaluate_policy(
            test_support, rf_highcap_extratrees_fullfeat_routed_actions
        )
        rf_highcap_margin_router_metrics = evaluate_policy(test_support, rf_highcap_margin_routed_actions)
        rf_highcap_soft_margin_router_metrics = evaluate_policy(test_support, rf_highcap_soft_margin_routed_actions)

        rf_router_utility = _chosen_utilities(test_support, rf_routed_actions)
        rf_highcap_router_utility = _chosen_utilities(test_support, rf_highcap_routed_actions)
        rf_highcap_extratrees_router_utility = _chosen_utilities(
            test_support, rf_highcap_extratrees_routed_actions
        )
        rf_highcap_extratrees_fullfeat_router_utility = _chosen_utilities(
            test_support, rf_highcap_extratrees_fullfeat_routed_actions
        )
        rf_highcap_margin_router_utility = _chosen_utilities(test_support, rf_highcap_margin_routed_actions)
        rf_highcap_soft_margin_router_utility = _chosen_utilities(test_support, rf_highcap_soft_margin_routed_actions)
        oracle_metrics = evaluate_policy(test_support, oracle_actions)

        for baseline, metrics in [
            ("hard_specialist_portfolio_predicted_state", hard_portfolio_metrics),
            ("rf_specialist_router_predicted_state", rf_router_metrics),
            ("rf_high_capacity_specialist_router_predicted_state", rf_highcap_router_metrics),
            ("rf_high_capacity_extra_trees_specialist_router_predicted_state", rf_highcap_extratrees_router_metrics),
            (
                "rf_high_capacity_extra_trees_full_features_specialist_router_predicted_state",
                rf_highcap_extratrees_fullfeat_router_metrics,
            ),
            ("rf_high_capacity_margin_specialist_router_predicted_state", rf_highcap_margin_router_metrics),
            ("rf_high_capacity_soft_margin_specialist_router_predicted_state", rf_highcap_soft_margin_router_metrics),
            ("oracle_expert_selector_predicted_state", oracle_metrics),
        ]:
            records.append(
                {
                    "baseline": baseline,
                    "fold": fold_index,
                    "num_train": len(train_frame),
                    "num_test": len(test_frame),
                    **metrics,
                }
            )

        for index in range(len(test_frame)):
            sample_records.append(
                {
                    "fold": fold_index,
                    "sample_id": str(test_support.iloc[index][group_column]),
                    "env": str(test_support.iloc[index]["env"]),
                    "oracle_prefers_linear": int(oracle_prefers_linear[index]),
                    "oracle_is_tie": int(oracle_is_tie[index]),
                    "oracle_margin": float(abs(linear_utility[index] - arithmetic_utility[index])),
                    "arithmetic_action": arithmetic_actions[index],
                    "linear_action": linear_actions[index],
                    "hard_action": hard_portfolio_actions[index],
                    "rf_router_action": rf_routed_actions[index],
                    "rf_highcap_router_action": rf_highcap_routed_actions[index],
                    "rf_highcap_extratrees_router_action": rf_highcap_extratrees_routed_actions[index],
                    "rf_highcap_extratrees_fullfeat_router_action": rf_highcap_extratrees_fullfeat_routed_actions[
                        index
                    ],
                    "rf_highcap_margin_router_action": rf_highcap_margin_routed_actions[index],
                    "rf_highcap_soft_margin_router_action": rf_highcap_soft_margin_routed_actions[index],
                    "oracle_action": oracle_actions[index],
                    "arithmetic_utility": float(arithmetic_utility[index]),
                    "linear_utility": float(linear_utility[index]),
                    "hard_utility": float(hard_utility[index]),
                    "rf_router_utility": float(rf_router_utility[index]),
                    "rf_highcap_router_utility": float(rf_highcap_router_utility[index]),
                    "rf_highcap_extratrees_router_utility": float(rf_highcap_extratrees_router_utility[index]),
                    "rf_highcap_extratrees_fullfeat_router_utility": float(
                        rf_highcap_extratrees_fullfeat_router_utility[index]
                    ),
                    "rf_highcap_margin_router_utility": float(rf_highcap_margin_router_utility[index]),
                    "rf_highcap_soft_margin_router_utility": float(rf_highcap_soft_margin_router_utility[index]),
                    "oracle_utility": float(oracle_utility[index]),
                    "hard_matches_oracle": int(hard_portfolio_actions[index] == oracle_actions[index]),
                    "rf_router_matches_oracle": int(rf_routed_actions[index] == oracle_actions[index]),
                    "rf_highcap_router_matches_oracle": int(
                        rf_highcap_routed_actions[index] == oracle_actions[index]
                    ),
                    "rf_highcap_extratrees_router_matches_oracle": int(
                        rf_highcap_extratrees_routed_actions[index] == oracle_actions[index]
                    ),
                    "rf_highcap_extratrees_fullfeat_router_matches_oracle": int(
                        rf_highcap_extratrees_fullfeat_routed_actions[index] == oracle_actions[index]
                    ),
                    "rf_highcap_margin_router_matches_oracle": int(
                        rf_highcap_margin_routed_actions[index] == oracle_actions[index]
                    ),
                    "rf_highcap_soft_margin_router_matches_oracle": int(
                        rf_highcap_soft_margin_routed_actions[index] == oracle_actions[index]
                    ),
                }
            )
    return pd.DataFrame(records), pd.DataFrame(sample_records)


def _mean_or_nan(frame: pd.DataFrame, column: str) -> float:
    if column not in frame.columns:
        return float("nan")
    return float(frame[column].mean())


def _oracle_gap_or_nan(frame: pd.DataFrame, utility_column: str) -> float:
    if utility_column not in frame.columns:
        return float("nan")
    return float((frame["oracle_utility"] - frame[utility_column]).mean())


def _rf_highcap_cache_paths(cache_dir: Path, fold_index: int) -> dict[str, Path]:
    fold_dir = cache_dir / f"fold_{fold_index:02d}"
    return {
        "fold_dir": fold_dir,
        "train_router_x": fold_dir / "train_router_x.pkl",
        "train_targets": fold_dir / "train_targets.pkl",
        "test_router_x": fold_dir / "test_router_x.pkl",
        "test_support": fold_dir / "test_support.pkl",
    }


def _load_rf_highcap_fold_cache(cache_dir: Path, fold_index: int) -> dict[str, pd.DataFrame] | None:
    paths = _rf_highcap_cache_paths(cache_dir, fold_index)
    required = [paths["train_router_x"], paths["train_targets"], paths["test_router_x"], paths["test_support"]]
    if not all(path.exists() for path in required):
        return None
    return {
        "train_router_x": pd.read_pickle(paths["train_router_x"]),
        "train_targets": pd.read_pickle(paths["train_targets"]),
        "test_router_x": pd.read_pickle(paths["test_router_x"]),
        "test_support": pd.read_pickle(paths["test_support"]),
    }


def _save_rf_highcap_fold_cache(
    cache_dir: Path,
    fold_index: int,
    train_router_x: pd.DataFrame,
    train_targets: pd.DataFrame,
    test_router_x: pd.DataFrame,
    test_support: pd.DataFrame,
) -> None:
    paths = _rf_highcap_cache_paths(cache_dir, fold_index)
    paths["fold_dir"].mkdir(parents=True, exist_ok=True)
    train_router_x.to_pickle(paths["train_router_x"])
    train_targets.to_pickle(paths["train_targets"])
    test_router_x.to_pickle(paths["test_router_x"])
    test_support.to_pickle(paths["test_support"])


def summarize_router_diagnostics(sample_results: pd.DataFrame) -> pd.DataFrame:
    scopes = [("all", sample_results)]
    for env_name in sorted(sample_results["env"].unique()):
        scopes.append((env_name, sample_results.loc[sample_results["env"] == env_name].reset_index(drop=True)))

    rows: list[dict[str, float | int | str]] = []
    for scope_name, scope_frame in scopes:
        rows.append(
            {
                "scope": scope_name,
                "num_samples": len(scope_frame),
                "oracle_prefers_linear_rate": float(scope_frame["oracle_prefers_linear"].mean()),
                "oracle_tie_rate": float(scope_frame["oracle_is_tie"].mean()),
                "mean_oracle_margin": float(scope_frame["oracle_margin"].mean()),
                "hard_matches_oracle_rate": _mean_or_nan(scope_frame, "hard_matches_oracle"),
                "learned_router_matches_oracle_rate": _mean_or_nan(scope_frame, "learned_router_matches_oracle"),
                "rf_router_matches_oracle_rate": _mean_or_nan(scope_frame, "rf_router_matches_oracle"),
                "rf_highcap_router_matches_oracle_rate": _mean_or_nan(
                    scope_frame, "rf_highcap_router_matches_oracle"
                ),
                "rf_highcap_extratrees_router_matches_oracle_rate": _mean_or_nan(
                    scope_frame, "rf_highcap_extratrees_router_matches_oracle"
                ),
                "rf_highcap_extratrees_fullfeat_router_matches_oracle_rate": _mean_or_nan(
                    scope_frame, "rf_highcap_extratrees_fullfeat_router_matches_oracle"
                ),
                "rf_highcap_margin_router_matches_oracle_rate": _mean_or_nan(
                    scope_frame, "rf_highcap_margin_router_matches_oracle"
                ),
                "rf_highcap_soft_margin_router_matches_oracle_rate": _mean_or_nan(
                    scope_frame, "rf_highcap_soft_margin_router_matches_oracle"
                ),
                "rf_specialist_fallback_matches_oracle_rate": _mean_or_nan(
                    scope_frame, "rf_specialist_fallback_matches_oracle"
                ),
                "gap_router_matches_oracle_rate": _mean_or_nan(scope_frame, "gap_router_matches_oracle"),
                "gap_fallback_matches_oracle_rate": _mean_or_nan(scope_frame, "gap_fallback_matches_oracle"),
                "rf_gap_router_matches_oracle_rate": _mean_or_nan(scope_frame, "rf_gap_router_matches_oracle"),
                "rf_gap_fallback_matches_oracle_rate": _mean_or_nan(
                    scope_frame, "rf_gap_fallback_matches_oracle"
                ),
                "direct_utility_router_matches_oracle_rate": _mean_or_nan(
                    scope_frame, "direct_utility_router_matches_oracle"
                ),
                "rf_direct_utility_router_matches_oracle_rate": _mean_or_nan(
                    scope_frame, "rf_direct_utility_router_matches_oracle"
                ),
                "margin_router_matches_oracle_rate": _mean_or_nan(scope_frame, "margin_router_matches_oracle"),
                "margin_fallback_matches_oracle_rate": _mean_or_nan(
                    scope_frame, "margin_fallback_matches_oracle"
                ),
                "override_router_matches_oracle_rate": _mean_or_nan(
                    scope_frame, "override_router_matches_oracle"
                ),
                "sparse_override_router_matches_oracle_rate": _mean_or_nan(
                    scope_frame, "sparse_override_router_matches_oracle"
                ),
                "hard_to_oracle_utility_gap": _oracle_gap_or_nan(scope_frame, "hard_utility"),
                "learned_to_oracle_utility_gap": _oracle_gap_or_nan(scope_frame, "learned_router_utility"),
                "rf_router_to_oracle_utility_gap": _oracle_gap_or_nan(scope_frame, "rf_router_utility"),
                "rf_highcap_router_to_oracle_utility_gap": _oracle_gap_or_nan(
                    scope_frame, "rf_highcap_router_utility"
                ),
                "rf_highcap_extratrees_router_to_oracle_utility_gap": _oracle_gap_or_nan(
                    scope_frame, "rf_highcap_extratrees_router_utility"
                ),
                "rf_highcap_extratrees_fullfeat_router_to_oracle_utility_gap": _oracle_gap_or_nan(
                    scope_frame, "rf_highcap_extratrees_fullfeat_router_utility"
                ),
                "rf_highcap_margin_router_to_oracle_utility_gap": _oracle_gap_or_nan(
                    scope_frame, "rf_highcap_margin_router_utility"
                ),
                "rf_highcap_soft_margin_router_to_oracle_utility_gap": _oracle_gap_or_nan(
                    scope_frame, "rf_highcap_soft_margin_router_utility"
                ),
                "rf_specialist_fallback_to_oracle_utility_gap": _oracle_gap_or_nan(
                    scope_frame, "rf_specialist_fallback_utility"
                ),
                "gap_router_to_oracle_utility_gap": _oracle_gap_or_nan(scope_frame, "gap_router_utility"),
                "gap_fallback_to_oracle_utility_gap": _oracle_gap_or_nan(scope_frame, "gap_fallback_utility"),
                "rf_gap_router_to_oracle_utility_gap": _oracle_gap_or_nan(
                    scope_frame, "rf_gap_router_utility"
                ),
                "rf_gap_fallback_to_oracle_utility_gap": _oracle_gap_or_nan(
                    scope_frame, "rf_gap_fallback_utility"
                ),
                "direct_utility_router_to_oracle_utility_gap": _oracle_gap_or_nan(
                    scope_frame, "direct_utility_router_utility"
                ),
                "rf_direct_utility_router_to_oracle_utility_gap": _oracle_gap_or_nan(
                    scope_frame, "rf_direct_utility_router_utility"
                ),
                "margin_router_to_oracle_utility_gap": _oracle_gap_or_nan(
                    scope_frame, "margin_router_utility"
                ),
                "margin_fallback_to_oracle_utility_gap": _oracle_gap_or_nan(
                    scope_frame, "margin_fallback_utility"
                ),
                "override_to_oracle_utility_gap": _oracle_gap_or_nan(scope_frame, "override_router_utility"),
                "sparse_override_to_oracle_utility_gap": _oracle_gap_or_nan(
                    scope_frame, "sparse_override_router_utility"
                ),
                "mean_gap_fallback_threshold": _mean_or_nan(scope_frame, "gap_fallback_threshold"),
                "mean_rf_specialist_fallback_threshold": _mean_or_nan(
                    scope_frame, "rf_specialist_fallback_threshold"
                ),
                "mean_rf_gap_fallback_threshold": _mean_or_nan(scope_frame, "rf_gap_fallback_threshold"),
                "mean_margin_fallback_threshold": _mean_or_nan(scope_frame, "margin_fallback_threshold"),
                "mean_sparse_override_threshold": _mean_or_nan(scope_frame, "sparse_override_threshold"),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    arithmetic_frame, arithmetic_q_cols, arithmetic_s_cols = _load_domain_frame(
        args.arithmetic_input_csv,
        args.arithmetic_embedding_npz,
        "arithmetic",
        args.group_column,
    )
    linear_frame, linear_q_cols, linear_s_cols = _load_domain_frame(
        args.linear_input_csv,
        args.linear_embedding_npz,
        "linear_equations",
        args.group_column,
    )
    if arithmetic_q_cols != linear_q_cols or arithmetic_s_cols != linear_s_cols:
        raise ValueError("Embedding column layouts must match across domains for pooled experiments")

    merged_frame = pd.concat([arithmetic_frame, linear_frame], ignore_index=True)
    if args.router_family_mode == "rf_highcap_only":
        results, sample_results = run_rf_highcap_family_cv(
            merged_frame=merged_frame,
            q_embedding_columns=arithmetic_q_cols,
            s_embedding_columns=arithmetic_s_cols,
            group_column=args.group_column,
            n_splits=args.n_splits,
            state_mode=args.state_mode,
            state_head_model=args.state_head_model,
            include_env_feature=args.include_env_feature,
            arithmetic_specialist_model=args.arithmetic_specialist_model,
            linear_specialist_model=args.linear_specialist_model,
            router_cache_dir=Path(args.router_cache_dir) if args.router_cache_dir else None,
        )
    else:
        results, sample_results = run_router_cv(
            merged_frame=merged_frame,
            q_embedding_columns=arithmetic_q_cols,
            s_embedding_columns=arithmetic_s_cols,
            group_column=args.group_column,
            n_splits=args.n_splits,
            state_mode=args.state_mode,
            state_head_model=args.state_head_model,
            include_env_feature=args.include_env_feature,
            arithmetic_specialist_model=args.arithmetic_specialist_model,
            linear_specialist_model=args.linear_specialist_model,
        )
    diagnostics_summary = summarize_router_diagnostics(sample_results)
    summary = (
        results.groupby("baseline", as_index=False)[
            ["oracle_action_accuracy", "mean_action_regret", "mean_chosen_utility"]
        ]
        .mean()
        .sort_values("mean_action_regret", ascending=True)
        .reset_index(drop=True)
    )
    summary["state_mode"] = args.state_mode
    summary["state_head_model"] = args.state_head_model
    summary["router_model"] = "logistic"
    summary["router_family_mode"] = args.router_family_mode
    summary["env_conditioning"] = "enabled" if args.include_env_feature else "disabled"
    summary["portfolio_arithmetic_model"] = args.arithmetic_specialist_model
    summary["portfolio_linear_model"] = args.linear_specialist_model

    results.to_csv(output_dir / "router_cv_results.csv", index=False)
    sample_results.to_csv(output_dir / "router_sample_results.csv", index=False)
    summary.to_csv(output_dir / "router_summary.csv", index=False)
    diagnostics_summary.to_csv(output_dir / "router_diagnostics_summary.csv", index=False)
    with (output_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "summary": summary.to_dict(orient="records"),
                "diagnostics_summary": diagnostics_summary.to_dict(orient="records"),
            },
            handle,
            ensure_ascii=False,
            indent=2,
        )

    print(summary.to_string(index=False))
    print()
    print(diagnostics_summary.to_string(index=False))


if __name__ == "__main__":
    main()
