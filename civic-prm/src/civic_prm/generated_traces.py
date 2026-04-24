from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import torch

from civic_prm.generated_counterfactuals import STATE_PATTERN, audit_generated_anchor
from civic_prm.audit import load_records
from civic_prm.domains.blocksworld import _canonicalize, _moves, _render_state, _shortest_plan
from civic_prm.prompt_verifier import _parse_response, load_model
from civic_prm.splits import build_quartet_split_map


def _extract_json_object(text: str) -> dict[str, Any]:
    candidates = re.findall(r"\{.*\}", text, flags=re.DOTALL)
    for candidate in reversed(candidates):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    raise ValueError(f"could not parse JSON from: {text[:200]}")


def _extract_text_payload(text: str) -> dict[str, Any]:
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    final_index = next((index for index, line in enumerate(lines) if line.lower().startswith("final answer:")), None)
    if final_index is not None:
        final_answer_line = lines[final_index]
    else:
        candidate = lines[-1]
        if re.search(r"\[[^\]]+\]", candidate) or "x =" in candidate or "->" in candidate:
            answer_surface = re.sub(r"^(Therefore|So|Hence|Thus|The answer is)\s*[:,-]?\s*", "", candidate, flags=re.IGNORECASE).strip()
            final_answer_line = answer_surface if answer_surface.lower().startswith("final answer:") else f"Final answer: {answer_surface}"
            final_index = len(lines) - 1
        else:
            raise ValueError("missing final answer line")
    step_lines = lines[:final_index]
    normalized_steps = []
    for line in step_lines:
        normalized = re.sub(r"^(Step|Reasoning)\s*\d+:\s*", "", line, flags=re.IGNORECASE).strip()
        normalized = normalized.lstrip("-* ").strip()
        if normalized:
            normalized_steps.append(normalized)
    if not normalized_steps:
        raise ValueError("missing steps")
    return {
        "steps": normalized_steps,
        "final_answer_line": final_answer_line,
    }


def _extract_state_surface(text: str) -> str:
    matches = STATE_PATTERN.findall(text)
    if not matches:
        raise ValueError("missing state surface")
    return matches[-1]


def _parse_state_surface(text: str) -> tuple[tuple[str, ...], ...]:
    stacks = []
    for stack in re.findall(r"\[([A-Z](?: [A-Z])*)\]", text):
        stacks.append(tuple(stack.split()))
    if not stacks:
        raise ValueError(f"cannot parse state from: {text}")
    return _canonicalize(tuple(stacks))


def _normalize_final_answer_line(problem_spec: dict[str, Any], final_answer_line: str) -> str:
    cleaned = final_answer_line.strip().strip(",").strip('"').strip()
    cleaned = re.sub(r'^(?:"?final_answer_line"?\s*:\s*)', "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^Final answer:\s*", "", cleaned, flags=re.IGNORECASE)
    if problem_spec["domain"] == "algebra":
        match = re.findall(r"x\s*=\s*-?\d+(?:\.\d+)?", cleaned)
        if not match:
            raise ValueError("bad algebra final answer")
        return f"Final answer: {match[-1]}"
    if problem_spec["domain"] == "graph_path":
        match = re.search(r"S\s*->\s*[A-Z]\s*->\s*[A-Z]\s*->\s*T\s+with total cost\s+-?\d+", cleaned)
        if not match:
            raise ValueError("bad graph final answer")
        normalized_surface = re.sub(r"\s+", " ", match.group(0)).strip()
        return f"Final answer: {normalized_surface}"
    matches = STATE_PATTERN.findall(cleaned)
    if not matches:
        raise ValueError("bad blocksworld final answer")
    return f"Final answer: {matches[-1]}"


def _extract_answer_surface(record: dict[str, Any]) -> str:
    prefix, suffix = record["masked_answer_line"].split("[ANSWER_MASK]")
    if not record["final_answer_line"].startswith(prefix) or not record["final_answer_line"].endswith(suffix):
        raise ValueError("cannot align answer surface")
    return record["final_answer_line"][len(prefix) : len(record["final_answer_line"]) - len(suffix) if suffix else None]


def load_problem_specs(dataset_path: str | Path, split_seed: int = 17) -> list[dict[str, Any]]:
    records = load_records(dataset_path)
    split_map = build_quartet_split_map(records, seed=split_seed)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        if split_map[record["quartet_id"]] != "test":
            continue
        grouped.setdefault(record["quartet_id"], []).append(record)

    specs = []
    for quartet_id in sorted(grouped):
        rows = grouped[quartet_id]
        valid_correct = next(
            row
            for row in rows
            if row["counterfactual_role"] == "valid_correct" and row["verbalizer_id"].endswith("v1")
        )
        valid_swapped = next(
            row
            for row in rows
            if row["counterfactual_role"] == "valid_swapped" and row["verbalizer_id"].endswith("v1")
        )
        specs.append(
            {
                "quartet_id": quartet_id,
                "problem_id": valid_correct["problem_id"],
                "domain": valid_correct["domain"],
                "problem_text": valid_correct["problem_text"],
                "correct_answer": _extract_answer_surface(valid_correct),
                "distractor_answer": _extract_answer_surface(valid_swapped),
                "metadata": valid_correct.get("metadata", {}),
            }
        )
    return specs


