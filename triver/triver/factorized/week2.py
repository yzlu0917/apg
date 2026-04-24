from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import ElasticNet, HuberRegressor, LogisticRegression, Ridge
from sklearn.metrics import mean_squared_error, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures
from sklearn.preprocessing import StandardScaler

from triver.baselines.week2 import ACTIONS, UTILITY_COLUMNS, build_policy_sample_records, evaluate_policy


EMBEDDING_PREFIX = "emb_"
BASE_CONTEXT_COLUMNS = ["budget_tokens", "prefix_length", "is_perturbed", "env_is_linear"]
PAIRWISE_VALUE_MODELS = {"pairwise_logit", "pairwise_interaction_logit"}
LOWRANK_VALUE_MODELS = {
    "lowrank_heteroscedastic_interaction": 1,
    "rank2_lowrank_heteroscedastic_interaction": 2,
}
STATE_MODE_CONFIG = {
    "legacy": {
        "exact_columns": ["q_t", "mu_continue", "nu_continue", *BASE_CONTEXT_COLUMNS],
        "pred_columns": ["q_hat", "mu_hat", "nu_hat", *BASE_CONTEXT_COLUMNS],
        "state_targets": [
            ("mu_continue", "mu_hat", 0.0, 1.0),
            ("nu_continue", "nu_hat", 0.0, 0.25),
        ],
    },
    "s_proxy": {
        "exact_columns": [
            "q_t",
            "mu_continue",
            "nu_continue",
            "continue_std_utility",
            "continue_wrong_rate",
            "continue_mean_tokens",
            *BASE_CONTEXT_COLUMNS,
        ],
        "pred_columns": [
            "q_hat",
            "mu_hat",
            "nu_hat",
            "u_std_hat",
            "wrong_hat",
            "tok_hat",
            *BASE_CONTEXT_COLUMNS,
        ],
        "state_targets": [
            ("mu_continue", "mu_hat", 0.0, 1.0),
            ("nu_continue", "nu_hat", 0.0, 0.25),
            ("continue_std_utility", "u_std_hat", 0.0, None),
            ("continue_wrong_rate", "wrong_hat", 0.0, 1.0),
            ("continue_mean_tokens", "tok_hat", 0.0, None),
        ],
    },
}


@dataclass(frozen=True)
class StateHeadBundle:
    q_head: object | None
    regressors: dict[str, object]


@dataclass(frozen=True)
class ActionValueBundle:
    model_kind: str
    regressors: dict[str, object]
    metadata: dict[str, object] | None = None


@dataclass(frozen=True)
class ConstantRegressor:
    value: float

    def predict(self, features: pd.DataFrame | np.ndarray) -> np.ndarray:
        return np.full(len(features), self.value, dtype=float)


@dataclass(frozen=True)
class ConstantBinaryClassifier:
    prob_one: float

    def predict_proba(self, features: pd.DataFrame | np.ndarray) -> np.ndarray:
        prob = np.clip(self.prob_one, 0.0, 1.0)
        probs = np.full(len(features), prob, dtype=float)
        return np.column_stack([1.0 - probs, probs])


@dataclass(frozen=True)
class ConstantLabelModel:
    label: int

    def predict(self, features: pd.DataFrame | np.ndarray) -> np.ndarray:
        return np.full(len(features), self.label, dtype=int)


def infer_embedding_columns(frame: pd.DataFrame, prefix: str = EMBEDDING_PREFIX) -> list[str]:
    return [column for column in frame.columns if column.startswith(prefix)]


def ensure_base_context_columns(frame: pd.DataFrame) -> pd.DataFrame:
    ensured = frame.copy()
    for column in BASE_CONTEXT_COLUMNS:
        if column not in ensured.columns:
            ensured[column] = 0.0
    return ensured


def state_mode_feature_columns(state_mode: str) -> tuple[list[str], list[str]]:
    config = STATE_MODE_CONFIG[state_mode]
    return list(config["exact_columns"]), list(config["pred_columns"])


def state_uncertainty_columns(state_mode: str) -> list[str]:
    columns = ["q_hat_std"]
    columns.extend(f"{pred_column}_std" for _, pred_column, _, _ in STATE_MODE_CONFIG[state_mode]["state_targets"])
    return columns


def _base_value_head_model(value_head_model: str) -> str:
    if value_head_model.startswith("uncertainty_"):
        return value_head_model[len("uncertainty_") :]
    return value_head_model


def _uses_uncertainty_features(value_head_model: str) -> bool:
    return value_head_model.startswith("uncertainty_")


def _lowrank_model_rank(value_head_model: str) -> int | None:
    return LOWRANK_VALUE_MODELS.get(_base_value_head_model(value_head_model))


def _pca_components(num_samples: int, num_features: int) -> int | None:
    max_components = min(16, num_samples - 1, num_features)
    return max_components if max_components >= 2 else None


def requires_uncertainty_features(value_head_model: str) -> bool:
    return _uses_uncertainty_features(value_head_model) or value_head_model in {
        "joint_pairwise_gate",
        "pairwise_error_calibrated",
        "conditional_lowrank_pairwise_error_calibrated",
        "conditional_lowrank_selective_pairwise_error_calibrated",
        "conditional_lowrank_capped_pairwise_error_calibrated",
        "conditional_lowrank_banded_pairwise_error_calibrated",
        "conditional_lowrank_clustered_pairwise_error_calibrated",
        "pairwise_meta_calibrated",
        "pairwise_selective_calibrated",
    }


def _build_q_head(state_head_model: str, num_samples: int, num_features: int) -> object:
    if state_head_model == "linear":
        return Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                ("logreg", LogisticRegression(max_iter=2000)),
            ]
        )
    if state_head_model in {"pca_ridge", "pca_enet"}:
        steps: list[tuple[str, object]] = [("scaler", StandardScaler())]
        n_components = _pca_components(num_samples, num_features)
        if n_components is not None:
            steps.append(("pca", PCA(n_components=n_components)))
        steps.append(("logreg", LogisticRegression(max_iter=4000, class_weight="balanced", C=0.5)))
        return Pipeline(steps=steps)
    if state_head_model == "rf":
        return RandomForestClassifier(
            n_estimators=200,
            max_depth=6,
            min_samples_leaf=2,
            random_state=0,
            class_weight="balanced",
        )
    raise ValueError(f"Unsupported state_head_model: {state_head_model}")


def _build_state_regressor(state_head_model: str, num_samples: int, num_features: int) -> object:
    if state_head_model in {"linear", "pca_ridge"}:
        steps: list[tuple[str, object]] = [("scaler", StandardScaler())]
        if state_head_model == "pca_ridge":
            n_components = _pca_components(num_samples, num_features)
            if n_components is not None:
                steps.append(("pca", PCA(n_components=n_components)))
        steps.append(("ridge", Ridge(alpha=1.0)))
        return Pipeline(steps=steps)
    if state_head_model == "pca_enet":
        steps: list[tuple[str, object]] = [("scaler", StandardScaler())]
        n_components = _pca_components(num_samples, num_features)
        if n_components is not None:
            steps.append(("pca", PCA(n_components=n_components)))
        steps.append(("enet", ElasticNet(alpha=0.01, l1_ratio=0.2, max_iter=5000)))
        return Pipeline(steps=steps)
    if state_head_model == "rf":
        return RandomForestRegressor(
            n_estimators=200,
            max_depth=6,
            min_samples_leaf=2,
            random_state=0,
        )
    raise ValueError(f"Unsupported state_head_model: {state_head_model}")


def fit_state_heads(
    train_frame: pd.DataFrame,
    q_embedding_columns: list[str],
    s_embedding_columns: list[str],
    state_mode: str,
    state_head_model: str,
) -> StateHeadBundle:
    q_train_x = train_frame[q_embedding_columns]
    s_train_x = train_frame[s_embedding_columns]

    q_head: object | None
    q_labels = train_frame["prefix_invalid"].astype(int)
    if q_labels.nunique() < 2:
        q_head = None
    else:
        q_head = _build_q_head(state_head_model, len(train_frame), len(q_embedding_columns))
        q_head.fit(q_train_x, q_labels)

    regressors: dict[str, object] = {}
    for target_column, _, _, _ in STATE_MODE_CONFIG[state_mode]["state_targets"]:
        targets = train_frame[target_column].to_numpy(dtype=float)
        if np.allclose(targets, targets[0]):
            regressor = ConstantRegressor(float(targets[0]))
        else:
            regressor = _build_state_regressor(state_head_model, len(train_frame), len(s_embedding_columns))
            regressor.fit(s_train_x, targets)
        regressors[target_column] = regressor
    return StateHeadBundle(q_head=q_head, regressors=regressors)


def apply_state_heads(
    bundle: StateHeadBundle,
    frame: pd.DataFrame,
    q_embedding_columns: list[str],
    s_embedding_columns: list[str],
    state_mode: str,
) -> pd.DataFrame:
    pred_frame = frame.copy()
    q_pred_x = frame[q_embedding_columns]
    s_pred_x = frame[s_embedding_columns]
    if bundle.q_head is None:
        pred_frame["q_hat"] = float(frame["prefix_invalid"].mode().iloc[0]) if len(frame) else 0.0
    else:
        pred_frame["q_hat"] = bundle.q_head.predict_proba(q_pred_x)[:, 1]

    for target_column, pred_column, clip_low, clip_high in STATE_MODE_CONFIG[state_mode]["state_targets"]:
        values = bundle.regressors[target_column].predict(s_pred_x)
        if clip_high is None:
            values = np.clip(values, clip_low, None)
        else:
            values = np.clip(values, clip_low, clip_high)
        pred_frame[pred_column] = values
    return pred_frame


def build_exact_state_frame(frame: pd.DataFrame, state_mode: str, include_uncertainty: bool = False) -> pd.DataFrame:
    exact_frame = ensure_base_context_columns(frame)
    exact_frame["q_hat"] = exact_frame["q_t"].to_numpy(dtype=float)
    for target_column, pred_column, _, _ in STATE_MODE_CONFIG[state_mode]["state_targets"]:
        exact_frame[pred_column] = exact_frame[target_column].to_numpy(dtype=float)
    if include_uncertainty:
        exact_frame["q_hat_std"] = 0.0
        for _, pred_column, _, _ in STATE_MODE_CONFIG[state_mode]["state_targets"]:
            exact_frame[f"{pred_column}_std"] = 0.0
    return exact_frame


def fit_state_head_committee(
    train_frame: pd.DataFrame,
    q_embedding_columns: list[str],
    s_embedding_columns: list[str],
    state_mode: str,
    state_head_model: str,
    group_column: str,
) -> list[StateHeadBundle]:
    unique_groups = train_frame[group_column].nunique()
    effective_splits = min(4, unique_groups)
    if effective_splits < 2:
        return [fit_state_heads(train_frame, q_embedding_columns, s_embedding_columns, state_mode, state_head_model)]

    splitter = GroupKFold(n_splits=effective_splits)
    committee: list[StateHeadBundle] = []
    for inner_train_index, _ in splitter.split(train_frame, groups=train_frame[group_column]):
        inner_train_frame = train_frame.iloc[inner_train_index]
        committee.append(
            fit_state_heads(
                inner_train_frame,
                q_embedding_columns,
                s_embedding_columns,
                state_mode,
                state_head_model,
            )
        )
    return committee


def apply_state_head_committee(
    committee: list[StateHeadBundle],
    frame: pd.DataFrame,
    q_embedding_columns: list[str],
    s_embedding_columns: list[str],
    state_mode: str,
) -> pd.DataFrame:
    committee_predictions = [
        apply_state_heads(bundle, frame, q_embedding_columns, s_embedding_columns, state_mode)
        for bundle in committee
    ]
    aggregate_frame = committee_predictions[0].copy()

    q_stack = np.stack([pred_frame["q_hat"].to_numpy(dtype=float) for pred_frame in committee_predictions], axis=1)
    aggregate_frame["q_hat"] = q_stack.mean(axis=1)
    aggregate_frame["q_hat_std"] = q_stack.std(axis=1)

    for _, pred_column, _, _ in STATE_MODE_CONFIG[state_mode]["state_targets"]:
        pred_stack = np.stack(
            [pred_frame[pred_column].to_numpy(dtype=float) for pred_frame in committee_predictions],
            axis=1,
        )
        aggregate_frame[pred_column] = pred_stack.mean(axis=1)
        aggregate_frame[f"{pred_column}_std"] = pred_stack.std(axis=1)
    return aggregate_frame


def build_oof_predicted_state_frame(
    train_frame: pd.DataFrame,
    q_embedding_columns: list[str],
    s_embedding_columns: list[str],
    state_mode: str,
    state_head_model: str,
    group_column: str,
    with_uncertainty: bool = False,
) -> pd.DataFrame:
    unique_groups = train_frame[group_column].nunique()
    effective_splits = min(4, unique_groups)
    if effective_splits < 2:
        if with_uncertainty:
            committee = fit_state_head_committee(
                train_frame,
                q_embedding_columns,
                s_embedding_columns,
                state_mode,
                state_head_model,
                group_column,
            )
            return apply_state_head_committee(
                committee,
                train_frame,
                q_embedding_columns,
                s_embedding_columns,
                state_mode,
            )
        return apply_state_heads(
            fit_state_heads(train_frame, q_embedding_columns, s_embedding_columns, state_mode, state_head_model),
            train_frame,
            q_embedding_columns,
            s_embedding_columns,
            state_mode,
        )

    splitter = GroupKFold(n_splits=effective_splits)
    oof_parts: list[pd.DataFrame] = []
    for inner_train_index, inner_valid_index in splitter.split(train_frame, groups=train_frame[group_column]):
        inner_train_frame = train_frame.iloc[inner_train_index]
        inner_valid_frame = train_frame.iloc[inner_valid_index]
        if with_uncertainty:
            committee = fit_state_head_committee(
                inner_train_frame,
                q_embedding_columns,
                s_embedding_columns,
                state_mode,
                state_head_model,
                group_column,
            )
            oof_parts.append(
                apply_state_head_committee(
                    committee,
                    inner_valid_frame,
                    q_embedding_columns,
                    s_embedding_columns,
                    state_mode,
                )
            )
        else:
            state_heads = fit_state_heads(
                inner_train_frame,
                q_embedding_columns,
                s_embedding_columns,
                state_mode,
                state_head_model,
            )
            oof_parts.append(
                apply_state_heads(
                    state_heads,
                    inner_valid_frame,
                    q_embedding_columns,
                    s_embedding_columns,
                    state_mode,
                )
            )
    return pd.concat(oof_parts).sort_index().reset_index(drop=True)


def build_oof_exact_teacher_score_frame(
    train_frame: pd.DataFrame,
    exact_feature_columns: list[str],
    state_mode: str,
    value_head_model: str,
    group_column: str,
) -> pd.DataFrame:
    unique_groups = train_frame[group_column].nunique()
    effective_splits = min(4, unique_groups)
    if effective_splits < 2:
        teacher_bundle = fit_action_value_heads(train_frame, exact_feature_columns, state_mode, value_head_model)
        teacher_scores = score_action_values(teacher_bundle, train_frame, exact_feature_columns)
        teacher_frame = train_frame[["row_id"]].copy()
        for action_index, action in enumerate(ACTIONS):
            teacher_frame[f"teacher_{action}_score"] = teacher_scores[:, action_index]
        return teacher_frame.reset_index(drop=True)

    splitter = GroupKFold(n_splits=effective_splits)
    teacher_parts: list[pd.DataFrame] = []
    for inner_train_index, inner_valid_index in splitter.split(train_frame, groups=train_frame[group_column]):
        inner_train_frame = train_frame.iloc[inner_train_index].reset_index(drop=True)
        inner_valid_frame = train_frame.iloc[inner_valid_index].copy()
        teacher_bundle = fit_action_value_heads(inner_train_frame, exact_feature_columns, state_mode, value_head_model)
        teacher_scores = score_action_values(teacher_bundle, inner_valid_frame, exact_feature_columns)
        teacher_part = inner_valid_frame[["row_id"]].copy()
        for action_index, action in enumerate(ACTIONS):
            teacher_part[f"teacher_{action}_score"] = teacher_scores[:, action_index]
        teacher_parts.append(teacher_part)
    return pd.concat(teacher_parts).sort_index().reset_index(drop=True)


