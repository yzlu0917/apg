#!/usr/bin/env python3

import argparse
import json
import re
from pathlib import Path

import requests
from reasoning_gym.factory import get_score_answer_fn


REASONING_RE = re.compile(r"<reasoning>\s*(.*?)\s*</reasoning>", re.DOTALL | re.IGNORECASE)
FINAL_RE = re.compile(r"<final>\s*(.*?)\s*</final>", re.DOTALL | re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect a tiny API calibration batch from a manifest.")
    parser.add_argument("--manifest", required=True, help="Path to input manifest JSONL.")
    parser.add_argument("--output", required=True, help="Path to output traces JSONL.")
    parser.add_argument("--limit", type=int, default=2, help="Number of prompts to sample.")
    parser.add_argument("--start", type=int, default=0, help="Start offset inside the manifest.")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument(
        "--protocol-mode",
        choices=["default", "quantum_lock_shortplan"],
        default="default",
        help="Optional family-specific prompting mode for small rescue branches.",
    )
    return parser.parse_args()


def load_api_config() -> dict:
    readme = Path("README.md").read_text(encoding="utf-8")
    return {
        "base_url": re.search(r"base_url:\s*(\S+)", readme).group(1),
        "endpoint": re.search(r"endpoint:\s*(\S+)", readme).group(1),
        "api_key": re.search(r"api_key:\s*(\S+)", readme).group(1),
    }


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


def build_system_prompt(row: dict, protocol_mode: str) -> str:
    default = (
        "Follow the output format exactly. "
        "Use <reasoning> for a very short plan or key checks only. "
        "Keep <reasoning> to at most 4 short lines. "
        "Do not copy the full final answer, move list, or final-format expression into <reasoning>."
    )
    if protocol_mode != "quantum_lock_shortplan" or row["family"] != "quantum_lock":
        return default

    return (
        "Follow the output format exactly. "
        "For quantum_lock, do not simulate many candidate sequences inside <reasoning>. "
        "Keep <reasoning> to at most 2 short lines: one line for the button/light-state pattern, one line for the chosen shortest sequence motif. "
        "Do not write step-by-step exhaustive search, and do not exceed 35 words inside <reasoning>. "
        "If you find a valid shortest-looking sequence, stop searching and put only that sequence inside <final>. "
        "The <final> content must be just the button sequence separated by the arrow symbol."
    )


def main() -> None:
    args = parse_args()
    api_cfg = load_api_config()
    manifest_path = Path(args.manifest)
    output_path = Path(args.output)
    rows = load_rows(manifest_path, args.start, args.limit)
    if not rows:
        raise ValueError(f"No rows loaded from {manifest_path}")

    url = api_cfg["base_url"].rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_cfg['api_key']}",
        "Content-Type": "application/json",
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0

    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            payload = {
                "model": api_cfg["endpoint"],
                "messages": [
                    {
                        "role": "system",
                        "content": build_system_prompt(row, args.protocol_mode),
                    },
                    {"role": "user", "content": row["model_prompt"]},
                ],
                "temperature": args.temperature,
                "max_tokens": args.max_tokens,
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            total_prompt_tokens += usage.get("prompt_tokens", 0)
            total_completion_tokens += usage.get("completion_tokens", 0)
            total_tokens += usage.get("total_tokens", 0)

            reasoning = extract_tag(text, REASONING_RE)
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
                "backend": "api",
                "provider": "deepseek-v3.2-via-ark",
                "protocol_mode": args.protocol_mode,
                "temperature": args.temperature,
                "max_tokens": args.max_tokens,
                "raw_completion": text,
                "reasoning": reasoning,
                "final": final,
                "reasoning_present": reasoning is not None,
                "final_present": final is not None,
                "format_ok": reasoning is not None and final is not None,
                "score": score,
                "usage": usage,
                "oracle_answer": row["oracle_answer"],
                "metadata": row["metadata"],
            }
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")

    summary = {
        "output": str(output_path),
        "count": len(rows),
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
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "total_tokens": total_tokens,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
