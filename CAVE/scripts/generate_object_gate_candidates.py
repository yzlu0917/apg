#!/usr/bin/env python3

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from validate_object_gate_seed import validate_pairs, validate_record


SYSTEM_PROMPT = """You are generating bootstrap candidates for the CAVE object gate.

Goal:
- Produce paired interventions for causal verifier evaluation.
- Each pair must contain one keep example and one revise example.
- The pair must use the same question, with only a local intervention changed.
- Output must be valid JSON only.

Schema:
{
  "pair_id": "string",
  "domain": "sym|code|plan",
  "question": "string",
  "examples": [
    {
      "id": "string",
      "initial_trace": "string",
      "gold_fail_span": {"text": "string", "kind": "string"},
      "gold_action": "keep|revise",
      "gold_repair_suffix": "string",
      "expected_final_answer": "string",
      "checker": {"type": "string", "reference": "string"},
      "utility_delta": {"keep": number, "revise": number, "abstain": number},
      "notes": "string"
    }
  ]
}

Hard constraints:
- Exactly 2 examples.
- One example must have gold_action = keep, empty fail span text, and fail span kind = "none".
- One example must have gold_action = revise and non-empty fail span text.
- The revise example must be locally fixable.
- Do not include abstain in this stage.
- Keep the tasks exact-checkable.
- Keep and revise must share the same question and the same intended correct final answer.
- The revise example must contain a real local error in the initial_trace, not just a different but valid rewrite.
- For revise examples, fail span text must be at least expression-level or line-level, not a single vague token.
- For revise examples, gold_repair_suffix must be a usable corrected continuation with enough context to apply the fix, not just a fragment like "== 0" or "**2" or "should be 44".
- If the correct repair is to delete a buggy line or block, gold_repair_suffix must still be non-empty and show the corrected continuation after that deletion.
- checker must always be an object with keys "type" and "reference". Never output a bare string like "unit_test".
- pair_id must be unique and should include the domain plus a seed/index-derived suffix.
- Avoid fancy formatting, markdown fences, or extra explanation.
"""


DOMAIN_INSTRUCTIONS = {
    "sym": """Create a small symbolic or arithmetic reasoning task.
Use a single local arithmetic or logic error in the revise example.
The checker should be exact_match.
Keep tasks short and unambiguous.
The initial_trace should show concrete intermediate calculations, not just a bare expression.
The revise example must keep the same underlying problem and same correct answer, but include one wrong intermediate calculation or propagated value inside the trace.
The repair suffix should restate the corrected local step and the corrected final answer.""",
    "code": """Create a small Python coding task.
Use a single-line or tightly local bug in the revise example.
The checker should be unit_test with one or two simple assertions.
Keep code short and executable-looking.
The fail span should be a whole buggy expression or line.
The revise code must actually fail the stated tests.
Do not make keep and revise semantically equivalent.
The repair suffix should be the corrected line or corrected continuation, not a token fragment.
The expected_final_answer should be the actual corrected code or exact target behavior, not a vague phrase like "passes unit tests".
Make the tests strong enough to rule out nearby but wrong algorithms, not just the gold local patch.""",
    "plan": """Create a small planning or ordering task.
Use a local dependency or ordering violation in the revise example.
The checker should be constraint_check with a compact constraint description.
Keep the plan short and fully specified.
The revise example must actually violate at least one explicit checker constraint.
Do not label a valid order as revise; the wrong trace must fail under the stated constraints.
By default, the checker reference should state the real order or dependency in plain language, unless a family-domain override explicitly asks for a structured checker format.
Do not use a weak constraint that both keep and revise satisfy.
The notes must name the violated constraint in plain language.
The repair suffix should explicitly show the corrected local ordering or continuation.""",
}

PROFILE_INSTRUCTIONS = {
    "standard": """Keep the pair simple and clearly checkable.""",
    "harder": """Make the pair harder while staying exact-checkable.
The revise example should still be locally fixable, but the error should be less
obvious than a trivial typo.
Prefer one of:
- a later-step arithmetic propagation error,
- a locally wrong operator or loop update that still looks plausible,
- a planning violation that requires respecting multiple nearby constraints.
Do not turn the task into a multi-error or open-ended case.""",
}