def build_teacher_distilled_train_variant(
    train_variant: pd.DataFrame,
    teacher_score_frame: pd.DataFrame,
) -> pd.DataFrame:
    distilled = train_variant.merge(teacher_score_frame, on="row_id", how="left", validate="many_to_one")
    teacher_columns = [f"teacher_{action}_score" for action in ACTIONS]
    if distilled[teacher_columns].isna().any().any():
        missing_rows = int(distilled[teacher_columns].isna().any(axis=1).sum())
        raise ValueError(f"Missing exact-teacher targets for {missing_rows} train rows")
    for action in ACTIONS:
        distilled[UTILITY_COLUMNS[action]] = distilled[f"teacher_{action}_score"].to_numpy(dtype=float)
    return distilled


def _build_value_regressor(value_head_model: str) -> object:
    base_model = _base_value_head_model(value_head_model)
    if base_model in {"ridge", "noise_weighted_ridge"}:
        return Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                ("ridge", Ridge(alpha=1.0)),
            ]
        )
    if base_model == "interaction_ridge":
        return Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                ("poly", PolynomialFeatures(degree=2, include_bias=False)),
                ("ridge", Ridge(alpha=1.0)),
            ]
        )
    if base_model == "heteroscedastic_interaction":
        return Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                ("poly", PolynomialFeatures(degree=2, include_bias=False)),
                ("ridge", Ridge(alpha=1.0)),
            ]
        )
    if base_model == "huber":
        return Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                ("huber", HuberRegressor(alpha=0.001, epsilon=1.35, max_iter=1000)),
            ]
        )
    if base_model == "pairwise_logit":
        return Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                ("logreg", LogisticRegression(max_iter=4000, class_weight="balanced", C=0.5)),
            ]
        )
    if base_model == "pairwise_interaction_logit":
        return Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                ("poly", PolynomialFeatures(degree=2, include_bias=False)),
                ("logreg", LogisticRegression(max_iter=4000, class_weight="balanced", C=0.5)),
            ]
        )
    if base_model == "pairwise_heteroscedastic_interaction":
        return Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                ("poly", PolynomialFeatures(degree=2, include_bias=False)),
                ("ridge", Ridge(alpha=1.0)),
            ]
        )
    if base_model == "shared_covariance_heteroscedastic_interaction":
        return Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                ("poly", PolynomialFeatures(degree=2, include_bias=False)),
                ("ridge", Ridge(alpha=1.0)),
            ]
        )
    if base_model in LOWRANK_VALUE_MODELS:
        return Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                ("poly", PolynomialFeatures(degree=2, include_bias=False)),
                ("ridge", Ridge(alpha=1.0)),
            ]
        )
    if base_model == "conditional_lowrank_heteroscedastic_interaction":
        return Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                ("poly", PolynomialFeatures(degree=2, include_bias=False)),
                ("ridge", Ridge(alpha=1.0)),
            ]
        )
    raise ValueError(f"Unsupported value_head_model: {value_head_model}")


def _state_noise_weights(train_frame: pd.DataFrame, state_mode: str) -> np.ndarray:
    if "q_t" not in train_frame.columns or "q_hat" not in train_frame.columns:
        return np.ones(len(train_frame), dtype=float)

    discrepancies = [
        np.abs(
            train_frame["q_hat"].to_numpy(dtype=float) - train_frame["q_t"].to_numpy(dtype=float)
        )
    ]
    for target_column, pred_column, clip_low, clip_high in STATE_MODE_CONFIG[state_mode]["state_targets"]:
        if target_column not in train_frame.columns or pred_column not in train_frame.columns:
            continue
        target_values = train_frame[target_column].to_numpy(dtype=float)
        pred_values = train_frame[pred_column].to_numpy(dtype=float)
        scale = float(np.std(target_values))
        if scale < 1e-6:
            if clip_high is not None:
                scale = max(clip_high - clip_low, 1e-6)
            else:
                scale = max(float(np.mean(np.abs(target_values))), 1.0)
        discrepancies.append(np.abs(pred_values - target_values) / scale)
    mean_noise = np.mean(np.column_stack(discrepancies), axis=1)
    return np.clip(1.0 / (1.0 + mean_noise), 0.1, 1.0)


def _fit_gate_classifier(
    frame: pd.DataFrame,
    feature_columns: list[str],
    labels: np.ndarray,
    sample_weights: np.ndarray,
) -> object:
    if np.unique(labels).size < 2:
        return ConstantBinaryClassifier(float(labels[0]))
    classifier = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("logreg", LogisticRegression(max_iter=4000, class_weight="balanced", C=0.5)),
        ]
    )
    classifier.fit(frame[feature_columns], labels, logreg__sample_weight=sample_weights)
    return classifier


def _build_error_regressor() -> object:
    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("poly", PolynomialFeatures(degree=2, include_bias=False)),
            ("ridge", Ridge(alpha=1.0)),
        ]
    )


def _build_meta_pairwise_classifier() -> object:
    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("poly", PolynomialFeatures(degree=2, include_bias=False)),
            ("logreg", LogisticRegression(max_iter=4000, class_weight="balanced", C=0.5)),
        ]
    )


def _fit_pairwise_cluster_model(meta_features: pd.DataFrame) -> object:
    if len(meta_features) < 6:
        return ConstantLabelModel(0)
    if meta_features.nunique(dropna=False).sum() <= len(meta_features.columns):
        return ConstantLabelModel(0)
    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("kmeans", KMeans(n_clusters=2, random_state=0, n_init=20)),
        ]
    )
    try:
        model.fit(meta_features)
        labels = model.predict(meta_features)
    except ValueError:
        return ConstantLabelModel(0)
    if np.unique(labels).size < 2:
        return ConstantLabelModel(int(labels[0]))
    return model


def _select_cluster_shrinkage_strategy(
    base_prob: np.ndarray,
    error_hat: np.ndarray,
    labels: np.ndarray,
    sample_weights: np.ndarray,
) -> dict[str, float | str]:
    best_config: dict[str, float | str] = {"strategy": "no_shrink", "retention_floor": 1.0}
    best_loss = float(np.average(np.abs(base_prob - labels), weights=sample_weights))

    full_shrink = 0.5 + (1.0 - error_hat) * (base_prob - 0.5)
    full_loss = float(np.average(np.abs(full_shrink - labels), weights=sample_weights))
    if full_loss < best_loss:
        best_loss = full_loss
        best_config = {"strategy": "full_shrink", "retention_floor": 1.0}

    for floor in [0.2, 0.35, 0.5, 0.65, 0.8]:
        capped_shrink = 0.5 + np.maximum(1.0 - error_hat, floor) * (base_prob - 0.5)
        capped_loss = float(np.average(np.abs(capped_shrink - labels), weights=sample_weights))
        if capped_loss < best_loss:
            best_loss = capped_loss
            best_config = {"strategy": "capped_shrink", "retention_floor": float(floor)}
    return best_config


def _project_psd(matrix: np.ndarray, min_eig: float = 1e-6) -> np.ndarray:
    sym = 0.5 * (matrix + matrix.T)
    eigvals, eigvecs = np.linalg.eigh(sym)
    eigvals = np.clip(eigvals, min_eig, None)
    return eigvecs @ np.diag(eigvals) @ eigvecs.T


def _first_loading_vector(matrix: np.ndarray, output_dim: int) -> np.ndarray:
    if matrix.size == 0:
        return np.zeros(output_dim, dtype=float)
    _, _, vt = np.linalg.svd(matrix, full_matrices=False)
    if vt.size == 0:
        return np.zeros(output_dim, dtype=float)
    loading = vt[0].astype(float)
    norm = float(np.linalg.norm(loading))
    if norm > 1e-8:
        loading = loading / norm
    return loading


def _fit_log_square_factor_model(
    train_x: pd.DataFrame,
    factor_scores: np.ndarray,
    base_model: str,
) -> object:
    if factor_scores.size == 0:
        return ConstantRegressor(float(np.log(1e-4)))
    factor_target = np.log(np.square(factor_scores) + 1e-4)
    if np.allclose(factor_target, factor_target[0]):
        return ConstantRegressor(float(factor_target[0]))
    factor_model = _build_value_regressor(base_model)
    factor_model.fit(train_x, factor_target)
    return factor_model


def _fit_actionwise_gaussian_components(
    train_frame: pd.DataFrame,
    feature_columns: list[str],
    base_model: str,
) -> tuple[dict[str, object], pd.DataFrame, np.ndarray, np.ndarray]:
    regressors: dict[str, object] = {}
    train_x = train_frame[feature_columns]
    group_column = "sample_id" if "sample_id" in train_frame.columns else None
    residual_matrix = np.zeros((len(train_frame), len(ACTIONS)), dtype=float)
    var_matrix = np.zeros((len(train_frame), len(ACTIONS)), dtype=float)

    for action_index, action in enumerate(ACTIONS):
        target = train_frame[UTILITY_COLUMNS[action]].to_numpy(dtype=float)
        mean_model = _build_value_regressor(base_model)

        oof_prediction = np.zeros(len(train_frame), dtype=float)
        has_oof = False
        if group_column is not None:
            unique_groups = train_frame[group_column].nunique()
            effective_splits = min(4, unique_groups)
            if effective_splits >= 2:
                splitter = GroupKFold(n_splits=effective_splits)
                for inner_train_index, inner_valid_index in splitter.split(train_frame, groups=train_frame[group_column]):
                    inner_train_frame = train_frame.iloc[inner_train_index]
                    inner_valid_frame = train_frame.iloc[inner_valid_index]
                    inner_model = _build_value_regressor(base_model)
                    inner_model.fit(
                        inner_train_frame[feature_columns],
                        inner_train_frame[UTILITY_COLUMNS[action]].to_numpy(dtype=float),
                    )
                    oof_prediction[inner_valid_index] = inner_model.predict(inner_valid_frame[feature_columns])
                has_oof = True
        mean_model.fit(train_x, target)
        if not has_oof:
            oof_prediction = mean_model.predict(train_x)

        residual = target - oof_prediction
        logvar_target = np.log(np.square(residual) + 1e-4)
        logvar_model = _build_value_regressor(base_model)
        logvar_model.fit(train_x, logvar_target)
        var_hat = np.exp(np.clip(logvar_model.predict(train_x), -6.0, 6.0))

        residual_matrix[:, action_index] = residual
        var_matrix[:, action_index] = var_hat
        regressors[action] = {
            "mean": mean_model,
            "logvar": logvar_model,
        }
    return regressors, train_x, residual_matrix, var_matrix


def _pairwise_meta_feature_frame(
    frame: pd.DataFrame,
    risk_feature_columns: list[str],
    base_prob: np.ndarray,
) -> pd.DataFrame:
    meta_frame = frame[risk_feature_columns].copy()
    clipped_prob = np.clip(base_prob, 1e-4, 1.0 - 1e-4)
    meta_frame["base_prob"] = clipped_prob
    meta_frame["base_margin"] = clipped_prob - 0.5
    meta_frame["base_confidence"] = np.abs(clipped_prob - 0.5)
    return meta_frame


def _pairwise_probability_map(
    bundle: ActionValueBundle,
    frame: pd.DataFrame,
    feature_columns: list[str],
) -> dict[str, np.ndarray]:
    feature_matrix = frame[feature_columns]
    pairwise_probs: dict[str, np.ndarray] = {}

    if bundle.model_kind == "pairwise_logit":
        for left_index, action_a in enumerate(ACTIONS):
            for right_index in range(left_index + 1, len(ACTIONS)):
                action_b = ACTIONS[right_index]
                key = f"{action_a}__vs__{action_b}"
                pairwise_probs[key] = bundle.regressors[key].predict_proba(feature_matrix)[:, 1]
        return pairwise_probs

    if bundle.model_kind == "heteroscedastic_gaussian":
        mean_matrix = np.stack(
            [bundle.regressors[action]["mean"].predict(feature_matrix) for action in ACTIONS],
            axis=1,
        )
        var_matrix = np.stack(
            [
                np.exp(np.clip(bundle.regressors[action]["logvar"].predict(feature_matrix), -6.0, 6.0))
                for action in ACTIONS
            ],
            axis=1,
        )
        for left_index, action_a in enumerate(ACTIONS):
            for right_index in range(left_index + 1, len(ACTIONS)):
                action_b = ACTIONS[right_index]
                denom = np.sqrt(var_matrix[:, left_index] + var_matrix[:, right_index] + 1e-6)
                z = (mean_matrix[:, left_index] - mean_matrix[:, right_index]) / denom
                z = np.clip(z, -20.0, 20.0)
                pairwise_probs[f"{action_a}__vs__{action_b}"] = 1.0 / (1.0 + np.exp(-z))
        return pairwise_probs

    if bundle.model_kind == "shared_covariance_heteroscedastic":
        mean_matrix = np.stack(
            [bundle.regressors[action]["mean"].predict(feature_matrix) for action in ACTIONS],
            axis=1,
        )
        scale = np.exp(np.clip(bundle.regressors["shared_scale_model"].predict(feature_matrix), -6.0, 6.0))
        covariance_template = np.asarray(bundle.regressors["covariance_template"], dtype=float)
        for left_index, action_a in enumerate(ACTIONS):
            for right_index in range(left_index + 1, len(ACTIONS)):
                action_b = ACTIONS[right_index]
                base_var = (
                    covariance_template[left_index, left_index]
                    + covariance_template[right_index, right_index]
                    - 2.0 * covariance_template[left_index, right_index]
                )
                diff_var = np.clip(scale * base_var, 1e-6, None)
                z = (mean_matrix[:, left_index] - mean_matrix[:, right_index]) / np.sqrt(diff_var)
                z = np.clip(z, -20.0, 20.0)
                pairwise_probs[f"{action_a}__vs__{action_b}"] = 1.0 / (1.0 + np.exp(-z))
        return pairwise_probs

    if bundle.model_kind == "lowrank_heteroscedastic_gaussian":
        mean_matrix = np.stack(
            [bundle.regressors[action]["mean"].predict(feature_matrix) for action in ACTIONS],
            axis=1,
        )
        var_matrix = np.stack(
            [
                np.exp(np.clip(bundle.regressors[action]["logvar"].predict(feature_matrix), -6.0, 6.0))
                for action in ACTIONS
            ],
            axis=1,
        )
        loading_matrix = bundle.regressors.get("loading_matrix")
        factor_models = bundle.regressors.get("factor_models")
        if loading_matrix is None or factor_models is None:
            loading_matrix = np.asarray(bundle.regressors["loading_vector"], dtype=float)[:, None]
            factor_models = [bundle.regressors["factor_model"]]
        else:
            loading_matrix = np.asarray(loading_matrix, dtype=float)
        factor_var_matrix = (
            np.column_stack(
                [np.exp(np.clip(model.predict(feature_matrix), -6.0, 6.0)) for model in factor_models]
            )
            if factor_models
            else np.zeros((len(frame), 0), dtype=float)
        )
        for left_index, action_a in enumerate(ACTIONS):
            for right_index in range(left_index + 1, len(ACTIONS)):
                action_b = ACTIONS[right_index]
                loading_diff = loading_matrix[left_index, :] - loading_matrix[right_index, :]
                diff_var = var_matrix[:, left_index] + var_matrix[:, right_index]
                if factor_var_matrix.shape[1] > 0:
                    diff_var = diff_var + np.sum(
                        factor_var_matrix * np.square(loading_diff[None, :]),
                        axis=1,
                    )
                z = (mean_matrix[:, left_index] - mean_matrix[:, right_index]) / np.sqrt(np.clip(diff_var, 1e-6, None))
                z = np.clip(z, -20.0, 20.0)
                pairwise_probs[f"{action_a}__vs__{action_b}"] = 1.0 / (1.0 + np.exp(-z))
        return pairwise_probs

    if bundle.model_kind == "conditional_lowrank_heteroscedastic_gaussian":
        mean_matrix = np.stack(
            [bundle.regressors[action]["mean"].predict(feature_matrix) for action in ACTIONS],
            axis=1,
        )
        var_matrix = np.stack(
            [
                np.exp(np.clip(bundle.regressors[action]["logvar"].predict(feature_matrix), -6.0, 6.0))
                for action in ACTIONS
            ],
            axis=1,
        )
        loading_templates = np.asarray(bundle.regressors["loading_templates"], dtype=float)
        factor_models = bundle.regressors["factor_models"]
        gate_prob = bundle.regressors["gate_model"].predict_proba(feature_matrix)[:, 1]
        factor_var_matrix = np.column_stack(
            [np.exp(np.clip(model.predict(feature_matrix), -6.0, 6.0)) for model in factor_models]
        )
        for left_index, action_a in enumerate(ACTIONS):
            for right_index in range(left_index + 1, len(ACTIONS)):
                action_b = ACTIONS[right_index]
                diff_var = var_matrix[:, left_index] + var_matrix[:, right_index]
                low_diff = float((loading_templates[left_index, 0] - loading_templates[right_index, 0]) ** 2)
                high_diff = float((loading_templates[left_index, 1] - loading_templates[right_index, 1]) ** 2)
                diff_var = diff_var + (1.0 - gate_prob) * factor_var_matrix[:, 0] * low_diff
                diff_var = diff_var + gate_prob * factor_var_matrix[:, 1] * high_diff
                z = (mean_matrix[:, left_index] - mean_matrix[:, right_index]) / np.sqrt(np.clip(diff_var, 1e-6, None))
                z = np.clip(z, -20.0, 20.0)
                pairwise_probs[f"{action_a}__vs__{action_b}"] = 1.0 / (1.0 + np.exp(-z))
        return pairwise_probs

    raise ValueError(f"Unsupported bundle for pairwise probabilities: {bundle.model_kind}")


