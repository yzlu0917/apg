from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import random
import re
from statistics import mean
from typing import Any, Dict, Iterable, List, Sequence
import urllib.request

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


GSM8K_URLS = {
    "test": "https://raw.githubusercontent.com/openai/grade-school-math/master/grade_school_math/data/test.jsonl",
    "train": "https://raw.githubusercontent.com/openai/grade-school-math/master/grade_school_math/data/train.jsonl",
}

DEFAULT_QWEN3_1P7B = Path(
    "/cephfs/shared/hf_cache/hub/models--Qwen--Qwen3-1.7B/snapshots/70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
)

FEWSHOT_EXAMPLES = (
    {
        "question": "Mia had 12 apples. She gave 5 away and then bought 3 more apples. How many apples does she have now?",
        "solution": "1. Mia starts with 12 apples.\n2. She gives away 5 apples, so 12 - 5 = 7 apples remain.\n3. She buys 3 more apples, so 7 + 3 = 10.\nFinal answer: 10",
    },
    {
        "question": "A box has 4 rows of pencils with 6 pencils in each row. Sam removes 5 pencils. How many pencils are left?",
        "solution": "1. First find the total pencils: 4 * 6 = 24.\n2. Sam removes 5 pencils, so 24 - 5 = 19.\nFinal answer: 19",
    },
)

FINAL_ANSWER_VALUE_PATTERN = re.compile(
    r"Final answer:\s*([$]?\s*[-+]?\d[\d,]*(?:\.\d+)?%?)",
    flags=re.IGNORECASE,
)
FINAL_ANSWER_STUB_PATTERN = re.compile(r"Final answer:\s*$", flags=re.IGNORECASE)


@dataclass(frozen=True)
class MathExample:
    example_id: str
    question: str
    answer_text: str
    gold_answer: Decimal


@dataclass
class TraceRecord:
    example_id: str
    question: str
    gold_answer: str
    attempt_index: int
    prompt_style: str
    generated_text: str
    predicted_answer: str | None
    verified: bool
    step_texts: List[str]
    candidate_step_indices: List[int]
    completion_tokens: int

    def to_json(self) -> Dict[str, Any]:
        return {
            "example_id": self.example_id,
            "question": self.question,
            "gold_answer": self.gold_answer,
            "attempt_index": self.attempt_index,
            "prompt_style": self.prompt_style,
            "generated_text": self.generated_text,
            "predicted_answer": self.predicted_answer,
            "verified": self.verified,
            "step_texts": self.step_texts,
            "candidate_step_indices": self.candidate_step_indices,
            "completion_tokens": self.completion_tokens,
        }


def download_gsm8k(data_dir: Path, split: str) -> Path:
    if split not in GSM8K_URLS:
        raise ValueError(f"Unsupported split: {split}")
    data_dir.mkdir(parents=True, exist_ok=True)
    output_path = data_dir / f"{split}.jsonl"
    if output_path.exists():
        return output_path
    with urllib.request.urlopen(GSM8K_URLS[split], timeout=60) as response:
        output_path.write_bytes(response.read())
    return output_path


def _normalize_numeric_string(text: str) -> str:
    value = text.strip()
    value = value.replace(",", "")
    value = value.replace("$", "")
    value = value.replace("%", "")
    if value.endswith("."):
        value = value[:-1]
    return value


def parse_decimal(text: str) -> Decimal | None:
    value = _normalize_numeric_string(text)
    if not value:
        return None
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def extract_gold_answer(answer_text: str) -> Decimal:
    marker = answer_text.split("####")[-1]
    value = parse_decimal(marker)
    if value is None:
        raise ValueError(f"Could not parse GSM8K gold answer from: {answer_text}")
    return value


def extract_predicted_answer(generated_text: str) -> Decimal | None:
    final_match = FINAL_ANSWER_VALUE_PATTERN.findall(generated_text)
    if final_match:
        return parse_decimal(final_match[-1])
    numeric_matches = re.findall(r"[-+]?\d[\d,]*(?:\.\d+)?", generated_text)
    if numeric_matches:
        return parse_decimal(numeric_matches[-1])
    return None


def extract_verifiable_answer(generated_text: str) -> tuple[Decimal | None, str]:
    strict_match = FINAL_ANSWER_VALUE_PATTERN.findall(generated_text)
    if strict_match:
        return parse_decimal(strict_match[-1]), "strict_final_answer"
    if FINAL_ANSWER_STUB_PATTERN.search(generated_text):
        prefix_text = FINAL_ANSWER_STUB_PATTERN.sub("", generated_text, count=1)
        recovered = extract_predicted_answer(prefix_text)
        if recovered is not None:
            return recovered, "recovered_blank_final_answer"
        return None, "blank_final_answer_no_numeric"
    return None, "missing_final_answer"


