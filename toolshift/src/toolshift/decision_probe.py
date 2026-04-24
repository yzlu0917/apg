from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Sequence

try:
    import torch
    import torch.nn.functional as F
except ModuleNotFoundError:  # pragma: no cover - exercised in infer env
    torch = None
    F = None

from .benchmark import ViewExample
from .embedding_policy import (
    DenseCapabilityScorer,
    EmbeddingPolicyAgent,
    LearnedCapabilityScorer,
    NeuralDenseCapabilityScorer,
    SemanticGateAgent,
    _capability_dense_feature_vector,
    _capability_feature_map,
    _tool_contract_compatible,
)
from .schema import ShiftKind


@dataclass(frozen=True)
class LinearProbe:
    weights: tuple[float, ...]
    bias: float
    feature_means: tuple[float, ...]
    feature_scales: tuple[float, ...]

    def score(self, feature_vector) -> float:
        values = feature_vector.float().cpu().tolist()
        normalized = [
            (value - mean) / scale
            for value, mean, scale in zip(values, self.feature_means, self.feature_scales, strict=True)
        ]
        return sum(weight * value for weight, value in zip(self.weights, normalized, strict=True)) + self.bias

    def predict(self, feature_vector) -> bool:
        return self.score(feature_vector) >= 0.0


def extract_semantic_gate_decision_state(agent: SemanticGateAgent, example: ViewExample):
    _require_torch()
    request_feature = agent._request_feature(example.case.request)
    active_tools = [tool for tool in example.schema_view.tools if tool.status == "active"]
    active_scores = [(agent._tool_similarity(request_feature, tool), tool) for tool in active_tools]
    active_scores.sort(key=lambda item: item[0], reverse=True)

    best_any_score = float("-inf")
    best_any_tool = None
    for tool in example.schema_view.tools:
        score = agent._tool_similarity(request_feature, tool)
        if score > best_any_score:
            best_any_score = score
            best_any_tool = tool

    best_active_score = active_scores[0][0] if active_scores else 0.0
    best_active_tool = active_scores[0][1] if active_scores else None
    second_active_score = active_scores[1][0] if len(active_scores) > 1 else 0.0
    contract_ok = float(
        best_active_tool is not None and _tool_contract_compatible(best_active_tool, example.case.slot_values)
    )
    deprecated_any = float(best_any_tool is not None and best_any_tool.status == "deprecated")

    base_values = [
        float(best_active_score),
        float(second_active_score),
        float(best_any_score if best_any_score != float("-inf") else 0.0),
        float(agent.threshold),
        float(best_active_score - agent.threshold),
        float(best_active_score - second_active_score),
        contract_ok,
        deprecated_any,
    ]

    if best_active_tool is None:
        return torch.tensor(base_values, dtype=torch.float32)

    if agent.capability_scorer is not None:
        feature_map = _capability_feature_map(
            tool=best_active_tool,
            request=example.case.request,
            best_active_score=best_active_score,
            second_active_score=second_active_score,
            request_feature=request_feature,
            text_feature_lookup=agent._text_feature,
            feature_names=agent.capability_scorer.feature_names,
        )
        score = agent.capability_scorer.score(feature_map)
        extra = [float(feature_map[name]) for name in agent.capability_scorer.feature_names]
        extra.extend([float(score), float(score - agent.capability_scorer.threshold)])
        return torch.tensor(base_values + extra, dtype=torch.float32)

    if agent.dense_capability_scorer is not None:
        dense_feature_vector = _capability_dense_feature_vector(
            tool=best_active_tool,
            request=example.case.request,
            request_feature=request_feature,
            best_active_score=best_active_score,
            second_active_score=second_active_score,
            text_feature_lookup=agent._text_feature,
            mode=agent.dense_capability_scorer.mode,
            clause_localizer=agent.clause_localizer,
        )
        score = agent.dense_capability_scorer.score(dense_feature_vector)
        extra = [float(value) for value in dense_feature_vector.float().cpu().tolist()]
        extra.extend([float(score), float(score - agent.dense_capability_scorer.threshold)])
        return torch.tensor(base_values + extra, dtype=torch.float32)

    return torch.tensor(base_values, dtype=torch.float32)