def fit_action_value_heads(
    train_frame: pd.DataFrame,
    feature_columns: list[str],
    state_mode: str,
    value_head_model: str,
) -> ActionValueBundle:
    base_model = _base_value_head_model(value_head_model)
    if base_model in PAIRWISE_VALUE_MODELS:
        classifiers: dict[str, object] = {}
        train_x = train_frame[feature_columns]
        for action_a, action_b in combinations(ACTIONS, 2):
            key = f"{action_a}__vs__{action_b}"
            utility_diff = (
                train_frame[UTILITY_COLUMNS[action_a]].to_numpy(dtype=float)
                - train_frame[UTILITY_COLUMNS[action_b]].to_numpy(dtype=float)
            )
            labels = (utility_diff > 0.0).astype(int)
            sample_weights = np.abs(utility_diff) + 1e-3
            if np.allclose(utility_diff, 0.0):
                classifiers[key] = ConstantBinaryClassifier(0.5)
                continue
            if np.unique(labels).size < 2:
                classifiers[key] = ConstantBinaryClassifier(float(labels[0]))
                continue
            classifier = _build_value_regressor(base_model)
            classifier.fit(train_x, labels, logreg__sample_weight=sample_weights)
            classifiers[key] = classifier
        return ActionValueBundle(model_kind="pairwise_logit", regressors=classifiers)

    if base_model == "heteroscedastic_interaction":
        regressors: dict[str, object] = {}
        train_x = train_frame[feature_columns]
        group_column = "sample_id" if "sample_id" in train_frame.columns else None
        for action in ACTIONS:
            target = train_frame[UTILITY_COLUMNS[action]].to_numpy(dtype=float)
            mean_model = _build_value_regressor(base_model)

            oof_prediction = np.zeros(len(train_frame), dtype=float)
            has_oof = False
            if group_column is not None:
                unique_groups = train_frame[group_column].nunique()
                effective_splits = min(4, unique_groups)
                if effective_splits >= 2:
                    splitter = GroupKFold(n_splits=effective_splits)
                    for inner_train_index, inner_valid_index in splitter.split(train_frame, groups=train_frame[group_column]):
                        inner_train_frame = train_frame.iloc[inner_train_index]
                        inner_valid_frame = train_frame.iloc[inner_valid_index]
                        inner_model = _build_value_regressor(base_model)
                        inner_model.fit(
                            inner_train_frame[feature_columns],
                            inner_train_frame[UTILITY_COLUMNS[action]].to_numpy(dtype=float),
                        )
                        oof_prediction[inner_valid_index] = inner_model.predict(inner_valid_frame[feature_columns])
                    has_oof = True
            mean_model.fit(train_x, target)
            if not has_oof:
                oof_prediction = mean_model.predict(train_x)

            residual = target - oof_prediction
            logvar_target = np.log(np.square(residual) + 1e-4)
            logvar_model = _build_value_regressor(base_model)
            logvar_model.fit(train_x, logvar_target)
            regressors[action] = {
                "mean": mean_model,
                "logvar": logvar_model,
            }
        return ActionValueBundle(model_kind="heteroscedastic_gaussian", regressors=regressors)

    if base_model == "pairwise_heteroscedastic_interaction":
        pair_models: dict[str, dict[str, object]] = {}
        train_x = train_frame[feature_columns]
        group_column = "sample_id" if "sample_id" in train_frame.columns else None
        for action_a, action_b in combinations(ACTIONS, 2):
            key = f"{action_a}__vs__{action_b}"
            utility_diff = (
                train_frame[UTILITY_COLUMNS[action_a]].to_numpy(dtype=float)
                - train_frame[UTILITY_COLUMNS[action_b]].to_numpy(dtype=float)
            )
            sample_weights = np.abs(utility_diff) + 1e-3

            if np.allclose(utility_diff, utility_diff[0]):
                mean_model: object = ConstantRegressor(float(utility_diff[0]))
                logvar_model: object = ConstantRegressor(float(np.log(1e-4)))
                pair_models[key] = {"mean": mean_model, "logvar": logvar_model}
                continue

            mean_model = _build_value_regressor(base_model)
            oof_prediction = np.zeros(len(train_frame), dtype=float)
            has_oof = False
            if group_column is not None:
                unique_groups = train_frame[group_column].nunique()
                effective_splits = min(4, unique_groups)
                if effective_splits >= 2:
                    splitter = GroupKFold(n_splits=effective_splits)
                    for inner_train_index, inner_valid_index in splitter.split(train_frame, groups=train_frame[group_column]):
                        inner_train_frame = train_frame.iloc[inner_train_index]
                        inner_valid_frame = train_frame.iloc[inner_valid_index]
                        inner_model = _build_value_regressor(base_model)
                        inner_diff = (
                            inner_train_frame[UTILITY_COLUMNS[action_a]].to_numpy(dtype=float)
                            - inner_train_frame[UTILITY_COLUMNS[action_b]].to_numpy(dtype=float)
                        )
                        inner_weights = np.abs(inner_diff) + 1e-3
                        inner_model.fit(
                            inner_train_frame[feature_columns],
                            inner_diff,
                            ridge__sample_weight=inner_weights,
                        )
                        oof_prediction[inner_valid_index] = inner_model.predict(inner_valid_frame[feature_columns])
                    has_oof = True
            mean_model.fit(train_x, utility_diff, ridge__sample_weight=sample_weights)
            if not has_oof:
                oof_prediction = mean_model.predict(train_x)

            residual = utility_diff - oof_prediction
            logvar_target = np.log(np.square(residual) + 1e-4)
            logvar_model = _build_value_regressor(base_model)
            logvar_model.fit(train_x, logvar_target, ridge__sample_weight=sample_weights)
            pair_models[key] = {
                "mean": mean_model,
                "logvar": logvar_model,
            }
        return ActionValueBundle(model_kind="pairwise_heteroscedastic", regressors=pair_models)

    if base_model == "shared_covariance_heteroscedastic_interaction":
        regressors: dict[str, object] = {}
        train_x = train_frame[feature_columns]
        group_column = "sample_id" if "sample_id" in train_frame.columns else None
        residual_matrix = np.zeros((len(train_frame), len(ACTIONS)), dtype=float)

        for action_index, action in enumerate(ACTIONS):
            target = train_frame[UTILITY_COLUMNS[action]].to_numpy(dtype=float)
            mean_model = _build_value_regressor(base_model)

            oof_prediction = np.zeros(len(train_frame), dtype=float)
            has_oof = False
            if group_column is not None:
                unique_groups = train_frame[group_column].nunique()
                effective_splits = min(4, unique_groups)
                if effective_splits >= 2:
                    splitter = GroupKFold(n_splits=effective_splits)
                    for inner_train_index, inner_valid_index in splitter.split(train_frame, groups=train_frame[group_column]):
                        inner_train_frame = train_frame.iloc[inner_train_index]
                        inner_valid_frame = train_frame.iloc[inner_valid_index]
                        inner_model = _build_value_regressor(base_model)
                        inner_model.fit(
                            inner_train_frame[feature_columns],
                            inner_train_frame[UTILITY_COLUMNS[action]].to_numpy(dtype=float),
                        )
                        oof_prediction[inner_valid_index] = inner_model.predict(inner_valid_frame[feature_columns])
                    has_oof = True
            mean_model.fit(train_x, target)
            if not has_oof:
                oof_prediction = mean_model.predict(train_x)

            residual_matrix[:, action_index] = target - oof_prediction
            regressors[action] = {"mean": mean_model}

        scale_target = np.log(np.mean(np.square(residual_matrix), axis=1) + 1e-4)
        if np.allclose(scale_target, scale_target[0]):
            scale_model: object = ConstantRegressor(float(scale_target[0]))
        else:
            scale_model = _build_value_regressor(base_model)
            scale_model.fit(train_x, scale_target)

        scale_hat = np.exp(np.clip(scale_model.predict(train_x), -6.0, 6.0))
        normalized_residual = residual_matrix / np.sqrt(scale_hat[:, None] + 1e-6)
        covariance_template = np.cov(normalized_residual, rowvar=False)
        if covariance_template.ndim == 0:
            covariance_template = np.eye(len(ACTIONS), dtype=float) * float(covariance_template)
        covariance_template = _project_psd(covariance_template)
        trace = float(np.trace(covariance_template))
        if trace > 1e-6:
            covariance_template = covariance_template * (len(ACTIONS) / trace)

        regressors["shared_scale_model"] = scale_model
        regressors["covariance_template"] = covariance_template
        return ActionValueBundle(model_kind="shared_covariance_heteroscedastic", regressors=regressors)

    lowrank_rank = _lowrank_model_rank(base_model)
    if lowrank_rank is not None:
        regressors: dict[str, object] = {}
        train_x = train_frame[feature_columns]
        group_column = "sample_id" if "sample_id" in train_frame.columns else None
        residual_matrix = np.zeros((len(train_frame), len(ACTIONS)), dtype=float)
        var_matrix = np.zeros((len(train_frame), len(ACTIONS)), dtype=float)

        for action_index, action in enumerate(ACTIONS):
            target = train_frame[UTILITY_COLUMNS[action]].to_numpy(dtype=float)
            mean_model = _build_value_regressor(base_model)

            oof_prediction = np.zeros(len(train_frame), dtype=float)
            has_oof = False
            if group_column is not None:
                unique_groups = train_frame[group_column].nunique()
                effective_splits = min(4, unique_groups)
                if effective_splits >= 2:
                    splitter = GroupKFold(n_splits=effective_splits)
                    for inner_train_index, inner_valid_index in splitter.split(train_frame, groups=train_frame[group_column]):
                        inner_train_frame = train_frame.iloc[inner_train_index]
                        inner_valid_frame = train_frame.iloc[inner_valid_index]
                        inner_model = _build_value_regressor(base_model)
                        inner_model.fit(
                            inner_train_frame[feature_columns],
                            inner_train_frame[UTILITY_COLUMNS[action]].to_numpy(dtype=float),
                        )
                        oof_prediction[inner_valid_index] = inner_model.predict(inner_valid_frame[feature_columns])
                    has_oof = True
            mean_model.fit(train_x, target)
            if not has_oof:
                oof_prediction = mean_model.predict(train_x)

            residual = target - oof_prediction
            logvar_target = np.log(np.square(residual) + 1e-4)
            logvar_model = _build_value_regressor(base_model)
            logvar_model.fit(train_x, logvar_target)
            var_hat = np.exp(np.clip(logvar_model.predict(train_x), -6.0, 6.0))

            residual_matrix[:, action_index] = residual
            var_matrix[:, action_index] = var_hat
            regressors[action] = {
                "mean": mean_model,
                "logvar": logvar_model,
            }

        standardized = residual_matrix / np.sqrt(var_matrix + 1e-6)
        standardized = standardized - standardized.mean(axis=0, keepdims=True)
        if standardized.size == 0:
            loading_matrix = np.zeros((len(ACTIONS), 0), dtype=float)
            factor_models: list[object] = []
        else:
            _, _, vt = np.linalg.svd(standardized, full_matrices=False)
            effective_rank = min(lowrank_rank, vt.shape[0], len(ACTIONS))
            if effective_rank <= 0:
                loading_matrix = np.zeros((len(ACTIONS), 0), dtype=float)
                factor_models = []
            else:
                loading_matrix = vt[:effective_rank].T.astype(float)
                column_norms = np.linalg.norm(loading_matrix, axis=0)
                for factor_index, norm in enumerate(column_norms):
                    if norm > 1e-8:
                        loading_matrix[:, factor_index] /= norm
                    else:
                        loading_matrix[:, factor_index] = 0.0
                factor_models = []
                for factor_index in range(loading_matrix.shape[1]):
                    factor_scores = standardized @ loading_matrix[:, factor_index]
                    factor_target = np.log(np.square(factor_scores) + 1e-4)
                    if np.allclose(factor_target, factor_target[0]):
                        factor_model = ConstantRegressor(float(factor_target[0]))
                    else:
                        factor_model = _build_value_regressor(base_model)
                        factor_model.fit(train_x, factor_target)
                    factor_models.append(factor_model)

        regressors["loading_matrix"] = loading_matrix
        regressors["factor_models"] = factor_models
        if loading_matrix.shape[1] == 1 and factor_models:
            regressors["loading_vector"] = loading_matrix[:, 0]
            regressors["factor_model"] = factor_models[0]
        return ActionValueBundle(model_kind="lowrank_heteroscedastic_gaussian", regressors=regressors)

    if base_model == "conditional_lowrank_heteroscedastic_interaction":
        regressors, train_x, residual_matrix, var_matrix = _fit_actionwise_gaussian_components(
            train_frame,
            feature_columns,
            base_model,
        )
        standardized = residual_matrix / np.sqrt(var_matrix + 1e-6)
        standardized = standardized - standardized.mean(axis=0, keepdims=True)

        primary_loading = _first_loading_vector(standardized, len(ACTIONS))
        primary_scores = standardized @ primary_loading
        score_center = float(np.median(primary_scores)) if primary_scores.size else 0.0
        regime_labels = (primary_scores > score_center).astype(int) if primary_scores.size else np.zeros(len(train_frame), dtype=int)
        if regime_labels.sum() == 0 or regime_labels.sum() == len(regime_labels):
            fallback_center = float(np.mean(primary_scores)) if primary_scores.size else 0.0
            regime_labels = (
                (primary_scores > fallback_center).astype(int) if primary_scores.size else np.zeros(len(train_frame), dtype=int)
            )
        gate_weights = np.abs(primary_scores - score_center) + 1e-3 if primary_scores.size else np.ones(len(train_frame))
        gate_model = _fit_gate_classifier(train_frame, feature_columns, regime_labels, gate_weights)

        global_factor_model = _fit_log_square_factor_model(train_x, primary_scores, base_model)
        loading_templates = np.zeros((len(ACTIONS), 2), dtype=float)
        factor_models: list[object] = []
        for regime_value in range(2):
            regime_mask = regime_labels == regime_value
            if int(regime_mask.sum()) < 2:
                loading_templates[:, regime_value] = primary_loading
                factor_models.append(global_factor_model)
                continue
            regime_loading = _first_loading_vector(standardized[regime_mask], len(ACTIONS))
            regime_scores = standardized[regime_mask] @ regime_loading
            loading_templates[:, regime_value] = regime_loading
            factor_models.append(
                _fit_log_square_factor_model(
                    train_x.loc[regime_mask].reset_index(drop=True),
                    regime_scores,
                    base_model,
                )
            )

        regressors["loading_templates"] = loading_templates
        regressors["factor_models"] = factor_models
        regressors["gate_model"] = gate_model
        return ActionValueBundle(model_kind="conditional_lowrank_heteroscedastic_gaussian", regressors=regressors)

    regressors: dict[str, object] = {}
    train_x = train_frame[feature_columns]
    sample_weights = None
    if base_model == "noise_weighted_ridge":
        sample_weights = _state_noise_weights(train_frame, state_mode)
    for action in ACTIONS:
        regressor = _build_value_regressor(base_model)
        fit_kwargs: dict[str, np.ndarray] = {}
        if sample_weights is not None:
            fit_kwargs["ridge__sample_weight"] = sample_weights
        regressor.fit(train_x, train_frame[UTILITY_COLUMNS[action]].to_numpy(dtype=float), **fit_kwargs)
        regressors[action] = regressor
    return ActionValueBundle(model_kind="utility_regression", regressors=regressors)


def score_action_values(bundle: ActionValueBundle, frame: pd.DataFrame, feature_columns: list[str]) -> np.ndarray:
    feature_matrix = frame[feature_columns]
    if bundle.model_kind == "pairwise_logit":
        preference_scores = np.zeros((len(frame), len(ACTIONS)), dtype=float)
        for left_index, action_a in enumerate(ACTIONS):
            for right_index in range(left_index + 1, len(ACTIONS)):
                action_b = ACTIONS[right_index]
                key = f"{action_a}__vs__{action_b}"
                win_prob = bundle.regressors[key].predict_proba(feature_matrix)[:, 1]
                preference_scores[:, left_index] += win_prob
                preference_scores[:, right_index] += 1.0 - win_prob
        return preference_scores

    if bundle.model_kind == "gated_mixture":
        if bundle.metadata is None:
            raise ValueError("gated_mixture bundle requires metadata")
        exact_scores = score_action_values(
            bundle.regressors["exact_bundle"],
            frame,
            bundle.metadata["exact_feature_columns"],
        )
        predicted_scores = score_action_values(
            bundle.regressors["predicted_bundle"],
            frame,
            bundle.metadata["predicted_feature_columns"],
        )
        gate_probs = bundle.regressors["gate_model"].predict_proba(frame[bundle.metadata["gate_feature_columns"]])[:, 1]
        return (1.0 - gate_probs[:, None]) * exact_scores + gate_probs[:, None] * predicted_scores

    if bundle.model_kind == "pairwise_error_calibrated":
        if bundle.metadata is None:
            raise ValueError("pairwise_error_calibrated bundle requires metadata")
        base_features = frame[bundle.metadata["base_feature_columns"]]
        risk_features = frame[bundle.metadata["risk_feature_columns"]]
        preference_scores = np.zeros((len(frame), len(ACTIONS)), dtype=float)
        base_bundle = bundle.regressors["base_bundle"]
        error_models = bundle.regressors["error_models"]
        for left_index, action_a in enumerate(ACTIONS):
            for right_index in range(left_index + 1, len(ACTIONS)):
                action_b = ACTIONS[right_index]
                key = f"{action_a}__vs__{action_b}"
                base_prob = base_bundle.regressors[key].predict_proba(base_features)[:, 1]
                error_hat = np.clip(error_models[key].predict(risk_features), 0.0, 1.0)
                adjusted_prob = 0.5 + (1.0 - error_hat) * (base_prob - 0.5)
                preference_scores[:, left_index] += adjusted_prob
                preference_scores[:, right_index] += 1.0 - adjusted_prob
        return preference_scores

    if bundle.model_kind == "conditional_lowrank_pairwise_error_calibrated":
        if bundle.metadata is None:
            raise ValueError("conditional_lowrank_pairwise_error_calibrated bundle requires metadata")
        base_bundle = bundle.regressors["base_bundle"]
        error_models = bundle.regressors["error_models"]
        pairwise_probs = _pairwise_probability_map(
            base_bundle,
            frame,
            bundle.metadata["base_feature_columns"],
        )
        preference_scores = np.zeros((len(frame), len(ACTIONS)), dtype=float)
        for left_index, action_a in enumerate(ACTIONS):
            for right_index in range(left_index + 1, len(ACTIONS)):
                action_b = ACTIONS[right_index]
                key = f"{action_a}__vs__{action_b}"
                base_prob = pairwise_probs[key]
                meta_features = _pairwise_meta_feature_frame(
                    frame,
                    bundle.metadata["risk_feature_columns"],
                    base_prob,
                )
                error_hat = np.clip(error_models[key].predict(meta_features), 0.0, 1.0)
                adjusted_prob = 0.5 + (1.0 - error_hat) * (base_prob - 0.5)
                preference_scores[:, left_index] += adjusted_prob
                preference_scores[:, right_index] += 1.0 - adjusted_prob
        return preference_scores

    if bundle.model_kind == "conditional_lowrank_selective_pairwise_error_calibrated":
        if bundle.metadata is None:
            raise ValueError("conditional_lowrank_selective_pairwise_error_calibrated bundle requires metadata")
        base_bundle = bundle.regressors["base_bundle"]
        error_models = bundle.regressors["error_models"]
        gate_models = bundle.regressors["gate_models"]
        pairwise_probs = _pairwise_probability_map(
            base_bundle,
            frame,
            bundle.metadata["base_feature_columns"],
        )
        preference_scores = np.zeros((len(frame), len(ACTIONS)), dtype=float)
        for left_index, action_a in enumerate(ACTIONS):
            for right_index in range(left_index + 1, len(ACTIONS)):
                action_b = ACTIONS[right_index]
                key = f"{action_a}__vs__{action_b}"
                base_prob = pairwise_probs[key]
                meta_features = _pairwise_meta_feature_frame(
                    frame,
                    bundle.metadata["risk_feature_columns"],
                    base_prob,
                )
                error_hat = np.clip(error_models[key].predict(meta_features), 0.0, 1.0)
                calibrated_prob = 0.5 + (1.0 - error_hat) * (base_prob - 0.5)
                gate_prob = gate_models[key].predict_proba(meta_features)[:, 1]
                win_prob = (1.0 - gate_prob) * base_prob + gate_prob * calibrated_prob
                preference_scores[:, left_index] += win_prob
                preference_scores[:, right_index] += 1.0 - win_prob
        return preference_scores

    if bundle.model_kind == "conditional_lowrank_capped_pairwise_error_calibrated":
        if bundle.metadata is None:
            raise ValueError("conditional_lowrank_capped_pairwise_error_calibrated bundle requires metadata")
        base_bundle = bundle.regressors["base_bundle"]
        error_models = bundle.regressors["error_models"]
        cap_params = bundle.regressors["cap_params"]
        pairwise_probs = _pairwise_probability_map(
            base_bundle,
            frame,
            bundle.metadata["base_feature_columns"],
        )
        preference_scores = np.zeros((len(frame), len(ACTIONS)), dtype=float)
        for left_index, action_a in enumerate(ACTIONS):
            for right_index in range(left_index + 1, len(ACTIONS)):
                action_b = ACTIONS[right_index]
                key = f"{action_a}__vs__{action_b}"
                base_prob = pairwise_probs[key]
                meta_features = _pairwise_meta_feature_frame(
                    frame,
                    bundle.metadata["risk_feature_columns"],
                    base_prob,
                )
                error_hat = np.clip(error_models[key].predict(meta_features), 0.0, 1.0)
                confidence = np.abs(base_prob - 0.5)
                threshold = cap_params[key]["confidence_threshold"]
                floor = cap_params[key]["retention_floor"]
                retention = np.maximum(1.0 - error_hat, floor)
                win_prob = np.where(
                    confidence >= threshold,
                    base_prob,
                    0.5 + retention * (base_prob - 0.5),
                )
                preference_scores[:, left_index] += win_prob
                preference_scores[:, right_index] += 1.0 - win_prob
        return preference_scores

    if bundle.model_kind == "conditional_lowrank_banded_pairwise_error_calibrated":
        if bundle.metadata is None:
            raise ValueError("conditional_lowrank_banded_pairwise_error_calibrated bundle requires metadata")
        base_bundle = bundle.regressors["base_bundle"]
        error_models = bundle.regressors["error_models"]
        band_params = bundle.regressors["band_params"]
        pairwise_probs = _pairwise_probability_map(
            base_bundle,
            frame,
            bundle.metadata["base_feature_columns"],
        )
        preference_scores = np.zeros((len(frame), len(ACTIONS)), dtype=float)
        for left_index, action_a in enumerate(ACTIONS):
            for right_index in range(left_index + 1, len(ACTIONS)):
                action_b = ACTIONS[right_index]
                key = f"{action_a}__vs__{action_b}"
                base_prob = pairwise_probs[key]
                meta_features = _pairwise_meta_feature_frame(
                    frame,
                    bundle.metadata["risk_feature_columns"],
                    base_prob,
                )
                error_hat = np.clip(error_models[key].predict(meta_features), 0.0, 1.0)
                confidence = np.abs(base_prob - 0.5)
                params = band_params[key]
                low_threshold = params["low_confidence_threshold"]
                high_threshold = params["high_confidence_threshold"]
                floor = params["retention_floor"]
                full_shrink = 0.5 + (1.0 - error_hat) * (base_prob - 0.5)
                capped_shrink = 0.5 + np.maximum(1.0 - error_hat, floor) * (base_prob - 0.5)
                win_prob = np.where(
                    confidence >= high_threshold,
                    base_prob,
                    np.where(confidence >= low_threshold, capped_shrink, full_shrink),
                )
                preference_scores[:, left_index] += win_prob
                preference_scores[:, right_index] += 1.0 - win_prob
        return preference_scores

    if bundle.model_kind == "conditional_lowrank_clustered_pairwise_error_calibrated":
        if bundle.metadata is None:
            raise ValueError("conditional_lowrank_clustered_pairwise_error_calibrated bundle requires metadata")
        base_bundle = bundle.regressors["base_bundle"]
        error_models = bundle.regressors["error_models"]
        cluster_models = bundle.regressors["cluster_models"]
        cluster_params = bundle.regressors["cluster_params"]
        pairwise_probs = _pairwise_probability_map(
            base_bundle,
            frame,
            bundle.metadata["base_feature_columns"],
        )
        preference_scores = np.zeros((len(frame), len(ACTIONS)), dtype=float)
        for left_index, action_a in enumerate(ACTIONS):
            for right_index in range(left_index + 1, len(ACTIONS)):
                action_b = ACTIONS[right_index]
                key = f"{action_a}__vs__{action_b}"
                base_prob = pairwise_probs[key]
                meta_features = _pairwise_meta_feature_frame(
                    frame,
                    bundle.metadata["risk_feature_columns"],
                    base_prob,
                )
                error_hat = np.clip(error_models[key].predict(meta_features), 0.0, 1.0)
                cluster_labels = cluster_models[key].predict(meta_features).astype(int)
                win_prob = base_prob.copy()
                for cluster_id, params in cluster_params[key].items():
                    cluster_mask = cluster_labels == int(cluster_id)
                    if not np.any(cluster_mask):
                        continue
                    strategy = params["strategy"]
                    if strategy == "no_shrink":
                        candidate_prob = base_prob[cluster_mask]
                    elif strategy == "full_shrink":
                        candidate_prob = 0.5 + (1.0 - error_hat[cluster_mask]) * (base_prob[cluster_mask] - 0.5)
                    else:
                        floor = float(params["retention_floor"])
                        candidate_prob = 0.5 + np.maximum(1.0 - error_hat[cluster_mask], floor) * (
                            base_prob[cluster_mask] - 0.5
                        )
                    win_prob[cluster_mask] = candidate_prob
                preference_scores[:, left_index] += win_prob
                preference_scores[:, right_index] += 1.0 - win_prob
        return preference_scores

    if bundle.model_kind == "pairwise_meta_calibrated":
        if bundle.metadata is None:
            raise ValueError("pairwise_meta_calibrated bundle requires metadata")
        base_features = frame[bundle.metadata["base_feature_columns"]]
        preference_scores = np.zeros((len(frame), len(ACTIONS)), dtype=float)
        base_bundle = bundle.regressors["base_bundle"]
        meta_models = bundle.regressors["meta_models"]
        for left_index, action_a in enumerate(ACTIONS):
            for right_index in range(left_index + 1, len(ACTIONS)):
                action_b = ACTIONS[right_index]
                key = f"{action_a}__vs__{action_b}"
                base_prob = base_bundle.regressors[key].predict_proba(base_features)[:, 1]
                meta_features = _pairwise_meta_feature_frame(
                    frame,
                    bundle.metadata["risk_feature_columns"],
                    base_prob,
                )
                win_prob = meta_models[key].predict_proba(meta_features)[:, 1]
                preference_scores[:, left_index] += win_prob
                preference_scores[:, right_index] += 1.0 - win_prob
        return preference_scores

    if bundle.model_kind == "pairwise_selective_calibrated":
        if bundle.metadata is None:
            raise ValueError("pairwise_selective_calibrated bundle requires metadata")
        base_features = frame[bundle.metadata["base_feature_columns"]]
        preference_scores = np.zeros((len(frame), len(ACTIONS)), dtype=float)
        base_bundle = bundle.regressors["base_bundle"]
        error_models = bundle.regressors["error_models"]
        gate_models = bundle.regressors["gate_models"]
        for left_index, action_a in enumerate(ACTIONS):
            for right_index in range(left_index + 1, len(ACTIONS)):
                action_b = ACTIONS[right_index]
                key = f"{action_a}__vs__{action_b}"
                base_prob = base_bundle.regressors[key].predict_proba(base_features)[:, 1]
                error_hat = np.clip(error_models[key].predict(frame[bundle.metadata["risk_feature_columns"]]), 0.0, 1.0)
                calibrated_prob = 0.5 + (1.0 - error_hat) * (base_prob - 0.5)
                gate_features = _pairwise_meta_feature_frame(
                    frame,
                    bundle.metadata["risk_feature_columns"],
                    base_prob,
                )
                gate_prob = gate_models[key].predict_proba(gate_features)[:, 1]
                win_prob = (1.0 - gate_prob) * base_prob + gate_prob * calibrated_prob
                preference_scores[:, left_index] += win_prob
                preference_scores[:, right_index] += 1.0 - win_prob
        return preference_scores

    if bundle.model_kind == "heteroscedastic_gaussian":
        mean_matrix = np.stack(
            [bundle.regressors[action]["mean"].predict(feature_matrix) for action in ACTIONS],
            axis=1,
        )
        var_matrix = np.stack(
            [
                np.exp(np.clip(bundle.regressors[action]["logvar"].predict(feature_matrix), -6.0, 6.0))
                for action in ACTIONS
            ],
            axis=1,
        )
        preference_scores = np.zeros((len(frame), len(ACTIONS)), dtype=float)
        for left_index in range(len(ACTIONS)):
            for right_index in range(left_index + 1, len(ACTIONS)):
                denom = np.sqrt(var_matrix[:, left_index] + var_matrix[:, right_index] + 1e-6)
                z = (mean_matrix[:, left_index] - mean_matrix[:, right_index]) / denom
                z = np.clip(z, -20.0, 20.0)
                win_prob = 1.0 / (1.0 + np.exp(-z))
                preference_scores[:, left_index] += win_prob
                preference_scores[:, right_index] += 1.0 - win_prob
        return preference_scores

    if bundle.model_kind == "pairwise_heteroscedastic":
        preference_scores = np.zeros((len(frame), len(ACTIONS)), dtype=float)
        for left_index, action_a in enumerate(ACTIONS):
            for right_index in range(left_index + 1, len(ACTIONS)):
                action_b = ACTIONS[right_index]
                key = f"{action_a}__vs__{action_b}"
                mean_diff = bundle.regressors[key]["mean"].predict(feature_matrix)
                var_diff = np.exp(
                    np.clip(bundle.regressors[key]["logvar"].predict(feature_matrix), -6.0, 6.0)
                )
                z = mean_diff / np.sqrt(var_diff + 1e-6)
                z = np.clip(z, -20.0, 20.0)
                win_prob = 1.0 / (1.0 + np.exp(-z))
                preference_scores[:, left_index] += win_prob
                preference_scores[:, right_index] += 1.0 - win_prob
        return preference_scores

    if bundle.model_kind == "shared_covariance_heteroscedastic":
        mean_matrix = np.stack(
            [bundle.regressors[action]["mean"].predict(feature_matrix) for action in ACTIONS],
            axis=1,
        )
        scale = np.exp(np.clip(bundle.regressors["shared_scale_model"].predict(feature_matrix), -6.0, 6.0))
        covariance_template = np.asarray(bundle.regressors["covariance_template"], dtype=float)
        preference_scores = np.zeros((len(frame), len(ACTIONS)), dtype=float)
        for left_index in range(len(ACTIONS)):
            for right_index in range(left_index + 1, len(ACTIONS)):
                base_var = (
                    covariance_template[left_index, left_index]
                    + covariance_template[right_index, right_index]
                    - 2.0 * covariance_template[left_index, right_index]
                )
                diff_var = np.clip(scale * base_var, 1e-6, None)
                z = (mean_matrix[:, left_index] - mean_matrix[:, right_index]) / np.sqrt(diff_var)
                z = np.clip(z, -20.0, 20.0)
                win_prob = 1.0 / (1.0 + np.exp(-z))
                preference_scores[:, left_index] += win_prob
                preference_scores[:, right_index] += 1.0 - win_prob
        return preference_scores

    if bundle.model_kind == "lowrank_heteroscedastic_gaussian":
        mean_matrix = np.stack(
            [bundle.regressors[action]["mean"].predict(feature_matrix) for action in ACTIONS],
            axis=1,
        )
        var_matrix = np.stack(
            [
                np.exp(np.clip(bundle.regressors[action]["logvar"].predict(feature_matrix), -6.0, 6.0))
                for action in ACTIONS
            ],
            axis=1,
        )
        loading_matrix = bundle.regressors.get("loading_matrix")
        factor_models = bundle.regressors.get("factor_models")
        if loading_matrix is None or factor_models is None:
            loading_matrix = np.asarray(bundle.regressors["loading_vector"], dtype=float)[:, None]
            factor_models = [bundle.regressors["factor_model"]]
        else:
            loading_matrix = np.asarray(loading_matrix, dtype=float)
        factor_var_matrix = (
            np.column_stack(
                [np.exp(np.clip(model.predict(feature_matrix), -6.0, 6.0)) for model in factor_models]
            )
            if factor_models
            else np.zeros((len(frame), 0), dtype=float)
        )
        preference_scores = np.zeros((len(frame), len(ACTIONS)), dtype=float)
        for left_index in range(len(ACTIONS)):
            for right_index in range(left_index + 1, len(ACTIONS)):
                loading_diff = loading_matrix[left_index, :] - loading_matrix[right_index, :]
                diff_var = (
                    var_matrix[:, left_index]
                    + var_matrix[:, right_index]
                )
                if factor_var_matrix.shape[1] > 0:
                    diff_var = diff_var + np.sum(
                        factor_var_matrix * np.square(loading_diff[None, :]),
                        axis=1,
                    )
                z = (mean_matrix[:, left_index] - mean_matrix[:, right_index]) / np.sqrt(np.clip(diff_var, 1e-6, None))
                z = np.clip(z, -20.0, 20.0)
                win_prob = 1.0 / (1.0 + np.exp(-z))
                preference_scores[:, left_index] += win_prob
                preference_scores[:, right_index] += 1.0 - win_prob
        return preference_scores

    if bundle.model_kind == "conditional_lowrank_heteroscedastic_gaussian":
        mean_matrix = np.stack(
            [bundle.regressors[action]["mean"].predict(feature_matrix) for action in ACTIONS],
            axis=1,
        )
        var_matrix = np.stack(
            [
                np.exp(np.clip(bundle.regressors[action]["logvar"].predict(feature_matrix), -6.0, 6.0))
                for action in ACTIONS
            ],
            axis=1,
        )
        loading_templates = np.asarray(bundle.regressors["loading_templates"], dtype=float)
        factor_models = bundle.regressors["factor_models"]
        gate_prob = bundle.regressors["gate_model"].predict_proba(feature_matrix)[:, 1]
        factor_var_matrix = np.column_stack(
            [np.exp(np.clip(model.predict(feature_matrix), -6.0, 6.0)) for model in factor_models]
        )
        preference_scores = np.zeros((len(frame), len(ACTIONS)), dtype=float)
        for left_index in range(len(ACTIONS)):
            for right_index in range(left_index + 1, len(ACTIONS)):
                diff_var = var_matrix[:, left_index] + var_matrix[:, right_index]
                low_diff = float((loading_templates[left_index, 0] - loading_templates[right_index, 0]) ** 2)
                high_diff = float((loading_templates[left_index, 1] - loading_templates[right_index, 1]) ** 2)
                diff_var = diff_var + (1.0 - gate_prob) * factor_var_matrix[:, 0] * low_diff
                diff_var = diff_var + gate_prob * factor_var_matrix[:, 1] * high_diff
                z = (mean_matrix[:, left_index] - mean_matrix[:, right_index]) / np.sqrt(np.clip(diff_var, 1e-6, None))
                z = np.clip(z, -20.0, 20.0)
                win_prob = 1.0 / (1.0 + np.exp(-z))
                preference_scores[:, left_index] += win_prob
                preference_scores[:, right_index] += 1.0 - win_prob
        return preference_scores

    utilities = np.stack(
        [bundle.regressors[action].predict(feature_matrix) for action in ACTIONS],
        axis=1,
    )
    return utilities


