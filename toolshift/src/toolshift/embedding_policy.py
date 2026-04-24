from __future__ import annotations

import math
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Sequence

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
except ModuleNotFoundError:
    torch = None
    nn = None
    F = None

from .agents import BaseAgent
from .benchmark import BenchmarkSuite, ViewExample
from .schema import ControlTag, RenderedArgument, RenderedTool, ShiftKind, ToolCall


CONTROL_ORDER: tuple[ControlTag, ...] = (
    ControlTag.EXECUTE,
    ControlTag.ASK_CLARIFICATION,
    ControlTag.ABSTAIN,
)

CAPABILITY_GAP_CUES: tuple[str, ...] = (
    "no longer",
    "does not exactly",
    "do not exactly",
    "not exactly",
    "does not provide this specific operation",
    "not a drop-in replacement",
    "no direct replacement",
    "not supported",
    "unsupported",
    "read-only",
)

CAPABILITY_FEATURE_NAMES: tuple[str, ...] = (
    "best_active_score",
    "score_margin",
    "tool_overlap",
    "description_overlap",
    "cue_clause_count",
    "max_cue_overlap",
    "total_cue_overlap",
    "has_gap_rule",
    "is_deprecated",
)

CAPABILITY_CUE_FEATURE_NAMES: tuple[str, ...] = (
    "description_overlap",
    "cue_clause_count",
    "max_cue_overlap",
    "total_cue_overlap",
    "has_gap_rule",
    "is_deprecated",
)

CAPABILITY_CONTINUOUS_FEATURE_NAMES: tuple[str, ...] = (
    "description_overlap",
    "max_cue_overlap",
    "total_cue_overlap",
)

CAPABILITY_EMBEDDING_FEATURE_NAMES: tuple[str, ...] = (
    "description_similarity",
    "max_cue_similarity",
    "mean_cue_similarity",
)

CAPABILITY_RAWTEXT_FEATURE_NAMES: tuple[str, ...] = (
    "tool_similarity",
    "description_similarity",
    "argument_similarity",
)

CAPABILITY_DESCRIPTION_POOL_FEATURE_NAMES: tuple[str, ...] = (
    "tool_similarity",
    "description_similarity",
    "argument_similarity",
    "max_description_clause_similarity",
    "mean_description_clause_similarity",
)

CROSS_ENCODER_FEATURE_NAMES: tuple[str, ...] = (
    "best_active_score",
    "score_margin",
    "top_clause_score",
    "second_clause_score",
    "mean_clause_score",
    "full_capability_score",
    "localized_capability_score",
    "localized_minus_full",
)

CROSS_ENCODER_CLAUSE_FEATURE_NAMES: tuple[str, ...] = (
    "localizer_score",
    "clause_capability_score",
    "clause_minus_full",
)

CROSS_ENCODER_RERANKER_DEFAULT_PATH = "/cephfs/shared/hf_cache/hub/Qwen3-Reranker-0.6B"
CROSS_ENCODER_LOCALIZER_INSTRUCTION = (
    "Given a user request, retrieve tool-description clauses that state the candidate tool cannot directly satisfy "
    "the request because of capability removal, deprecation, replacement semantics, or scope mismatch."
)
CROSS_ENCODER_CAPABILITY_INSTRUCTION = (
    "Given a user request, judge whether the candidate tool context indicates a semantic capability gap, meaning "
    "the tool should not be executed directly for this request."
)

SEMANTIC_RESCUE_MARGIN: float = 0.03
SEMANTIC_RESCUE_MIN_LEAD: float = 0.01
SEMANTIC_RESCUE_MIN_OVERLAP: int = 2

CAPABILITY_STOPWORDS: frozenset[str] = frozenset(
    {
        "a",
        "an",
        "and",
        "api",
        "are",
        "as",
        "be",
        "can",
        "content",
        "data",
        "directly",
        "do",
        "does",
        "exactly",
        "for",
        "include",
        "integration",
        "into",
        "is",
        "it",
        "its",
        "list",
        "may",
        "no",
        "not",
        "of",
        "old",
        "on",
        "or",
        "response",
        "responses",
        "result",
        "results",
        "the",
        "this",
        "to",
        "tool",
        "visible",
        "with",
    }
)


def build_tool_vocab(suite: BenchmarkSuite) -> tuple[str, ...]:
    return tuple(sorted({tool.canonical_tool_id for example in suite.examples for tool in example.schema_view.tools}))


def build_slot_vocab(suite: BenchmarkSuite) -> tuple[str, ...]:
    slot_names = {
        argument.canonical_name
        for tool in suite.tool_lookup.values()
        for argument in tool.arguments
    }
    for case in suite.cases:
        slot_names.update(case.slot_values)
    return tuple(sorted(slot_names))


def serialize_view(example: ViewExample) -> str:
    lines = [f"User request: {example.case.request}", "Visible tools:"]
    for tool in example.schema_view.tools:
        lines.append(f"Tool {tool.rendered_name} [status={tool.status}]: {tool.description}")
        for argument in tool.arguments:
            requirement = "required" if argument.required else "optional"
            constraints: list[str] = []
            if argument.enum_values:
                constraints.append(f"enum={'/'.join(argument.enum_values)}")
            if argument.minimum is not None:
                constraints.append(f"min={argument.minimum}")
            if argument.maximum is not None:
                constraints.append(f"max={argument.maximum}")
            suffix = f" [{' '.join(constraints)}]" if constraints else ""
            lines.append(
                f"Arg {argument.rendered_name} ({argument.arg_type}, {requirement}){suffix}: {argument.description}"
            )
    return "\n".join(lines)


def serialize_request(request: str) -> str:
    return f"User request: {request}"


def serialize_tool(tool: RenderedTool) -> str:
    lines = [f"Tool {tool.rendered_name} [status={tool.status}]: {tool.description}"]
    for argument in tool.arguments:
        requirement = "required" if argument.required else "optional"
        constraints: list[str] = []
        if argument.enum_values:
            constraints.append(f"enum={'/'.join(argument.enum_values)}")
        if argument.minimum is not None:
            constraints.append(f"min={argument.minimum}")
        if argument.maximum is not None:
            constraints.append(f"max={argument.maximum}")
        suffix = f" [{' '.join(constraints)}]" if constraints else ""
        lines.append(
            f"Arg {argument.rendered_name} ({argument.arg_type}, {requirement}){suffix}: {argument.description}"
        )
    return "\n".join(lines)


def serialize_clause_localizer_pair(request: str, tool: RenderedTool, clause: str) -> str:
    lines = [
        "Task: determine whether the candidate tool-description clause expresses a capability gap for the request.",
        serialize_request(request),
        f"Candidate tool: {tool.rendered_name}",
        f"Candidate clause: {clause}",
        f"Tool description: {tool.description}",
    ]
    argument_text = _tool_argument_text(tool)
    if argument_text:
        lines.append(f"Tool arguments: {argument_text}")
    return "\n".join(lines)


def serialize_capability_pair(request: str, tool: RenderedTool, localized_clause: str | None) -> str:
    lines = [
        "Task: determine whether the candidate tool can safely satisfy the request without semantic capability mismatch.",
        serialize_request(request),
        f"Candidate tool: {tool.rendered_name}",
        f"Tool description: {tool.description}",
    ]
    if localized_clause is not None:
        lines.append(f"Localized capability clause: {localized_clause}")
    argument_text = _tool_argument_text(tool)
    if argument_text:
        lines.append(f"Tool arguments: {argument_text}")
    return "\n".join(lines)


def serialize_clause_localizer_document(tool: RenderedTool, clause: str) -> str:
    lines = [
        f"Candidate tool: {tool.rendered_name}",
        f"Candidate clause: {clause}",
        f"Tool description: {tool.description}",
    ]
    argument_text = _tool_argument_text(tool)
    if argument_text:
        lines.append(f"Tool arguments: {argument_text}")
    return "\n".join(lines)


def serialize_capability_document(tool: RenderedTool, localized_clause: str | None) -> str:
    lines = [
        f"Candidate tool: {tool.rendered_name}",
        f"Tool description: {tool.description}",
    ]
    if localized_clause is not None:
        lines.append(f"Localized capability clause: {localized_clause}")
    argument_text = _tool_argument_text(tool)
    if argument_text:
        lines.append(f"Tool arguments: {argument_text}")
    return "\n".join(lines)


@dataclass(frozen=True)
class EmbeddingPolicyConfig:
    bottleneck_dim: int = 128
    epochs: int = 300
    learning_rate: float = 1e-2
    weight_decay: float = 1e-4
    lambda_inv: float = 0.1
    lambda_ctr: float = 0.1
    lambda_slot: float = 0.25
    lambda_distill_control: float = 0.25
    lambda_distill_tool: float = 0.25
    lambda_distill_slot: float = 0.1
    lambda_distill_gap: float = 0.1
    contrastive_margin: float = 0.2
    seed: int = 0
    cross_encoder_model_path: str = CROSS_ENCODER_RERANKER_DEFAULT_PATH
    cross_encoder_batch_size: int = 4
    cross_encoder_max_length: int = 4096
    cross_encoder_finetune_epochs: int = 2
    cross_encoder_finetune_learning_rate: float = 5e-5
    cross_encoder_finetune_weight_decay: float = 1e-4
    cross_encoder_finetune_batch_size: int = 2
    cross_encoder_tune_last_n_layers: int = 1
    cross_encoder_class_balance_power: float = 0.5
    cross_encoder_hard_negative_multiplier: float = 1.5
    cross_encoder_positive_retention_target: float = 0.95
    cross_encoder_execute_margin: float = 0.0
    cross_encoder_execute_margin_weight: float = 0.5


@dataclass(frozen=True)
class PrototypeExecuteGateStats:
    threshold: float
    train_accuracy: float
    train_execute_recall: float
    train_execute_rate: float


@dataclass(frozen=True)
class SemanticGateStats:
    threshold: float
    train_accuracy: float
    train_execute_recall: float
    train_execute_rate: float


@dataclass(frozen=True)
class LearnedCapabilityScorerStats:
    threshold: float
    train_accuracy: float
    train_inhibit_recall: float
    train_inhibit_rate: float


@dataclass(frozen=True)
class ClauseLocalizerStats:
    threshold: float
    train_accuracy: float
    train_positive_recall: float
    train_positive_rate: float


@dataclass(frozen=True)
class LearnedCapabilityScorer:
    weights: tuple[float, ...]
    bias: float
    threshold: float
    feature_means: tuple[float, ...]
    feature_scales: tuple[float, ...]
    feature_names: tuple[str, ...] = CAPABILITY_FEATURE_NAMES

    def score(self, feature_map: dict[str, float]) -> float:
        values = [feature_map[name] for name in self.feature_names]
        normalized = [
            (value - mean) / scale
            for value, mean, scale in zip(values, self.feature_means, self.feature_scales, strict=True)
        ]
        return sum(weight * value for weight, value in zip(self.weights, normalized, strict=True)) + self.bias

    def should_inhibit(self, feature_map: dict[str, float]) -> tuple[bool, float]:
        score = self.score(feature_map)
        margin = score - self.threshold
        return score >= self.threshold, _sigmoid(margin)


@dataclass(frozen=True)
class DenseCapabilityScorer:
    weights: tuple[float, ...]
    bias: float
    threshold: float
    feature_means: tuple[float, ...]
    feature_scales: tuple[float, ...]
    mode: str

    def score(self, feature_vector: torch.Tensor) -> float:
        values = feature_vector.float().cpu().tolist()
        normalized = [
            (value - mean) / scale
            for value, mean, scale in zip(values, self.feature_means, self.feature_scales, strict=True)
        ]
        return sum(weight * value for weight, value in zip(self.weights, normalized, strict=True)) + self.bias

    def should_inhibit(self, feature_vector: torch.Tensor) -> tuple[bool, float]:
        score = self.score(feature_vector)
        margin = score - self.threshold
        return score >= self.threshold, _sigmoid(margin)


@dataclass(frozen=True)
class LearnedClauseLocalizer:
    weights: tuple[float, ...]
    bias: float
    threshold: float
    feature_means: tuple[float, ...]
    feature_scales: tuple[float, ...]

    def score(self, feature_vector: torch.Tensor) -> float:
        values = feature_vector.float().cpu().tolist()
        normalized = [
            (value - mean) / scale
            for value, mean, scale in zip(values, self.feature_means, self.feature_scales, strict=True)
        ]
        return sum(weight * value for weight, value in zip(self.weights, normalized, strict=True)) + self.bias


@dataclass(frozen=True)
class NeuralDenseCapabilityScorer:
    hidden_weights: tuple[tuple[float, ...], ...]
    hidden_bias: tuple[float, ...]
    output_weights: tuple[float, ...]
    output_bias: float
    threshold: float
    feature_means: tuple[float, ...]
    feature_scales: tuple[float, ...]
    mode: str

    def score(self, feature_vector: torch.Tensor) -> float:
        values = feature_vector.float().cpu().tolist()
        normalized = [
            (value - mean) / scale
            for value, mean, scale in zip(values, self.feature_means, self.feature_scales, strict=True)
        ]
        hidden = [
            max(
                0.0,
                bias + sum(weight * value for weight, value in zip(row, normalized, strict=True)),
            )
            for row, bias in zip(self.hidden_weights, self.hidden_bias, strict=True)
        ]
        return self.output_bias + sum(
            weight * value for weight, value in zip(self.output_weights, hidden, strict=True)
        )

    def should_inhibit(self, feature_vector: torch.Tensor) -> tuple[bool, float]:
        score = self.score(feature_vector)
        margin = score - self.threshold
        return score >= self.threshold, _sigmoid(margin)


@dataclass(frozen=True)
class NeuralClauseLocalizer:
    hidden_weights: tuple[tuple[float, ...], ...]
    hidden_bias: tuple[float, ...]
    output_weights: tuple[float, ...]
    output_bias: float
    threshold: float
    feature_means: tuple[float, ...]
    feature_scales: tuple[float, ...]

    def score(self, feature_vector: torch.Tensor) -> float:
        values = feature_vector.float().cpu().tolist()
        normalized = [
            (value - mean) / scale
            for value, mean, scale in zip(values, self.feature_means, self.feature_scales, strict=True)
        ]
        hidden = [
            max(
                0.0,
                bias + sum(weight * value for weight, value in zip(row, normalized, strict=True)),
            )
            for row, bias in zip(self.hidden_weights, self.hidden_bias, strict=True)
        ]
        return self.output_bias + sum(
            weight * value for weight, value in zip(self.output_weights, hidden, strict=True)
        )


