from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any
from typing import Sequence

from .benchmark import BenchmarkSuite, ViewExample
from .schema import CanonicalAction, ControlTag, ShiftKind, SplitTag, ToolCall

TEMPORAL_BUNDLE_RE = re.compile(
    r"^\s*"
    r"(?P<datetime>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})?)"
    r"\s+"
    r"(?P<timezone>(?:[A-Za-z_+-]+/[A-Za-z0-9_+-]+)|(?:UTC[+-]\d{2}:\d{2}))"
    r"\s*$"
)
GRAPH_EDGE_BUNDLE_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\[(.*?)\]")


@dataclass(frozen=True)
class CanonicalizedPrediction:
    action: CanonicalAction
    contract_ok: bool
    errors: tuple[str, ...]


@dataclass(frozen=True)
class EvalRecord:
    agent_name: str
    case_id: str
    view_id: str
    transform_name: str
    shift_kind: ShiftKind
    split_tag: str
    admissible: bool
    contract_ok: bool
    confidence: float
    predicted_action: CanonicalAction
    expected_actions: tuple[CanonicalAction, ...]
    errors: tuple[str, ...]
    raw_call: ToolCall

    def to_dict(self, tool_lookup) -> dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "case_id": self.case_id,
            "view_id": self.view_id,
            "transform_name": self.transform_name,
            "shift_kind": self.shift_kind.value,
            "split_tag": self.split_tag,
            "admissible": self.admissible,
            "contract_ok": self.contract_ok,
            "confidence": self.confidence,
            "predicted_action": self.predicted_action.to_dict(),
            "predicted_fingerprint": self.predicted_action.fingerprint(tool_lookup),
            "expected_actions": [action.to_dict() for action in self.expected_actions],
            "errors": list(self.errors),
            "raw_call": self.raw_call.to_dict(),
        }


def canonicalize_prediction(
    example: ViewExample,
    tool_lookup,
    call: ToolCall,
) -> CanonicalizedPrediction:
    if call.control != ControlTag.EXECUTE:
        return CanonicalizedPrediction(
            action=CanonicalAction(control=call.control),
            contract_ok=True,
            errors=(),
        )
    if call.rendered_tool_name is None:
        return CanonicalizedPrediction(
            action=CanonicalAction(control=ControlTag.ABSTAIN),
            contract_ok=False,
            errors=("execute call missing rendered tool name",),
        )
    tool = example.schema_view.tool_by_name(call.rendered_tool_name)
    if tool is None:
        return CanonicalizedPrediction(
            action=CanonicalAction(control=ControlTag.ABSTAIN),
            contract_ok=False,
            errors=(f"unknown rendered tool {call.rendered_tool_name}",),
        )
    errors: list[str] = []
    canonical_arguments: dict[str, Any] = {}
    canonical_tool = tool_lookup[tool.canonical_tool_id]
    resolved_arguments = _resolve_temporal_argument_bundles(call.arguments, tool, canonical_tool)
    for rendered_argument in tool.arguments:
        if rendered_argument.rendered_name in resolved_arguments:
            value = resolved_arguments[rendered_argument.rendered_name]
        else:
            value = None
        if rendered_argument.canonical_name == "edge_descriptor":
            parsed_bundle = _parse_graph_edge_bundle(value)
            if parsed_bundle:
                for bundle_name, bundle_value in parsed_bundle.items():
                    try:
                        canonical_argument = canonical_tool.argument(bundle_name)
                    except KeyError:
                        continue
                    valid, error = canonical_argument.validate(bundle_value)
                    if error is not None:
                        errors.append(error)
                    if valid:
                        canonical_arguments[bundle_name] = canonical_argument.normalize(bundle_value)
                continue
        try:
            canonical_argument = canonical_tool.argument(rendered_argument.canonical_name)
        except KeyError:
            continue
        valid, error = canonical_argument.validate(value)
        if error is not None:
            errors.append(error)
        if valid:
            canonical_arguments[rendered_argument.canonical_name] = canonical_argument.normalize(value)
    extra_arguments = set(resolved_arguments) - {argument.rendered_name for argument in tool.arguments}
    if extra_arguments:
        errors.append(f"unknown arguments: {sorted(extra_arguments)}")
    return CanonicalizedPrediction(
        action=CanonicalAction(
            control=ControlTag.EXECUTE,
            tool_id=tool.canonical_tool_id,
            arguments=canonical_arguments,
        ),
        contract_ok=not errors,
        errors=tuple(errors),
    )