def extract_embedding_policy_decision_state(agent: EmbeddingPolicyAgent, example: ViewExample):
    _require_torch()
    feature = agent._feature_for(example)
    with torch.inference_mode():
        action_state, control_logits, tool_logits = agent.model(feature.unsqueeze(0))
        slot_logits = agent.model.slot_logits(action_state)
        gap_logits = agent.model.gap_logits(action_state)
    action_state = action_state[0]
    control_logits = control_logits[0]
    control_probs = F.softmax(control_logits, dim=-1)

    visible_tools = [tool for tool in example.schema_view.tools if tool.canonical_tool_id in agent.tool_to_index]
    if visible_tools:
        visible_indices = torch.tensor(
            [agent.tool_to_index[tool.canonical_tool_id] for tool in visible_tools],
            dtype=torch.long,
        )
        visible_logits = tool_logits[0].index_select(0, visible_indices)
        visible_probs = F.softmax(visible_logits, dim=-1)
        best_visible_prob = float(visible_probs.max().item())
        second_visible_prob = float(visible_probs.topk(min(2, visible_probs.numel())).values[-1].item()) if visible_probs.numel() > 1 else 0.0
        visible_margin = best_visible_prob - second_visible_prob
    else:
        best_visible_prob = 0.0
        second_visible_prob = 0.0
        visible_margin = 0.0

    gap_logit = 0.0 if gap_logits is None else float(gap_logits[0].item())
    gap_prob = 0.0 if gap_logits is None else float(torch.sigmoid(gap_logits[0]).item())
    slot_mean = 0.0 if slot_logits is None else float(torch.sigmoid(slot_logits[0]).mean().item())
    slot_max = 0.0 if slot_logits is None else float(torch.sigmoid(slot_logits[0]).max().item())

    state_values = [float(value) for value in action_state.float().cpu().tolist()]
    state_values.extend(float(value) for value in control_logits.float().cpu().tolist())
    state_values.extend(float(value) for value in control_probs.float().cpu().tolist())
    state_values.extend(
        [
            best_visible_prob,
            second_visible_prob,
            visible_margin,
            float(len(visible_tools)),
            gap_logit,
            gap_prob,
            slot_mean,
            slot_max,
        ]
    )
    return torch.tensor(state_values, dtype=torch.float32)


def extract_decision_state(agent: SemanticGateAgent | EmbeddingPolicyAgent, example: ViewExample):
    if isinstance(agent, SemanticGateAgent):
        return extract_semantic_gate_decision_state(agent, example)
    if isinstance(agent, EmbeddingPolicyAgent):
        return extract_embedding_policy_decision_state(agent, example)
    raise TypeError(f"unsupported agent type for decision probe: {type(agent).__name__}")


def positive_state_similarity(state_vectors: Sequence, examples: Sequence[ViewExample]) -> float | None:
    _require_torch()
    grouped_indices: dict[str, list[int]] = defaultdict(list)
    positive_vectors = []
    for vector, example in zip(state_vectors, examples, strict=True):
        if example.schema_view.shift_kind in {ShiftKind.CLEAN, ShiftKind.POSITIVE_ORBIT}:
            grouped_indices[example.case.case_id].append(len(positive_vectors))
            positive_vectors.append(vector)
    if not positive_vectors:
        return None
    features = torch.stack([vector.float() for vector in positive_vectors])
    normalized = F.normalize(features, dim=-1)
    similarities = []
    for indices in grouped_indices.values():
        if len(indices) < 2:
            continue
        pairwise = normalized[indices] @ normalized[indices].T
        count = len(indices)
        similarities.append(float(((pairwise.sum() - count) / (count * (count - 1))).item()))
    if not similarities:
        return None
    return sum(similarities) / len(similarities)


