from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from civic_prm.schema import ExternalStepExample


PROCESSBENCH_DATASET_ID = "Qwen/ProcessBench"
PRM800K_DATASET_ID = "tasksource/PRM800K"


def _load_hf_symbols():
    try:
        from datasets import get_dataset_split_names, load_dataset
    except ImportError as error:
        raise RuntimeError(
            "datasets is required for external dataset import; install the 'datasets' package in the active environment."
        ) from error
    return load_dataset, get_dataset_split_names


def _stable_problem_id(prefix: str, text: str) -> str:
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def _compose_trace(step_texts: list[str]) -> str:
    return "\n".join(step_texts)


def get_processbench_splits() -> list[str]:
    _, get_dataset_split_names = _load_hf_symbols()
    return list(get_dataset_split_names(PROCESSBENCH_DATASET_ID))


def _normalize_processbench_row(row: dict[str, Any], split_name: str) -> ExternalStepExample:
    step_texts = [str(step).strip() for step in row["steps"] if str(step).strip()]
    problem_text = str(row["problem"]).strip()
    raw_label = row.get("label")
    # ProcessBench uses -1 when all steps are correct; non-negative labels denote the first incorrect step.
    first_incorrect_step = raw_label if isinstance(raw_label, int) and raw_label >= 0 else None
    source_problem_id = str(row.get("id") or _stable_problem_id(split_name, problem_text))
    return ExternalStepExample(
        example_id=f"processbench-{source_problem_id}",
        dataset_name="processbench",
        dataset_split=split_name,
        domain=split_name,
        source_problem_id=source_problem_id,
        problem_text=problem_text,
        step_texts=step_texts,
        trace_text=_compose_trace(step_texts),
        final_answer_correct=bool(row["final_answer_correct"]),
        raw_label=raw_label,
        metadata={
            "hf_dataset_id": PROCESSBENCH_DATASET_ID,
            "generator": row.get("generator"),
            "first_incorrect_step": first_incorrect_step,
        },
    )


def load_processbench_records(split_name: str = "all", limit: int | None = None) -> list[ExternalStepExample]:
    load_dataset, _ = _load_hf_symbols()
    splits = get_processbench_splits() if split_name == "all" else [split_name]
    records: list[ExternalStepExample] = []
    remaining = limit
    for current_split in splits:
        dataset = load_dataset(PROCESSBENCH_DATASET_ID, split=current_split)
        rows = dataset if remaining is None else dataset.select(range(min(remaining, len(dataset))))
        normalized = [_normalize_processbench_row(row, current_split) for row in rows]
        records.extend(normalized)
        if remaining is not None:
            remaining -= len(normalized)
            if remaining <= 0:
                break
    return records


def _extract_prm800k_step(step_payload: dict[str, Any]) -> tuple[str | None, Any, Any]:
    completions = step_payload.get("completions") or []
    chosen_index = step_payload.get("chosen_completion")
    if isinstance(chosen_index, int) and 0 <= chosen_index < len(completions):
        completion = completions[chosen_index]
        return (
            str(completion.get("text", "")).strip() or None,
            completion.get("rating"),
            completion.get("flagged"),
        )
    human_completion = step_payload.get("human_completion")
    if isinstance(human_completion, str) and human_completion.strip():
        return human_completion.strip(), None, None
    return None, None, None


def _normalize_prm800k_row(row: dict[str, Any], split_name: str, row_index: int) -> ExternalStepExample:
    question = row.get("question") or {}
    label = row.get("label") or {}
    problem_text = str(question.get("problem", "")).strip()
    ground_truth_answer = question.get("ground_truth_answer")
    step_texts: list[str] = []
    chosen_ratings: list[Any] = []
    chosen_flagged: list[Any] = []
    for step_payload in label.get("steps", []):
        step_text, rating, flagged = _extract_prm800k_step(step_payload)
        if step_text is None:
            continue
        step_texts.append(step_text)
        chosen_ratings.append(rating)
        chosen_flagged.append(flagged)
    source_problem_id = _stable_problem_id("prm800k", problem_text)
    return ExternalStepExample(
        example_id=f"prm800k-{split_name}-{row_index:06d}",
        dataset_name="prm800k",
        dataset_split=split_name,
        domain="math",
        source_problem_id=source_problem_id,
        problem_text=problem_text,
        step_texts=step_texts,
        trace_text=_compose_trace(step_texts),
        final_answer_correct=None,
        raw_label=None,
        metadata={
            "hf_dataset_id": PRM800K_DATASET_ID,
            "ground_truth_answer": ground_truth_answer,
            "labeler": row.get("labeler"),
            "timestamp": row.get("timestamp"),
            "finish_reason": label.get("finish_reason"),
            "chosen_ratings": chosen_ratings,
            "chosen_flagged": chosen_flagged,
            "is_quality_control_question": row.get("is_quality_control_question"),
            "is_initial_screening_question": row.get("is_initial_screening_question"),
            "generation": row.get("generation"),
        },
    )


def load_prm800k_records(
    split_name: str = "train",
    limit: int | None = None,
    streaming: bool = True,
) -> list[ExternalStepExample]:
    load_dataset, _ = _load_hf_symbols()
    records: list[ExternalStepExample] = []
    if streaming:
        dataset: Iterable[dict[str, Any]] = load_dataset(PRM800K_DATASET_ID, split=split_name, streaming=True)
        for row_index, row in enumerate(dataset):
            records.append(_normalize_prm800k_row(row, split_name, row_index))
            if limit is not None and len(records) >= limit:
                break
        return records

    dataset = load_dataset(PRM800K_DATASET_ID, split=split_name)
    rows = dataset if limit is None else dataset.select(range(min(limit, len(dataset))))
    for row_index, row in enumerate(rows):
        records.append(_normalize_prm800k_row(row, split_name, row_index))
    return records


def save_external_dataset(records: list[ExternalStepExample], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record.to_record(), ensure_ascii=False) + "\n")


def summarize_external_dataset(records: list[ExternalStepExample]) -> dict[str, Any]:
    step_counts = [len(record.step_texts) for record in records]
    label_counts = Counter(str(record.raw_label) for record in records)
    final_answer_counts = Counter(str(record.final_answer_correct) for record in records)
    dataset_counts = Counter(record.dataset_name for record in records)
    split_counts = Counter(record.dataset_split for record in records)
    domain_counts = Counter(record.domain for record in records)
    return {
        "num_records": len(records),
        "datasets": dict(dataset_counts),
        "splits": dict(split_counts),
        "domains": dict(domain_counts),
        "avg_num_steps": round(sum(step_counts) / len(step_counts), 4) if step_counts else 0.0,
        "max_num_steps": max(step_counts) if step_counts else 0,
        "final_answer_correct": dict(final_answer_counts),
        "raw_label_distribution": dict(label_counts),
    }

