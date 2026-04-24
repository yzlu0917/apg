from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from civic_prm.external_datasets import load_processbench_records
from civic_prm.schema import ExternalStepExample, TraceExample


_ANSWER_LINE_RE = re.compile(
    r"(?i)\b(the answer is|therefore[, ]+the answer is|thus[, ]+the answer is|so[, ]+the answer is)\b.*"
)
_FINAL_ANSWER_RE = re.compile(r"(?i)\b(?:the\s+)?final answer\b\s*(?:is|:)?")
_INLINE_TERMINAL_ANSWER_RE = re.compile(
    r"(?i)\b(?:is|are|=)\s*(\\\([^\\n]*?\\\)|\$[^\n$]*\$|[-+]?\d[\d,./%]*|\\boxed\{(?:[^{}]|\{[^{}]*\})*\})\s*(?=[.)\]]?\s*$)"
)
_EQUALS_TERMINAL_RE = re.compile(r"(?i)(=\s*)([-+]?\d[\d,./%]*)(\s*$)")


def mask_answer_surface(text: str) -> str:
    needle = r"\boxed{"
    pieces: list[str] = []
    cursor = 0
    while True:
        start = text.find(needle, cursor)
        if start < 0:
            pieces.append(text[cursor:])
            break
        pieces.append(text[cursor:start])
        brace_depth = 0
        index = start + len(needle)
        while index < len(text):
            char = text[index]
            if char == "{":
                brace_depth += 1
            elif char == "}":
                if brace_depth == 0:
                    index += 1
                    break
                brace_depth -= 1
            index += 1
        pieces.append("[ANSWER_MASK]")
        cursor = index
    return "".join(pieces)


def _mask_answer_surface(text: str) -> str:
    masked = mask_answer_surface(text)
    if _FINAL_ANSWER_RE.search(masked):
        masked = _FINAL_ANSWER_RE.sub("final answer is", masked)
        masked = _INLINE_TERMINAL_ANSWER_RE.sub("is [ANSWER_MASK]", masked)
    masked = _ANSWER_LINE_RE.sub(r"\1 [ANSWER_MASK]", masked)
    masked = _INLINE_TERMINAL_ANSWER_RE.sub("is [ANSWER_MASK]", masked)
    masked = _EQUALS_TERMINAL_RE.sub(r"\1[ANSWER_MASK]\3", masked)
    return masked


def _normalize_audited_locus(example: ExternalStepExample) -> int:
    raw = example.metadata.get("first_incorrect_step")
    if isinstance(raw, int) and 0 <= raw < len(example.step_texts):
        return raw
    return max(0, len(example.step_texts) - 1)


def normalize_processbench_examples(
    examples: list[ExternalStepExample],
) -> list[TraceExample]:
    records: list[TraceExample] = []
    for example in examples:
        is_valid_process = example.metadata.get("first_incorrect_step") is None
        answer_is_correct = bool(example.final_answer_correct)
        masked_steps = [_mask_answer_surface(step) for step in example.step_texts]
        records.append(
            TraceExample(
                trace_id=example.example_id,
                quartet_id=example.example_id,
                problem_id=example.source_problem_id,
                domain=example.domain,
                verbalizer_id=f"processbench_{example.dataset_split}",
                audited_locus=_normalize_audited_locus(example),
                counterfactual_role="observed",
                process_variant="valid" if is_valid_process else "invalid",
                answer_variant="correct" if answer_is_correct else "wrong",
                is_valid_process=is_valid_process,
                answer_is_correct=answer_is_correct,
                problem_text=example.problem_text,
                step_texts=example.step_texts,
                final_answer_line="",
                masked_answer_line="",
                trace_text="\n".join(example.step_texts),
                masked_trace_text="\n".join(masked_steps),
                metadata={
                    **example.metadata,
                    "source_dataset": example.dataset_name,
                    "source_split": example.dataset_split,
                    "source_example_id": example.example_id,
                },
            )
        )
    return records


def build_processbench_records(split_name: str = "all", limit: int | None = None) -> list[TraceExample]:
    examples = load_processbench_records(split_name=split_name, limit=limit)
    return normalize_processbench_examples(examples)


def save_processbench_records(records: list[TraceExample], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record.to_record(), ensure_ascii=False) + "\n")


def summarize_processbench_records(records: list[TraceExample]) -> dict[str, Any]:
    domain_counts = Counter(record.domain for record in records)
    split_counts = Counter(str(record.metadata.get("source_split")) for record in records)
    valid_counts = Counter(str(record.is_valid_process) for record in records)
    answer_counts = Counter(str(record.answer_is_correct) for record in records)
    audited_loci = [record.audited_locus for record in records]
    return {
        "num_records": len(records),
        "domains": dict(domain_counts),
        "source_splits": dict(split_counts),
        "is_valid_process": dict(valid_counts),
        "answer_is_correct": dict(answer_counts),
        "avg_num_steps": round(sum(len(record.step_texts) for record in records) / len(records), 4) if records else 0.0,
        "avg_audited_locus": round(sum(audited_loci) / len(audited_loci), 4) if audited_loci else 0.0,
    }