FAMILY_INSTRUCTIONS = {
    "default": """Use the standard CAVE paired-intervention setup.""",
    "contrastive_locality": """Build examples where verifier content should matter more than generic retry.
Requirements:
- Prefer `code` and `plan` style tasks over pure arithmetic unless arithmetic is unusually diagnostic.
- The revise example should have at least two nearby plausible local fixes, but only one is actually correct under the checker.
- A generic retry should be tempted to rewrite or choose a plausible but wrong local fix.
- The gold repair suffix should disambiguate among nearby candidate fixes, not just restate the obvious answer.
- The checker must disambiguate the plausible local fixes. Do not use tests or constraints that accidentally allow multiple fixes.
- For `code`, make sure the unit tests, the natural-language spec, and the intended correct code all agree.
- For `code`, do not cite semantically equivalent edits as alternative fixes. The checker must reject the plausible wrong alternatives.
- For `code`, avoid alternative fixes that are only syntactic variants of the gold fix or that are behaviorally identical on all valid inputs.
- For `code`, include edge-case tests that rule out hidden spec ambiguities or nearby non-gold algorithms.
- For `plan`, avoid trivial three-step total orders with one obvious repair. Prefer at least four items or mixed scheduling constraints where at least two local reorderings look plausible but only one satisfies every constraint.
- For `plan`, the revise trace must fail the stated constraints in an obvious, checkable way. Do not rely on a mistaken explanation about why a valid order is wrong.
- Avoid tasks where recomputing from scratch is trivial.
- Keep the task exact-checkable and still locally repairable.
""",
}

FAMILY_DOMAIN_OVERRIDES = {
    ("contrastive_locality", "plan"): """Extra requirements for plan in this family:
- Do not use free-form prose schedule constraints as the checker.
- Use a structured local-repair plan object with four or five single-letter tasks such as A, B, C, D.
- Keep both traces as compact order strings like `A -> D -> B -> C`.
- The checker reference must be a JSON string with this schema:
  {
    "schema": "plan_local_repair_v1",
    "tasks": ["A", "B", "C", "D"],
    "edges": [["A", "B"], ["B", "C"], ["D", "C"]],
    "locality": {"kind": "adjacent_swap", "max_swaps": 1}
  }
- Choose the revise trace so it is invalid under the edges, and so the adjacent-swap neighborhood of the revise trace contains at least two plausible candidate repairs.
- Exactly one adjacent-swap neighbor of the revise trace must satisfy the edges, and that unique valid neighbor must be the keep trace.
- Avoid trivial single-chain edge sets where every local repair is obvious.
- In notes, name one nearby wrong adjacent-swap repair that still looks plausible but fails the checker.
"""
}


_LOCAL_BACKEND_CACHE: dict[str, tuple[Any, Any]] = {}