def _parse_graph_edge_bundle(value: Any) -> dict[str, Any]:
    if not isinstance(value, str):
        return {}
    normalized: dict[str, Any] = {}
    for raw_key, raw_payload in GRAPH_EDGE_BUNDLE_RE.findall(value):
        key = raw_key.strip().lower()
        payload = raw_payload.strip()
        if key in {"graph", "graph_name"}:
            normalized["graph_name"] = payload
        elif key in {"firstnode", "node1", "vertex1"}:
            normalized["node1"] = payload
        elif key in {"secondnode", "node2", "vertex2"}:
            normalized["node2"] = payload
    return normalized


def _resolve_temporal_argument_bundles(call_arguments, rendered_tool, canonical_tool):
    resolved = dict(call_arguments)
    timezone_rendered_name = None
    timezone_value = None
    timezone_argument = None
    for rendered_argument in rendered_tool.arguments:
        if rendered_argument.canonical_name == "timezone":
            timezone_rendered_name = rendered_argument.rendered_name
            timezone_value = resolved.get(timezone_rendered_name)
            timezone_argument = canonical_tool.argument("timezone")
            break
    if timezone_rendered_name is None:
        return resolved

    for rendered_argument in rendered_tool.arguments:
        canonical_name = rendered_argument.canonical_name
        if not canonical_name.endswith("_datetime"):
            continue
        raw_value = resolved.get(rendered_argument.rendered_name)
        if not isinstance(raw_value, str):
            continue
        match = TEMPORAL_BUNDLE_RE.match(raw_value.strip())
        if match is None:
            continue
        extracted_datetime = match.group("datetime")
        extracted_timezone = match.group("timezone")
        if timezone_value is not None:
            normalized_timezone = timezone_argument.normalize(timezone_value)
            if normalized_timezone != timezone_argument.normalize(extracted_timezone):
                continue
        else:
            resolved[timezone_rendered_name] = extracted_timezone
            timezone_value = extracted_timezone
        resolved[rendered_argument.rendered_name] = extracted_datetime
    return resolved


def _is_admissible(
    prediction: CanonicalizedPrediction,
    example: ViewExample,
    tool_lookup,
) -> bool:
    predicted_fingerprint = prediction.action.fingerprint(tool_lookup)
    return any(
        expected.fingerprint(tool_lookup) == predicted_fingerprint
        for expected in example.admissible_actions
    )


def evaluate_agent(
    agent,
    suite: BenchmarkSuite,
    *,
    examples: Sequence[ViewExample] | None = None,
) -> tuple[list[EvalRecord], dict[str, Any]]:
    records: list[EvalRecord] = []
    evaluation_examples = suite.examples if examples is None else tuple(examples)
    for example in evaluation_examples:
        raw_call = agent.predict(example)
        canonicalized = canonicalize_prediction(example, suite.tool_lookup, raw_call)
        admissible = _is_admissible(canonicalized, example, suite.tool_lookup)
        records.append(
            EvalRecord(
                agent_name=agent.name,
                case_id=example.case.case_id,
                view_id=example.schema_view.view_id,
                transform_name=example.schema_view.transform_name,
                shift_kind=example.schema_view.shift_kind,
                split_tag=example.split_tag.value,
                admissible=admissible,
                contract_ok=canonicalized.contract_ok,
                confidence=raw_call.confidence,
                predicted_action=canonicalized.action,
                expected_actions=example.admissible_actions,
                errors=canonicalized.errors,
                raw_call=raw_call,
            )
        )
    return records, summarize_records(records, suite.tool_lookup)


