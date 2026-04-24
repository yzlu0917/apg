from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from civic_prm.prompt_verifier import _parse_response, build_prompt, compute_pilot_metrics


class APIJudgeClient:
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

    def score_record(self, record: dict[str, Any], answer_visible: bool) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": build_prompt(record, answer_visible=answer_visible),
            "temperature": 0,
            "max_tokens": 96,
        }
        response = self._post_json(payload)
        content = response["choices"][0]["message"]["content"]
        score, verdict = _parse_response(content)
        usage = response.get("usage", {})
        return {
            "trace_id": record["trace_id"],
            "quartet_id": record["quartet_id"],
            "domain": record["domain"],
            "verbalizer_id": record["verbalizer_id"],
            "answer_visible": answer_visible,
            "score": score,
            "verdict": verdict,
            "gold_valid": record["is_valid_process"],
            "answer_variant": record["answer_variant"],
            "process_variant": record["process_variant"],
            "raw_response": content,
            "usage": usage,
        }

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


def load_api_config() -> dict[str, str]:
    base_url = os.environ.get("ARK_BASE_URL")
    model = os.environ.get("ARK_MODEL_ENDPOINT")
    api_key = os.environ.get("ARK_API_KEY")
    missing = [
        name
        for name, value in [
            ("ARK_BASE_URL", base_url),
            ("ARK_MODEL_ENDPOINT", model),
            ("ARK_API_KEY", api_key),
        ]
        if not value
    ]
    if missing:
        raise RuntimeError(f"missing required environment variables: {', '.join(missing)}")
    return {
        "base_url": base_url,
        "model": model,
        "api_key": api_key,
    }


def load_existing_rows(path: str | Path) -> list[dict[str, Any]]:
    target = Path(path)
    if not target.exists():
        return []
    return [json.loads(line) for line in target.read_text(encoding="utf-8").splitlines() if line.strip()]


def append_row(path: str | Path, row: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def summarize_api_judge(rows: list[dict[str, Any]]) -> dict[str, Any]:
    visible_rows = [row for row in rows if row["answer_visible"]]
    masked_rows = [row for row in rows if not row["answer_visible"]]

    usage_totals = {
        "prompt_tokens": sum(row.get("usage", {}).get("prompt_tokens", 0) for row in rows),
        "completion_tokens": sum(row.get("usage", {}).get("completion_tokens", 0) for row in rows),
        "total_tokens": sum(row.get("usage", {}).get("total_tokens", 0) for row in rows),
        "num_calls": len(rows),
    }

    return {
        "visible": compute_pilot_metrics(visible_rows),
        "masked": compute_pilot_metrics(masked_rows),
        "usage": usage_totals,
        "raw_scores": rows,
    }
