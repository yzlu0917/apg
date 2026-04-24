from __future__ import annotations

import json
import random
import re
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

ANSWER_MASK_TOKEN = "[ANSWER_MASK]"


def extract_answer_span(record: dict) -> str | None:
    trace_text = str(record["trace_text"])
    masked_trace_text = str(record["masked_trace_text"])
    if masked_trace_text.count(ANSWER_MASK_TOKEN) != 1:
        return None
    prefix, suffix = masked_trace_text.split(ANSWER_MASK_TOKEN, 1)
    if not trace_text.startswith(prefix):
        return None
    if suffix and not trace_text.endswith(suffix):
        return None
    start = len(prefix)
    end = len(trace_text) - len(suffix) if suffix else len(trace_text)
    answer_span = trace_text[start:end].strip()
    return answer_span or None


def is_maskable(record: dict) -> bool:
    return extract_answer_span(record) is not None


def select_maskable_examples(records: list[dict], per_domain: int, seed: int) -> list[dict]:
    by_domain: dict[str, list[dict]] = {}
    for record in records:
        if not is_maskable(record):
            continue
        by_domain.setdefault(record["domain"], []).append(record)

    selected: list[dict] = []
    rng = random.Random(seed)
    for domain in sorted(by_domain):
        buckets: dict[tuple[str, str], list[dict]] = {}
        for record in by_domain[domain]:
            key = (record["process_variant"], record["answer_variant"])
            buckets.setdefault(key, []).append(record)
        for rows in buckets.values():
            rows.sort(key=lambda row: row["trace_id"])
            rng.shuffle(rows)
        bucket_keys = sorted(buckets)
        domain_selected: list[dict] = []
        cursor = 0
        while len(domain_selected) < per_domain:
            added = False
            for key in bucket_keys:
                rows = buckets[key]
                if cursor < len(rows):
                    domain_selected.append(rows[cursor])
                    added = True
                    if len(domain_selected) >= per_domain:
                        break
            if not added:
                break
            cursor += 1
        selected.extend(domain_selected)
    return selected


def select_invalid_correct_maskable_examples(records: list[dict], per_domain: int, seed: int) -> list[dict]:
    candidates = [
        record
        for record in records
        if record["process_variant"] == "invalid"
        and record["answer_variant"] == "correct"
        and is_maskable(record)
    ]
    by_domain: dict[str, list[dict]] = {}
    for record in candidates:
        by_domain.setdefault(record["domain"], []).append(record)

    selected: list[dict] = []
    rng = random.Random(seed)
    for domain in sorted(by_domain):
        rows = sorted(by_domain[domain], key=lambda row: row["trace_id"])
        rng.shuffle(rows)
        selected.extend(rows[:per_domain])
    return selected


def build_swapped_record(record: dict, swapped_answer_text: str, source_answer_span: str) -> dict:
    swapped_trace_text = str(record["masked_trace_text"]).replace(ANSWER_MASK_TOKEN, swapped_answer_text)
    swapped = dict(record)
    swapped["trace_id"] = f"{record['trace_id']}::answer_swap"
    swapped["verbalizer_id"] = f"{record['verbalizer_id']}_answer_swap"
    swapped["answer_variant"] = "swapped"
    swapped["answer_is_correct"] = False
    swapped["trace_text"] = swapped_trace_text
    swapped["masked_trace_text"] = str(record["masked_trace_text"])
    swapped["metadata"] = {
        **dict(record.get("metadata", {})),
        "source_trace_id": record["trace_id"],
        "swap_group": "swapped",
        "source_answer_span": source_answer_span,
        "swapped_answer_span": swapped_answer_text,
    }
    return swapped


def build_observed_record(record: dict, source_answer_span: str) -> dict:
    observed = dict(record)
    observed["metadata"] = {
        **dict(record.get("metadata", {})),
        "source_trace_id": record["trace_id"],
        "swap_group": "observed",
        "source_answer_span": source_answer_span,
    }
    return observed


def replace_last_occurrence(text: str, old: str, new: str) -> str | None:
    index = text.rfind(old)
    if index < 0:
        return None
    return text[:index] + new + text[index + len(old) :]