def negative_state_similarity(state_vectors: Sequence, examples: Sequence[ViewExample]) -> float | None:
    _require_torch()
    vectors = [vector.float() for vector in state_vectors]
    grouped: dict[str, dict[str, list[torch.Tensor]]] = defaultdict(lambda: {"positive": [], "negative": []})
    for vector, example in zip(vectors, examples, strict=True):
        if example.schema_view.shift_kind in {ShiftKind.CLEAN, ShiftKind.POSITIVE_ORBIT}:
            grouped[example.case.case_id]["positive"].append(vector)
        elif example.schema_view.shift_kind == ShiftKind.NEGATIVE_NEAR_ORBIT:
            grouped[example.case.case_id]["negative"].append(vector)
    similarities = []
    for payload in grouped.values():
        if not payload["positive"] or not payload["negative"]:
            continue
        positive_centroid = F.normalize(torch.stack(payload["positive"]).mean(dim=0, keepdim=True), dim=-1)[0]
        negative_states = F.normalize(torch.stack(payload["negative"]), dim=-1)
        scores = negative_states @ positive_centroid
        similarities.append(float(scores.mean().item()))
    if not similarities:
        return None
    return sum(similarities) / len(similarities)


def fit_linear_probe(state_vectors: Sequence, labels: Sequence[bool], *, epochs: int = 300, learning_rate: float = 5e-2) -> tuple[LinearProbe, dict[str, float]]:
    _require_torch()
    if not state_vectors:
        raise ValueError("state_vectors must be non-empty")
    feature_tensor = torch.stack([vector.float() for vector in state_vectors])
    feature_means = feature_tensor.mean(dim=0)
    feature_scales = feature_tensor.std(dim=0, unbiased=False)
    feature_scales = torch.where(feature_scales > 0, feature_scales, torch.ones_like(feature_scales))
    normalized = (feature_tensor - feature_means) / feature_scales
    targets = torch.tensor([float(label) for label in labels], dtype=torch.float32)

    model = torch.nn.Linear(normalized.shape[1], 1)
    positives = max(1.0, float(targets.sum().item()))
    negatives = max(1.0, float(len(labels) - positives))
    pos_weight = torch.tensor([negatives / positives], dtype=torch.float32)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-2)
    for _ in range(epochs):
        logits = model(normalized).squeeze(-1)
        loss = F.binary_cross_entropy_with_logits(logits, targets, pos_weight=pos_weight)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    with torch.inference_mode():
        logits = model(normalized).squeeze(-1)
        predictions = logits >= 0.0
    labels_bool = [bool(value) for value in labels]
    predicted_bool = [bool(item) for item in predictions.cpu().tolist()]
    accuracy = sum(int(pred == label) for pred, label in zip(predicted_bool, labels_bool, strict=True)) / len(labels_bool)
    positives_total = sum(int(label) for label in labels_bool)
    true_positive = sum(int(pred and label) for pred, label in zip(predicted_bool, labels_bool, strict=True))
    stats = {
        "train_accuracy": accuracy,
        "train_positive_recall": (true_positive / positives_total) if positives_total else 0.0,
        "train_positive_rate": sum(int(pred) for pred in predicted_bool) / len(predicted_bool),
    }
    probe = LinearProbe(
        weights=tuple(float(value) for value in model.weight.detach().cpu()[0].tolist()),
        bias=float(model.bias.detach().cpu().item()),
        feature_means=tuple(float(value) for value in feature_means.tolist()),
        feature_scales=tuple(float(value) for value in feature_scales.tolist()),
    )
    return probe, stats


def evaluate_linear_probe(probe: LinearProbe, state_vectors: Sequence, labels: Sequence[bool]) -> dict[str, float]:
    if not state_vectors:
        raise ValueError("state_vectors must be non-empty")
    predictions = [probe.predict(vector) for vector in state_vectors]
    labels_bool = [bool(label) for label in labels]
    accuracy = sum(int(pred == label) for pred, label in zip(predictions, labels_bool, strict=True)) / len(labels_bool)
    positives_total = sum(int(label) for label in labels_bool)
    true_positive = sum(int(pred and label) for pred, label in zip(predictions, labels_bool, strict=True))
    return {
        "accuracy": accuracy,
        "positive_recall": (true_positive / positives_total) if positives_total else 0.0,
        "positive_rate": sum(int(pred) for pred in predictions) / len(predictions),
    }


def _require_torch() -> None:
    if torch is None or F is None:
        raise ModuleNotFoundError("decision_probe requires torch")