def _answer_format(domain: str) -> str:
    if domain == "algebra":
        return "Final answer: x = <value>"
    if domain == "graph_path":
        return "Final answer: S -> ... -> T with total cost <number>"
    return "Final answer: [state]"


def _domain_generation_guidance(problem_spec: dict[str, Any]) -> str:
    domain = problem_spec["domain"]
    if domain == "algebra":
        return (
            "Use one algebra transformation per step. "
            "Keep the equations exact. "
            "The last reasoning step must explicitly conclude with x = <value>."
        )
    if domain == "graph_path":
        return (
            "Use the full four-node path notation exactly, for example "
            "`S -> G -> H -> T with total cost 9`. "
            "Do not shorten paths to forms like `S-H-T` or `S-F-T`. "
            "The last reasoning step must start with "
            "`The shortest path from S to T is ...` and use the full path notation."
        )
    return (
        "Each step must describe exactly one legal top-block move from the previous state. "
        "End every step with the exact resulting state string like `[A] [B C] [D]`. "
        "Do not use the word `swap`. Do not move two blocks at once. Do not skip intermediate states. "
        "Do not jump straight to the goal in one step unless it is one legal move, and do not repeat the same state. "
        "The final answer line must equal the goal state exactly, not an intermediate state."
    )


def _domain_extra_context(problem_spec: dict[str, Any]) -> str:
    domain = problem_spec["domain"]
    if domain == "graph_path":
        return (
            "A valid route must use the exact format `S -> X -> Y -> T with total cost N`.\n"
            "The last reasoning step must explicitly state the shortest path using that full format."
        )
    if domain == "blocksworld":
        metadata = problem_spec.get("metadata", {})
        return (
            f"Start state: {metadata.get('start_state', '')}\n"
            f"Goal state: {metadata.get('goal_state', '')}\n"
            "Only legal top-block moves are allowed.\n"
            "Every reasoning step must end with the full resulting state.\n"
            "The final answer line must be exactly the goal state."
        )
    return ""


def _build_generation_messages(problem_spec: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "Solve the problem with a short natural reasoning trace. "
                "Use 3 to 8 reasoning steps written as plain sentences, not numbered bullet labels. "
                "Keep all equations, path expressions, or block states exact. "
                f"{_domain_generation_guidance(problem_spec)} "
                'Reply with JSON only using keys "steps" and "final_answer_line".'
            ),
        },
        {
            "role": "user",
            "content": (
                "/no_think\n"
                f"Problem:\n{problem_spec['problem_text']}\n\n"
                f"{_domain_extra_context(problem_spec)}\n\n"
                f"Final answer format:\n{_answer_format(problem_spec['domain'])}"
            ),
        },
    ]


def _similarity_to_goal(
    state: tuple[tuple[str, ...], ...],
    goal: tuple[tuple[str, ...], ...],
) -> int:
    state_positions = {}
    goal_positions = {}
    for stack_index, stack in enumerate(state):
        for height, block in enumerate(stack):
            state_positions[block] = (stack_index, height)
    for stack_index, stack in enumerate(goal):
        for height, block in enumerate(stack):
            goal_positions[block] = (stack_index, height)
    return sum(int(state_positions.get(block) == goal_positions[block]) for block in goal_positions)


def _distance_to_goal(
    state: tuple[tuple[str, ...], ...],
    goal: tuple[tuple[str, ...], ...],
    blocks: tuple[str, ...],
) -> int:
    return len(_shortest_plan(state, goal, blocks))


def _build_blocksworld_step_messages(
    current_state: str,
    goal_state: str,
    legal_options: list[tuple[str, str]],
    remaining_steps: int,
) -> list[dict[str, str]]:
    option_lines = "\n".join(
        f"{index + 1}. {action}, reaching state {next_state}"
        for index, (action, next_state) in enumerate(legal_options)
    )
    return [
        {
            "role": "system",
            "content": (
                "Choose one legal next blocksworld move and describe it in one short sentence. "
                "Use exactly one move from the allowed options. "
                "Your sentence must end with the exact resulting state string. "
                'Reply with JSON only using keys "choice" and "step". '
                '"choice" must be the integer option number.'
            ),
        },
        {
            "role": "user",
            "content": (
                "/no_think\n"
                f"Current state:\n{current_state}\n\n"
                f"Goal state:\n{goal_state}\n\n"
                f"Remaining step budget:\n{remaining_steps}\n\n"
                f"Allowed legal next moves:\n{option_lines}"
            ),
        },
    ]