def parse_json_payload(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        for index, char in enumerate(text):
            if char != "{":
                continue
            try:
                payload, _ = decoder.raw_decode(text[index:])
                return payload
            except json.JSONDecodeError:
                continue
    raise ValueError(f"could not parse JSON payload from model output: {text[:200]!r}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--provider",
        choices=["api", "local"],
        default="api",
        help="Generation backend.",
    )
    parser.add_argument(
        "--domains",
        nargs="+",
        default=["sym", "code", "plan"],
        choices=sorted(DOMAIN_INSTRUCTIONS),
        help="Domains to generate.",
    )
    parser.add_argument(
        "--pairs-per-domain",
        type=int,
        default=1,
        help="Number of pairs to request per domain.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to write JSONL candidates.",
    )
    parser.add_argument(
        "--meta-output",
        help="Optional path to write run metadata JSON.",
    )
    parser.add_argument(
        "--model",
        default="ep-20251213141929-gk2jb",
        help="API model name or local model path.",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("CAVE_API_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
        help="API base URL.",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("CAVE_API_KEY"),
        help="API key. Defaults to CAVE_API_KEY env var.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Sampling temperature.",
    )
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=1200,
        help="API max completion tokens.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=31,
        help="Random seed for pair ids and local generation.",
    )
    parser.add_argument(
        "--request-timeout",
        type=float,
        default=60.0,
        help="Per-request timeout in seconds for API calls.",
    )
    parser.add_argument(
        "--profile",
        choices=["standard", "harder"],
        default="standard",
        help="Generation profile.",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=3,
        help="Maximum attempts per requested pair before failing.",
    )
    parser.add_argument(
        "--family",
        choices=sorted(FAMILY_INSTRUCTIONS),
        default="default",
        help="Prompt family for candidate construction.",
    )
    return parser.parse_args()


@dataclass
class GenerationResult:
    payload: dict[str, Any]
    usage: dict[str, Any] | None
    raw_text: str


def build_user_prompt(domain: str, index: int, seed: int, profile: str, family: str) -> str:
    extra = FAMILY_DOMAIN_OVERRIDES.get((family, domain), "")
    prompt = (
        f"Domain: {domain}\n"
        f"Pair index: {index}\n"
        f"Seed: {seed}\n"
        f"Profile: {profile}\n"
        f"Family: {family}\n"
        f"Instructions:\n{DOMAIN_INSTRUCTIONS[domain]}\n"
        f"Profile instructions:\n{PROFILE_INSTRUCTIONS[profile]}\n"
        f"Family instructions:\n{FAMILY_INSTRUCTIONS[family]}\n"
        "Return one JSON object following the schema."
    )
    if extra:
        prompt = prompt.replace(
            "Return one JSON object following the schema.",
            f"Family-domain overrides:\n{extra}\nReturn one JSON object following the schema.",
        )
    return prompt


def call_api(
    *,
    model: str,
    base_url: str,
    api_key: str,
    user_prompt: str,
    temperature: float,
    max_output_tokens: int,
    request_timeout: float,
) -> GenerationResult:
    import httpx
    from openai import OpenAI

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        http_client=httpx.Client(trust_env=False, timeout=request_timeout),
    )
    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        max_completion_tokens=max_output_tokens,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    text = response.choices[0].message.content
    return GenerationResult(
        payload=parse_json_payload(text),
        usage=response.usage.model_dump() if response.usage else None,
        raw_text=text,
    )


def call_local(
    *,
    model: str,
    user_prompt: str,
    temperature: float,
    max_output_tokens: int,
    backend: tuple[Any, Any] | None = None,
) -> GenerationResult:
    tokenizer, model_obj = backend or load_local_backend(model)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    inputs = tokenizer(prompt, return_tensors="pt").to(model_obj.device)
    outputs = model_obj.generate(
        **inputs,
        do_sample=True,
        temperature=temperature,
        max_new_tokens=max_output_tokens,
    )
    new_tokens = outputs[0][inputs["input_ids"].shape[1] :]
    text = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
    return GenerationResult(payload=parse_json_payload(text), usage=None, raw_text=text)


def load_local_backend(model: str) -> tuple[Any, Any]:
    if model not in _LOCAL_BACKEND_CACHE:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(model, trust_remote_code=True)
        model_obj = AutoModelForCausalLM.from_pretrained(
            model,
            torch_dtype="auto",
            device_map="auto",
            trust_remote_code=True,
        )
        _LOCAL_BACKEND_CACHE[model] = (tokenizer, model_obj)
    return _LOCAL_BACKEND_CACHE[model]


def normalize_payload(payload: dict[str, Any], domain: str, family: str) -> list[dict[str, Any]]:
    pair_id = payload["pair_id"]
    question = payload["question"]
    records = []
    for example in payload["examples"]:
        span = example["gold_fail_span"]
        utility = dict(example["utility_delta"])
        for key in ("keep", "revise", "abstain"):
            utility.setdefault(key, 0.0)
        if example["gold_action"] == "keep":
            span = {"text": "", "kind": "none"}
            repair_suffix = ""
        else:
            repair_suffix = example["gold_repair_suffix"]
        record = {
            "id": example["id"],
            "pair_id": pair_id,
            "domain": domain,
            "question": question,
            "initial_trace": example["initial_trace"],
            "gold_fail_span": span,
            "gold_action": example["gold_action"],
            "gold_repair_suffix": repair_suffix,
            "expected_final_answer": example["expected_final_answer"],
            "checker": example["checker"],
            "utility_delta": utility,
            "notes": example["notes"],
            "candidate_source": "model_generated",
            "generation_family": family,
            "review_status": "pending",
        }
        records.append(record)
    return records


