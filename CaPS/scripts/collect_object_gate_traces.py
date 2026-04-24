#!/usr/bin/env python3

import argparse
import json
import re
from pathlib import Path

from reasoning_gym.factory import get_score_answer_fn
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from vllm import LLM, SamplingParams


REASONING_RE = re.compile(r"<reasoning>\s*(.*?)\s*</reasoning>", re.DOTALL | re.IGNORECASE)
FINAL_RE = re.compile(r"<final>\s*(.*?)\s*</final>", re.DOTALL | re.IGNORECASE)
THINK_RE = re.compile(r"<think>\s*(.*?)\s*</think>", re.DOTALL | re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect minimal Object-gate traces from a manifest.")
    parser.add_argument("--manifest", required=True, help="Path to input manifest JSONL.")
    parser.add_argument("--output", required=True, help="Path to output traces JSONL.")
    parser.add_argument("--model-path", required=True, help="Local HF snapshot path for the model.")
    parser.add_argument("--limit", type=int, default=8, help="Number of prompts to sample from the manifest.")
    parser.add_argument("--start", type=int, default=0, help="Start offset inside the manifest.")
    parser.add_argument("--temperature", type=float, default=0.6)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--tensor-parallel-size", type=int, default=1)
    parser.add_argument(
        "--backend",
        choices=["auto", "vllm", "transformers"],
        default="auto",
        help="Inference backend. auto tries vllm first, then falls back to transformers.",
    )
    parser.add_argument(
        "--enable-thinking",
        action="store_true",
        help="Allow the Qwen chat template to open a native <think> block.",
    )
    parser.add_argument(
        "--assistant-prefill",
        default="",
        help="Optional assistant prefix to continue from, e.g. '<reasoning>\\n'.",
    )
    return parser.parse_args()


def load_rows(path: Path, start: int, limit: int) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle):
            if idx < start:
                continue
            if len(rows) >= limit:
                break
            rows.append(json.loads(line))
    return rows


def extract_tag(text: str, pattern: re.Pattern[str]) -> str | None:
    match = pattern.search(text)
    if not match:
        return None
    return match.group(1).strip()


def extract_reasoning(text: str, assistant_prefill: str) -> str | None:
    reasoning = extract_tag(text, REASONING_RE)
    if reasoning is not None:
        return reasoning

    if "<reasoning>" in assistant_prefill and "</reasoning>" in text:
        return text.split("</reasoning>", 1)[0].strip()

    reasoning = extract_tag(text, THINK_RE)
    if reasoning is not None:
        return reasoning

    return None


def build_chat_prompts(
    tokenizer: AutoTokenizer,
    rows: list[dict],
    enable_thinking: bool,
    assistant_prefill: str,
) -> list[str]:
    prompts = []
    for row in rows:
        messages = [{"role": "user", "content": row["model_prompt"]}]
        if assistant_prefill:
            messages.append({"role": "assistant", "content": assistant_prefill})
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=not bool(assistant_prefill),
            continue_final_message=bool(assistant_prefill),
            enable_thinking=enable_thinking,
        )
        prompts.append(prompt)
    return prompts


def resolve_assistant_prefill(row: dict, cli_prefill: str) -> str:
    if cli_prefill:
        return cli_prefill
    return row.get("output_contract", {}).get("assistant_prefill", "")


def generate_with_vllm(args: argparse.Namespace, prompts: list[str]) -> list[str]:
    llm = LLM(
        model=args.model_path,
        tokenizer=args.model_path,
        trust_remote_code=True,
        tensor_parallel_size=args.tensor_parallel_size,
    )
    sampling_params = SamplingParams(
        temperature=args.temperature,
        top_p=args.top_p,
        max_tokens=args.max_tokens,
    )
    outputs = llm.generate(prompts, sampling_params)
    return [out.outputs[0].text for out in outputs]


def generate_with_transformers(
    args: argparse.Namespace,
    prompts: list[str],
    tokenizer: AutoTokenizer,
) -> list[str]:
    model = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
        attn_implementation="sdpa",
    )
    generated_texts: list[str] = []
    eos_token_id = tokenizer.eos_token_id

    for prompt in prompts:
        model_inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            generated = model.generate(
                **model_inputs,
                do_sample=True,
                temperature=args.temperature,
                top_p=args.top_p,
                max_new_tokens=args.max_tokens,
                eos_token_id=eos_token_id,
                pad_token_id=eos_token_id,
            )
        new_tokens = generated[0][model_inputs["input_ids"].shape[1] :]
        text = tokenizer.decode(new_tokens, skip_special_tokens=False)
        generated_texts.append(text)

    return generated_texts


def main() -> None:
    args = parse_args()

    manifest_path = Path(args.manifest)
    output_path = Path(args.output)
    rows = load_rows(manifest_path, args.start, args.limit)
    if not rows:
        raise ValueError(f"No rows loaded from {manifest_path}")

    tokenizer = AutoTokenizer.from_pretrained(args.model_path, trust_remote_code=True)
    resolved_prefills = []
    for row in rows:
        resolved_prefill = resolve_assistant_prefill(row, args.assistant_prefill)
        resolved_prefills.append(resolved_prefill)

    prompts = [
        build_chat_prompts(tokenizer, [row], args.enable_thinking, prefill)[0]
        for row, prefill in zip(rows, resolved_prefills)
    ]

    backend_used = args.backend
    if args.backend in {"auto", "vllm"}:
        try:
            generated_texts = generate_with_vllm(args, prompts)
            backend_used = "vllm"
        except Exception as exc:
            if args.backend == "vllm":
                raise
            print(f"vllm_failed: {type(exc).__name__}: {exc}")
            generated_texts = generate_with_transformers(args, prompts, tokenizer)
            backend_used = "transformers"
    else:
        generated_texts = generate_with_transformers(args, prompts, tokenizer)
        backend_used = "transformers"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row, text, resolved_prefill in zip(rows, generated_texts, resolved_prefills):
            reasoning = extract_reasoning(text, resolved_prefill)
            final = extract_tag(text, FINAL_RE)
            score_fn = get_score_answer_fn(row["family"])
            entry = {
                "question": row["raw_question"],
                "answer": row["oracle_answer"],
                "metadata": row["metadata"],
            }
            score = score_fn(final, entry) if final is not None else 0.0
            record = {
                "prompt_id": row["prompt_id"],
                "split": row["split"],
                "difficulty_stratum": row["difficulty_stratum"],
                "family": row["family"],
                "backend": backend_used,
                "enable_thinking": args.enable_thinking,
                "model_path": args.model_path,
                "assistant_prefill": resolved_prefill,
                "temperature": args.temperature,
                "top_p": args.top_p,
                "max_tokens": args.max_tokens,
                "raw_completion": text,
                "reasoning": reasoning,
                "final": final,
                "reasoning_present": reasoning is not None,
                "final_present": final is not None,
                "format_ok": reasoning is not None and final is not None,
                "score": score,
                "oracle_answer": row["oracle_answer"],
                "metadata": row["metadata"],
            }
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")

    summary = {
        "output": str(output_path),
        "count": len(rows),
        "backend": backend_used,
        "format_ok_count": sum(
            1
            for line in output_path.read_text(encoding="utf-8").splitlines()
            if json.loads(line)["format_ok"]
        ),
        "nonzero_score_count": sum(
            1
            for line in output_path.read_text(encoding="utf-8").splitlines()
            if json.loads(line)["score"] > 0.0
        ),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