class FrozenEmbeddingEncoder:
    def __init__(
        self,
        model_path: str,
        *,
        device: str = "cuda:0",
        batch_size: int = 8,
        instruction: str = "Determine the canonical tool-use action from the user request and visible schema.",
    ) -> None:
        self.model_path = model_path
        self.device = device
        self.batch_size = batch_size
        self.instruction = instruction
        self._model = None
        self._tokenizer = None

    def encode_examples(self, examples: Sequence[ViewExample]) -> dict[str, torch.Tensor]:
        texts = [self._with_instruction(serialize_view(example)) for example in examples]
        embeddings = self.encode_texts(texts)
        return {example.schema_view.view_id: embedding for example, embedding in zip(examples, embeddings, strict=True)}

    def encode_texts(self, texts: Sequence[str]) -> torch.Tensor:
        _require_torch()
        if not texts:
            return torch.empty((0, 0), dtype=torch.float32)
        model, tokenizer = self._ensure_model()
        batches: list[torch.Tensor] = []
        with torch.inference_mode():
            for start in range(0, len(texts), self.batch_size):
                batch = list(texts[start:start + self.batch_size])
                encoded = tokenizer(batch, padding=True, truncation=True, return_tensors="pt").to(model.device)
                hidden = model(**encoded).last_hidden_state
                pooled = self._last_token_pool(hidden, encoded["attention_mask"])
                batches.append(F.normalize(pooled.float(), dim=-1).cpu())
        return torch.cat(batches, dim=0)

    def _with_instruction(self, text: str) -> str:
        return f"Instruct: {self.instruction}\nQuery: {text}"

    def _ensure_model(self):
        _require_torch()
        if self._model is not None and self._tokenizer is not None:
            return self._model, self._tokenizer
        from transformers import AutoModel, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(self.model_path, trust_remote_code=True)
        model = AutoModel.from_pretrained(
            self.model_path,
            trust_remote_code=True,
            dtype="auto",
        ).to(self.device)
        model.eval()
        self._model = model
        self._tokenizer = tokenizer
        return model, tokenizer

    @staticmethod
    def _last_token_pool(last_hidden_state: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        left_padding = attention_mask[:, -1].sum() == attention_mask.shape[0]
        if left_padding:
            return last_hidden_state[:, -1]
        sequence_lengths = attention_mask.sum(dim=1) - 1
        batch_size = last_hidden_state.shape[0]
        return last_hidden_state[
            torch.arange(batch_size, device=last_hidden_state.device),
            sequence_lengths,
        ]


class QwenRerankerCrossEncoder:
    _MODEL_CACHE: dict[tuple[str, str], tuple[object, object, int, int, list[int], list[int], int]] = {}

    def __init__(
        self,
        model_path: str,
        *,
        device: str = "cuda:0",
        batch_size: int = 4,
        max_length: int = 4096,
    ) -> None:
        self.model_path = model_path
        self.device = device
        self.batch_size = batch_size
        self.max_length = max_length
        self._score_cache: dict[tuple[str, str, str], float] = {}

    def score_pairs(self, *, instruction: str, pairs: Sequence[tuple[str, str]]) -> list[float]:
        _require_torch()
        if not pairs:
            return []
        results = [0.0] * len(pairs)
        uncached_indices: list[int] = []
        uncached_pairs: list[tuple[str, str]] = []
        for index, pair in enumerate(pairs):
            key = (instruction, pair[0], pair[1])
            cached = self._score_cache.get(key)
            if cached is not None:
                results[index] = cached
            else:
                uncached_indices.append(index)
                uncached_pairs.append(pair)
        if not uncached_pairs:
            return results

        model, tokenizer, true_token_id, false_token_id, prefix_tokens, suffix_tokens, max_length = self._ensure_model()
        scored: list[float] = []
        with torch.inference_mode():
            for start in range(0, len(uncached_pairs), self.batch_size):
                batch_pairs = uncached_pairs[start:start + self.batch_size]
                padded = self._prepare_model_inputs(
                    tokenizer=tokenizer,
                    prefix_tokens=prefix_tokens,
                    suffix_tokens=suffix_tokens,
                    max_length=max_length,
                    device=model.device,
                    instruction=instruction,
                    pairs=batch_pairs,
                )
                batch_scores, _ = self._yes_probabilities(
                    model=model,
                    padded_inputs=padded,
                    true_token_id=true_token_id,
                    false_token_id=false_token_id,
                )
                scored.extend(float(score) for score in batch_scores.cpu().tolist())
        for index, pair, score in zip(uncached_indices, uncached_pairs, scored, strict=True):
            results[index] = score
            self._score_cache[(instruction, pair[0], pair[1])] = score
        return results

    @staticmethod
    def _pair_texts(instruction: str, pairs: Sequence[tuple[str, str]]) -> list[str]:
        return [
            f"<Instruct>: {instruction}\n<Query>: {query}\n<Document>: {document}"
            for query, document in pairs
        ]

    @classmethod
    def _prepare_model_inputs(
        cls,
        *,
        tokenizer,
        prefix_tokens: Sequence[int],
        suffix_tokens: Sequence[int],
        max_length: int,
        device: str | torch.device,
        instruction: str,
        pairs: Sequence[tuple[str, str]],
    ) -> dict[str, torch.Tensor]:
        max_pair_length = max_length - len(prefix_tokens) - len(suffix_tokens)
        encoded = tokenizer(
            cls._pair_texts(instruction, pairs),
            padding=False,
            truncation="longest_first",
            return_attention_mask=False,
            max_length=max_pair_length,
        )
        input_ids = [list(prefix_tokens) + ids + list(suffix_tokens) for ids in encoded["input_ids"]]
        padded = tokenizer.pad({"input_ids": input_ids}, padding=True, return_tensors="pt")
        for key, value in padded.items():
            padded[key] = value.to(device)
        return padded

    @staticmethod
    def _yes_probabilities(
        *,
        model,
        padded_inputs: dict[str, torch.Tensor],
        true_token_id: int,
        false_token_id: int,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        logits = model(**padded_inputs).logits[:, -1, :]
        true_logits = logits[:, true_token_id]
        false_logits = logits[:, false_token_id]
        logit_diff = true_logits - false_logits
        return torch.sigmoid(logit_diff), logit_diff

    def _ensure_model(self):
        _require_torch()
        key = (self.model_path, self.device)
        cached = self._MODEL_CACHE.get(key)
        if cached is not None:
            return cached
        from transformers import AutoModelForCausalLM, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(self.model_path, trust_remote_code=True, padding_side="left")
        tokenizer.pad_token = tokenizer.eos_token
        model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            trust_remote_code=True,
            dtype="auto",
        ).to(self.device)
        model.eval()
        true_token_id = tokenizer("yes", add_special_tokens=False).input_ids[0]
        false_token_id = tokenizer("no", add_special_tokens=False).input_ids[0]
        prefix = (
            "<|im_start|>system\nJudge whether the Document meets the requirements based on the Query and the "
            "Instruct provided. Note that the answer can only be \"yes\" or \"no\".<|im_end|>\n<|im_start|>user\n"
        )
        suffix = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
        prefix_tokens = tokenizer.encode(prefix, add_special_tokens=False)
        suffix_tokens = tokenizer.encode(suffix, add_special_tokens=False)
        cached = (model, tokenizer, true_token_id, false_token_id, prefix_tokens, suffix_tokens, self.max_length)
        self._MODEL_CACHE[key] = cached
        return cached


class FineTunedQwenRerankerCrossEncoder(QwenRerankerCrossEncoder):
    def __init__(
        self,
        model_path: str,
        *,
        device: str,
        batch_size: int,
        max_length: int,
        model,
        tokenizer,
        true_token_id: int,
        false_token_id: int,
        prefix_tokens: Sequence[int],
        suffix_tokens: Sequence[int],
    ) -> None:
        super().__init__(model_path, device=device, batch_size=batch_size, max_length=max_length)
        self._finetuned_model = model.eval()
        self._finetuned_tokenizer = tokenizer
        self._finetuned_true_token_id = true_token_id
        self._finetuned_false_token_id = false_token_id
        self._finetuned_prefix_tokens = list(prefix_tokens)
        self._finetuned_suffix_tokens = list(suffix_tokens)

    def _ensure_model(self):
        return (
            self._finetuned_model,
            self._finetuned_tokenizer,
            self._finetuned_true_token_id,
            self._finetuned_false_token_id,
            self._finetuned_prefix_tokens,
            self._finetuned_suffix_tokens,
            self.max_length,
        )


DenseCapabilityInferenceScorer = DenseCapabilityScorer | NeuralDenseCapabilityScorer
ClauseLocalizationInferenceScorer = LearnedClauseLocalizer | NeuralClauseLocalizer


@dataclass(frozen=True)
class CrossEncoderClauseLocalizer:
    threshold: float
    instruction: str = CROSS_ENCODER_LOCALIZER_INSTRUCTION
    selection_mode: str = "threshold"
    ranker: LearnedCapabilityScorer | None = None


@dataclass(frozen=True)
class CrossEncoderCapabilityGate:
    threshold: float
    instruction: str = CROSS_ENCODER_CAPABILITY_INSTRUCTION
    abstain_threshold: float | None = None


@dataclass(frozen=True)
class CrossEncoderBinaryTaskSpec:
    name: str
    instruction: str
    pairs: tuple[tuple[str, str], ...]
    labels: tuple[bool, ...]


@dataclass(frozen=True)
class CrossEncoderCapabilityTrainingRow:
    example: ViewExample
    best_active_tool: CanonicalTool
    should_execute: bool


class SemanticGateAgent(BaseAgent):
    def __init__(
        self,
        *,
        name: str,
        encoder: FrozenEmbeddingEncoder,
        threshold: float,
        contract_aware_inhibition: bool = False,
        description_aware_inhibition: bool = False,
        capability_scorer: LearnedCapabilityScorer | None = None,
        dense_capability_scorer: DenseCapabilityInferenceScorer | None = None,
        clause_localizer: ClauseLocalizationInferenceScorer | None = None,
        capability_require_cue: bool = False,
    ) -> None:
        super().__init__(name=name)
        self.encoder = encoder
        self.threshold = threshold
        self.contract_aware_inhibition = contract_aware_inhibition
        self.description_aware_inhibition = description_aware_inhibition
        self.capability_scorer = capability_scorer
        self.dense_capability_scorer = dense_capability_scorer
        self.clause_localizer = clause_localizer
        self.capability_require_cue = capability_require_cue
        self._request_cache: dict[str, torch.Tensor] = {}
        self._text_cache: dict[str, torch.Tensor] = {}

    def predict(self, example: ViewExample) -> ToolCall:
        _require_torch()
        request_feature = self._request_feature(example.case.request)
        active_tools = [tool for tool in example.schema_view.tools if tool.status == "active"]
        active_scores = [(self._tool_similarity(request_feature, tool), tool) for tool in active_tools]
        active_scores.sort(key=lambda item: item[0], reverse=True)

        best_any_score = float("-inf")
        best_any_tool = None
        for tool in example.schema_view.tools:
            score = self._tool_similarity(request_feature, tool)
            if score > best_any_score:
                best_any_score = score
                best_any_tool = tool

        best_active_score = active_scores[0][0] if active_scores else float("-inf")
        best_active_tool = active_scores[0][1] if active_scores else None
        second_active_score = active_scores[1][0] if len(active_scores) > 1 else 0.0

        if best_active_tool is not None and best_active_score >= self.threshold:
            return self._build_execute_call(
                example=example,
                tool=best_active_tool,
                best_active_score=best_active_score,
                second_active_score=second_active_score,
                decision_floor=self.threshold,
                request_feature=request_feature,
            )

        if self._should_rescue_execute(
            example=example,
            tool=best_active_tool,
            best_active_score=best_active_score,
            second_active_score=second_active_score,
        ):
            return self._build_execute_call(
                example=example,
                tool=best_active_tool,
                best_active_score=best_active_score,
                second_active_score=second_active_score,
                decision_floor=self.threshold - SEMANTIC_RESCUE_MARGIN,
                request_feature=request_feature,
            )

        if best_any_tool is not None and best_any_tool.status == "deprecated" and best_any_score >= self.threshold:
            return ToolCall(control=ControlTag.ABSTAIN, confidence=_sigmoid(best_any_score - self.threshold))
        return ToolCall(control=ControlTag.ASK_CLARIFICATION, confidence=_sigmoid(self.threshold - max(best_active_score, 0.0)))

    def _request_feature(self, request: str) -> torch.Tensor:
        cached = self._request_cache.get(request)
        if cached is not None:
            return cached
        feature = self._encode_text(self.encoder._with_instruction(serialize_request(request)))
        self._request_cache[request] = feature
        return feature

    def _tool_similarity(self, request_feature: torch.Tensor, tool: RenderedTool) -> float:
        tool_text = serialize_tool(tool)
        return float(torch.dot(request_feature, self._encode_text(self.encoder._with_instruction(tool_text))).item())

    def _build_execute_call(
        self,
        *,
        example: ViewExample,
        tool: RenderedTool,
        best_active_score: float,
        second_active_score: float,
        decision_floor: float,
        request_feature: torch.Tensor,
    ) -> ToolCall:
        if self.contract_aware_inhibition and not _tool_contract_compatible(tool, example.case.slot_values):
            return ToolCall(control=ControlTag.ASK_CLARIFICATION, confidence=_sigmoid(best_active_score - self.threshold))
        if self.capability_scorer is not None:
            feature_map = _capability_feature_map(
                tool=tool,
                request=example.case.request,
                best_active_score=best_active_score,
                second_active_score=second_active_score,
                request_feature=request_feature,
                text_feature_lookup=self._text_feature,
                feature_names=self.capability_scorer.feature_names,
            )
            if (not self.capability_require_cue) or feature_map["cue_clause_count"] > 0:
                inhibit, confidence = self.capability_scorer.should_inhibit(feature_map)
                if inhibit:
                    return ToolCall(control=ControlTag.ASK_CLARIFICATION, confidence=confidence)
        if self.dense_capability_scorer is not None:
            dense_feature_vector = _capability_dense_feature_vector(
                tool=tool,
                request=example.case.request,
                request_feature=request_feature,
                best_active_score=best_active_score,
                second_active_score=second_active_score,
                text_feature_lookup=self._text_feature,
                mode=self.dense_capability_scorer.mode,
                clause_localizer=self.clause_localizer,
            )
            inhibit, confidence = self.dense_capability_scorer.should_inhibit(dense_feature_vector)
            if inhibit:
                return ToolCall(control=ControlTag.ASK_CLARIFICATION, confidence=confidence)
        if self.description_aware_inhibition and _tool_has_description_capability_gap(tool, example.case.request):
            return ToolCall(control=ControlTag.ASK_CLARIFICATION, confidence=_sigmoid(best_active_score - self.threshold))
        arguments: dict[str, object] = {}
        for argument in tool.arguments:
            value = example.case.slot_values.get(argument.canonical_name)
            if value is None:
                if argument.required:
                    return ToolCall(control=ControlTag.ASK_CLARIFICATION, confidence=_sigmoid(best_active_score - self.threshold))
                continue
            arguments[argument.rendered_name] = value
        confidence = _sigmoid(best_active_score - max(second_active_score, decision_floor))
        return ToolCall(
            control=ControlTag.EXECUTE,
            rendered_tool_name=tool.rendered_name,
            arguments=arguments,
            confidence=confidence,
        )

    def _should_rescue_execute(
        self,
        *,
        example: ViewExample,
        tool: RenderedTool | None,
        best_active_score: float,
        second_active_score: float,
    ) -> bool:
        if tool is None:
            return False
        if best_active_score < self.threshold - SEMANTIC_RESCUE_MARGIN:
            return False
        if (best_active_score - second_active_score) < SEMANTIC_RESCUE_MIN_LEAD:
            return False
        if self.contract_aware_inhibition and not _tool_contract_compatible(tool, example.case.slot_values):
            return False
        if self.description_aware_inhibition and _tool_has_description_capability_gap(tool, example.case.request):
            return False
        return _tool_request_capability_overlap(tool, example.case.request) >= SEMANTIC_RESCUE_MIN_OVERLAP

    def _text_feature(self, text: str) -> torch.Tensor:
        return self._encode_text(self.encoder._with_instruction(text))

    def _encode_text(self, text: str) -> torch.Tensor:
        cached = self._text_cache.get(text)
        if cached is not None:
            return cached
        feature = self.encoder.encode_texts([text])[0].float().cpu()
        self._text_cache[text] = feature
        return feature


class CrossEncoderSemanticGateAgent(BaseAgent):
    def __init__(
        self,
        *,
        name: str,
        encoder: FrozenEmbeddingEncoder,
        threshold: float,
        cross_encoder: QwenRerankerCrossEncoder,
        contract_aware_inhibition: bool,
        clause_localizer: CrossEncoderClauseLocalizer,
        capability_gate: CrossEncoderCapabilityGate,
        capability_scorer: LearnedCapabilityScorer | None = None,
    ) -> None:
        super().__init__(name=name)
        self.encoder = encoder
        self.threshold = threshold
        self.cross_encoder = cross_encoder
        self.contract_aware_inhibition = contract_aware_inhibition
        self.clause_localizer = clause_localizer
        self.capability_gate = capability_gate
        self.capability_scorer = capability_scorer
        self._request_cache: dict[str, torch.Tensor] = {}
        self._text_cache: dict[str, torch.Tensor] = {}

    def predict(self, example: ViewExample) -> ToolCall:
        _require_torch()
        request_feature = self._request_feature(example.case.request)
        active_tools = [tool for tool in example.schema_view.tools if tool.status == "active"]
        active_scores = [(self._tool_similarity(request_feature, tool), tool) for tool in active_tools]
        active_scores.sort(key=lambda item: item[0], reverse=True)

        best_any_score = float("-inf")
        best_any_tool = None
        for tool in example.schema_view.tools:
            score = self._tool_similarity(request_feature, tool)
            if score > best_any_score:
                best_any_score = score
                best_any_tool = tool

        best_active_score = active_scores[0][0] if active_scores else float("-inf")
        best_active_tool = active_scores[0][1] if active_scores else None
        second_active_score = active_scores[1][0] if len(active_scores) > 1 else 0.0

        if best_active_tool is not None and best_active_score >= self.threshold:
            return self._build_execute_call(
                example=example,
                tool=best_active_tool,
                best_active_score=best_active_score,
                second_active_score=second_active_score,
                decision_floor=self.threshold,
            )

        if best_any_tool is not None and best_any_score > 0:
            return ToolCall(control=ControlTag.ABSTAIN, confidence=_sigmoid(best_any_score - self.threshold))
        return ToolCall(control=ControlTag.ASK_CLARIFICATION, confidence=_sigmoid(self.threshold - max(best_active_score, 0.0)))

    def _build_execute_call(
        self,
        *,
        example: ViewExample,
        tool: RenderedTool,
        best_active_score: float,
        second_active_score: float,
        decision_floor: float,
    ) -> ToolCall:
        if self.contract_aware_inhibition and not _tool_contract_compatible(tool, example.case.slot_values):
            return ToolCall(control=ControlTag.ASK_CLARIFICATION, confidence=_sigmoid(best_active_score - self.threshold))

        if self.capability_scorer is not None:
            feature_map, _selected_clause = _cross_encoder_feature_map(
                request=example.case.request,
                tool=tool,
                best_active_score=best_active_score,
                second_active_score=second_active_score,
                cross_encoder=self.cross_encoder,
                clause_localizer=self.clause_localizer,
                capability_instruction=self.capability_gate.instruction,
                feature_names=self.capability_scorer.feature_names,
            )
            inhibit, confidence = self.capability_scorer.should_inhibit(feature_map)
        else:
            selected_clause = _select_cross_encoder_clause(
                request=example.case.request,
                tool=tool,
                cross_encoder=self.cross_encoder,
                clause_localizer=self.clause_localizer,
            )
            control, confidence = _cross_encoder_decide_capability_control(
                request=example.case.request,
                tool=tool,
                selected_clause=selected_clause,
                cross_encoder=self.cross_encoder,
                capability_gate=self.capability_gate,
            )
            if control is not None:
                return ToolCall(control=control, confidence=confidence)
            inhibit = False
        if inhibit:
            return ToolCall(control=ControlTag.ASK_CLARIFICATION, confidence=confidence)

        arguments: dict[str, object] = {}
        for argument in tool.arguments:
            value = example.case.slot_values.get(argument.canonical_name)
            if value is None:
                if argument.required:
                    return ToolCall(control=ControlTag.ASK_CLARIFICATION, confidence=_sigmoid(best_active_score - self.threshold))
                continue
            arguments[argument.rendered_name] = value
        confidence = _sigmoid(best_active_score - max(second_active_score, decision_floor))
        return ToolCall(
            control=ControlTag.EXECUTE,
            rendered_tool_name=tool.rendered_name,
            arguments=arguments,
            confidence=confidence,
        )

    def _request_feature(self, request: str) -> torch.Tensor:
        cached = self._request_cache.get(request)
        if cached is not None:
            return cached
        feature = self._encode_text(self.encoder._with_instruction(serialize_request(request)))
        self._request_cache[request] = feature
        return feature

    def _tool_similarity(self, request_feature: torch.Tensor, tool: RenderedTool) -> float:
        tool_text = serialize_tool(tool)
        return float(torch.dot(request_feature, self._encode_text(self.encoder._with_instruction(tool_text))).item())

    def _encode_text(self, text: str) -> torch.Tensor:
        cached = self._text_cache.get(text)
        if cached is not None:
            return cached
        feature = self.encoder.encode_texts([text])[0].float().cpu()
        self._text_cache[text] = feature
        return feature


if nn is not None:
    class ActionBottleneckModel(nn.Module):
        def __init__(
            self,
            input_dim: int,
            bottleneck_dim: int,
            tool_vocab_size: int,
            *,
            slot_vocab_size: int = 0,
            use_gap_head: bool = False,
        ) -> None:
            super().__init__()
            self.projection = nn.Sequential(
                nn.Linear(input_dim, bottleneck_dim),
                nn.Tanh(),
            )
            self.control_head = nn.Linear(bottleneck_dim, len(CONTROL_ORDER))
            self.tool_head = nn.Linear(bottleneck_dim, tool_vocab_size)
            self.slot_head = nn.Linear(bottleneck_dim, slot_vocab_size) if slot_vocab_size > 0 else None
            self.gap_head = nn.Linear(bottleneck_dim, 1) if use_gap_head else None

        def action_state(self, features: torch.Tensor) -> torch.Tensor:
            return self.projection(features)

        def forward(self, features: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
            action_state = self.action_state(features)
            return action_state, self.control_head(action_state), self.tool_head(action_state)

        def slot_logits(self, action_state: torch.Tensor) -> torch.Tensor | None:
            if self.slot_head is None:
                return None
            return self.slot_head(action_state)

        def gap_logits(self, action_state: torch.Tensor) -> torch.Tensor | None:
            if self.gap_head is None:
                return None
            return self.gap_head(action_state).squeeze(-1)
else:
    class ActionBottleneckModel:
        def __init__(self, *args, **kwargs) -> None:
            raise ModuleNotFoundError("torch is required for ActionBottleneckModel")


if nn is not None:
    @dataclass(frozen=True)
    class PrototypeExecuteGate:
        execute_center: torch.Tensor
        nonexecute_center: torch.Tensor
        ask_center: torch.Tensor | None
        abstain_center: torch.Tensor | None
        threshold: float

        def decide(self, action_state: torch.Tensor, control_logits: torch.Tensor) -> tuple[ControlTag, float]:
            normalized = F.normalize(action_state.unsqueeze(0), dim=-1)[0]
            execute_score = float(torch.dot(normalized, self.execute_center).item())
            nonexecute_score = float(torch.dot(normalized, self.nonexecute_center).item())
            margin = execute_score - nonexecute_score
            if margin >= self.threshold:
                confidence = _sigmoid(margin - self.threshold)
                return ControlTag.EXECUTE, confidence

            nonexecute_scores: list[tuple[ControlTag, float]] = []
            if self.ask_center is not None:
                nonexecute_scores.append(
                    (ControlTag.ASK_CLARIFICATION, float(torch.dot(normalized, self.ask_center).item()))
                )
            if self.abstain_center is not None:
                nonexecute_scores.append(
                    (ControlTag.ABSTAIN, float(torch.dot(normalized, self.abstain_center).item()))
                )
            if nonexecute_scores:
                nonexecute_scores.sort(key=lambda item: item[1], reverse=True)
                best_control, best_score = nonexecute_scores[0]
                runner_up = nonexecute_scores[1][1] if len(nonexecute_scores) > 1 else 0.0
                confidence = _sigmoid(best_score - runner_up)
                return best_control, confidence

            nonexecute_indices = torch.tensor(
                [CONTROL_ORDER.index(ControlTag.ASK_CLARIFICATION), CONTROL_ORDER.index(ControlTag.ABSTAIN)],
                dtype=torch.long,
            )
            nonexecute_logits = control_logits.index_select(0, nonexecute_indices)
            nonexecute_probs = F.softmax(nonexecute_logits, dim=-1)
            best_index = int(nonexecute_probs.argmax().item())
            confidence = float(nonexecute_probs[best_index].item())
            return (ControlTag.ASK_CLARIFICATION, confidence) if best_index == 0 else (ControlTag.ABSTAIN, confidence)
else:
    @dataclass(frozen=True)
    class PrototypeExecuteGate:
        execute_center: object
        nonexecute_center: object
        ask_center: object
        abstain_center: object
        threshold: float

        def decide(self, action_state, control_logits):
            raise ModuleNotFoundError("torch is required for PrototypeExecuteGate")


class EmbeddingPolicyAgent(BaseAgent):
    def __init__(
        self,
        *,
        name: str,
        model: ActionBottleneckModel,
        suite: BenchmarkSuite,
        tool_vocab: Sequence[str],
        feature_lookup: dict[str, torch.Tensor],
        encoder: FrozenEmbeddingEncoder | None = None,
        prototype_gate: PrototypeExecuteGate | None = None,
    ) -> None:
        super().__init__(name=name)
        self.model = model.cpu().eval()
        self.suite = suite
        self.tool_vocab = tuple(tool_vocab)
        self.tool_to_index = {tool_id: index for index, tool_id in enumerate(self.tool_vocab)}
        self.feature_lookup = {view_id: feature.float().cpu() for view_id, feature in feature_lookup.items()}
        self.encoder = encoder
        self.prototype_gate = prototype_gate

    def predict(self, example: ViewExample) -> ToolCall:
        _require_torch()
        feature = self._feature_for(example)
        with torch.inference_mode():
            action_state, control_logits, tool_logits = self.model(feature.unsqueeze(0))
        control_probs = F.softmax(control_logits[0], dim=-1)
        if self.prototype_gate is None:
            control_index = int(control_probs.argmax().item())
            control = CONTROL_ORDER[control_index]
            control_confidence = float(control_probs[control_index].item())
        else:
            control, control_confidence = self.prototype_gate.decide(action_state[0], control_logits[0])
        if control != ControlTag.EXECUTE:
            return ToolCall(
                control=control,
                confidence=control_confidence,
            )

        visible_tools = [tool for tool in example.schema_view.tools if tool.canonical_tool_id in self.tool_to_index]
        if not visible_tools:
            return ToolCall(control=ControlTag.ABSTAIN, confidence=control_confidence)

        visible_indices = torch.tensor(
            [self.tool_to_index[tool.canonical_tool_id] for tool in visible_tools],
            dtype=torch.long,
        )
        visible_logits = tool_logits[0].index_select(0, visible_indices)
        visible_probs = F.softmax(visible_logits, dim=-1)
        best_local_index = int(visible_probs.argmax().item())
        best_tool = visible_tools[best_local_index]
        arguments: dict[str, object] = {}
        for argument in best_tool.arguments:
            value = example.case.slot_values.get(argument.canonical_name)
            if value is None:
                if argument.required:
                    return ToolCall(control=ControlTag.ASK_CLARIFICATION, confidence=control_confidence)
                continue
            arguments[argument.rendered_name] = value
        confidence = float(control_confidence * visible_probs[best_local_index].item())
        return ToolCall(
            control=ControlTag.EXECUTE,
            rendered_tool_name=best_tool.rendered_name,
            arguments=arguments,
            confidence=confidence,
        )

    def _feature_for(self, example: ViewExample) -> torch.Tensor:
        _require_torch()
        cached = self.feature_lookup.get(example.schema_view.view_id)
        if cached is not None:
            return cached
        if self.encoder is None:
            raise KeyError(f"missing embedding for {example.schema_view.view_id}")
        encoded = self.encoder.encode_texts([self.encoder._with_instruction(serialize_view(example))])[0]
        self.feature_lookup[example.schema_view.view_id] = encoded
        return encoded


def train_teacher_distilled_bottleneck_scc_agent(
    *,
    name: str,
    suite: BenchmarkSuite,
    train_examples: Sequence[ViewExample],
    feature_lookup: dict[str, torch.Tensor],
    config: EmbeddingPolicyConfig,
    encoder: FrozenEmbeddingEncoder | None,
) -> tuple[EmbeddingPolicyAgent, dict[str, float]]:
    _require_torch()
    if encoder is None:
        raise ValueError("teacher_distilled_bottleneck_scc requires an encoder for teacher supervision")

    teacher_agent, teacher_metrics = train_semantic_gate_agent(
        name=f"{name}_teacher",
        train_examples=train_examples,
        config=config,
        encoder=encoder,
        contract_aware_inhibition=True,
        description_aware_inhibition=False,
        learned_capability_inhibition=True,
        capability_feature_names=CAPABILITY_EMBEDDING_FEATURE_NAMES,
        capability_require_cue=False,
    )

    torch.manual_seed(config.seed)
    tool_vocab = build_tool_vocab(suite)
    slot_vocab = build_slot_vocab(suite)
    tool_to_index = {tool_id: index for index, tool_id in enumerate(tool_vocab)}
    slot_to_index = {slot_name: index for index, slot_name in enumerate(slot_vocab)}
    train_features = torch.stack([feature_lookup[example.schema_view.view_id].float() for example in train_examples])
    control_targets = torch.tensor([_control_index(example) for example in train_examples], dtype=torch.long)
    tool_targets = torch.tensor([_tool_index(example, tool_to_index) for example in train_examples], dtype=torch.long)
    slot_targets = torch.stack(
        [
            _canonical_slot_target(
                example,
                slot_to_index=slot_to_index,
                tool_lookup=suite.tool_lookup,
            )
            for example in train_examples
        ]
    )

    teacher_calls = [teacher_agent.predict(example) for example in train_examples]
    teacher_control_targets = torch.tensor(
        [CONTROL_ORDER.index(call.control) for call in teacher_calls],
        dtype=torch.long,
    )
    teacher_tool_targets = torch.tensor(
        [
            tool_to_index[_rendered_tool_to_canonical_id(example, call.rendered_tool_name)]
            if call.control == ControlTag.EXECUTE
            and _rendered_tool_to_canonical_id(example, call.rendered_tool_name) in tool_to_index
            else -1
            for example, call in zip(train_examples, teacher_calls, strict=True)
        ],
        dtype=torch.long,
    )
    teacher_slot_targets = torch.stack(
        [
            _teacher_slot_target(example, call, slot_to_index=slot_to_index)
            for example, call in zip(train_examples, teacher_calls, strict=True)
        ]
    )
    teacher_gap_targets = torch.tensor(
        [_teacher_gap_target(teacher_agent, example) for example in train_examples],
        dtype=torch.float32,
    )

    model = ActionBottleneckModel(
        input_dim=int(train_features.shape[1]),
        bottleneck_dim=config.bottleneck_dim,
        tool_vocab_size=len(tool_vocab),
        slot_vocab_size=len(slot_vocab),
        use_gap_head=True,
    )
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay,
    )
    execute_mask = tool_targets >= 0
    teacher_execute_mask = teacher_tool_targets >= 0

    metrics = {"train_examples": float(len(train_examples))}
    for _ in range(config.epochs):
        action_state, control_logits, tool_logits = model(train_features)
        slot_logits = model.slot_logits(action_state)
        gap_logits = model.gap_logits(action_state)

        control_loss = F.cross_entropy(control_logits, control_targets)
        tool_loss = (
            F.cross_entropy(tool_logits[execute_mask], tool_targets[execute_mask])
            if execute_mask.any()
            else torch.tensor(0.0)
        )
        slot_loss = (
            F.binary_cross_entropy_with_logits(slot_logits[execute_mask], slot_targets[execute_mask])
            if slot_logits is not None and execute_mask.any()
            else torch.tensor(0.0)
        )
        invariance_loss = _positive_invariance_loss(action_state, train_examples)
        contrastive_loss = _negative_contrastive_loss(
            action_state,
            train_examples,
            margin=config.contrastive_margin,
        )
        distill_control_loss = F.cross_entropy(control_logits, teacher_control_targets)
        distill_tool_loss = (
            F.cross_entropy(tool_logits[teacher_execute_mask], teacher_tool_targets[teacher_execute_mask])
            if teacher_execute_mask.any()
            else torch.tensor(0.0)
        )
        distill_slot_loss = (
            F.binary_cross_entropy_with_logits(slot_logits[teacher_execute_mask], teacher_slot_targets[teacher_execute_mask])
            if slot_logits is not None and teacher_execute_mask.any()
            else torch.tensor(0.0)
        )
        distill_gap_loss = (
            F.binary_cross_entropy_with_logits(gap_logits, teacher_gap_targets)
            if gap_logits is not None
            else torch.tensor(0.0)
        )

        loss = (
            control_loss
            + tool_loss
            + config.lambda_slot * slot_loss
            + config.lambda_inv * invariance_loss
            + config.lambda_ctr * contrastive_loss
            + config.lambda_distill_control * distill_control_loss
            + config.lambda_distill_tool * distill_tool_loss
            + config.lambda_distill_slot * distill_slot_loss
            + config.lambda_distill_gap * distill_gap_loss
        )
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        metrics = {
            "L_total": float(loss.item()),
            "L_ctl": float(control_loss.item()),
            "L_ce": float(tool_loss.item()),
            "L_slot": float(slot_loss.item()),
            "L_inv": float(invariance_loss.item()),
            "L_ctr": float(contrastive_loss.item()),
            "L_distill_ctl": float(distill_control_loss.item()),
            "L_distill_tool": float(distill_tool_loss.item()),
            "L_distill_slot": float(distill_slot_loss.item()),
            "L_distill_gap": float(distill_gap_loss.item()),
            "train_examples": float(len(train_examples)),
            "slot_vocab_size": float(len(slot_vocab)),
            "teacher_execute_rate": float(teacher_execute_mask.float().mean().item()),
            "teacher_gap_rate": float(teacher_gap_targets.mean().item()),
        }

    with torch.inference_mode():
        final_action_state, final_control_logits, final_tool_logits = model(train_features)
        final_slot_logits = model.slot_logits(final_action_state)
        final_gap_logits = model.gap_logits(final_action_state)
        control_predictions = final_control_logits.argmax(dim=-1)
        metrics.update(
            {
                "train_control_accuracy": float((control_predictions == control_targets).float().mean().item()),
                "teacher_control_agreement": float((control_predictions == teacher_control_targets).float().mean().item()),
                "teacher_train_execute_recall": teacher_metrics["gate_train_execute_recall"],
                "teacher_train_execute_rate": teacher_metrics["gate_train_execute_rate"],
            }
        )
        if execute_mask.any():
            tool_predictions = final_tool_logits[execute_mask].argmax(dim=-1)
            metrics["train_tool_accuracy"] = float((tool_predictions == tool_targets[execute_mask]).float().mean().item())
        else:
            metrics["train_tool_accuracy"] = 0.0
        if final_slot_logits is not None and execute_mask.any():
            slot_predictions = (torch.sigmoid(final_slot_logits[execute_mask]) >= 0.5).float()
            metrics["train_slot_accuracy"] = float((slot_predictions == slot_targets[execute_mask]).float().mean().item())
        else:
            metrics["train_slot_accuracy"] = 0.0
        if final_gap_logits is not None:
            gap_predictions = (torch.sigmoid(final_gap_logits) >= 0.5).float()
            metrics["train_gap_accuracy"] = float((gap_predictions == teacher_gap_targets).float().mean().item())
        else:
            metrics["train_gap_accuracy"] = 0.0

    return (
        EmbeddingPolicyAgent(
            name=name,
            model=model,
            suite=suite,
            tool_vocab=tool_vocab,
            feature_lookup=feature_lookup,
            encoder=encoder,
        ),
        metrics,
    )


def train_embedding_policy_agent(
    *,
    name: str,
    suite: BenchmarkSuite,
    train_examples: Sequence[ViewExample],
    feature_lookup: dict[str, torch.Tensor],
    config: EmbeddingPolicyConfig,
    method: str,
    encoder: FrozenEmbeddingEncoder | None = None,
) -> tuple[EmbeddingPolicyAgent, dict[str, float]]:
    _require_torch()
    if not train_examples:
        raise ValueError("train_examples must be non-empty")
    if method == "seed_only":
        clean_examples = [example for example in train_examples if example.schema_view.shift_kind == ShiftKind.CLEAN]
        if not clean_examples:
            raise ValueError("seed_only requires at least one clean training example")
        return train_embedding_policy_agent(
            name=name,
            suite=suite,
            train_examples=clean_examples,
            feature_lookup=feature_lookup,
            config=config,
            method="aug_only",
            encoder=encoder,
        )
    if method == "teacher_distilled_bottleneck_scc":
        return train_teacher_distilled_bottleneck_scc_agent(
            name=name,
            suite=suite,
            train_examples=train_examples,
            feature_lookup=feature_lookup,
            config=config,
            encoder=encoder,
        )
    if method == "semantic_gate":
        return train_semantic_gate_agent(
            name=name,
            train_examples=train_examples,
            config=config,
            encoder=encoder,
            contract_aware_inhibition=False,
            description_aware_inhibition=False,
        )
    if method == "semantic_contract_gate":
        return train_semantic_gate_agent(
            name=name,
            train_examples=train_examples,
            config=config,
            encoder=encoder,
            contract_aware_inhibition=True,
            description_aware_inhibition=False,
        )
    if method == "semantic_capability_gate":
        return train_semantic_gate_agent(
            name=name,
            train_examples=train_examples,
            config=config,
            encoder=encoder,
            contract_aware_inhibition=True,
            description_aware_inhibition=True,
        )
    if method == "semantic_learned_capability_gate":
        return train_semantic_gate_agent(
            name=name,
            train_examples=train_examples,
            config=config,
            encoder=encoder,
            contract_aware_inhibition=True,
            description_aware_inhibition=False,
            learned_capability_inhibition=True,
            capability_feature_names=CAPABILITY_FEATURE_NAMES,
            capability_require_cue=True,
        )
    if method == "semantic_sparse_capability_gate":
        return train_semantic_gate_agent(
            name=name,
            train_examples=train_examples,
            config=config,
            encoder=encoder,
            contract_aware_inhibition=True,
            description_aware_inhibition=False,
            learned_capability_inhibition=True,
            capability_feature_names=CAPABILITY_CUE_FEATURE_NAMES,
            capability_require_cue=False,
        )
    if method == "semantic_continuous_capability_gate":
        return train_semantic_gate_agent(
            name=name,
            train_examples=train_examples,
            config=config,
            encoder=encoder,
            contract_aware_inhibition=True,
            description_aware_inhibition=False,
            learned_capability_inhibition=True,
            capability_feature_names=CAPABILITY_CONTINUOUS_FEATURE_NAMES,
            capability_require_cue=False,
        )
    if method == "semantic_embedding_capability_gate":
        return train_semantic_gate_agent(
            name=name,
            train_examples=train_examples,
            config=config,
            encoder=encoder,
            contract_aware_inhibition=True,
            description_aware_inhibition=False,
            learned_capability_inhibition=True,
            capability_feature_names=CAPABILITY_EMBEDDING_FEATURE_NAMES,
            capability_require_cue=False,
        )
    if method == "semantic_raw_text_capability_gate":
        return train_semantic_gate_agent(
            name=name,
            train_examples=train_examples,
            config=config,
            encoder=encoder,
            contract_aware_inhibition=True,
            description_aware_inhibition=False,
            learned_capability_inhibition=True,
            capability_feature_names=CAPABILITY_RAWTEXT_FEATURE_NAMES,
            capability_require_cue=False,
        )
    if method == "semantic_description_pool_capability_gate":
        return train_semantic_gate_agent(
            name=name,
            train_examples=train_examples,
            config=config,
            encoder=encoder,
            contract_aware_inhibition=True,
            description_aware_inhibition=False,
            learned_capability_inhibition=True,
            capability_feature_names=CAPABILITY_DESCRIPTION_POOL_FEATURE_NAMES,
            capability_require_cue=False,
        )
    if method == "semantic_interaction_capability_gate":
        return train_semantic_gate_agent(
            name=name,
            train_examples=train_examples,
            config=config,
            encoder=encoder,
            contract_aware_inhibition=True,
            description_aware_inhibition=False,
            dense_capability_inhibition_mode="localized_clause_interaction",
        )
    if method == "semantic_clause_localization_capability_gate":
        return train_semantic_gate_agent(
            name=name,
            train_examples=train_examples,
            config=config,
            encoder=encoder,
            contract_aware_inhibition=True,
            description_aware_inhibition=False,
            dense_capability_inhibition_mode="learned_clause_localization_interaction",
        )
    if method == "semantic_clause_localization_calibrated_gate":
        return train_semantic_gate_agent(
            name=name,
            train_examples=train_examples,
            config=config,
            encoder=encoder,
            contract_aware_inhibition=True,
            description_aware_inhibition=False,
            dense_capability_inhibition_mode="learned_clause_localization_scalar",
        )
    if method == "semantic_pair_text_capability_gate":
        return train_semantic_gate_agent(
            name=name,
            train_examples=train_examples,
            config=config,
            encoder=encoder,
            contract_aware_inhibition=True,
            description_aware_inhibition=False,
            dense_capability_inhibition_mode="learned_clause_localization_pair_text",
        )
    if method == "semantic_pair_text_mlp_capability_gate":
        return train_semantic_gate_agent(
            name=name,
            train_examples=train_examples,
            config=config,
            encoder=encoder,
            contract_aware_inhibition=True,
            description_aware_inhibition=False,
            dense_capability_inhibition_mode="learned_clause_localization_pair_text_mlp",
        )
    if method == "semantic_cross_encoder_capability_gate":
        return train_cross_encoder_semantic_gate_agent(
            name=name,
            train_examples=train_examples,
            config=config,
            encoder=encoder,
            contract_aware_inhibition=True,
        )
    if method == "semantic_cross_encoder_supervised_capability_gate":
        return train_supervised_cross_encoder_semantic_gate_agent(
            name=name,
            train_examples=train_examples,
            config=config,
            encoder=encoder,
            contract_aware_inhibition=True,
        )
    if method == "semantic_cross_encoder_ranked_capability_gate":
        return train_ranked_cross_encoder_semantic_gate_agent(
            name=name,
            train_examples=train_examples,
            config=config,
            encoder=encoder,
            contract_aware_inhibition=True,
        )
    if method == "semantic_cross_encoder_pairwise_capability_gate":
        return train_pairwise_cross_encoder_semantic_gate_agent(
            name=name,
            train_examples=train_examples,
            config=config,
            encoder=encoder,
            contract_aware_inhibition=True,
        )
    if method == "semantic_cross_encoder_listwise_capability_gate":
        return train_listwise_cross_encoder_semantic_gate_agent(
            name=name,
            train_examples=train_examples,
            config=config,
            encoder=encoder,
            contract_aware_inhibition=True,
        )
    if method == "semantic_cross_encoder_finetuned_capability_gate":
        return train_finetuned_cross_encoder_capability_gate_agent(
            name=name,
            train_examples=train_examples,
            config=config,
            encoder=encoder,
            contract_aware_inhibition=True,
        )
    if method == "semantic_cross_encoder_multitask_capability_gate":
        return train_multitask_cross_encoder_capability_gate_agent(
            name=name,
            train_examples=train_examples,
            config=config,
            encoder=encoder,
            contract_aware_inhibition=True,
        )
    if method == "semantic_cross_encoder_hard_negative_capability_gate":
        return train_hard_negative_finetuned_cross_encoder_capability_gate_agent(
            name=name,
            train_examples=train_examples,
            config=config,
            encoder=encoder,
            contract_aware_inhibition=True,
        )
    if method == "semantic_cross_encoder_asymmetric_capability_gate":
        return train_asymmetric_hard_negative_finetuned_cross_encoder_capability_gate_agent(
            name=name,
            train_examples=train_examples,
            config=config,
            encoder=encoder,
            contract_aware_inhibition=True,
        )
    if method == "semantic_cross_encoder_asymmetric_objective_capability_gate":
        return train_asymmetric_objective_finetuned_cross_encoder_capability_gate_agent(
            name=name,
            train_examples=train_examples,
            config=config,
            encoder=encoder,
            contract_aware_inhibition=True,
        )
    if method == "semantic_cross_encoder_dual_threshold_capability_gate":
        return train_dual_threshold_finetuned_cross_encoder_capability_gate_agent(
            name=name,
            train_examples=train_examples,
            config=config,
            encoder=encoder,
            contract_aware_inhibition=True,
        )
    base_method, use_prototype_gate = _parse_method(method)
    if base_method not in {"aug_only", "scc_lite"}:
        raise ValueError(f"unsupported method: {method}")

    torch.manual_seed(config.seed)
    tool_vocab = build_tool_vocab(suite)
    tool_to_index = {tool_id: index for index, tool_id in enumerate(tool_vocab)}
    train_features = torch.stack([feature_lookup[example.schema_view.view_id].float() for example in train_examples])
    control_targets = torch.tensor([_control_index(example) for example in train_examples], dtype=torch.long)
    tool_targets = torch.tensor([_tool_index(example, tool_to_index) for example in train_examples], dtype=torch.long)

    model = ActionBottleneckModel(
        input_dim=int(train_features.shape[1]),
        bottleneck_dim=config.bottleneck_dim,
        tool_vocab_size=len(tool_vocab),
    )
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay,
    )
    execute_mask = tool_targets >= 0

    metrics = {"train_examples": float(len(train_examples))}
    for _ in range(config.epochs):
        action_state, control_logits, tool_logits = model(train_features)
        control_loss = F.cross_entropy(control_logits, control_targets)
        tool_loss = (
            F.cross_entropy(tool_logits[execute_mask], tool_targets[execute_mask])
            if execute_mask.any()
            else torch.tensor(0.0)
        )
        invariance_loss = torch.tensor(0.0)
        contrastive_loss = torch.tensor(0.0)
        loss = control_loss + tool_loss
        if base_method == "scc_lite":
            invariance_loss = _positive_invariance_loss(action_state, train_examples)
            contrastive_loss = _negative_contrastive_loss(
                action_state,
                train_examples,
                margin=config.contrastive_margin,
            )
            loss = loss + config.lambda_inv * invariance_loss + config.lambda_ctr * contrastive_loss
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        metrics = {
            "L_total": float(loss.item()),
            "L_ctl": float(control_loss.item()),
            "L_ce": float(tool_loss.item()),
            "L_inv": float(invariance_loss.item()),
            "L_ctr": float(contrastive_loss.item()),
            "train_examples": float(len(train_examples)),
        }

    prototype_gate = None
    if use_prototype_gate:
        with torch.inference_mode():
            train_action_state = model.action_state(train_features).cpu()
        prototype_gate, gate_stats = _fit_prototype_execute_gate(train_action_state, control_targets)
        metrics.update(
            {
                "gate_threshold": gate_stats.threshold,
                "gate_train_accuracy": gate_stats.train_accuracy,
                "gate_train_execute_recall": gate_stats.train_execute_recall,
                "gate_train_execute_rate": gate_stats.train_execute_rate,
            }
        )

    return (
        EmbeddingPolicyAgent(
            name=name,
            model=model,
            suite=suite,
            tool_vocab=tool_vocab,
            feature_lookup=feature_lookup,
            encoder=encoder,
            prototype_gate=prototype_gate,
        ),
        metrics,
    )


