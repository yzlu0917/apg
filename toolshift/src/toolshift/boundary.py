from __future__ import annotations

from dataclasses import replace
from typing import Sequence

from .benchmark import BenchmarkSuite, ViewExample
from .eval import EvalRecord
from .schema import ControlTag, SchemaView, ShiftKind


def build_impossible_shadow_examples(
    suite: BenchmarkSuite,
    *,
    examples: Sequence[ViewExample] | None = None,
) -> tuple[ViewExample, ...]:
    source_examples = tuple(suite.examples if examples is None else examples)
    clean_by_case = {
        example.case.case_id: example
        for example in source_examples
        if example.schema_view.shift_kind == ShiftKind.CLEAN
    }
    shadows: list[ViewExample] = []
    for example in source_examples:
        if example.schema_view.shift_kind != ShiftKind.NEGATIVE_NEAR_ORBIT:
            continue
        clean_example = clean_by_case.get(example.case.case_id)
        if clean_example is None:
            raise ValueError(f"missing clean view for impossible shadow case {example.case.case_id}")
        shadow_view = SchemaView(
            view_id=f"{example.case.case_id}::impossible_shadow_from_{example.schema_view.transform_name}",
            transform_name=f"impossible_shadow_from_{example.schema_view.transform_name}",
            shift_kind=ShiftKind.IMPOSSIBLE,
            tools=clean_example.schema_view.tools,
            notes=(
                f"Counterfactual impossible shadow: hidden backend semantics now follow "
                f"`{example.schema_view.transform_name}`, but the visible schema stays identical to clean."
            ),
        )
        shadows.append(
            replace(
                example,
                schema_view=shadow_view,
                notes=(
                    f"{example.notes} Impossible shadow derived from clean surface; "
                    "used only for boundary evidence."
                ).strip(),
            )
        )
    return tuple(shadows)


def summarize_impossible_shadow_records(records: Sequence[EvalRecord]) -> dict[str, float]:
    impossible_records = [record for record in records if record.shift_kind == ShiftKind.IMPOSSIBLE]
    if not impossible_records:
        return {
            "count": 0.0,
            "impossible_CAA": 0.0,
            "execute_rate": 0.0,
            "abstain_rate": 0.0,
            "ask_clarification_rate": 0.0,
        }
    total = float(len(impossible_records))
    return {
        "count": total,
        "impossible_CAA": sum(1.0 for record in impossible_records if record.admissible) / total,
        "execute_rate": sum(1.0 for record in impossible_records if record.predicted_action.control == ControlTag.EXECUTE) / total,
        "abstain_rate": sum(1.0 for record in impossible_records if record.predicted_action.control == ControlTag.ABSTAIN) / total,
        "ask_clarification_rate": sum(1.0 for record in impossible_records if record.predicted_action.control == ControlTag.ASK_CLARIFICATION) / total,
    }