def predict_actions(bundle: ActionValueBundle, frame: pd.DataFrame, feature_columns: list[str]) -> list[str]:
    utilities = score_action_values(bundle, frame, feature_columns)
    action_indices = np.argmax(utilities, axis=1)
    return [ACTIONS[index] for index in action_indices]


def fit_joint_pairwise_gate(
    train_exact_state: pd.DataFrame,
    train_predicted_state: pd.DataFrame,
    calibration_state: pd.DataFrame,
    state_mode: str,
) -> ActionValueBundle:
    exact_feature_columns = state_mode_feature_columns(state_mode)[1]
    predicted_feature_columns = exact_feature_columns + state_uncertainty_columns(state_mode)
    gate_feature_columns = predicted_feature_columns

    exact_bundle = fit_action_value_heads(
        train_exact_state,
        exact_feature_columns,
        state_mode,
        "pairwise_interaction_logit",
    )
    predicted_bundle = fit_action_value_heads(
        train_predicted_state,
        predicted_feature_columns,
        state_mode,
        "uncertainty_pairwise_interaction_logit",
    )

    exact_actions = predict_actions(exact_bundle, calibration_state, exact_feature_columns)
    predicted_actions = predict_actions(predicted_bundle, calibration_state, predicted_feature_columns)
    exact_utilities = np.array(
        [calibration_state.iloc[index][UTILITY_COLUMNS[action]] for index, action in enumerate(exact_actions)],
        dtype=float,
    )
    predicted_utilities = np.array(
        [calibration_state.iloc[index][UTILITY_COLUMNS[action]] for index, action in enumerate(predicted_actions)],
        dtype=float,
    )
    gate_labels = (predicted_utilities > exact_utilities).astype(int)
    gate_weights = np.abs(predicted_utilities - exact_utilities) + 1e-3
    gate_model = _fit_gate_classifier(calibration_state, gate_feature_columns, gate_labels, gate_weights)

    return ActionValueBundle(
        model_kind="gated_mixture",
        regressors={
            "exact_bundle": exact_bundle,
            "predicted_bundle": predicted_bundle,
            "gate_model": gate_model,
        },
        metadata={
            "exact_feature_columns": exact_feature_columns,
            "predicted_feature_columns": predicted_feature_columns,
            "gate_feature_columns": gate_feature_columns,
        },
    )


def fit_pairwise_error_calibrated_bundle(
    train_exact_state: pd.DataFrame,
    calibration_state: pd.DataFrame,
    state_mode: str,
) -> ActionValueBundle:
    base_feature_columns = state_mode_feature_columns(state_mode)[1]
    risk_feature_columns = base_feature_columns + state_uncertainty_columns(state_mode)

    base_bundle = fit_action_value_heads(
        train_exact_state,
        base_feature_columns,
        state_mode,
        "pairwise_interaction_logit",
    )

    error_models: dict[str, object] = {}
    base_features = calibration_state[base_feature_columns]
    risk_features = calibration_state[risk_feature_columns]
    for action_a, action_b in combinations(ACTIONS, 2):
        key = f"{action_a}__vs__{action_b}"
        utility_diff = (
            calibration_state[UTILITY_COLUMNS[action_a]].to_numpy(dtype=float)
            - calibration_state[UTILITY_COLUMNS[action_b]].to_numpy(dtype=float)
        )
        labels = (utility_diff > 0.0).astype(float)
        base_prob = base_bundle.regressors[key].predict_proba(base_features)[:, 1]
        error_targets = np.abs(base_prob - labels)
        sample_weights = np.abs(utility_diff) + 1e-3
        if np.allclose(error_targets, error_targets[0]):
            error_models[key] = ConstantRegressor(float(error_targets[0]))
            continue
        regressor = _build_error_regressor()
        regressor.fit(risk_features, error_targets, ridge__sample_weight=sample_weights)
        error_models[key] = regressor

    return ActionValueBundle(
        model_kind="pairwise_error_calibrated",
        regressors={
            "base_bundle": base_bundle,
            "error_models": error_models,
        },
        metadata={
            "base_feature_columns": base_feature_columns,
            "risk_feature_columns": risk_feature_columns,
        },
    )


def fit_conditional_lowrank_pairwise_error_calibrated_bundle(
    train_exact_state: pd.DataFrame,
    calibration_state: pd.DataFrame,
    state_mode: str,
) -> ActionValueBundle:
    base_feature_columns = state_mode_feature_columns(state_mode)[1] + state_uncertainty_columns(state_mode)
    risk_feature_columns = base_feature_columns

    base_bundle = fit_action_value_heads(
        train_exact_state,
        base_feature_columns,
        state_mode,
        "uncertainty_conditional_lowrank_heteroscedastic_interaction",
    )

    error_models: dict[str, object] = {}
    pairwise_probs = _pairwise_probability_map(base_bundle, calibration_state, base_feature_columns)
    for action_a, action_b in combinations(ACTIONS, 2):
        key = f"{action_a}__vs__{action_b}"
        utility_diff = (
            calibration_state[UTILITY_COLUMNS[action_a]].to_numpy(dtype=float)
            - calibration_state[UTILITY_COLUMNS[action_b]].to_numpy(dtype=float)
        )
        labels = (utility_diff > 0.0).astype(float)
        base_prob = pairwise_probs[key]
        error_targets = np.abs(base_prob - labels)
        sample_weights = np.abs(utility_diff) + 1e-3
        if np.allclose(error_targets, error_targets[0]):
            error_models[key] = ConstantRegressor(float(error_targets[0]))
            continue
        meta_features = _pairwise_meta_feature_frame(
            calibration_state,
            risk_feature_columns,
            base_prob,
        )
        regressor = _build_error_regressor()
        regressor.fit(meta_features, error_targets, ridge__sample_weight=sample_weights)
        error_models[key] = regressor

    return ActionValueBundle(
        model_kind="conditional_lowrank_pairwise_error_calibrated",
        regressors={
            "base_bundle": base_bundle,
            "error_models": error_models,
        },
        metadata={
            "base_feature_columns": base_feature_columns,
            "risk_feature_columns": risk_feature_columns,
        },
    )


def fit_conditional_lowrank_selective_pairwise_error_calibrated_bundle(
    train_exact_state: pd.DataFrame,
    calibration_state: pd.DataFrame,
    state_mode: str,
) -> ActionValueBundle:
    error_bundle = fit_conditional_lowrank_pairwise_error_calibrated_bundle(
        train_exact_state=train_exact_state,
        calibration_state=calibration_state,
        state_mode=state_mode,
    )
    base_bundle = error_bundle.regressors["base_bundle"]
    error_models = error_bundle.regressors["error_models"]
    base_feature_columns = error_bundle.metadata["base_feature_columns"]
    risk_feature_columns = error_bundle.metadata["risk_feature_columns"]

    gate_models: dict[str, object] = {}
    pairwise_probs = _pairwise_probability_map(base_bundle, calibration_state, base_feature_columns)
    for action_a, action_b in combinations(ACTIONS, 2):
        key = f"{action_a}__vs__{action_b}"
        utility_diff = (
            calibration_state[UTILITY_COLUMNS[action_a]].to_numpy(dtype=float)
            - calibration_state[UTILITY_COLUMNS[action_b]].to_numpy(dtype=float)
        )
        labels = (utility_diff > 0.0).astype(float)
        base_prob = pairwise_probs[key]
        meta_features = _pairwise_meta_feature_frame(
            calibration_state,
            risk_feature_columns,
            base_prob,
        )
        error_hat = np.clip(error_models[key].predict(meta_features), 0.0, 1.0)
        calibrated_prob = 0.5 + (1.0 - error_hat) * (base_prob - 0.5)
        base_loss = np.abs(base_prob - labels)
        calibrated_loss = np.abs(calibrated_prob - labels)
        gate_labels = (calibrated_loss + 1e-6 < base_loss).astype(int)
        gate_weights = (np.abs(base_loss - calibrated_loss) + 1e-3) * (np.abs(utility_diff) + 1e-3)
        gate_models[key] = _fit_gate_classifier(
            meta_features,
            list(meta_features.columns),
            gate_labels,
            gate_weights,
        )

    return ActionValueBundle(
        model_kind="conditional_lowrank_selective_pairwise_error_calibrated",
        regressors={
            "base_bundle": base_bundle,
            "error_models": error_models,
            "gate_models": gate_models,
        },
        metadata={
            "base_feature_columns": base_feature_columns,
            "risk_feature_columns": risk_feature_columns,
        },
    )


