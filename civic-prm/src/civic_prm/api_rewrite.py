from __future__ import annotations

import json
import re
from collections import Counter
from typing import Any

from civic_prm.acceptance import filter_surface_feedback
from civic_prm.api_judge import APIJudgeClient


def _extract_json_object(text: str) -> dict[str, Any]:
    candidates = re.findall(r"\{.*\}", text, flags=re.DOTALL)
    for candidate in reversed(candidates):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    raise ValueError(f"could not parse JSON from response: {text[:200]}")


def _anchor_tokens(text: str) -> set[str]:
    anchors = set()
    anchors.update(re.findall(r"\[[^\]]+\]", text))
    anchors.update(re.findall(r"-?\d+(?:\.\d+)?", text))
    return {anchor.strip() for anchor in anchors if anchor.strip()}


def _strip_step_label(text: str) -> str:
    return re.sub(r"^(Step|Line|Reasoning|Candidate|Move)\s+\d+:\s*", "", text.strip())


def _strip_discourse_opener(text: str) -> str:
    return re.sub(r"^(First|Next|Then|After that|Now|Finally),\s*", "", text.strip(), flags=re.IGNORECASE)


def _sentence_case(text: str) -> str:
    if not text:
        return text
    return text[0].upper() + text[1:]


def _benchmark_acceptance_guidance() -> str:
    return (
        "Optimize for artifact cleanliness, not for hiding semantic wrongness. "
        "Remove non-semantic edit cues such as copied endings, one-sided scaffolding, overt discourse-marker asymmetry, "
        "near-copy-plus-one-patch structure, and mismatched polish or verbosity. "
        "It is acceptable if a mathematically or procedurally wrong step remains visibly wrong because of its content. "
        "Do not try to make invalid reasoning look semantically correct; only make the writing surface look independently written and free of obvious editing artifacts."
    )
def _normalize_algebra_step_surface(text: str) -> str:
    core = text.strip().rstrip(".")
    core = re.sub(r"^I(?:'ll| will)\s+", "", core, flags=re.IGNORECASE)
    core = re.sub(r"^I\s+", "", core, flags=re.IGNORECASE)
    core = re.sub(r"^we\s+", "", core, flags=re.IGNORECASE)
    core = re.sub(r"^we conclude that\s+", "", core, flags=re.IGNORECASE)
    return _sentence_case(core) + "."


def _extract_algebra_equation_fragment(text: str) -> str | None:
    match = re.search(r"([0-9xX()\s+\-]+=\s*-?\d+)", text)
    if not match:
        return None
    return re.sub(r"\s+", " ", match.group(1)).strip()


def _align_algebra_step_fragment(source_step: str, rewritten_step: str) -> str:
    source_fragment = _extract_algebra_equation_fragment(_strip_step_label(source_step))
    if source_fragment is None:
        return rewritten_step
    if source_fragment in rewritten_step:
        return rewritten_step
    rewritten_fragment = _extract_algebra_equation_fragment(rewritten_step)
    if rewritten_fragment is not None:
        return rewritten_step.replace(rewritten_fragment, source_fragment, 1)
    return rewritten_step.rstrip(".") + f" This gives {source_fragment}."


def _cancel_bias_text_local(bias: int) -> str:
    if bias >= 0:
        return f"Subtract {bias} from both sides"
    return f"Add {abs(bias)} to both sides"


def _undo_shift_text_local(shift: int) -> str:
    if shift >= 0:
        return f"Subtract {shift} from both sides"
    return f"Add {abs(shift)} to both sides"


def _canonicalize_algebra_benchmark_v3_step(record: dict[str, Any], step_index: int) -> str:
    source_step = record["step_texts"][step_index]
    fragment = _extract_algebra_equation_fragment(_strip_step_label(source_step)) or _strip_step_label(source_step).rstrip(".")
    metadata = record.get("metadata", {})
    prefixes = [
        f"{_cancel_bias_text_local(int(metadata.get('bias_b', 0)))} to get ",
        f"Divide both sides by {int(metadata.get('coeff_a', 1))} to get ",
        f"{_undo_shift_text_local(int(metadata.get('shift', 0)))} to get ",
    ]
    prefix = prefixes[min(step_index, len(prefixes) - 1)]
    return prefix + fragment + "."


