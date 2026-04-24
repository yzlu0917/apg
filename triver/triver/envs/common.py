from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import random
import re
from typing import Any, Protocol


@dataclass(frozen=True)
class TraceEvaluation:
    trace: list[str]
    valid_prefix_length: int
    invalid_transition_index: int | None
    transition_validity: list[bool]
    terminal: bool
    final_answer: Any
    success: bool

    @property
    def prefix_invalid(self) -> bool:
        return self.invalid_transition_index is not None


def perturb_new_integer_token(
    previous_line: str,
    current_line: str,
    rng: random.Random,
    deltas: tuple[int, ...] = (-2, -1, 1, 2),
) -> str | None:
    current_matches = list(re.finditer(r"-?\d+", current_line))
    if not current_matches:
        return None

    previous_counts = Counter(match.group(0) for match in re.finditer(r"-?\d+", previous_line))
    target_index = len(current_matches) - 1
    for index, match in enumerate(current_matches):
        token = match.group(0)
        if previous_counts[token] > 0:
            previous_counts[token] -= 1
            continue
        target_index = index
        break

    replacement = str(int(current_matches[target_index].group(0)) + rng.choice(deltas))
    start, end = current_matches[target_index].span()
    return f"{current_line[:start]}{replacement}{current_line[end:]}"


class ExactCheckerEnv(Protocol):
    name: str

    def generate_sample(self, rng) -> Any:
        ...

    def problem_text(self, sample: Any) -> str:
        ...

    def target_text(self, sample: Any) -> str:
        ...

    def sample_from_record(self, problem: str, target: str) -> Any:
        ...

    def initial_trace(self, sample: Any) -> list[str]:
        ...

    def build_solver_messages(
        self,
        sample: Any,
        prefix_lines: list[str],
        action: str,
        prompt_style: str = "default",
    ) -> tuple[list[dict[str, str]], list[str]]:
        ...

    def extract_trace_lines(self, text: str) -> list[str]:
        ...

    def is_terminal_line(self, line: str) -> bool:
        ...

    def check_trace(self, trace: list[str], sample: Any) -> TraceEvaluation:
        ...

    def prefix_invalidity_risk(self, trace: list[str], sample: Any) -> float:
        ...

    def make_recoverable_prefix(
        self,
        prefix_lines: list[str],
        sample: Any,
        rng,
        recoverable_style: str = "default",
    ) -> list[str] | None:
        ...