def summarize_records(records: list[EvalRecord], tool_lookup) -> dict[str, Any]:
    main_records = [record for record in records if record.shift_kind != ShiftKind.IMPOSSIBLE]
    core_records = [record for record in main_records if record.split_tag == SplitTag.UNAMBIGUOUS_CORE.value]
    ambiguous_records = [record for record in main_records if record.split_tag == SplitTag.AMBIGUOUS.value]

    metrics = _compute_metrics(core_records, tool_lookup)
    control_distribution = Counter(record.predicted_action.control.value for record in core_records)
    impossible_summary = {
        "count": len([record for record in records if record.shift_kind == ShiftKind.IMPOSSIBLE]),
        "impossible_CAA": _mean_or_none(record.admissible for record in records if record.shift_kind == ShiftKind.IMPOSSIBLE),
    }
    ambiguous_summary = {
        "count": len(ambiguous_records),
        "metrics": _compute_metrics(ambiguous_records, tool_lookup),
    }
    return {
        "metrics": metrics,
        "counts": {
            "core": len(core_records),
            "ambiguous": len(ambiguous_records),
            "impossible": impossible_summary["count"],
        },
        "control_distribution": dict(control_distribution),
        "ambiguous": ambiguous_summary,
        "impossible": impossible_summary,
    }


def nos_at_coverage(records: list[EvalRecord], target_coverage: float) -> float:
    negative_records = [
        record
        for record in records
        if record.shift_kind == ShiftKind.NEGATIVE_NEAR_ORBIT and record.split_tag == SplitTag.UNAMBIGUOUS_CORE.value
    ]
    if not negative_records:
        return 0.0
    count = max(1, round(len(negative_records) * target_coverage))
    ranked = sorted(negative_records, key=lambda record: record.confidence, reverse=True)
    selected = ranked[:count]
    return _mean(record.admissible for record in selected)


def dump_json(path: str, payload: Any) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def _compute_metrics(records: list[EvalRecord], tool_lookup) -> dict[str, float | None]:
    grouped_positive = defaultdict(list)
    for record in records:
        if record.shift_kind == ShiftKind.POSITIVE_ORBIT:
            grouped_positive[record.case_id].append(record)

    poc_values = []
    for case_records in grouped_positive.values():
        if not case_records:
            continue
        all_admissible = all(record.admissible for record in case_records)
        same_action = len(
            {
                record.predicted_action.fingerprint(tool_lookup)
                for record in case_records
            }
        ) == 1
        poc_values.append(1.0 if all_admissible and same_action else 0.0)

    return {
        "CAA_overall": _mean_or_none(record.admissible for record in records),
        "CAA_clean": _mean_or_none(record.admissible for record in records if record.shift_kind == ShiftKind.CLEAN),
        "CAA_positive": _mean_or_none(record.admissible for record in records if record.shift_kind == ShiftKind.POSITIVE_ORBIT),
        "CAA_negative": _mean_or_none(record.admissible for record in records if record.shift_kind == ShiftKind.NEGATIVE_NEAR_ORBIT),
        "POC": _mean_or_none(poc_values),
        "NOS": _mean_or_none(record.admissible for record in records if record.shift_kind == ShiftKind.NEGATIVE_NEAR_ORBIT),
        "coverage": _mean_or_none(record.predicted_action.control != ControlTag.ABSTAIN for record in records),
        "negative_coverage": _mean_or_none(
            record.predicted_action.control != ControlTag.ABSTAIN
            for record in records
            if record.shift_kind == ShiftKind.NEGATIVE_NEAR_ORBIT
        ),
        "selective_risk": _selective_risk(records),
        "contract_validity": _mean_or_none(record.contract_ok for record in records),
    }


def _mean(values) -> float:
    items = list(values)
    if not items:
        return 0.0
    return sum(float(item) for item in items) / len(items)


def _mean_or_none(values) -> float | None:
    items = list(values)
    if not items:
        return None
    return _mean(items)


def _selective_risk(records: list[EvalRecord]) -> float:
    covered = [record for record in records if record.predicted_action.control != ControlTag.ABSTAIN]
    if not covered:
        return 0.0
    return 1.0 - _mean(record.admissible for record in covered)