def _domain_rewrite_guidance(record: dict[str, Any]) -> str:
    if record["domain"] == "algebra":
        return (
            "Keep the algebra trace sounding like someone talking through operations, not a bare equation dump. "
            "If a source step is mistaken, preserve the mistaken equation but present it as the writer's own algebra move. "
            "Keep the operation framing compact and parallel across steps instead of mixing very different registers."
        )
    if record["domain"] == "graph_path":
        return (
            "Avoid a rigid candidate-by-candidate scaffold. Vary sentence openings while keeping every route identity and stated total exact. "
            "Do not back-fill edge-by-edge arithmetic into a step that only states a recorded route total."
        )
    if record["domain"] == "blocksworld":
        return (
            "Use direct move-report style with the exact source action phrase, for example 'move block X ...'. "
            "Avoid pedagogical discourse markers such as First, Next, Then, Now, or Finally. "
            "Do not add explanatory narration about stack structure, desired arrangement, or why the move helps."
        )
    return ""


def _build_rewrite_messages(record: dict[str, Any]) -> list[dict[str, str]]:
    numbered_steps = "\n".join(
        f"{index + 1}. {step}" for index, step in enumerate(record["step_texts"])
    )
    algebra_fragments = ""
    if record["domain"] == "algebra":
        fragments = [
            _extract_algebra_equation_fragment(step) or _strip_step_label(step)
            for step in record["step_texts"]
        ]
        algebra_fragments = "\n\nExact algebra fragment to preserve in each step:\n" + "\n".join(
            f"{index + 1}. {fragment}" for index, fragment in enumerate(fragments)
        )
    domain_guidance = _domain_rewrite_guidance(record)
    return [
        {
            "role": "system",
            "content": (
                "Rewrite the following reasoning trace into natural language that sounds like an independently written solution. "
                "Preserve the same problem meaning, the same number of reasoning steps, and the same latent step content. "
                "Keep all equations, numeric values, graph paths, and block-state strings exact whenever they appear. "
                "You may change connective language, sentence shape, and local phrasing, but do not add or remove reasoning content. "
                "If the source contains an incorrect equation, keep that incorrect equation exactly rather than repairing it. "
                f"{_benchmark_acceptance_guidance()} "
                f"{domain_guidance} "
                "Avoid labels like Step 1 or Line 2. Do not mention that this is a rewrite. "
                'Reply with JSON only using keys "problem_text" and "steps".'
            ),
        },
        {
            "role": "user",
            "content": (
                "/no_think\n"
                f"Problem:\n{record['problem_text']}\n\n"
                f"Steps:\n{numbered_steps}\n\n"
                f"Return the same number of steps.{algebra_fragments}"
            ),
        },
    ]


def _build_problem_rewrite_messages(record: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "Rewrite the problem statement into natural language while preserving all concrete numbers, "
                "equations, graph edges, path tokens, and block-state strings exactly. "
                'Reply with JSON only using key "problem_text".'
            ),
        },
        {
            "role": "user",
            "content": f"/no_think\nProblem:\n{record['problem_text']}",
        },
    ]


def _build_pair_rewrite_messages(record_a: dict[str, Any], record_b: dict[str, Any]) -> list[dict[str, str]]:
    numbered_steps_a = "\n".join(
        f"{index + 1}. {step}" for index, step in enumerate(record_a["step_texts"])
    )
    numbered_steps_b = "\n".join(
        f"{index + 1}. {step}" for index, step in enumerate(record_b["step_texts"])
    )
    domain_guidance = _domain_rewrite_guidance(record_a) if record_a["domain"] == record_b["domain"] else ""
    return [
        {
            "role": "system",
            "content": (
                "Rewrite the following two reasoning traces into natural language that sounds like independently written solutions. "
                "The two traces solve the same problem. Rewrite them jointly so they do not look like one clean trace plus one patched edit. "
                "Preserve the same problem meaning, the same number of reasoning steps in each trace, and the same latent step content. "
                "Keep all equations, numeric values, graph paths, and block-state strings exact whenever they appear. "
                "If a source contains an incorrect equation or state claim, keep that incorrect content exactly rather than repairing it. "
                f"{_benchmark_acceptance_guidance()} "
                f"{domain_guidance} "
                "Vary local phrasing and cadence across the two traces, but do not add or remove reasoning content. "
                "Avoid labels like Step 1 or Trace 1. Do not mention that this is a rewrite. "
                'Reply with JSON only using keys "problem_text", "trace_1_steps", and "trace_2_steps".'
            ),
        },
        {
            "role": "user",
            "content": (
                "/no_think\n"
                f"Problem:\n{record_a['problem_text']}\n\n"
                f"Trace 1 steps:\n{numbered_steps_a}\n\n"
                f"Trace 2 steps:\n{numbered_steps_b}\n\n"
                "Return the same number of steps for each trace."
            ),
        },
    ]


