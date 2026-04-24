#!/usr/bin/env python3

import argparse
import json
import re
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate paraphrase and distractor candidates for ready intervention steps.")
    parser.add_argument(
        "--input",
        default="artifacts/object_gate/interventions/draft_candidates_v0.jsonl",
        help="Draft intervention candidates JSONL.",
    )
    parser.add_argument(
        "--output",
        default="artifacts/object_gate/interventions/generated_candidates_v0.jsonl",
        help="Output JSONL with generated paraphrase and distractor candidates.",
    )
    parser.add_argument("--limit", type=int, default=7, help="Maximum number of ready steps to process.")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--max-tokens", type=int, default=220)
    return parser.parse_args()


def load_api_config() -> dict:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    return {
        "base_url": re.search(r"base_url:\s*(\S+)", readme).group(1),
        "endpoint": re.search(r"endpoint:\s*(\S+)", readme).group(1),
        "api_key": re.search(r"api_key:\s*(\S+)", readme).group(1),
    }


def load_ready_rows(path: Path, limit: int) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row["trace_readiness"] != "ready":
                continue
            rows.append(row)
            if len(rows) >= limit:
                break
    return rows


def build_user_prompt(row: dict) -> str:
    context_lines = row["delete_variant"]["reasoning_lines_after_delete"]
    context_block = "\n".join(f"- {line}" for line in context_lines) if context_lines else "- <empty>"
    return (
        "You are preparing matched counterfactual interventions for a reasoning step.\n\n"
        f"Family: {row['family']}\n"
        f"Difficulty stratum: {row['difficulty_stratum']}\n"
        f"Selected step:\n{row['step_text']}\n\n"
        "Remaining reasoning context after deleting this step:\n"
        f"{context_block}\n\n"
        "Return strict JSON with two string fields:\n"
        "- paraphrase: semantically equivalent to the selected step, same role in the reasoning.\n"
        "- distractor: stylistically similar and locally plausible, but not genuinely useful for solving the task.\n\n"
        "Rules:\n"
        "- Keep each field to one short line.\n"
        "- Do not include markdown or code fences.\n"
        "- Do not copy the selected step verbatim unless unavoidable.\n"
        "- The distractor should not be obviously nonsensical.\n"
    )


def request_generation(api_cfg: dict, row: dict, temperature: float, max_tokens: int) -> tuple[dict, dict]:
    url = api_cfg["base_url"].rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_cfg['api_key']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": api_cfg["endpoint"],
        "messages": [
            {
                "role": "system",
                "content": "Respond with valid JSON only.",
            },
            {
                "role": "user",
                "content": build_user_prompt(row),
            },
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    return parsed, data.get("usage", {})


def main() -> None:
    args = parse_args()
    api_cfg = load_api_config()
    input_path = ROOT / args.input
    output_path = ROOT / args.output
    rows = load_ready_rows(input_path, args.limit)
    if not rows:
        raise ValueError(f"No ready rows found in {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0

    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            generated, usage = request_generation(api_cfg, row, args.temperature, args.max_tokens)
            total_prompt_tokens += usage.get("prompt_tokens", 0)
            total_completion_tokens += usage.get("completion_tokens", 0)
            total_tokens += usage.get("total_tokens", 0)

            record = dict(row)
            record["paraphrase_candidates"] = [generated["paraphrase"].strip()]
            record["distractor_candidates"] = [generated["distractor"].strip()]
            record["generation_backend"] = "api"
            record["generation_provider"] = "deepseek-v3.2-via-ark"
            record["generation_usage"] = usage
            record["status"] = "candidate_generated"
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")

    summary = {
        "output": str(output_path.relative_to(ROOT)),
        "count": len(rows),
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "total_tokens": total_tokens,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
