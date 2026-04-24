#!/usr/bin/env python3

import argparse
import json
import re
from pathlib import Path

import requests
from reasoning_gym.factory import get_score_answer_fn


FINAL_RE = re.compile(r"<final>\s*(.*?)\s*</final>", re.DOTALL | re.IGNORECASE)
ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect answer-only quantum_lock sequences from the API.")
    parser.add_argument("--manifest", required=True, help="Input manifest JSONL.")
    parser.add_argument("--output", required=True, help="Output rollout JSONL.")
    parser.add_argument("--limit", type=int, default=4)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=96)
    return parser.parse_args()


def load_api_config() -> dict:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
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


def extract_final(text: str) -> str | None:
    match = FINAL_RE.search(text)
    if not match:
        return None
    return match.group(1).strip()


def build_user_prompt(raw_question: str) -> str:
    return (
        "Solve the task and return only the shortest button sequence.\n"
        "Do not show your search.\n"
        "Do not explain.\n"
        "Return exactly:\n"
        "<final>\n"
        "A \u2192 B \u2192 C\n"
        "</final>\n\n"
        f"Problem:\n{raw_question}\n"
    )


def main() -> None:
    args = parse_args()
    api_cfg = load_api_config()
    manifest_path = ROOT / args.manifest
    output_path = ROOT / args.output
    rows = load_rows(manifest_path, args.start, args.limit)
    if not rows:
        raise ValueError(f"No rows loaded from {manifest_path}")

    url = api_cfg["base_url"].rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_cfg['api_key']}",
        "Content-Type": "application/json",
    }

    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            payload = {
                "model": api_cfg["endpoint"],
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Return only a tagged final answer. "
                            "No chain-of-thought, no search trace, no extra text."
                        ),
                    },
                    {"role": "user", "content": build_user_prompt(row["raw_question"])},
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

            final = extract_final(text)
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
                "protocol_branch": "quantum_lock_answer_only_v0",
                "temperature": args.temperature,
                "max_tokens": args.max_tokens,
                "raw_completion": text,
                "reasoning": None,
                "final": final,
                "reasoning_present": False,
                "final_present": final is not None,
                "format_ok": final is not None,
                "score": score,
                "usage": usage,
                "oracle_answer": row["oracle_answer"],
                "metadata": row["metadata"],
            }
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")

    summary = {
        "output": str(output_path.relative_to(ROOT)),
        "count": len(rows),
        "final_present_count": sum(
            1 for line in output_path.read_text(encoding="utf-8").splitlines() if json.loads(line)["final_present"]
        ),
        "nonzero_score_count": sum(
            1 for line in output_path.read_text(encoding="utf-8").splitlines() if json.loads(line)["score"] > 0.0
        ),
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "total_tokens": total_tokens,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
