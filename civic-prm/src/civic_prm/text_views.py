from __future__ import annotations


def build_full_text(record: dict, answer_visible: bool) -> str:
    trace_text = record["trace_text"] if answer_visible else record["masked_trace_text"]
    parts = [f"Problem:\n{record['problem_text']}"]
    if "audited_locus" in record and record["audited_locus"] is not None:
        parts.append(f"Audited step index: {record['audited_locus'] + 1}")
    parts.append(f"Trace:\n{trace_text}")
    return "\n\n".join(parts)


def build_step_only_text_at_locus(record: dict, locus: int) -> str:
    prefix = "\n".join(record["step_texts"][:locus]) if locus > 0 else "[NO PRIOR STEP]"
    audited_step = record["step_texts"][locus]
    return (
        f"Problem:\n{record['problem_text']}\n\n"
        f"Prior context:\n{prefix}\n\n"
        f"Audited step:\n{audited_step}"
    )


def build_step_only_text(record: dict) -> str:
    return build_step_only_text_at_locus(record, record["audited_locus"])


def build_view_text(record: dict, view_name: str) -> str:
    if view_name == "visible":
        return build_full_text(record, answer_visible=True)
    if view_name == "masked":
        return build_full_text(record, answer_visible=False)
    if view_name == "step_only":
        return build_step_only_text(record)
    raise ValueError(f"unknown view: {view_name}")