def build_repaired_record(record: dict, repaired_steps: list[str], source_answer_span: str) -> dict:
    repaired_trace_text = "\n".join(step.strip() for step in repaired_steps if step.strip())
    masked_trace_text = replace_last_occurrence(repaired_trace_text, source_answer_span, ANSWER_MASK_TOKEN)
    if masked_trace_text is None:
        raise ValueError(f"failed to locate final answer span in repaired trace for {record['trace_id']}")
    repaired = dict(record)
    repaired["trace_id"] = f"{record['trace_id']}::repair"
    repaired["verbalizer_id"] = f"{record['verbalizer_id']}_repair"
    repaired["counterfactual_role"] = "repair"
    repaired["process_variant"] = "valid"
    repaired["is_valid_process"] = True
    repaired["step_texts"] = repaired_steps
    repaired["trace_text"] = repaired_trace_text
    repaired["masked_trace_text"] = masked_trace_text
    repaired["metadata"] = {
        **dict(record.get("metadata", {})),
        "source_trace_id": record["trace_id"],
        "repair_group": "repaired",
        "source_answer_span": source_answer_span,
    }
    return repaired


def save_records(records: list[dict], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def summarize_swap_dataset(records: list[dict]) -> dict:
    domains = Counter(record["domain"] for record in records)
    swap_groups = Counter(record.get("metadata", {}).get("swap_group", "unknown") for record in records)
    process_variants = Counter(record["process_variant"] for record in records)
    answer_variants = Counter(record["answer_variant"] for record in records)
    return {
        "num_records": len(records),
        "domains": dict(domains),
        "swap_groups": dict(swap_groups),
        "process_variants": dict(process_variants),
        "answer_variants": dict(answer_variants),
    }


def normalize_answer_span(text: str) -> str:
    normalized = text.strip().lower()
    normalized = normalized.replace("\\boxed", "")
    normalized = normalized.replace("\\(", "").replace("\\)", "")
    normalized = normalized.replace("$", "")
    normalized = re.sub(r"\s+", "", normalized)
    normalized = normalized.strip(".")
    normalized = re.sub(r"[^a-z0-9%+\-=/\.]+", "", normalized)
    numeric_match = re.fullmatch(r"([+\-]?\d+(?:\.\d+)?)(%?)", normalized)
    if numeric_match:
        value, suffix = numeric_match.groups()
        if "." in value:
            value = value.rstrip("0").rstrip(".")
        normalized = value + suffix
    return normalized


def swapped_answer_is_valid(source_answer_span: str, swapped_answer_text: str) -> bool:
    if not swapped_answer_text or ANSWER_MASK_TOKEN in swapped_answer_text:
        return False
    return normalize_answer_span(source_answer_span) != normalize_answer_span(swapped_answer_text)


def build_answer_swap_prompt(record: dict[str, Any], source_answer_span: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You rewrite only the final answer span of a math solution. "
                "Keep the reasoning unchanged. "
                "Return compact JSON only: "
                '{"answer_text": "<replacement final answer span>"}.\n'
                "The replacement must be different from the original answer span, "
                "must be short, and should preserve formatting style when possible "
                "(for example boxed notation, units, currency, or percent signs)."
            ),
        },
        {
            "role": "user",
            "content": (
                "/no_think\n"
                f"Problem:\n{record['problem_text']}\n\n"
                f"Original final answer span:\n{source_answer_span}\n\n"
                "Requirements:\n"
                "- Return only the replacement answer span, not a sentence.\n"
                "- Keep the style close to the original answer span.\n"
                "- Make the answer clearly different from the original.\n"
                "- Changing only spacing, braces, or LaTeX formatting is not enough; change the value or symbolic expression itself.\n"
                "- Do not include the literal token [ANSWER_MASK]."
            ),
        },
    ]


def build_repair_prompt(record: dict[str, Any], source_answer_span: str) -> list[dict[str, str]]:
    audited_step = int(record["audited_locus"]) + 1
    prefix_steps = record["step_texts"][: audited_step - 1]
    suffix_steps = record["step_texts"][audited_step - 1 :]
    prefix_block = "\n".join(f"{index + 1}. {step}" for index, step in enumerate(prefix_steps))
    suffix_block = "\n".join(
        f"{audited_step + offset}. {step}"
        for offset, step in enumerate(suffix_steps)
    )
    return [
        {
            "role": "system",
            "content": (
                "You repair a math solution trace. "
                "Return compact JSON only: {\"steps\": [\"...\", ...]}.\n"
                "Requirements:\n"
                "- Rewrite only the suffix starting at the audited step.\n"
                "- Fix the reasoning so the suffix is locally valid from the audited step onward.\n"
                "- Keep a one-to-one alignment with the original suffix steps; do not restart the solution from scratch.\n"
                "- Keep the final answer span exactly unchanged.\n"
                "- Keep the number of rewritten suffix steps exactly the same.\n"
                "- Keep each rewritten step concise, local, and no longer than the corresponding original suffix step when possible.\n"
                "- Do not perform exhaustive case searches if a direct local repair is possible.\n"
                "- Preserve the original style when possible.\n"
                "- Do not repeat the fixed prefix in the output.\n"
                "- Begin the response with the JSON object itself, not with explanation.\n"
                "- Do not add commentary outside the JSON object."
            ),
        },
        {
            "role": "user",
            "content": (
                "/no_think\n"
                f"Problem:\n{record['problem_text']}\n\n"
                f"Audited step index (1-based): {audited_step}\n"
                f"Final answer span that must stay exactly unchanged:\n{source_answer_span}\n\n"
                "Fixed prefix that must remain unchanged:\n"
                f"{prefix_block if prefix_block else '[empty prefix]'}\n\n"
                "Suffix to rewrite:\n"
                f"{suffix_block}\n\n"
                "Return only the rewritten suffix steps."
            ),
        },
    ]


class APIAnswerSwapClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str,
        timeout_seconds: int = 60,
        max_retries: int = 3,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def generate_swapped_answer(self, record: dict[str, Any], source_answer_span: str) -> dict[str, Any]:
        messages = build_answer_swap_prompt(record, source_answer_span)
        total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        last_swapped_answer_text = ""
        for semantic_attempt in range(self.max_retries):
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": 64,
            }
            response = self._post_json(payload)
            usage = response.get("usage", {})
            for key in total_usage:
                total_usage[key] += int(usage.get(key, 0))
            content = response["choices"][0]["message"]["content"]
            swapped_answer_text = self._parse_answer_text(content)
            last_swapped_answer_text = swapped_answer_text
            if swapped_answer_is_valid(source_answer_span, swapped_answer_text):
                return {
                    "source_trace_id": record["trace_id"],
                    "source_answer_span": source_answer_span,
                    "swapped_answer_span": swapped_answer_text,
                    "raw_response": content,
                    "usage": total_usage,
                }
            messages = [
                *messages,
                {"role": "assistant", "content": content},
                {
                    "role": "user",
                    "content": (
                        "That answer is not acceptable because it is identical or too close to the original answer. "
                        "Return a different final answer span only. Keep the style, but change the answer."
                    ),
                },
            ]
        raise RuntimeError(
            f"api returned invalid swapped answer span for {record['trace_id']}: {last_swapped_answer_text!r}"
        )

    def _parse_answer_text(self, text: str) -> str:
        stripped = text.strip()
        if stripped.startswith("```"):
            stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
            stripped = re.sub(r"\s*```$", "", stripped)
        try:
            payload = json.loads(stripped)
            answer_text = str(payload["answer_text"]).strip()
            if answer_text:
                return answer_text
        except Exception:
            pass
        match = re.search(r'"answer_text"\s*:\s*"((?:\\.|[^"])*)"', stripped, flags=re.DOTALL)
        if match:
            answer_text = match.group(1).strip()
            answer_text = answer_text.replace('\\"', '"').replace("\\\\", "\\")
            if answer_text:
                return answer_text
        object_matches = re.findall(r"\{.*?\}", stripped, flags=re.DOTALL)
        for candidate in reversed(object_matches):
            try:
                payload = json.loads(candidate)
                answer_text = str(payload["answer_text"]).strip()
                if answer_text:
                    return answer_text
            except Exception:
                continue
        return stripped

    def _post_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = self.base_url + "/chat/completions"
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        last_error: Exception | None = None
        for attempt in range(self.max_retries):
            request = urllib.request.Request(url, data=data, headers=headers)
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    body = response.read().decode("utf-8")
                return json.loads(body)
            except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError) as error:
                last_error = error
                if attempt + 1 == self.max_retries:
                    break
                time.sleep(2**attempt)
        raise RuntimeError(f"api request failed after {self.max_retries} attempts: {last_error}")