def action_state_similarity(
    agent: BaseAgent,
    examples: Sequence[ViewExample],
    feature_lookup: dict[str, torch.Tensor],
) -> float | None:
    _require_torch()
    if not hasattr(agent, "model"):
        return None
    positive_examples = [
        example
        for example in examples
        if example.schema_view.shift_kind in {ShiftKind.CLEAN, ShiftKind.POSITIVE_ORBIT}
    ]
    if not positive_examples:
        return None
    features = torch.stack([feature_lookup[example.schema_view.view_id].float() for example in positive_examples])
    with torch.inference_mode():
        action_state = agent.model.action_state(features)

    grouped_indices: dict[str, list[int]] = defaultdict(list)
    for index, example in enumerate(positive_examples):
        grouped_indices[example.case.case_id].append(index)

    similarities: list[float] = []
    normalized = F.normalize(action_state, dim=-1)
    for indices in grouped_indices.values():
        if len(indices) < 2:
            continue
        pairwise = normalized[indices] @ normalized[indices].T
        count = len(indices)
        mean_similarity = (pairwise.sum() - count) / (count * (count - 1))
        similarities.append(float(mean_similarity.item()))
    if not similarities:
        return None
    return sum(similarities) / len(similarities)


def _control_index(example: ViewExample) -> int:
    target_control = example.admissible_actions[0].control
    return CONTROL_ORDER.index(target_control)


def _tool_index(example: ViewExample, tool_to_index: dict[str, int]) -> int:
    action = example.admissible_actions[0]
    if action.control != ControlTag.EXECUTE or action.tool_id is None:
        return -1
    return tool_to_index[action.tool_id]


def _canonical_slot_target(
    example: ViewExample,
    *,
    slot_to_index: dict[str, int],
    tool_lookup: dict[str, RenderedTool] | None = None,
) -> torch.Tensor:
    _require_torch()
    target = torch.zeros(len(slot_to_index), dtype=torch.float32)
    action = example.admissible_actions[0]
    if action.control != ControlTag.EXECUTE:
        return target
    if tool_lookup is None:
        argument_names = action.arguments.keys()
    else:
        tool = tool_lookup.get(action.tool_id or "")
        if tool is None:
            argument_names = action.arguments.keys()
        else:
            argument_names = [
                argument.canonical_name
                for argument in tool.arguments
                if argument.canonical_name in action.arguments
            ]
    for canonical_name in argument_names:
        index = slot_to_index.get(canonical_name)
        if index is not None:
            target[index] = 1.0
    return target


def _rendered_tool_to_canonical_id(example: ViewExample, rendered_name: str | None) -> str | None:
    if rendered_name is None:
        return None
    for tool in example.schema_view.tools:
        if tool.rendered_name == rendered_name:
            return tool.canonical_tool_id
    return None


def _teacher_slot_target(
    example: ViewExample,
    teacher_call: ToolCall,
    *,
    slot_to_index: dict[str, int],
) -> torch.Tensor:
    _require_torch()
    target = torch.zeros(len(slot_to_index), dtype=torch.float32)
    if teacher_call.control != ControlTag.EXECUTE or teacher_call.rendered_tool_name is None:
        return target
    selected_tool = next(
        (tool for tool in example.schema_view.tools if tool.rendered_name == teacher_call.rendered_tool_name),
        None,
    )
    if selected_tool is None:
        return target
    rendered_to_canonical = {
        argument.rendered_name: argument.canonical_name
        for argument in selected_tool.arguments
    }
    for rendered_name in teacher_call.arguments:
        canonical_name = rendered_to_canonical.get(rendered_name)
        if canonical_name is None:
            continue
        index = slot_to_index.get(canonical_name)
        if index is not None:
            target[index] = 1.0
    return target


def _teacher_gap_target(teacher: SemanticGateAgent, example: ViewExample) -> float:
    active_tools = [tool for tool in example.schema_view.tools if tool.status == "active"]
    if not active_tools:
        return 0.0
    request_feature = teacher._request_feature(example.case.request)
    scored = sorted(
        ((teacher._tool_similarity(request_feature, tool), tool) for tool in active_tools),
        key=lambda item: item[0],
        reverse=True,
    )
    best_tool = scored[0][1]
    has_contract_gap = teacher.contract_aware_inhibition and not _tool_contract_compatible(best_tool, example.case.slot_values)
    has_description_gap = _tool_has_description_capability_gap(best_tool, example.case.request)
    return 1.0 if has_contract_gap or has_description_gap else 0.0


def _parse_method(method: str) -> tuple[str, bool]:
    if method == "semantic_gate":
        raise ValueError("semantic_gate should be dispatched before _parse_method")
    if method == "aug_only":
        return "aug_only", False
    if method == "scc_lite":
        return "scc_lite", False
    if method == "aug_proto_gate":
        return "aug_only", True
    if method == "scc_proto_gate":
        return "scc_lite", True
    raise ValueError(f"unsupported method: {method}")


def train_semantic_gate_agent(
    *,
    name: str,
    train_examples: Sequence[ViewExample],
    config: EmbeddingPolicyConfig,
    encoder: FrozenEmbeddingEncoder | None,
    contract_aware_inhibition: bool,
    description_aware_inhibition: bool,
    learned_capability_inhibition: bool = False,
    capability_feature_names: Sequence[str] = CAPABILITY_FEATURE_NAMES,
    capability_require_cue: bool = False,
    dense_capability_inhibition_mode: str | None = None,
) -> tuple[SemanticGateAgent, dict[str, float]]:
    _require_torch()
    if encoder is None:
        raise ValueError("semantic_gate requires an encoder")

    execute_scores = []
    execute_labels = []
    for example in train_examples:
        request_feature = encoder.encode_texts([encoder._with_instruction(serialize_request(example.case.request))])[0].float().cpu()
        active_scores = [
            float(torch.dot(request_feature, encoder.encode_texts([encoder._with_instruction(serialize_tool(tool))])[0].float().cpu()).item())
            for tool in example.schema_view.tools
            if tool.status == "active"
        ]
        execute_scores.append(max(active_scores) if active_scores else float("-inf"))
        execute_labels.append(example.admissible_actions[0].control == ControlTag.EXECUTE)

    threshold = _best_binary_threshold(execute_scores, execute_labels)
    predictions = [score >= threshold for score in execute_scores]
    correct = sum(int(pred == label) for pred, label in zip(predictions, execute_labels, strict=True))
    true_execute = sum(int(label) for label in execute_labels)
    true_positive = sum(int(pred and label) for pred, label in zip(predictions, execute_labels, strict=True))
    stats = SemanticGateStats(
        threshold=threshold,
        train_accuracy=correct / len(execute_labels),
        train_execute_recall=(true_positive / true_execute) if true_execute else 0.0,
        train_execute_rate=sum(int(pred) for pred in predictions) / len(predictions),
    )
    capability_scorer = None
    dense_capability_scorer = None
    clause_localizer = None
    clause_localizer_stats = None
    capability_stats = None
    if learned_capability_inhibition:
        capability_scorer, capability_stats = _train_capability_inhibition_scorer(
            train_examples=train_examples,
            encoder=encoder,
            threshold=threshold,
            contract_aware_inhibition=contract_aware_inhibition,
            feature_names=capability_feature_names,
        )
    if dense_capability_inhibition_mode is not None:
        if dense_capability_inhibition_mode in {
            "learned_clause_localization_interaction",
            "learned_clause_localization_scalar",
            "learned_clause_localization_pair_text",
            "learned_clause_localization_pair_text_mlp",
        }:
            clause_localizer_mode = (
                "pair_text"
                if dense_capability_inhibition_mode in {
                    "learned_clause_localization_pair_text",
                    "learned_clause_localization_pair_text_mlp",
                }
                else "interaction"
            )
            clause_localizer_model_kind = (
                "mlp" if dense_capability_inhibition_mode == "learned_clause_localization_pair_text_mlp" else "linear"
            )
            clause_localizer, clause_localizer_stats = _train_clause_localizer(
                train_examples=train_examples,
                encoder=encoder,
                contract_aware_inhibition=contract_aware_inhibition,
                mode=clause_localizer_mode,
                model_kind=clause_localizer_model_kind,
            )
        dense_capability_scorer, capability_stats = _train_dense_capability_inhibition_scorer(
            train_examples=train_examples,
            encoder=encoder,
            threshold=threshold,
            contract_aware_inhibition=contract_aware_inhibition,
            mode=dense_capability_inhibition_mode,
            clause_localizer=clause_localizer,
        )
        dense_feature_count = len(dense_capability_scorer.feature_means)
    else:
        dense_feature_count = 0
    return (
        SemanticGateAgent(
            name=name,
            encoder=encoder,
            threshold=threshold,
            contract_aware_inhibition=contract_aware_inhibition,
            description_aware_inhibition=description_aware_inhibition,
            capability_scorer=capability_scorer,
            dense_capability_scorer=dense_capability_scorer,
            clause_localizer=clause_localizer,
            capability_require_cue=capability_require_cue,
        ),
        {
            "train_examples": float(len(train_examples)),
            "gate_threshold": stats.threshold,
            "gate_train_accuracy": stats.train_accuracy,
            "gate_train_execute_recall": stats.train_execute_recall,
            "gate_train_execute_rate": stats.train_execute_rate,
            "contract_aware_inhibition": float(contract_aware_inhibition),
            "description_aware_inhibition": float(description_aware_inhibition),
            "learned_capability_inhibition": float(learned_capability_inhibition),
            "capability_require_cue": float(capability_require_cue),
            "capability_feature_count": float(len(capability_feature_names) if learned_capability_inhibition else dense_feature_count),
            "capability_gate_threshold": capability_stats.threshold if capability_stats is not None else 0.0,
            "capability_gate_train_accuracy": capability_stats.train_accuracy if capability_stats is not None else 0.0,
            "capability_gate_train_inhibit_recall": capability_stats.train_inhibit_recall if capability_stats is not None else 0.0,
            "capability_gate_train_inhibit_rate": capability_stats.train_inhibit_rate if capability_stats is not None else 0.0,
            "clause_localizer_threshold": clause_localizer_stats.threshold if clause_localizer_stats is not None else 0.0,
            "clause_localizer_train_accuracy": clause_localizer_stats.train_accuracy if clause_localizer_stats is not None else 0.0,
            "clause_localizer_train_positive_recall": clause_localizer_stats.train_positive_recall if clause_localizer_stats is not None else 0.0,
            "clause_localizer_train_positive_rate": clause_localizer_stats.train_positive_rate if clause_localizer_stats is not None else 0.0,
        },
    )


def train_cross_encoder_semantic_gate_agent(
    *,
    name: str,
    train_examples: Sequence[ViewExample],
    config: EmbeddingPolicyConfig,
    encoder: FrozenEmbeddingEncoder | None,
    contract_aware_inhibition: bool,
) -> tuple[CrossEncoderSemanticGateAgent, dict[str, float]]:
    _require_torch()
    if encoder is None:
        raise ValueError("cross_encoder semantic gate requires an encoder")

    execute_scores = []
    execute_labels = []
    for example in train_examples:
        request_feature = encoder.encode_texts([encoder._with_instruction(serialize_request(example.case.request))])[0].float().cpu()
        active_scores = [
            float(torch.dot(request_feature, encoder.encode_texts([encoder._with_instruction(serialize_tool(tool))])[0].float().cpu()).item())
            for tool in example.schema_view.tools
            if tool.status == "active"
        ]
        execute_scores.append(max(active_scores) if active_scores else float("-inf"))
        execute_labels.append(example.admissible_actions[0].control == ControlTag.EXECUTE)

    threshold = _best_binary_threshold(execute_scores, execute_labels)
    predictions = [score >= threshold for score in execute_scores]
    correct = sum(int(pred == label) for pred, label in zip(predictions, execute_labels, strict=True))
    true_execute = sum(int(label) for label in execute_labels)
    true_positive = sum(int(pred and label) for pred, label in zip(predictions, execute_labels, strict=True))
    gate_stats = SemanticGateStats(
        threshold=threshold,
        train_accuracy=correct / len(execute_labels),
        train_execute_recall=(true_positive / true_execute) if true_execute else 0.0,
        train_execute_rate=sum(int(pred) for pred in predictions) / len(predictions),
    )

    cross_encoder = QwenRerankerCrossEncoder(
        config.cross_encoder_model_path,
        device=encoder.device,
        batch_size=config.cross_encoder_batch_size,
        max_length=config.cross_encoder_max_length,
    )

    clause_scores: list[float] = []
    clause_labels: list[bool] = []
    capability_scores: list[float] = []
    capability_labels: list[bool] = []

    request_cache: dict[str, torch.Tensor] = {}
    text_cache: dict[str, torch.Tensor] = {}

    def request_feature_for(request: str) -> torch.Tensor:
        cached = request_cache.get(request)
        if cached is not None:
            return cached
        feature = encoder.encode_texts([encoder._with_instruction(serialize_request(request))])[0].float().cpu()
        request_cache[request] = feature
        return feature

    def text_feature_for(text: str) -> torch.Tensor:
        cached = text_cache.get(text)
        if cached is not None:
            return cached
        feature = encoder.encode_texts([encoder._with_instruction(text)])[0].float().cpu()
        text_cache[text] = feature
        return feature

    training_rows: list[tuple[str, RenderedTool, bool]] = []
    for example in train_examples:
        request_feature = request_feature_for(example.case.request)
        active_tools = [tool for tool in example.schema_view.tools if tool.status == "active"]
        if not active_tools:
            continue
        active_scores = [
            (float(torch.dot(request_feature, text_feature_for(serialize_tool(tool))).item()), tool)
            for tool in active_tools
        ]
        active_scores.sort(key=lambda item: item[0], reverse=True)
        _, best_active_tool = active_scores[0]
        if contract_aware_inhibition and not _tool_contract_compatible(best_active_tool, example.case.slot_values):
            continue
        execute_expected_tool_ids = {
            action.tool_id
            for action in example.admissible_actions
            if action.control == ControlTag.EXECUTE and action.tool_id is not None
        }
        should_execute = bool(execute_expected_tool_ids) and best_active_tool.canonical_tool_id in execute_expected_tool_ids
        positive_clauses = set(_capability_cue_clauses(best_active_tool)) if not should_execute else set()
        description_clauses = _description_clauses(best_active_tool.description)
        if description_clauses:
            clause_documents = [serialize_clause_localizer_document(best_active_tool, clause) for clause in description_clauses]
            scores = cross_encoder.score_pairs(
                instruction=CROSS_ENCODER_LOCALIZER_INSTRUCTION,
                pairs=[(example.case.request, document) for document in clause_documents],
            )
            clause_scores.extend(scores)
            clause_labels.extend(clause in positive_clauses for clause in description_clauses)
        training_rows.append((example.case.request, best_active_tool, should_execute))

    clause_threshold = _best_binary_threshold(clause_scores, clause_labels)
    clause_predictions = [score >= clause_threshold for score in clause_scores]
    clause_correct = sum(int(pred == label) for pred, label in zip(clause_predictions, clause_labels, strict=True))
    clause_true_positive = sum(int(label) for label in clause_labels)
    clause_predicted_positive = sum(int(pred) for pred in clause_predictions)
    clause_stats = ClauseLocalizerStats(
        threshold=clause_threshold,
        train_accuracy=clause_correct / len(clause_labels),
        train_positive_recall=(
            sum(int(pred and label) for pred, label in zip(clause_predictions, clause_labels, strict=True)) / clause_true_positive
            if clause_true_positive
            else 0.0
        ),
        train_positive_rate=(clause_predicted_positive / len(clause_labels)) if clause_labels else 0.0,
    )
    clause_localizer = CrossEncoderClauseLocalizer(threshold=clause_threshold)

    for request, best_active_tool, should_execute in training_rows:
        selected_clause = _select_cross_encoder_clause(
            request=request,
            tool=best_active_tool,
            cross_encoder=cross_encoder,
            clause_localizer=clause_localizer,
        )
        score = cross_encoder.score_pairs(
            instruction=CROSS_ENCODER_CAPABILITY_INSTRUCTION,
            pairs=[(request, serialize_capability_document(best_active_tool, selected_clause))],
        )[0]
        capability_scores.append(score)
        capability_labels.append(not should_execute)

    capability_threshold = _best_binary_threshold(capability_scores, capability_labels)
    capability_predictions = [score >= capability_threshold for score in capability_scores]
    capability_correct = sum(int(pred == label) for pred, label in zip(capability_predictions, capability_labels, strict=True))
    true_inhibit = sum(int(label) for label in capability_labels)
    true_positive_inhibit = sum(
        int(pred and label) for pred, label in zip(capability_predictions, capability_labels, strict=True)
    )
    capability_stats = LearnedCapabilityScorerStats(
        threshold=capability_threshold,
        train_accuracy=capability_correct / len(capability_labels),
        train_inhibit_recall=(true_positive_inhibit / true_inhibit) if true_inhibit else 0.0,
        train_inhibit_rate=sum(int(pred) for pred in capability_predictions) / len(capability_predictions),
    )
    capability_gate = CrossEncoderCapabilityGate(threshold=capability_threshold)

    return (
        CrossEncoderSemanticGateAgent(
            name=name,
            encoder=encoder,
            threshold=threshold,
            cross_encoder=cross_encoder,
            contract_aware_inhibition=contract_aware_inhibition,
            clause_localizer=clause_localizer,
            capability_gate=capability_gate,
        ),
        {
            "train_examples": float(len(train_examples)),
            "gate_threshold": gate_stats.threshold,
            "gate_train_accuracy": gate_stats.train_accuracy,
            "gate_train_execute_recall": gate_stats.train_execute_recall,
            "gate_train_execute_rate": gate_stats.train_execute_rate,
            "contract_aware_inhibition": float(contract_aware_inhibition),
            "description_aware_inhibition": 0.0,
            "learned_capability_inhibition": 0.0,
            "capability_require_cue": 0.0,
            "capability_feature_count": 0.0,
            "capability_gate_threshold": capability_stats.threshold,
            "capability_gate_train_accuracy": capability_stats.train_accuracy,
            "capability_gate_train_inhibit_recall": capability_stats.train_inhibit_recall,
            "capability_gate_train_inhibit_rate": capability_stats.train_inhibit_rate,
            "clause_localizer_threshold": clause_stats.threshold,
            "clause_localizer_train_accuracy": clause_stats.train_accuracy,
            "clause_localizer_train_positive_recall": clause_stats.train_positive_recall,
            "clause_localizer_train_positive_rate": clause_stats.train_positive_rate,
        },
    )