def _build_pair_contrast_messages(record_a: dict[str, Any], record_b: dict[str, Any]) -> list[dict[str, str]]:
    numbered_steps_a = "\n".join(
        f"{index + 1}. {step}" for index, step in enumerate(record_a["step_texts"])
    )
    numbered_steps_b = "\n".join(
        f"{index + 1}. {step}" for index, step in enumerate(record_b["step_texts"])
    )
    domain_guidance = _domain_rewrite_guidance(record_a) if record_a["domain"] == record_b["domain"] else ""
    return [
        {
            "role": "system",
            "content": (
                "Rewrite the following two reasoning traces into natural language that sounds like two independently written solutions by similarly fluent writers. "
                "The two traces solve the same problem and will later be compared side by side. "
                "Keep both traces equally free of obvious editing artifacts. "
                "Do not let one trace become much more polished, much more heavily scaffolded, much more compressed, or much more obviously patched than the other. "
                "Do not make one trace a near-copy of the other with only one local textual patch. "
                "Preserve the same problem meaning, the same number of reasoning steps in each trace, and the same latent step content. "
                "Keep all equations, numeric values, graph paths, and block-state strings exact whenever they appear. "
                "If a source contains an incorrect equation or state claim, keep that incorrect content exactly rather than repairing it. "
                f"{_benchmark_acceptance_guidance()} "
                f"{domain_guidance} "
                "You may vary local wording and sentence rhythm, but do not optimize for total semantic indistinguishability. "
                "Avoid labels like Step 1 or Trace 1. Do not mention that this is a rewrite. "
                'Reply with JSON only using keys "problem_text", "trace_1_steps", and "trace_2_steps".'
            ),
        },
        {
            "role": "user",
            "content": (
                "/no_think\n"
                f"Problem:\n{record_a['problem_text']}\n\n"
                f"Trace 1 steps:\n{numbered_steps_a}\n\n"
                f"Trace 2 steps:\n{numbered_steps_b}\n\n"
                "Return the same number of steps for each trace. Optimize the pair for balanced side-by-side naturalness."
            ),
        },
    ]


def _build_pair_feedback_messages(
    record_a: dict[str, Any],
    record_b: dict[str, Any],
    feedback: list[str],
) -> list[dict[str, str]]:
    numbered_steps_a = "\n".join(
        f"{index + 1}. {step}" for index, step in enumerate(record_a["step_texts"])
    )
    numbered_steps_b = "\n".join(
        f"{index + 1}. {step}" for index, step in enumerate(record_b["step_texts"])
    )
    filtered_feedback = filter_surface_feedback(feedback)
    feedback_block = "\n".join(f"- {item}" for item in filtered_feedback) if filtered_feedback else "- remove surface asymmetry and patched-edit cues without hiding semantic wrongness"
    domain_guidance = _domain_rewrite_guidance(record_a) if record_a["domain"] == record_b["domain"] else ""
    return [
        {
            "role": "system",
            "content": (
                "Rewrite the following two reasoning traces into natural language that sounds like two independently written solutions by similarly fluent writers. "
                "The two traces solve the same problem and will later be compared side by side. "
                "The previous pair looked too patched or asymmetrical under blind review. "
                "Fix only the surface writing asymmetry; do not change the latent reasoning content, step count, equations, numbers, graph paths, or block states. "
                "Keep both traces equally free of obvious editing artifacts. "
                "Do not make one trace more polished, more scaffolded, or more compressed than the other. "
                "Do not make one trace a near-copy of the other with one local textual patch. "
                "If a source contains an incorrect equation or state claim, keep that incorrect content exactly rather than repairing it. "
                f"{_benchmark_acceptance_guidance()} "
                f"{domain_guidance} "
                "Avoid labels like Step 1 or Trace 1. Do not mention that this is a rewrite. "
                'Reply with JSON only using keys "problem_text", "trace_1_steps", and "trace_2_steps".'
            ),
        },
        {
            "role": "user",
            "content": (
                "/no_think\n"
                f"Problem:\n{record_a['problem_text']}\n\n"
                f"Artifact-level concerns to fix:\n{feedback_block}\n\n"
                f"Trace 1 steps:\n{numbered_steps_a}\n\n"
                f"Trace 2 steps:\n{numbered_steps_b}\n\n"
                "Return the same number of steps for each trace. Remove surface artifact cues while preserving exact latent content and without trying to hide semantic errors."
            ),
        },
    ]