def validate_payload_shape(payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise ValueError("payload is not a JSON object")
    required_top_level = ["pair_id", "question", "examples"]
    missing = [key for key in required_top_level if key not in payload]
    if missing:
        raise ValueError(f"payload missing required top-level keys: {', '.join(missing)}")
    if not isinstance(payload["examples"], list) or len(payload["examples"]) != 2:
        raise ValueError("payload.examples must be a list of exactly 2 examples")


def validate_normalized_records(records: list[dict[str, Any]]) -> None:
    validated_records = []
    for line_no, record in enumerate(records, start=1):
        checked = dict(record)
        checked["_line_no"] = line_no
        validate_record(checked)
        validated_records.append(checked)
    validate_pairs(validated_records)


def try_parse_reference_json(reference: str) -> dict[str, Any] | None:
    if not isinstance(reference, str):
        return None
    stripped = reference.strip()
    if not stripped.startswith("{"):
        return None
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def parse_order_from_tasks(trace: str, tasks: list[str]) -> list[str]:
    import re

    hits: list[tuple[int, str]] = []
    for task in tasks:
        for match in re.finditer(rf"\b{re.escape(task)}\b", trace):
            hits.append((match.start(), task))
    hits.sort()
    seen: set[str] = set()
    order: list[str] = []
    for _, task in hits:
        if task in seen:
            continue
        seen.add(task)
        order.append(task)
    return order


def validate_order(order: list[str], tasks: set[str], edges: list[tuple[str, str]]) -> bool:
    if set(order) != tasks or len(order) != len(tasks):
        return False
    position = {task: index for index, task in enumerate(order)}
    return all(position[left] < position[right] for left, right in edges)


def enumerate_adjacent_swap_neighbors(order: list[str]) -> list[list[str]]:
    neighbors: list[list[str]] = []
    for index in range(len(order) - 1):
        swapped = list(order)
        swapped[index], swapped[index + 1] = swapped[index + 1], swapped[index]
        neighbors.append(swapped)
    return neighbors


def validate_family_semantics(records: list[dict[str, Any]], domain: str, family: str) -> None:
    if family != "contrastive_locality" or domain != "plan":
        return

    by_action = {record["gold_action"]: record for record in records}
    keep = by_action["keep"]
    revise = by_action["revise"]
    checker = keep["checker"]
    if checker.get("type") != "constraint_check":
        raise ValueError("contrastive_locality plan requires checker.type = constraint_check")

    structured = try_parse_reference_json(checker["reference"])
    if not structured or structured.get("schema") != "plan_local_repair_v1":
        raise ValueError("contrastive_locality plan requires structured checker schema plan_local_repair_v1")

    tasks = structured.get("tasks", [])
    raw_edges = structured.get("edges", [])
    locality = structured.get("locality", {})
    if (
        not isinstance(tasks, list)
        or len(tasks) < 4
        or not all(isinstance(task, str) and task for task in tasks)
        or locality.get("kind") != "adjacent_swap"
        or locality.get("max_swaps", 1) != 1
    ):
        raise ValueError("structured plan checker must define 4+ tasks and adjacent_swap locality")

    edges: list[tuple[str, str]] = []
    for edge in raw_edges:
        if (
            not isinstance(edge, list)
            or len(edge) != 2
            or not all(isinstance(item, str) and item for item in edge)
        ):
            raise ValueError("structured plan checker contains malformed edge")
        edges.append((edge[0], edge[1]))

    task_set = set(tasks)
    keep_order = parse_order_from_tasks(keep["initial_trace"], tasks)
    revise_order = parse_order_from_tasks(revise["initial_trace"], tasks)
    if not validate_order(keep_order, task_set, edges):
        raise ValueError("structured plan keep order does not satisfy precedence edges")
    if validate_order(revise_order, task_set, edges):
        raise ValueError("structured plan revise order already satisfies precedence edges")

    neighbors = enumerate_adjacent_swap_neighbors(revise_order)
    if len(neighbors) < 2:
        raise ValueError("structured plan revise order has too few adjacent-swap neighbors")
    valid_neighbors = [order for order in neighbors if validate_order(order, task_set, edges)]
    if len(valid_neighbors) != 1:
        raise ValueError(
            f"structured plan revise order has {len(valid_neighbors)} valid adjacent-swap repairs, expected exactly 1"
        )
    if keep_order != valid_neighbors[0]:
        raise ValueError("structured plan keep order is not the unique valid adjacent-swap repair")


def generate_one_pair(args: argparse.Namespace, *, domain: str, index: int, local_backend):
    errors: list[dict[str, Any]] = []
    for attempt in range(1, args.max_attempts + 1):
        user_prompt = build_user_prompt(domain, index, args.seed + index, args.profile, args.family)
        try:
            if args.provider == "api":
                result = call_api(
                    model=args.model,
                    base_url=args.base_url,
                    api_key=args.api_key,
                    user_prompt=user_prompt,
                    temperature=args.temperature,
                    max_output_tokens=args.max_output_tokens,
                    request_timeout=args.request_timeout,
                )
            else:
                result = call_local(
                    model=args.model,
                    user_prompt=user_prompt,
                    temperature=args.temperature,
                    max_output_tokens=args.max_output_tokens,
                    backend=local_backend,
                )
            validate_payload_shape(result.payload)
            records = normalize_payload(result.payload, domain, args.family)
            validate_normalized_records(records)
            validate_family_semantics(records, domain, args.family)
            return result, records, errors
        except Exception as exc:  # noqa: BLE001
            errors.append(
                {
                    "attempt": attempt,
                    "error": str(exc),
                    "raw_text": result.raw_text if "result" in locals() else "",
                }
            )
    error_summary = "; ".join(f"attempt {e['attempt']}: {e['error']}" for e in errors)
    raise RuntimeError(f"failed to generate valid pair for domain={domain} index={index}: {error_summary}")


def main() -> int:
    args = parse_args()
    random.seed(args.seed)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("", encoding="utf-8")

    if args.provider == "api" and not args.api_key:
        print("error: --api-key or CAVE_API_KEY is required for provider=api", file=sys.stderr)
        return 2

    all_records: list[dict[str, Any]] = []
    usage_log: list[dict[str, Any]] = []
    failure_log: list[dict[str, Any]] = []
    local_backend: tuple[Any, Any] | None = None

    if args.provider == "local":
        local_backend = load_local_backend(args.model)

    for domain in args.domains:
        for index in range(args.pairs_per_domain):
            result, records, errors = generate_one_pair(
                args,
                domain=domain,
                index=index,
                local_backend=local_backend,
            )
            if errors:
                failure_log.append(
                    {
                        "domain": domain,
                        "pair_index": index,
                        "errors": errors,
                    }
                )
            all_records.extend(records)
            with output_path.open("a", encoding="utf-8") as handle:
                for record in records:
                    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            usage_log.append(
                {
                    "domain": domain,
                    "pair_index": index,
                    "pair_id": result.payload.get("pair_id"),
                    "usage": result.usage,
                    "raw_text": result.raw_text,
                }
            )
            print(
                f"generated pair {result.payload.get('pair_id')} "
                f"for domain={domain} index={index}",
                flush=True,
            )

    if args.meta_output:
        meta_path = Path(args.meta_output)
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        meta = {
            "provider": args.provider,
            "model": args.model,
            "domains": args.domains,
            "pairs_per_domain": args.pairs_per_domain,
            "profile": args.profile,
            "family": args.family,
            "temperature": args.temperature,
            "seed": args.seed,
            "max_attempts": args.max_attempts,
            "usage_log": usage_log,
            "failure_log": failure_log,
        }
        with meta_path.open("w", encoding="utf-8") as handle:
            json.dump(meta, handle, ensure_ascii=False, indent=2)

    print(f"wrote {len(all_records)} records to {output_path}")
    if args.meta_output:
        print(f"wrote metadata to {args.meta_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
