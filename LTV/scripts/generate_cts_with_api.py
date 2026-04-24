#!/usr/bin/env python3
import argparse
import json
import os
import time
from pathlib import Path
from typing import Dict, List

import requests


def prompt_version(prompt_mode: str) -> str:
    return f"cts_api_v1_{prompt_mode}"


def load_jsonl(path: Path) -> List[Dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def build_raw_index(rows: List[Dict]) -> Dict[str, Dict]:
    return {row["theorem_id"]: row for row in rows}


def make_messages(raw_row: Dict, step_index: int, prompt_mode: str) -> List[Dict]:
    prior_steps = raw_row["steps"][:step_index]
    step_text = raw_row["steps"][step_index]
    payload = {
        "theorem_id": raw_row["theorem_id"],
        "header": raw_row["header"],
        "prior_steps": prior_steps,
        "source_step_index": step_index,
        "source_step": step_text,
    }
    system = (
        "You are helping build a tiny counterfactual transition set for Lean theorem proving. "
        "Return only valid JSON. Do not use markdown."
    )
    if prompt_mode == "diverse_same":
        same_instruction = (
            "For same_semantics, prefer a visibly different surface form: change theorem-application style, "
            "notation, explicitness, or tactic keyword if possible, while keeping it to one Lean step line."
        )
        flip_instruction = "Make semantic_flip locally plausible, not random garbage."
    elif prompt_mode == "plausible_flip":
        same_instruction = (
            "For same_semantics, prefer a visibly different but still concise surface form that preserves proof intent."
        )
        flip_instruction = (
            "For semantic_flip, prefer a wrong-but-plausible local step: ideally type-plausible or theorem-plausible, "
            "not obviously malformed syntax."
        )
    else:
        same_instruction = "For same_semantics, prefer a compact local rewrite that preserves proof intent."
        flip_instruction = "Make semantic_flip locally plausible, not random garbage."

    user = (
        "Given the Lean theorem context and one source step, produce exactly two variants:\n"
        "1. same_semantics: a single Lean step line that should preserve the local proof intent.\n"
        "2. semantic_flip: a single Lean step line that looks plausible but changes local proof semantics "
        "so the local step should become unsound in this context.\n\n"
        "Constraints:\n"
        "- Keep each variant to one Lean step line.\n"
        "- Preserve leading indentation similar to the source step.\n"
        "- Do not change theorem header or prior steps.\n"
        f"- {same_instruction}\n"
        f"- {flip_instruction}\n\n"
        "Return JSON with keys: same_semantics, semantic_flip, same_rationale, flip_rationale.\n\n"
        f"Context:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def source_constraints(source: Dict) -> List[str]:
    constraints = []
    target_same = source.get("target_same_family")
    target_flip = source.get("target_flip_family")
    same_hint = source.get("same_hint")
    flip_hint = source.get("flip_hint")
    if target_same:
        constraints.append(
            f"- For same_semantics, target the rewrite family `{target_same}` when possible."
        )
    if same_hint:
        constraints.append(f"- same_semantics hint: {same_hint}")
    if target_flip:
        constraints.append(
            f"- For semantic_flip, target the failure family `{target_flip}` when possible."
        )
    if flip_hint:
        constraints.append(f"- semantic_flip hint: {flip_hint}")
    return constraints


def make_targeted_messages(raw_row: Dict, source: Dict) -> List[Dict]:
    step_index = int(source["source_step_index"])
    prior_steps = raw_row["steps"][:step_index]
    step_text = raw_row["steps"][step_index]
    payload = {
        "theorem_id": raw_row["theorem_id"],
        "header": raw_row["header"],
        "prior_steps": prior_steps,
        "source_step_index": step_index,
        "source_step": step_text,
        "target_same_family": source.get("target_same_family"),
        "target_flip_family": source.get("target_flip_family"),
        "same_hint": source.get("same_hint"),
        "flip_hint": source.get("flip_hint"),
    }
    system = (
        "You are helping build a tiny counterfactual transition set for Lean theorem proving. "
        "Return only valid JSON. Do not use markdown."
    )
    extra_constraints = source_constraints(source)
    user = (
        "Given the Lean theorem context and one source step, produce exactly two variants:\n"
        "1. same_semantics: a single Lean step line that should preserve the local proof intent.\n"
        "2. semantic_flip: a single Lean step line that looks locally plausible but changes local proof semantics.\n\n"
        "Constraints:\n"
        "- Keep each variant to one Lean step line.\n"
        "- Preserve leading indentation similar to the source step.\n"
        "- Do not change theorem header or prior steps.\n"
        "- Prefer variants that are Lean-plausible, not random malformed garbage.\n"
        "- If the requested family does not fit perfectly, return the closest plausible variant and explain why.\n"
    )
    if extra_constraints:
        user += "\n".join(extra_constraints) + "\n"
    user += (
        "\nReturn JSON with keys: same_semantics, semantic_flip, same_rationale, flip_rationale.\n\n"
        f"Context:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


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
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate CTS candidates via API.")
    parser.add_argument("--raw-jsonl", required=True)
    parser.add_argument("--sources-jsonl", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-sources", type=int, default=None)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--sleep-seconds", type=float, default=0.5)
    parser.add_argument(
        "--prompt-mode",
        choices=["default", "diverse_same", "plausible_flip", "targeted_family"],
        default="default",
    )
    args = parser.parse_args()

    base_url = os.environ["LTV_API_BASE_URL"]
    api_key = os.environ["LTV_API_KEY"]
    model = os.environ["LTV_API_MODEL"]

    raw_rows = load_jsonl(Path(args.raw_jsonl))
    raw_index = build_raw_index(raw_rows)
    source_rows = load_jsonl(Path(args.sources_jsonl))
    if args.max_sources is not None:
        source_rows = source_rows[: args.max_sources]

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        for idx, source in enumerate(source_rows):
            theorem_id = source["source_theorem_id"]
            step_index = int(source["source_step_index"])
            raw_row = raw_index[theorem_id]
            if args.prompt_mode == "targeted_family":
                messages = make_targeted_messages(raw_row, source)
            else:
                messages = make_messages(raw_row, step_index, args.prompt_mode)
            response = call_api(base_url, api_key, model, messages, args.temperature)
            content = response["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            usage = response.get("usage", {})

            output_row = {
                "pair_source_id": f"{theorem_id}__step{step_index}",
                "source_theorem_id": theorem_id,
                "source_step_index": step_index,
                "source_step": raw_row["steps"][step_index],
                "same_semantics": parsed["same_semantics"],
                "semantic_flip": parsed["semantic_flip"],
                "same_rationale": parsed.get("same_rationale", ""),
                "flip_rationale": parsed.get("flip_rationale", ""),
                "target_same_family": source.get("target_same_family"),
                "target_flip_family": source.get("target_flip_family"),
                "same_hint": source.get("same_hint"),
                "flip_hint": source.get("flip_hint"),
                "api_provenance": {
                    "prompt_version": prompt_version(args.prompt_mode),
                    "prompt_mode": args.prompt_mode,
                    "base_url": base_url,
                    "model": model,
                    "temperature": args.temperature,
                    "usage": usage,
                },
            }
            f.write(json.dumps(output_row, ensure_ascii=False) + "\n")
            f.flush()
            time.sleep(args.sleep_seconds)

            print(
                json.dumps(
                    {
                        "idx": idx,
                        "pair_source_id": output_row["pair_source_id"],
                        "same_semantics": output_row["same_semantics"],
                        "semantic_flip": output_row["semantic_flip"],
                        "usage": usage,
                    },
                    ensure_ascii=False,
                )
            )


if __name__ == "__main__":
    main()