def _build_step_rewrite_messages(record: dict[str, Any], step_text: str, step_index: int) -> list[dict[str, str]]:
    clean_step = _strip_step_label(step_text)
    if record["domain"] == "algebra":
        required_fragment = _extract_algebra_equation_fragment(clean_step) or clean_step
        domain_instruction = (
            "Rewrite this algebra step as a natural sentence that states the intended operation and the resulting equation. "
            "Do not answer with only a bare equation. If the source step is mistaken, preserve the mistaken equation exactly. "
            f'The final sentence must contain this exact algebra fragment verbatim: "{required_fragment}".'
        )
    elif record["domain"] == "graph_path":
        if step_index == len(record["step_texts"]) - 1:
            domain_instruction = (
                "Rewrite the comparison step naturally. Avoid a rigid comma-list if possible, but keep every route reference and total exact."
            )
        else:
            domain_instruction = (
                "Rewrite this route-cost step naturally. Vary the opening and keep the route identity and stated total exact. "
                "Do not introduce edge-by-edge arithmetic if the source step only reports a total."
            )
    elif record["domain"] == "blocksworld":
        domain_instruction = (
            "Rewrite this move in direct report style using the same move action as the source. "
            "Avoid discourse markers like First, Next, Then, Now, or Finally. "
            "Do not add extra narration about stack structure or goals."
        )
    else:
        domain_instruction = "Rewrite this step naturally while preserving the same content."
    return [
        {
            "role": "system",
            "content": (
                "Rewrite one reasoning step into a natural single sentence. "
                "Keep every equation fragment, numeric value, path string, or block-state string exact. "
                "Do not add step labels. Do not add or remove reasoning content. "
                f"{domain_instruction} "
                'Reply with JSON only using key "step_text".'
            ),
        },
        {
            "role": "user",
            "content": f"/no_think\nProblem:\n{record['problem_text']}\n\nStep:\n{clean_step}",
        },
    ]


