#!/usr/bin/env python3

import json
import re
from pathlib import Path

import requests
import torch
from reasoning_gym.factory import get_score_answer_fn
from transformers import AutoModelForCausalLM, AutoTokenizer


ROOT = Path(__file__).resolve().parents[1]
FINAL_RE = re.compile(r"<final>\s*(.*?)\s*</final>", re.DOTALL | re.IGNORECASE)
MODEL_PATH = "/cephfs/shared/hf_cache/hub/models--Qwen--Qwen3-1.7B/snapshots/70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"


def extract_tag(text: str, pattern: re.Pattern[str]) -> str | None:
    match = pattern.search(text)
    if not match:
        return None
    return match.group(1).strip()


def load_api_config() -> dict:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    return {
        "base_url": re.search(r"base_url:\s*(\S+)", readme).group(1),
        "endpoint": re.search(r"endpoint:\s*(\S+)", readme).group(1),
        "api_key": re.search(r"api_key:\s*(\S+)", readme).group(1),
    }


def load_manifest_map() -> dict[str, dict]:
    mapping = {}
    with (ROOT / "artifacts" / "object_gate" / "samples" / "dev_manifest.jsonl").open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            mapping[row["prompt_id"]] = row
    return mapping


def choose_records() -> list[dict]:
    rows = [json.loads(line) for line in (ROOT / "artifacts" / "object_gate" / "interventions" / "micro_batch_v0.jsonl").open("r", encoding="utf-8")]

    selected_groups = []
    highdep_keys = sorted(
        {
            (r["source_rollout_file"], r["prompt_id"], r["step_index"])
            for r in rows
            if r["family"] == "tower_of_hanoi" and r["source_score"] > 0
        }
    )
    shallow_keys = sorted(
        {
            (r["source_rollout_file"], r["prompt_id"], r["step_index"])
            for r in rows
            if r["family"] == "basic_arithmetic" and r["source_score"] > 0
        }
    )
    if highdep_keys:
        selected_groups.append(highdep_keys[0])
    if shallow_keys:
        selected_groups.append(shallow_keys[0])

    chosen = []
    for source_rollout_file, prompt_id, step_index in selected_groups:
        group_rows = [
            r
            for r in rows
            if r["source_rollout_file"] == source_rollout_file
            and r["prompt_id"] == prompt_id
            and r["step_index"] == step_index
        ]
        group_rows = sorted(group_rows, key=lambda r: {"delete": 0, "paraphrase": 1, "distractor": 2}[r["variant_type"]])
        chosen.extend(group_rows)
    return chosen


def build_user_prompt(raw_question: str, reasoning_lines: list[str]) -> str:
    reasoning_block = "\n".join(reasoning_lines)
    return (
        "You are given a verifiable reasoning task and an existing reasoning draft.\n"
        "Do not rewrite the reasoning draft.\n"
        "Use it as context and output only the final answer inside <final> tags.\n"
        "The content inside <final> must follow the original task formatting instructions exactly.\n\n"
        f"Problem:\n{raw_question}\n\n"
        f"Existing reasoning draft:\n<reasoning>\n{reasoning_block}\n</reasoning>\n\n"
        "Return exactly:\n<final>\n...\n</final>\n"
    )


def run_api(record: dict, manifest_row: dict, api_cfg: dict) -> tuple[str, dict]:
    url = api_cfg["base_url"].rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_cfg['api_key']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": api_cfg["endpoint"],
        "messages": [
            {"role": "system", "content": "Return only the final answer wrapped in <final> tags."},
            {"role": "user", "content": build_user_prompt(manifest_row["raw_question"], record["reasoning_lines"])},
        ],
        "temperature": 0.0,
        "max_tokens": 256,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    text = data["choices"][0]["message"]["content"]
    return text, data.get("usage", {})


def run_local(records_with_manifest: list[tuple[dict, dict]]) -> list[tuple[str, dict]]:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
        attn_implementation="sdpa",
    )
    outputs: list[tuple[str, dict]] = []
    eos_token_id = tokenizer.eos_token_id

    for record, manifest_row in records_with_manifest:
        prompt = build_user_prompt(manifest_row["raw_question"], record["reasoning_lines"])
        messages = [{"role": "user", "content": prompt}]
        chat_prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        model_inputs = tokenizer(chat_prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            generated = model.generate(
                **model_inputs,
                do_sample=False,
                max_new_tokens=256,
                eos_token_id=eos_token_id,
                pad_token_id=eos_token_id,
            )
        new_tokens = generated[0][model_inputs["input_ids"].shape[1] :]
        text = tokenizer.decode(new_tokens, skip_special_tokens=False)
        usage = {
            "prompt_tokens": int(model_inputs["input_ids"].shape[1]),
            "completion_tokens": int(new_tokens.shape[0]),
            "total_tokens": int(model_inputs["input_ids"].shape[1] + new_tokens.shape[0]),
        }
        outputs.append((text, usage))
    return outputs


def main() -> None:
    records = choose_records()
    if not records:
        raise ValueError("No records selected from micro_batch_v0.jsonl")

    manifest_map = load_manifest_map()
    api_cfg = load_api_config()
    output_path = ROOT / "artifacts" / "object_gate" / "analysis" / "intervention_rollout_smoke_000.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    local_batch = []
    processed = []
    for record in records:
        manifest_row = manifest_map[record["prompt_id"]]
        if record["backend"] == "transformers":
            local_batch.append((record, manifest_row))
        else:
            text, usage = run_api(record, manifest_row, api_cfg)
            processed.append((record, manifest_row, text, usage, "api"))

    if local_batch:
        local_outputs = run_local(local_batch)
        for (record, manifest_row), (text, usage) in zip(local_batch, local_outputs):
            processed.append((record, manifest_row, text, usage, "transformers"))

    with output_path.open("w", encoding="utf-8") as handle:
        for record, manifest_row, text, usage, backend_used in processed:
            final = extract_tag(text, FINAL_RE)
            if final is None:
                stripped = text.strip().replace("<|im_end|>", "").strip()
                final = stripped if stripped else None
            score_fn = get_score_answer_fn(record["family"])
            entry = {
                "question": manifest_row["raw_question"],
                "answer": manifest_row["oracle_answer"],
                "metadata": manifest_row["metadata"],
            }
            score = score_fn(final, entry) if final is not None else 0.0
            row = {
                "prompt_id": record["prompt_id"],
                "intervention_id": record["intervention_id"],
                "family": record["family"],
                "variant_type": record["variant_type"],
                "backend_used": backend_used,
                "needs_review": record["needs_review"],
                "source_score": record["source_score"],
                "raw_completion": text,
                "final": final,
                "final_present": final is not None,
                "score": score,
                "usage": usage,
            }
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")

    rows = [json.loads(line) for line in output_path.open("r", encoding="utf-8")]
    summary = {
        "output": str(output_path.relative_to(ROOT)),
        "count": len(rows),
        "final_present_count": sum(int(r["final_present"]) for r in rows),
        "nonzero_score_count": sum(int(r["score"] > 0) for r in rows),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