def fit_conditional_lowrank_capped_pairwise_error_calibrated_bundle(
    train_exact_state: pd.DataFrame,
    calibration_state: pd.DataFrame,
    state_mode: str,
) -> ActionValueBundle:
    error_bundle = fit_conditional_lowrank_pairwise_error_calibrated_bundle(
        train_exact_state=train_exact_state,
        calibration_state=calibration_state,
        state_mode=state_mode,
    )
    base_bundle = error_bundle.regressors["base_bundle"]
    error_models = error_bundle.regressors["error_models"]
    base_feature_columns = error_bundle.metadata["base_feature_columns"]
    risk_feature_columns = error_bundle.metadata["risk_feature_columns"]

    cap_params: dict[str, dict[str, float]] = {}
    pairwise_probs = _pairwise_probability_map(base_bundle, calibration_state, base_feature_columns)
    floor_grid = [0.2, 0.35, 0.5, 0.65, 0.8]
    for action_a, action_b in combinations(ACTIONS, 2):
        key = f"{action_a}__vs__{action_b}"
        utility_diff = (
            calibration_state[UTILITY_COLUMNS[action_a]].to_numpy(dtype=float)
            - calibration_state[UTILITY_COLUMNS[action_b]].to_numpy(dtype=float)
        )
        labels = (utility_diff > 0.0).astype(float)
        sample_weights = np.abs(utility_diff) + 1e-3
        base_prob = pairwise_probs[key]
        meta_features = _pairwise_meta_feature_frame(
            calibration_state,
            risk_feature_columns,
            base_prob,
        )
        error_hat = np.clip(error_models[key].predict(meta_features), 0.0, 1.0)
        confidence = np.abs(base_prob - 0.5)
        quantile_levels = [0.5, 0.65, 0.8, 0.9]
        threshold_grid = sorted({0.0, *[float(np.quantile(confidence, q)) for q in quantile_levels]})

        best_loss = float("inf")
        best_threshold = 0.0
        best_floor = 0.5
        for threshold in threshold_grid:
            no_shrink_mask = confidence >= threshold
            for floor in floor_grid:
                retention = np.maximum(1.0 - error_hat, floor)
                candidate_prob = np.where(
                    no_shrink_mask,
                    base_prob,
                    0.5 + retention * (base_prob - 0.5),
                )
                loss = float(np.average(np.abs(candidate_prob - labels), weights=sample_weights))
                if loss < best_loss:
                    best_loss = loss
                    best_threshold = threshold
                    best_floor = floor
        cap_params[key] = {
            "confidence_threshold": best_threshold,
            "retention_floor": best_floor,
        }

    return ActionValueBundle(
        model_kind="conditional_lowrank_capped_pairwise_error_calibrated",
        regressors={
            "base_bundle": base_bundle,
            "error_models": error_models,
            "cap_params": cap_params,
        },
        metadata={
            "base_feature_columns": base_feature_columns,
            "risk_feature_columns": risk_feature_columns,
        },
    )


def fit_conditional_lowrank_banded_pairwise_error_calibrated_bundle(
    train_exact_state: pd.DataFrame,
    calibration_state: pd.DataFrame,
    state_mode: str,
) -> ActionValueBundle:
    error_bundle = fit_conditional_lowrank_pairwise_error_calibrated_bundle(
        train_exact_state=train_exact_state,
        calibration_state=calibration_state,
        state_mode=state_mode,
    )
    base_bundle = error_bundle.regressors["base_bundle"]
    error_models = error_bundle.regressors["error_models"]
    base_feature_columns = error_bundle.metadata["base_feature_columns"]
    risk_feature_columns = error_bundle.metadata["risk_feature_columns"]

    band_params: dict[str, dict[str, float]] = {}
    pairwise_probs = _pairwise_probability_map(base_bundle, calibration_state, base_feature_columns)
    floor_grid = [0.2, 0.35, 0.5, 0.65, 0.8]
    for action_a, action_b in combinations(ACTIONS, 2):
        key = f"{action_a}__vs__{action_b}"
        utility_diff = (
            calibration_state[UTILITY_COLUMNS[action_a]].to_numpy(dtype=float)
            - calibration_state[UTILITY_COLUMNS[action_b]].to_numpy(dtype=float)
        )
        labels = (utility_diff > 0.0).astype(float)
        sample_weights = np.abs(utility_diff) + 1e-3
        base_prob = pairwise_probs[key]
        meta_features = _pairwise_meta_feature_frame(
            calibration_state,
            risk_feature_columns,
            base_prob,
        )
        error_hat = np.clip(error_models[key].predict(meta_features), 0.0, 1.0)
        confidence = np.abs(base_prob - 0.5)
        quantile_levels = [0.35, 0.5, 0.65, 0.8, 0.9]
        threshold_grid = sorted({0.0, *[float(np.quantile(confidence, q)) for q in quantile_levels]})

        best_loss = float("inf")
        best_low = 0.0
        best_high = 0.0
        best_floor = 0.5
        for low_threshold in threshold_grid:
            for high_threshold in threshold_grid:
                if high_threshold < low_threshold:
                    continue
                low_conf_mask = confidence < low_threshold
                high_conf_mask = confidence >= high_threshold
                mid_conf_mask = ~(low_conf_mask | high_conf_mask)
                for floor in floor_grid:
                    full_shrink = 0.5 + (1.0 - error_hat) * (base_prob - 0.5)
                    capped_shrink = 0.5 + np.maximum(1.0 - error_hat, floor) * (base_prob - 0.5)
                    candidate_prob = np.where(
                        high_conf_mask,
                        base_prob,
                        np.where(mid_conf_mask, capped_shrink, full_shrink),
                    )
                    loss = float(np.average(np.abs(candidate_prob - labels), weights=sample_weights))
                    if loss < best_loss:
                        best_loss = loss
                        best_low = low_threshold
                        best_high = high_threshold
                        best_floor = floor
        band_params[key] = {
            "low_confidence_threshold": best_low,
            "high_confidence_threshold": best_high,
            "retention_floor": best_floor,
        }

    return ActionValueBundle(
        model_kind="conditional_lowrank_banded_pairwise_error_calibrated",
        regressors={
            "base_bundle": base_bundle,
            "error_models": error_models,
            "band_params": band_params,
        },
        metadata={
            "base_feature_columns": base_feature_columns,
            "risk_feature_columns": risk_feature_columns,
        },
    )


def fit_conditional_lowrank_clustered_pairwise_error_calibrated_bundle(
    train_exact_state: pd.DataFrame,
    calibration_state: pd.DataFrame,
    state_mode: str,
) -> ActionValueBundle:
    error_bundle = fit_conditional_lowrank_pairwise_error_calibrated_bundle(
        train_exact_state=train_exact_state,
        calibration_state=calibration_state,
        state_mode=state_mode,
    )
    base_bundle = error_bundle.regressors["base_bundle"]
    error_models = error_bundle.regressors["error_models"]
    base_feature_columns = error_bundle.metadata["base_feature_columns"]
    risk_feature_columns = error_bundle.metadata["risk_feature_columns"]

    cluster_models: dict[str, object] = {}
    cluster_params: dict[str, dict[int, dict[str, float | str]]] = {}
    pairwise_probs = _pairwise_probability_map(base_bundle, calibration_state, base_feature_columns)
    for action_a, action_b in combinations(ACTIONS, 2):
        key = f"{action_a}__vs__{action_b}"
        utility_diff = (
            calibration_state[UTILITY_COLUMNS[action_a]].to_numpy(dtype=float)
            - calibration_state[UTILITY_COLUMNS[action_b]].to_numpy(dtype=float)
        )
        labels = (utility_diff > 0.0).astype(float)
        sample_weights = np.abs(utility_diff) + 1e-3
        base_prob = pairwise_probs[key]
        meta_features = _pairwise_meta_feature_frame(
            calibration_state,
            risk_feature_columns,
            base_prob,
        )
        error_hat = np.clip(error_models[key].predict(meta_features), 0.0, 1.0)
        cluster_model = _fit_pairwise_cluster_model(meta_features)
        cluster_labels = cluster_model.predict(meta_features).astype(int)
        cluster_models[key] = cluster_model
        cluster_params[key] = {}
        for cluster_id in np.unique(cluster_labels):
            cluster_mask = cluster_labels == cluster_id
            cluster_params[key][int(cluster_id)] = _select_cluster_shrinkage_strategy(
                base_prob=base_prob[cluster_mask],
                error_hat=error_hat[cluster_mask],
                labels=labels[cluster_mask],
                sample_weights=sample_weights[cluster_mask],
            )

    return ActionValueBundle(
        model_kind="conditional_lowrank_clustered_pairwise_error_calibrated",
        regressors={
            "base_bundle": base_bundle,
            "error_models": error_models,
            "cluster_models": cluster_models,
            "cluster_params": cluster_params,
        },
        metadata={
            "base_feature_columns": base_feature_columns,
            "risk_feature_columns": risk_feature_columns,
        },
    )


def fit_pairwise_meta_calibrated_bundle(
    train_exact_state: pd.DataFrame,
    calibration_state: pd.DataFrame,
    state_mode: str,
) -> ActionValueBundle:
    base_feature_columns = state_mode_feature_columns(state_mode)[1]
    risk_feature_columns = base_feature_columns + state_uncertainty_columns(state_mode)

    base_bundle = fit_action_value_heads(
        train_exact_state,
        base_feature_columns,
        state_mode,
        "pairwise_interaction_logit",
    )

    meta_models: dict[str, object] = {}
    base_features = calibration_state[base_feature_columns]
    for action_a, action_b in combinations(ACTIONS, 2):
        key = f"{action_a}__vs__{action_b}"
        utility_diff = (
            calibration_state[UTILITY_COLUMNS[action_a]].to_numpy(dtype=float)
            - calibration_state[UTILITY_COLUMNS[action_b]].to_numpy(dtype=float)
        )
        labels = (utility_diff > 0.0).astype(int)
        sample_weights = np.abs(utility_diff) + 1e-3
        if np.unique(labels).size < 2:
            meta_models[key] = ConstantBinaryClassifier(float(labels[0]))
            continue
        base_prob = base_bundle.regressors[key].predict_proba(base_features)[:, 1]
        meta_features = _pairwise_meta_feature_frame(
            calibration_state,
            risk_feature_columns,
            base_prob,
        )
        classifier = _build_meta_pairwise_classifier()
        classifier.fit(meta_features, labels, logreg__sample_weight=sample_weights)
        meta_models[key] = classifier

    return ActionValueBundle(
        model_kind="pairwise_meta_calibrated",
        regressors={
            "base_bundle": base_bundle,
            "meta_models": meta_models,
        },
        metadata={
            "base_feature_columns": base_feature_columns,
            "risk_feature_columns": risk_feature_columns,
        },
    )


def fit_pairwise_selective_calibrated_bundle(
    train_exact_state: pd.DataFrame,
    calibration_state: pd.DataFrame,
    state_mode: str,
) -> ActionValueBundle:
    error_bundle = fit_pairwise_error_calibrated_bundle(
        train_exact_state=train_exact_state,
        calibration_state=calibration_state,
        state_mode=state_mode,
    )
    base_bundle = error_bundle.regressors["base_bundle"]
    error_models = error_bundle.regressors["error_models"]
    base_feature_columns = error_bundle.metadata["base_feature_columns"]
    risk_feature_columns = error_bundle.metadata["risk_feature_columns"]

    gate_models: dict[str, object] = {}
    base_features = calibration_state[base_feature_columns]
    risk_features = calibration_state[risk_feature_columns]
    for action_a, action_b in combinations(ACTIONS, 2):
        key = f"{action_a}__vs__{action_b}"
        utility_diff = (
            calibration_state[UTILITY_COLUMNS[action_a]].to_numpy(dtype=float)
            - calibration_state[UTILITY_COLUMNS[action_b]].to_numpy(dtype=float)
        )
        labels = (utility_diff > 0.0).astype(float)
        base_prob = base_bundle.regressors[key].predict_proba(base_features)[:, 1]
        error_hat = np.clip(error_models[key].predict(risk_features), 0.0, 1.0)
        calibrated_prob = 0.5 + (1.0 - error_hat) * (base_prob - 0.5)
        base_loss = np.abs(base_prob - labels)
        calibrated_loss = np.abs(calibrated_prob - labels)
        gate_labels = (calibrated_loss + 1e-6 < base_loss).astype(int)
        gate_weights = (np.abs(base_loss - calibrated_loss) + 1e-3) * (np.abs(utility_diff) + 1e-3)
        gate_features = _pairwise_meta_feature_frame(
            calibration_state,
            risk_feature_columns,
            base_prob,
        )
        gate_models[key] = _fit_gate_classifier(
            gate_features,
            list(gate_features.columns),
            gate_labels,
            gate_weights,
        )

    return ActionValueBundle(
        model_kind="pairwise_selective_calibrated",
        regressors={
            "base_bundle": base_bundle,
            "error_models": error_models,
            "gate_models": gate_models,
        },
        metadata={
            "base_feature_columns": base_feature_columns,
            "risk_feature_columns": risk_feature_columns,
        },
    )


def evaluate_state_heads(
    frame_with_predictions: pd.DataFrame,
    state_mode: str,
) -> dict[str, float]:
    q_true = frame_with_predictions["prefix_invalid"].to_numpy(dtype=float)
    q_hat = frame_with_predictions["q_hat"].to_numpy(dtype=float)

    metrics = {
        "q_brier": float(np.mean((q_true - q_hat) ** 2)),
    }
    if len(np.unique(q_true)) > 1:
        metrics["q_auc"] = float(roc_auc_score(q_true, q_hat))
    else:
        metrics["q_auc"] = float("nan")

    for target_column, pred_column, _, _ in STATE_MODE_CONFIG[state_mode]["state_targets"]:
        metric_name = target_column.replace("continue_", "").replace("_utility", "").replace("_tokens", "_tok")
        metrics[f"{metric_name}_rmse"] = float(
            np.sqrt(
                mean_squared_error(
                    frame_with_predictions[target_column].to_numpy(dtype=float),
                    frame_with_predictions[pred_column].to_numpy(dtype=float),
                )
            )
        )
    return metrics


def prepare_factorized_split_states(
    train_frame: pd.DataFrame,
    test_frame: pd.DataFrame,
    q_embedding_columns: list[str],
    s_embedding_columns: list[str] | None,
    state_mode: str,
    state_head_model: str,
    value_head_model: str,
    group_column: str = "sample_id",
) -> dict[str, object]:
    if state_mode not in STATE_MODE_CONFIG:
        raise ValueError(f"Unsupported state_mode: {state_mode}")

    train_frame = ensure_base_context_columns(train_frame)
    test_frame = ensure_base_context_columns(test_frame)
    s_embedding_columns = list(s_embedding_columns or q_embedding_columns)
    exact_columns, pred_columns = state_mode_feature_columns(state_mode)
    uncertainty_columns = state_uncertainty_columns(state_mode)
    use_uncertainty = requires_uncertainty_features(value_head_model)
    exact_feature_columns = pred_columns + uncertainty_columns if use_uncertainty else exact_columns
    pred_feature_columns = pred_columns + uncertainty_columns if use_uncertainty else pred_columns

    if use_uncertainty:
        committee = fit_state_head_committee(
            train_frame,
            q_embedding_columns,
            s_embedding_columns,
            state_mode,
            state_head_model,
            group_column,
        )
        train_state = apply_state_head_committee(
            committee,
            train_frame,
            q_embedding_columns,
            s_embedding_columns,
            state_mode,
        )
        test_state = apply_state_head_committee(
            committee,
            test_frame,
            q_embedding_columns,
            s_embedding_columns,
            state_mode,
        )
        train_oof_state = build_oof_predicted_state_frame(
            train_frame,
            q_embedding_columns,
            s_embedding_columns,
            state_mode,
            state_head_model,
            group_column,
            with_uncertainty=True,
        )
        train_exact_state = build_exact_state_frame(train_frame, state_mode, include_uncertainty=True)
        test_exact_state = build_exact_state_frame(test_frame, state_mode, include_uncertainty=True)
    else:
        state_heads = fit_state_heads(
            train_frame,
            q_embedding_columns,
            s_embedding_columns,
            state_mode,
            state_head_model,
        )
        train_state = apply_state_heads(
            state_heads,
            train_frame,
            q_embedding_columns,
            s_embedding_columns,
            state_mode,
        )
        test_state = apply_state_heads(
            state_heads,
            test_frame,
            q_embedding_columns,
            s_embedding_columns,
            state_mode,
        )
        train_oof_state = build_oof_predicted_state_frame(
            train_frame,
            q_embedding_columns,
            s_embedding_columns,
            state_mode,
            state_head_model,
            group_column,
        )
        train_exact_state = build_exact_state_frame(train_frame, state_mode)
        test_exact_state = build_exact_state_frame(test_frame, state_mode)

    return {
        "train_state": train_state,
        "test_state": test_state,
        "train_oof_state": train_oof_state,
        "train_exact_state": train_exact_state,
        "test_exact_state": test_exact_state,
        "exact_feature_columns": exact_feature_columns,
        "pred_feature_columns": pred_feature_columns,
        "state_metrics": evaluate_state_heads(test_state, state_mode),
    }


