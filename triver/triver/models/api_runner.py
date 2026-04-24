from __future__ import annotations

import os
import time
from typing import Sequence

import requests

from triver.models.qwen_runner import GenerationResult


class ApiRunner:
    def __init__(
        self,
        model: str,
        api_key: str,
        base_url: str,
        tokenizer_path: str | None = None,
        timeout_sec: float = 120.0,
        max_retries: int = 3,
        retry_backoff_sec: float = 2.0,
    ) -> None:
        if not model:
            raise ValueError("API runner requires a non-empty model/endpoint name")
        if not api_key:
            raise ValueError("API runner requires a non-empty api_key")
        if not base_url:
            raise ValueError("API runner requires a non-empty base_url")
        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.tokenizer_path = tokenizer_path
        self.timeout_sec = timeout_sec
        self.max_retries = max_retries
        self.retry_backoff_sec = retry_backoff_sec
        self._tokenizer = None

    @property
    def tokenizer(self):
        if not self.tokenizer_path:
            return None
        if self._tokenizer is None:
            from transformers import AutoTokenizer

            self._tokenizer = AutoTokenizer.from_pretrained(self.tokenizer_path, trust_remote_code=True)
        return self._tokenizer

    def count_tokens(self, text: str) -> int:
        tokenizer = self.tokenizer
        if tokenizer is None:
            # Coarse fallback for API-only setups without a local tokenizer.
            return max(1, len(text) // 4)
        return len(tokenizer(text, add_special_tokens=False)["input_ids"])

    def generate(
        self,
        prompt: str | list[dict[str, str]],
        max_new_tokens: int,
        num_return_sequences: int = 1,
        temperature: float = 0.7,
        top_p: float = 0.9,
        seed: int | None = None,
    ) -> list[GenerationResult]:
        if num_return_sequences != 1:
            raise ValueError("ApiRunner currently supports only num_return_sequences=1")

        payload = {
            "model": self.model,
            "messages": self._messages_from_prompt(prompt),
            "max_tokens": max_new_tokens,
            "temperature": max(0.0, temperature),
            "top_p": top_p,
            "n": 1,
        }
        if seed is not None:
            payload["seed"] = seed

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout_sec,
                )
                response.raise_for_status()
                data = response.json()
                choice = data["choices"][0]
                text = self._extract_content(choice.get("message", {}).get("content", ""))
                usage = data.get("usage", {})
                completion_tokens = usage.get("completion_tokens")
                if completion_tokens is None:
                    completion_tokens = self.count_tokens(text)
                return [GenerationResult(text=text, new_tokens=int(completion_tokens))]
            except Exception as exc:  # requests/json/key errors are all surfaced with retry
                last_error = exc
                if attempt >= self.max_retries:
                    break
                time.sleep(self.retry_backoff_sec * attempt)

        raise RuntimeError(
            f"API generation failed after {self.max_retries} attempts "
            f"for model={self.model} base_url={self.base_url}"
        ) from last_error

    def _messages_from_prompt(self, prompt: str | list[dict[str, str]]) -> list[dict[str, str]]:
        if isinstance(prompt, str):
            return [{"role": "user", "content": prompt}]
        normalized: list[dict[str, str]] = []
        for message in prompt:
            normalized.append(
                {
                    "role": message.get("role", "user"),
                    "content": message.get("content", ""),
                }
            )
        return normalized

    def _extract_content(self, content: str | Sequence[object]) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, Sequence):
            chunks: list[str] = []
            for item in content:
                if isinstance(item, str):
                    chunks.append(item)
                elif isinstance(item, dict):
                    text = item.get("text")
                    if isinstance(text, str):
                        chunks.append(text)
            return "".join(chunks)
        return str(content)


def runner_from_env(
    *,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    tokenizer_path: str | None = None,
    timeout_sec: float = 120.0,
) -> ApiRunner:
    resolved_model = model or os.environ.get("TRIVER_API_MODEL", "")
    resolved_key = api_key or os.environ.get("TRIVER_API_KEY", "")
    resolved_base_url = base_url or os.environ.get("TRIVER_API_BASE_URL", "")
    return ApiRunner(
        model=resolved_model,
        api_key=resolved_key,
        base_url=resolved_base_url,
        tokenizer_path=tokenizer_path,
        timeout_sec=timeout_sec,
    )