def train_supervised_cross_encoder_semantic_gate_agent(
    *,
    name: str,
    train_examples: Sequence[ViewExample],
    config: EmbeddingPolicyConfig,
    encoder: FrozenEmbeddingEncoder | None,
    contract_aware_inhibition: bool,
) -> tuple[CrossEncoderSemanticGateAgent, dict[str, float]]:
    _require_torch()
    if encoder is None:
        raise ValueError("cross_encoder semantic gate requires an encoder")

    execute_scores = []
    execute_labels = []
    for example in train_examples:
        request_feature = encoder.encode_texts([encoder._with_instruction(serialize_request(example.case.request))])[0].float().cpu()
        active_scores = [
            float(torch.dot(request_feature, encoder.encode_texts([encoder._with_instruction(serialize_tool(tool))])[0].float().cpu()).item())
            for tool in example.schema_view.tools
            if tool.status == "active"
        ]
        execute_scores.append(max(active_scores) if active_scores else float("-inf"))
        execute_labels.append(example.admissible_actions[0].control == ControlTag.EXECUTE)

    threshold = _best_binary_threshold(execute_scores, execute_labels)
    predictions = [score >= threshold for score in execute_scores]
    correct = sum(int(pred == label) for pred, label in zip(predictions, execute_labels, strict=True))
    true_execute = sum(int(label) for label in execute_labels)
    true_positive = sum(int(pred and label) for pred, label in zip(predictions, execute_labels, strict=True))
    gate_stats = SemanticGateStats(
        threshold=threshold,
        train_accuracy=correct / len(execute_labels),
        train_execute_recall=(true_positive / true_execute) if true_execute else 0.0,
        train_execute_rate=sum(int(pred) for pred in predictions) / len(predictions),
    )

    cross_encoder = QwenRerankerCrossEncoder(
        config.cross_encoder_model_path,
        device=encoder.device,
        batch_size=config.cross_encoder_batch_size,
        max_length=config.cross_encoder_max_length,
    )

    clause_scores: list[float] = []
    clause_labels: list[bool] = []
    training_rows: list[tuple[str, RenderedTool, float, float, bool]] = []

    request_cache: dict[str, torch.Tensor] = {}
    text_cache: dict[str, torch.Tensor] = {}

    def request_feature_for(request: str) -> torch.Tensor:
        cached = request_cache.get(request)
        if cached is not None:
            return cached
        feature = encoder.encode_texts([encoder._with_instruction(serialize_request(request))])[0].float().cpu()
        request_cache[request] = feature
        return feature

    def text_feature_for(text: str) -> torch.Tensor:
        cached = text_cache.get(text)
        if cached is not None:
            return cached
        feature = encoder.encode_texts([encoder._with_instruction(text)])[0].float().cpu()
        text_cache[text] = feature
        return feature

    for example in train_examples:
        request_feature = request_feature_for(example.case.request)
        active_tools = [tool for tool in example.schema_view.tools if tool.status == "active"]
        if not active_tools:
            continue
        active_scores = [
            (float(torch.dot(request_feature, text_feature_for(serialize_tool(tool))).item()), tool)
            for tool in active_tools
        ]
        active_scores.sort(key=lambda item: item[0], reverse=True)
        best_active_score, best_active_tool = active_scores[0]
        second_active_score = active_scores[1][0] if len(active_scores) > 1 else 0.0
        if contract_aware_inhibition and not _tool_contract_compatible(best_active_tool, example.case.slot_values):
            continue
        execute_expected_tool_ids = {
            action.tool_id
            for action in example.admissible_actions
            if action.control == ControlTag.EXECUTE and action.tool_id is not None
        }
        should_execute = bool(execute_expected_tool_ids) and best_active_tool.canonical_tool_id in execute_expected_tool_ids
        positive_clauses = set(_capability_cue_clauses(best_active_tool)) if not should_execute else set()
        description_clauses = _description_clauses(best_active_tool.description)
        if description_clauses:
            clause_documents = [serialize_clause_localizer_document(best_active_tool, clause) for clause in description_clauses]
            scores = cross_encoder.score_pairs(
                instruction=CROSS_ENCODER_LOCALIZER_INSTRUCTION,
                pairs=[(example.case.request, document) for document in clause_documents],
            )
            clause_scores.extend(scores)
            clause_labels.extend(clause in positive_clauses for clause in description_clauses)
        training_rows.append(
            (
                example.case.request,
                best_active_tool,
                best_active_score,
                second_active_score,
                should_execute,
            )
        )

    clause_threshold = _best_binary_threshold(clause_scores, clause_labels)
    clause_predictions = [score >= clause_threshold for score in clause_scores]
    clause_correct = sum(int(pred == label) for pred, label in zip(clause_predictions, clause_labels, strict=True))
    clause_true_positive = sum(int(label) for label in clause_labels)
    clause_predicted_positive = sum(int(pred) for pred in clause_predictions)
    clause_stats = ClauseLocalizerStats(
        threshold=clause_threshold,
        train_accuracy=clause_correct / len(clause_labels),
        train_positive_recall=(
            sum(int(pred and label) for pred, label in zip(clause_predictions, clause_labels, strict=True)) / clause_true_positive
            if clause_true_positive
            else 0.0
        ),
        train_positive_rate=(clause_predicted_positive / len(clause_labels)) if clause_labels else 0.0,
    )
    clause_localizer = CrossEncoderClauseLocalizer(threshold=clause_threshold)

    capability_rows: list[list[float]] = []
    capability_labels: list[bool] = []
    for request, best_active_tool, best_active_score, second_active_score, should_execute in training_rows:
        feature_map, _selected_clause = _cross_encoder_feature_map(
            request=request,
            tool=best_active_tool,
            best_active_score=best_active_score,
            second_active_score=second_active_score,
            cross_encoder=cross_encoder,
            clause_localizer=clause_localizer,
            capability_instruction=CROSS_ENCODER_CAPABILITY_INSTRUCTION,
            feature_names=CROSS_ENCODER_FEATURE_NAMES,
        )
        capability_rows.append([feature_map[name] for name in CROSS_ENCODER_FEATURE_NAMES])
        capability_labels.append(not should_execute)

    capability_scorer, capability_stats = _fit_learned_capability_scorer(
        rows=capability_rows,
        labels=capability_labels,
        feature_names=CROSS_ENCODER_FEATURE_NAMES,
    )
    capability_gate = CrossEncoderCapabilityGate(
        threshold=capability_scorer.threshold,
        instruction=CROSS_ENCODER_CAPABILITY_INSTRUCTION,
    )

    return (
        CrossEncoderSemanticGateAgent(
            name=name,
            encoder=encoder,
            threshold=threshold,
            cross_encoder=cross_encoder,
            contract_aware_inhibition=contract_aware_inhibition,
            clause_localizer=clause_localizer,
            capability_gate=capability_gate,
            capability_scorer=capability_scorer,
        ),
        {
            "train_examples": float(len(train_examples)),
            "gate_threshold": gate_stats.threshold,
            "gate_train_accuracy": gate_stats.train_accuracy,
            "gate_train_execute_recall": gate_stats.train_execute_recall,
            "gate_train_execute_rate": gate_stats.train_execute_rate,
            "contract_aware_inhibition": float(contract_aware_inhibition),
            "description_aware_inhibition": 0.0,
            "learned_capability_inhibition": 1.0,
            "capability_require_cue": 0.0,
            "capability_feature_count": float(len(CROSS_ENCODER_FEATURE_NAMES)),
            "capability_gate_threshold": capability_stats.threshold,
            "capability_gate_train_accuracy": capability_stats.train_accuracy,
            "capability_gate_train_inhibit_recall": capability_stats.train_inhibit_recall,
            "capability_gate_train_inhibit_rate": capability_stats.train_inhibit_rate,
            "clause_localizer_threshold": clause_stats.threshold,
            "clause_localizer_train_accuracy": clause_stats.train_accuracy,
            "clause_localizer_train_positive_recall": clause_stats.train_positive_recall,
            "clause_localizer_train_positive_rate": clause_stats.train_positive_rate,
        },
    )


def train_ranked_cross_encoder_semantic_gate_agent(
    *,
    name: str,
    train_examples: Sequence[ViewExample],
    config: EmbeddingPolicyConfig,
    encoder: FrozenEmbeddingEncoder | None,
    contract_aware_inhibition: bool,
) -> tuple[CrossEncoderSemanticGateAgent, dict[str, float]]:
    _require_torch()
    if encoder is None:
        raise ValueError("cross_encoder semantic gate requires an encoder")

    execute_scores = []
    execute_labels = []
    for example in train_examples:
        request_feature = encoder.encode_texts([encoder._with_instruction(serialize_request(example.case.request))])[0].float().cpu()
        active_scores = [
            float(torch.dot(request_feature, encoder.encode_texts([encoder._with_instruction(serialize_tool(tool))])[0].float().cpu()).item())
            for tool in example.schema_view.tools
            if tool.status == "active"
        ]
        execute_scores.append(max(active_scores) if active_scores else float("-inf"))
        execute_labels.append(example.admissible_actions[0].control == ControlTag.EXECUTE)

    threshold = _best_binary_threshold(execute_scores, execute_labels)
    predictions = [score >= threshold for score in execute_scores]
    correct = sum(int(pred == label) for pred, label in zip(predictions, execute_labels, strict=True))
    true_execute = sum(int(label) for label in execute_labels)
    true_positive = sum(int(pred and label) for pred, label in zip(predictions, execute_labels, strict=True))
    gate_stats = SemanticGateStats(
        threshold=threshold,
        train_accuracy=correct / len(execute_labels),
        train_execute_recall=(true_positive / true_execute) if true_execute else 0.0,
        train_execute_rate=sum(int(pred) for pred in predictions) / len(predictions),
    )

    cross_encoder = QwenRerankerCrossEncoder(
        config.cross_encoder_model_path,
        device=encoder.device,
        batch_size=config.cross_encoder_batch_size,
        max_length=config.cross_encoder_max_length,
    )

    training_rows: list[tuple[str, RenderedTool, float, float, bool]] = []
    top_hit_total = 0
    top_hit_correct = 0
    pairwise_total = 0
    pairwise_correct = 0

    request_cache: dict[str, torch.Tensor] = {}
    text_cache: dict[str, torch.Tensor] = {}

    def request_feature_for(request: str) -> torch.Tensor:
        cached = request_cache.get(request)
        if cached is not None:
            return cached
        feature = encoder.encode_texts([encoder._with_instruction(serialize_request(request))])[0].float().cpu()
        request_cache[request] = feature
        return feature

    def text_feature_for(text: str) -> torch.Tensor:
        cached = text_cache.get(text)
        if cached is not None:
            return cached
        feature = encoder.encode_texts([encoder._with_instruction(text)])[0].float().cpu()
        text_cache[text] = feature
        return feature

    for example in train_examples:
        request_feature = request_feature_for(example.case.request)
        active_tools = [tool for tool in example.schema_view.tools if tool.status == "active"]
        if not active_tools:
            continue
        active_scores = [
            (float(torch.dot(request_feature, text_feature_for(serialize_tool(tool))).item()), tool)
            for tool in active_tools
        ]
        active_scores.sort(key=lambda item: item[0], reverse=True)
        best_active_score, best_active_tool = active_scores[0]
        second_active_score = active_scores[1][0] if len(active_scores) > 1 else 0.0
        if contract_aware_inhibition and not _tool_contract_compatible(best_active_tool, example.case.slot_values):
            continue
        execute_expected_tool_ids = {
            action.tool_id
            for action in example.admissible_actions
            if action.control == ControlTag.EXECUTE and action.tool_id is not None
        }
        should_execute = bool(execute_expected_tool_ids) and best_active_tool.canonical_tool_id in execute_expected_tool_ids
        positive_clauses = set(_capability_cue_clauses(best_active_tool)) if not should_execute else set()
        description_clauses, clause_scores, best_index = _cross_encoder_clause_ranking(
            request=example.case.request,
            tool=best_active_tool,
            cross_encoder=cross_encoder,
            instruction=CROSS_ENCODER_LOCALIZER_INSTRUCTION,
        )
        if description_clauses and positive_clauses:
            top_hit_total += 1
            if description_clauses[best_index] in positive_clauses:
                top_hit_correct += 1
            positive_scores = [
                score
                for clause, score in zip(description_clauses, clause_scores, strict=True)
                if clause in positive_clauses
            ]
            negative_scores = [
                score
                for clause, score in zip(description_clauses, clause_scores, strict=True)
                if clause not in positive_clauses
            ]
            for positive_score in positive_scores:
                for negative_score in negative_scores:
                    pairwise_total += 1
                    if positive_score > negative_score:
                        pairwise_correct += 1
        training_rows.append(
            (
                example.case.request,
                best_active_tool,
                best_active_score,
                second_active_score,
                should_execute,
            )
        )

    clause_stats = ClauseLocalizerStats(
        threshold=0.0,
        train_accuracy=(top_hit_correct / top_hit_total) if top_hit_total else 0.0,
        train_positive_recall=(pairwise_correct / pairwise_total) if pairwise_total else 0.0,
        train_positive_rate=1.0,
    )
    clause_localizer = CrossEncoderClauseLocalizer(threshold=0.0, selection_mode="top")

    capability_rows: list[list[float]] = []
    capability_labels: list[bool] = []
    for request, best_active_tool, best_active_score, second_active_score, should_execute in training_rows:
        feature_map, _selected_clause = _cross_encoder_feature_map(
            request=request,
            tool=best_active_tool,
            best_active_score=best_active_score,
            second_active_score=second_active_score,
            cross_encoder=cross_encoder,
            clause_localizer=clause_localizer,
            capability_instruction=CROSS_ENCODER_CAPABILITY_INSTRUCTION,
            feature_names=CROSS_ENCODER_FEATURE_NAMES,
        )
        capability_rows.append([feature_map[name] for name in CROSS_ENCODER_FEATURE_NAMES])
        capability_labels.append(not should_execute)

    capability_scorer, capability_stats = _fit_learned_capability_scorer(
        rows=capability_rows,
        labels=capability_labels,
        feature_names=CROSS_ENCODER_FEATURE_NAMES,
    )
    capability_gate = CrossEncoderCapabilityGate(
        threshold=capability_scorer.threshold,
        instruction=CROSS_ENCODER_CAPABILITY_INSTRUCTION,
    )

    return (
        CrossEncoderSemanticGateAgent(
            name=name,
            encoder=encoder,
            threshold=threshold,
            cross_encoder=cross_encoder,
            contract_aware_inhibition=contract_aware_inhibition,
            clause_localizer=clause_localizer,
            capability_gate=capability_gate,
            capability_scorer=capability_scorer,
        ),
        {
            "train_examples": float(len(train_examples)),
            "gate_threshold": gate_stats.threshold,
            "gate_train_accuracy": gate_stats.train_accuracy,
            "gate_train_execute_recall": gate_stats.train_execute_recall,
            "gate_train_execute_rate": gate_stats.train_execute_rate,
            "contract_aware_inhibition": float(contract_aware_inhibition),
            "description_aware_inhibition": 0.0,
            "learned_capability_inhibition": 1.0,
            "capability_require_cue": 0.0,
            "capability_feature_count": float(len(CROSS_ENCODER_FEATURE_NAMES)),
            "capability_gate_threshold": capability_stats.threshold,
            "capability_gate_train_accuracy": capability_stats.train_accuracy,
            "capability_gate_train_inhibit_recall": capability_stats.train_inhibit_recall,
            "capability_gate_train_inhibit_rate": capability_stats.train_inhibit_rate,
            "clause_localizer_threshold": clause_stats.threshold,
            "clause_localizer_train_accuracy": clause_stats.train_accuracy,
            "clause_localizer_train_positive_recall": clause_stats.train_positive_recall,
            "clause_localizer_train_positive_rate": clause_stats.train_positive_rate,
        },
    )


def train_pairwise_cross_encoder_semantic_gate_agent(
    *,
    name: str,
    train_examples: Sequence[ViewExample],
    config: EmbeddingPolicyConfig,
    encoder: FrozenEmbeddingEncoder | None,
    contract_aware_inhibition: bool,
) -> tuple[CrossEncoderSemanticGateAgent, dict[str, float]]:
    _require_torch()
    if encoder is None:
        raise ValueError("cross_encoder semantic gate requires an encoder")

    execute_scores = []
    execute_labels = []
    for example in train_examples:
        request_feature = encoder.encode_texts([encoder._with_instruction(serialize_request(example.case.request))])[0].float().cpu()
        active_scores = [
            float(torch.dot(request_feature, encoder.encode_texts([encoder._with_instruction(serialize_tool(tool))])[0].float().cpu()).item())
            for tool in example.schema_view.tools
            if tool.status == "active"
        ]
        execute_scores.append(max(active_scores) if active_scores else float("-inf"))
        execute_labels.append(example.admissible_actions[0].control == ControlTag.EXECUTE)

    threshold = _best_binary_threshold(execute_scores, execute_labels)
    predictions = [score >= threshold for score in execute_scores]
    correct = sum(int(pred == label) for pred, label in zip(predictions, execute_labels, strict=True))
    true_execute = sum(int(label) for label in execute_labels)
    true_positive = sum(int(pred and label) for pred, label in zip(predictions, execute_labels, strict=True))
    gate_stats = SemanticGateStats(
        threshold=threshold,
        train_accuracy=correct / len(execute_labels),
        train_execute_recall=(true_positive / true_execute) if true_execute else 0.0,
        train_execute_rate=sum(int(pred) for pred in predictions) / len(predictions),
    )

    cross_encoder = QwenRerankerCrossEncoder(
        config.cross_encoder_model_path,
        device=encoder.device,
        batch_size=config.cross_encoder_batch_size,
        max_length=config.cross_encoder_max_length,
    )

    training_rows: list[tuple[str, RenderedTool, float, float, bool]] = []
    feature_maps_by_example: list[list[dict[str, float]]] = []
    labels_by_example: list[list[bool]] = []

    request_cache: dict[str, torch.Tensor] = {}
    text_cache: dict[str, torch.Tensor] = {}

    def request_feature_for(request: str) -> torch.Tensor:
        cached = request_cache.get(request)
        if cached is not None:
            return cached
        feature = encoder.encode_texts([encoder._with_instruction(serialize_request(request))])[0].float().cpu()
        request_cache[request] = feature
        return feature

    def text_feature_for(text: str) -> torch.Tensor:
        cached = text_cache.get(text)
        if cached is not None:
            return cached
        feature = encoder.encode_texts([encoder._with_instruction(text)])[0].float().cpu()
        text_cache[text] = feature
        return feature

    for example in train_examples:
        request_feature = request_feature_for(example.case.request)
        active_tools = [tool for tool in example.schema_view.tools if tool.status == "active"]
        if not active_tools:
            continue
        active_scores = [
            (float(torch.dot(request_feature, text_feature_for(serialize_tool(tool))).item()), tool)
            for tool in active_tools
        ]
        active_scores.sort(key=lambda item: item[0], reverse=True)
        best_active_score, best_active_tool = active_scores[0]
        second_active_score = active_scores[1][0] if len(active_scores) > 1 else 0.0
        if contract_aware_inhibition and not _tool_contract_compatible(best_active_tool, example.case.slot_values):
            continue
        execute_expected_tool_ids = {
            action.tool_id
            for action in example.admissible_actions
            if action.control == ControlTag.EXECUTE and action.tool_id is not None
        }
        should_execute = bool(execute_expected_tool_ids) and best_active_tool.canonical_tool_id in execute_expected_tool_ids
        positive_clauses = set(_capability_cue_clauses(best_active_tool)) if not should_execute else set()
        description_clauses = _description_clauses(best_active_tool.description)
        if description_clauses and positive_clauses:
            full_capability_score = cross_encoder.score_pairs(
                instruction=CROSS_ENCODER_CAPABILITY_INSTRUCTION,
                pairs=[(example.case.request, serialize_capability_document(best_active_tool, None))],
            )[0]
            clause_feature_maps = [
                _cross_encoder_clause_feature_map(
                    request=example.case.request,
                    tool=best_active_tool,
                    clause=clause,
                    cross_encoder=cross_encoder,
                    localizer_instruction=CROSS_ENCODER_LOCALIZER_INSTRUCTION,
                    capability_instruction=CROSS_ENCODER_CAPABILITY_INSTRUCTION,
                    full_capability_score=full_capability_score,
                    feature_names=CROSS_ENCODER_CLAUSE_FEATURE_NAMES,
                )
                for clause in description_clauses
            ]
            clause_labels = [clause in positive_clauses for clause in description_clauses]
            if any(clause_labels) and not all(clause_labels):
                feature_maps_by_example.append(clause_feature_maps)
                labels_by_example.append(clause_labels)
        training_rows.append(
            (
                example.case.request,
                best_active_tool,
                best_active_score,
                second_active_score,
                should_execute,
            )
        )

    clause_ranker, clause_stats = _fit_pairwise_clause_ranker(
        feature_maps_by_example=feature_maps_by_example,
        labels_by_example=labels_by_example,
        feature_names=CROSS_ENCODER_CLAUSE_FEATURE_NAMES,
    )
    clause_localizer = CrossEncoderClauseLocalizer(
        threshold=0.0,
        selection_mode="learned",
        ranker=clause_ranker,
    )

    capability_rows: list[list[float]] = []
    capability_labels: list[bool] = []
    for request, best_active_tool, best_active_score, second_active_score, should_execute in training_rows:
        feature_map, _selected_clause = _cross_encoder_feature_map(
            request=request,
            tool=best_active_tool,
            best_active_score=best_active_score,
            second_active_score=second_active_score,
            cross_encoder=cross_encoder,
            clause_localizer=clause_localizer,
            capability_instruction=CROSS_ENCODER_CAPABILITY_INSTRUCTION,
            feature_names=CROSS_ENCODER_FEATURE_NAMES,
        )
        capability_rows.append([feature_map[name] for name in CROSS_ENCODER_FEATURE_NAMES])
        capability_labels.append(not should_execute)

    capability_scorer, capability_stats = _fit_learned_capability_scorer(
        rows=capability_rows,
        labels=capability_labels,
        feature_names=CROSS_ENCODER_FEATURE_NAMES,
    )
    capability_gate = CrossEncoderCapabilityGate(
        threshold=capability_scorer.threshold,
        instruction=CROSS_ENCODER_CAPABILITY_INSTRUCTION,
    )

    return (
        CrossEncoderSemanticGateAgent(
            name=name,
            encoder=encoder,
            threshold=threshold,
            cross_encoder=cross_encoder,
            contract_aware_inhibition=contract_aware_inhibition,
            clause_localizer=clause_localizer,
            capability_gate=capability_gate,
            capability_scorer=capability_scorer,
        ),
        {
            "train_examples": float(len(train_examples)),
            "gate_threshold": gate_stats.threshold,
            "gate_train_accuracy": gate_stats.train_accuracy,
            "gate_train_execute_recall": gate_stats.train_execute_recall,
            "gate_train_execute_rate": gate_stats.train_execute_rate,
            "contract_aware_inhibition": float(contract_aware_inhibition),
            "description_aware_inhibition": 0.0,
            "learned_capability_inhibition": 1.0,
            "capability_require_cue": 0.0,
            "capability_feature_count": float(len(CROSS_ENCODER_FEATURE_NAMES)),
            "capability_gate_threshold": capability_stats.threshold,
            "capability_gate_train_accuracy": capability_stats.train_accuracy,
            "capability_gate_train_inhibit_recall": capability_stats.train_inhibit_recall,
            "capability_gate_train_inhibit_rate": capability_stats.train_inhibit_rate,
            "clause_localizer_threshold": clause_stats.threshold,
            "clause_localizer_train_accuracy": clause_stats.train_accuracy,
            "clause_localizer_train_positive_recall": clause_stats.train_positive_recall,
            "clause_localizer_train_positive_rate": clause_stats.train_positive_rate,
        },
    )


def train_listwise_cross_encoder_semantic_gate_agent(
    *,
    name: str,
    train_examples: Sequence[ViewExample],
    config: EmbeddingPolicyConfig,
    encoder: FrozenEmbeddingEncoder | None,
    contract_aware_inhibition: bool,
) -> tuple[CrossEncoderSemanticGateAgent, dict[str, float]]:
    _require_torch()
    if encoder is None:
        raise ValueError("cross_encoder semantic gate requires an encoder")

    execute_scores = []
    execute_labels = []
    for example in train_examples:
        request_feature = encoder.encode_texts([encoder._with_instruction(serialize_request(example.case.request))])[0].float().cpu()
        active_scores = [
            float(torch.dot(request_feature, encoder.encode_texts([encoder._with_instruction(serialize_tool(tool))])[0].float().cpu()).item())
            for tool in example.schema_view.tools
            if tool.status == "active"
        ]
        execute_scores.append(max(active_scores) if active_scores else float("-inf"))
        execute_labels.append(example.admissible_actions[0].control == ControlTag.EXECUTE)

    threshold = _best_binary_threshold(execute_scores, execute_labels)
    predictions = [score >= threshold for score in execute_scores]
    correct = sum(int(pred == label) for pred, label in zip(predictions, execute_labels, strict=True))
    true_execute = sum(int(label) for label in execute_labels)
    true_positive = sum(int(pred and label) for pred, label in zip(predictions, execute_labels, strict=True))
    gate_stats = SemanticGateStats(
        threshold=threshold,
        train_accuracy=correct / len(execute_labels),
        train_execute_recall=(true_positive / true_execute) if true_execute else 0.0,
        train_execute_rate=sum(int(pred) for pred in predictions) / len(predictions),
    )

    cross_encoder = QwenRerankerCrossEncoder(
        config.cross_encoder_model_path,
        device=encoder.device,
        batch_size=config.cross_encoder_batch_size,
        max_length=config.cross_encoder_max_length,
    )

    training_rows: list[tuple[str, RenderedTool, float, float, bool]] = []
    feature_maps_by_example: list[list[dict[str, float]]] = []
    labels_by_example: list[list[bool]] = []

    request_cache: dict[str, torch.Tensor] = {}
    text_cache: dict[str, torch.Tensor] = {}

    def request_feature_for(request: str) -> torch.Tensor:
        cached = request_cache.get(request)
        if cached is not None:
            return cached
        feature = encoder.encode_texts([encoder._with_instruction(serialize_request(request))])[0].float().cpu()
        request_cache[request] = feature
        return feature

    def text_feature_for(text: str) -> torch.Tensor:
        cached = text_cache.get(text)
        if cached is not None:
            return cached
        feature = encoder.encode_texts([encoder._with_instruction(text)])[0].float().cpu()
        text_cache[text] = feature
        return feature

    for example in train_examples:
        request_feature = request_feature_for(example.case.request)
        active_tools = [tool for tool in example.schema_view.tools if tool.status == "active"]
        if not active_tools:
            continue
        active_scores = [
            (float(torch.dot(request_feature, text_feature_for(serialize_tool(tool))).item()), tool)
            for tool in active_tools
        ]
        active_scores.sort(key=lambda item: item[0], reverse=True)
        best_active_score, best_active_tool = active_scores[0]
        second_active_score = active_scores[1][0] if len(active_scores) > 1 else 0.0
        if contract_aware_inhibition and not _tool_contract_compatible(best_active_tool, example.case.slot_values):
            continue
        execute_expected_tool_ids = {
            action.tool_id
            for action in example.admissible_actions
            if action.control == ControlTag.EXECUTE and action.tool_id is not None
        }
        should_execute = bool(execute_expected_tool_ids) and best_active_tool.canonical_tool_id in execute_expected_tool_ids
        positive_clauses = set(_capability_cue_clauses(best_active_tool)) if not should_execute else set()
        description_clauses = _description_clauses(best_active_tool.description)
        if description_clauses and positive_clauses:
            full_capability_score = cross_encoder.score_pairs(
                instruction=CROSS_ENCODER_CAPABILITY_INSTRUCTION,
                pairs=[(example.case.request, serialize_capability_document(best_active_tool, None))],
            )[0]
            clause_feature_maps = [
                _cross_encoder_clause_feature_map(
                    request=example.case.request,
                    tool=best_active_tool,
                    clause=clause,
                    cross_encoder=cross_encoder,
                    localizer_instruction=CROSS_ENCODER_LOCALIZER_INSTRUCTION,
                    capability_instruction=CROSS_ENCODER_CAPABILITY_INSTRUCTION,
                    full_capability_score=full_capability_score,
                    feature_names=CROSS_ENCODER_CLAUSE_FEATURE_NAMES,
                )
                for clause in description_clauses
            ]
            clause_labels = [clause in positive_clauses for clause in description_clauses]
            if any(clause_labels) and not all(clause_labels):
                feature_maps_by_example.append(clause_feature_maps)
                labels_by_example.append(clause_labels)
        training_rows.append(
            (
                example.case.request,
                best_active_tool,
                best_active_score,
                second_active_score,
                should_execute,
            )
        )

    clause_ranker, clause_stats = _fit_listwise_clause_ranker(
        feature_maps_by_example=feature_maps_by_example,
        labels_by_example=labels_by_example,
        feature_names=CROSS_ENCODER_CLAUSE_FEATURE_NAMES,
    )
    clause_localizer = CrossEncoderClauseLocalizer(
        threshold=0.0,
        selection_mode="learned",
        ranker=clause_ranker,
    )

    capability_rows: list[list[float]] = []
    capability_labels: list[bool] = []
    for request, best_active_tool, best_active_score, second_active_score, should_execute in training_rows:
        feature_map, _selected_clause = _cross_encoder_feature_map(
            request=request,
            tool=best_active_tool,
            best_active_score=best_active_score,
            second_active_score=second_active_score,
            cross_encoder=cross_encoder,
            clause_localizer=clause_localizer,
            capability_instruction=CROSS_ENCODER_CAPABILITY_INSTRUCTION,
            feature_names=CROSS_ENCODER_FEATURE_NAMES,
        )
        capability_rows.append([feature_map[name] for name in CROSS_ENCODER_FEATURE_NAMES])
        capability_labels.append(not should_execute)

    capability_scorer, capability_stats = _fit_learned_capability_scorer(
        rows=capability_rows,
        labels=capability_labels,
        feature_names=CROSS_ENCODER_FEATURE_NAMES,
    )
    capability_gate = CrossEncoderCapabilityGate(
        threshold=capability_scorer.threshold,
        instruction=CROSS_ENCODER_CAPABILITY_INSTRUCTION,
    )

    return (
        CrossEncoderSemanticGateAgent(
            name=name,
            encoder=encoder,
            threshold=threshold,
            cross_encoder=cross_encoder,
            contract_aware_inhibition=contract_aware_inhibition,
            clause_localizer=clause_localizer,
            capability_gate=capability_gate,
            capability_scorer=capability_scorer,
        ),
        {
            "train_examples": float(len(train_examples)),
            "gate_threshold": gate_stats.threshold,
            "gate_train_accuracy": gate_stats.train_accuracy,
            "gate_train_execute_recall": gate_stats.train_execute_recall,
            "gate_train_execute_rate": gate_stats.train_execute_rate,
            "contract_aware_inhibition": float(contract_aware_inhibition),
            "description_aware_inhibition": 0.0,
            "learned_capability_inhibition": 1.0,
            "capability_require_cue": 0.0,
            "capability_feature_count": float(len(CROSS_ENCODER_FEATURE_NAMES)),
            "capability_gate_threshold": capability_stats.threshold,
            "capability_gate_train_accuracy": capability_stats.train_accuracy,
            "capability_gate_train_inhibit_recall": capability_stats.train_inhibit_recall,
            "capability_gate_train_inhibit_rate": capability_stats.train_inhibit_rate,
            "clause_localizer_threshold": clause_stats.threshold,
            "clause_localizer_train_accuracy": clause_stats.train_accuracy,
            "clause_localizer_train_positive_recall": clause_stats.train_positive_recall,
            "clause_localizer_train_positive_rate": clause_stats.train_positive_rate,
        },
    )


