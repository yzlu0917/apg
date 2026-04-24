from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
import re
from statistics import mean, pvariance
from typing import Any, Dict, List, Sequence

from .countertrace_mini import (
    DEFAULT_QWEN3_1P7B,
    FEWSHOT_EXAMPLES,
    LocalQwenGenerator,
    extract_predicted_answer,
    extract_verifiable_answer,
    split_steps,
    truncate_at_final_answer,
)


CONTINUATOR_STYLES = ("locked", "locked_careful", "locked_minimal")
EDIT_FAMILIES = ("paraphrase", "swap_quantity", "swap_operation")


@dataclass(frozen=True)
class SuccessTrace:
    example_id: str
    question: str
    gold_answer: str
    step_texts: List[str]
    candidate_step_indices: List[int]


def load_success_traces(path: Path, max_traces: int | None = None, trace_offset: int = 0) -> List[SuccessTrace]:
    traces: List[SuccessTrace] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            payload = json.loads(line)
            traces.append(
                SuccessTrace(
                    example_id=payload["example_id"],
                    question=payload["question"],
                    gold_answer=payload["gold_answer"],
                    step_texts=list(payload["step_texts"]),
                    candidate_step_indices=list(payload["candidate_step_indices"]),
                )
            )
    if trace_offset < 0:
        raise ValueError("trace_offset must be non-negative")
    traces = traces[trace_offset:]
    if max_traces is None:
        return traces
    return traces[:max_traces]


def strip_numbering(step_text: str) -> str:
    return re.sub(r"^\s*\d+\.\s*", "", step_text).strip()


def renumber_steps(step_contents: Sequence[str]) -> List[str]:
    return [f"{index}. {content}" for index, content in enumerate(step_contents, start=1)]


def build_prefix_steps(
    step_texts: Sequence[str],
    candidate_index: int,
    replacement_text: str | None = None,
    drop: bool = False,
) -> List[str]:
    contents: List[str] = []
    for index, step_text in enumerate(step_texts[: candidate_index + 1]):
        if index == candidate_index:
            if drop:
                continue
            if replacement_text is not None:
                contents.append(strip_numbering(replacement_text))
            else:
                contents.append(strip_numbering(step_text))
        else:
            contents.append(strip_numbering(step_text))
    return renumber_steps(contents)


