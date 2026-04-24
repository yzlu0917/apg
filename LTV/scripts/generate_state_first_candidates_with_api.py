#!/usr/bin/env python3
import argparse
import json
import os
import time
from pathlib import Path
from typing import Dict, List

import requests


def load_jsonl(path: Path) -> List[Dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def call_api(base_url: str, api_key: str, model: str, messages: List[Dict], temperature: float) -> Dict:
    url = base_url.rstrip("/") + "/chat/completions"
    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        },
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json()


def make_messages(seed_row: Dict, requested_candidates: int) -> List[Dict]:
    system = (
        "You are proposing candidate next tactics for Lean theorem proving. "
        "Return only valid JSON and do not use markdown."
    )
    payload = {
        "state_id": seed_row["state_id"],
        "theorem_id": seed_row["theorem_id"],
        "header": seed_row["header"],
        "prefix_steps": seed_row["prefix_steps"],
        "before_goals": seed_row["before_goals"],
        "gold_tactic": seed_row["gold_tactic"],
        "notes": seed_row.get("notes"),
    }
    optional_fields = [
        "context_snippet",
        "source_file",
        "decl_name",
        "proof_state",
        "project_root",
        "source_type",
    ]
    for field in optional_fields:
        if field in seed_row:
            payload[field] = seed_row[field]
    user = (
        f"Given the Lean theorem context, prior steps, and current before-state, propose exactly {requested_candidates} "
        "candidate next tactics.\n\n"
        "Constraints:\n"
        "- Each candidate must be one Lean tactic line only.\n"
        "- Do not include numbering, bullets, explanations, or code fences.\n"
        "- Prefer diverse but plausible tactic styles.\n"
        "- Do not output `sorry`.\n"
        "- Keep candidates local to this exact state.\n\n"
        "Return JSON with keys:\n"
        "- candidates: list[str]\n"
        "- rationale: short string\n\n"
        f"Context:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate candidate tactics for state-first seed states via API.")
    parser.add_argument("--seed-panel", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-states", type=int, default=None)
    parser.add_argument("--num-candidates", type=int, default=8)
    parser.add_argument("--temperature", type=float, default=0.6)
    parser.add_argument("--sleep-seconds", type=float, default=0.5)
    args = parser.parse_args()

    base_url = os.environ["LTV_API_BASE_URL"]
    api_key = os.environ["LTV_API_KEY"]
    model = os.environ["LTV_API_MODEL"]

    seed_rows = load_jsonl(Path(args.seed_panel))
    if args.max_states is not None:
        seed_rows = seed_rows[: args.max_states]

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        for idx, row in enumerate(seed_rows):
            messages = make_messages(row, args.num_candidates)
            response = call_api(base_url, api_key, model, messages, args.temperature)
            content = response["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            candidates = parsed["candidates"]
            usage = response.get("usage", {})

            output_row = {
                "state_id": row["state_id"],
                "theorem_id": row["theorem_id"],
                "step_index": row["step_index"],
                "header": row["header"],
                "prefix_steps": row["prefix_steps"],
                "before_goals": row["before_goals"],
                "gold_tactic": row["gold_tactic"],
                "generated_candidates": candidates,
                "generation_rationale": parsed.get("rationale", ""),
                "api_provenance": {
                    "base_url": base_url,
                    "model": model,
                    "temperature": args.temperature,
                    "num_candidates": args.num_candidates,
                    "usage": usage,
                },
            }
            for field in [
                "context_snippet",
                "source_file",
                "decl_name",
                "proof_state",
                "project_root",
                "source_type",
                "sorry_position",
                "file_mode_env",
                "notes",
                "seed_source",
            ]:
                if field in row:
                    output_row[field] = row[field]
            f.write(json.dumps(output_row, ensure_ascii=False) + "\n")
            f.flush()
            print(
                json.dumps(
                    {
                        "idx": idx,
                        "state_id": row["state_id"],
                        "num_candidates": len(candidates),
                        "usage": usage,
                    },
                    ensure_ascii=False,
                )
            )
            time.sleep(args.sleep_seconds)


if __name__ == "__main__":
    main()
