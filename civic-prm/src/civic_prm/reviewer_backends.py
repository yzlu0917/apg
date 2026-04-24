from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from civic_prm.api_judge import APIJudgeClient


def _extract_json_object(text: str) -> dict[str, Any]:
    candidates = re.findall(r"\{.*\}", text, flags=re.DOTALL)
    for candidate in reversed(candidates):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    label_match = re.search(r'"more_artificial"\s*:\s*"(trace_1|trace_2|both|neither)"', text, flags=re.IGNORECASE)
    confidence_match = re.search(r'"confidence"\s*:\s*([1-5])', text)
    if label_match and confidence_match:
        reason_match = re.search(r'"reason"\s*:\s*"([^"]*)', text, flags=re.DOTALL)
        return {
            "more_artificial": label_match.group(1).lower(),
            "confidence": int(confidence_match.group(1)),
            "reason": (reason_match.group(1) if reason_match else "").strip(),
        }
    single_label_match = re.search(r'"looks_artificial"\s*:\s*"(yes|no|unclear)"', text, flags=re.IGNORECASE)
    if single_label_match and confidence_match:
        reason_match = re.search(r'"reason"\s*:\s*"([^"]*)', text, flags=re.DOTALL)
        return {
            "looks_artificial": single_label_match.group(1).lower(),
            "confidence": int(confidence_match.group(1)),
            "reason": (reason_match.group(1) if reason_match else "").strip(),
        }
    raise ValueError(f"could not parse JSON from reviewer response: {text[:200]}")


def _summarize_usage(usages: list[dict[str, int]]) -> dict[str, int]:
    totals = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    for usage in usages:
        totals["prompt_tokens"] += int(usage.get("prompt_tokens", 0))
        totals["completion_tokens"] += int(usage.get("completion_tokens", 0))
        totals["total_tokens"] += int(usage.get("total_tokens", 0))
    return totals


def _aggregate_pair_reviews(parsed_reviews: list[dict[str, Any]]) -> dict[str, Any]:
    labels = [str(item.get("more_artificial", "neither")).lower() for item in parsed_reviews]
    confidence = max(int(item.get("confidence", 1)) for item in parsed_reviews)
    label_set = set(labels)
    if "both" in label_set or ("trace_1" in label_set and "trace_2" in label_set):
        label = "both"
    elif "trace_1" in label_set:
        label = "trace_1"
    elif "trace_2" in label_set:
        label = "trace_2"
    else:
        label = "neither"
    reasons = [str(item.get("reason", "")).strip() for item in parsed_reviews if str(item.get("reason", "")).strip()]
    return {
        "more_artificial": label,
        "confidence": confidence,
        "reason": " | ".join(reasons[:2]),
    }


def _pair_penalty(review: dict[str, Any]) -> tuple[float, int]:
    label = str(review.get("more_artificial", "neither")).lower()
    confidence = int(review.get("confidence", 1))
    if label == "neither":
        return (0.0, confidence)
    if label == "both":
        return (0.5, confidence)
    return (0.5 + 0.1 * confidence, confidence)


def _aggregate_single_reviews(parsed_reviews: list[dict[str, Any]]) -> dict[str, Any]:
    labels = [str(item.get("looks_artificial", "unclear")).lower() for item in parsed_reviews]
    confidence = max(int(item.get("confidence", 1)) for item in parsed_reviews)
    if "yes" in labels:
        label = "yes"
    elif "unclear" in labels:
        label = "unclear"
    else:
        label = "no"
    reasons = [str(item.get("reason", "")).strip() for item in parsed_reviews if str(item.get("reason", "")).strip()]
    return {
        "looks_artificial": label,
        "confidence": confidence,
        "reason": " | ".join(reasons[:2]),
    }


def _single_penalty(review: dict[str, Any]) -> tuple[float, int]:
    label = str(review.get("looks_artificial", "unclear")).lower()
    confidence = int(review.get("confidence", 1))
    if label == "no":
        return (0.0, confidence)
    if label == "unclear":
        return (0.25, confidence)
    return (0.5 + 0.1 * confidence, confidence)


