from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any

from .benchmark import BenchmarkSuite, ViewExample
from .eval import EvalRecord
from .reliability import summarize_benchmark_structure
from .schema import CanonicalAction, ControlTag, ShiftKind, SplitTag, ToolCall

POLICY_VARIANTS = (
    "canonical",
    "single_action_only",
    "ask_only_negative",
    "abstain_only_negative",
)


def apply_policy_variant(
    suite: BenchmarkSuite,
    records: list[EvalRecord],
    *,
    variant: str,
) -> tuple[list[EvalRecord], dict[str, Any]]:
    if variant not in POLICY_VARIANTS:
        raise ValueError(f"unknown policy variant: {variant}")
    example_lookup = {example.schema_view.view_id: example for example in suite.examples}
    updated_records: list[EvalRecord] = []
    excluded_view_count = 0
    relabeled_negative_view_count = 0
    for record in records:
        example = example_lookup[record.view_id]
        split_tag = example.split_tag
        admissible_actions = example.admissible_actions
        if variant == "single_action_only" and len(admissible_actions) > 1:
            split_tag = SplitTag.AMBIGUOUS
            excluded_view_count += 1
        elif record.shift_kind == ShiftKind.NEGATIVE_NEAR_ORBIT and len(admissible_actions) > 1:
            if variant == "ask_only_negative":
                admissible_actions = tuple(
                    action for action in admissible_actions if action.control == ControlTag.ASK_CLARIFICATION
                )
                relabeled_negative_view_count += 1
            elif variant == "abstain_only_negative":
                admissible_actions = tuple(action for action in admissible_actions if action.control == ControlTag.ABSTAIN)
                relabeled_negative_view_count += 1
        predicted_fingerprint = record.predicted_action.fingerprint(suite.tool_lookup)
        admissible = any(action.fingerprint(suite.tool_lookup) == predicted_fingerprint for action in admissible_actions)
        updated_records.append(
            EvalRecord(
                agent_name=record.agent_name,
                case_id=record.case_id,
                view_id=record.view_id,
                transform_name=record.transform_name,
                shift_kind=record.shift_kind,
                split_tag=split_tag.value,
                admissible=admissible,
                contract_ok=record.contract_ok,
                confidence=record.confidence,
                predicted_action=record.predicted_action,
                expected_actions=admissible_actions,
                errors=record.errors,
                raw_call=ToolCall(
                    control=record.raw_call.control,
                    rendered_tool_name=record.raw_call.rendered_tool_name,
                    arguments=dict(record.raw_call.arguments),
                    confidence=record.raw_call.confidence,
                    metadata=dict(record.raw_call.metadata),
                ),
            )
        )
    return updated_records, {
        "excluded_view_count": excluded_view_count,
        "relabeled_negative_view_count": relabeled_negative_view_count,
    }


def summarize_protocol_records(records: list[EvalRecord], tool_lookup) -> dict[str, Any]:
    main_records = [record for record in records if record.shift_kind != ShiftKind.IMPOSSIBLE]
    core_records = [record for record in main_records if record.split_tag == SplitTag.UNAMBIGUOUS_CORE.value]
    ambiguous_records = [record for record in main_records if record.split_tag == SplitTag.AMBIGUOUS.value]
    metrics = _compute_metrics(core_records, tool_lookup)
    return {
        "metrics": metrics,
        "counts": {
            "core": len(core_records),
            "ambiguous": len(ambiguous_records),
            "impossible": len([record for record in records if record.shift_kind == ShiftKind.IMPOSSIBLE]),
        },
        "control_distribution": dict(Counter(record.predicted_action.control.value for record in core_records)),
    }


def summarize_benchmark_protocol(payload: dict[str, Any]) -> dict[str, Any]:
    structure = summarize_benchmark_structure(payload)
    multi_action_views = sum(
        int(size) * count for size, count in []  # pragma: no cover
    )
    del multi_action_views
    action_histogram = structure["action_size_histogram"]
    total_views = structure["counts"]["views"]
    multi_action_view_count = sum(
        count for action_size, count in action_histogram.items() if int(action_size) > 1
    )
    return {
        **structure,
        "multi_action_view_fraction": multi_action_view_count / total_views,
        "multi_action_negative_fraction": (
            structure["multi_action_negative"]
            / max(1, sum(
                count
                for key, count in structure["shift_action_histogram"].items()
                if key.startswith(f"{ShiftKind.NEGATIVE_NEAR_ORBIT.value}:")
            ))
        ),
    }


def _compute_metrics(records: list[EvalRecord], tool_lookup) -> dict[str, float | None]:
    grouped_positive: dict[str, list[EvalRecord]] = defaultdict(list)
    for record in records:
        if record.shift_kind == ShiftKind.POSITIVE_ORBIT:
            grouped_positive[record.case_id].append(record)
    poc_values: list[float] = []
    for case_records in grouped_positive.values():
        if not case_records:
            continue
        all_admissible = all(record.admissible for record in case_records)
        same_action = len({record.predicted_action.fingerprint(tool_lookup) for record in case_records}) == 1
        poc_values.append(1.0 if all_admissible and same_action else 0.0)
    return {
        "CAA_overall": _mean_or_none(record.admissible for record in records),
        "CAA_clean": _mean_or_none(record.admissible for record in records if record.shift_kind == ShiftKind.CLEAN),
        "CAA_positive": _mean_or_none(record.admissible for record in records if record.shift_kind == ShiftKind.POSITIVE_ORBIT),
        "CAA_negative": _mean_or_none(
            record.admissible for record in records if record.shift_kind == ShiftKind.NEGATIVE_NEAR_ORBIT
        ),
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


def _mean_or_none(values) -> float | None:
    items = list(values)
    if not items:
        return None
    return mean(float(item) for item in items)


def _selective_risk(records: list[EvalRecord]) -> float:
    covered = [record for record in records if record.predicted_action.control != ControlTag.ABSTAIN]
    if not covered:
        return 0.0
    return 1.0 - mean(float(record.admissible) for record in covered)
