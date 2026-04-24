from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from civic_prm.audit import load_records
from civic_prm.domains.blocksworld import _canonicalize, _moves, _render_state
from civic_prm.schema import TraceExample


STATE_PATTERN = re.compile(r"\[[A-Z](?: [A-Z])*\](?:\s+\[[A-Z](?: [A-Z])*\])*")


@dataclass(frozen=True)
class AnchorAudit:
    accepted: bool
    reason: str
    cleaned_steps: list[str]
    audited_locus: int | None = None
    invalid_step_text: str | None = None
    canonical_answer_surface: str | None = None
    distractor_answer_surface: str | None = None


def _clean_step(step_text: str) -> str:
    text = step_text.strip()
    if not text:
        return ""
    if text in {"{", "}", "[", "]"}:
        return ""
    if re.fullmatch(r'"steps"\s*:\s*\[', text.strip('", ')):
        return ""
    text = text.strip(",")
    if text.startswith('"') and text.endswith('"') and len(text) >= 2:
        text = text[1:-1]
    text = text.strip().strip(",")
    text = re.sub(r"^\d+\.\s*", "", text)
    return text.strip()


def _clean_steps(record: dict[str, Any]) -> list[str]:
    cleaned = [_clean_step(step) for step in record["step_texts"]]
    return [step for step in cleaned if step]


def _replace_x_solution(step_text: str, new_value: int | str) -> str:
    replaced = re.sub(r"\bx\s*=\s*-?\d+(?:\.\d+)?\b", f"x = {new_value}", step_text, count=1)
    if replaced != step_text:
        return replaced
    return f"{step_text} This would instead imply x = {new_value}."


def _normalize_arrow_path(text: str) -> str:
    return re.sub(r"\s+", "", text).replace("-", "->")


def _parse_graph_answer_surface(surface: str) -> tuple[str, int]:
    match = re.match(r"(.+?)\s+with total cost\s+(-?\d+)", surface.strip())
    if not match:
        raise ValueError(f"bad graph answer surface: {surface}")
    return match.group(1).strip(), int(match.group(2))


def _parse_state(text: str) -> tuple[tuple[str, ...], ...]:
    stacks = []
    for stack in re.findall(r"\[([A-Z](?: [A-Z])*)\]", text):
        stacks.append(tuple(stack.split()))
    if not stacks:
        raise ValueError(f"cannot parse state from: {text}")
    return _canonicalize(tuple(stacks))


def _replace_last_state(step_text: str, replacement_state: str) -> str:
    matches = list(STATE_PATTERN.finditer(step_text))
    if not matches:
        return f"{step_text} Reaching state {replacement_state}."
    last = matches[-1]
    return step_text[: last.start()] + replacement_state + step_text[last.end() :]


def audit_algebra_anchor(record: dict[str, Any], cleaned_steps: list[str]) -> AnchorAudit:
    solution = str(record["metadata"]["solution_x"])
    distractor = record["metadata"]["distractor_x"]
    locus = None
    for index, step in enumerate(cleaned_steps):
        matches = re.findall(r"\bx\s*=\s*(-?\d+(?:\.\d+)?)\b", step)
        if matches and matches[-1] == solution:
            locus = index
    if locus is None:
        return AnchorAudit(False, "missing_correct_solution_statement", cleaned_steps)
    invalid_step = _replace_x_solution(cleaned_steps[locus], distractor)
    return AnchorAudit(
        accepted=True,
        reason="accepted",
        cleaned_steps=cleaned_steps,
        audited_locus=locus,
        invalid_step_text=invalid_step,
        canonical_answer_surface=record["metadata"]["correct_answer_surface"],
        distractor_answer_surface=record["metadata"]["distractor_answer_surface"],
    )


