from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations
from pathlib import Path
from typing import Protocol

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA


ACTIONS = ("continue", "revise_1", "abstain")
UTILITY_COLUMNS = {
    "continue": "continue_utility",
    "revise_1": "revise_utility",
    "abstain": "abstain_utility",
}
DEFAULT_FEATURE_COLUMNS = [
    "q_t",
    "mu_continue",
    "nu_continue",
    "budget_tokens",
    "prefix_length",
    "prefix_invalid",
    "is_perturbed",
]


class Policy(Protocol):
    def predict(self, frame: pd.DataFrame) -> list[str]:
        ...


@dataclass(frozen=True)
class ThresholdPolicy:
    score_column: str | None
    action_order: tuple[str, str, str]
    threshold_low: float
    threshold_high: float
    scores_override: np.ndarray | None = None

    def predict(self, frame: pd.DataFrame) -> list[str]:
        if self.scores_override is not None:
            scores = self.scores_override
        elif self.score_column is not None:
            scores = frame[self.score_column].to_numpy(dtype=float)
        else:
            raise ValueError("No score source available")
        return _apply_thresholds(scores, self.action_order, self.threshold_low, self.threshold_high)


@dataclass(frozen=True)
class Learned1DPolicy:
    feature_columns: list[str]
    regressor: Pipeline
    threshold_policy: ThresholdPolicy

    def predict(self, frame: pd.DataFrame) -> list[str]:
        scores = self.regressor.predict(frame[self.feature_columns])
        return _apply_thresholds(
            scores,
            self.threshold_policy.action_order,
            self.threshold_policy.threshold_low,
            self.threshold_policy.threshold_high,
        )


@dataclass(frozen=True)
class DirectPolicy:
    feature_columns: list[str]
    classifier: Pipeline

    def predict(self, frame: pd.DataFrame) -> list[str]:
        return self.classifier.predict(frame[self.feature_columns]).tolist()


@dataclass(frozen=True)
class ConstantPolicy:
    action: str

    def predict(self, frame: pd.DataFrame) -> list[str]:
        return [self.action] * len(frame)


def load_oracle_frame(csv_path: str | Path, exclude_ambiguous: bool = True) -> pd.DataFrame:
    frame = pd.read_csv(csv_path)
    frame["row_id"] = np.arange(len(frame), dtype=np.int64)
    bool_columns = ["prefix_invalid", "ambiguous"]
    for column in bool_columns:
        if frame[column].dtype == object:
            frame[column] = frame[column].str.lower() == "true"
        frame[column] = frame[column].astype(bool)
    frame["is_perturbed"] = (frame.get("prefix_variant", "base") != "base").astype(int)
    frame["prefix_invalid"] = frame["prefix_invalid"].astype(int)
    if exclude_ambiguous:
        frame = frame.loc[~frame["ambiguous"]].copy()
    return frame.reset_index(drop=True)


def attach_embeddings(
    frame: pd.DataFrame,
    embedding_npz_path: str | Path,
    column_prefix: str = "emb",
) -> tuple[pd.DataFrame, list[str]]:
    payload = np.load(embedding_npz_path)
    embeddings = payload["embeddings"]
    row_ids = payload["row_ids"]
    embedding_columns = [f"{column_prefix}_{index}" for index in range(embeddings.shape[1])]
    embedding_frame = pd.DataFrame(embeddings, columns=embedding_columns)
    embedding_frame["row_id"] = row_ids
    merged = frame.merge(embedding_frame, on="row_id", how="left", validate="one_to_one")
    return merged, embedding_columns


def evaluate_policy(frame: pd.DataFrame, predicted_actions: list[str]) -> dict[str, float]:
    oracle_utilities = frame[[UTILITY_COLUMNS[action] for action in ACTIONS]].max(axis=1).to_numpy(dtype=float)
    chosen_utilities = np.array(
        [frame.iloc[index][UTILITY_COLUMNS[action]] for index, action in enumerate(predicted_actions)],
        dtype=float,
    )
    oracle_actions = frame["oracle_action"].tolist()
    regrets = oracle_utilities - chosen_utilities
    return {
        "oracle_action_accuracy": float(np.mean(np.array(predicted_actions) == np.array(oracle_actions))),
        "mean_action_regret": float(np.mean(regrets)),
        "mean_chosen_utility": float(np.mean(chosen_utilities)),
    }


