from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class TraceExample:
    trace_id: str
    quartet_id: str
    problem_id: str
    domain: str
    verbalizer_id: str
    audited_locus: int
    counterfactual_role: str
    process_variant: str
    answer_variant: str
    is_valid_process: bool
    answer_is_correct: bool
    problem_text: str
    step_texts: list[str]
    final_answer_line: str
    masked_answer_line: str
    trace_text: str
    masked_trace_text: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExternalStepExample:
    example_id: str
    dataset_name: str
    dataset_split: str
    domain: str
    source_problem_id: str
    problem_text: str
    step_texts: list[str]
    trace_text: str
    final_answer_correct: bool | None
    raw_label: Any
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> dict[str, Any]:
        return asdict(self)