def audit_graph_anchor(record: dict[str, Any], cleaned_steps: list[str]) -> AnchorAudit:
    correct_surface = record["metadata"]["correct_answer_surface"]
    distractor_surface = record["metadata"]["distractor_answer_surface"]
    correct_path, correct_total = _parse_graph_answer_surface(correct_surface)
    norm_path = _normalize_arrow_path(correct_path)
    locus = None
    for index, step in enumerate(cleaned_steps):
        normalized = _normalize_arrow_path(step)
        lower_step = step.lower()
        has_affirming_cue = any(
            cue in lower_step for cue in ["shortest path", "best route", "cheapest route", "choose", "final route"]
        )
        has_negative_cue = any(cue in lower_step for cue in ["longer than", "alternatively", "alternative", "not shortest"])
        if norm_path in normalized and str(correct_total) in step and has_affirming_cue and not has_negative_cue:
            locus = index
    if locus is None:
        return AnchorAudit(False, "missing_correct_path_conclusion", cleaned_steps)
    invalid_step = f"The shortest path from S to T is {distractor_surface}."
    return AnchorAudit(
        accepted=True,
        reason="accepted",
        cleaned_steps=cleaned_steps,
        audited_locus=locus,
        invalid_step_text=invalid_step,
        canonical_answer_surface=correct_surface,
        distractor_answer_surface=distractor_surface,
    )


def audit_blocksworld_anchor(record: dict[str, Any], cleaned_steps: list[str]) -> AnchorAudit:
    try:
        start_state = _parse_state(record["metadata"]["start_state"])
        goal_state = _parse_state(record["metadata"]["goal_state"])
    except Exception:
        return AnchorAudit(False, "bad_state_metadata", cleaned_steps)
    blocks = tuple(chr(ord("A") + offset) for offset in range(record["metadata"]["num_blocks"]))
    current = start_state
    move_history: list[tuple[int, tuple[tuple[str, ...], ...], tuple[tuple[str, ...], ...]]] = []
    for index, step in enumerate(cleaned_steps):
        state_mentions = [match.group(0) for match in STATE_PATTERN.finditer(step)]
        if not state_mentions:
            continue
        try:
            target_state = _parse_state(state_mentions[-1])
        except Exception:
            return AnchorAudit(False, "bad_state_surface", cleaned_steps)
        if target_state == current:
            return AnchorAudit(False, "noop_or_repeated_state", cleaned_steps)
        legal_targets = [state for _, state in _moves(current, blocks)]
        if target_state not in legal_targets:
            return AnchorAudit(False, "illegal_multi_move_transition", cleaned_steps)
        move_history.append((index, current, target_state))
        current = target_state
    if not move_history:
        return AnchorAudit(False, "missing_auditable_state_transitions", cleaned_steps)
    if current != goal_state:
        return AnchorAudit(False, "does_not_reach_goal", cleaned_steps)
    chosen = None
    alternative_targets = None
    for locus, prior_state, target_state in move_history:
        candidates = [state for _, state in _moves(prior_state, blocks) if state != target_state]
        if candidates:
            chosen = (locus, prior_state, target_state)
            alternative_targets = candidates
            break
    if chosen is None or not alternative_targets:
        return AnchorAudit(False, "missing_alternative_legal_move", cleaned_steps)
    locus, _, _ = chosen
    invalid_step = _replace_last_state(cleaned_steps[locus], _render_state(alternative_targets[0]))
    return AnchorAudit(
        accepted=True,
        reason="accepted",
        cleaned_steps=cleaned_steps,
        audited_locus=locus,
        invalid_step_text=invalid_step,
        canonical_answer_surface=record["metadata"]["correct_answer_surface"],
        distractor_answer_surface=record["metadata"]["distractor_answer_surface"],
    )


def audit_generated_anchor(record: dict[str, Any]) -> AnchorAudit:
    cleaned_steps = _clean_steps(record)
    if not cleaned_steps:
        return AnchorAudit(False, "empty_after_cleanup", cleaned_steps)
    if record["domain"] == "algebra":
        return audit_algebra_anchor(record, cleaned_steps)
    if record["domain"] == "graph_path":
        return audit_graph_anchor(record, cleaned_steps)
    if record["domain"] == "blocksworld":
        return audit_blocksworld_anchor(record, cleaned_steps)
    return AnchorAudit(False, "unknown_domain", cleaned_steps)