def build_policy_sample_records(
    frame: pd.DataFrame,
    predicted_actions: list[str],
    baseline: str,
    fold: int,
    group_column: str = "sample_id",
    extra_fields: dict[str, float | int | str] | None = None,
    extra_columns: dict[str, object] | None = None,
) -> pd.DataFrame:
    oracle_utilities = frame[[UTILITY_COLUMNS[action] for action in ACTIONS]].max(axis=1).to_numpy(dtype=float)
    chosen_utilities = np.array(
        [frame.iloc[index][UTILITY_COLUMNS[action]] for index, action in enumerate(predicted_actions)],
        dtype=float,
    )
    oracle_actions = frame["oracle_action"].tolist()
    regrets = oracle_utilities - chosen_utilities
    records: list[dict[str, float | int | str]] = []
    passthrough_columns = [
        "row_id",
        "sample_id",
        "env",
        "problem",
        "target",
        "prefix_variant",
        "prefix_length",
        "budget_tokens",
        "q_t",
        "prefix_invalid",
        "mu_continue",
        "nu_continue",
        "continue_std_utility",
        "continue_wrong_rate",
        "continue_mean_tokens",
        "continue_utility",
        "revise_utility",
        "abstain_utility",
        "revise_gain",
        "action_gap",
        "ambiguous",
    ]
    extra_fields = dict(extra_fields or {})
    extra_columns = dict(extra_columns or {})
    for key, value in extra_columns.items():
        if np.isscalar(value) or isinstance(value, str):
            continue
        if len(value) != len(frame):
            raise ValueError(f"extra_columns[{key}] length mismatch: expected {len(frame)}, got {len(value)}")
    for index, predicted_action in enumerate(predicted_actions):
        row = frame.iloc[index]
        record: dict[str, float | int | str] = {
            "baseline": baseline,
            "fold": fold,
            "predicted_action": predicted_action,
            "oracle_action": oracle_actions[index],
            "oracle_action_correct": int(predicted_action == oracle_actions[index]),
            "chosen_utility": float(chosen_utilities[index]),
            "oracle_utility": float(oracle_utilities[index]),
            "action_regret": float(regrets[index]),
        }
        if group_column in row.index:
            record[group_column] = row[group_column]
        for column in passthrough_columns:
            if column in row.index and column not in record:
                value = row[column]
                if pd.isna(value):
                    continue
                record[column] = value.item() if hasattr(value, "item") else value
        for key, value in extra_fields.items():
            record[key] = value
        for key, value in extra_columns.items():
            if np.isscalar(value) or isinstance(value, str):
                record[key] = value
                continue
            item = value[index]
            record[key] = item.item() if hasattr(item, "item") else item
        records.append(record)
    return pd.DataFrame(records)


def extract_policy_proxy_columns(policy: Policy, frame: pd.DataFrame) -> dict[str, object]:
    if isinstance(policy, ThresholdPolicy):
        if policy.scores_override is not None:
            scores = np.asarray(policy.scores_override, dtype=float)
        elif policy.score_column is not None:
            scores = frame[policy.score_column].to_numpy(dtype=float)
        else:
            scores = np.full(len(frame), np.nan, dtype=float)
        return {
            "predicted_proxy_value": scores,
            "predicted_proxy_type": "ordered_scalar_score",
            "predicted_proxy_is_utility_scale": 0,
        }

    if isinstance(policy, Learned1DPolicy):
        scores = policy.regressor.predict(frame[policy.feature_columns])
        return {
            "predicted_proxy_value": np.asarray(scores, dtype=float),
            "predicted_proxy_type": "learned_1d_score",
            "predicted_proxy_is_utility_scale": 0,
        }

    if isinstance(policy, DirectPolicy):
        feature_matrix = frame[policy.feature_columns]
        probs = policy.classifier.predict_proba(feature_matrix)
        classes = list(policy.classifier.named_steps["logreg"].classes_)
        prob_map = {
            action: probs[:, classes.index(action)] if action in classes else np.zeros(len(frame), dtype=float)
            for action in ACTIONS
        }
        non_abstain_prob = prob_map["continue"] + prob_map["revise_1"]
        chosen_prob = np.max(probs, axis=1)
        return {
            "pred_continue_score": prob_map["continue"],
            "pred_revise_score": prob_map["revise_1"],
            "pred_abstain_score": prob_map["abstain"],
            "predicted_proxy_value": non_abstain_prob,
            "predicted_proxy_aux": chosen_prob,
            "predicted_proxy_type": "nonabstain_probability",
            "predicted_proxy_is_utility_scale": 0,
        }

    if isinstance(policy, ConstantPolicy):
        return {
            "predicted_proxy_type": "constant_policy",
            "predicted_proxy_is_utility_scale": 0,
        }

    return {}