class APIProcessBenchRepairClient(APIAnswerSwapClient):
    def generate_repaired_steps(self, record: dict[str, Any], source_answer_span: str) -> dict[str, Any]:
        messages = build_repair_prompt(record, source_answer_span)
        total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        audited_locus = int(record["audited_locus"])
        original_prefix = list(record["step_texts"][:audited_locus])
        original_suffix_length = len(record["step_texts"][audited_locus:])
        last_steps: list[str] = []
        last_content = ""
        for _ in range(max(self.max_retries, 5)):
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.0,
                "max_tokens": min(1536, max(512, 160 * original_suffix_length)),
            }
            response = self._post_json(payload)
            usage = response.get("usage", {})
            for key in total_usage:
                total_usage[key] += int(usage.get(key, 0))
            content = response["choices"][0]["message"]["content"]
            last_content = content
            repaired_suffix_steps = self._parse_steps(content)
            repaired_steps = original_prefix + repaired_suffix_steps
            last_steps = repaired_steps
            if self._repair_is_valid(record, repaired_steps, source_answer_span):
                return {
                    "source_trace_id": record["trace_id"],
                    "source_answer_span": source_answer_span,
                    "repaired_steps": repaired_steps,
                    "raw_response": content,
                    "usage": total_usage,
                }
            messages = [
                *messages,
                {"role": "assistant", "content": content},
                {
                    "role": "user",
                    "content": (
                        "That repair is not acceptable. "
                        f"It must return exactly {original_suffix_length} rewritten suffix steps, "
                        f"must contain this exact final answer span verbatim in the last rewritten step: {source_answer_span!r}, "
                        "and must change the audited step into a locally valid one."
                    ),
                },
            ]
        raise RuntimeError(
            f"api returned invalid repaired steps for {record['trace_id']} at audited step {audited_locus + 1}: "
            f"parsed={last_steps!r} raw={last_content[:1600]!r}"
        )

    def _parse_steps(self, text: str) -> list[str]:
        stripped = text.strip()
        if stripped.startswith("```"):
            stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
            stripped = re.sub(r"\s*```$", "", stripped)
        try:
            payload = json.loads(self._stabilize_json_candidate(stripped))
            if isinstance(payload, str):
                return self._parse_steps(payload)
            steps = payload["steps"]
            if isinstance(steps, list):
                parsed = [str(step).strip() for step in steps if str(step).strip()]
                if parsed:
                    return parsed
        except Exception:
            pass
        decoder = json.JSONDecoder()
        object_starts = [match.start() for match in re.finditer(r'\{\s*"steps"\s*:', stripped)]
        for object_start in reversed(object_starts):
            try:
                payload, _ = decoder.raw_decode(self._stabilize_json_candidate(stripped[object_start:]))
                if isinstance(payload, str):
                    return self._parse_steps(payload)
                steps = payload["steps"]
                if isinstance(steps, list):
                    parsed = [str(step).strip() for step in steps if str(step).strip()]
                    if parsed:
                        return parsed
            except Exception:
                continue
        escaped_object_starts = [match.start() for match in re.finditer(r'\{\s*\\"steps\\"\s*:', stripped)]
        for object_start in reversed(escaped_object_starts):
            candidate = stripped[object_start:]
            object_end = candidate.rfind("}")
            if object_end < 0:
                continue
            candidate = candidate[: object_end + 1].replace('\\"', '"')
            try:
                payload = json.loads(self._stabilize_json_candidate(candidate))
                if isinstance(payload, str):
                    return self._parse_steps(payload)
                steps = payload["steps"]
                if isinstance(steps, list):
                    parsed = [str(step).strip() for step in steps if str(step).strip()]
                    if parsed:
                        return parsed
            except Exception:
                continue
        object_matches = re.findall(r"\{.*?\}", stripped, flags=re.DOTALL)
        for candidate in reversed(object_matches):
            try:
                payload = json.loads(self._stabilize_json_candidate(candidate))
                if isinstance(payload, str):
                    return self._parse_steps(payload)
                steps = payload["steps"]
                if isinstance(steps, list):
                    parsed = [str(step).strip() for step in steps if str(step).strip()]
                    if parsed:
                        return parsed
            except Exception:
                continue
        return [line.strip() for line in stripped.splitlines() if line.strip()]

    def _stabilize_json_candidate(self, candidate: str) -> str:
        # Models often emit LaTeX with lone backslashes inside JSON strings
        # (for example \boxed, \frac, \{, \}), which either decode into
        # control characters or make the JSON invalid. Re-escape any lone
        # backslash while leaving already doubled ones unchanged.
        return re.sub(r'(?<!\\)\\(?!\\)', r'\\\\', candidate)

    def _repair_is_valid(self, record: dict[str, Any], repaired_steps: list[str], source_answer_span: str) -> bool:
        if len(repaired_steps) != len(record["step_texts"]):
            return False
        if repaired_steps[int(record["audited_locus"])].strip() == str(record["step_texts"][int(record["audited_locus"])]).strip():
            return False
        repaired_trace_text = "\n".join(repaired_steps)
        return replace_last_occurrence(repaired_trace_text, source_answer_span, ANSWER_MASK_TOKEN) is not None