def _parse_blocksworld_step_payload(
    text: str,
    legal_options: list[tuple[str, str]],
) -> dict[str, str]:
    payload = _extract_json_object(text)
    step = str(payload.get("step", "")).strip()
    if not step:
        raise ValueError("missing scaffolded step")
    choice = payload.get("choice")
    if not isinstance(choice, int):
        choice_text = str(choice).strip()
        if not re.fullmatch(r"\d+", choice_text):
            raise ValueError("missing scaffolded choice")
        choice = int(choice_text)
    if not 1 <= choice <= len(legal_options):
        raise ValueError("out-of-range scaffolded choice")
    chosen_action, canonical_state = legal_options[choice - 1]
    if len(step) < 12 or re.fullmatch(r"[\d\s\[\]A-Z]+", step):
        step = f"{chosen_action}, reaching state {canonical_state}"
    if canonical_state not in step:
        step = f"{step.rstrip('.')} reaching state {canonical_state}"
    return {
        "step": step,
        "next_state": canonical_state,
    }


def _validate_generation(problem_spec: dict[str, Any], payload: dict[str, Any]) -> None:
    steps = payload.get("steps")
    final_answer_line = payload.get("final_answer_line")
    if not isinstance(steps, list) or not 1 <= len(steps) <= 12:
        raise ValueError("bad steps")
    if not isinstance(final_answer_line, str) or not final_answer_line.strip():
        raise ValueError("bad final answer line")
    for step in steps:
        if not isinstance(step, str) or not step.strip():
            raise ValueError("empty generated step")
        stripped = step.strip().strip(",")
        if stripped in {"{", "}", "[", "]"}:
            raise ValueError("structural token leaked into steps")
        if "final_answer_line" in stripped.lower():
            raise ValueError("field-name leakage in steps")
        if re.fullmatch(r'"steps"\s*:\s*\[', stripped.strip('"')):
            raise ValueError("json list header leaked into steps")


@torch.inference_mode()
def generate_blocksworld_trace_sample(
    tokenizer,
    model,
    problem_spec: dict[str, Any],
    max_steps: int | None = None,
    per_step_retries: int = 6,
    temperature: float = 0.6,
    top_p: float = 0.9,
    max_new_tokens: int = 120,
) -> dict[str, Any]:
    metadata = problem_spec["metadata"]
    current_state = _parse_state_surface(metadata["start_state"])
    goal_state = _parse_state_surface(metadata["goal_state"])
    blocks = tuple(chr(ord("A") + offset) for offset in range(metadata["num_blocks"]))
    step_budget = max_steps or max(2, metadata.get("plan_length", 4) + 1)
    visited = {current_state}
    step_texts: list[str] = []
    raw_responses: list[str] = []

    for step_index in range(step_budget):
        if current_state == goal_state:
            break
        legal_moves = _moves(current_state, blocks)
        current_distance = _distance_to_goal(current_state, goal_state, blocks)
        improving_moves = []
        for action, next_state in legal_moves:
            try:
                next_distance = _distance_to_goal(next_state, goal_state, blocks)
            except Exception:  # noqa: BLE001
                continue
            if next_distance < current_distance:
                improving_moves.append((action, next_state, next_distance))
        if improving_moves:
            best_distance = min(item[2] for item in improving_moves)
            legal_moves = [(action, next_state) for action, next_state, distance in improving_moves if distance == best_distance]
        ordered_options = sorted(
            legal_moves,
            key=lambda item: _similarity_to_goal(item[1], goal_state),
            reverse=True,
        )
        legal_options = [(action, _render_state(next_state)) for action, next_state in ordered_options]
        messages = _build_blocksworld_step_messages(
            current_state=_render_state(current_state),
            goal_state=_render_state(goal_state),
            legal_options=legal_options,
            remaining_steps=step_budget - step_index,
        )
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        model_inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        parsed = None
        last_error = None
        for _ in range(per_step_retries):
            generated = model.generate(
                **model_inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=temperature,
                top_p=top_p,
                eos_token_id=tokenizer.eos_token_id,
                pad_token_id=tokenizer.eos_token_id,
            )
            response = tokenizer.decode(
                generated[0][model_inputs["input_ids"].shape[1] :],
                skip_special_tokens=True,
            ).strip()
            raw_responses.append(response)
            try:
                parsed = _parse_blocksworld_step_payload(response, legal_options)
                next_state = _parse_state_surface(parsed["next_state"])
                if next_state in visited:
                    raise ValueError("repeated scaffolded state")
                current_state = next_state
                visited.add(next_state)
                step_texts.append(parsed["step"])
                break
            except Exception as error:  # noqa: BLE001
                last_error = error
        if parsed is None:
            raise RuntimeError(f"failed scaffolded blocksworld step {step_index}: {last_error}")

    if current_state != goal_state:
        raise RuntimeError("scaffolded blocksworld generation did not reach goal")

    final_answer_line = f"Final answer: {_render_state(goal_state)}"
    return {
        "steps": step_texts,
        "final_answer_line": final_answer_line,
        "raw_response": "\n---\n".join(raw_responses),
    }