def truncate_at_final_answer(generated_text: str) -> str:
    lines = []
    for line in generated_text.splitlines():
        lines.append(line.rstrip())
        if line.strip().lower().startswith("final answer:"):
            break
    return "\n".join(line for line in lines if line.strip()).strip()


def load_gsm8k(data_path: Path, limit: int | None = None, seed: int = 0) -> List[MathExample]:
    rows: List[MathExample] = []
    with data_path.open("r", encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            payload = json.loads(line)
            rows.append(
                MathExample(
                    example_id=f"gsm8k-{index:05d}",
                    question=payload["question"].strip(),
                    answer_text=payload["answer"].strip(),
                    gold_answer=extract_gold_answer(payload["answer"]),
                )
            )
    if limit is None or limit >= len(rows):
        return rows
    rng = random.Random(seed)
    indices = list(range(len(rows)))
    rng.shuffle(indices)
    chosen = sorted(indices[:limit])
    return [rows[index] for index in chosen]


def split_steps(generated_text: str) -> List[str]:
    lines = [line.strip() for line in generated_text.splitlines() if line.strip()]
    cleaned: List[str] = []
    for line in lines:
        if line.startswith("```"):
            break
        cleaned.append(line)
        if line.lower().startswith("final answer:"):
            break
    if not cleaned:
        return []
    numbered = [line for line in cleaned if re.match(r"^\d+\.", line)]
    if numbered:
        return numbered
    return cleaned


def choose_candidate_steps(step_texts: Sequence[str], max_candidates: int = 5) -> List[int]:
    if len(step_texts) <= max_candidates:
        return list(range(len(step_texts)))
    buckets: List[List[int]] = [[], [], []]
    for index in range(len(step_texts)):
        bucket_id = min((3 * index) // len(step_texts), 2)
        buckets[bucket_id].append(index)
    chosen: List[int] = []
    for bucket in buckets:
        if bucket:
            chosen.append(bucket[len(bucket) // 2])
    remaining = [index for index in range(len(step_texts)) if index not in chosen]
    remaining.sort(key=lambda index: (len(step_texts[index].split()), -index), reverse=True)
    for index in remaining:
        if len(chosen) >= max_candidates:
            break
        chosen.append(index)
    return sorted(chosen)


def build_prompt(question: str, prompt_style: str) -> str:
    intro_lines = [
        "You solve grade-school math problems.",
        "Write concise numbered reasoning steps.",
        "Use every numeric quantity in the problem when it matters.",
        "Finish with a final line exactly in the form: Final answer: <number>",
    ]
    blocks = ["\n".join(intro_lines), ""]
    for example in FEWSHOT_EXAMPLES:
        blocks.append(f"Problem: {example['question']}\nSolution:\n{example['solution']}")
        blocks.append("")
    if prompt_style == "repair":
        blocks.append("The previous attempt was incorrect. Re-solve carefully and check that every number in the problem is used consistently.")
        blocks.append("")
    blocks.append(f"Problem: {question}\nSolution:")
    return "\n".join(blocks)


class LocalQwenGenerator:
    def __init__(self, model_dir: Path, device: str, max_new_tokens: int) -> None:
        self.model_dir = model_dir
        self.device = device
        self.max_new_tokens = max_new_tokens
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_dir,
            local_files_only=True,
            dtype=torch.bfloat16,
            device_map=device,
        )

    def generate(self, prompt: str, max_new_tokens: int | None = None) -> tuple[str, int]:
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        output = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens or self.max_new_tokens,
            do_sample=False,
            pad_token_id=self.tokenizer.eos_token_id,
        )
        completion_ids = output[0][inputs["input_ids"].shape[1] :]
        text = self.tokenizer.decode(completion_ids, skip_special_tokens=True)
        return text.strip(), int(completion_ids.shape[0])


def collect_countertrace_mini_math(
    data_path: Path,
    output_dir: Path,
    model_dir: Path = DEFAULT_QWEN3_1P7B,
    device: str = "cuda:0",
    split: str = "test",
    max_examples: int = 24,
    target_successes: int = 6,
    max_new_tokens: int = 256,
    seed: int = 7,
) -> Dict[str, Any]:
    examples = load_gsm8k(data_path, limit=max_examples, seed=seed)
    generator = LocalQwenGenerator(model_dir=model_dir, device=device, max_new_tokens=max_new_tokens)
    output_dir.mkdir(parents=True, exist_ok=True)

    trace_rows: List[Dict[str, Any]] = []
    successful_trace_rows: List[Dict[str, Any]] = []
    attempted = 0

    for example in examples:
        if len(successful_trace_rows) >= target_successes:
            break
        for attempt_index, prompt_style in enumerate(("base", "repair"), start=1):
            attempted += 1
            prompt = build_prompt(example.question, prompt_style=prompt_style)
            generated_text, completion_tokens = generator.generate(prompt)
            generated_text = truncate_at_final_answer(generated_text)
            predicted = extract_predicted_answer(generated_text)
            verified = predicted == example.gold_answer if predicted is not None else False
            step_texts = split_steps(generated_text)
            candidate_step_indices = choose_candidate_steps(step_texts)
            record = TraceRecord(
                example_id=example.example_id,
                question=example.question,
                gold_answer=str(example.gold_answer),
                attempt_index=attempt_index,
                prompt_style=prompt_style,
                generated_text=generated_text,
                predicted_answer=str(predicted) if predicted is not None else None,
                verified=verified,
                step_texts=step_texts,
                candidate_step_indices=candidate_step_indices,
                completion_tokens=completion_tokens,
            )
            trace_rows.append(record.to_json())
            if verified:
                successful_trace_rows.append(record.to_json())
                break

    summary = {
        "dataset": "gsm8k",
        "split": split,
        "model_dir": str(model_dir),
        "device": device,
        "max_examples": max_examples,
        "target_successes": target_successes,
        "num_questions_considered": len(examples),
        "num_attempts": attempted,
        "num_verified_traces": len(successful_trace_rows),
        "verified_trace_rate_over_attempts": len(successful_trace_rows) / max(attempted, 1),
        "verified_trace_rate_over_questions": len(successful_trace_rows) / max(len(examples), 1),
        "mean_step_count_all": mean(len(row["step_texts"]) for row in trace_rows) if trace_rows else 0.0,
        "mean_step_count_verified": mean(len(row["step_texts"]) for row in successful_trace_rows) if successful_trace_rows else 0.0,
        "mean_candidate_steps_verified": mean(
            len(row["candidate_step_indices"]) for row in successful_trace_rows
        )
        if successful_trace_rows
        else 0.0,
        "successful_example_ids": [row["example_id"] for row in successful_trace_rows],
        "sample_verified_rows": successful_trace_rows[:3],
    }

    (output_dir / "math_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    with (output_dir / "math_traces.jsonl").open("w", encoding="utf-8") as handle:
        for row in trace_rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")
    with (output_dir / "math_success_traces.jsonl").open("w", encoding="utf-8") as handle:
        for row in successful_trace_rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")
    return {"summary": summary, "rows": trace_rows, "success_rows": successful_trace_rows}


def merge_countertrace_mini_runs(input_dirs: Sequence[Path], output_dir: Path) -> Dict[str, Any]:
    summaries: List[Dict[str, Any]] = []
    trace_rows: List[Dict[str, Any]] = []
    success_rows_by_example: Dict[str, Dict[str, Any]] = {}

    for input_dir in input_dirs:
        summary_path = input_dir / "math_summary.json"
        traces_path = input_dir / "math_traces.jsonl"
        success_path = input_dir / "math_success_traces.jsonl"
        summaries.append(json.loads(summary_path.read_text(encoding="utf-8")))
        with traces_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                trace_rows.append(json.loads(line))
        with success_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                success_rows_by_example.setdefault(row["example_id"], row)

    success_rows = [success_rows_by_example[key] for key in sorted(success_rows_by_example)]
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "dataset": summaries[0].get("dataset") if summaries else "gsm8k",
        "split": summaries[0].get("split") if summaries else "test",
        "num_input_runs": len(input_dirs),
        "input_dirs": [str(path) for path in input_dirs],
        "num_trace_rows_total": len(trace_rows),
        "num_unique_verified_traces": len(success_rows),
        "successful_example_ids": [row["example_id"] for row in success_rows],
        "child_run_meta": [
            {
                key: child.get(key)
                for key in ("device", "max_examples", "target_successes", "num_verified_traces", "seed", "model_dir")
            }
            for child in summaries
        ],
        "sample_verified_rows": success_rows[:3],
    }
    (output_dir / "math_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    with (output_dir / "math_traces.jsonl").open("w", encoding="utf-8") as handle:
        for row in trace_rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")
    with (output_dir / "math_success_traces.jsonl").open("w", encoding="utf-8") as handle:
        for row in success_rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")
    return {"summary": summary, "rows": trace_rows, "success_rows": success_rows}