def fit_ordered_scalar_mu(train_frame: pd.DataFrame) -> ThresholdPolicy:
    scores = train_frame["mu_continue"].to_numpy(dtype=float)
    action_order, threshold_low, threshold_high = _search_threshold_policy(scores, train_frame)
    return ThresholdPolicy(
        score_column="mu_continue",
        action_order=action_order,
        threshold_low=threshold_low,
        threshold_high=threshold_high,
    )


def fit_learned_1d(
    train_frame: pd.DataFrame,
    feature_columns: list[str],
) -> Policy:
    best_policy: Learned1DPolicy | None = None
    best_regret = float("inf")
    train_x = train_frame[feature_columns]
    for action_order in permutations(ACTIONS):
        targets = np.array([action_order.index(action) for action in train_frame["oracle_action"]], dtype=float)
        regressor = Pipeline(steps=_make_feature_steps(train_frame, feature_columns) + [("ridge", Ridge(alpha=1.0))])
        regressor.fit(train_x, targets)
        scores = regressor.predict(train_x)
        _, threshold_low, threshold_high = _search_threshold_policy(scores, train_frame, fixed_order=action_order)
        predicted = _apply_thresholds(scores, action_order, threshold_low, threshold_high)
        metrics = evaluate_policy(train_frame, predicted)
        if metrics["mean_action_regret"] < best_regret:
            best_regret = metrics["mean_action_regret"]
            best_policy = Learned1DPolicy(
                feature_columns=list(feature_columns),
                regressor=regressor,
                threshold_policy=ThresholdPolicy(
                    score_column=None,
                    action_order=action_order,
                    threshold_low=threshold_low,
                    threshold_high=threshold_high,
                ),
            )
    if best_policy is None:
        return ConstantPolicy(action=train_frame["oracle_action"].mode().iloc[0])
    return best_policy


def fit_direct_policy(train_frame: pd.DataFrame, feature_columns: list[str]) -> Policy:
    labels = train_frame["oracle_action"]
    if labels.nunique() < 2:
        return ConstantPolicy(action=labels.iloc[0])
    classifier = Pipeline(
        steps=_make_feature_steps(train_frame, feature_columns)
        + [
            (
                "logreg",
                LogisticRegression(
                    max_iter=2000,
                ),
            ),
        ]
    )
    classifier.fit(train_frame[feature_columns], labels)
    return DirectPolicy(feature_columns=list(feature_columns), classifier=classifier)


def run_group_cv(
    frame: pd.DataFrame,
    feature_columns: list[str] | None = None,
    group_column: str = "sample_id",
    n_splits: int = 5,
    baseline_suffix: str = "",
) -> pd.DataFrame:
    feature_columns = list(feature_columns or DEFAULT_FEATURE_COLUMNS)
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

        baselines: dict[str, Policy] = {
            f"ordered_scalar_mu{baseline_suffix}": fit_ordered_scalar_mu(train_frame),
            f"learned_1d_linear{baseline_suffix}": fit_learned_1d(train_frame, feature_columns),
            f"direct_policy{baseline_suffix}": fit_direct_policy(train_frame, feature_columns),
        }

        for baseline_name, baseline in baselines.items():
            predicted = baseline.predict(test_frame)
            metrics = evaluate_policy(test_frame, predicted)
            records.append(
                {
                    "baseline": baseline_name,
                    "fold": fold_index,
                    "num_train": len(train_frame),
                    "num_test": len(test_frame),
                    **metrics,
                }
            )
    return pd.DataFrame(records)


