from __future__ import annotations

import math
import re
from dataclasses import dataclass

from .benchmark import ViewExample
from .schema import ControlTag, RenderedArgument, ToolCall


TOKEN_RE = re.compile(r"[a-z0-9_@.]+")


def tokenize(text: str) -> set[str]:
    return set(TOKEN_RE.findall(text.lower()))


def _overlap_score(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    intersection = len(left & right)
    return intersection / math.sqrt(len(left) * len(right))


@dataclass
class BaseAgent:
    name: str

    def predict(self, example: ViewExample) -> ToolCall:
        raise NotImplementedError


class OracleAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(name="oracle")

    def predict(self, example: ViewExample) -> ToolCall:
        action = example.admissible_actions[0]
        if action.control != ControlTag.EXECUTE:
            return ToolCall(control=action.control, confidence=1.0)
        tool = next(tool for tool in example.schema_view.tools if tool.canonical_tool_id == action.tool_id)
        arguments = {}
        for rendered_argument in tool.arguments:
            if rendered_argument.canonical_name in action.arguments:
                arguments[rendered_argument.rendered_name] = action.arguments[rendered_argument.canonical_name]
                continue
            if rendered_argument.canonical_name in example.case.slot_values:
                # Preserve optional explicit-view slots that are surfaced in the benchmark
                # but omitted from the minimal canonical action.
                arguments[rendered_argument.rendered_name] = example.case.slot_values[rendered_argument.canonical_name]
        return ToolCall(
            control=ControlTag.EXECUTE,
            rendered_tool_name=tool.rendered_name,
            arguments=arguments,
            confidence=1.0,
        )


class HeuristicAgent(BaseAgent):
    def __init__(
        self,
        *,
        name: str,
        tool_name_weight: float,
        tool_desc_weight: float,
        arg_name_weight: float,
        arg_desc_weight: float,
        deprecated_penalty: float,
        enforce_contract_compatibility: bool,
        honor_deprecation_status: bool,
    ) -> None:
        super().__init__(name=name)
        self.tool_name_weight = tool_name_weight
        self.tool_desc_weight = tool_desc_weight
        self.arg_name_weight = arg_name_weight
        self.arg_desc_weight = arg_desc_weight
        self.deprecated_penalty = deprecated_penalty
        self.enforce_contract_compatibility = enforce_contract_compatibility
        self.honor_deprecation_status = honor_deprecation_status

    def predict(self, example: ViewExample) -> ToolCall:
        request_tokens = tokenize(example.case.request)
        scored_tools = []
        for tool in example.schema_view.tools:
            name_tokens = tokenize(tool.rendered_name.replace(".", " ").replace("_", " "))
            description_tokens = tokenize(tool.description)
            arg_name_tokens = set().union(*(tokenize(argument.rendered_name.replace("_", " ")) for argument in tool.arguments))
            arg_desc_tokens = set().union(*(tokenize(argument.description) for argument in tool.arguments))
            score = (
                self.tool_name_weight * _overlap_score(request_tokens, name_tokens)
                + self.tool_desc_weight * _overlap_score(request_tokens, description_tokens)
                + self.arg_name_weight * _overlap_score(request_tokens, arg_name_tokens)
                + self.arg_desc_weight * _overlap_score(request_tokens, arg_desc_tokens)
            )
            if tool.status == "deprecated":
                score -= self.deprecated_penalty
            scored_tools.append((score, tool))
        scored_tools.sort(key=lambda item: item[0], reverse=True)
        best_score, best_tool = scored_tools[0]
        second_score = scored_tools[1][0] if len(scored_tools) > 1 else 0.0
        if best_score <= 0.0:
            return ToolCall(control=ControlTag.ABSTAIN, confidence=0.05)
        if best_tool.status == "deprecated" and self.honor_deprecation_status:
            return ToolCall(control=ControlTag.ABSTAIN, confidence=max(best_score - second_score, 0.05))
        arguments: dict[str, object] = {}
        slot_usage: set[str] = set()
        for argument in best_tool.arguments:
            slot_name, slot_score = self._match_slot(argument, example.case.slot_values, slot_usage)
            if argument.required and slot_name is None:
                control = ControlTag.ASK_CLARIFICATION if best_tool.status != "deprecated" else ControlTag.ABSTAIN
                return ToolCall(control=control, confidence=max(best_score - second_score, 0.05))
            if slot_name is not None:
                slot_usage.add(slot_name)
                arguments[argument.rendered_name] = example.case.slot_values[slot_name]
        confidence = max(best_score - second_score, 0.05)
        return ToolCall(
            control=ControlTag.EXECUTE,
            rendered_tool_name=best_tool.rendered_name,
            arguments=arguments,
            confidence=confidence,
        )

    def _match_slot(
        self,
        argument: RenderedArgument,
        slot_values: dict[str, object],
        used_slots: set[str],
    ) -> tuple[str | None, float]:
        name_tokens = tokenize(argument.rendered_name.replace("_", " "))
        description_tokens = tokenize(argument.description)
        best_slot = None
        best_score = 0.0
        for slot_name in slot_values:
            if slot_name in used_slots:
                continue
            if self.enforce_contract_compatibility and not _slot_compatible(argument, slot_values[slot_name]):
                continue
            slot_tokens = tokenize(slot_name.replace("_", " "))
            score = (
                self.arg_name_weight * _overlap_score(slot_tokens, name_tokens)
                + self.arg_desc_weight * _overlap_score(slot_tokens, description_tokens)
            )
            if score > best_score:
                best_slot = slot_name
                best_score = score
        return best_slot, best_score


class LexicalShortcutAgent(HeuristicAgent):
    def __init__(self) -> None:
        super().__init__(
            name="lexical_shortcut",
            tool_name_weight=0.9,
            tool_desc_weight=0.0,
            arg_name_weight=0.8,
            arg_desc_weight=0.0,
            deprecated_penalty=0.05,
            enforce_contract_compatibility=False,
            honor_deprecation_status=False,
        )


class DescriptionGroundedAgent(HeuristicAgent):
    def __init__(self) -> None:
        super().__init__(
            name="description_grounded",
            tool_name_weight=0.2,
            tool_desc_weight=0.7,
            arg_name_weight=0.2,
            arg_desc_weight=0.8,
            deprecated_penalty=0.35,
            enforce_contract_compatibility=True,
            honor_deprecation_status=True,
        )


class DocumentRetrievalRerankAgent(BaseAgent):
    def __init__(
        self,
        *,
        name: str = "doc_retrieval_rerank",
        shortlist_size: int = 3,
        retrieval_floor: float = 0.04,
        execute_floor: float = 0.35,
        deprecation_penalty: float = 0.30,
    ) -> None:
        super().__init__(name=name)
        self.shortlist_size = shortlist_size
        self.retrieval_floor = retrieval_floor
        self.execute_floor = execute_floor
        self.deprecation_penalty = deprecation_penalty

    def predict(self, example: ViewExample) -> ToolCall:
        request_tokens = tokenize(example.case.request)
        ranked_tools = sorted(
            [
                (
                    self._retrieval_score(request_tokens, tool),
                    tool,
                )
                for tool in example.schema_view.tools
            ],
            key=lambda item: item[0],
            reverse=True,
        )
        best_retrieval, best_tool = ranked_tools[0]
        if best_retrieval < self.retrieval_floor:
            return ToolCall(control=ControlTag.ABSTAIN, confidence=0.05)

        shortlist = ranked_tools[: self.shortlist_size]
        reranked = sorted(
            [
                (
                    self._rerank_score(tool, retrieval_score, example.case.slot_values),
                    retrieval_score,
                    tool,
                )
                for retrieval_score, tool in shortlist
            ],
            key=lambda item: (item[0], item[1]),
            reverse=True,
        )
        best_score, _, best_tool = reranked[0]
        second_score = reranked[1][0] if len(reranked) > 1 else 0.0

        grounding = self._ground_arguments(best_tool, example.case.slot_values)
        confidence = max(min(best_score - second_score, 1.0), 0.05)

        if best_tool.status == "deprecated":
            return ToolCall(control=ControlTag.ABSTAIN, confidence=confidence)
        if grounding["contract_mismatch"]:
            return ToolCall(control=ControlTag.ASK_CLARIFICATION, confidence=confidence)
        if grounding["missing_required"]:
            return ToolCall(control=ControlTag.ASK_CLARIFICATION, confidence=confidence)
        if best_score < self.execute_floor:
            return ToolCall(control=ControlTag.ABSTAIN, confidence=confidence)
        return ToolCall(
            control=ControlTag.EXECUTE,
            rendered_tool_name=best_tool.rendered_name,
            arguments=grounding["arguments"],
            confidence=confidence,
        )

    def _retrieval_score(self, request_tokens: set[str], tool) -> float:
        name_tokens = tokenize(tool.rendered_name.replace(".", " ").replace("_", " "))
        desc_tokens = tokenize(tool.description)
        arg_name_tokens = set().union(*(tokenize(argument.rendered_name.replace("_", " ")) for argument in tool.arguments))
        arg_desc_tokens = set().union(*(tokenize(argument.description) for argument in tool.arguments))
        full_doc_tokens = name_tokens | desc_tokens | arg_name_tokens | arg_desc_tokens
        return (
            0.20 * _overlap_score(request_tokens, name_tokens)
            + 0.40 * _overlap_score(request_tokens, desc_tokens)
            + 0.15 * _overlap_score(request_tokens, arg_name_tokens)
            + 0.15 * _overlap_score(request_tokens, arg_desc_tokens)
            + 0.10 * _overlap_score(request_tokens, full_doc_tokens)
        )

    def _rerank_score(self, tool, retrieval_score: float, slot_values: dict[str, object]) -> float:
        grounding = self._ground_arguments(tool, slot_values)
        required_arguments = [argument for argument in tool.arguments if argument.required]
        optional_arguments = [argument for argument in tool.arguments if not argument.required]
        required_coverage = grounding["matched_required"] / max(len(required_arguments), 1)
        optional_coverage = grounding["matched_optional"] / max(len(optional_arguments), 1) if optional_arguments else 0.0
        mismatch_penalty = 0.35 if grounding["contract_mismatch"] else 0.0
        status_penalty = self.deprecation_penalty if tool.status == "deprecated" else 0.0
        return (
            0.55 * retrieval_score
            + 0.30 * required_coverage
            + 0.10 * optional_coverage
            - mismatch_penalty
            - status_penalty
        )

    def _ground_arguments(self, tool, slot_values: dict[str, object]) -> dict[str, object]:
        arguments: dict[str, object] = {}
        used_slots: set[str] = set()
        matched_required = 0
        matched_optional = 0
        missing_required = False
        contract_mismatch = False
        for argument in tool.arguments:
            slot_name, slot_score = self._match_slot(argument, slot_values, used_slots)
            if slot_name is None:
                if argument.required:
                    missing_required = True
                continue
            if slot_score <= 0.0:
                if argument.required:
                    missing_required = True
                continue
            value = slot_values[slot_name]
            if not _slot_compatible(argument, value):
                contract_mismatch = True
                continue
            used_slots.add(slot_name)
            arguments[argument.rendered_name] = value
            if argument.required:
                matched_required += 1
            else:
                matched_optional += 1
        return {
            "arguments": arguments,
            "matched_required": matched_required,
            "matched_optional": matched_optional,
            "missing_required": missing_required,
            "contract_mismatch": contract_mismatch,
        }

    def _match_slot(
        self,
        argument: RenderedArgument,
        slot_values: dict[str, object],
        used_slots: set[str],
    ) -> tuple[str | None, float]:
        field_tokens = (
            tokenize(argument.rendered_name.replace("_", " "))
            | tokenize(argument.description)
            | tokenize(argument.canonical_name.replace("_", " "))
        )
        best_slot = None
        best_score = 0.0
        for slot_name, slot_value in slot_values.items():
            if slot_name in used_slots:
                continue
            slot_tokens = tokenize(slot_name.replace("_", " "))
            score = 0.8 * _overlap_score(slot_tokens, field_tokens)
            if isinstance(slot_value, str):
                value_tokens = tokenize(slot_value.replace("_", " "))
                score += 0.2 * _overlap_score(value_tokens, field_tokens)
            if score > best_score:
                best_slot = slot_name
                best_score = score
        return best_slot, best_score


def _slot_compatible(argument: RenderedArgument, value: object) -> bool:
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