def run_factorized_cv(
    frame: pd.DataFrame,
    q_embedding_columns: list[str],
    s_embedding_columns: list[str] | None = None,
    group_column: str = "sample_id",
    n_splits: int = 5,
    state_mode: str = "legacy",
    state_head_model: str = "linear",
    value_head_model: str = "ridge",
) -> pd.DataFrame:
    if state_mode not in STATE_MODE_CONFIG:
        raise ValueError(f"Unsupported state_mode: {state_mode}")
    frame = ensure_base_context_columns(frame)
    s_embedding_columns = list(s_embedding_columns or q_embedding_columns)
    exact_columns, pred_columns = state_mode_feature_columns(state_mode)
    uncertainty_columns = state_uncertainty_columns(state_mode)
    use_joint_pairwise_gate = value_head_model == "joint_pairwise_gate"
    use_pairwise_error_calibrated = value_head_model == "pairwise_error_calibrated"
    use_conditional_lowrank_pairwise_error_calibrated = (
        value_head_model == "conditional_lowrank_pairwise_error_calibrated"
    )
    use_conditional_lowrank_selective_pairwise_error_calibrated = (
        value_head_model == "conditional_lowrank_selective_pairwise_error_calibrated"
    )
    use_conditional_lowrank_capped_pairwise_error_calibrated = (
        value_head_model == "conditional_lowrank_capped_pairwise_error_calibrated"
    )
    use_conditional_lowrank_banded_pairwise_error_calibrated = (
        value_head_model == "conditional_lowrank_banded_pairwise_error_calibrated"
    )
    use_conditional_lowrank_clustered_pairwise_error_calibrated = (
        value_head_model == "conditional_lowrank_clustered_pairwise_error_calibrated"
    )
    use_pairwise_meta_calibrated = value_head_model == "pairwise_meta_calibrated"
    use_pairwise_selective_calibrated = value_head_model == "pairwise_selective_calibrated"
    use_uncertainty_features = (
        _uses_uncertainty_features(value_head_model)
        or use_joint_pairwise_gate
        or use_pairwise_error_calibrated
        or use_conditional_lowrank_pairwise_error_calibrated
        or use_conditional_lowrank_selective_pairwise_error_calibrated
        or use_conditional_lowrank_capped_pairwise_error_calibrated
        or use_conditional_lowrank_banded_pairwise_error_calibrated
        or use_conditional_lowrank_clustered_pairwise_error_calibrated
        or use_pairwise_meta_calibrated
        or use_pairwise_selective_calibrated
    )
    exact_feature_columns = pred_columns + uncertainty_columns if use_uncertainty_features else exact_columns
    pred_feature_columns = pred_columns + uncertainty_columns if use_uncertainty_features else pred_columns
    unique_groups = frame[group_column].nunique()
    effective_splits = min(n_splits, unique_groups)
    if effective_splits < 2:
        raise ValueError("Need at least 2 groups for cross-validation")

    splitter = GroupKFold(n_splits=effective_splits)
    records: list[dict[str, float | int | str]] = []
    for fold_index, (train_index, test_index) in enumerate(
        splitter.split(frame, groups=frame[group_column]),
        start=1,
    ):
        train_frame = frame.iloc[train_index].reset_index(drop=True)
        test_frame = frame.iloc[test_index].reset_index(drop=True)

        if use_uncertainty_features:
            committee = fit_state_head_committee(
                train_frame,
                q_embedding_columns,
                s_embedding_columns,
                state_mode,
                state_head_model,
                group_column,
            )
            train_state = apply_state_head_committee(
                committee,
                train_frame,
                q_embedding_columns,
                s_embedding_columns,
                state_mode,
            )
            test_state = apply_state_head_committee(
                committee,
                test_frame,
                q_embedding_columns,
                s_embedding_columns,
                state_mode,
            )
            train_oof_state = build_oof_predicted_state_frame(
                train_frame,
                q_embedding_columns,
                s_embedding_columns,
                state_mode,
                state_head_model,
                group_column,
                with_uncertainty=True,
            )
            train_exact_state = build_exact_state_frame(train_frame, state_mode, include_uncertainty=True)
            test_exact_state = build_exact_state_frame(test_frame, state_mode, include_uncertainty=True)
        else:
            state_heads = fit_state_heads(
                train_frame,
                q_embedding_columns,
                s_embedding_columns,
                state_mode,
                state_head_model,
            )
            train_state = apply_state_heads(
                state_heads,
                train_frame,
                q_embedding_columns,
                s_embedding_columns,
                state_mode,
            )
            test_state = apply_state_heads(state_heads, test_frame, q_embedding_columns, s_embedding_columns, state_mode)
            train_oof_state = build_oof_predicted_state_frame(
                train_frame,
                q_embedding_columns,
                s_embedding_columns,
                state_mode,
                state_head_model,
                group_column,
            )
            train_exact_state = build_exact_state_frame(train_frame, state_mode)
            test_exact_state = build_exact_state_frame(test_frame, state_mode)
        state_metrics = evaluate_state_heads(test_state, state_mode)

        if use_joint_pairwise_gate:
            joint_bundle = fit_joint_pairwise_gate(
                train_exact_state=train_exact_state,
                train_predicted_state=train_state,
                calibration_state=train_oof_state,
                state_mode=state_mode,
            )
            exact_pred = predict_actions(
                joint_bundle.regressors["exact_bundle"],
                test_exact_state,
                joint_bundle.metadata["exact_feature_columns"],
            )
            exact_metrics = evaluate_policy(test_frame, exact_pred)
            records.append(
                {
                    "baseline": "factorized_exact_state",
                    "state_mode": state_mode,
                    "state_head_model": state_head_model,
                    "value_head_model": value_head_model,
                    "fold": fold_index,
                    "num_train": len(train_frame),
                    "num_test": len(test_frame),
                    **exact_metrics,
                }
            )
            predicted_actions = predict_actions(
                joint_bundle,
                test_state,
                joint_bundle.metadata["predicted_feature_columns"],
            )
            metrics = evaluate_policy(test_frame, predicted_actions)
            records.append(
                {
                    "baseline": "factorized_predicted_state_joint_gate",
                    "state_mode": state_mode,
                    "state_head_model": state_head_model,
                    "value_head_model": value_head_model,
                    "fold": fold_index,
                    "num_train": len(train_frame),
                    "num_test": len(test_frame),
                    **metrics,
                    **state_metrics,
                }
            )
            continue

        if use_pairwise_error_calibrated:
            calibrated_bundle = fit_pairwise_error_calibrated_bundle(
                train_exact_state=train_exact_state,
                calibration_state=train_oof_state,
                state_mode=state_mode,
            )
            exact_pred = predict_actions(
                calibrated_bundle.regressors["base_bundle"],
                test_exact_state,
                calibrated_bundle.metadata["base_feature_columns"],
            )
            exact_metrics = evaluate_policy(test_frame, exact_pred)
            records.append(
                {
                    "baseline": "factorized_exact_state",
                    "state_mode": state_mode,
                    "state_head_model": state_head_model,
                    "value_head_model": value_head_model,
                    "fold": fold_index,
                    "num_train": len(train_frame),
                    "num_test": len(test_frame),
                    **exact_metrics,
                }
            )
            predicted_actions = predict_actions(
                calibrated_bundle,
                test_state,
                calibrated_bundle.metadata["risk_feature_columns"],
            )
            metrics = evaluate_policy(test_frame, predicted_actions)
            records.append(
                {
                    "baseline": "factorized_predicted_state_pairwise_error_calibrated",
                    "state_mode": state_mode,
                    "state_head_model": state_head_model,
                    "value_head_model": value_head_model,
                    "fold": fold_index,
                    "num_train": len(train_frame),
                    "num_test": len(test_frame),
                    **metrics,
                    **state_metrics,
                }
            )
            continue

        if use_conditional_lowrank_pairwise_error_calibrated:
            calibrated_bundle = fit_conditional_lowrank_pairwise_error_calibrated_bundle(
                train_exact_state=train_exact_state,
                calibration_state=train_oof_state,
                state_mode=state_mode,
            )
            exact_pred = predict_actions(
                calibrated_bundle.regressors["base_bundle"],
                test_exact_state,
                calibrated_bundle.metadata["base_feature_columns"],
            )
            exact_metrics = evaluate_policy(test_frame, exact_pred)
            records.append(
                {
                    "baseline": "factorized_exact_state",
                    "state_mode": state_mode,
                    "state_head_model": state_head_model,
                    "value_head_model": value_head_model,
                    "fold": fold_index,
                    "num_train": len(train_frame),
                    "num_test": len(test_frame),
                    **exact_metrics,
                }
            )
            predicted_actions = predict_actions(
                calibrated_bundle,
                test_state,
                calibrated_bundle.metadata["risk_feature_columns"],
            )
            metrics = evaluate_policy(test_frame, predicted_actions)
            records.append(
                {
                    "baseline": "factorized_predicted_state_conditional_lowrank_pairwise_error_calibrated",
                    "state_mode": state_mode,
                    "state_head_model": state_head_model,
                    "value_head_model": value_head_model,
                    "fold": fold_index,
                    "num_train": len(train_frame),
                    "num_test": len(test_frame),
                    **metrics,
                    **state_metrics,
                }
            )
            continue

        if use_conditional_lowrank_selective_pairwise_error_calibrated:
            calibrated_bundle = fit_conditional_lowrank_selective_pairwise_error_calibrated_bundle(
                train_exact_state=train_exact_state,
                calibration_state=train_oof_state,
                state_mode=state_mode,
            )
            exact_pred = predict_actions(
                calibrated_bundle.regressors["base_bundle"],
                test_exact_state,
                calibrated_bundle.metadata["base_feature_columns"],
            )
            exact_metrics = evaluate_policy(test_frame, exact_pred)
            records.append(
                {
                    "baseline": "factorized_exact_state",
                    "state_mode": state_mode,
                    "state_head_model": state_head_model,
                    "value_head_model": value_head_model,
                    "fold": fold_index,
                    "num_train": len(train_frame),
                    "num_test": len(test_frame),
                    **exact_metrics,
                }
            )
            predicted_actions = predict_actions(
                calibrated_bundle,
                test_state,
                calibrated_bundle.metadata["risk_feature_columns"],
            )
            metrics = evaluate_policy(test_frame, predicted_actions)
            records.append(
                {
                    "baseline": "factorized_predicted_state_conditional_lowrank_selective_pairwise_error_calibrated",
                    "state_mode": state_mode,
                    "state_head_model": state_head_model,
                    "value_head_model": value_head_model,
                    "fold": fold_index,
                    "num_train": len(train_frame),
                    "num_test": len(test_frame),
                    **metrics,
                    **state_metrics,
                }
            )
            continue

        if use_conditional_lowrank_capped_pairwise_error_calibrated:
            calibrated_bundle = fit_conditional_lowrank_capped_pairwise_error_calibrated_bundle(
                train_exact_state=train_exact_state,
                calibration_state=train_oof_state,
                state_mode=state_mode,
            )
            exact_pred = predict_actions(
                calibrated_bundle.regressors["base_bundle"],
                test_exact_state,
                calibrated_bundle.metadata["base_feature_columns"],
            )
            exact_metrics = evaluate_policy(test_frame, exact_pred)
            records.append(
                {
                    "baseline": "factorized_exact_state",
                    "state_mode": state_mode,
                    "state_head_model": state_head_model,
                    "value_head_model": value_head_model,
                    "fold": fold_index,
                    "num_train": len(train_frame),
                    "num_test": len(test_frame),
                    **exact_metrics,
                }
            )
            predicted_actions = predict_actions(
                calibrated_bundle,
                test_state,
                calibrated_bundle.metadata["risk_feature_columns"],
            )
            metrics = evaluate_policy(test_frame, predicted_actions)
            records.append(
                {
                    "baseline": "factorized_predicted_state_conditional_lowrank_capped_pairwise_error_calibrated",
                    "state_mode": state_mode,
                    "state_head_model": state_head_model,
                    "value_head_model": value_head_model,
                    "fold": fold_index,
                    "num_train": len(train_frame),
                    "num_test": len(test_frame),
                    **metrics,
                    **state_metrics,
                }
            )
            continue

        if use_conditional_lowrank_banded_pairwise_error_calibrated:
            calibrated_bundle = fit_conditional_lowrank_banded_pairwise_error_calibrated_bundle(
                train_exact_state=train_exact_state,
                calibration_state=train_oof_state,
                state_mode=state_mode,
            )
            exact_pred = predict_actions(
                calibrated_bundle.regressors["base_bundle"],
                test_exact_state,
                calibrated_bundle.metadata["base_feature_columns"],
            )
            exact_metrics = evaluate_policy(test_frame, exact_pred)
            records.append(
                {
                    "baseline": "factorized_exact_state",
                    "state_mode": state_mode,
                    "state_head_model": state_head_model,
                    "value_head_model": value_head_model,
                    "fold": fold_index,
                    "num_train": len(train_frame),
                    "num_test": len(test_frame),
                    **exact_metrics,
                }
            )
            predicted_actions = predict_actions(
                calibrated_bundle,
                test_state,
                calibrated_bundle.metadata["risk_feature_columns"],
            )
            metrics = evaluate_policy(test_frame, predicted_actions)
            records.append(
                {
                    "baseline": "factorized_predicted_state_conditional_lowrank_banded_pairwise_error_calibrated",
                    "state_mode": state_mode,
                    "state_head_model": state_head_model,
                    "value_head_model": value_head_model,
                    "fold": fold_index,
                    "num_train": len(train_frame),
                    "num_test": len(test_frame),
                    **metrics,
                    **state_metrics,
                }
            )
            continue

        if use_conditional_lowrank_clustered_pairwise_error_calibrated:
            calibrated_bundle = fit_conditional_lowrank_clustered_pairwise_error_calibrated_bundle(
                train_exact_state=train_exact_state,
                calibration_state=train_oof_state,
                state_mode=state_mode,
            )
            exact_pred = predict_actions(
                calibrated_bundle.regressors["base_bundle"],
                test_exact_state,
                calibrated_bundle.metadata["base_feature_columns"],
            )
            exact_metrics = evaluate_policy(test_frame, exact_pred)
            records.append(
                {
                    "baseline": "factorized_exact_state",
                    "state_mode": state_mode,
                    "state_head_model": state_head_model,
                    "value_head_model": value_head_model,
                    "fold": fold_index,
                    "num_train": len(train_frame),
                    "num_test": len(test_frame),
                    **exact_metrics,
                }
            )
            predicted_actions = predict_actions(
                calibrated_bundle,
                test_state,
                calibrated_bundle.metadata["risk_feature_columns"],
            )
            metrics = evaluate_policy(test_frame, predicted_actions)
            records.append(
                {
                    "baseline": "factorized_predicted_state_conditional_lowrank_clustered_pairwise_error_calibrated",
                    "state_mode": state_mode,
                    "state_head_model": state_head_model,
                    "value_head_model": value_head_model,
                    "fold": fold_index,
                    "num_train": len(train_frame),
                    "num_test": len(test_frame),
                    **metrics,
                    **state_metrics,
                }
            )
            continue

        if use_pairwise_meta_calibrated:
            calibrated_bundle = fit_pairwise_meta_calibrated_bundle(
                train_exact_state=train_exact_state,
                calibration_state=train_oof_state,
                state_mode=state_mode,
            )
            exact_pred = predict_actions(
                calibrated_bundle.regressors["base_bundle"],
                test_exact_state,
                calibrated_bundle.metadata["base_feature_columns"],
            )
            exact_metrics = evaluate_policy(test_frame, exact_pred)
            records.append(
                {
                    "baseline": "factorized_exact_state",
                    "state_mode": state_mode,
                    "state_head_model": state_head_model,
                    "value_head_model": value_head_model,
                    "fold": fold_index,
                    "num_train": len(train_frame),
                    "num_test": len(test_frame),
                    **exact_metrics,
                }
            )
            predicted_actions = predict_actions(
                calibrated_bundle,
                test_state,
                calibrated_bundle.metadata["risk_feature_columns"],
            )
            metrics = evaluate_policy(test_frame, predicted_actions)
            records.append(
                {
                    "baseline": "factorized_predicted_state_pairwise_meta_calibrated",
                    "state_mode": state_mode,
                    "state_head_model": state_head_model,
                    "value_head_model": value_head_model,
                    "fold": fold_index,
                    "num_train": len(train_frame),
                    "num_test": len(test_frame),
                    **metrics,
                    **state_metrics,
                }
            )
            continue

        if use_pairwise_selective_calibrated:
            calibrated_bundle = fit_pairwise_selective_calibrated_bundle(
                train_exact_state=train_exact_state,
                calibration_state=train_oof_state,
                state_mode=state_mode,
            )
            exact_pred = predict_actions(
                calibrated_bundle.regressors["base_bundle"],
                test_exact_state,
                calibrated_bundle.metadata["base_feature_columns"],
            )
            exact_metrics = evaluate_policy(test_frame, exact_pred)
            records.append(
                {
                    "baseline": "factorized_exact_state",
                    "state_mode": state_mode,
                    "state_head_model": state_head_model,
                    "value_head_model": value_head_model,
                    "fold": fold_index,
                    "num_train": len(train_frame),
                    "num_test": len(test_frame),
                    **exact_metrics,
                }
            )
            predicted_actions = predict_actions(
                calibrated_bundle,
                test_state,
                calibrated_bundle.metadata["risk_feature_columns"],
            )
            metrics = evaluate_policy(test_frame, predicted_actions)
            records.append(
                {
                    "baseline": "factorized_predicted_state_pairwise_selective_calibrated",
                    "state_mode": state_mode,
                    "state_head_model": state_head_model,
                    "value_head_model": value_head_model,
                    "fold": fold_index,
                    "num_train": len(train_frame),
                    "num_test": len(test_frame),
                    **metrics,
                    **state_metrics,
                }
            )
            continue

        if use_uncertainty_features:
            exact_bundle = fit_action_value_heads(
                train_exact_state,
                exact_feature_columns,
                state_mode,
                value_head_model,
            )
            exact_pred = predict_actions(exact_bundle, test_exact_state, exact_feature_columns)
        else:
            exact_bundle = fit_action_value_heads(train_frame, exact_columns, state_mode, value_head_model)
            exact_pred = predict_actions(exact_bundle, test_frame, exact_columns)
        exact_metrics = evaluate_policy(test_frame, exact_pred)
        records.append(
            {
                "baseline": "factorized_exact_state",
                "state_mode": state_mode,
                "state_head_model": state_head_model,
                "value_head_model": value_head_model,
                "fold": fold_index,
                "num_train": len(train_frame),
                "num_test": len(test_frame),
                **exact_metrics,
            }
        )

        train_variants = {
            "factorized_predicted_state_train_exact": train_exact_state,
            "factorized_predicted_state_train_predicted": train_state,
            "factorized_predicted_state_train_predicted_oof": train_oof_state,
            "factorized_predicted_state_train_exact_plus_oof": pd.concat(
                [train_exact_state, train_oof_state],
                ignore_index=True,
            ),
        }
        for baseline_name, train_variant in train_variants.items():
            value_bundle = fit_action_value_heads(train_variant, pred_feature_columns, state_mode, value_head_model)
            predicted_actions = predict_actions(value_bundle, test_state, pred_feature_columns)
            metrics = evaluate_policy(test_frame, predicted_actions)
            records.append(
                {
                    "baseline": baseline_name,
                    "state_mode": state_mode,
                    "state_head_model": state_head_model,
                    "value_head_model": value_head_model,
                    "fold": fold_index,
                    "num_train": len(train_variant),
                    "num_test": len(test_frame),
                    **metrics,
                    **state_metrics,
                }
            )
    return pd.DataFrame(records)


