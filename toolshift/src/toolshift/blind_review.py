from __future__ import annotations

from typing import Sequence

from .benchmark import BenchmarkSuite, ViewExample
from .eval import EvalRecord, summarize_records
from .schema import ShiftKind, SplitTag


def core_training_examples(
    suite: BenchmarkSuite,
    *,
    excluded_cases: set[str] | None = None,
) -> list[ViewExample]:
    excluded_cases = excluded_cases or set()
    return [
        example
        for example in suite.examples
        if example.split_tag == SplitTag.UNAMBIGUOUS_CORE
        and example.schema_view.shift_kind != ShiftKind.IMPOSSIBLE
        and example.case.case_id not in excluded_cases
    ]


def primary_family_groups(suite: BenchmarkSuite) -> dict[str, set[str]]:
    groups: dict[str, set[str]] = {}
    for case in suite.cases:
        family_id = case.family_tag or case.primary_action.tool_id
        if family_id is None:
            continue
        groups.setdefault(family_id, set()).add(case.case_id)
    return groups


def summarize_records_by_family(
    suite: BenchmarkSuite,
    records: Sequence[EvalRecord],
) -> dict[str, dict[str, float | int | None]]:
    family_groups = primary_family_groups(suite)
    summaries: dict[str, dict[str, float | int | None]] = {}
    for family_id, case_ids in sorted(family_groups.items()):
        family_records = [record for record in records if record.case_id in case_ids]
        summary = summarize_records(family_records, suite.tool_lookup)
        summaries[family_id] = {
            "case_count": len(case_ids),
            "view_count": len(family_records),
            "CAA": summary["metrics"]["CAA_overall"],
            "CAA_positive": summary["metrics"]["CAA_positive"],
            "NOS": summary["metrics"]["NOS"],
            "POC": summary["metrics"]["POC"],
            "coverage": summary["metrics"]["coverage"],
        }
    return summaries