def _prepare_cross_encoder_capability_training_rows(
    *,
    train_examples: Sequence[ViewExample],
    encoder: FrozenEmbeddingEncoder,
    contract_aware_inhibition: bool,
) -> tuple[SemanticGateStats, list[CrossEncoderCapabilityTrainingRow]]:
    execute_scores = []
    execute_labels = []
    for example in train_examples:
        request_feature = encoder.encode_texts([encoder._with_instruction(serialize_request(example.case.request))])[0].float().cpu()
        active_scores = [
            float(torch.dot(request_feature, encoder.encode_texts([encoder._with_instruction(serialize_tool(tool))])[0].float().cpu()).item())
            for tool in example.schema_view.tools
            if tool.status == "active"
        ]
        execute_scores.append(max(active_scores) if active_scores else float("-inf"))
        execute_labels.append(example.admissible_actions[0].control == ControlTag.EXECUTE)

    threshold = _best_binary_threshold(execute_scores, execute_labels)
    predictions = [score >= threshold for score in execute_scores]
    correct = sum(int(pred == label) for pred, label in zip(predictions, execute_labels, strict=True))
    true_execute = sum(int(label) for label in execute_labels)
    true_positive = sum(int(pred and label) for pred, label in zip(predictions, execute_labels, strict=True))
    gate_stats = SemanticGateStats(
        threshold=threshold,
        train_accuracy=correct / len(execute_labels),
        train_execute_recall=(true_positive / true_execute) if true_execute else 0.0,
        train_execute_rate=sum(int(pred) for pred in predictions) / len(predictions),
    )

    request_cache: dict[str, torch.Tensor] = {}
    text_cache: dict[str, torch.Tensor] = {}

    def request_feature_for(request: str) -> torch.Tensor:
        cached = request_cache.get(request)
        if cached is not None:
            return cached
        feature = encoder.encode_texts([encoder._with_instruction(serialize_request(request))])[0].float().cpu()
        request_cache[request] = feature
        return feature

    def text_feature_for(text: str) -> torch.Tensor:
        cached = text_cache.get(text)
        if cached is not None:
            return cached
        feature = encoder.encode_texts([encoder._with_instruction(text)])[0].float().cpu()
        text_cache[text] = feature
        return feature

    training_rows: list[CrossEncoderCapabilityTrainingRow] = []
    for example in train_examples:
        request_feature = request_feature_for(example.case.request)
        active_tools = [tool for tool in example.schema_view.tools if tool.status == "active"]
        if not active_tools:
            continue
        active_scores = [
            (float(torch.dot(request_feature, text_feature_for(serialize_tool(tool))).item()), tool)
            for tool in active_tools
        ]
        active_scores.sort(key=lambda item: item[0], reverse=True)
        _, best_active_tool = active_scores[0]
        if contract_aware_inhibition and not _tool_contract_compatible(best_active_tool, example.case.slot_values):
            continue
        execute_expected_tool_ids = {
            action.tool_id
            for action in example.admissible_actions
            if action.control == ControlTag.EXECUTE and action.tool_id is not None
        }
        should_execute = bool(execute_expected_tool_ids) and best_active_tool.canonical_tool_id in execute_expected_tool_ids
        training_rows.append(
            CrossEncoderCapabilityTrainingRow(
                example=example,
                best_active_tool=best_active_tool,
                should_execute=should_execute,
            )
        )

    return gate_stats, training_rows


def train_finetuned_cross_encoder_capability_gate_agent(
    *,
    name: str,
    train_examples: Sequence[ViewExample],
    config: EmbeddingPolicyConfig,
    encoder: FrozenEmbeddingEncoder | None,
    contract_aware_inhibition: bool,
) -> tuple[CrossEncoderSemanticGateAgent, dict[str, float]]:
    _require_torch()
    if encoder is None:
        raise ValueError("cross_encoder semantic gate requires an encoder")

    gate_stats, training_rows = _prepare_cross_encoder_capability_training_rows(
        train_examples=train_examples,
        encoder=encoder,
        contract_aware_inhibition=contract_aware_inhibition,
    )
    capability_pairs: list[tuple[str, str]] = []
    capability_labels: list[bool] = []
    for row in training_rows:
        capability_pairs.append(
            (
                row.example.case.request,
                serialize_capability_document(row.best_active_tool, None),
            )
        )
        capability_labels.append(not row.should_execute)

    cross_encoder, capability_stats, tuned_param_count = _finetune_cross_encoder_binary_classifier(
        model_path=config.cross_encoder_model_path,
        device=encoder.device,
        batch_size=config.cross_encoder_batch_size,
        max_length=config.cross_encoder_max_length,
        instruction=CROSS_ENCODER_CAPABILITY_INSTRUCTION,
        pairs=capability_pairs,
        labels=capability_labels,
        sample_weights=None,
        epochs=config.cross_encoder_finetune_epochs,
        learning_rate=config.cross_encoder_finetune_learning_rate,
        weight_decay=config.cross_encoder_finetune_weight_decay,
        tune_last_n_layers=config.cross_encoder_tune_last_n_layers,
        seed=config.seed,
    )
    capability_gate = CrossEncoderCapabilityGate(
        threshold=capability_stats.threshold,
        instruction=CROSS_ENCODER_CAPABILITY_INSTRUCTION,
    )
    disabled_localizer = CrossEncoderClauseLocalizer(threshold=1.1)

    return (
        CrossEncoderSemanticGateAgent(
            name=name,
            encoder=encoder,
            threshold=threshold,
            cross_encoder=cross_encoder,
            contract_aware_inhibition=contract_aware_inhibition,
            clause_localizer=disabled_localizer,
            capability_gate=capability_gate,
        ),
        {
            "train_examples": float(len(train_examples)),
            "gate_threshold": gate_stats.threshold,
            "gate_train_accuracy": gate_stats.train_accuracy,
            "gate_train_execute_recall": gate_stats.train_execute_recall,
            "gate_train_execute_rate": gate_stats.train_execute_rate,
            "contract_aware_inhibition": float(contract_aware_inhibition),
            "description_aware_inhibition": 0.0,
            "learned_capability_inhibition": 1.0,
            "capability_require_cue": 0.0,
            "capability_feature_count": 0.0,
            "capability_gate_threshold": capability_stats.threshold,
            "capability_gate_train_accuracy": capability_stats.train_accuracy,
            "capability_gate_train_inhibit_recall": capability_stats.train_inhibit_recall,
            "capability_gate_train_inhibit_rate": capability_stats.train_inhibit_rate,
            "clause_localizer_threshold": disabled_localizer.threshold,
            "clause_localizer_train_accuracy": 0.0,
            "clause_localizer_train_positive_recall": 0.0,
            "clause_localizer_train_positive_rate": 0.0,
            "cross_encoder_tunable_param_count": float(tuned_param_count),
            "cross_encoder_finetune_epochs": float(config.cross_encoder_finetune_epochs),
            "cross_encoder_tune_last_n_layers": float(config.cross_encoder_tune_last_n_layers),
        },
    )


def train_multitask_cross_encoder_capability_gate_agent(
    *,
    name: str,
    train_examples: Sequence[ViewExample],
    config: EmbeddingPolicyConfig,
    encoder: FrozenEmbeddingEncoder | None,
    contract_aware_inhibition: bool,
) -> tuple[CrossEncoderSemanticGateAgent, dict[str, float]]:
    _require_torch()
    if encoder is None:
        raise ValueError("cross_encoder semantic gate requires an encoder")

    gate_stats, training_rows = _prepare_cross_encoder_capability_training_rows(
        train_examples=train_examples,
        encoder=encoder,
        contract_aware_inhibition=contract_aware_inhibition,
    )
    clause_pairs: list[tuple[str, str]] = []
    clause_labels: list[bool] = []
    capability_pairs: list[tuple[str, str]] = []
    capability_labels: list[bool] = []

    for row in training_rows:
        positive_clauses = set(_capability_cue_clauses(row.best_active_tool)) if not row.should_execute else set()
        description_clauses = _description_clauses(row.best_active_tool.description)
        if description_clauses and positive_clauses:
            for clause in description_clauses:
                clause_pairs.append((row.example.case.request, serialize_clause_localizer_document(row.best_active_tool, clause)))
                clause_labels.append(clause in positive_clauses)
        capability_pairs.append(
            (
                row.example.case.request,
                serialize_capability_document(row.best_active_tool, None),
            )
        )
        capability_labels.append(not row.should_execute)

    cross_encoder, task_stats, tuned_param_count = _finetune_cross_encoder_multitask_binary_classifier(
        model_path=config.cross_encoder_model_path,
        device=encoder.device,
        batch_size=config.cross_encoder_finetune_batch_size,
        max_length=config.cross_encoder_max_length,
        tasks=(
            CrossEncoderBinaryTaskSpec(
                name="localizer",
                instruction=CROSS_ENCODER_LOCALIZER_INSTRUCTION,
                pairs=tuple(clause_pairs),
                labels=tuple(clause_labels),
            ),
            CrossEncoderBinaryTaskSpec(
                name="capability",
                instruction=CROSS_ENCODER_CAPABILITY_INSTRUCTION,
                pairs=tuple(capability_pairs),
                labels=tuple(capability_labels),
            ),
        ),
        epochs=config.cross_encoder_finetune_epochs,
        learning_rate=config.cross_encoder_finetune_learning_rate,
        weight_decay=config.cross_encoder_finetune_weight_decay,
        tune_last_n_layers=config.cross_encoder_tune_last_n_layers,
        seed=config.seed,
    )

    clause_scores = cross_encoder.score_pairs(
        instruction=CROSS_ENCODER_LOCALIZER_INSTRUCTION,
        pairs=clause_pairs,
    )
    clause_threshold = _best_binary_threshold(clause_scores, clause_labels)
    clause_predictions = [score >= clause_threshold for score in clause_scores]
    clause_correct = sum(int(pred == label) for pred, label in zip(clause_predictions, clause_labels, strict=True))
    clause_true_positive = sum(int(label) for label in clause_labels)
    clause_predicted_positive = sum(int(pred) for pred in clause_predictions)
    clause_stats = ClauseLocalizerStats(
        threshold=clause_threshold,
        train_accuracy=(clause_correct / len(clause_labels)) if clause_labels else 0.0,
        train_positive_recall=(
            sum(int(pred and label) for pred, label in zip(clause_predictions, clause_labels, strict=True)) / clause_true_positive
            if clause_true_positive
            else 0.0
        ),
        train_positive_rate=(clause_predicted_positive / len(clause_labels)) if clause_labels else 0.0,
    )
    clause_localizer = CrossEncoderClauseLocalizer(threshold=clause_threshold)
    capability_gate = CrossEncoderCapabilityGate(
        threshold=task_stats["capability"].threshold,
        instruction=CROSS_ENCODER_CAPABILITY_INSTRUCTION,
    )

    return (
        CrossEncoderSemanticGateAgent(
            name=name,
            encoder=encoder,
            threshold=threshold,
            cross_encoder=cross_encoder,
            contract_aware_inhibition=contract_aware_inhibition,
            clause_localizer=clause_localizer,
            capability_gate=capability_gate,
        ),
        {
            "train_examples": float(len(train_examples)),
            "gate_threshold": gate_stats.threshold,
            "gate_train_accuracy": gate_stats.train_accuracy,
            "gate_train_execute_recall": gate_stats.train_execute_recall,
            "gate_train_execute_rate": gate_stats.train_execute_rate,
            "contract_aware_inhibition": float(contract_aware_inhibition),
            "description_aware_inhibition": 0.0,
            "learned_capability_inhibition": 1.0,
            "capability_require_cue": 0.0,
            "capability_feature_count": 0.0,
            "capability_gate_threshold": task_stats["capability"].threshold,
            "capability_gate_train_accuracy": task_stats["capability"].train_accuracy,
            "capability_gate_train_inhibit_recall": task_stats["capability"].train_inhibit_recall,
            "capability_gate_train_inhibit_rate": task_stats["capability"].train_inhibit_rate,
            "clause_localizer_threshold": clause_stats.threshold,
            "clause_localizer_train_accuracy": clause_stats.train_accuracy,
            "clause_localizer_train_positive_recall": clause_stats.train_positive_recall,
            "clause_localizer_train_positive_rate": clause_stats.train_positive_rate,
            "cross_encoder_tunable_param_count": float(tuned_param_count),
            "cross_encoder_finetune_epochs": float(config.cross_encoder_finetune_epochs),
            "cross_encoder_tune_last_n_layers": float(config.cross_encoder_tune_last_n_layers),
            "cross_encoder_multitask_capability_examples": float(len(capability_pairs)),
            "cross_encoder_multitask_clause_examples": float(len(clause_pairs)),
        },
    )


def _build_class_balanced_hard_negative_weights(
    *,
    labels: Sequence[bool],
    hard_negative_flags: Sequence[bool],
    class_balance_power: float,
    hard_negative_multiplier: float,
) -> tuple[list[float], dict[str, float]]:
    if len(labels) != len(hard_negative_flags):
        raise ValueError("labels and hard_negative_flags must align")
    if not labels:
        raise ValueError("hard-negative weighting requires non-empty labels")
    if not 0.0 <= class_balance_power <= 1.0:
        raise ValueError("class_balance_power must be in [0, 1]")
    if hard_negative_multiplier < 1.0:
        raise ValueError("hard_negative_multiplier must be >= 1.0")

    inhibit_count = sum(int(label) for label in labels)
    execute_count = len(labels) - inhibit_count
    inhibit_weight = ((len(labels) / (2 * inhibit_count)) ** class_balance_power) if inhibit_count else 1.0
    execute_weight = ((len(labels) / (2 * execute_count)) ** class_balance_power) if execute_count else 1.0

    raw_weights: list[float] = []
    for label, is_hard_negative in zip(labels, hard_negative_flags, strict=True):
        weight = inhibit_weight if label else execute_weight
        if label and is_hard_negative:
            weight *= hard_negative_multiplier
        raw_weights.append(weight)

    mean_weight = sum(raw_weights) / len(raw_weights)
    normalized = [weight / mean_weight for weight in raw_weights]
    inhibit_weights = [weight for weight, label in zip(normalized, labels, strict=True) if label]
    execute_weights = [weight for weight, label in zip(normalized, labels, strict=True) if not label]
    hard_negative_weights = [
        weight
        for weight, label, is_hard_negative in zip(normalized, labels, hard_negative_flags, strict=True)
        if label and is_hard_negative
    ]
    return normalized, {
        "inhibit_examples": float(inhibit_count),
        "execute_examples": float(execute_count),
        "hard_negative_examples": float(sum(int(flag and label) for flag, label in zip(hard_negative_flags, labels, strict=True))),
        "mean_inhibit_weight": (sum(inhibit_weights) / len(inhibit_weights)) if inhibit_weights else 0.0,
        "mean_execute_weight": (sum(execute_weights) / len(execute_weights)) if execute_weights else 0.0,
        "mean_hard_negative_weight": (sum(hard_negative_weights) / len(hard_negative_weights)) if hard_negative_weights else 0.0,
        "class_balance_power": float(class_balance_power),
        "hard_negative_multiplier": float(hard_negative_multiplier),
    }


def train_hard_negative_finetuned_cross_encoder_capability_gate_agent(
    *,
    name: str,
    train_examples: Sequence[ViewExample],
    config: EmbeddingPolicyConfig,
    encoder: FrozenEmbeddingEncoder | None,
    contract_aware_inhibition: bool,
) -> tuple[CrossEncoderSemanticGateAgent, dict[str, float]]:
    _require_torch()
    if encoder is None:
        raise ValueError("cross_encoder semantic gate requires an encoder")

    gate_stats, training_rows = _prepare_cross_encoder_capability_training_rows(
        train_examples=train_examples,
        encoder=encoder,
        contract_aware_inhibition=contract_aware_inhibition,
    )
    capability_pairs = [
        (
            row.example.case.request,
            serialize_capability_document(row.best_active_tool, None),
        )
        for row in training_rows
    ]
    capability_labels = [not row.should_execute for row in training_rows]
    hard_negative_flags = [
        row.example.schema_view.shift_kind == ShiftKind.NEGATIVE_NEAR_ORBIT and not row.should_execute
        for row in training_rows
    ]
    sample_weights, weight_stats = _build_class_balanced_hard_negative_weights(
        labels=capability_labels,
        hard_negative_flags=hard_negative_flags,
        class_balance_power=config.cross_encoder_class_balance_power,
        hard_negative_multiplier=config.cross_encoder_hard_negative_multiplier,
    )

    cross_encoder, capability_stats, tuned_param_count = _finetune_cross_encoder_binary_classifier(
        model_path=config.cross_encoder_model_path,
        device=encoder.device,
        batch_size=config.cross_encoder_batch_size,
        max_length=config.cross_encoder_max_length,
        instruction=CROSS_ENCODER_CAPABILITY_INSTRUCTION,
        pairs=capability_pairs,
        labels=capability_labels,
        sample_weights=sample_weights,
        epochs=config.cross_encoder_finetune_epochs,
        learning_rate=config.cross_encoder_finetune_learning_rate,
        weight_decay=config.cross_encoder_finetune_weight_decay,
        tune_last_n_layers=config.cross_encoder_tune_last_n_layers,
        seed=config.seed,
    )
    capability_gate = CrossEncoderCapabilityGate(
        threshold=capability_stats.threshold,
        instruction=CROSS_ENCODER_CAPABILITY_INSTRUCTION,
    )
    disabled_localizer = CrossEncoderClauseLocalizer(threshold=1.1)

    return (
        CrossEncoderSemanticGateAgent(
            name=name,
            encoder=encoder,
            threshold=gate_stats.threshold,
            cross_encoder=cross_encoder,
            contract_aware_inhibition=contract_aware_inhibition,
            clause_localizer=disabled_localizer,
            capability_gate=capability_gate,
        ),
        {
            "train_examples": float(len(train_examples)),
            "gate_threshold": gate_stats.threshold,
            "gate_train_accuracy": gate_stats.train_accuracy,
            "gate_train_execute_recall": gate_stats.train_execute_recall,
            "gate_train_execute_rate": gate_stats.train_execute_rate,
            "contract_aware_inhibition": float(contract_aware_inhibition),
            "description_aware_inhibition": 0.0,
            "learned_capability_inhibition": 1.0,
            "capability_require_cue": 0.0,
            "capability_feature_count": 0.0,
            "capability_gate_threshold": capability_stats.threshold,
            "capability_gate_train_accuracy": capability_stats.train_accuracy,
            "capability_gate_train_inhibit_recall": capability_stats.train_inhibit_recall,
            "capability_gate_train_inhibit_rate": capability_stats.train_inhibit_rate,
            "clause_localizer_threshold": disabled_localizer.threshold,
            "clause_localizer_train_accuracy": 0.0,
            "clause_localizer_train_positive_recall": 0.0,
            "clause_localizer_train_positive_rate": 0.0,
            "cross_encoder_tunable_param_count": float(tuned_param_count),
            "cross_encoder_finetune_epochs": float(config.cross_encoder_finetune_epochs),
            "cross_encoder_tune_last_n_layers": float(config.cross_encoder_tune_last_n_layers),
            "cross_encoder_class_balance_power": weight_stats["class_balance_power"],
            "cross_encoder_hard_negative_multiplier": weight_stats["hard_negative_multiplier"],
            "cross_encoder_weighted_inhibit_examples": weight_stats["inhibit_examples"],
            "cross_encoder_weighted_execute_examples": weight_stats["execute_examples"],
            "cross_encoder_weighted_hard_negative_examples": weight_stats["hard_negative_examples"],
            "cross_encoder_weighted_mean_inhibit_weight": weight_stats["mean_inhibit_weight"],
            "cross_encoder_weighted_mean_execute_weight": weight_stats["mean_execute_weight"],
            "cross_encoder_weighted_mean_hard_negative_weight": weight_stats["mean_hard_negative_weight"],
        },
    )


def train_asymmetric_hard_negative_finetuned_cross_encoder_capability_gate_agent(
    *,
    name: str,
    train_examples: Sequence[ViewExample],
    config: EmbeddingPolicyConfig,
    encoder: FrozenEmbeddingEncoder | None,
    contract_aware_inhibition: bool,
) -> tuple[CrossEncoderSemanticGateAgent, dict[str, float]]:
    _require_torch()
    if encoder is None:
        raise ValueError("cross_encoder semantic gate requires an encoder")

    gate_stats, training_rows = _prepare_cross_encoder_capability_training_rows(
        train_examples=train_examples,
        encoder=encoder,
        contract_aware_inhibition=contract_aware_inhibition,
    )
    capability_pairs = [
        (
            row.example.case.request,
            serialize_capability_document(row.best_active_tool, None),
        )
        for row in training_rows
    ]
    capability_labels = [not row.should_execute for row in training_rows]
    hard_negative_flags = [
        row.example.schema_view.shift_kind == ShiftKind.NEGATIVE_NEAR_ORBIT and not row.should_execute
        for row in training_rows
    ]
    sample_weights, weight_stats = _build_class_balanced_hard_negative_weights(
        labels=capability_labels,
        hard_negative_flags=hard_negative_flags,
        class_balance_power=config.cross_encoder_class_balance_power,
        hard_negative_multiplier=config.cross_encoder_hard_negative_multiplier,
    )

    def threshold_selector(
        scores: Sequence[float],
        labels: Sequence[bool],
        weights: Sequence[float] | None,
    ) -> float:
        return _best_asymmetric_binary_threshold(
            scores,
            labels,
            sample_weights=weights,
            min_execute_retention=config.cross_encoder_positive_retention_target,
        )

    cross_encoder, capability_stats, tuned_param_count = _finetune_cross_encoder_binary_classifier(
        model_path=config.cross_encoder_model_path,
        device=encoder.device,
        batch_size=config.cross_encoder_batch_size,
        max_length=config.cross_encoder_max_length,
        instruction=CROSS_ENCODER_CAPABILITY_INSTRUCTION,
        pairs=capability_pairs,
        labels=capability_labels,
        sample_weights=sample_weights,
        epochs=config.cross_encoder_finetune_epochs,
        learning_rate=config.cross_encoder_finetune_learning_rate,
        weight_decay=config.cross_encoder_finetune_weight_decay,
        tune_last_n_layers=config.cross_encoder_tune_last_n_layers,
        seed=config.seed,
        threshold_selector=threshold_selector,
    )
    capability_gate = CrossEncoderCapabilityGate(
        threshold=capability_stats.threshold,
        instruction=CROSS_ENCODER_CAPABILITY_INSTRUCTION,
    )
    disabled_localizer = CrossEncoderClauseLocalizer(threshold=1.1)

    return (
        CrossEncoderSemanticGateAgent(
            name=name,
            encoder=encoder,
            threshold=gate_stats.threshold,
            cross_encoder=cross_encoder,
            contract_aware_inhibition=contract_aware_inhibition,
            clause_localizer=disabled_localizer,
            capability_gate=capability_gate,
        ),
        {
            "train_examples": float(len(train_examples)),
            "gate_threshold": gate_stats.threshold,
            "gate_train_accuracy": gate_stats.train_accuracy,
            "gate_train_execute_recall": gate_stats.train_execute_recall,
            "gate_train_execute_rate": gate_stats.train_execute_rate,
            "contract_aware_inhibition": float(contract_aware_inhibition),
            "description_aware_inhibition": 0.0,
            "learned_capability_inhibition": 1.0,
            "capability_require_cue": 0.0,
            "capability_feature_count": 0.0,
            "capability_gate_threshold": capability_stats.threshold,
            "capability_gate_train_accuracy": capability_stats.train_accuracy,
            "capability_gate_train_inhibit_recall": capability_stats.train_inhibit_recall,
            "capability_gate_train_inhibit_rate": capability_stats.train_inhibit_rate,
            "clause_localizer_threshold": disabled_localizer.threshold,
            "clause_localizer_train_accuracy": 0.0,
            "clause_localizer_train_positive_recall": 0.0,
            "clause_localizer_train_positive_rate": 0.0,
            "cross_encoder_tunable_param_count": float(tuned_param_count),
            "cross_encoder_finetune_epochs": float(config.cross_encoder_finetune_epochs),
            "cross_encoder_tune_last_n_layers": float(config.cross_encoder_tune_last_n_layers),
            "cross_encoder_class_balance_power": weight_stats["class_balance_power"],
            "cross_encoder_hard_negative_multiplier": weight_stats["hard_negative_multiplier"],
            "cross_encoder_positive_retention_target": float(config.cross_encoder_positive_retention_target),
            "cross_encoder_weighted_inhibit_examples": weight_stats["inhibit_examples"],
            "cross_encoder_weighted_execute_examples": weight_stats["execute_examples"],
            "cross_encoder_weighted_hard_negative_examples": weight_stats["hard_negative_examples"],
            "cross_encoder_weighted_mean_inhibit_weight": weight_stats["mean_inhibit_weight"],
            "cross_encoder_weighted_mean_execute_weight": weight_stats["mean_execute_weight"],
            "cross_encoder_weighted_mean_hard_negative_weight": weight_stats["mean_hard_negative_weight"],
        },
    )


def train_asymmetric_objective_finetuned_cross_encoder_capability_gate_agent(
    *,
    name: str,
    train_examples: Sequence[ViewExample],
    config: EmbeddingPolicyConfig,
    encoder: FrozenEmbeddingEncoder | None,
    contract_aware_inhibition: bool,
) -> tuple[CrossEncoderSemanticGateAgent, dict[str, float]]:
    _require_torch()
    if encoder is None:
        raise ValueError("cross_encoder semantic gate requires an encoder")

    gate_stats, training_rows = _prepare_cross_encoder_capability_training_rows(
        train_examples=train_examples,
        encoder=encoder,
        contract_aware_inhibition=contract_aware_inhibition,
    )
    capability_pairs = [
        (
            row.example.case.request,
            serialize_capability_document(row.best_active_tool, None),
        )
        for row in training_rows
    ]
    capability_labels = [not row.should_execute for row in training_rows]
    hard_negative_flags = [
        row.example.schema_view.shift_kind == ShiftKind.NEGATIVE_NEAR_ORBIT and not row.should_execute
        for row in training_rows
    ]
    sample_weights, weight_stats = _build_class_balanced_hard_negative_weights(
        labels=capability_labels,
        hard_negative_flags=hard_negative_flags,
        class_balance_power=config.cross_encoder_class_balance_power,
        hard_negative_multiplier=config.cross_encoder_hard_negative_multiplier,
    )

    cross_encoder, capability_stats, tuned_param_count = _finetune_cross_encoder_binary_classifier(
        model_path=config.cross_encoder_model_path,
        device=encoder.device,
        batch_size=config.cross_encoder_batch_size,
        max_length=config.cross_encoder_max_length,
        instruction=CROSS_ENCODER_CAPABILITY_INSTRUCTION,
        pairs=capability_pairs,
        labels=capability_labels,
        sample_weights=sample_weights,
        epochs=config.cross_encoder_finetune_epochs,
        learning_rate=config.cross_encoder_finetune_learning_rate,
        weight_decay=config.cross_encoder_finetune_weight_decay,
        tune_last_n_layers=config.cross_encoder_tune_last_n_layers,
        seed=config.seed,
        execute_margin=config.cross_encoder_execute_margin,
        execute_margin_weight=config.cross_encoder_execute_margin_weight,
    )
    capability_gate = CrossEncoderCapabilityGate(
        threshold=capability_stats.threshold,
        instruction=CROSS_ENCODER_CAPABILITY_INSTRUCTION,
    )
    disabled_localizer = CrossEncoderClauseLocalizer(threshold=1.1)

    return (
        CrossEncoderSemanticGateAgent(
            name=name,
            encoder=encoder,
            threshold=gate_stats.threshold,
            cross_encoder=cross_encoder,
            contract_aware_inhibition=contract_aware_inhibition,
            clause_localizer=disabled_localizer,
            capability_gate=capability_gate,
        ),
        {
            "train_examples": float(len(train_examples)),
            "gate_threshold": gate_stats.threshold,
            "gate_train_accuracy": gate_stats.train_accuracy,
            "gate_train_execute_recall": gate_stats.train_execute_recall,
            "gate_train_execute_rate": gate_stats.train_execute_rate,
            "contract_aware_inhibition": float(contract_aware_inhibition),
            "description_aware_inhibition": 0.0,
            "learned_capability_inhibition": 1.0,
            "capability_require_cue": 0.0,
            "capability_feature_count": 0.0,
            "capability_gate_threshold": capability_stats.threshold,
            "capability_gate_train_accuracy": capability_stats.train_accuracy,
            "capability_gate_train_inhibit_recall": capability_stats.train_inhibit_recall,
            "capability_gate_train_inhibit_rate": capability_stats.train_inhibit_rate,
            "clause_localizer_threshold": disabled_localizer.threshold,
            "clause_localizer_train_accuracy": 0.0,
            "clause_localizer_train_positive_recall": 0.0,
            "clause_localizer_train_positive_rate": 0.0,
            "cross_encoder_tunable_param_count": float(tuned_param_count),
            "cross_encoder_finetune_epochs": float(config.cross_encoder_finetune_epochs),
            "cross_encoder_tune_last_n_layers": float(config.cross_encoder_tune_last_n_layers),
            "cross_encoder_class_balance_power": weight_stats["class_balance_power"],
            "cross_encoder_hard_negative_multiplier": weight_stats["hard_negative_multiplier"],
            "cross_encoder_execute_margin": float(config.cross_encoder_execute_margin),
            "cross_encoder_execute_margin_weight": float(config.cross_encoder_execute_margin_weight),
            "cross_encoder_weighted_inhibit_examples": weight_stats["inhibit_examples"],
            "cross_encoder_weighted_execute_examples": weight_stats["execute_examples"],
            "cross_encoder_weighted_hard_negative_examples": weight_stats["hard_negative_examples"],
            "cross_encoder_weighted_mean_inhibit_weight": weight_stats["mean_inhibit_weight"],
            "cross_encoder_weighted_mean_execute_weight": weight_stats["mean_execute_weight"],
            "cross_encoder_weighted_mean_hard_negative_weight": weight_stats["mean_hard_negative_weight"],
        },
    )


