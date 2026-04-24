from __future__ import annotations

from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


DEFAULT_RERANK_INSTRUCTION = (
    "Given a problem statement and a reasoning trace, judge whether the trace shows a valid "
    "reasoning process at the audited step. Rank traces with valid local reasoning above traces "
    "with invalid reasoning even when an invalid trace reaches the correct final answer by luck. "
    "Focus on process validity rather than answer correctness."
)

_PREFIX_TEMPLATE = (
    "<|im_start|>system\n"
    'Judge whether the Document meets the requirements based on the Query and the Instruct provided. '
    'Note that the answer can only be "yes" or "no".'
    "<|im_end|>\n"
    "<|im_start|>user\n"
)
_SUFFIX_TEMPLATE = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"


def load_qwen_reranker(model_root: str | Path):
    tokenizer = AutoTokenizer.from_pretrained(
        model_root,
        padding_side="left",
        trust_remote_code=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_root,
        dtype="auto",
        device_map="auto",
        trust_remote_code=True,
    )
    model.eval()
    return tokenizer, model


def build_reranker_query(record: dict) -> str:
    return (
        f"Problem:\n{record['problem_text']}\n\n"
        f"Audited step index: {record['audited_locus'] + 1}\n"
        "Question: Is the reasoning locally valid at the audited step?"
    )


def build_reranker_document(record: dict, answer_visible: bool) -> str:
    trace_text = record["trace_text"] if answer_visible else record["masked_trace_text"]
    return f"Trace:\n{trace_text}"


def format_reranker_pair(instruction: str, query: str, document: str) -> str:
    return f"<Instruct>: {instruction}\n<Query>: {query}\n<Document>: {document}"


def _build_prefix_suffix_tokens(tokenizer):
    prefix_tokens = tokenizer.encode(_PREFIX_TEMPLATE, add_special_tokens=False)
    suffix_tokens = tokenizer.encode(_SUFFIX_TEMPLATE, add_special_tokens=False)
    token_false_id = tokenizer.convert_tokens_to_ids("no")
    token_true_id = tokenizer.convert_tokens_to_ids("yes")
    return prefix_tokens, suffix_tokens, token_false_id, token_true_id


def _process_inputs(
    pairs: list[str],
    tokenizer,
    prefix_tokens: list[int],
    suffix_tokens: list[int],
    max_length: int,
):
    inputs = tokenizer(
        pairs,
        padding=False,
        truncation="longest_first",
        return_attention_mask=False,
        max_length=max_length - len(prefix_tokens) - len(suffix_tokens),
    )
    for index, token_ids in enumerate(inputs["input_ids"]):
        inputs["input_ids"][index] = prefix_tokens + token_ids + suffix_tokens
    padded = tokenizer.pad(inputs, padding=True, return_tensors="pt")
    return padded


@torch.inference_mode()
def score_reranker_pairs(
    pairs: list[str],
    tokenizer,
    model,
    batch_size: int = 2,
    max_length: int = 2048,
) -> list[float]:
    prefix_tokens, suffix_tokens, token_false_id, token_true_id = _build_prefix_suffix_tokens(tokenizer)
    scores: list[float] = []
    for start in range(0, len(pairs), batch_size):
        batch_pairs = pairs[start : start + batch_size]
        inputs = _process_inputs(
            batch_pairs,
            tokenizer=tokenizer,
            prefix_tokens=prefix_tokens,
            suffix_tokens=suffix_tokens,
            max_length=max_length,
        )
        inputs = {key: value.to(model.device) for key, value in inputs.items()}
        logits = model(**inputs).logits[:, -1, :]
        false_logits = logits[:, token_false_id]
        true_logits = logits[:, token_true_id]
        batch_scores = torch.stack([false_logits, true_logits], dim=1)
        batch_scores = torch.nn.functional.log_softmax(batch_scores, dim=1)
        scores.extend(batch_scores[:, 1].exp().detach().cpu().tolist())
    return scores
