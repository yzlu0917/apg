from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from .schema import ControlTag, ShiftKind, SplitTag


def classify_serialized_record(record: dict[str, Any]) -> dict[str, Any]:
    predicted_action = record["predicted_action"]
    expected_actions = record["expected_actions"]
    predicted_control = predicted_action["control"]
    expected_controls = sorted({action["control"] for action in expected_actions})
    expected_execute_actions = [action for action in expected_actions if action["control"] == ControlTag.EXECUTE.value]

    if record["admissible"]:
        bucket = "correct_execute" if predicted_control == ControlTag.EXECUTE.value else "correct_non_execute"
        group = "correct"
    elif predicted_control != ControlTag.EXECUTE.value:
        if expected_execute_actions:
            bucket = f"missed_execute_{predicted_control}"
        else:
            bucket = "wrong_non_execute_policy"
        group = "control_policy_error"
    elif not record["contract_ok"]:
        bucket = "invalid_execute_contract"
        group = "argument_or_contract_error"
    else:
        expected_tool_ids = {action.get("tool_id") for action in expected_execute_actions}
        if predicted_action.get("tool_id") in expected_tool_ids:
            bucket = "argument_grounding_error"
            group = "argument_or_contract_error"
        else:
            bucket = "wrong_tool_choice"
            group = "tool_choice_error"

    return {
        "bucket": bucket,
        "group": group,
        "predicted_control": predicted_control,
        "expected_controls": expected_controls,
        "expected_execute": bool(expected_execute_actions),
        "predicted_tool_id": predicted_action.get("tool_id"),
        "expected_tool_ids": sorted(tool_id for tool_id in {action.get("tool_id") for action in expected_execute_actions} if tool_id),
    }


def summarize_serialized_records(
    records: list[dict[str, Any]],
    *,
    case_to_family: dict[str, str] | None = None,
    max_examples_per_bucket: int = 3,
) -> dict[str, Any]:
    case_to_family = case_to_family or {}
    scoped_records = [
        record
        for record in records
        if record["split_tag"] == SplitTag.UNAMBIGUOUS_CORE.value and record["shift_kind"] != ShiftKind.IMPOSSIBLE.value
    ]
    return _summarize_scope(
        scoped_records,
        case_to_family=case_to_family,
        max_examples_per_bucket=max_examples_per_bucket,
        include_examples=True,
        include_breakdowns=True,
    )


def _summarize_scope(
    records: list[dict[str, Any]],
    *,
    case_to_family: dict[str, str],
    max_examples_per_bucket: int,
    include_examples: bool,
    include_breakdowns: bool,
) -> dict[str, Any]:
    total = len(records)
    control_distribution = Counter()
    bucket_counts = Counter()
    group_counts = Counter()
    expected_execute_count = 0
    representative_examples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    policy_mismatch_counts = Counter()

    by_transform_records: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_shift_kind_records: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_family_records: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for record in records:
        diagnosis = classify_serialized_record(record)
        control_distribution[diagnosis["predicted_control"]] += 1
        bucket_counts[diagnosis["bucket"]] += 1
        group_counts[diagnosis["group"]] += 1
        expected_execute_count += int(diagnosis["expected_execute"])

        if diagnosis["bucket"] == "wrong_non_execute_policy":
            detail = f"pred={diagnosis['predicted_control']}|expected={'+'.join(diagnosis['expected_controls'])}"
            policy_mismatch_counts[detail] += 1

        if diagnosis["group"] != "correct" and len(representative_examples[diagnosis["bucket"]]) < max_examples_per_bucket:
            representative_examples[diagnosis["bucket"]].append(
                {
                    "case_id": record["case_id"],
                    "view_id": record["view_id"],
                    "transform_name": record["transform_name"],
                    "shift_kind": record["shift_kind"],
                    "predicted_action": record["predicted_action"],
                    "expected_actions": record["expected_actions"],
                    "errors": record["errors"],
                }
            )

        by_transform_records[record["transform_name"]].append(record)
        by_shift_kind_records[record["shift_kind"]].append(record)
        family_id = case_to_family.get(record["case_id"])
        if family_id is not None:
            by_family_records[family_id].append(record)

    expected_non_execute_count = total - expected_execute_count
    summary = {
        "count": total,
        "admissible_rate": _safe_rate(group_counts["correct"], total),
        "execute_rate": _safe_rate(control_distribution[ControlTag.EXECUTE.value], total),
        "ask_clarification_rate": _safe_rate(control_distribution[ControlTag.ASK_CLARIFICATION.value], total),
        "abstain_rate": _safe_rate(control_distribution[ControlTag.ABSTAIN.value], total),
        "expected_execute_rate": _safe_rate(expected_execute_count, total),
        "expected_execute_count": expected_execute_count,
        "expected_non_execute_count": expected_non_execute_count,
        "control_distribution": dict(control_distribution),
        "bucket_counts": dict(bucket_counts),
        "bucket_rates": _rate_dict(bucket_counts, total),
        "group_counts": dict(group_counts),
        "group_rates": _rate_dict(group_counts, total),
        "policy_mismatch_counts": dict(policy_mismatch_counts),
    }

    if include_examples:
        summary["representative_examples"] = dict(representative_examples)

    if include_breakdowns:
        summary["by_transform"] = {
            key: _summarize_scope(
                value,
                case_to_family={},
                max_examples_per_bucket=max_examples_per_bucket,
                include_examples=False,
                include_breakdowns=False,
            )
            for key, value in sorted(by_transform_records.items())
        }
        summary["by_shift_kind"] = {
            key: _summarize_scope(
                value,
                case_to_family={},
                max_examples_per_bucket=max_examples_per_bucket,
                include_examples=False,
                include_breakdowns=False,
            )
            for key, value in sorted(by_shift_kind_records.items())
        }
        if by_family_records:
            summary["by_family"] = {
                key: _summarize_scope(
                    value,
                    case_to_family={},
                    max_examples_per_bucket=max_examples_per_bucket,
                    include_examples=False,
                    include_breakdowns=False,
                )
                for key, value in sorted(by_family_records.items())
            }
        else:
            summary["by_family"] = {}
    return summary


def _rate_dict(counter: Counter, total: int) -> dict[str, float]:
    return {key: _safe_rate(value, total) for key, value in counter.items()}


def _safe_rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator
