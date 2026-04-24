#!/usr/bin/env python3

import argparse
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SYSTEM_PROMPT = """You are evaluating verifier-guided revision decisions.

Return JSON only with this schema:
{
  "action_taken": "keep|revise|abstain",
  "final_output": "string",
  "notes": "short explanation"
}

Rules:
- Respect the requested condition.
- If you revise, produce the corrected final output in a concise canonical form.
- For code tasks, final_output should be code only.
- For exact-match arithmetic tasks, final_output should be the final answer only.
- For planning tasks, final_output should be the corrected ordered sequence only.
"""


_LOCAL_BACKEND_CACHE: dict[str, tuple[Any, Any]] = {}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--slice", required=True)
    parser.add_argument("--controls", required=True)
    parser.add_argument("--output-log", required=True)
    parser.add_argument("--output-summary", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--conditions",
        nargs="+",
        default=["direct", "procedure_retry", "gold_signal", "matched_shuffle"],
        choices=["direct", "procedure_retry", "gold_signal", "matched_shuffle"],
    )
    parser.add_argument(
        "--sample-filter",
        choices=["revise_only", "all"],
        default="revise_only",
    )
    parser.add_argument(
        "--provider",
        choices=["api", "local"],
        default="api",
    )
    parser.add_argument("--model", default="ep-20251213141929-gk2jb")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("CAVE_API_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
    )
    parser.add_argument("--api-key", default=os.environ.get("CAVE_API_KEY"))
    parser.add_argument("--request-timeout", type=float, default=60.0)
    parser.add_argument("--max-output-tokens", type=int, default=400)
    return parser.parse_args()


def load_jsonl(path: Path):
    items = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def parse_json_payload(text: str):
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