def train_dual_threshold_finetuned_cross_encoder_capability_gate_agent(
    *,
    name: str,
    train_examples: Sequence[ViewExample],
    config: EmbeddingPolicyConfig,
    encoder: FrozenEmbeddingEncoder | None,
    contract_aware_inhibition: bool,
) -> tuple[CrossEncoderSemanticGateAgent, dict[str, float]]:
    _require_torch()
    if encoder is None:
        raise ValueError("cross_encoder semantic gate requires an encoder")

    gate_stats, training_rows = _prepare_cross_encoder_capability_training_rows(
        train_examples=train_examples,
        encoder=encoder,
        contract_aware_inhibition=contract_aware_inhibition,
    )
    capability_pairs = [
        (
            row.example.case.request,
            serialize_capability_document(row.best_active_tool, None),
        )
        for row in training_rows
    ]
    capability_labels = [not row.should_execute for row in training_rows]
    hard_negative_flags = [
        row.example.schema_view.shift_kind == ShiftKind.NEGATIVE_NEAR_ORBIT and not row.should_execute
        for row in training_rows
    ]
    sample_weights, weight_stats = _build_class_balanced_hard_negative_weights(
        labels=capability_labels,
        hard_negative_flags=hard_negative_flags,
        class_balance_power=config.cross_encoder_class_balance_power,
        hard_negative_multiplier=config.cross_encoder_hard_negative_multiplier,
    )

    cross_encoder, _binary_stats, tuned_param_count = _finetune_cross_encoder_binary_classifier(
        model_path=config.cross_encoder_model_path,
        device=encoder.device,
        batch_size=config.cross_encoder_batch_size,
        max_length=config.cross_encoder_max_length,
        instruction=CROSS_ENCODER_CAPABILITY_INSTRUCTION,
        pairs=capability_pairs,
        labels=capability_labels,
        sample_weights=sample_weights,
        epochs=config.cross_encoder_finetune_epochs,
        learning_rate=config.cross_encoder_finetune_learning_rate,
        weight_decay=config.cross_encoder_finetune_weight_decay,
        tune_last_n_layers=config.cross_encoder_tune_last_n_layers,
        seed=config.seed,
    )
    capability_scores = cross_encoder.score_pairs(
        instruction=CROSS_ENCODER_CAPABILITY_INSTRUCTION,
        pairs=capability_pairs,
    )
    should_execute = [row.should_execute for row in training_rows]
    allowed_nonexecute_controls = [
        frozenset(
            action.control
            for action in row.example.admissible_actions
            if action.control != ControlTag.EXECUTE
        )
        for row in training_rows
    ]
    abstain_threshold, ask_threshold = _best_dual_threshold_band(
        capability_scores,
        should_execute,
        allowed_nonexecute_controls,
        sample_weights=sample_weights,
    )
    capability_gate = CrossEncoderCapabilityGate(
        threshold=ask_threshold,
        instruction=CROSS_ENCODER_CAPABILITY_INSTRUCTION,
        abstain_threshold=abstain_threshold,
    )
    disabled_localizer = CrossEncoderClauseLocalizer(threshold=1.1)

    predictions = [
        _dual_threshold_control(
            score,
            abstain_threshold=abstain_threshold,
            ask_threshold=ask_threshold,
        )
        for score in capability_scores
    ]
    weights = list(sample_weights)
    total_weight = sum(weights)
    execute_weight = sum(weight for weight, flag in zip(weights, should_execute, strict=True) if flag)
    inhibit_weight = total_weight - execute_weight
    weighted_correct = sum(
        weight
        for predicted, flag, controls, weight in zip(
            predictions,
            should_execute,
            allowed_nonexecute_controls,
            weights,
            strict=True,
        )
        if (flag and predicted == ControlTag.EXECUTE) or ((not flag) and predicted in controls)
    )
    weighted_execute_hit = sum(
        weight
        for predicted, flag, weight in zip(predictions, should_execute, weights, strict=True)
        if flag and predicted == ControlTag.EXECUTE
    )
    weighted_inhibit_hit = sum(
        weight
        for predicted, flag, controls, weight in zip(
            predictions,
            should_execute,
            allowed_nonexecute_controls,
            weights,
            strict=True,
        )
        if (not flag) and predicted in controls
    )
    weighted_abstain = sum(
        weight
        for predicted, weight in zip(predictions, weights, strict=True)
        if predicted == ControlTag.ABSTAIN
    )
    weighted_nonexecute = sum(
        weight
        for predicted, weight in zip(predictions, weights, strict=True)
        if predicted != ControlTag.EXECUTE
    )
    capability_stats = LearnedCapabilityScorerStats(
        threshold=ask_threshold,
        train_accuracy=weighted_correct / total_weight,
        train_inhibit_recall=(weighted_inhibit_hit / inhibit_weight) if inhibit_weight else 0.0,
        train_inhibit_rate=(weighted_nonexecute / total_weight) if total_weight else 0.0,
    )

    return (
        CrossEncoderSemanticGateAgent(
            name=name,
            encoder=encoder,
            threshold=gate_stats.threshold,
            cross_encoder=cross_encoder,
            contract_aware_inhibition=contract_aware_inhibition,
            clause_localizer=disabled_localizer,
            capability_gate=capability_gate,
        ),
        {
            "train_examples": float(len(train_examples)),
            "gate_threshold": gate_stats.threshold,
            "gate_train_accuracy": gate_stats.train_accuracy,
            "gate_train_execute_recall": gate_stats.train_execute_recall,
            "gate_train_execute_rate": gate_stats.train_execute_rate,
            "contract_aware_inhibition": float(contract_aware_inhibition),
            "description_aware_inhibition": 0.0,
            "learned_capability_inhibition": 1.0,
            "capability_require_cue": 0.0,
            "capability_feature_count": 0.0,
            "capability_gate_threshold": capability_stats.threshold,
            "capability_gate_abstain_threshold": float(abstain_threshold),
            "capability_gate_train_accuracy": capability_stats.train_accuracy,
            "capability_gate_train_inhibit_recall": capability_stats.train_inhibit_recall,
            "capability_gate_train_inhibit_rate": capability_stats.train_inhibit_rate,
            "capability_gate_train_execute_recall": (weighted_execute_hit / execute_weight) if execute_weight else 1.0,
            "capability_gate_train_abstain_rate": (weighted_abstain / total_weight) if total_weight else 0.0,
            "clause_localizer_threshold": disabled_localizer.threshold,
            "clause_localizer_train_accuracy": 0.0,
            "clause_localizer_train_positive_recall": 0.0,
            "clause_localizer_train_positive_rate": 0.0,
            "cross_encoder_tunable_param_count": float(tuned_param_count),
            "cross_encoder_finetune_epochs": float(config.cross_encoder_finetune_epochs),
            "cross_encoder_tune_last_n_layers": float(config.cross_encoder_tune_last_n_layers),
            "cross_encoder_class_balance_power": weight_stats["class_balance_power"],
            "cross_encoder_hard_negative_multiplier": weight_stats["hard_negative_multiplier"],
            "cross_encoder_weighted_inhibit_examples": weight_stats["inhibit_examples"],
            "cross_encoder_weighted_execute_examples": weight_stats["execute_examples"],
            "cross_encoder_weighted_hard_negative_examples": weight_stats["hard_negative_examples"],
            "cross_encoder_weighted_mean_inhibit_weight": weight_stats["mean_inhibit_weight"],
            "cross_encoder_weighted_mean_execute_weight": weight_stats["mean_execute_weight"],
            "cross_encoder_weighted_mean_hard_negative_weight": weight_stats["mean_hard_negative_weight"],
        },
    )


def _positive_invariance_loss(action_state: torch.Tensor, train_examples: Sequence[ViewExample]) -> torch.Tensor:
    _require_torch()
    grouped_indices: dict[str, list[int]] = defaultdict(list)
    for index, example in enumerate(train_examples):
        if example.schema_view.shift_kind in {ShiftKind.CLEAN, ShiftKind.POSITIVE_ORBIT}:
            grouped_indices[example.case.case_id].append(index)

    losses: list[torch.Tensor] = []
    normalized = F.normalize(action_state, dim=-1)
    for indices in grouped_indices.values():
        if len(indices) < 2:
            continue
        pairwise = normalized[indices] @ normalized[indices].T
        count = len(indices)
        losses.append(1 - ((pairwise.sum() - count) / (count * (count - 1))))
    if not losses:
        return torch.tensor(0.0)
    return torch.stack(losses).mean()


def _negative_contrastive_loss(
    action_state: torch.Tensor,
    train_examples: Sequence[ViewExample],
    *,
    margin: float,
) -> torch.Tensor:
    _require_torch()
    positive_indices: dict[str, list[int]] = defaultdict(list)
    negative_indices: dict[str, list[int]] = defaultdict(list)
    for index, example in enumerate(train_examples):
        if example.schema_view.shift_kind in {ShiftKind.CLEAN, ShiftKind.POSITIVE_ORBIT}:
            positive_indices[example.case.case_id].append(index)
        elif example.schema_view.shift_kind == ShiftKind.NEGATIVE_NEAR_ORBIT:
            negative_indices[example.case.case_id].append(index)

    normalized = F.normalize(action_state, dim=-1)
    losses: list[torch.Tensor] = []
    for case_id, neg_rows in negative_indices.items():
        pos_rows = positive_indices.get(case_id)
        if not pos_rows:
            continue
        positive_center = F.normalize(normalized[pos_rows].mean(dim=0, keepdim=True), dim=-1)
        negative_state = normalized[neg_rows]
        similarities = (negative_state @ positive_center.T).squeeze(-1)
        losses.append(F.relu(similarities - margin).mean())
    if not losses:
        return torch.tensor(0.0)
    return torch.stack(losses).mean()


def _fit_prototype_execute_gate(
    action_state: torch.Tensor,
    control_targets: torch.Tensor,
) -> tuple[PrototypeExecuteGate, PrototypeExecuteGateStats]:
    normalized = F.normalize(action_state, dim=-1)
    execute_mask = control_targets == CONTROL_ORDER.index(ControlTag.EXECUTE)
    nonexecute_mask = ~execute_mask
    if not execute_mask.any() or not nonexecute_mask.any():
        raise ValueError("prototype execute gate requires both execute and non-execute training examples")

    execute_center = F.normalize(normalized[execute_mask].mean(dim=0, keepdim=True), dim=-1)[0].cpu()
    nonexecute_center = F.normalize(normalized[nonexecute_mask].mean(dim=0, keepdim=True), dim=-1)[0].cpu()
    ask_mask = control_targets == CONTROL_ORDER.index(ControlTag.ASK_CLARIFICATION)
    abstain_mask = control_targets == CONTROL_ORDER.index(ControlTag.ABSTAIN)
    ask_center = F.normalize(normalized[ask_mask].mean(dim=0, keepdim=True), dim=-1)[0].cpu() if ask_mask.any() else None
    abstain_center = F.normalize(normalized[abstain_mask].mean(dim=0, keepdim=True), dim=-1)[0].cpu() if abstain_mask.any() else None

    execute_scores = (normalized @ execute_center.unsqueeze(1)).squeeze(1)
    nonexecute_scores = (normalized @ nonexecute_center.unsqueeze(1)).squeeze(1)
    margins = (execute_scores - nonexecute_scores).tolist()
    labels = execute_mask.tolist()
    threshold = _best_binary_threshold(margins, labels)
    predictions = [score >= threshold for score in margins]
    correct = sum(int(pred == label) for pred, label in zip(predictions, labels, strict=True))
    true_execute = sum(int(label) for label in labels)
    true_positive = sum(int(pred and label) for pred, label in zip(predictions, labels, strict=True))
    gate_stats = PrototypeExecuteGateStats(
        threshold=threshold,
        train_accuracy=correct / len(labels),
        train_execute_recall=(true_positive / true_execute) if true_execute else 0.0,
        train_execute_rate=sum(int(pred) for pred in predictions) / len(predictions),
    )
    return (
        PrototypeExecuteGate(
            execute_center=execute_center,
            nonexecute_center=nonexecute_center,
            ask_center=ask_center,
            abstain_center=abstain_center,
            threshold=threshold,
        ),
        gate_stats,
    )


def _best_binary_threshold(
    scores: Sequence[float],
    labels: Sequence[bool],
    sample_weights: Sequence[float] | None = None,
) -> float:
    if len(scores) != len(labels):
        raise ValueError("scores and labels must have the same length")
    if not scores:
        raise ValueError("scores must be non-empty")
    if sample_weights is not None and len(sample_weights) != len(labels):
        raise ValueError("sample_weights and labels must have the same length")
    ordered = sorted(set(float(score) for score in scores))
    candidates = [ordered[0] - 1e-6]
    candidates.extend((left + right) / 2 for left, right in zip(ordered, ordered[1:], strict=False))
    candidates.append(ordered[-1] + 1e-6)

    weights = list(sample_weights) if sample_weights is not None else [1.0] * len(labels)
    total_weight = sum(weights)
    best_threshold = candidates[0]
    best_metrics: tuple[float, float, float] | None = None
    label_execute_rate = sum(weight for weight, label in zip(weights, labels, strict=True) if label) / total_weight
    for threshold in candidates:
        predictions = [score >= threshold for score in scores]
        accuracy = (
            sum(
                weight
                for pred, label, weight in zip(predictions, labels, weights, strict=True)
                if pred == label
            )
            / total_weight
        )
        true_execute = sum(weight for weight, label in zip(weights, labels, strict=True) if label)
        true_positive = sum(
            weight
            for pred, label, weight in zip(predictions, labels, weights, strict=True)
            if pred and label
        )
        execute_recall = (true_positive / true_execute) if true_execute else 0.0
        predicted_execute_rate = sum(
            weight
            for pred, weight in zip(predictions, weights, strict=True)
            if pred
        ) / total_weight
        metrics = (accuracy, execute_recall, -abs(predicted_execute_rate - label_execute_rate))
        if best_metrics is None or metrics > best_metrics:
            best_metrics = metrics
            best_threshold = threshold
    return best_threshold


def _best_asymmetric_binary_threshold(
    scores: Sequence[float],
    labels: Sequence[bool],
    sample_weights: Sequence[float] | None = None,
    *,
    min_execute_retention: float,
) -> float:
    if not 0.0 <= min_execute_retention <= 1.0:
        raise ValueError("min_execute_retention must be in [0, 1]")
    if len(scores) != len(labels):
        raise ValueError("scores and labels must have the same length")
    if not scores:
        raise ValueError("scores must be non-empty")
    if sample_weights is not None and len(sample_weights) != len(labels):
        raise ValueError("sample_weights and labels must have the same length")

    ordered = sorted(set(float(score) for score in scores))
    candidates = [ordered[0] - 1e-6]
    candidates.extend((left + right) / 2 for left, right in zip(ordered, ordered[1:], strict=False))
    candidates.append(ordered[-1] + 1e-6)

    weights = list(sample_weights) if sample_weights is not None else [1.0] * len(labels)
    total_weight = sum(weights)
    total_execute_weight = sum(weight for weight, label in zip(weights, labels, strict=True) if not label)
    total_inhibit_weight = sum(weight for weight, label in zip(weights, labels, strict=True) if label)
    label_inhibit_rate = total_inhibit_weight / total_weight

    best_threshold = candidates[0]
    best_metrics: tuple[float, float, float, float, float] | None = None
    for threshold in candidates:
        predictions = [score >= threshold for score in scores]
        weighted_correct = sum(
            weight
            for pred, label, weight in zip(predictions, labels, weights, strict=True)
            if pred == label
        )
        weighted_execute_keep = sum(
            weight
            for pred, label, weight in zip(predictions, labels, weights, strict=True)
            if (not pred) and (not label)
        )
        weighted_inhibit_hit = sum(
            weight
            for pred, label, weight in zip(predictions, labels, weights, strict=True)
            if pred and label
        )
        execute_retention = (weighted_execute_keep / total_execute_weight) if total_execute_weight else 1.0
        inhibit_recall = (weighted_inhibit_hit / total_inhibit_weight) if total_inhibit_weight else 0.0
        predicted_inhibit_rate = sum(
            weight
            for pred, weight in zip(predictions, weights, strict=True)
            if pred
        ) / total_weight
        weighted_accuracy = weighted_correct / total_weight
        feasible = float(execute_retention + 1e-9 >= min_execute_retention)
        metrics = (
            feasible,
            inhibit_recall if feasible else execute_retention,
            weighted_accuracy,
            execute_retention,
            -abs(predicted_inhibit_rate - label_inhibit_rate),
        )
        if best_metrics is None or metrics > best_metrics:
            best_metrics = metrics
            best_threshold = threshold
    return best_threshold


def _dual_threshold_control(
    score: float,
    *,
    abstain_threshold: float,
    ask_threshold: float,
) -> ControlTag:
    if abstain_threshold > ask_threshold:
        raise ValueError("abstain_threshold must be <= ask_threshold")
    if score >= ask_threshold:
        return ControlTag.ASK_CLARIFICATION
    if score >= abstain_threshold:
        return ControlTag.ABSTAIN
    return ControlTag.EXECUTE


def _best_dual_threshold_band(
    scores: Sequence[float],
    should_execute: Sequence[bool],
    allowed_nonexecute_controls: Sequence[frozenset[ControlTag]],
    sample_weights: Sequence[float] | None = None,
) -> tuple[float, float]:
    if not scores:
        raise ValueError("scores must be non-empty")
    if len(scores) != len(should_execute) or len(scores) != len(allowed_nonexecute_controls):
        raise ValueError("scores, should_execute, and allowed_nonexecute_controls must align")
    if sample_weights is not None and len(sample_weights) != len(scores):
        raise ValueError("sample_weights and scores must align")

    ordered = sorted(set(float(score) for score in scores))
    candidates = [ordered[0] - 1e-6]
    candidates.extend((left + right) / 2 for left, right in zip(ordered, ordered[1:], strict=False))
    candidates.append(ordered[-1] + 1e-6)

    weights = list(sample_weights) if sample_weights is not None else [1.0] * len(scores)
    total_weight = sum(weights)
    execute_weight = sum(weight for weight, flag in zip(weights, should_execute, strict=True) if flag)
    nonexecute_weight = total_weight - execute_weight
    abstain_only_weight = sum(
        weight
        for weight, flag, controls in zip(weights, should_execute, allowed_nonexecute_controls, strict=True)
        if (not flag) and controls == frozenset({ControlTag.ABSTAIN})
    )
    label_execute_rate = execute_weight / total_weight

    best_pair = (candidates[0], candidates[0])
    best_metrics: tuple[float, float, float, float, float, float] | None = None
    for abstain_threshold in candidates:
        for ask_threshold in candidates:
            if ask_threshold < abstain_threshold:
                continue
            predictions = [
                _dual_threshold_control(
                    score,
                    abstain_threshold=abstain_threshold,
                    ask_threshold=ask_threshold,
                )
                for score in scores
            ]
            weighted_correct = sum(
                weight
                for predicted, flag, controls, weight in zip(
                    predictions,
                    should_execute,
                    allowed_nonexecute_controls,
                    weights,
                    strict=True,
                )
                if (flag and predicted == ControlTag.EXECUTE) or ((not flag) and predicted in controls)
            )
            weighted_execute_hit = sum(
                weight
                for predicted, flag, weight in zip(predictions, should_execute, weights, strict=True)
                if flag and predicted == ControlTag.EXECUTE
            )
            weighted_nonexecute_hit = sum(
                weight
                for predicted, flag, controls, weight in zip(
                    predictions,
                    should_execute,
                    allowed_nonexecute_controls,
                    weights,
                    strict=True,
                )
                if (not flag) and predicted in controls
            )
            weighted_abstain_only_hit = sum(
                weight
                for predicted, flag, controls, weight in zip(
                    predictions,
                    should_execute,
                    allowed_nonexecute_controls,
                    weights,
                    strict=True,
                )
                if (not flag) and controls == frozenset({ControlTag.ABSTAIN}) and predicted == ControlTag.ABSTAIN
            )
            weighted_abstain_rate = sum(
                weight
                for predicted, flag, weight in zip(predictions, should_execute, weights, strict=True)
                if (not flag) and predicted == ControlTag.ABSTAIN
            )
            predicted_execute_rate = sum(
                weight
                for predicted, weight in zip(predictions, weights, strict=True)
                if predicted == ControlTag.EXECUTE
            ) / total_weight
            metrics = (
                weighted_correct / total_weight,
                (weighted_execute_hit / execute_weight) if execute_weight else 1.0,
                (weighted_nonexecute_hit / nonexecute_weight) if nonexecute_weight else 1.0,
                (weighted_abstain_only_hit / abstain_only_weight) if abstain_only_weight else 1.0,
                -((weighted_abstain_rate / nonexecute_weight) if nonexecute_weight else 0.0),
                -abs(predicted_execute_rate - label_execute_rate),
            )
            if best_metrics is None or metrics > best_metrics:
                best_metrics = metrics
                best_pair = (abstain_threshold, ask_threshold)
    return best_pair


def _cross_encoder_execute_margin_penalty(
    logit_diff: torch.Tensor,
    targets: torch.Tensor,
    *,
    execute_margin: float,
) -> torch.Tensor:
    execute_mask = targets < 0.5
    if not bool(execute_mask.any()):
        return logit_diff.new_tensor(0.0)
    execute_logits = logit_diff.float()[execute_mask]
    return torch.relu(execute_logits - float(execute_margin)).mean()


def _sigmoid(value: float) -> float:
    if value >= 0:
        exp_neg = math.exp(-value)
        return float(1 / (1 + exp_neg))
    exp_pos = math.exp(value)
    return float(exp_pos / (1 + exp_pos))


def _tool_contract_compatible(tool: RenderedTool, slot_values: dict[str, object]) -> bool:
    for argument in tool.arguments:
        value = slot_values.get(argument.canonical_name)
        if value is None:
            if argument.required:
                return False
            continue
        if not _rendered_argument_compatible(argument, value):
            return False
    return True


def _tool_has_description_capability_gap(tool: RenderedTool, request: str) -> bool:
    return bool(_capability_gap_stats(tool, request)["has_gap_rule"])


def _capability_feature_map(
    *,
    tool: RenderedTool,
    request: str,
    best_active_score: float,
    second_active_score: float,
    request_feature: torch.Tensor | None = None,
    text_feature_lookup=None,
    feature_names: Sequence[str] | None = None,
) -> dict[str, float]:
    requested = set(feature_names) if feature_names is not None else {
        *CAPABILITY_FEATURE_NAMES,
        *CAPABILITY_EMBEDDING_FEATURE_NAMES,
        *CAPABILITY_RAWTEXT_FEATURE_NAMES,
        *CAPABILITY_DESCRIPTION_POOL_FEATURE_NAMES,
    }
    feature_map: dict[str, float] = {}
    if "best_active_score" in requested:
        feature_map["best_active_score"] = float(best_active_score)
    if "score_margin" in requested:
        feature_map["score_margin"] = float(best_active_score - second_active_score)
    if "tool_overlap" in requested:
        feature_map["tool_overlap"] = float(_tool_request_capability_overlap(tool, request))
    if "is_deprecated" in requested:
        feature_map["is_deprecated"] = float(tool.status == "deprecated")
    if "tool_similarity" in requested:
        feature_map["tool_similarity"] = float(best_active_score)

    gap_stat_features = {
        "description_overlap",
        "cue_clause_count",
        "max_cue_overlap",
        "total_cue_overlap",
        "has_gap_rule",
    }
    if requested & gap_stat_features:
        stats = _capability_gap_stats(tool, request)
        for name in gap_stat_features & requested:
            feature_map[name] = float(stats[name])

    if request_feature is not None and text_feature_lookup is not None:
        if "description_similarity" in requested:
            description_feature = text_feature_lookup(tool.description)
            feature_map["description_similarity"] = float(torch.dot(request_feature, description_feature).item())
        if "argument_similarity" in requested:
            argument_text = _tool_argument_text(tool)
            if argument_text:
                argument_feature = text_feature_lookup(argument_text)
                feature_map["argument_similarity"] = float(torch.dot(request_feature, argument_feature).item())
            else:
                feature_map["argument_similarity"] = 0.0
        if requested & {"max_description_clause_similarity", "mean_description_clause_similarity"}:
            description_clauses = _description_clauses(tool.description)
            if description_clauses:
                clause_similarities = [float(torch.dot(request_feature, text_feature_lookup(clause)).item()) for clause in description_clauses]
                if "max_description_clause_similarity" in requested:
                    feature_map["max_description_clause_similarity"] = max(clause_similarities)
                if "mean_description_clause_similarity" in requested:
                    feature_map["mean_description_clause_similarity"] = sum(clause_similarities) / len(clause_similarities)
            else:
                if "max_description_clause_similarity" in requested:
                    feature_map["max_description_clause_similarity"] = 0.0
                if "mean_description_clause_similarity" in requested:
                    feature_map["mean_description_clause_similarity"] = 0.0
        if requested & {"max_cue_similarity", "mean_cue_similarity"}:
            cue_clauses = _capability_cue_clauses(tool)
            if cue_clauses:
                cue_similarities = [float(torch.dot(request_feature, text_feature_lookup(clause)).item()) for clause in cue_clauses]
                if "max_cue_similarity" in requested:
                    feature_map["max_cue_similarity"] = max(cue_similarities)
                if "mean_cue_similarity" in requested:
                    feature_map["mean_cue_similarity"] = sum(cue_similarities) / len(cue_similarities)
            else:
                if "max_cue_similarity" in requested:
                    feature_map["max_cue_similarity"] = 0.0
                if "mean_cue_similarity" in requested:
                    feature_map["mean_cue_similarity"] = 0.0
    return feature_map


def _capability_gap_stats(tool: RenderedTool, request: str) -> dict[str, int | bool]:
    description = tool.description.lower().replace("_", " ")
    request_tokens = _capability_tokens(request)
    description_tokens = _capability_tokens(description)
    description_overlap = len(request_tokens & description_tokens) if request_tokens else 0
    cue_clause_count = 0
    max_cue_overlap = 0
    total_cue_overlap = 0
    for clause in re.split(r"[.;]", description):
        clause = clause.strip()
        if not clause:
            continue
        if not any(cue in clause for cue in CAPABILITY_GAP_CUES):
            continue
        cue_clause_count += 1
        overlap = len(request_tokens & _capability_tokens(clause))
        max_cue_overlap = max(max_cue_overlap, overlap)
        total_cue_overlap += overlap
    return {
        "description_overlap": description_overlap,
        "cue_clause_count": cue_clause_count,
        "max_cue_overlap": max_cue_overlap,
        "total_cue_overlap": total_cue_overlap,
        "has_gap_rule": description_overlap >= 2 and cue_clause_count > 0,
    }