def select_candidate_indices(candidate_indices: Sequence[int], max_candidates: int) -> List[int]:
    if len(candidate_indices) <= max_candidates:
        return list(candidate_indices)
    if max_candidates <= 1:
        return [candidate_indices[len(candidate_indices) // 2]]
    selected_positions = []
    for slot in range(max_candidates):
        raw = round(slot * (len(candidate_indices) - 1) / (max_candidates - 1))
        if raw not in selected_positions:
            selected_positions.append(raw)
    while len(selected_positions) < max_candidates:
        mid = len(candidate_indices) // 2
        if mid not in selected_positions:
            selected_positions.append(mid)
        else:
            break
    selected_positions = sorted(selected_positions[:max_candidates])
    return [candidate_indices[position] for position in selected_positions]


def build_continuation_prompt(question: str, prefix_steps: Sequence[str], style: str) -> str:
    intro = [
        "You are continuing an existing grade-school math solution.",
        "Treat all earlier numbered steps as fixed.",
        "Do not rewrite, delete, or correct any previous step.",
        "Continue from the next step number and use earlier results exactly as written.",
        "Finish with a final line that starts with: Final answer:",
    ]
    if style == "locked_careful":
        intro.append("Check arithmetic carefully in the new steps only.")
    elif style == "locked_minimal":
        intro.append("Add the minimum number of new steps needed to finish.")
    blocks = ["\n".join(intro), ""]
    for example in FEWSHOT_EXAMPLES:
        blocks.append(f"Problem: {example['question']}\nSolution:\n{example['solution']}")
        blocks.append("")
    if prefix_steps:
        next_step = len(prefix_steps) + 1
        blocks.append(f"Problem: {question}\nSolution:\n" + "\n".join(prefix_steps) + f"\n{next_step}.")
    else:
        blocks.append(f"Problem: {question}\nSolution:\n1.")
    return "\n".join(blocks)


def build_edit_prompt(question: str, full_steps: Sequence[str], candidate_index: int, edit_family: str) -> str:
    step_text = full_steps[candidate_index]
    base = [
        "Rewrite one numbered math-reasoning step.",
        "Output exactly one numbered line and nothing else.",
        "Keep the line natural and similar in length to the original.",
    ]
    if edit_family == "paraphrase":
        base.append("Preserve the exact mathematical meaning and preserve all numbers.")
    elif edit_family == "swap_quantity":
        base.append("Make it a plausible but incorrect step by changing one quantity or computed result.")
    elif edit_family == "swap_operation":
        base.append("Make it a plausible but incorrect step by changing one arithmetic relation or operator.")
    else:
        raise ValueError(f"Unsupported edit family: {edit_family}")
    return (
        "\n".join(base)
        + "\n\nProblem: "
        + question
        + "\nFull solution:\n"
        + "\n".join(full_steps)
        + "\n\nTarget step:\n"
        + step_text
        + "\n\nRewritten step:"
    )


def sanitize_step_output(raw_text: str, step_number: int, fallback_text: str) -> str:
    line = raw_text.strip().splitlines()[0] if raw_text.strip() else fallback_text
    line = re.sub(r"^Rewritten step:\s*", "", line, flags=re.IGNORECASE).strip()
    line = truncate_at_final_answer(line)
    if not line:
        line = fallback_text
    if not re.match(r"^\d+\.", line):
        line = f"{step_number}. {strip_numbering(line)}"
    return line


def _replace_first(text: str, pattern: str, repl: str) -> str:
    return re.sub(pattern, repl, text, count=1)


def format_number(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    text = f"{value:.4f}".rstrip("0").rstrip(".")
    return text


def _is_integerish(value: float) -> bool:
    return abs(value - round(value)) < 1e-9


def _split_equation(content: str) -> tuple[str, str, str] | None:
    if "=" not in content:
        return None
    left, right = content.split("=", 1)
    return left.rstrip(), right.strip(), "="


def _last_numeric_span(text: str) -> re.Match[str] | None:
    matches = list(re.finditer(r"[-+]?\d+(?:\.\d+)?", text))
    return matches[-1] if matches else None


def _rewrite_last_number(text: str, new_value: str) -> str:
    match = _last_numeric_span(text)
    if not match:
        return text
    return text[: match.start()] + new_value + text[match.end() :]


def _extract_simple_binary_expression(text: str) -> tuple[float, str, float] | None:
    match = re.search(r"(-?\d+(?:\.\d+)?)\s*([+\-*/])\s*(-?\d+(?:\.\d+)?)", text)
    if not match:
        return None
    left = float(match.group(1))
    op = match.group(2)
    right = float(match.group(3))
    return left, op, right


def _compute_binary(left: float, op: str, right: float) -> float | None:
    if op == "+":
        return left + right
    if op == "-":
        return left - right
    if op == "*":
        return left * right
    if op == "/":
        if abs(right) < 1e-9:
            return None
        return left / right
    return None


def _operator_swap_candidates(op: str) -> List[str]:
    if op == "*":
        return ["+", "-", "/"]
    if op == "+":
        return ["-", "/", "*"]
    if op == "-":
        return ["/", "+", "*"]
    if op == "/":
        return ["-", "+", "*"]
    return []


def _is_plausible_operation_result(original: float, candidate: float) -> bool:
    if not math.isfinite(candidate):
        return False
    if candidate < 0:
        return False
    if abs(candidate - original) < 1e-9:
        return False
    scale = max(abs(original), 1.0)
    ratio = max(abs(candidate), 1.0) / scale
    inverse_ratio = scale / max(abs(candidate), 1.0)
    if ratio > 4.0 or inverse_ratio > 4.0:
        return False
    if _is_integerish(original) and abs(candidate) > 1.0 and not _is_integerish(candidate):
        return False
    return True


def _count_arithmetic_ops(text: str) -> int:
    return len(re.findall(r"(?<=\d|\))\s*[+\-*/]\s*(?=\d|\()", text))


def fallback_paraphrase(step_text: str, step_number: int) -> str:
    content = strip_numbering(step_text)
    if ", so " in content:
        left, right = content.split(", so ", 1)
        rewritten = f"{left.strip().rstrip('.')}, giving {right.strip()}"
    elif ", which is " in content:
        left, right = content.split(", which is ", 1)
        rewritten = f"{left.strip()}, and this is {right.strip()}"
    elif content.startswith("Total ") and "=" in content:
        rewritten = "Overall, " + content[0].lower() + content[1:]
    elif ":" in content:
        left, right = content.split(":", 1)
        left = left.strip()
        right = right.strip().rstrip(".")
        if left.lower().startswith(("normal ", "time ", "total ")):
            rewritten = f"{left} is {right}."
        else:
            # Leave unfamiliar colon-forms unchanged rather than risking a semantic drift.
            rewritten = content
    elif content.startswith("Total "):
        rewritten = "Overall, " + content[0].lower() + content[1:]
    else:
        rewritten = content
    return f"{step_number}. {rewritten}"


def fallback_swap_quantity(step_text: str, step_number: int) -> str:
    content = strip_numbering(step_text)
    equation = _split_equation(content)
    if equation is not None:
        left, right, _ = equation
        result_match = _last_numeric_span(right)
        if result_match:
            original_value = float(result_match.group(0))
            delta = 1.0 if abs(original_value) < 10 else max(1.0, round(abs(original_value) * 0.1))
            replacement = format_number(original_value + delta)
            rewritten_right = right[: result_match.start()] + replacement + right[result_match.end() :]
            return f"{step_number}. {left} = {rewritten_right}"
    number_match = _last_numeric_span(content)
    if not number_match:
        return f"{step_number}. {content}"
    original = float(number_match.group(0))
    delta = 1.0 if abs(original) < 10 else max(1.0, round(abs(original) * 0.1))
    replacement = format_number(original + delta)
    rewritten = content[: number_match.start()] + replacement + content[number_match.end() :]
    return f"{step_number}. {rewritten}"


def fallback_swap_operation(step_text: str, step_number: int) -> str:
    content = strip_numbering(step_text)
    if _count_arithmetic_ops(content) == 1 and "(" not in content and ")" not in content:
        expr = _extract_simple_binary_expression(content)
        result_match = _last_numeric_span(content)
        if expr is not None and result_match is not None:
            left, op, right = expr
            original_value = float(result_match.group(0))
            expr_pattern = re.escape(format_number(left)) + r"\s*" + re.escape(op) + r"\s*" + re.escape(format_number(right))
            best_rewrite: str | None = None
            best_score: float | None = None
            for swapped_op in _operator_swap_candidates(op):
                new_value = _compute_binary(left, swapped_op, right)
                if new_value is None or not _is_plausible_operation_result(original_value, new_value):
                    continue
                updated = re.sub(
                    expr_pattern,
                    f"{format_number(left)} {swapped_op} {format_number(right)}",
                    content,
                    count=1,
                )
                updated = _rewrite_last_number(updated, format_number(new_value))
                score = abs(new_value - original_value) / max(abs(original_value), 1.0)
                if best_score is None or score < best_score:
                    best_score = score
                    best_rewrite = updated
            if best_rewrite is not None:
                return f"{step_number}. {best_rewrite}"
    lexical_map = [
        (r"\btwice\b", "half as many"),
        (r"\bfewer\b", "more"),
        (r"\bmore\b", "fewer"),
    ]
    for pattern, replacement in lexical_map:
        updated = _replace_first(content, pattern, replacement)
        if updated != content:
            return f"{step_number}. {updated}"
    return fallback_swap_quantity(step_text, step_number)


def generate_edit_variants(
    generator: LocalQwenGenerator,
    question: str,
    step_texts: Sequence[str],
    candidate_index: int,
    edit_max_new_tokens: int,
) -> Dict[str, str]:
    variants: Dict[str, str] = {}
    original_step = step_texts[candidate_index]
    step_number = candidate_index + 1
    for family in EDIT_FAMILIES:
        if family == "paraphrase":
            edited = fallback_paraphrase(original_step, step_number=step_number)
        elif family == "swap_quantity":
            edited = fallback_swap_quantity(original_step, step_number=step_number)
        elif family == "swap_operation":
            edited = fallback_swap_operation(original_step, step_number=step_number)
        else:
            raise ValueError(f"Unsupported edit family: {family}")
        variants[family] = edited
    return variants


def evaluate_prefix(
    generator: LocalQwenGenerator,
    question: str,
    prefix_steps: Sequence[str],
    gold_answer: str,
    continuation_max_new_tokens: int,
) -> Dict[str, Any]:
    style_results: Dict[str, Dict[str, Any]] = {}
    gold_decimal = extract_predicted_answer(f"Final answer: {gold_answer}")
    solve_scores: List[float] = []
    for style in CONTINUATOR_STYLES:
        prompt = build_continuation_prompt(question, prefix_steps, style=style)
        generated, completion_tokens = generator.generate(prompt, max_new_tokens=continuation_max_new_tokens)
        generated = truncate_at_final_answer(generated)
        predicted, answer_source = extract_verifiable_answer(generated)
        verified = predicted == gold_decimal if predicted is not None else False
        solve_scores.append(float(verified))
        style_results[style] = {
            "generated_text": generated,
            "predicted_answer": str(predicted) if predicted is not None else None,
            "answer_source": answer_source,
            "verified": verified,
            "completion_tokens": completion_tokens,
            "step_texts": split_steps(generated),
        }
    return {
        "solve_probability": mean(solve_scores) if solve_scores else 0.0,
        "style_results": style_results,
    }


def summarize_stage_a(records: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    if not records:
        return {
            "num_records": 0,
            "mean_original_solve": 0.0,
            "mean_drop_solve": 0.0,
            "mean_paraphrase_solve": 0.0,
            "mean_swap_solve": 0.0,
            "mean_n_t": 0.0,
            "mean_n_t_weighted": 0.0,
            "mean_stability": 0.0,
            "mean_paraphrase_gap": 0.0,
            "positive_n_fraction": 0.0,
            "sample_records": [],
        }

    def avg(path: str) -> float:
        keys = path.split(".")
        values: List[float] = []
        for record in records:
            current: Any = record
            for key in keys:
                current = current[key]
            values.append(float(current))
        return mean(values)

    positive_fraction = mean(1.0 if record["scores"]["n_t"] > 0 else 0.0 for record in records)
    return {
        "num_records": len(records),
        "mean_original_solve": avg("scores.original"),
        "mean_drop_solve": avg("scores.drop"),
        "mean_paraphrase_solve": avg("scores.paraphrase"),
        "mean_swap_solve": mean(
            (record["scores"]["swap_quantity"] + record["scores"]["swap_operation"]) / 2.0 for record in records
        ),
        "mean_n_t": avg("scores.n_t"),
        "mean_n_t_weighted": avg("scores.n_t_weighted"),
        "mean_stability": avg("scores.stability"),
        "mean_paraphrase_gap": avg("scores.paraphrase_gap"),
        "positive_n_fraction": positive_fraction,
        "sample_records": list(records[:3]),
    }


def _run_meta(
    success_trace_path: Path,
    model_dir: Path,
    device: str,
    max_traces: int,
    trace_offset: int,
    max_candidates_per_trace: int,
    continuation_max_new_tokens: int,
    edit_max_new_tokens: int,
    stability_sigma: float,
) -> Dict[str, Any]:
    return {
        "success_trace_path": str(success_trace_path),
        "model_dir": str(model_dir),
        "device": device,
        "max_traces": max_traces,
        "trace_offset": trace_offset,
        "max_candidates_per_trace": max_candidates_per_trace,
        "continuation_max_new_tokens": continuation_max_new_tokens,
        "edit_max_new_tokens": edit_max_new_tokens,
        "stability_sigma": stability_sigma,
        "continuator_styles": list(CONTINUATOR_STYLES),
        "edit_families": list(EDIT_FAMILIES),
    }


def _record_key(record: Dict[str, Any]) -> tuple[str, int]:
    return record["example_id"], int(record["candidate_step_index"])


def _load_existing_records(record_path: Path) -> List[Dict[str, Any]]:
    if not record_path.exists():
        return []
    records: List[Dict[str, Any]] = []
    with record_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def _write_stage_a_outputs(output_dir: Path, records: Sequence[Dict[str, Any]], run_meta: Dict[str, Any]) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize_stage_a(records)
    summary.update(run_meta)
    (output_dir / "stage_a_math_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    with (output_dir / "stage_a_math_records.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")
    return summary


def run_math_stage_a_pilot(
    success_trace_path: Path,
    output_dir: Path,
    model_dir: Path = DEFAULT_QWEN3_1P7B,
    device: str = "cuda:0",
    max_traces: int = 4,
    trace_offset: int = 0,
    max_candidates_per_trace: int = 3,
    continuation_max_new_tokens: int = 160,
    edit_max_new_tokens: int = 64,
    stability_sigma: float = 0.25,
    resume: bool = False,
) -> Dict[str, Any]:
    traces = load_success_traces(success_trace_path, max_traces=max_traces, trace_offset=trace_offset)
    selected_candidates_by_trace = {
        trace.example_id: select_candidate_indices(trace.candidate_step_indices, max_candidates=max_candidates_per_trace)
        for trace in traces
    }
    record_path = output_dir / "stage_a_math_records.jsonl"
    records: List[Dict[str, Any]] = _load_existing_records(record_path) if resume else []
    completed_keys = {_record_key(record) for record in records}
    run_meta = _run_meta(
        success_trace_path=success_trace_path,
        model_dir=model_dir,
        device=device,
        max_traces=max_traces,
        trace_offset=trace_offset,
        max_candidates_per_trace=max_candidates_per_trace,
        continuation_max_new_tokens=continuation_max_new_tokens,
        edit_max_new_tokens=edit_max_new_tokens,
        stability_sigma=stability_sigma,
    )
    summary = _write_stage_a_outputs(output_dir=output_dir, records=records, run_meta=run_meta)

    pending_keys = [
        (trace.example_id, candidate_index)
        for trace in traces
        for candidate_index in selected_candidates_by_trace[trace.example_id]
        if (trace.example_id, candidate_index) not in completed_keys
    ]
    if not pending_keys:
        return {"summary": summary, "records": records}

    generator = LocalQwenGenerator(model_dir=model_dir, device=device, max_new_tokens=continuation_max_new_tokens)
    for trace in traces:
        selected_candidates = selected_candidates_by_trace[trace.example_id]
        for candidate_index in selected_candidates:
            if (trace.example_id, candidate_index) in completed_keys:
                continue
            edit_variants = generate_edit_variants(
                generator=generator,
                question=trace.question,
                step_texts=trace.step_texts,
                candidate_index=candidate_index,
                edit_max_new_tokens=edit_max_new_tokens,
            )
            original_prefix = build_prefix_steps(trace.step_texts, candidate_index)
            drop_prefix = build_prefix_steps(trace.step_texts, candidate_index, drop=True)
            paraphrase_prefix = build_prefix_steps(
                trace.step_texts, candidate_index, replacement_text=edit_variants["paraphrase"]
            )
            swap_quantity_prefix = build_prefix_steps(
                trace.step_texts, candidate_index, replacement_text=edit_variants["swap_quantity"]
            )
            swap_operation_prefix = build_prefix_steps(
                trace.step_texts, candidate_index, replacement_text=edit_variants["swap_operation"]
            )

            original_eval = evaluate_prefix(
                generator=generator,
                question=trace.question,
                prefix_steps=original_prefix,
                gold_answer=trace.gold_answer,
                continuation_max_new_tokens=continuation_max_new_tokens,
            )
            drop_eval = evaluate_prefix(
                generator=generator,
                question=trace.question,
                prefix_steps=drop_prefix,
                gold_answer=trace.gold_answer,
                continuation_max_new_tokens=continuation_max_new_tokens,
            )
            paraphrase_eval = evaluate_prefix(
                generator=generator,
                question=trace.question,
                prefix_steps=paraphrase_prefix,
                gold_answer=trace.gold_answer,
                continuation_max_new_tokens=continuation_max_new_tokens,
            )
            swap_quantity_eval = evaluate_prefix(
                generator=generator,
                question=trace.question,
                prefix_steps=swap_quantity_prefix,
                gold_answer=trace.gold_answer,
                continuation_max_new_tokens=continuation_max_new_tokens,
            )
            swap_operation_eval = evaluate_prefix(
                generator=generator,
                question=trace.question,
                prefix_steps=swap_operation_prefix,
                gold_answer=trace.gold_answer,
                continuation_max_new_tokens=continuation_max_new_tokens,
            )

            deltas = [
                original_eval["solve_probability"] - drop_eval["solve_probability"],
                original_eval["solve_probability"] - swap_quantity_eval["solve_probability"],
                original_eval["solve_probability"] - swap_operation_eval["solve_probability"],
            ]
            style_level_deltas: List[float] = []
            for style in CONTINUATOR_STYLES:
                original_score = float(original_eval["style_results"][style]["verified"])
                style_level_deltas.extend(
                    [
                        original_score - float(drop_eval["style_results"][style]["verified"]),
                        original_score - float(swap_quantity_eval["style_results"][style]["verified"]),
                        original_score - float(swap_operation_eval["style_results"][style]["verified"]),
                    ]
                )
            stability = math.exp(-pvariance(style_level_deltas) / (stability_sigma**2)) if len(style_level_deltas) > 1 else 1.0
            n_t = mean(deltas)
            record = {
                "example_id": trace.example_id,
                "question": trace.question,
                "candidate_step_index": candidate_index,
                "original_step": trace.step_texts[candidate_index],
                "prefixes": {
                    "original": original_prefix,
                    "drop": drop_prefix,
                    "paraphrase": paraphrase_prefix,
                    "swap_quantity": swap_quantity_prefix,
                    "swap_operation": swap_operation_prefix,
                },
                "edits": edit_variants,
                "scores": {
                    "original": original_eval["solve_probability"],
                    "drop": drop_eval["solve_probability"],
                    "paraphrase": paraphrase_eval["solve_probability"],
                    "swap_quantity": swap_quantity_eval["solve_probability"],
                    "swap_operation": swap_operation_eval["solve_probability"],
                    "n_t": n_t,
                    "stability": stability,
                    "n_t_weighted": n_t * stability,
                    "paraphrase_gap": abs(original_eval["solve_probability"] - paraphrase_eval["solve_probability"]),
                },
                "style_results": {
                    "original": original_eval["style_results"],
                    "drop": drop_eval["style_results"],
                    "paraphrase": paraphrase_eval["style_results"],
                    "swap_quantity": swap_quantity_eval["style_results"],
                    "swap_operation": swap_operation_eval["style_results"],
                },
            }
            records.append(record)
            completed_keys.add((trace.example_id, candidate_index))
            summary = _write_stage_a_outputs(output_dir=output_dir, records=records, run_meta=run_meta)
    return {"summary": summary, "records": records}


def merge_stage_a_runs(input_dirs: Sequence[Path], output_dir: Path) -> Dict[str, Any]:
    records: List[Dict[str, Any]] = []
    summaries: List[Dict[str, Any]] = []
    for input_dir in input_dirs:
        summary_path = input_dir / "stage_a_math_summary.json"
        record_path = input_dir / "stage_a_math_records.jsonl"
        summaries.append(json.loads(summary_path.read_text(encoding="utf-8")))
        with record_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                records.append(json.loads(line))

    summary = summarize_stage_a(records)
    summary["input_dirs"] = [str(path) for path in input_dirs]
    summary["num_input_runs"] = len(input_dirs)
    summary["child_run_meta"] = [
        {
            key: child.get(key)
            for key in (
                "device",
                "max_traces",
                "trace_offset",
                "max_candidates_per_trace",
                "success_trace_path",
            )
        }
        for child in summaries
    ]
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "stage_a_math_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    with (output_dir / "stage_a_math_records.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")
    return {"summary": summary, "records": records}
