from __future__ import annotations

import json
import hashlib
import re
from pathlib import Path
from typing import Any

import torch

from civic_prm.prompt_verifier import load_model
from civic_prm.schema import TraceExample


def _extract_json_object(text: str) -> dict[str, Any]:
    candidates = re.findall(r"\{.*\}", text, flags=re.DOTALL)
    for candidate in reversed(candidates):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    raise ValueError(f"could not parse JSON from response: {text[:200]}")


def _build_rewrite_messages(record: dict[str, Any]) -> list[dict[str, str]]:
    numbered_steps = "\n".join(
        f"{index + 1}. {step}" for index, step in enumerate(record["step_texts"])
    )
    return [
        {
            "role": "system",
            "content": (
                "Rewrite the following reasoning trace into more natural language while preserving "
                "the exact semantic content and the same number of reasoning steps, "
                "and all concrete numbers, symbols, graph nodes, or block states. "
                "Keep every equation fragment, path expression, and block-state string verbatim whenever it appears. "
                "Only rewrite the connective language around those exact expressions. "
                "Do not add or remove steps. Do not use labels like Step 1 or Line 2. "
                'Reply with JSON only using keys "problem_text" and "steps".'
            ),
        },
        {
            "role": "user",
            "content": (
                "/no_think\n"
                f"Problem:\n{record['problem_text']}\n\n"
                f"Steps:\n{numbered_steps}"
            ),
        },
    ]


def _lower_first_alpha(text: str) -> str:
    chars = list(text)
    for index, char in enumerate(chars):
        if char.isalpha():
            chars[index] = char.lower()
            break
    return "".join(chars)


def heuristic_naturalize_record(record: dict[str, Any]) -> dict[str, Any]:
    stripped_steps = [
        re.sub(r"^(Step|Line|Reasoning|Candidate|Move)\s+\d+:\s*", "", step).strip()
        for step in record["step_texts"]
    ]
    templates = [
        "{core}",
        "From there, {core_lc}",
        "At this point, {core_lc}",
        "So {core_lc}",
        "That leaves {core_lc}",
    ]
    rewritten_steps = []
    for index, step in enumerate(stripped_steps):
        digest = hashlib.md5(f"{record['trace_id']}::{index}".encode("utf-8")).hexdigest()
        template = templates[int(digest[:8], 16) % len(templates)]
        rewritten_steps.append(
            template.format(
                core=step,
                core_lc=_lower_first_alpha(step),
            )
        )

    problem_text = record["problem_text"]
    algebra_match = re.search(r"(?:equation|in|if)\s+(.+?)\.$", record["problem_text"])
    if record["domain"] == "algebra" and algebra_match:
        problem_text = f"Work out x in {algebra_match.group(1)}."
    return {
        "problem_text": problem_text,
        "step_texts": rewritten_steps,
        "raw_response": "[heuristic_fallback]",
        "naturalizer_name": "heuristic-fallback",
    }


def _anchor_tokens(text: str) -> set[str]:
    anchors = set()
    anchors.update(re.findall(r"\[[^\]]+\]", text))
    anchors.update(re.findall(r"-?\d+(?:\.\d+)?", text))
    anchors.update(re.findall(r"[A-Z](?:\s*->\s*[A-Z])+", text))
    return {anchor.strip() for anchor in anchors if anchor.strip()}


def _extract_answer_surface(record: dict[str, Any]) -> str:
    if "[ANSWER_MASK]" not in record["masked_answer_line"]:
        raise ValueError("masked_answer_line missing [ANSWER_MASK]")
    prefix, suffix = record["masked_answer_line"].split("[ANSWER_MASK]")
    if not record["final_answer_line"].startswith(prefix) or not record["final_answer_line"].endswith(suffix):
        raise ValueError("cannot align answer surface")
    return record["final_answer_line"][len(prefix) : len(record["final_answer_line"]) - len(suffix) if suffix else None]


def _validate_rewrite(record: dict[str, Any], payload: dict[str, Any]) -> None:
    if not isinstance(payload.get("problem_text"), str) or not payload["problem_text"].strip():
        raise ValueError("missing problem_text")
    steps = payload.get("steps")
    if not isinstance(steps, list) or len(steps) != len(record["step_texts"]):
        raise ValueError("wrong number of steps")
    for rewritten_step in steps:
        if not isinstance(rewritten_step, str) or not rewritten_step.strip():
            raise ValueError("empty step")
    source_anchor_set = _anchor_tokens(record["problem_text"] + "\n" + "\n".join(record["step_texts"]))
    rewritten_text = payload["problem_text"] + "\n" + "\n".join(steps)
    rewritten_anchor_set = _anchor_tokens(rewritten_text)
    missing = [anchor for anchor in source_anchor_set if anchor not in rewritten_anchor_set]
    if missing:
        raise ValueError(f"missing anchor tokens: {missing[:5]}")


@torch.inference_mode()
def naturalize_record(tokenizer, model, record: dict[str, Any], max_new_tokens: int = 320) -> dict[str, Any]:
    messages = _build_rewrite_messages(record)
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    model_inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    generated = model.generate(
        **model_inputs,
        max_new_tokens=max_new_tokens,
        do_sample=False,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.eos_token_id,
    )
    response = tokenizer.decode(
        generated[0][model_inputs["input_ids"].shape[1] :],
        skip_special_tokens=True,
    ).strip()
    payload = _extract_json_object(response)
    _validate_rewrite(record, payload)
    return {
        "problem_text": payload["problem_text"].strip(),
        "step_texts": [step.strip() for step in payload["steps"]],
        "raw_response": response,
        "naturalizer_name": "qwen3-1.7b",
    }


def build_naturalized_example(record: dict[str, Any], rewrite: dict[str, Any], naturalizer_name: str) -> TraceExample:
    final_answer_line = record["final_answer_line"]
    masked_answer_line = record["masked_answer_line"]
    trace_text = "\n".join(rewrite["step_texts"] + [final_answer_line])
    masked_trace_text = "\n".join(rewrite["step_texts"] + [masked_answer_line])
    metadata = dict(record.get("metadata", {}))
    metadata.update(
        {
            "naturalized": True,
            "naturalizer_name": naturalizer_name,
            "source_trace_id": record["trace_id"],
        }
    )
    return TraceExample(
        trace_id=f"{record['trace_id']}-natural",
        quartet_id=record["quartet_id"],
        problem_id=record["problem_id"],
        domain=record["domain"],
        verbalizer_id=f"{record['verbalizer_id']}_natural",
        audited_locus=record["audited_locus"],
        counterfactual_role=record["counterfactual_role"],
        process_variant=record["process_variant"],
        answer_variant=record["answer_variant"],
        is_valid_process=record["is_valid_process"],
        answer_is_correct=record["answer_is_correct"],
        problem_text=rewrite["problem_text"],
        step_texts=rewrite["step_texts"],
        final_answer_line=final_answer_line,
        masked_answer_line=masked_answer_line,
        trace_text=trace_text,
        masked_trace_text=masked_trace_text,
        metadata=metadata,
    )


def load_naturalizer(model_root: str | Path):
    return load_model(model_root)