def _capability_cue_clauses(tool: RenderedTool) -> tuple[str, ...]:
    clauses = []
    for clause in _description_clauses(tool.description):
        lowered = clause.lower()
        if any(cue in lowered for cue in CAPABILITY_GAP_CUES):
            clauses.append(clause)
    return tuple(clauses)


def _description_clauses(description: str) -> tuple[str, ...]:
    clauses = []
    for clause in re.split(r"[.;]", description):
        clause = clause.strip()
        if not clause:
            continue
        clauses.append(clause)
    return tuple(clauses)


def _tool_argument_text(tool: RenderedTool) -> str:
    lines = []
    for argument in tool.arguments:
        lines.append(f"{argument.rendered_name}: {argument.description}")
    return "\n".join(lines)


def _localized_description_clause_stats(
    tool: RenderedTool,
    request_feature: torch.Tensor,
    text_feature_lookup,
) -> tuple[torch.Tensor, float, float, float]:
    description_clauses = _description_clauses(tool.description)
    if not description_clauses:
        description_feature = text_feature_lookup(tool.description)
        similarity = float(torch.dot(request_feature, description_feature).item())
        return description_feature, similarity, 0.0, similarity

    clause_pairs = [
        (float(torch.dot(request_feature, text_feature_lookup(clause)).item()), text_feature_lookup(clause))
        for clause in description_clauses
    ]
    clause_pairs.sort(key=lambda item: item[0], reverse=True)
    top_similarity, top_feature = clause_pairs[0]
    second_similarity = clause_pairs[1][0] if len(clause_pairs) > 1 else 0.0
    mean_similarity = sum(item[0] for item in clause_pairs) / len(clause_pairs)
    return top_feature, top_similarity, second_similarity, mean_similarity


def _clause_localizer_feature_vector(
    *,
    clause: str,
    tool: RenderedTool,
    request_feature: torch.Tensor,
    text_feature_lookup,
) -> torch.Tensor:
    clause_feature = text_feature_lookup(clause)
    description_feature = text_feature_lookup(tool.description)
    argument_text = _tool_argument_text(tool)
    if argument_text:
        argument_feature = text_feature_lookup(argument_text)
        argument_similarity = float(torch.dot(request_feature, argument_feature).item())
        clause_argument_similarity = float(torch.dot(clause_feature, argument_feature).item())
    else:
        argument_similarity = 0.0
        clause_argument_similarity = 0.0
    request_clause_similarity = float(torch.dot(request_feature, clause_feature).item())
    description_similarity = float(torch.dot(request_feature, description_feature).item())
    clause_description_similarity = float(torch.dot(clause_feature, description_feature).item())
    scalar_tail = torch.tensor(
        [
            request_clause_similarity,
            description_similarity,
            argument_similarity,
            clause_description_similarity,
            clause_argument_similarity,
        ],
        dtype=torch.float32,
    )
    return torch.cat([request_feature * clause_feature, scalar_tail], dim=0)


def _clause_localizer_pair_feature_vector(
    *,
    request: str,
    clause: str,
    tool: RenderedTool,
    request_feature: torch.Tensor,
    text_feature_lookup,
) -> torch.Tensor:
    pair_feature = text_feature_lookup(serialize_clause_localizer_pair(request, tool, clause))
    clause_feature = text_feature_lookup(clause)
    description_feature = text_feature_lookup(tool.description)
    argument_text = _tool_argument_text(tool)
    if argument_text:
        argument_feature = text_feature_lookup(argument_text)
        argument_similarity = float(torch.dot(request_feature, argument_feature).item())
    else:
        argument_similarity = 0.0
    request_clause_similarity = float(torch.dot(request_feature, clause_feature).item())
    description_similarity = float(torch.dot(request_feature, description_feature).item())
    clause_description_similarity = float(torch.dot(clause_feature, description_feature).item())
    scalar_tail = torch.tensor(
        [
            request_clause_similarity,
            description_similarity,
            argument_similarity,
            clause_description_similarity,
            float(len(_capability_tokens(clause))),
        ],
        dtype=torch.float32,
    )
    return torch.cat([pair_feature, scalar_tail], dim=0)


def _select_localized_description_clause(
    *,
    request: str,
    tool: RenderedTool,
    request_feature: torch.Tensor,
    text_feature_lookup,
    clause_localizer: ClauseLocalizationInferenceScorer,
    mode: str = "interaction",
) -> tuple[str | None, torch.Tensor | None, float, float, float]:
    description_clauses = _description_clauses(tool.description)
    if not description_clauses:
        return None, None, 0.0, 0.0, 0.0

    candidates: list[tuple[float, float, str, torch.Tensor]] = []
    for clause in description_clauses:
        if mode == "pair_text":
            feature_vector = _clause_localizer_pair_feature_vector(
                request=request,
                clause=clause,
                tool=tool,
                request_feature=request_feature,
                text_feature_lookup=text_feature_lookup,
            )
        else:
            feature_vector = _clause_localizer_feature_vector(
                clause=clause,
                tool=tool,
                request_feature=request_feature,
                text_feature_lookup=text_feature_lookup,
            )
        clause_feature = text_feature_lookup(clause)
        score = clause_localizer.score(feature_vector)
        similarity = float(torch.dot(request_feature, clause_feature).item())
        candidates.append((score, similarity, clause, clause_feature))
    candidates.sort(key=lambda item: item[0], reverse=True)
    best_score, best_similarity, best_clause, best_feature = candidates[0]
    second_score = candidates[1][0] if len(candidates) > 1 else 0.0
    if best_score >= clause_localizer.threshold:
        return best_clause, best_feature, best_similarity, best_score, best_score - second_score
    return None, None, 0.0, best_score, best_score - second_score


def _capability_dense_feature_vector(
    *,
    tool: RenderedTool,
    request: str,
    request_feature: torch.Tensor,
    best_active_score: float,
    second_active_score: float,
    text_feature_lookup,
    mode: str,
    clause_localizer: ClauseLocalizationInferenceScorer | None = None,
) -> torch.Tensor:
    if mode != "localized_clause_interaction":
        if mode not in {
            "learned_clause_localization_interaction",
            "learned_clause_localization_scalar",
            "learned_clause_localization_pair_text",
            "learned_clause_localization_pair_text_mlp",
        }:
            raise ValueError(f"unsupported dense capability mode: {mode}")
        if clause_localizer is None:
            raise ValueError(f"{mode} requires a clause_localizer")

    if mode == "localized_clause_interaction":
        selected_clause_text = None
        top_clause_feature, top_clause_similarity, second_clause_similarity, mean_clause_similarity = (
            _localized_description_clause_stats(tool, request_feature, text_feature_lookup)
        )
        localizer_score = top_clause_similarity
        localizer_margin = top_clause_similarity - second_clause_similarity
        selected_flag = 1.0
    else:
        localization_mode = (
            "pair_text"
            if mode in {"learned_clause_localization_pair_text", "learned_clause_localization_pair_text_mlp"}
            else "interaction"
        )
        selected_clause_text, selected_clause_feature, selected_clause_similarity, localizer_score, localizer_margin = (
            _select_localized_description_clause(
                request=request,
                tool=tool,
                request_feature=request_feature,
                text_feature_lookup=text_feature_lookup,
                clause_localizer=clause_localizer,
                mode=localization_mode,
            )
        )
        if selected_clause_feature is None:
            top_clause_feature = torch.zeros_like(request_feature)
            top_clause_similarity = 0.0
            second_clause_similarity = 0.0
            mean_clause_similarity = 0.0
            selected_flag = 0.0
        else:
            top_clause_feature = selected_clause_feature
            top_clause_similarity = selected_clause_similarity
            second_clause_similarity = 0.0
            mean_clause_similarity = selected_clause_similarity
            selected_flag = 1.0

    description_feature = text_feature_lookup(tool.description)
    argument_text = _tool_argument_text(tool)
    if argument_text:
        argument_feature = text_feature_lookup(argument_text)
        argument_similarity = float(torch.dot(request_feature, argument_feature).item())
    else:
        argument_similarity = 0.0
    description_similarity = float(torch.dot(request_feature, description_feature).item())
    scalar_tail = torch.tensor(
        [
            best_active_score,
            best_active_score - second_active_score,
            description_similarity,
            argument_similarity,
            top_clause_similarity,
            second_clause_similarity,
            mean_clause_similarity,
            localizer_score,
            localizer_margin,
            selected_flag,
        ],
        dtype=torch.float32,
    )
    if mode == "learned_clause_localization_scalar":
        return scalar_tail
    if mode in {"learned_clause_localization_pair_text", "learned_clause_localization_pair_text_mlp"}:
        if selected_clause_text is None:
            pair_feature = torch.zeros_like(request_feature)
        else:
            pair_feature = text_feature_lookup(serialize_capability_pair(request, tool, selected_clause_text))
        return torch.cat([pair_feature, scalar_tail], dim=0)
    return torch.cat([request_feature * top_clause_feature, scalar_tail], dim=0)


def _tool_request_capability_overlap(tool: RenderedTool, request: str) -> int:
    tool_text_parts = [tool.rendered_name, tool.description]
    for argument in tool.arguments:
        tool_text_parts.append(argument.rendered_name)
        tool_text_parts.append(argument.description)
    tool_tokens = _capability_tokens(" ".join(tool_text_parts))
    return len(_capability_tokens(request) & tool_tokens)


def _cross_encoder_clause_feature_map(
    *,
    request: str,
    tool: RenderedTool,
    clause: str,
    cross_encoder: QwenRerankerCrossEncoder,
    localizer_instruction: str,
    capability_instruction: str,
    full_capability_score: float | None = None,
    feature_names: Sequence[str] | None = None,
) -> dict[str, float]:
    requested = set(feature_names) if feature_names is not None else set(CROSS_ENCODER_CLAUSE_FEATURE_NAMES)
    feature_map: dict[str, float] = {}
    clause_document = serialize_clause_localizer_document(tool, clause)
    if "localizer_score" in requested:
        localizer_score = cross_encoder.score_pairs(
            instruction=localizer_instruction,
            pairs=[(request, clause_document)],
        )[0]
        feature_map["localizer_score"] = float(localizer_score)
    localized_capability_score = None
    if requested & {"clause_capability_score", "clause_minus_full"}:
        localized_capability_score = cross_encoder.score_pairs(
            instruction=capability_instruction,
            pairs=[(request, serialize_capability_document(tool, clause))],
        )[0]
        if "clause_capability_score" in requested:
            feature_map["clause_capability_score"] = float(localized_capability_score)
    if "clause_minus_full" in requested:
        if full_capability_score is None:
            full_capability_score = cross_encoder.score_pairs(
                instruction=capability_instruction,
                pairs=[(request, serialize_capability_document(tool, None))],
            )[0]
        if localized_capability_score is None:
            localized_capability_score = cross_encoder.score_pairs(
                instruction=capability_instruction,
                pairs=[(request, serialize_capability_document(tool, clause))],
            )[0]
        feature_map["clause_minus_full"] = float(localized_capability_score - full_capability_score)
    return feature_map


def _cross_encoder_feature_map(
    *,
    request: str,
    tool: RenderedTool,
    best_active_score: float,
    second_active_score: float,
    cross_encoder: QwenRerankerCrossEncoder,
    clause_localizer: CrossEncoderClauseLocalizer,
    capability_instruction: str,
    feature_names: Sequence[str] | None = None,
) -> tuple[dict[str, float], str | None]:
    requested = set(feature_names) if feature_names is not None else set(CROSS_ENCODER_FEATURE_NAMES)
    feature_map: dict[str, float] = {}
    if "best_active_score" in requested:
        feature_map["best_active_score"] = float(best_active_score)
    if "score_margin" in requested:
        feature_map["score_margin"] = float(best_active_score - second_active_score)

    description_clauses = _description_clauses(tool.description)
    selected_clause = None
    top_clause_score = 0.0
    second_clause_score = 0.0
    mean_clause_score = 0.0
    if description_clauses:
        clause_documents = [serialize_clause_localizer_document(tool, clause) for clause in description_clauses]
        clause_scores = cross_encoder.score_pairs(
            instruction=clause_localizer.instruction,
            pairs=[(request, document) for document in clause_documents],
        )
        best_index = max(range(len(clause_scores)), key=clause_scores.__getitem__)
        ordered_scores = sorted(clause_scores, reverse=True)
        top_clause_score = float(ordered_scores[0])
        second_clause_score = float(ordered_scores[1]) if len(ordered_scores) > 1 else 0.0
        mean_clause_score = float(sum(clause_scores) / len(clause_scores))
        if clause_localizer.selection_mode == "learned":
            selected_clause = _select_cross_encoder_clause(
                request=request,
                tool=tool,
                cross_encoder=cross_encoder,
                clause_localizer=clause_localizer,
            )
        elif clause_scores[best_index] >= clause_localizer.threshold:
            selected_clause = description_clauses[best_index]
    if "top_clause_score" in requested:
        feature_map["top_clause_score"] = top_clause_score
    if "second_clause_score" in requested:
        feature_map["second_clause_score"] = second_clause_score
    if "mean_clause_score" in requested:
        feature_map["mean_clause_score"] = mean_clause_score

    if requested & {"full_capability_score", "localized_capability_score", "localized_minus_full"}:
        full_capability_score = cross_encoder.score_pairs(
            instruction=capability_instruction,
            pairs=[(request, serialize_capability_document(tool, None))],
        )[0]
        localized_capability_score = full_capability_score
        if selected_clause is not None:
            localized_capability_score = cross_encoder.score_pairs(
                instruction=capability_instruction,
                pairs=[(request, serialize_capability_document(tool, selected_clause))],
            )[0]
        if "full_capability_score" in requested:
            feature_map["full_capability_score"] = float(full_capability_score)
        if "localized_capability_score" in requested:
            feature_map["localized_capability_score"] = float(localized_capability_score)
        if "localized_minus_full" in requested:
            feature_map["localized_minus_full"] = float(localized_capability_score - full_capability_score)
    return feature_map, selected_clause


def _cross_encoder_clause_ranking(
    *,
    request: str,
    tool: RenderedTool,
    cross_encoder: QwenRerankerCrossEncoder,
    instruction: str,
) -> tuple[tuple[str, ...], list[float], int]:
    description_clauses = _description_clauses(tool.description)
    if not description_clauses:
        return (), [], -1
    documents = [serialize_clause_localizer_document(tool, clause) for clause in description_clauses]
    scores = cross_encoder.score_pairs(
        instruction=instruction,
        pairs=[(request, document) for document in documents],
    )
    best_index = max(range(len(scores)), key=scores.__getitem__)
    return description_clauses, scores, best_index


def _select_cross_encoder_clause(
    *,
    request: str,
    tool: RenderedTool,
    cross_encoder: QwenRerankerCrossEncoder,
    clause_localizer: CrossEncoderClauseLocalizer,
) -> str | None:
    description_clauses, scores, best_index = _cross_encoder_clause_ranking(
        request=request,
        tool=tool,
        cross_encoder=cross_encoder,
        instruction=clause_localizer.instruction,
    )
    if not description_clauses:
        return None
    if clause_localizer.selection_mode == "learned":
        if clause_localizer.ranker is None:
            raise ValueError("learned cross-encoder clause localizer requires a ranker")
        full_capability_score = cross_encoder.score_pairs(
            instruction=CROSS_ENCODER_CAPABILITY_INSTRUCTION,
            pairs=[(request, serialize_capability_document(tool, None))],
        )[0]
        ranked: list[tuple[float, str]] = []
        for clause in description_clauses:
            feature_map = _cross_encoder_clause_feature_map(
                request=request,
                tool=tool,
                clause=clause,
                cross_encoder=cross_encoder,
                localizer_instruction=clause_localizer.instruction,
                capability_instruction=CROSS_ENCODER_CAPABILITY_INSTRUCTION,
                full_capability_score=full_capability_score,
                feature_names=clause_localizer.ranker.feature_names,
            )
            ranked.append((clause_localizer.ranker.score(feature_map), clause))
        ranked.sort(key=lambda item: item[0], reverse=True)
        return ranked[0][1]
    if clause_localizer.selection_mode == "top":
        return description_clauses[best_index]
    return description_clauses[best_index] if scores[best_index] >= clause_localizer.threshold else None


def _cross_encoder_should_inhibit(
    *,
    request: str,
    tool: RenderedTool,
    selected_clause: str | None,
    cross_encoder: QwenRerankerCrossEncoder,
    capability_gate: CrossEncoderCapabilityGate,
) -> tuple[bool, float]:
    score = cross_encoder.score_pairs(
        instruction=capability_gate.instruction,
        pairs=[(request, serialize_capability_document(tool, selected_clause))],
    )[0]
    margin = score - capability_gate.threshold
    return score >= capability_gate.threshold, _sigmoid(margin * 10.0)


def _cross_encoder_decide_capability_control(
    *,
    request: str,
    tool: RenderedTool,
    selected_clause: str | None,
    cross_encoder: QwenRerankerCrossEncoder,
    capability_gate: CrossEncoderCapabilityGate,
) -> tuple[ControlTag | None, float]:
    score = cross_encoder.score_pairs(
        instruction=capability_gate.instruction,
        pairs=[(request, serialize_capability_document(tool, selected_clause))],
    )[0]
    if capability_gate.abstain_threshold is None:
        if score >= capability_gate.threshold:
            margin = score - capability_gate.threshold
            return ControlTag.ASK_CLARIFICATION, _sigmoid(margin * 10.0)
        return None, _sigmoid((capability_gate.threshold - score) * 10.0)
    control = _dual_threshold_control(
        score,
        abstain_threshold=capability_gate.abstain_threshold,
        ask_threshold=capability_gate.threshold,
    )
    if control == ControlTag.EXECUTE:
        return None, _sigmoid((capability_gate.abstain_threshold - score) * 10.0)
    if control == ControlTag.ASK_CLARIFICATION:
        margin = score - capability_gate.threshold
        return ControlTag.ASK_CLARIFICATION, _sigmoid(margin * 10.0)
    band_margin = min(score - capability_gate.abstain_threshold, capability_gate.threshold - score)
    return ControlTag.ABSTAIN, _sigmoid(max(band_margin, 0.0) * 10.0)


def _capability_tokens(text: str) -> set[str]:
    tokens = set()
    for raw_token in re.findall(r"[a-z0-9]+", text.lower().replace("_", " ")):
        if len(raw_token) > 3 and raw_token.endswith("s"):
            token = raw_token[:-1]
        else:
            token = raw_token
        if token in CAPABILITY_STOPWORDS:
            continue
        tokens.add(token)
    return tokens


def _rendered_argument_compatible(argument: RenderedArgument, value: object) -> bool:
    if argument.arg_type == "string":
        return isinstance(value, str)
    if argument.arg_type == "enum":
        if not isinstance(value, str):
            return False
        allowed = {item.lower() for item in argument.enum_values}
        return value.lower() in allowed
    if argument.arg_type == "integer":
        if not isinstance(value, int):
            return False
        if argument.minimum is not None and value < argument.minimum:
            return False
        if argument.maximum is not None and value > argument.maximum:
            return False
        return True
    if argument.arg_type == "number":
        if not isinstance(value, (int, float)):
            return False
        numeric_value = float(value)
        if argument.minimum is not None and numeric_value < argument.minimum:
            return False
        if argument.maximum is not None and numeric_value > argument.maximum:
            return False
        return True
    if argument.arg_type == "boolean":
        return isinstance(value, bool)
    return True


def _require_torch() -> None:
    if torch is None or nn is None or F is None:
        raise ModuleNotFoundError("torch is required for embedding-policy training; run this module in the infer environment")


def _fit_learned_capability_scorer(
    *,
    rows: Sequence[Sequence[float]],
    labels: Sequence[bool],
    feature_names: Sequence[str],
    learning_rate: float = 5e-2,
    weight_decay: float = 1e-3,
    epochs: int = 250,
) -> tuple[LearnedCapabilityScorer, LearnedCapabilityScorerStats]:
    if not rows:
        raise ValueError("capability inhibition scorer requires non-empty training rows")
    feature_tensor = torch.tensor(rows, dtype=torch.float32)
    feature_means = feature_tensor.mean(dim=0)
    feature_scales = feature_tensor.std(dim=0, unbiased=False)
    feature_scales = torch.where(feature_scales > 0, feature_scales, torch.ones_like(feature_scales))
    normalized = (feature_tensor - feature_means) / feature_scales
    targets = torch.tensor(labels, dtype=torch.float32)

    model = nn.Linear(normalized.shape[1], 1)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
    for _ in range(epochs):
        logits = model(normalized).squeeze(-1)
        loss = F.binary_cross_entropy_with_logits(logits, targets)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    with torch.inference_mode():
        logits = model(normalized).squeeze(-1)
        scores = logits.tolist()
    scorer_threshold = _best_binary_threshold(scores, labels)
    predictions = [score >= scorer_threshold for score in scores]
    correct = sum(int(pred == label) for pred, label in zip(predictions, labels, strict=True))
    true_inhibit = sum(int(label) for label in labels)
    true_positive = sum(int(pred and label) for pred, label in zip(predictions, labels, strict=True))
    stats = LearnedCapabilityScorerStats(
        threshold=scorer_threshold,
        train_accuracy=correct / len(labels),
        train_inhibit_recall=(true_positive / true_inhibit) if true_inhibit else 0.0,
        train_inhibit_rate=sum(int(pred) for pred in predictions) / len(predictions),
    )
    weights = tuple(float(value) for value in model.weight.detach().cpu()[0].tolist())
    bias = float(model.bias.detach().cpu().item())
    return (
        LearnedCapabilityScorer(
            weights=weights,
            bias=bias,
            threshold=scorer_threshold,
            feature_means=tuple(float(value) for value in feature_means.tolist()),
            feature_scales=tuple(float(value) for value in feature_scales.tolist()),
            feature_names=tuple(feature_names),
        ),
        stats,
    )


def _fit_pairwise_clause_ranker(
    *,
    feature_maps_by_example: Sequence[Sequence[dict[str, float]]],
    labels_by_example: Sequence[Sequence[bool]],
    feature_names: Sequence[str],
    learning_rate: float = 5e-2,
    weight_decay: float = 1e-3,
    epochs: int = 250,
) -> tuple[LearnedCapabilityScorer, ClauseLocalizerStats]:
    clause_rows: list[list[float]] = []
    clause_example_ids: list[int] = []
    clause_positive: list[bool] = []
    pair_indices: list[tuple[int, int]] = []

    for example_index, (feature_maps, labels) in enumerate(zip(feature_maps_by_example, labels_by_example, strict=True)):
        if len(feature_maps) != len(labels):
            raise ValueError("feature_maps and labels must align")
        start_index = len(clause_rows)
        positive_indices: list[int] = []
        negative_indices: list[int] = []
        for local_index, (feature_map, is_positive) in enumerate(zip(feature_maps, labels, strict=True)):
            clause_rows.append([feature_map[name] for name in feature_names])
            clause_example_ids.append(example_index)
            clause_positive.append(bool(is_positive))
            if is_positive:
                positive_indices.append(start_index + local_index)
            else:
                negative_indices.append(start_index + local_index)
        for positive_index in positive_indices:
            for negative_index in negative_indices:
                pair_indices.append((positive_index, negative_index))

    if not clause_rows or not pair_indices:
        raise ValueError("pairwise clause ranker requires positive/negative clause pairs")

    feature_tensor = torch.tensor(clause_rows, dtype=torch.float32)
    feature_means = feature_tensor.mean(dim=0)
    feature_scales = feature_tensor.std(dim=0, unbiased=False)
    feature_scales = torch.where(feature_scales > 0, feature_scales, torch.ones_like(feature_scales))
    normalized = (feature_tensor - feature_means) / feature_scales

    model = nn.Linear(normalized.shape[1], 1, bias=False)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
    positive_indices = torch.tensor([index for index, _ in pair_indices], dtype=torch.long)
    negative_indices = torch.tensor([index for _, index in pair_indices], dtype=torch.long)
    for _ in range(epochs):
        scores = model(normalized).squeeze(-1)
        positive_scores = scores.index_select(0, positive_indices)
        negative_scores = scores.index_select(0, negative_indices)
        loss = F.softplus(-(positive_scores - negative_scores)).mean()
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    with torch.inference_mode():
        scores = model(normalized).squeeze(-1).tolist()

    pairwise_correct = 0
    for positive_index, negative_index in pair_indices:
        if scores[positive_index] > scores[negative_index]:
            pairwise_correct += 1

    top_hit_total = 0
    top_hit_correct = 0
    grouped_indices: dict[int, list[int]] = defaultdict(list)
    for clause_index, example_index in enumerate(clause_example_ids):
        grouped_indices[example_index].append(clause_index)
    for indices in grouped_indices.values():
        if not any(clause_positive[index] for index in indices):
            continue
        top_hit_total += 1
        best_index = max(indices, key=scores.__getitem__)
        if clause_positive[best_index]:
            top_hit_correct += 1

    stats = ClauseLocalizerStats(
        threshold=0.0,
        train_accuracy=(top_hit_correct / top_hit_total) if top_hit_total else 0.0,
        train_positive_recall=(pairwise_correct / len(pair_indices)) if pair_indices else 0.0,
        train_positive_rate=1.0,
    )
    weights = tuple(float(value) for value in model.weight.detach().cpu()[0].tolist())
    return (
        LearnedCapabilityScorer(
            weights=weights,
            bias=0.0,
            threshold=0.0,
            feature_means=tuple(float(value) for value in feature_means.tolist()),
            feature_scales=tuple(float(value) for value in feature_scales.tolist()),
            feature_names=tuple(feature_names),
        ),
        stats,
    )


def _fit_listwise_clause_ranker(
    *,
    feature_maps_by_example: Sequence[Sequence[dict[str, float]]],
    labels_by_example: Sequence[Sequence[bool]],
    feature_names: Sequence[str],
    learning_rate: float = 5e-2,
    weight_decay: float = 1e-3,
    epochs: int = 250,
) -> tuple[LearnedCapabilityScorer, ClauseLocalizerStats]:
    clause_rows: list[list[float]] = []
    clause_example_ids: list[int] = []
    clause_positive: list[bool] = []
    grouped_spans: list[tuple[int, int]] = []

    for example_index, (feature_maps, labels) in enumerate(zip(feature_maps_by_example, labels_by_example, strict=True)):
        if len(feature_maps) != len(labels):
            raise ValueError("feature_maps and labels must align")
        if not any(labels) or all(labels):
            continue
        start_index = len(clause_rows)
        for feature_map, is_positive in zip(feature_maps, labels, strict=True):
            clause_rows.append([feature_map[name] for name in feature_names])
            clause_example_ids.append(example_index)
            clause_positive.append(bool(is_positive))
        grouped_spans.append((start_index, len(feature_maps)))

    if not clause_rows or not grouped_spans:
        raise ValueError("listwise clause ranker requires mixed positive/negative clause groups")

    feature_tensor = torch.tensor(clause_rows, dtype=torch.float32)
    feature_means = feature_tensor.mean(dim=0)
    feature_scales = feature_tensor.std(dim=0, unbiased=False)
    feature_scales = torch.where(feature_scales > 0, feature_scales, torch.ones_like(feature_scales))
    normalized = (feature_tensor - feature_means) / feature_scales

    model = nn.Linear(normalized.shape[1], 1)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
    positive_masks = []
    group_index_tensors = []
    for start_index, length in grouped_spans:
        group_index_tensors.append(torch.arange(start_index, start_index + length, dtype=torch.long))
        positive_masks.append(torch.tensor(clause_positive[start_index : start_index + length], dtype=torch.float32))

    for _ in range(epochs):
        scores = model(normalized).squeeze(-1)
        losses = []
        for indices, positive_mask in zip(group_index_tensors, positive_masks, strict=True):
            group_scores = scores.index_select(0, indices)
            target = positive_mask / positive_mask.sum()
            losses.append(-(target * F.log_softmax(group_scores, dim=0)).sum())
        loss = torch.stack(losses).mean()
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    with torch.inference_mode():
        scores = model(normalized).squeeze(-1).tolist()

    pairwise_total = 0
    pairwise_correct = 0
    top_hit_total = 0
    top_hit_correct = 0
    grouped_indices: dict[int, list[int]] = defaultdict(list)
    for clause_index, example_index in enumerate(clause_example_ids):
        grouped_indices[example_index].append(clause_index)
    for indices in grouped_indices.values():
        positive_indices = [index for index in indices if clause_positive[index]]
        negative_indices = [index for index in indices if not clause_positive[index]]
        if not positive_indices or not negative_indices:
            continue
        top_hit_total += 1
        best_index = max(indices, key=scores.__getitem__)
        if clause_positive[best_index]:
            top_hit_correct += 1
        for positive_index in positive_indices:
            for negative_index in negative_indices:
                pairwise_total += 1
                if scores[positive_index] > scores[negative_index]:
                    pairwise_correct += 1

    stats = ClauseLocalizerStats(
        threshold=0.0,
        train_accuracy=(top_hit_correct / top_hit_total) if top_hit_total else 0.0,
        train_positive_recall=(pairwise_correct / pairwise_total) if pairwise_total else 0.0,
        train_positive_rate=1.0,
    )
    weights = tuple(float(value) for value in model.weight.detach().cpu()[0].tolist())
    bias = float(model.bias.detach().cpu().item())
    return (
        LearnedCapabilityScorer(
            weights=weights,
            bias=bias,
            threshold=0.0,
            feature_means=tuple(float(value) for value in feature_means.tolist()),
            feature_scales=tuple(float(value) for value in feature_scales.tolist()),
            feature_names=tuple(feature_names),
        ),
        stats,
    )