def run_group_cv_with_samples(
    frame: pd.DataFrame,
    feature_columns: list[str] | None = None,
    group_column: str = "sample_id",
    n_splits: int = 5,
    baseline_suffix: str = "",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    feature_columns = list(feature_columns or DEFAULT_FEATURE_COLUMNS)
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

        baselines: dict[str, Policy] = {
            f"ordered_scalar_mu{baseline_suffix}": fit_ordered_scalar_mu(train_frame),
            f"learned_1d_linear{baseline_suffix}": fit_learned_1d(train_frame, feature_columns),
            f"direct_policy{baseline_suffix}": fit_direct_policy(train_frame, feature_columns),
        }

        for baseline_name, baseline in baselines.items():
            predicted = baseline.predict(test_frame)
            metrics = evaluate_policy(test_frame, predicted)
            records.append(
                {
                    "baseline": baseline_name,
                    "fold": fold_index,
                    "num_train": len(train_frame),
                    "num_test": len(test_frame),
                    **metrics,
                }
            )
            sample_frames.append(
                build_policy_sample_records(
                    frame=test_frame,
                    predicted_actions=predicted,
                    baseline=baseline_name,
                    fold=fold_index,
                    group_column=group_column,
                    extra_columns=extract_policy_proxy_columns(baseline, test_frame),
                )
            )
    return pd.DataFrame(records), pd.concat(sample_frames, ignore_index=True)


def summarize_cv_results(results: pd.DataFrame) -> pd.DataFrame:
    return (
        results.groupby("baseline", as_index=False)[
            ["oracle_action_accuracy", "mean_action_regret", "mean_chosen_utility"]
        ]
        .mean()
        .sort_values("mean_action_regret", ascending=True)
        .reset_index(drop=True)
    )


def _search_threshold_policy(
    scores: np.ndarray,
    frame: pd.DataFrame,
    fixed_order: tuple[str, str, str] | None = None,
) -> tuple[tuple[str, str, str], float, float]:
    orders = [fixed_order] if fixed_order is not None else list(permutations(ACTIONS))
    unique_scores = np.unique(scores)
    if len(unique_scores) <= 1:
        return tuple(ACTIONS), float("-inf"), float("inf")

    midpoints = ((unique_scores[:-1] + unique_scores[1:]) / 2.0).tolist()
    candidates = [float("-inf")] + midpoints + [float("inf")]

    best_order: tuple[str, str, str] = tuple(ACTIONS)
    best_low = float("-inf")
    best_high = float("inf")
    best_regret = float("inf")
    best_accuracy = -1.0

    for action_order in orders:
        assert action_order is not None
        for low_index, threshold_low in enumerate(candidates):
            for threshold_high in candidates[low_index:]:
                predicted = _apply_thresholds(scores, action_order, threshold_low, threshold_high)
                metrics = evaluate_policy(frame, predicted)
                regret = metrics["mean_action_regret"]
                accuracy = metrics["oracle_action_accuracy"]
                if regret < best_regret or (np.isclose(regret, best_regret) and accuracy > best_accuracy):
                    best_order = action_order
                    best_low = threshold_low
                    best_high = threshold_high
                    best_regret = regret
                    best_accuracy = accuracy
    return best_order, best_low, best_high


def _apply_thresholds(
    scores: np.ndarray,
    action_order: tuple[str, str, str],
    threshold_low: float,
    threshold_high: float,
) -> list[str]:
    predictions: list[str] = []
    for score in scores:
        if score <= threshold_low:
            predictions.append(action_order[0])
        elif score <= threshold_high:
            predictions.append(action_order[1])
        else:
            predictions.append(action_order[2])
    return predictions


def _make_feature_steps(train_frame: pd.DataFrame, feature_columns: list[str]) -> list[tuple[str, object]]:
    steps: list[tuple[str, object]] = [("scaler", StandardScaler())]
    num_features = len(feature_columns)
    if num_features > 128:
        max_components = min(32, len(train_frame) - 1, num_features)
        if max_components >= 2:
            steps.append(("pca", PCA(n_components=max_components)))
    return steps
