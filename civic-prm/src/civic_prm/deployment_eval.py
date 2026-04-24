from __future__ import annotations

import json
import math
import re
import urllib.request
from pathlib import Path
from typing import Any

import torch

from civic_prm.prompt_verifier import _parse_response, load_model


def build_deployment_messages(record: dict[str, Any], answer_visible: bool) -> list[dict[str, str]]:
    trace_text = record["trace_text"] if answer_visible else record["masked_trace_text"]
    return [
        {
            "role": "system",
            "content": (
                "Assess whether the reasoning process is sound overall for the given problem. "
                "Focus on the quality of the reasoning, not just the final answer string. "
                'Reply with JSON only: {"score": <0-100 integer>, "verdict": "valid" or "invalid"}.'
            ),
        },
        {
            "role": "user",
            "content": f"/no_think\nProblem:\n{record['problem_text']}\n\nTrace:\n{trace_text}",
        },
    ]


def compute_swap_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_group = {}
    for row in rows:
        key = (row["swap_group_id"], row["answer_visible"])
        by_group.setdefault(key, {})[row["answer_variant"]] = row

    deltas = []
    correct_scores = []
    incorrect_scores = []
    for pair in by_group.values():
        if "original" in pair and "swapped" in pair:
            deltas.append(abs(pair["original"]["score"] - pair["swapped"]["score"]))
            for row in [pair["original"], pair["swapped"]]:
                if row["answer_is_correct"]:
                    correct_scores.append(row["score"])
                else:
                    incorrect_scores.append(row["score"])

    return {
        "num_scored_rows": len(rows),
        "num_swap_pairs": len(deltas),
        "ass_total": round(sum(deltas) / len(deltas), 4) if deltas else math.nan,
        "mean_score_correct_answer": round(sum(correct_scores) / len(correct_scores), 4) if correct_scores else math.nan,
        "mean_score_incorrect_answer": round(sum(incorrect_scores) / len(incorrect_scores), 4) if incorrect_scores else math.nan,
    }


@torch.inference_mode()
def score_local_record(tokenizer, model, record: dict[str, Any], answer_visible: bool) -> dict[str, Any]:
    messages = build_deployment_messages(record, answer_visible=answer_visible)
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    model_inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    generated = model.generate(
        **model_inputs,
        max_new_tokens=96,
        do_sample=False,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.eos_token_id,
    )
    response = tokenizer.decode(
        generated[0][model_inputs["input_ids"].shape[1] :],
        skip_special_tokens=True,
    ).strip()
    score, verdict = _parse_response(response)
    return {
        "trace_id": record["trace_id"],
        "swap_group_id": record["swap_group_id"],
        "domain": record["domain"],
        "answer_visible": answer_visible,
        "answer_variant": record["answer_variant"],
        "answer_is_correct": record["answer_is_correct"],
        "score": score,
        "verdict": verdict,
        "raw_response": response,
    }


class DeploymentAPIJudge:
    def __init__(self, base_url: str, model: str, api_key: str, timeout_seconds: int = 60) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def score_record(self, record: dict[str, Any], answer_visible: bool) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": build_deployment_messages(record, answer_visible=answer_visible),
            "temperature": 0,
            "max_tokens": 96,
        }
        req = urllib.request.Request(
            self.base_url + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        score, verdict = _parse_response(content)
        return {
            "trace_id": record["trace_id"],
            "swap_group_id": record["swap_group_id"],
            "domain": record["domain"],
            "answer_visible": answer_visible,
            "answer_variant": record["answer_variant"],
            "answer_is_correct": record["answer_is_correct"],
            "score": score,
            "verdict": verdict,
            "raw_response": content,
            "usage": body.get("usage", {}),
        }


def load_local_judge(model_root: str | Path):
    return load_model(model_root)