def _aggregate_pair_reviews_advmax(parsed_reviews: list[dict[str, Any]]) -> dict[str, Any]:
    winner = max(parsed_reviews, key=_pair_penalty)
    return {
        "more_artificial": str(winner.get("more_artificial", "neither")).lower(),
        "confidence": int(winner.get("confidence", 1)),
        "reason": str(winner.get("reason", "")).strip(),
    }


def _aggregate_single_reviews_advmax(parsed_reviews: list[dict[str, Any]]) -> dict[str, Any]:
    winner = max(parsed_reviews, key=_single_penalty)
    return {
        "looks_artificial": str(winner.get("looks_artificial", "unclear")).lower(),
        "confidence": int(winner.get("confidence", 1)),
        "reason": str(winner.get("reason", "")).strip(),
    }


class LocalChatReviewerClient:
    def __init__(
        self,
        model_root: str | Path,
        timeout_seconds: int = 60,
    ) -> None:
        del timeout_seconds
        self.model_root = str(model_root)
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_root,
            trust_remote_code=True,
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            model_root,
            dtype="auto",
            device_map="auto",
            trust_remote_code=True,
        )
        self.model.eval()

    @torch.inference_mode()
    def _post_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        messages = payload["messages"]
        max_tokens = int(payload.get("max_tokens", 96))
        prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        model_inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        generated = self.model.generate(
            **model_inputs,
            max_new_tokens=max_tokens,
            do_sample=False,
            eos_token_id=self.tokenizer.eos_token_id,
            pad_token_id=self.tokenizer.eos_token_id,
        )
        completion_ids = generated[0][model_inputs["input_ids"].shape[1] :]
        content = self.tokenizer.decode(completion_ids, skip_special_tokens=True).strip()
        usage = {
            "prompt_tokens": int(model_inputs["input_ids"].shape[1]),
            "completion_tokens": int(completion_ids.shape[0]),
            "total_tokens": int(model_inputs["input_ids"].shape[1] + completion_ids.shape[0]),
        }
        return {
            "choices": [{"message": {"content": content}}],
            "usage": usage,
        }


class EnsembleReviewerClient:
    def __init__(self, clients: list[Any], mode: str = "union") -> None:
        self.clients = clients
        self.mode = mode

    def _post_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        responses = []
        for client in self.clients:
            client_payload = dict(payload)
            if hasattr(client, "model") and "model" not in client_payload:
                client_payload["model"] = client.model
            responses.append(client._post_json(client_payload))
        contents = [response["choices"][0]["message"]["content"] for response in responses]
        parsed = [_extract_json_object(content) for content in contents]
        if "Trace 1:" in payload["messages"][-1]["content"] and "Trace 2:" in payload["messages"][-1]["content"]:
            if self.mode == "advmax":
                aggregate = _aggregate_pair_reviews_advmax(parsed)
            else:
                aggregate = _aggregate_pair_reviews(parsed)
        else:
            if self.mode == "advmax":
                aggregate = _aggregate_single_reviews_advmax(parsed)
            else:
                aggregate = _aggregate_single_reviews(parsed)
        usage = _summarize_usage([response.get("usage", {}) for response in responses])
        aggregate["ensemble_size"] = len(self.clients)
        aggregate["ensemble_mode"] = self.mode
        aggregate["member_outputs"] = contents
        return {
            "choices": [{"message": {"content": json.dumps(aggregate, ensure_ascii=False)}}],
            "usage": usage,
        }


def build_reviewer_client(
    backend: str,
    api_client: APIJudgeClient | None,
    reviewer_model_root: str | Path | None,
) -> Any:
    if backend == "api":
        if api_client is None:
            raise ValueError("api reviewer backend requires an API client")
        return api_client
    if reviewer_model_root is None:
        raise ValueError(f"reviewer backend {backend} requires --reviewer-model-root")
    local_client = LocalChatReviewerClient(model_root=reviewer_model_root)
    if backend == "local_qwen":
        return local_client
    if backend == "api_local_max":
        if api_client is None:
            raise ValueError("api_local_max reviewer backend requires an API client")
        return EnsembleReviewerClient([api_client, local_client], mode="union")
    if backend == "api_local_advmax":
        if api_client is None:
            raise ValueError("api_local_advmax reviewer backend requires an API client")
        return EnsembleReviewerClient([api_client, local_client], mode="advmax")
    raise ValueError(f"unsupported reviewer backend: {backend}")