def _configure_cross_encoder_finetuning(model, *, tune_last_n_layers: int) -> list[torch.nn.Parameter]:
    _require_torch()
    if tune_last_n_layers < 1:
        raise ValueError("tune_last_n_layers must be >= 1")
    if not hasattr(model, "model") or not hasattr(model.model, "layers") or not hasattr(model, "lm_head"):
        raise ValueError("unsupported cross-encoder model structure")

    for parameter in model.parameters():
        parameter.requires_grad = False

    layers = list(model.model.layers)
    selected_modules = list(layers[-min(tune_last_n_layers, len(layers)):])
    if hasattr(model.model, "norm"):
        selected_modules.append(model.model.norm)
    selected_modules.append(model.lm_head)

    trainable: list[torch.nn.Parameter] = []
    seen: set[int] = set()
    for module in selected_modules:
        for parameter in module.parameters():
            if id(parameter) in seen:
                continue
            seen.add(id(parameter))
            parameter.requires_grad = True
            trainable.append(parameter)
    if not trainable:
        raise ValueError("cross-encoder finetuning selected no trainable parameters")
    return trainable


def _load_qwen_reranker_model_uncached(
    *,
    model_path: str,
    device: str,
    max_length: int,
):
    _require_torch()
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True, padding_side="left")
    tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        trust_remote_code=True,
        dtype="auto",
    ).to(device)
    true_token_id = tokenizer("yes", add_special_tokens=False).input_ids[0]
    false_token_id = tokenizer("no", add_special_tokens=False).input_ids[0]
    prefix = (
        "<|im_start|>system\nJudge whether the Document meets the requirements based on the Query and the "
        "Instruct provided. Note that the answer can only be \"yes\" or \"no\".<|im_end|>\n<|im_start|>user\n"
    )
    suffix = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
    prefix_tokens = tokenizer.encode(prefix, add_special_tokens=False)
    suffix_tokens = tokenizer.encode(suffix, add_special_tokens=False)
    return model, tokenizer, true_token_id, false_token_id, prefix_tokens, suffix_tokens, max_length


def _flatten_cross_encoder_binary_tasks(
    tasks: Sequence[CrossEncoderBinaryTaskSpec],
) -> tuple[list[tuple[str, tuple[str, str], bool, float]], dict[str, int]]:
    flattened: list[tuple[str, tuple[str, str], bool, float]] = []
    task_counts: dict[str, int] = {}
    non_empty_tasks = [task for task in tasks if task.pairs]
    if not non_empty_tasks:
        raise ValueError("multitask cross-encoder requires at least one non-empty task")

    for task in non_empty_tasks:
        if len(task.pairs) != len(task.labels):
            raise ValueError(f"task {task.name} has misaligned pairs and labels")
        task_counts[task.name] = len(task.pairs)
        task_weight = 1.0 / len(task.pairs)
        for pair, label in zip(task.pairs, task.labels, strict=True):
            flattened.append((task.instruction, pair, label, task_weight))

    mean_weight = sum(weight for *_rest, weight in flattened) / len(flattened)
    normalized = [
        (instruction, pair, label, weight / mean_weight)
        for instruction, pair, label, weight in flattened
    ]
    return normalized, task_counts


def _finetune_cross_encoder_binary_classifier(
    *,
    model_path: str,
    device: str,
    batch_size: int,
    max_length: int,
    instruction: str,
    pairs: Sequence[tuple[str, str]],
    labels: Sequence[bool],
    sample_weights: Sequence[float] | None,
    epochs: int,
    learning_rate: float,
    weight_decay: float,
    tune_last_n_layers: int,
    seed: int,
    threshold_selector: Callable[[Sequence[float], Sequence[bool], Sequence[float] | None], float] | None = None,
    execute_margin: float | None = None,
    execute_margin_weight: float = 0.0,
) -> tuple[FineTunedQwenRerankerCrossEncoder, LearnedCapabilityScorerStats, int]:
    _require_torch()
    if not pairs:
        raise ValueError("fine-tuned cross-encoder requires non-empty pairs")
    if len(pairs) != len(labels):
        raise ValueError("pairs and labels must align")
    if sample_weights is not None and len(sample_weights) != len(labels):
        raise ValueError("sample_weights and labels must align")

    torch.manual_seed(seed)
    model, tokenizer, true_token_id, false_token_id, prefix_tokens, suffix_tokens, max_length = (
        _load_qwen_reranker_model_uncached(
            model_path=model_path,
            device=device,
            max_length=max_length,
        )
    )
    trainable_parameters = _configure_cross_encoder_finetuning(
        model,
        tune_last_n_layers=tune_last_n_layers,
    )
    optimizer = torch.optim.AdamW(
        trainable_parameters,
        lr=learning_rate,
        weight_decay=weight_decay,
    )

    model.train()
    pair_indices = torch.arange(len(pairs), dtype=torch.long)
    for _ in range(epochs):
        shuffled = pair_indices[torch.randperm(len(pair_indices))]
        for start in range(0, len(shuffled), batch_size):
            batch_indices = shuffled[start:start + batch_size].tolist()
            batch_pairs = [pairs[index] for index in batch_indices]
            padded = QwenRerankerCrossEncoder._prepare_model_inputs(
                tokenizer=tokenizer,
                prefix_tokens=prefix_tokens,
                suffix_tokens=suffix_tokens,
                max_length=max_length,
                device=model.device,
                instruction=instruction,
                pairs=batch_pairs,
            )
            targets = torch.tensor([float(labels[index]) for index in batch_indices], dtype=torch.float32, device=model.device)
            if sample_weights is None:
                weights = None
            else:
                weights = torch.tensor(
                    [float(sample_weights[index]) for index in batch_indices],
                    dtype=torch.float32,
                    device=model.device,
                )
            _batch_scores, logit_diff = QwenRerankerCrossEncoder._yes_probabilities(
                model=model,
                padded_inputs=padded,
                true_token_id=true_token_id,
                false_token_id=false_token_id,
            )
            if weights is None:
                loss = F.binary_cross_entropy_with_logits(logit_diff.float(), targets)
            else:
                per_example_loss = F.binary_cross_entropy_with_logits(logit_diff.float(), targets, reduction="none")
                loss = (per_example_loss * weights).mean()
            if execute_margin is not None and execute_margin_weight > 0.0:
                execute_penalty = _cross_encoder_execute_margin_penalty(
                    logit_diff,
                    targets,
                    execute_margin=execute_margin,
                )
                loss = loss + float(execute_margin_weight) * execute_penalty
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(trainable_parameters, 1.0)
            optimizer.step()

    tuned_cross_encoder = FineTunedQwenRerankerCrossEncoder(
        model_path=model_path,
        device=device,
        batch_size=batch_size,
        max_length=max_length,
        model=model,
        tokenizer=tokenizer,
        true_token_id=true_token_id,
        false_token_id=false_token_id,
        prefix_tokens=prefix_tokens,
        suffix_tokens=suffix_tokens,
    )
    scores = tuned_cross_encoder.score_pairs(
        instruction=instruction,
        pairs=pairs,
    )
    selector = threshold_selector or _best_binary_threshold
    threshold = selector(scores, labels, sample_weights)
    predictions = [score >= threshold for score in scores]
    weights = list(sample_weights) if sample_weights is not None else [1.0] * len(labels)
    total_weight = sum(weights)
    correct = sum(
        weight
        for pred, label, weight in zip(predictions, labels, weights, strict=True)
        if pred == label
    )
    true_inhibit = sum(weight for weight, label in zip(weights, labels, strict=True) if label)
    true_positive = sum(
        weight
        for pred, label, weight in zip(predictions, labels, weights, strict=True)
        if pred and label
    )
    stats = LearnedCapabilityScorerStats(
        threshold=threshold,
        train_accuracy=correct / total_weight,
        train_inhibit_recall=(true_positive / true_inhibit) if true_inhibit else 0.0,
        train_inhibit_rate=sum(
            weight
            for pred, weight in zip(predictions, weights, strict=True)
            if pred
        ) / total_weight,
    )
    tuned_cross_encoder._score_cache.clear()
    return tuned_cross_encoder, stats, sum(parameter.numel() for parameter in trainable_parameters)


def _finetune_cross_encoder_multitask_binary_classifier(
    *,
    model_path: str,
    device: str,
    batch_size: int,
    max_length: int,
    tasks: Sequence[CrossEncoderBinaryTaskSpec],
    epochs: int,
    learning_rate: float,
    weight_decay: float,
    tune_last_n_layers: int,
    seed: int,
) -> tuple[FineTunedQwenRerankerCrossEncoder, dict[str, LearnedCapabilityScorerStats], int]:
    _require_torch()
    flattened, _task_counts = _flatten_cross_encoder_binary_tasks(tasks)
    torch.manual_seed(seed)
    model, tokenizer, true_token_id, false_token_id, prefix_tokens, suffix_tokens, max_length = (
        _load_qwen_reranker_model_uncached(
            model_path=model_path,
            device=device,
            max_length=max_length,
        )
    )
    trainable_parameters = _configure_cross_encoder_finetuning(
        model,
        tune_last_n_layers=tune_last_n_layers,
    )
    optimizer = torch.optim.AdamW(
        trainable_parameters,
        lr=learning_rate,
        weight_decay=weight_decay,
    )

    model.train()
    flat_indices = torch.arange(len(flattened), dtype=torch.long)
    for _ in range(epochs):
        shuffled = flat_indices[torch.randperm(len(flat_indices))]
        for start in range(0, len(shuffled), batch_size):
            batch_entries = [flattened[index] for index in shuffled[start:start + batch_size].tolist()]
            # Rebuild inputs per-example because each task can carry a different instruction.
            # The batch is still padded together before the forward pass.
            batch_texts = [
                f"<Instruct>: {instruction}\n<Query>: {pair[0]}\n<Document>: {pair[1]}"
                for instruction, pair, _label, _weight in batch_entries
            ]
            max_pair_length = max_length - len(prefix_tokens) - len(suffix_tokens)
            encoded = tokenizer(
                batch_texts,
                padding=False,
                truncation="longest_first",
                return_attention_mask=False,
                max_length=max_pair_length,
            )
            input_ids = [list(prefix_tokens) + ids + list(suffix_tokens) for ids in encoded["input_ids"]]
            padded = tokenizer.pad({"input_ids": input_ids}, padding=True, return_tensors="pt")
            for key, value in padded.items():
                padded[key] = value.to(model.device)
            targets = torch.tensor([float(label) for _instruction, _pair, label, _weight in batch_entries], dtype=torch.float32, device=model.device)
            weights = torch.tensor([float(weight) for _instruction, _pair, _label, weight in batch_entries], dtype=torch.float32, device=model.device)
            _batch_scores, logit_diff = QwenRerankerCrossEncoder._yes_probabilities(
                model=model,
                padded_inputs=padded,
                true_token_id=true_token_id,
                false_token_id=false_token_id,
            )
            per_example_loss = F.binary_cross_entropy_with_logits(logit_diff.float(), targets, reduction="none")
            loss = (per_example_loss * weights).mean()
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(trainable_parameters, 1.0)
            optimizer.step()

    tuned_cross_encoder = FineTunedQwenRerankerCrossEncoder(
        model_path=model_path,
        device=device,
        batch_size=batch_size,
        max_length=max_length,
        model=model,
        tokenizer=tokenizer,
        true_token_id=true_token_id,
        false_token_id=false_token_id,
        prefix_tokens=prefix_tokens,
        suffix_tokens=suffix_tokens,
    )
    task_stats: dict[str, LearnedCapabilityScorerStats] = {}
    for task in tasks:
        if not task.pairs:
            continue
        scores = tuned_cross_encoder.score_pairs(
            instruction=task.instruction,
            pairs=task.pairs,
        )
        threshold = _best_binary_threshold(scores, task.labels)
        predictions = [score >= threshold for score in scores]
        correct = sum(int(pred == label) for pred, label in zip(predictions, task.labels, strict=True))
        true_positive_targets = sum(int(label) for label in task.labels)
        true_positives = sum(int(pred and label) for pred, label in zip(predictions, task.labels, strict=True))
        task_stats[task.name] = LearnedCapabilityScorerStats(
            threshold=threshold,
            train_accuracy=correct / len(task.labels),
            train_inhibit_recall=(true_positives / true_positive_targets) if true_positive_targets else 0.0,
            train_inhibit_rate=sum(int(pred) for pred in predictions) / len(predictions),
        )
    tuned_cross_encoder._score_cache.clear()
    return tuned_cross_encoder, task_stats, sum(parameter.numel() for parameter in trainable_parameters)


def _train_capability_inhibition_scorer(
    *,
    train_examples: Sequence[ViewExample],
    encoder: FrozenEmbeddingEncoder,
    threshold: float,
    contract_aware_inhibition: bool,
    feature_names: Sequence[str],
) -> tuple[LearnedCapabilityScorer, LearnedCapabilityScorerStats]:
    rows: list[list[float]] = []
    labels: list[bool] = []
    request_cache: dict[str, torch.Tensor] = {}
    text_cache: dict[str, torch.Tensor] = {}

    def request_feature_for(request: str) -> torch.Tensor:
        cached = request_cache.get(request)
        if cached is not None:
            return cached
        feature = encoder.encode_texts([encoder._with_instruction(serialize_request(request))])[0].float().cpu()
        request_cache[request] = feature
        return feature

    def text_feature_for(text: str) -> torch.Tensor:
        cached = text_cache.get(text)
        if cached is not None:
            return cached
        feature = encoder.encode_texts([encoder._with_instruction(text)])[0].float().cpu()
        text_cache[text] = feature
        return feature

    for example in train_examples:
        request_feature = request_feature_for(example.case.request)
        active_tools = [tool for tool in example.schema_view.tools if tool.status == "active"]
        if not active_tools:
            continue
        active_scores = [
            (float(torch.dot(request_feature, text_feature_for(serialize_tool(tool))).item()), tool)
            for tool in active_tools
        ]
        active_scores.sort(key=lambda item: item[0], reverse=True)
        best_active_score, best_active_tool = active_scores[0]
        second_active_score = active_scores[1][0] if len(active_scores) > 1 else 0.0
        if contract_aware_inhibition and not _tool_contract_compatible(best_active_tool, example.case.slot_values):
            continue
        execute_expected_tool_ids = {
            action.tool_id
            for action in example.admissible_actions
            if action.control == ControlTag.EXECUTE and action.tool_id is not None
        }
        should_execute = bool(execute_expected_tool_ids) and best_active_tool.canonical_tool_id in execute_expected_tool_ids
        feature_map = _capability_feature_map(
            tool=best_active_tool,
            request=example.case.request,
            best_active_score=best_active_score,
            second_active_score=second_active_score,
            request_feature=request_feature,
            text_feature_lookup=text_feature_for,
            feature_names=feature_names,
        )
        rows.append([feature_map[name] for name in feature_names])
        labels.append(not should_execute)

    if not rows:
        raise ValueError("capability inhibition scorer requires non-empty training rows")
    return _fit_learned_capability_scorer(rows=rows, labels=labels, feature_names=feature_names)


def _train_dense_capability_inhibition_scorer(
    *,
    train_examples: Sequence[ViewExample],
    encoder: FrozenEmbeddingEncoder,
    threshold: float,
    contract_aware_inhibition: bool,
    mode: str,
    clause_localizer: ClauseLocalizationInferenceScorer | None = None,
) -> tuple[DenseCapabilityInferenceScorer, LearnedCapabilityScorerStats]:
    rows: list[torch.Tensor] = []
    labels: list[bool] = []
    request_cache: dict[str, torch.Tensor] = {}
    text_cache: dict[str, torch.Tensor] = {}

    def request_feature_for(request: str) -> torch.Tensor:
        cached = request_cache.get(request)
        if cached is not None:
            return cached
        feature = encoder.encode_texts([encoder._with_instruction(serialize_request(request))])[0].float().cpu()
        request_cache[request] = feature
        return feature

    def text_feature_for(text: str) -> torch.Tensor:
        cached = text_cache.get(text)
        if cached is not None:
            return cached
        feature = encoder.encode_texts([encoder._with_instruction(text)])[0].float().cpu()
        text_cache[text] = feature
        return feature

    for example in train_examples:
        request_feature = request_feature_for(example.case.request)
        active_tools = [tool for tool in example.schema_view.tools if tool.status == "active"]
        if not active_tools:
            continue
        active_scores = [
            (float(torch.dot(request_feature, text_feature_for(serialize_tool(tool))).item()), tool)
            for tool in active_tools
        ]
        active_scores.sort(key=lambda item: item[0], reverse=True)
        best_active_score, best_active_tool = active_scores[0]
        second_active_score = active_scores[1][0] if len(active_scores) > 1 else 0.0
        if contract_aware_inhibition and not _tool_contract_compatible(best_active_tool, example.case.slot_values):
            continue
        execute_expected_tool_ids = {
            action.tool_id
            for action in example.admissible_actions
            if action.control == ControlTag.EXECUTE and action.tool_id is not None
        }
        should_execute = bool(execute_expected_tool_ids) and best_active_tool.canonical_tool_id in execute_expected_tool_ids
        rows.append(
            _capability_dense_feature_vector(
                tool=best_active_tool,
                request=example.case.request,
                request_feature=request_feature,
                best_active_score=best_active_score,
                second_active_score=second_active_score,
                text_feature_lookup=text_feature_for,
                mode=mode,
                clause_localizer=clause_localizer,
            )
        )
        labels.append(not should_execute)

    if not rows:
        raise ValueError("dense capability inhibition scorer requires non-empty training rows")

    feature_tensor = torch.stack(rows).float()
    feature_means = feature_tensor.mean(dim=0)
    feature_scales = feature_tensor.std(dim=0, unbiased=False)
    feature_scales = torch.where(feature_scales > 0, feature_scales, torch.ones_like(feature_scales))
    normalized = (feature_tensor - feature_means) / feature_scales
    targets = torch.tensor(labels, dtype=torch.float32)

    use_mlp = mode == "learned_clause_localization_pair_text_mlp"
    if use_mlp:
        hidden_dim = min(64, max(16, normalized.shape[1] // 4))
        model = nn.Sequential(
            nn.Linear(normalized.shape[1], hidden_dim),
            nn.ReLU(),
            nn.Dropout(p=0.15),
            nn.Linear(hidden_dim, 1),
        )
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-2, weight_decay=5e-2)
    else:
        model = nn.Linear(normalized.shape[1], 1)
        optimizer = torch.optim.AdamW(model.parameters(), lr=5e-2, weight_decay=1e-2)
    for _ in range(250):
        logits = model(normalized).squeeze(-1)
        loss = F.binary_cross_entropy_with_logits(logits, targets)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    with torch.inference_mode():
        logits = model(normalized).squeeze(-1)
        scores = logits.tolist()
    scorer_threshold = _best_binary_threshold(scores, labels)
    predictions = [score >= scorer_threshold for score in scores]
    correct = sum(int(pred == label) for pred, label in zip(predictions, labels, strict=True))
    true_inhibit = sum(int(label) for label in labels)
    true_positive = sum(int(pred and label) for pred, label in zip(predictions, labels, strict=True))
    stats = LearnedCapabilityScorerStats(
        threshold=scorer_threshold,
        train_accuracy=correct / len(labels),
        train_inhibit_recall=(true_positive / true_inhibit) if true_inhibit else 0.0,
        train_inhibit_rate=sum(int(pred) for pred in predictions) / len(predictions),
    )
    if use_mlp:
        first = model[0]
        last = model[3]
        scorer: DenseCapabilityInferenceScorer = NeuralDenseCapabilityScorer(
            hidden_weights=tuple(tuple(float(value) for value in row.tolist()) for row in first.weight.detach().cpu()),
            hidden_bias=tuple(float(value) for value in first.bias.detach().cpu().tolist()),
            output_weights=tuple(float(value) for value in last.weight.detach().cpu()[0].tolist()),
            output_bias=float(last.bias.detach().cpu().item()),
            threshold=scorer_threshold,
            feature_means=tuple(float(value) for value in feature_means.tolist()),
            feature_scales=tuple(float(value) for value in feature_scales.tolist()),
            mode=mode,
        )
    else:
        scorer = DenseCapabilityScorer(
            weights=tuple(float(value) for value in model.weight.detach().cpu()[0].tolist()),
            bias=float(model.bias.detach().cpu().item()),
            threshold=scorer_threshold,
            feature_means=tuple(float(value) for value in feature_means.tolist()),
            feature_scales=tuple(float(value) for value in feature_scales.tolist()),
            mode=mode,
        )
    return (scorer, stats)


def _train_clause_localizer(
    *,
    train_examples: Sequence[ViewExample],
    encoder: FrozenEmbeddingEncoder,
    contract_aware_inhibition: bool,
    mode: str = "interaction",
    model_kind: str = "linear",
) -> tuple[ClauseLocalizationInferenceScorer, ClauseLocalizerStats]:
    rows: list[torch.Tensor] = []
    labels: list[bool] = []
    request_cache: dict[str, torch.Tensor] = {}
    text_cache: dict[str, torch.Tensor] = {}

    def request_feature_for(request: str) -> torch.Tensor:
        cached = request_cache.get(request)
        if cached is not None:
            return cached
        feature = encoder.encode_texts([encoder._with_instruction(serialize_request(request))])[0].float().cpu()
        request_cache[request] = feature
        return feature

    def text_feature_for(text: str) -> torch.Tensor:
        cached = text_cache.get(text)
        if cached is not None:
            return cached
        feature = encoder.encode_texts([encoder._with_instruction(text)])[0].float().cpu()
        text_cache[text] = feature
        return feature

    for example in train_examples:
        request_feature = request_feature_for(example.case.request)
        active_tools = [tool for tool in example.schema_view.tools if tool.status == "active"]
        if not active_tools:
            continue
        active_scores = [
            (float(torch.dot(request_feature, text_feature_for(serialize_tool(tool))).item()), tool)
            for tool in active_tools
        ]
        active_scores.sort(key=lambda item: item[0], reverse=True)
        best_active_score, best_active_tool = active_scores[0]
        if contract_aware_inhibition and not _tool_contract_compatible(best_active_tool, example.case.slot_values):
            continue
        execute_expected_tool_ids = {
            action.tool_id
            for action in example.admissible_actions
            if action.control == ControlTag.EXECUTE and action.tool_id is not None
        }
        should_execute = bool(execute_expected_tool_ids) and best_active_tool.canonical_tool_id in execute_expected_tool_ids
        positive_clauses = set(_capability_cue_clauses(best_active_tool)) if not should_execute else set()
        for clause in _description_clauses(best_active_tool.description):
            feature_vector = (
                _clause_localizer_pair_feature_vector(
                    request=example.case.request,
                    clause=clause,
                    tool=best_active_tool,
                    request_feature=request_feature,
                    text_feature_lookup=text_feature_for,
                )
                if mode == "pair_text"
                else _clause_localizer_feature_vector(
                    clause=clause,
                    tool=best_active_tool,
                    request_feature=request_feature,
                    text_feature_lookup=text_feature_for,
                )
            )
            rows.append(feature_vector)
            labels.append(clause in positive_clauses)

    if not rows:
        raise ValueError("clause localizer requires non-empty training rows")

    feature_tensor = torch.stack(rows).float()
    feature_means = feature_tensor.mean(dim=0)
    feature_scales = feature_tensor.std(dim=0, unbiased=False)
    feature_scales = torch.where(feature_scales > 0, feature_scales, torch.ones_like(feature_scales))
    normalized = (feature_tensor - feature_means) / feature_scales
    targets = torch.tensor(labels, dtype=torch.float32)

    positives = sum(int(label) for label in labels)
    negatives = len(labels) - positives
    pos_weight_value = float(negatives / positives) if positives else 1.0
    use_mlp = model_kind == "mlp"
    if use_mlp:
        hidden_dim = min(64, max(16, normalized.shape[1] // 4))
        model = nn.Sequential(
            nn.Linear(normalized.shape[1], hidden_dim),
            nn.ReLU(),
            nn.Dropout(p=0.15),
            nn.Linear(hidden_dim, 1),
        )
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-2, weight_decay=5e-2)
    else:
        model = nn.Linear(normalized.shape[1], 1)
        optimizer = torch.optim.AdamW(model.parameters(), lr=5e-2, weight_decay=1e-2)
    pos_weight = torch.tensor([pos_weight_value], dtype=torch.float32)
    for _ in range(250):
        logits = model(normalized).squeeze(-1)
        loss = F.binary_cross_entropy_with_logits(logits, targets, pos_weight=pos_weight)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    with torch.inference_mode():
        logits = model(normalized).squeeze(-1)
        scores = logits.tolist()
    localizer_threshold = _best_binary_threshold(scores, labels)
    predictions = [score >= localizer_threshold for score in scores]
    correct = sum(int(pred == label) for pred, label in zip(predictions, labels, strict=True))
    true_positive = sum(int(label) for label in labels)
    predicted_positive = sum(int(pred) for pred in predictions)
    stats = ClauseLocalizerStats(
        threshold=localizer_threshold,
        train_accuracy=correct / len(labels),
        train_positive_recall=(sum(int(pred and label) for pred, label in zip(predictions, labels, strict=True)) / true_positive) if true_positive else 0.0,
        train_positive_rate=(predicted_positive / len(labels)) if labels else 0.0,
    )
    if use_mlp:
        first = model[0]
        last = model[3]
        localizer: ClauseLocalizationInferenceScorer = NeuralClauseLocalizer(
            hidden_weights=tuple(tuple(float(value) for value in row.tolist()) for row in first.weight.detach().cpu()),
            hidden_bias=tuple(float(value) for value in first.bias.detach().cpu().tolist()),
            output_weights=tuple(float(value) for value in last.weight.detach().cpu()[0].tolist()),
            output_bias=float(last.bias.detach().cpu().item()),
            threshold=localizer_threshold,
            feature_means=tuple(float(value) for value in feature_means.tolist()),
            feature_scales=tuple(float(value) for value in feature_scales.tolist()),
        )
    else:
        localizer = LearnedClauseLocalizer(
            weights=tuple(float(value) for value in model.weight.detach().cpu()[0].tolist()),
            bias=float(model.bias.detach().cpu().item()),
            threshold=localizer_threshold,
            feature_means=tuple(float(value) for value in feature_means.tolist()),
            feature_scales=tuple(float(value) for value in feature_scales.tolist()),
        )
    return (localizer, stats)