def _coerce_steps_payload(record: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    steps = payload.get("steps")
    if not isinstance(steps, str) or record["domain"] != "algebra":
        return payload

    normalized = re.sub(r"\s+", " ", steps).strip()
    chunks = [
        chunk.strip()
        for chunk in re.split(r"(?=(?:First|Next|Then|Finally|After that)\b)", normalized)
        if chunk.strip()
    ]
    if len(chunks) != len(record["step_texts"]):
        return payload

    rewritten = dict(payload)
    rewritten["steps"] = chunks
    return rewritten


def _validate_rewrite(record: dict[str, Any], payload: dict[str, Any]) -> None:
    payload = _coerce_steps_payload(record, payload)
    if not isinstance(payload.get("problem_text"), str) or not payload["problem_text"].strip():
        raise ValueError("missing problem_text")
    steps = payload.get("steps")
    if not isinstance(steps, list) or len(steps) != len(record["step_texts"]):
        raise ValueError("wrong number of steps")
    for source_step, rewritten_step in zip(record["step_texts"], steps):
        if not isinstance(rewritten_step, str) or not rewritten_step.strip():
            raise ValueError("empty step")
        if re.search(r"^(Step|Line|Reasoning|Candidate|Move)\s+\d+:", rewritten_step.strip()):
            raise ValueError("step label leaked into rewrite")
        _validate_step_rewrite(source_step, rewritten_step, record["domain"])
    source_steps = [_strip_step_label(step) for step in record["step_texts"]]
    source_anchor_set = _anchor_tokens(record["problem_text"] + "\n" + "\n".join(source_steps))
    rewritten_text = payload["problem_text"] + "\n" + "\n".join(steps)
    rewritten_anchor_set = _anchor_tokens(rewritten_text)
    missing = [anchor for anchor in source_anchor_set if anchor not in rewritten_anchor_set]
    if missing:
        raise ValueError(f"missing anchor tokens: {missing[:5]}")
    _validate_graph_routes(record["problem_text"] + "\n" + "\n".join(source_steps), rewritten_text)


def _validate_problem_rewrite(record: dict[str, Any], problem_text: str) -> None:
    if not problem_text.strip():
        raise ValueError("empty problem rewrite")
    source_anchor_set = _anchor_tokens(record["problem_text"])
    rewritten_anchor_set = _anchor_tokens(problem_text)
    missing = [anchor for anchor in source_anchor_set if anchor not in rewritten_anchor_set]
    if missing:
        raise ValueError(f"missing problem anchors: {missing[:5]}")
    _validate_graph_routes(record["problem_text"], problem_text)


def _validate_step_rewrite(source_step: str, rewritten_step: str, domain: str) -> None:
    if not rewritten_step.strip():
        raise ValueError("empty step rewrite")
    if re.search(r"^(Step|Line|Reasoning|Candidate|Move)\s+\d+:", rewritten_step.strip()):
        raise ValueError("step label leaked into step rewrite")
    source_anchor_set = _anchor_tokens(_strip_step_label(source_step))
    rewritten_anchor_set = _anchor_tokens(rewritten_step)
    missing = [anchor for anchor in source_anchor_set if anchor not in rewritten_anchor_set]
    if missing:
        raise ValueError(f"missing step anchors: {missing[:5]}")
    if domain == "graph_path":
        unexpected = [
            anchor
            for anchor in rewritten_anchor_set
            if anchor not in source_anchor_set and re.fullmatch(r"-?\d+(?:\.\d+)?", anchor)
        ]
        if unexpected:
            raise ValueError(f"unexpected graph step anchors: {unexpected[:5]}")
    _validate_graph_routes(_strip_step_label(source_step), rewritten_step)


def _validate_graph_routes(source_text: str, rewritten_text: str) -> None:
    source_routes = re.findall(r"S\s*->\s*([A-Z])\s*->\s*([A-Z])\s*->\s*T", source_text)
    if not source_routes:
        return
    normalized = re.sub(r"\s+", "", rewritten_text)
    for left, right in source_routes:
        canonical = f"S->{left}->{right}->T"
        if canonical in normalized:
            continue
        if left in rewritten_text and right in rewritten_text and "S" in rewritten_text and "T" in rewritten_text:
            continue
        raise ValueError(f"missing graph route identity: {canonical}")


def _canonicalize_graph_paths(text: str) -> str:
    return re.sub(
        r"\bS\s+to\s+([A-Z])\s+to\s+([A-Z])\s+to\s+T\b",
        lambda match: f"S -> {match.group(1)} -> {match.group(2)} -> T",
        text,
        flags=re.IGNORECASE,
    )


def _extract_blocksworld_action_state(source_step: str) -> tuple[str, str] | None:
    core = _strip_step_label(source_step).strip().rstrip(".")
    match = re.match(r"(move block [a-z0-9 ]+(?:to the table|onto block [a-z0-9]+)),\s*reaching state\s+(.+)$", core, flags=re.IGNORECASE)
    if not match:
        return None
    action = _sentence_case(match.group(1).strip())
    state = match.group(2).strip()
    return action, state


def _normalize_blocksworld_step_surface(source_step: str, rewritten_step: str) -> str:
    extracted = _extract_blocksworld_action_state(source_step)
    if extracted is None:
        core = _strip_discourse_opener(rewritten_step).strip().rstrip(".")
        return _sentence_case(core) + "."
    action, state = extracted
    return f"{action}, reaching state {state}."


def _smooth_step_sequence(record: dict[str, Any], step_texts: list[str], rewriter_name: str) -> list[str]:
    if record["domain"] == "graph_path":
        return [_canonicalize_graph_paths(step) for step in step_texts]
    if record["domain"] == "blocksworld":
        return [
            _normalize_blocksworld_step_surface(record["step_texts"][index], step)
            for index, step in enumerate(step_texts)
        ]
    if record["domain"] != "algebra":
        return step_texts
    if record.get("metadata", {}).get("benchmark_v3"):
        return [
            _canonicalize_algebra_benchmark_v3_step(record, index)
            for index, _step in enumerate(step_texts)
        ]

    metadata = record.get("metadata", {})
    operations = [
        f"{_cancel_bias_text_local(int(metadata.get('bias_b', 0)))} to get ",
        f"Divide both sides by {int(metadata.get('coeff_a', 1))}, so ",
        f"{_undo_shift_text_local(int(metadata.get('shift', 0)))}, giving ",
    ]
    smoothed = []
    for index, step in enumerate(step_texts):
        core = _strip_discourse_opener(step).strip().rstrip(".")
        if rewriter_name == "ark-llm-v2-stepwise" and (
            "=" in core
            and not re.search(
                r"\b(add\w*|subtract\w*|divid\w*|isolat\w*|simplif\w*|solv\w*|giv\w*|result\w*|which|conclud\w*|after|carry\w*|cancel\w*)\b",
                core,
                flags=re.IGNORECASE,
            )
        ):
            prefix = operations[min(index, len(operations) - 1)]
            smoothed.append(_align_algebra_step_fragment(record["step_texts"][index], prefix + core + "."))
            continue
        smoothed.append(_align_algebra_step_fragment(record["step_texts"][index], _normalize_algebra_step_surface(core)))
    return smoothed


def _post_json(client: APIJudgeClient, messages: list[dict[str, str]], temperature: float, max_tokens: int) -> dict[str, Any]:
    payload = {
        "model": client.model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    return client._post_json(payload)


def _rewrite_record_stepwise_with_api(
    client: APIJudgeClient,
    record: dict[str, Any],
    temperature: float,
    max_tokens: int,
) -> dict[str, Any]:
    usage_totals = Counter()
    raw_chunks = []
    api_calls = 0

    try:
        problem_response = _post_json(client, _build_problem_rewrite_messages(record), temperature=temperature, max_tokens=max_tokens)
        api_calls += 1
        problem_content = problem_response["choices"][0]["message"]["content"]
        problem_payload = _extract_json_object(problem_content)
        problem_text = str(problem_payload.get("problem_text", "")).strip()
        _validate_problem_rewrite(record, problem_text)
        raw_chunks.append(problem_content)
        usage = problem_response.get("usage", {})
        usage_totals["prompt_tokens"] += usage.get("prompt_tokens", 0)
        usage_totals["completion_tokens"] += usage.get("completion_tokens", 0)
        usage_totals["total_tokens"] += usage.get("total_tokens", 0)
    except Exception:
        problem_text = record["problem_text"]

    step_texts: list[str] = []
    for step_index, source_step in enumerate(record["step_texts"]):
        step_response = _post_json(
            client,
            _build_step_rewrite_messages(record, source_step, step_index),
            temperature=temperature,
            max_tokens=max_tokens,
        )
        api_calls += 1
        step_content = step_response["choices"][0]["message"]["content"]
        step_payload = _extract_json_object(step_content)
        rewritten_step = str(step_payload.get("step_text", "")).strip()
        _validate_step_rewrite(source_step, rewritten_step, record["domain"])
        step_texts.append(rewritten_step)
        raw_chunks.append(step_content)
        usage = step_response.get("usage", {})
        usage_totals["prompt_tokens"] += usage.get("prompt_tokens", 0)
        usage_totals["completion_tokens"] += usage.get("completion_tokens", 0)
        usage_totals["total_tokens"] += usage.get("total_tokens", 0)

    return {
        "problem_text": problem_text,
        "step_texts": _smooth_step_sequence(record, step_texts, "ark-llm-v2-stepwise"),
        "raw_response": "\n---\n".join(raw_chunks),
        "usage": dict(usage_totals),
        "rewriter_name": "ark-llm-v2-stepwise",
        "api_calls": api_calls,
    }


def rewrite_record_with_api(
    client: APIJudgeClient,
    record: dict[str, Any],
    temperature: float = 0.8,
    max_tokens: int = 320,
) -> dict[str, Any]:
    try:
        response = _post_json(client, _build_rewrite_messages(record), temperature=temperature, max_tokens=max_tokens)
        content = response["choices"][0]["message"]["content"]
        parsed = _extract_json_object(content)
        parsed = _coerce_steps_payload(record, parsed)
        if record["domain"] == "algebra" and record.get("metadata", {}).get("benchmark_v3"):
            parsed["problem_text"] = record["problem_text"]
        _validate_rewrite(record, parsed)
        return {
            "problem_text": parsed["problem_text"].strip(),
            "step_texts": _smooth_step_sequence(
                record,
                [step.strip() for step in parsed["steps"]],
                "ark-llm-v2-fulltrace",
            ),
            "raw_response": content,
            "usage": response.get("usage", {}),
            "rewriter_name": "ark-llm-v2-fulltrace",
            "api_calls": 1,
        }
    except Exception:
        return _rewrite_record_stepwise_with_api(
            client,
            record,
            temperature=max(0.3, temperature - 0.2),
            max_tokens=max(128, max_tokens // 2),
        )


def rewrite_record_pair_with_api(
    client: APIJudgeClient,
    record_a: dict[str, Any],
    record_b: dict[str, Any],
    temperature: float = 0.8,
    max_tokens: int = 480,
    contrast_aware: bool = False,
    feedback: list[str] | None = None,
) -> dict[str, Any]:
    try:
        response = _post_json(
            client,
            (
                _build_pair_feedback_messages(record_a, record_b, feedback)
                if feedback
                else (_build_pair_contrast_messages(record_a, record_b) if contrast_aware else _build_pair_rewrite_messages(record_a, record_b))
            ),
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response["choices"][0]["message"]["content"]
        parsed = _extract_json_object(content)
        problem_text = str(parsed.get("problem_text", "")).strip()
        if record_a["domain"] == "algebra" and record_a.get("metadata", {}).get("benchmark_v3"):
            problem_text = record_a["problem_text"]
        steps_a = parsed.get("trace_1_steps")
        steps_b = parsed.get("trace_2_steps")
        payload_a = {
            "problem_text": problem_text,
            "steps": steps_a,
        }
        payload_b = {
            "problem_text": problem_text,
            "steps": steps_b,
        }
        payload_a = _coerce_steps_payload(record_a, payload_a)
        payload_b = _coerce_steps_payload(record_b, payload_b)
        _validate_rewrite(record_a, payload_a)
        _validate_rewrite(record_b, payload_b)
        return {
            "problem_text": problem_text,
            "trace_1_steps": _smooth_step_sequence(
                record_a,
                [step.strip() for step in payload_a["steps"]],
                "ark-llm-v3-pairfeedback" if feedback else ("ark-llm-v3-paircontrast" if contrast_aware else "ark-llm-v3-pairtrace"),
            ),
            "trace_2_steps": _smooth_step_sequence(
                record_b,
                [step.strip() for step in payload_b["steps"]],
                "ark-llm-v3-pairfeedback" if feedback else ("ark-llm-v3-paircontrast" if contrast_aware else "ark-llm-v3-pairtrace"),
            ),
            "raw_response": content,
            "usage": response.get("usage", {}),
            "rewriter_name": "ark-llm-v3-pairfeedback" if feedback else ("ark-llm-v3-paircontrast" if contrast_aware else "ark-llm-v3-pairtrace"),
            "api_calls": 1,
        }
    except Exception:
        rewrite_a = rewrite_record_with_api(
            client,
            record_a,
            temperature=max(0.3, temperature - 0.2),
            max_tokens=max(160, max_tokens // 2),
        )
        rewrite_b = rewrite_record_with_api(
            client,
            record_b,
            temperature=max(0.3, temperature - 0.2),
            max_tokens=max(160, max_tokens // 2),
        )
        usage_totals = Counter()
        for rewrite in [rewrite_a, rewrite_b]:
            usage = rewrite.get("usage", {})
            usage_totals["prompt_tokens"] += usage.get("prompt_tokens", 0)
            usage_totals["completion_tokens"] += usage.get("completion_tokens", 0)
            usage_totals["total_tokens"] += usage.get("total_tokens", 0)
            usage_totals["num_calls"] += rewrite.get("api_calls", 1)
        return {
            "problem_text": rewrite_a["problem_text"],
            "trace_1_steps": rewrite_a["step_texts"],
            "trace_2_steps": rewrite_b["step_texts"],
            "raw_response": rewrite_a["raw_response"] + "\n---PAIR-FALLBACK---\n" + rewrite_b["raw_response"],
            "usage": dict(usage_totals),
            "rewriter_name": "ark-llm-v3-pair-fallback",
            "api_calls": usage_totals["num_calls"],
        }