@torch.inference_mode()
def generate_trace_sample(
    tokenizer,
    model,
    problem_spec: dict[str, Any],
    use_blocksworld_scaffold: bool = False,
    temperature: float = 0.8,
    top_p: float = 0.95,
    max_new_tokens: int = 320,
) -> dict[str, Any]:
    if use_blocksworld_scaffold and problem_spec["domain"] == "blocksworld":
        return generate_blocksworld_trace_sample(
            tokenizer=tokenizer,
            model=model,
            problem_spec=problem_spec,
        )
    messages = _build_generation_messages(problem_spec)
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    model_inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    generated = model.generate(
        **model_inputs,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        temperature=temperature,
        top_p=top_p,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.eos_token_id,
    )
    response = tokenizer.decode(
        generated[0][model_inputs["input_ids"].shape[1] :],
        skip_special_tokens=True,
    ).strip()
    try:
        payload = _extract_json_object(response)
    except ValueError:
        payload = _extract_text_payload(response)
    payload["final_answer_line"] = _normalize_final_answer_line(problem_spec, payload["final_answer_line"])
    _validate_generation(problem_spec, payload)
    return {
        "steps": [step.strip() for step in payload["steps"]],
        "final_answer_line": payload["final_answer_line"].strip(),
        "raw_response": response,
    }


def load_generator(model_root: str | Path):
    return load_model(model_root)


def build_generated_records(
    problem_spec: dict[str, Any],
    sample_index: int,
    generation: dict[str, Any],
) -> list[dict[str, Any]]:
    final_answer_line = generation["final_answer_line"]
    answer_surface = final_answer_line.removeprefix("Final answer:").strip()
    is_correct = answer_surface == problem_spec["correct_answer"]
    swapped_answer = (
        problem_spec["distractor_answer"] if is_correct else problem_spec["correct_answer"]
    )
    swap_group_id = f"{problem_spec['quartet_id']}-gen-{sample_index:02d}"
    metadata = dict(problem_spec.get("metadata", {}))
    metadata.update(
        {
            "generated": True,
            "generator_name": "qwen3-1.7b",
            "sample_index": sample_index,
            "swap_group_id": swap_group_id,
            "source_answer_surface": answer_surface,
            "correct_answer_surface": problem_spec["correct_answer"],
            "distractor_answer_surface": problem_spec["distractor_answer"],
        }
    )

    def make_row(answer_variant: str, answer_line: str, answer_is_correct: bool) -> dict[str, Any]:
        masked_answer_line = "Final answer: [ANSWER_MASK]"
        return {
            "trace_id": f"{swap_group_id}-{answer_variant}",
            "swap_group_id": swap_group_id,
            "quartet_id": problem_spec["quartet_id"],
            "problem_id": problem_spec["problem_id"],
            "domain": problem_spec["domain"],
            "verbalizer_id": "model_generated",
            "problem_text": problem_spec["problem_text"],
            "step_texts": generation["steps"],
            "final_answer_line": answer_line,
            "masked_answer_line": masked_answer_line,
            "trace_text": "\n".join(generation["steps"] + [answer_line]),
            "masked_trace_text": "\n".join(generation["steps"] + [masked_answer_line]),
            "answer_variant": answer_variant,
            "answer_is_correct": answer_is_correct,
            "metadata": metadata,
        }

    return [
        make_row("original", final_answer_line, is_correct),
        make_row("swapped", f"Final answer: {swapped_answer}", not is_correct if swapped_answer == problem_spec["correct_answer"] else False),
    ]


def generation_passes_audit(problem_spec: dict[str, Any], sample_index: int, generation: dict[str, Any]) -> tuple[bool, str]:
    rows = build_generated_records(problem_spec, sample_index, generation)
    original_row = next(row for row in rows if row["answer_variant"] == "original")
    if not original_row["answer_is_correct"]:
        return False, "incorrect_original_answer"
    audit = audit_generated_anchor(original_row)
    return audit.accepted, audit.reason


def summarize_generated_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    originals = [row for row in rows if row["answer_variant"] == "original"]
    return {
        "num_rows": len(rows),
        "num_original_traces": len(originals),
        "num_correct_original": sum(int(row["answer_is_correct"]) for row in originals),
        "num_incorrect_original": sum(int(not row["answer_is_correct"]) for row in originals),
    }
