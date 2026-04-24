from __future__ import annotations

import json
import math
import re
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from civic_prm.metrics import binary_accuracy, binary_auroc


def load_snapshot_path(model_root: str | Path) -> Path:
    root = Path(model_root)
    snapshots = sorted(path for path in root.iterdir() if path.is_dir())
    if not snapshots:
        raise FileNotFoundError(f"no snapshot found under {root}")
    return snapshots[0]


def build_prompt(record: dict, answer_visible: bool) -> list[dict[str, str]]:
    trace_text = record["trace_text"] if answer_visible else record["masked_trace_text"]
    return [
        {
            "role": "system",
            "content": (
                "You are auditing a single reasoning locus. "
                "Judge whether the audited step is locally valid. "
                "Ignore final-answer agreement unless it directly changes the local step. "
                "Reply with compact JSON only: "
                '{"score": <0-100 integer>, "verdict": "valid" or "invalid"}.'
            ),
        },
        {
            "role": "user",
            "content": (
                "/no_think\n"
                f"Problem:\n{record['problem_text']}\n\n"
                f"Audited step index: {record['audited_locus'] + 1}\n\n"
                f"Trace:\n{trace_text}"
            ),
        },
    ]


def load_model(model_root: str | Path):
    snapshot = load_snapshot_path(model_root)
    tokenizer = AutoTokenizer.from_pretrained(snapshot, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        snapshot,
        dtype="auto",
        device_map="auto",
        trust_remote_code=True,
    )
    model.eval()
    return tokenizer, model


def _parse_response(text: str) -> tuple[int, str]:
    try:
        payload = json.loads(text.strip())
        score = int(payload["score"])
        verdict = str(payload["verdict"]).lower()
        return max(0, min(100, score)), verdict
    except Exception:
        object_matches = re.findall(r"\{.*?\}", text, flags=re.DOTALL)
        for candidate in reversed(object_matches):
            try:
                payload = json.loads(candidate)
                score = int(payload["score"])
                verdict = str(payload["verdict"]).lower()
                return max(0, min(100, score)), verdict
            except Exception:
                continue
        score_matches = re.findall(r"(\d{1,3})", text)
        verdict_matches = re.findall(r"\b(valid|invalid)\b", text.lower())
        score = int(score_matches[-1]) if score_matches else 50
        verdict = verdict_matches[-1] if verdict_matches else ("valid" if score >= 50 else "invalid")
        return max(0, min(100, score)), verdict


@torch.inference_mode()
def score_record(tokenizer, model, record: dict, answer_visible: bool) -> dict:
    messages = build_prompt(record, answer_visible)
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    model_inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    generated = model.generate(
        **model_inputs,
        max_new_tokens=128,
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
        "quartet_id": record["quartet_id"],
        "domain": record["domain"],
        "verbalizer_id": record["verbalizer_id"],
        "answer_visible": answer_visible,
        "score": score,
        "verdict": verdict,
        "gold_valid": record["is_valid_process"],
        "answer_variant": record["answer_variant"],
        "process_variant": record["process_variant"],
        "raw_response": response,
    }


def compute_pilot_metrics(scores: list[dict]) -> dict:
    score_values = [row["score"] / 100.0 for row in scores]
    gold = [int(row["gold_valid"]) for row in scores]
    preds = [int(row["score"] >= 50) for row in scores]

    by_pair = {}
    for row in scores:
        key = (
            row["quartet_id"],
            row["verbalizer_id"],
            row["answer_variant"],
            row["answer_visible"],
        )
        by_pair.setdefault(key, {})[row["process_variant"]] = row["score"]

    amcd_hits = []
    for pair in by_pair.values():
        if "valid" in pair and "invalid" in pair:
            amcd_hits.append(int(pair["valid"] > pair["invalid"]))

    by_swap = {}
    for row in scores:
        key = (
            row["quartet_id"],
            row["verbalizer_id"],
            row["process_variant"],
            row["answer_visible"],
        )
        by_swap.setdefault(key, {})[row["answer_variant"]] = row["score"]

    swap_deltas = []
    for pair in by_swap.values():
        if "correct" in pair and "swapped" in pair:
            swap_deltas.append(abs(pair["correct"] - pair["swapped"]))

    metrics = {
        "num_scored_traces": len(scores),
        "ordinary_accuracy": round(binary_accuracy(gold, preds), 4),
        "ordinary_auroc": round(binary_auroc(gold, score_values), 4),
        "amcd": round(sum(amcd_hits) / len(amcd_hits), 4) if amcd_hits else math.nan,
        "ass_total": round(sum(swap_deltas) / len(swap_deltas), 4) if swap_deltas else math.nan,
    }
    return metrics