def normalize_text(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"```(?:python)?", "", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def canonical_plan(value: str) -> str:
    value = value.lower()
    value = re.sub(r"the correct (order|sequence) is:?", "", value)
    value = re.sub(r"[^a-z0-9,]+", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip(" ,")


def parse_schedule_ranges(value: str):
    matches = re.findall(r"\b([A-Z])\s*[:\[]\s*(\d+)\s*[-,]\s*(\d+)\b", value)
    if not matches:
        matches = re.findall(r"\b([A-Z])\s*\[\s*(\d+)\s*,\s*(\d+)\s*\]", value)
    schedule = {}
    for task, start, end in matches:
        schedule[task] = (int(start), int(end))
    return schedule


def parse_install_sequence(value: str):
    sequence = re.findall(r"install\s+([A-Z])", value, flags=re.IGNORECASE)
    return [item.upper() for item in sequence]


def parse_total_time(value: str):
    patterns = [
        r"total(?: completion)? time(?: is| =|:)?\s*(\d+)",
        r"finish(?:es)? at\s*(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, value, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def evaluate_constraint_check(checker: dict[str, Any], expected: str, final_output: str):
    mode = checker.get("constraint_mode")

    if mode == "scheduled_ranges":
        actual = parse_schedule_ranges(final_output)
        required = {
            task: tuple(bounds)
            for task, bounds in checker.get("required_ranges", {}).items()
        }
        if set(actual) != set(required):
            return False
        if any(actual[task] != required[task] for task in required):
            return False
        max_finish = checker.get("max_finish")
        if max_finish is not None and max(end for _, end in actual.values()) > max_finish:
            return False
        return True

    if mode == "ordered_sequence_total":
        sequence = parse_install_sequence(final_output)
        required_items = checker.get("required_items", [])
        if sorted(sequence) != sorted(required_items):
            return False
        positions = {item: index for index, item in enumerate(sequence)}
        for before, after in checker.get("precedence", []):
            if positions.get(before) is None or positions.get(after) is None:
                return False
            if positions[before] >= positions[after]:
                return False
        max_total = checker.get("max_total")
        total_time = parse_total_time(final_output)
        if max_total is not None:
            if total_time is None or total_time > max_total:
                return False
        return True

    return canonical_plan(final_output) == canonical_plan(expected)


def evaluate_checker(record, final_output: str):
    checker = record["checker"]
    checker_type = checker["type"]
    expected = record["expected_final_answer"]

    if checker_type == "exact_match":
        return normalize_text(final_output) == normalize_text(checker["reference"])

    if checker_type == "unit_test":
        code = final_output.strip()
        if code.startswith("```"):
            code = code.strip("`")
            code = code.replace("python", "", 1).strip()
        local_ns = {}
        try:
            exec(code, {}, local_ns)
            exec(checker["reference"], {}, local_ns)
            return True
        except Exception:
            return False

    if checker_type == "constraint_check":
        return evaluate_constraint_check(checker, expected, final_output)

    return False


def build_prompt(record, condition: str, control_lookup: dict[str, dict]):
    lines = [
        f"Condition: {condition}",
        f"Domain: {record['domain']}",
        f"Question: {record['question']}",
        f"Initial trace:\n{record['initial_trace']}",
    ]

    if condition == "gold_signal":
        lines.extend(
            [
                "Verifier signal:",
                f"- fail_span: {record['gold_fail_span']['text']}",
                f"- repair_hint: {record['gold_repair_suffix']}",
            ]
        )
    elif condition == "matched_shuffle":
        control = control_lookup[record["pair_id"]]
        lines.extend(
            [
                "Verifier signal:",
                f"- fail_span: {control['source_fail_span']['text']}",
                f"- repair_hint: {control['source_repair_suffix']}",
                f"- note: shuffled from pair {control['source_pair_id']}",
            ]
        )
    elif condition == "procedure_retry":
        lines.append(
            "Retry once from scratch without any verifier signal. You may keep, revise, or abstain."
        )
    else:
        lines.append(
            "Decide whether to keep, revise, or abstain based only on the question and initial trace."
        )

    lines.extend(
        [
            "Output instructions:",
            "- action_taken must be one of keep/revise/abstain.",
            "- final_output must be concise and canonical for the task type.",
            "- Return JSON only.",
        ]
    )
    return "\n".join(lines)


def call_api(*, model, base_url, api_key, request_timeout, max_output_tokens, prompt):
    import httpx
    from openai import OpenAI

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        http_client=httpx.Client(trust_env=False, timeout=request_timeout),
    )
    response = client.chat.completions.create(
        model=model,
        temperature=0.0,
        max_completion_tokens=max_output_tokens,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    text = response.choices[0].message.content
    payload = parse_json_payload(text)
    usage = response.usage.model_dump() if response.usage else {}
    return payload, usage


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


def call_local(*, model, prompt, max_output_tokens, backend=None):
    tokenizer, model_obj = backend or load_local_backend(model)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    prompt_text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    inputs = tokenizer(prompt_text, return_tensors="pt").to(model_obj.device)
    outputs = model_obj.generate(
        **inputs,
        do_sample=False,
        max_new_tokens=max_output_tokens,
    )
    new_tokens = outputs[0][inputs["input_ids"].shape[1] :]
    text = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
    return parse_json_payload(text), {}


def summarize(log_rows):
    by_condition = defaultdict(lambda: {"count": 0, "action_match": 0, "checker_pass": 0})
    total_tokens = 0
    for row in log_rows:
        bucket = by_condition[row["condition"]]
        bucket["count"] += 1
        bucket["action_match"] += int(row["action_taken"] == row["gold_action"])
        bucket["checker_pass"] += int(bool(row["checker_outcome"]))
        total_tokens += row["token_cost"]

    summary = {"total_rows": len(log_rows), "total_tokens": total_tokens, "by_condition": {}}
    for condition, bucket in by_condition.items():
        count = bucket["count"]
        summary["by_condition"][condition] = {
            "count": count,
            "action_match_rate": bucket["action_match"] / count if count else 0.0,
            "checker_pass_rate": bucket["checker_pass"] / count if count else 0.0,
        }
    return summary


def main():
    args = parse_args()
    if args.provider == "api" and not args.api_key:
        raise SystemExit("error: --api-key or CAVE_API_KEY is required")

    records = load_jsonl(Path(args.slice))
    if args.sample_filter == "revise_only":
        records = [r for r in records if r["gold_action"] == "revise"]

    controls = load_jsonl(Path(args.controls))
    control_lookup = {row["target_pair_id"]: row for row in controls}

    output_log = Path(args.output_log)
    output_log.parent.mkdir(parents=True, exist_ok=True)
    output_log.write_text("", encoding="utf-8")

    log_rows = []
    local_backend = load_local_backend(args.model) if args.provider == "local" else None

    for condition in args.conditions:
        for record in records:
            prompt = build_prompt(record, condition, control_lookup)
            if args.provider == "api":
                payload, usage = call_api(
                    model=args.model,
                    base_url=args.base_url,
                    api_key=args.api_key,
                    request_timeout=args.request_timeout,
                    max_output_tokens=args.max_output_tokens,
                    prompt=prompt,
                )
            else:
                payload, usage = call_local(
                    model=args.model,
                    prompt=prompt,
                    max_output_tokens=args.max_output_tokens,
                    backend=local_backend,
                )
            final_output = payload["final_output"]
            row = {
                "run_id": args.run_id,
                "slice_id": Path(args.slice).stem,
                "pair_id": record["pair_id"],
                "domain": record["domain"],
                "condition": condition,
                "model_or_system": args.model,
                "input_question": record["question"],
                "initial_trace": record["initial_trace"],
                "verifier_signal_used": (
                    {
                        "fail_span": record["gold_fail_span"]["text"],
                        "repair_suffix": record["gold_repair_suffix"],
                    }
                    if condition == "gold_signal"
                    else (
                        {
                            "fail_span": control_lookup[record["pair_id"]]["source_fail_span"]["text"],
                            "repair_suffix": control_lookup[record["pair_id"]]["source_repair_suffix"],
                            "source_pair_id": control_lookup[record["pair_id"]]["source_pair_id"],
                        }
                        if condition == "matched_shuffle"
                        else {"fail_span": "", "repair_suffix": ""}
                    )
                ),
                "action_taken": payload["action_taken"],
                "final_output": final_output,
                "checker_outcome": evaluate_checker(record, final_output),
                "token_cost": usage.get("total_tokens", 0),
                "notes": payload.get("notes", ""),
                "gold_action": record["gold_action"],
                "expected_final_answer": record["expected_final_answer"],
            }
            log_rows.append(row)
            with output_log.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(
                f"{condition} {record['pair_id']} action={row['action_taken']} "
                f"pass={row['checker_outcome']}",
                flush=True,
            )

    summary = summarize(log_rows)
    output_summary = Path(args.output_summary)
    output_summary.parent.mkdir(parents=True, exist_ok=True)
    output_summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote summary to {output_summary}")


if __name__ == "__main__":
    main()