def build_counterfactual_quartet(record: dict[str, Any], audit: AnchorAudit) -> list[TraceExample]:
    if not audit.accepted or audit.audited_locus is None or audit.invalid_step_text is None:
        raise ValueError("cannot build quartet from rejected audit")
    quartet_id = record["swap_group_id"]
    valid_steps = list(audit.cleaned_steps)
    invalid_steps = list(audit.cleaned_steps)
    invalid_steps[audit.audited_locus] = audit.invalid_step_text
    correct_answer_line = f"Final answer: {audit.canonical_answer_surface}"
    swapped_answer_line = f"Final answer: {audit.distractor_answer_surface}"
    masked_answer_line = "Final answer: [ANSWER_MASK]"
    metadata = dict(record["metadata"])
    metadata.update(
        {
            "counterfactual_builder_name": "deterministic_auditable_generated_v1",
            "source_generated_trace_id": record["trace_id"],
            "source_generated_answer_line": record["final_answer_line"],
            "source_generated_answer_is_correct": record["answer_is_correct"],
            "generated_counterfactual": True,
            "accepted_reason": audit.reason,
        }
    )

    variants = [
        ("valid_correct", valid_steps, correct_answer_line, True, True),
        ("invalid_correct", invalid_steps, correct_answer_line, False, True),
        ("valid_swapped", valid_steps, swapped_answer_line, True, False),
        ("invalid_swapped", invalid_steps, swapped_answer_line, False, False),
    ]
    records = []
    for role, steps, answer_line, is_valid_process, answer_is_correct in variants:
        trace_text = "\n".join(steps + [answer_line])
        masked_trace_text = "\n".join(steps + [masked_answer_line])
        records.append(
            TraceExample(
                trace_id=f"{quartet_id}-{role}",
                quartet_id=quartet_id,
                problem_id=record["problem_id"],
                domain=record["domain"],
                verbalizer_id="model_generated_cf",
                audited_locus=audit.audited_locus,
                counterfactual_role=role,
                process_variant="valid" if is_valid_process else "invalid",
                answer_variant="correct" if answer_is_correct else "swapped",
                is_valid_process=is_valid_process,
                answer_is_correct=answer_is_correct,
                problem_text=record["problem_text"],
                step_texts=steps,
                final_answer_line=answer_line,
                masked_answer_line=masked_answer_line,
                trace_text=trace_text,
                masked_trace_text=masked_trace_text,
                metadata=metadata,
            )
        )
    return records


def build_generated_counterfactual_dataset(dataset_path: str | Path) -> tuple[list[TraceExample], dict[str, Any], list[dict[str, Any]]]:
    rows = load_records(dataset_path)
    original_rows = [row for row in rows if row["answer_variant"] == "original"]
    generated_records: list[TraceExample] = []
    rejection_rows: list[dict[str, Any]] = []
    accepted_by_domain: dict[str, int] = {}
    original_by_domain: dict[str, int] = {}
    rejections_by_domain_reason: dict[str, dict[str, int]] = {}

    for row in original_rows:
        domain = row["domain"]
        original_by_domain[domain] = original_by_domain.get(domain, 0) + 1
        audit = audit_generated_anchor(row)
        if not audit.accepted:
            rejection_rows.append(
                {
                    "trace_id": row["trace_id"],
                    "domain": domain,
                    "reason": audit.reason,
                    "cleaned_steps": audit.cleaned_steps,
                    "final_answer_line": row["final_answer_line"],
                }
            )
            rejections_by_domain_reason.setdefault(domain, {})
            rejections_by_domain_reason[domain][audit.reason] = (
                rejections_by_domain_reason[domain].get(audit.reason, 0) + 1
            )
            continue
        accepted_by_domain[domain] = accepted_by_domain.get(domain, 0) + 1
        generated_records.extend(build_counterfactual_quartet(row, audit))

    summary = {
        "source_dataset": str(dataset_path),
        "num_original_generated_rows": len(original_rows),
        "num_accepted_anchors": len({record.quartet_id for record in generated_records}),
        "num_counterfactual_traces": len(generated_records),
        "accepted_anchors_by_domain": accepted_by_domain,
        "original_rows_by_domain": original_by_domain,
        "rejections_by_domain_reason": rejections_by_domain_reason,
    }
    return generated_records, summary, rejection_rows


def write_rejection_log(rejections: list[dict[str, Any]], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rejections:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