def run_factorized_cv_with_samples(
    frame: pd.DataFrame,
    q_embedding_columns: list[str],
    s_embedding_columns: list[str] | None = None,
    group_column: str = "sample_id",
    n_splits: int = 5,
    state_mode: str = "legacy",
    state_head_model: str = "linear",
    value_head_model: str = "ridge",
    predicted_baselines: list[str] | None = None,
    predicted_train_filter_mode: str = "all",
    high_det_gap_quantile: float = 0.5,
    teacher_distill_mode: str = "none",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if state_mode not in STATE_MODE_CONFIG:
        raise ValueError(f"Unsupported state_mode: {state_mode}")
    if requires_uncertainty_features(value_head_model) or value_head_model in {
        "pairwise_error_calibrated",
        "conditional_lowrank_pairwise_error_calibrated",
        "conditional_lowrank_selective_pairwise_error_calibrated",
        "conditional_lowrank_capped_pairwise_error_calibrated",
        "conditional_lowrank_banded_pairwise_error_calibrated",
        "conditional_lowrank_clustered_pairwise_error_calibrated",
        "pairwise_meta_calibrated",
        "pairwise_selective_calibrated",
        "joint_pairwise_gate",
    }:
        raise ValueError(
            "run_factorized_cv_with_samples currently supports only the generic non-wrapper value-head path"
        )
    if predicted_train_filter_mode not in {"all", "high_determinacy"}:
        raise ValueError(f"Unsupported predicted_train_filter_mode: {predicted_train_filter_mode}")
    if teacher_distill_mode not in {"none", "exact_oof_scores"}:
        raise ValueError(f"Unsupported teacher_distill_mode: {teacher_distill_mode}")

    frame = ensure_base_context_columns(frame)
    s_embedding_columns = list(s_embedding_columns or q_embedding_columns)
    exact_columns, pred_columns = state_mode_feature_columns(state_mode)
    unique_groups = frame[group_column].nunique()
    effective_splits = min(n_splits, unique_groups)
    if effective_splits < 2:
        raise ValueError("Need at least 2 groups for cross-validation")

    splitter = GroupKFold(n_splits=effective_splits)
    records: list[dict[str, float | int | str]] = []
    sample_frames: list[pd.DataFrame] = []
    for fold_index, (train_index, test_index) in enumerate(
        splitter.split(frame, groups=frame[group_column]),
        start=1,
    ):
        train_frame = frame.iloc[train_index].reset_index(drop=True)
        test_frame = frame.iloc[test_index].reset_index(drop=True)

        state_heads = fit_state_heads(
            train_frame,
            q_embedding_columns,
            s_embedding_columns,
            state_mode,
            state_head_model,
        )
        train_state = apply_state_heads(
            state_heads,
            train_frame,
            q_embedding_columns,
            s_embedding_columns,
            state_mode,
        )
        test_state = apply_state_heads(
            state_heads,
            test_frame,
            q_embedding_columns,
            s_embedding_columns,
            state_mode,
        )
        train_oof_state = build_oof_predicted_state_frame(
            train_frame,
            q_embedding_columns,
            s_embedding_columns,
            state_mode,
            state_head_model,
            group_column,
        )
        train_exact_state = build_exact_state_frame(train_frame, state_mode)
        test_exact_state = build_exact_state_frame(test_frame, state_mode)
        teacher_score_frame = None
        if teacher_distill_mode == "exact_oof_scores":
            teacher_score_frame = build_oof_exact_teacher_score_frame(
                train_frame,
                exact_columns,
                state_mode,
                value_head_model,
                group_column,
            )
        state_metrics = evaluate_state_heads(test_state, state_mode)

        exact_bundle = fit_action_value_heads(train_frame, exact_columns, state_mode, value_head_model)
        exact_pred = predict_actions(exact_bundle, test_frame, exact_columns)
        exact_scores = score_action_values(exact_bundle, test_frame, exact_columns)
        exact_metrics = evaluate_policy(test_frame, exact_pred)
        records.append(
            {
                "baseline": "factorized_exact_state",
                "state_mode": state_mode,
                "state_head_model": state_head_model,
                "value_head_model": value_head_model,
                "fold": fold_index,
                "num_train": len(train_frame),
                "num_test": len(test_frame),
                **exact_metrics,
            }
        )
        sample_frames.append(
            build_policy_sample_records(
                frame=test_frame,
                predicted_actions=exact_pred,
                baseline="factorized_exact_state",
                fold=fold_index,
                group_column=group_column,
                extra_fields={
                    "state_mode": state_mode,
                    "state_head_model": state_head_model,
                    "value_head_model": value_head_model,
                },
                extra_columns=build_factorized_proxy_columns(exact_scores),
            )
        )

        train_variants = {
            "factorized_predicted_state_train_exact": train_exact_state,
            "factorized_predicted_state_train_predicted": train_state,
            "factorized_predicted_state_train_predicted_oof": train_oof_state,
            "factorized_predicted_state_train_exact_plus_oof": pd.concat(
                [train_exact_state, train_oof_state],
                ignore_index=True,
            ),
        }
        selected_names = list(predicted_baselines) if predicted_baselines is not None else list(train_variants.keys())
        for baseline_name in selected_names:
            if baseline_name not in train_variants:
                raise ValueError(f"Unknown predicted baseline requested: {baseline_name}")
            train_variant = train_variants[baseline_name]
            train_variant, filter_metadata = _filter_predicted_train_variant(
                train_variant,
                predicted_train_filter_mode=predicted_train_filter_mode,
                high_det_gap_quantile=high_det_gap_quantile,
            )
            train_targets = train_variant
            record_baseline_name = baseline_name
            if teacher_distill_mode == "exact_oof_scores":
                train_targets = build_teacher_distilled_train_variant(train_variant, teacher_score_frame)
                record_baseline_name = f"{baseline_name}_teacher_exact_oof"
            value_bundle = fit_action_value_heads(train_targets, pred_columns, state_mode, value_head_model)
            predicted_actions = predict_actions(value_bundle, test_state, pred_columns)
            predicted_scores = score_action_values(value_bundle, test_state, pred_columns)
            metrics = evaluate_policy(test_frame, predicted_actions)
            records.append(
                {
                    "baseline": record_baseline_name,
                    "state_mode": state_mode,
                    "state_head_model": state_head_model,
                    "value_head_model": value_head_model,
                    "fold": fold_index,
                    "num_train": len(train_targets),
                    "num_test": len(test_frame),
                    "teacher_distill_mode": teacher_distill_mode,
                    **filter_metadata,
                    **metrics,
                    **state_metrics,
                }
            )
            sample_frames.append(
                build_policy_sample_records(
                    frame=test_frame,
                    predicted_actions=predicted_actions,
                    baseline=record_baseline_name,
                    fold=fold_index,
                    group_column=group_column,
                    extra_fields={
                        "state_mode": state_mode,
                        "state_head_model": state_head_model,
                        "value_head_model": value_head_model,
                        "teacher_distill_mode": teacher_distill_mode,
                        **filter_metadata,
                    },
                    extra_columns=build_factorized_proxy_columns(predicted_scores),
                )
            )
    return pd.DataFrame(records), pd.concat(sample_frames, ignore_index=True)


def _filter_predicted_train_variant(
    train_variant: pd.DataFrame,
    predicted_train_filter_mode: str,
    high_det_gap_quantile: float,
) -> tuple[pd.DataFrame, dict[str, float | int | str]]:
    metadata: dict[str, float | int | str] = {
        "predicted_train_filter_mode": predicted_train_filter_mode,
        "train_filter_gap_threshold": np.nan,
        "train_filter_gap_quantile": high_det_gap_quantile if predicted_train_filter_mode == "high_determinacy" else np.nan,
        "train_filter_num_before": int(len(train_variant)),
        "train_filter_num_after": int(len(train_variant)),
    }
    if predicted_train_filter_mode == "all":
        return train_variant, metadata

    eligible = train_variant.copy()
    if "ambiguous" in eligible.columns:
        eligible = eligible.loc[~eligible["ambiguous"].astype(bool)].copy()
    if eligible.empty:
        return train_variant, metadata

    threshold = float(eligible["action_gap"].quantile(high_det_gap_quantile))
    filtered = eligible.loc[eligible["action_gap"] >= threshold].copy()
    if filtered.empty:
        filtered = eligible

    metadata["train_filter_gap_threshold"] = threshold
    metadata["train_filter_num_after"] = int(len(filtered))
    return filtered.reset_index(drop=True), metadata


def build_factorized_proxy_columns(score_matrix: np.ndarray) -> dict[str, object]:
    continue_scores = score_matrix[:, ACTIONS.index("continue")]
    revise_scores = score_matrix[:, ACTIONS.index("revise_1")]
    abstain_scores = score_matrix[:, ACTIONS.index("abstain")]
    compute_margin = np.maximum(continue_scores, revise_scores) - abstain_scores
    sorted_scores = np.sort(score_matrix, axis=1)
    action_margin = sorted_scores[:, -1] - sorted_scores[:, -2]
    return {
        "pred_continue_score": continue_scores,
        "pred_revise_score": revise_scores,
        "pred_abstain_score": abstain_scores,
        "predicted_proxy_value": compute_margin,
        "predicted_proxy_aux": action_margin,
        "predicted_proxy_type": "utility_margin",
        "predicted_proxy_is_utility_scale": 1,
    }


def summarize_factorized_results(results: pd.DataFrame) -> pd.DataFrame:
    aggregate_columns = [
        "oracle_action_accuracy",
        "mean_action_regret",
        "mean_chosen_utility",
        "q_brier",
        "q_auc",
        "mu_rmse",
        "nu_rmse",
        "std_rmse",
        "wrong_rate_rmse",
        "mean_tok_rmse",
    ]
    available_columns = [column for column in aggregate_columns if column in results.columns]
    group_columns = ["baseline"]
    if "state_mode" in results.columns:
        group_columns.insert(0, "state_mode")
    if "state_head_model" in results.columns:
        insert_at = 1 if "state_mode" in results.columns else 0
        group_columns.insert(insert_at, "state_head_model")
    if "value_head_model" in results.columns:
        insert_at = 2 if "state_head_model" in results.columns else (1 if "state_mode" in results.columns else 0)
        group_columns.insert(insert_at, "value_head_model")
    return (
        results.groupby(group_columns, as_index=False)[available_columns]
        .mean()
        .sort_values("mean_action_regret", ascending=True)
        .reset_index(drop=True)
    )
