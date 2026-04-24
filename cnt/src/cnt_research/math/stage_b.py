from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
import math
from pathlib import Path
import random
import re
from statistics import mean
import time
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import torch
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer, get_linear_schedule_with_warmup

from .countertrace_mini import (
    DEFAULT_QWEN3_1P7B,
    LocalQwenGenerator,
    extract_predicted_answer,
    extract_verifiable_answer,
    load_gsm8k,
    split_steps,
    truncate_at_final_answer,
)
from .stage_a import CONTINUATOR_STYLES, build_continuation_prompt, summarize_stage_a
from .stage_a_audit import load_stage_a_records


RecordKey = Tuple[str, int]


@dataclass(frozen=True)
class StageBExample:
    row_id: str
    split: str
    task_type: str
    task_subtype: str | None
    example_id: str
    candidate_step_index: int
    question: str
    prompt: str
    chosen: str
    rejected_prompt: str | None
    rejected: str | None
    alt_prompt: str | None
    alt_completion: str | None
    weight_raw: float
    weight_normalized: float
    train_scores: Dict[str, float]
    heldout_scores: Dict[str, float]

    def to_json(self) -> Dict[str, Any]:
        return {
            "row_id": self.row_id,
            "split": self.split,
            "task_type": self.task_type,
            "task_subtype": self.task_subtype,
            "example_id": self.example_id,
            "candidate_step_index": self.candidate_step_index,
            "question": self.question,
            "prompt": self.prompt,
            "chosen": self.chosen,
            "rejected_prompt": self.rejected_prompt,
            "rejected": self.rejected,
            "alt_prompt": self.alt_prompt,
            "alt_completion": self.alt_completion,
            "weight_raw": self.weight_raw,
            "weight_normalized": self.weight_normalized,
            "train_scores": self.train_scores,
            "heldout_scores": self.heldout_scores,
        }


def _normalize_step_text(text: str) -> str:
    text = re.sub(r"^\s*\d+\.\s*", "", text).strip()
    text = re.sub(r"\s+", " ", text)
    return text


def _safe_mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return mean(values)


def _load_audit_keep_rows(path: Path) -> Dict[RecordKey, Dict[str, Any]]:
    rows: Dict[RecordKey, Dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            payload = json.loads(line)
            if not payload.get("keep", True):
                continue
            key = (payload["example_id"], int(payload["candidate_step_index"]))
            rows[key] = payload
    return rows


def _choose_weight(audit_row: Dict[str, Any], weight_source: str) -> float:
    train_weight = float(audit_row["train_scores"]["n_t_weighted"])
    heldout_weight = float(audit_row["heldout_scores"]["n_t_weighted"])
    if weight_source == "train":
        return train_weight
    if weight_source == "heldout":
        return heldout_weight
    if weight_source == "min":
        return min(train_weight, heldout_weight)
    raise ValueError(f"Unsupported weight_source: {weight_source}")


def _family_utility_delta(scores: Dict[str, Any], family: str) -> float:
    return float(scores["original"]) - float(scores[family])


def _passes_drop_sft_filter(audit_row: Dict[str, Any], drop_sft_filter: str) -> bool:
    if drop_sft_filter == "none":
        return True
    train_delta = _family_utility_delta(audit_row["train_scores"], "drop")
    heldout_delta = _family_utility_delta(audit_row["heldout_scores"], "drop")
    if drop_sft_filter == "one_side_positive":
        return train_delta > 0.0 or heldout_delta > 0.0
    if drop_sft_filter == "both_sides_positive":
        return train_delta > 0.0 and heldout_delta > 0.0
    raise ValueError(f"Unsupported drop_sft_filter: {drop_sft_filter}")


def _resolve_task_weights(
    *,
    task_type: str,
    weight_raw: float,
    weight_normalized: float,
    max_weight: float,
    equiv_weight_mode: str,
) -> Tuple[float, float]:
    if task_type != "equiv" or equiv_weight_mode == "match":
        return weight_raw, weight_normalized
    if equiv_weight_mode == "uniform":
        return max_weight, 1.0
    raise ValueError(f"Unsupported equiv_weight_mode: {equiv_weight_mode}")


def _pref_subtype_multiplier(
    task_subtype: str | None,
    *,
    pref_step_multiplier: float,
    pref_rollout_multiplier: float,
    pref_anchor_multiplier: float,
) -> float:
    if task_subtype in {"pref_step", "pref_same"}:
        return pref_step_multiplier
    if task_subtype == "pref_rollout":
        return pref_rollout_multiplier
    if task_subtype in {"pref_anchor_original_trunc", "pref_anchor_original_cf"}:
        return pref_anchor_multiplier
    return 1.0


def build_next_step_prompt(question: str, prefix_steps: Sequence[str]) -> str:
    blocks = [
        "You are writing the next step of a grade-school math solution.",
        "Treat the existing numbered steps as fixed context.",
        "Output exactly one numbered step and nothing else.",
        "Do not write the final answer or any later step.",
        "",
        f"Problem: {question}",
        "Existing solution:",
    ]
    if prefix_steps:
        blocks.extend(prefix_steps)
    else:
        blocks.append("(no previous steps)")
    blocks.extend(("", "Next step:"))
    return "\n".join(blocks)


def build_rollout_prompt(question: str, prefix_steps: Sequence[str]) -> str:
    blocks = [
        "You are continuing a grade-school math solution from a fixed prefix.",
        "Treat all earlier numbered steps as fixed context.",
        "Do not rewrite, delete, or correct any previous step.",
        "Continue from the next numbered step and finish with a final line that starts with: Final answer:",
        "",
        f"Problem: {question}",
        "Existing solution:",
    ]
    if prefix_steps:
        blocks.extend(prefix_steps)
    else:
        blocks.append("(no previous steps)")
    blocks.extend(("", "Continue the solution:"))
    return "\n".join(blocks)


def _split_example_ids(
    example_ids: Sequence[str],
    eval_examples: int,
    seed: int,
    eval_example_ids: Sequence[str] | None = None,
) -> Tuple[List[str], List[str]]:
    if eval_example_ids is not None:
        eval_id_set = set(eval_example_ids)
        missing = sorted(eval_id for eval_id in eval_id_set if eval_id not in set(example_ids))
        if missing:
            raise ValueError(f"Explicit eval ids missing from pool: {missing[:3]}")
        eval_ids = sorted(eval_id_set)
        train_ids = sorted(example_id for example_id in example_ids if example_id not in eval_id_set)
        if not eval_ids:
            raise ValueError("Explicit eval ids must be non-empty.")
        if not train_ids:
            raise ValueError("Explicit eval ids consume the full pool; need at least one train example.")
        return train_ids, eval_ids
    if eval_examples <= 0:
        return sorted(example_ids), []
    ids = list(sorted(example_ids))
    rng = random.Random(seed)
    rng.shuffle(ids)
    eval_count = min(eval_examples, max(1, len(ids) // 4))
    eval_ids = sorted(ids[:eval_count])
    train_ids = sorted(example_id for example_id in ids if example_id not in set(eval_ids))
    return train_ids, eval_ids


def _unique_negative_steps(record: Dict[str, Any]) -> List[str]:
    original = _normalize_step_text(record["original_step"])
    seen: set[str] = set()
    negatives: List[str] = []
    for key in ("swap_quantity", "swap_operation"):
        candidate = record["edits"][key]
        normalized = _normalize_step_text(candidate)
        if normalized == original or normalized in seen:
            continue
        negatives.append(candidate)
        seen.add(normalized)
    return negatives


def _copy_scores(audit_row: Dict[str, Any], side: str) -> Dict[str, float]:
    return {key: float(value) for key, value in audit_row[f"{side}_scores"].items()}


def _reconstruct_rollout_suffix(generated_text: str, start_step_number: int) -> str:
    lines = [line.strip() for line in truncate_at_final_answer(generated_text).splitlines() if line.strip()]
    if not lines:
        return ""
    if not re.match(r"^\d+\.", lines[0]) and not lines[0].lower().startswith("final answer:"):
        lines[0] = f"{start_step_number}. {lines[0]}"
    return "\n".join(lines)


def _load_success_trace_rows(path: Path) -> Dict[str, Dict[str, Any]]:
    rows: Dict[str, Dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            payload = json.loads(line)
            rows[payload["example_id"]] = payload
    return rows


def _build_rollout_completion(
    record: Dict[str, Any],
    family: str,
    rollout_style: str,
    candidate_step_index: int,
) -> str:
    if family == "original":
        first_step = record["original_step"]
    else:
        first_step = record["edits"][family]
    suffix = _reconstruct_rollout_suffix(
        generated_text=record["style_results"][family][rollout_style]["generated_text"],
        start_step_number=candidate_step_index + 2,
    )
    if not suffix:
        return first_step
    return first_step + "\n" + suffix


def _build_success_trace_completion(
    success_trace: Dict[str, Any],
    candidate_step_index: int,
    replacement_step: str | None = None,
) -> str:
    step_texts = list(success_trace["step_texts"])
    chosen_steps = step_texts[candidate_step_index:]
    if replacement_step is not None:
        chosen_steps[0] = replacement_step
    completion_lines = list(chosen_steps)
    completion_lines.append(f"Final answer: {success_trace['gold_answer']}")
    return "\n".join(completion_lines)


def _build_success_trace_suffix(
    success_trace: Dict[str, Any],
    start_step_index: int,
) -> str:
    step_texts = list(success_trace["step_texts"])
    completion_lines = list(step_texts[start_step_index:])
    completion_lines.append(f"Final answer: {success_trace['gold_answer']}")
    return "\n".join(completion_lines)


def _truncate_completion_suffix(completion: str) -> str:
    lines = [line.strip() for line in completion.splitlines() if line.strip()]
    if len(lines) <= 1:
        return ""
    return "\n".join(lines[:-1])


def _build_counterfactual_anchor_suffix(
    record: Dict[str, Any],
    family: str,
    rollout_style: str,
    candidate_step_index: int,
) -> str:
    return _reconstruct_rollout_suffix(
        generated_text=record["style_results"][family][rollout_style]["generated_text"],
        start_step_number=candidate_step_index + 2,
    )


def build_stage_b_dataset(
    train_records_path: Path,
    audit_kept_path: Path,
    output_dir: Path,
    eval_examples: int = 4,
    split_seed: int = 17,
    weight_source: str = "train",
    completion_mode: str = "step",
    rollout_style: str = "locked_careful",
    success_trace_path: Path | None = None,
    chosen_source: str = "stage_a_original",
    eval_example_ids: Sequence[str] | None = None,
    pair_completion_mode: str = "same",
    anchor_mode: str = "none",
    anchor_pair_mode: str = "none",
    protect_mode: str = "none",
    bundle_mode: str = "none",
    include_drop_sft: bool = True,
    drop_sft_filter: str = "none",
    equiv_weight_mode: str = "match",
) -> Dict[str, Any]:
    if completion_mode not in {"step", "rollout"}:
        raise ValueError(f"Unsupported completion_mode: {completion_mode}")
    if pair_completion_mode not in {"same", "step", "rollout", "step_and_rollout"}:
        raise ValueError(f"Unsupported pair_completion_mode: {pair_completion_mode}")
    if anchor_mode not in {"none", "original_rollout"}:
        raise ValueError(f"Unsupported anchor_mode: {anchor_mode}")
    if anchor_pair_mode not in {"none", "original_truncated_pref", "original_counterfactual_pref"}:
        raise ValueError(f"Unsupported anchor_pair_mode: {anchor_pair_mode}")
    if protect_mode not in {"none", "original_over_drop_hinge"}:
        raise ValueError(f"Unsupported protect_mode: {protect_mode}")
    if bundle_mode not in {"none", "original_drop_paraphrase"}:
        raise ValueError(f"Unsupported bundle_mode: {bundle_mode}")
    if drop_sft_filter not in {"none", "one_side_positive", "both_sides_positive"}:
        raise ValueError(f"Unsupported drop_sft_filter: {drop_sft_filter}")
    if equiv_weight_mode not in {"match", "uniform"}:
        raise ValueError(f"Unsupported equiv_weight_mode: {equiv_weight_mode}")
    if not include_drop_sft and anchor_mode == "none":
        raise ValueError("include_drop_sft=False requires anchor_mode=original_rollout.")
    if rollout_style not in CONTINUATOR_STYLES:
        raise ValueError(f"Unsupported rollout_style: {rollout_style}")
    if chosen_source not in {"stage_a_original", "success_trace"}:
        raise ValueError(f"Unsupported chosen_source: {chosen_source}")
    if completion_mode == "rollout" and chosen_source == "success_trace" and success_trace_path is None:
        raise ValueError("success_trace_path is required when chosen_source=success_trace.")
    if anchor_mode == "original_rollout" and (completion_mode != "rollout" or chosen_source != "success_trace"):
        raise ValueError("anchor_mode=original_rollout requires completion_mode=rollout and chosen_source=success_trace.")
    if anchor_pair_mode != "none" and anchor_mode != "original_rollout":
        raise ValueError("anchor_pair_mode requires anchor_mode=original_rollout.")

    train_records = load_stage_a_records(train_records_path)
    audit_rows = _load_audit_keep_rows(audit_kept_path)
    success_traces = _load_success_trace_rows(success_trace_path) if success_trace_path is not None else {}

    missing = sorted(key for key in audit_rows if key not in train_records)
    if missing:
        raise ValueError(f"Audit keep-set keys missing from train records: {missing[:3]}")

    base_rows: List[StageBExample] = []
    unique_examples = sorted({key[0] for key in audit_rows})
    train_ids, eval_ids = _split_example_ids(
        unique_examples,
        eval_examples=eval_examples,
        seed=split_seed,
        eval_example_ids=eval_example_ids,
    )
    eval_id_set = set(eval_ids)
    max_weight = max(_choose_weight(audit_rows[key], weight_source) for key in audit_rows) if audit_rows else 1.0
    max_weight = max(max_weight, 1e-9)
    resolved_pair_completion_mode = completion_mode if pair_completion_mode == "same" else pair_completion_mode
    if resolved_pair_completion_mode == "step_and_rollout":
        resolved_pair_completion_modes = ("step", "rollout")
    else:
        resolved_pair_completion_modes = (resolved_pair_completion_mode,)
    drop_sft_stats = Counter()

    for key in sorted(audit_rows):
        audit_row = audit_rows[key]
        train_record = train_records[key]
        example_id, candidate_step_index = key
        split = "eval" if example_id in eval_id_set else "train"
        prefix_steps = list(train_record["prefixes"]["drop"])
        if completion_mode == "step":
            sft_prompt = build_next_step_prompt(question=train_record["question"], prefix_steps=prefix_steps)
            chosen_completion = train_record["original_step"]
        else:
            sft_prompt = build_rollout_prompt(question=train_record["question"], prefix_steps=prefix_steps)
            if chosen_source == "success_trace":
                if example_id not in success_traces:
                    raise ValueError(f"Missing success trace for example_id={example_id}")
                chosen_completion = _build_success_trace_completion(
                    success_trace=success_traces[example_id],
                    candidate_step_index=candidate_step_index,
                )
            else:
                chosen_completion = _build_rollout_completion(
                    record=train_record,
                    family="original",
                    rollout_style=rollout_style,
                    candidate_step_index=candidate_step_index,
                )
        weight_raw = _choose_weight(audit_row, weight_source)
        weight_normalized = min(weight_raw / max_weight, 1.0)
        train_scores = _copy_scores(audit_row, "train")
        heldout_scores = _copy_scores(audit_row, "heldout")

        if include_drop_sft and _passes_drop_sft_filter(audit_row, drop_sft_filter):
            base_rows.append(
                StageBExample(
                    row_id=f"{example_id}::{candidate_step_index}::sft",
                    split=split,
                    task_type="sft",
                    task_subtype="sft_drop",
                    example_id=example_id,
                    candidate_step_index=candidate_step_index,
                    question=train_record["question"],
                    prompt=sft_prompt,
                    chosen=chosen_completion,
                    rejected_prompt=None,
                    rejected=None,
                    alt_prompt=None,
                    alt_completion=None,
                    weight_raw=weight_raw,
                    weight_normalized=weight_normalized,
                    train_scores=train_scores,
                    heldout_scores=heldout_scores,
                )
            )
            drop_sft_stats[f"{split}_kept"] += 1
        elif include_drop_sft:
            drop_sft_stats[f"{split}_filtered"] += 1

        if anchor_mode == "original_rollout":
            anchor_prompt = build_rollout_prompt(
                question=train_record["question"],
                prefix_steps=list(train_record["prefixes"]["original"]),
            )
            anchor_completion = _build_success_trace_suffix(
                success_trace=success_traces[example_id],
                start_step_index=candidate_step_index + 1,
            )
            base_rows.append(
                StageBExample(
                    row_id=f"{example_id}::{candidate_step_index}::sft_anchor_original",
                    split=split,
                    task_type="sft",
                    task_subtype="sft_anchor_original",
                    example_id=example_id,
                    candidate_step_index=candidate_step_index,
                    question=train_record["question"],
                    prompt=anchor_prompt,
                    chosen=anchor_completion,
                    rejected_prompt=None,
                    rejected=None,
                    alt_prompt=None,
                    alt_completion=None,
                    weight_raw=weight_raw,
                    weight_normalized=weight_normalized,
                    train_scores=train_scores,
                    heldout_scores=heldout_scores,
                )
            )
            if anchor_pair_mode == "original_truncated_pref":
                anchor_rejected = _truncate_completion_suffix(anchor_completion)
                if anchor_rejected and anchor_rejected != anchor_completion:
                    base_rows.append(
                        StageBExample(
                            row_id=f"{example_id}::{candidate_step_index}::pref_anchor_original_trunc",
                            split=split,
                            task_type="pref",
                            task_subtype="pref_anchor_original_trunc",
                            example_id=example_id,
                            candidate_step_index=candidate_step_index,
                            question=train_record["question"],
                            prompt=anchor_prompt,
                            chosen=anchor_completion,
                            rejected_prompt=None,
                            rejected=anchor_rejected,
                            alt_prompt=None,
                            alt_completion=None,
                            weight_raw=weight_raw,
                            weight_normalized=weight_normalized,
                            train_scores=train_scores,
                            heldout_scores=heldout_scores,
                        )
                    )
            elif anchor_pair_mode == "original_counterfactual_pref":
                seen_anchor_rejects: set[str] = set()
                for negative_index, family in enumerate(("swap_quantity", "swap_operation"), start=1):
                    anchor_rejected = _build_counterfactual_anchor_suffix(
                        record=train_record,
                        family=family,
                        rollout_style=rollout_style,
                        candidate_step_index=candidate_step_index,
                    )
                    normalized_rejected = _normalize_step_text(anchor_rejected)
                    if not anchor_rejected or anchor_rejected == anchor_completion or normalized_rejected in seen_anchor_rejects:
                        continue
                    seen_anchor_rejects.add(normalized_rejected)
                    base_rows.append(
                        StageBExample(
                            row_id=f"{example_id}::{candidate_step_index}::pref_anchor_original_cf::{negative_index}",
                            split=split,
                            task_type="pref",
                            task_subtype="pref_anchor_original_cf",
                            example_id=example_id,
                            candidate_step_index=candidate_step_index,
                            question=train_record["question"],
                            prompt=anchor_prompt,
                            chosen=anchor_completion,
                            rejected_prompt=None,
                            rejected=anchor_rejected,
                            alt_prompt=None,
                            alt_completion=None,
                            weight_raw=weight_raw,
                            weight_normalized=weight_normalized,
                            train_scores=train_scores,
                            heldout_scores=heldout_scores,
                        )
                    )
            if protect_mode == "original_over_drop_hinge":
                base_rows.append(
                    StageBExample(
                        row_id=f"{example_id}::{candidate_step_index}::protect_original_over_drop",
                        split=split,
                        task_type="protect",
                        task_subtype="protect_original_over_drop",
                        example_id=example_id,
                        candidate_step_index=candidate_step_index,
                        question=train_record["question"],
                        prompt=anchor_prompt,
                        chosen=anchor_completion,
                        rejected_prompt=sft_prompt,
                        rejected=chosen_completion,
                        alt_prompt=None,
                        alt_completion=None,
                        weight_raw=weight_raw,
                        weight_normalized=weight_normalized,
                        train_scores=train_scores,
                        heldout_scores=heldout_scores,
                    )
                )
            if bundle_mode == "original_drop_paraphrase":
                paraphrase_prompt = build_rollout_prompt(
                    question=train_record["question"],
                    prefix_steps=list(train_record["prefixes"]["paraphrase"]),
                )
                base_rows.append(
                    StageBExample(
                        row_id=f"{example_id}::{candidate_step_index}::bundle_original_drop_paraphrase",
                        split=split,
                        task_type="bundle",
                        task_subtype="bundle_original_drop_paraphrase",
                        example_id=example_id,
                        candidate_step_index=candidate_step_index,
                        question=train_record["question"],
                        prompt=anchor_prompt,
                        chosen=anchor_completion,
                        rejected_prompt=sft_prompt,
                        rejected=chosen_completion,
                        alt_prompt=paraphrase_prompt,
                        alt_completion=anchor_completion,
                        weight_raw=weight_raw,
                        weight_normalized=weight_normalized,
                        train_scores=train_scores,
                        heldout_scores=heldout_scores,
                    )
                )

        paraphrase = train_record["edits"]["paraphrase"]
        negative_steps = _unique_negative_steps(train_record)
        for active_pair_mode in resolved_pair_completion_modes:
            mode_suffix = "" if len(resolved_pair_completion_modes) == 1 else f"::{active_pair_mode}"
            if active_pair_mode == "step":
                pair_prompt = build_next_step_prompt(question=train_record["question"], prefix_steps=prefix_steps)
                chosen_pair_completion = train_record["original_step"]
            else:
                pair_prompt = build_rollout_prompt(question=train_record["question"], prefix_steps=prefix_steps)
                chosen_pair_completion = chosen_completion

            if _normalize_step_text(paraphrase) != _normalize_step_text(train_record["original_step"]):
                equiv_weight_raw, equiv_weight_normalized = _resolve_task_weights(
                    task_type="equiv",
                    weight_raw=weight_raw,
                    weight_normalized=weight_normalized,
                    max_weight=max_weight,
                    equiv_weight_mode=equiv_weight_mode,
                )
                paraphrase_completion = (
                    paraphrase
                    if active_pair_mode == "step"
                    else (
                        _build_success_trace_completion(
                            success_trace=success_traces[example_id],
                            candidate_step_index=candidate_step_index,
                            replacement_step=paraphrase,
                        )
                        if chosen_source == "success_trace"
                        else _build_rollout_completion(
                            record=train_record,
                            family="paraphrase",
                            rollout_style=rollout_style,
                            candidate_step_index=candidate_step_index,
                        )
                    )
                )
                base_rows.append(
                    StageBExample(
                        row_id=f"{example_id}::{candidate_step_index}::equiv{mode_suffix}",
                        split=split,
                        task_type="equiv",
                        task_subtype=f"equiv_{active_pair_mode}",
                        example_id=example_id,
                    candidate_step_index=candidate_step_index,
                    question=train_record["question"],
                    prompt=pair_prompt,
                    chosen=chosen_pair_completion,
                    rejected_prompt=None,
                    rejected=paraphrase_completion,
                    alt_prompt=None,
                    alt_completion=None,
                        weight_raw=equiv_weight_raw,
                        weight_normalized=equiv_weight_normalized,
                        train_scores=train_scores,
                        heldout_scores=heldout_scores,
                    )
                )

            for negative_index, negative_step in enumerate(negative_steps, start=1):
                if active_pair_mode == "step":
                    rejected_completion = negative_step
                else:
                    family = (
                        "swap_quantity"
                        if _normalize_step_text(negative_step) == _normalize_step_text(train_record["edits"]["swap_quantity"])
                        else "swap_operation"
                    )
                    rejected_completion = _build_rollout_completion(
                        record=train_record,
                        family=family,
                        rollout_style=rollout_style,
                        candidate_step_index=candidate_step_index,
                    )
                base_rows.append(
                    StageBExample(
                        row_id=f"{example_id}::{candidate_step_index}::pref{mode_suffix}::{negative_index}",
                        split=split,
                        task_type="pref",
                        task_subtype=f"pref_{active_pair_mode}",
                        example_id=example_id,
                        candidate_step_index=candidate_step_index,
                        question=train_record["question"],
                        prompt=pair_prompt,
                        chosen=chosen_pair_completion,
                        rejected_prompt=None,
                        rejected=rejected_completion,
                        alt_prompt=None,
                        alt_completion=None,
                        weight_raw=weight_raw,
                        weight_normalized=weight_normalized,
                        train_scores=train_scores,
                        heldout_scores=heldout_scores,
                    )
                )

    output_dir.mkdir(parents=True, exist_ok=True)
    train_rows = [row.to_json() for row in base_rows if row.split == "train"]
    eval_rows = [row.to_json() for row in base_rows if row.split == "eval"]
    for path, rows in (
        (output_dir / "train_rows.jsonl", train_rows),
        (output_dir / "eval_rows.jsonl", eval_rows),
        (output_dir / "all_rows.jsonl", [row.to_json() for row in base_rows]),
    ):
        with path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=True) + "\n")

    def summarize(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
        task_counts = Counter(row["task_type"] for row in rows)
        return {
            "num_rows": len(rows),
            "task_counts": dict(sorted(task_counts.items())),
            "num_examples": len({row["example_id"] for row in rows}),
            "mean_weight_raw": _safe_mean([float(row["weight_raw"]) for row in rows]),
            "mean_weight_normalized": _safe_mean([float(row["weight_normalized"]) for row in rows]),
        }

    summary = {
        "train_records_path": str(train_records_path),
        "audit_kept_path": str(audit_kept_path),
        "weight_source": weight_source,
        "split_seed": split_seed,
        "eval_examples": eval_examples,
        "explicit_eval_example_ids": sorted(eval_example_ids) if eval_example_ids is not None else None,
        "completion_mode": completion_mode,
        "pair_completion_mode": resolved_pair_completion_mode,
        "rollout_style": rollout_style if completion_mode == "rollout" else None,
        "chosen_source": chosen_source if completion_mode == "rollout" else None,
        "anchor_mode": anchor_mode,
        "anchor_pair_mode": anchor_pair_mode,
        "protect_mode": protect_mode,
        "bundle_mode": bundle_mode,
        "include_drop_sft": include_drop_sft,
        "drop_sft_filter": drop_sft_filter,
        "equiv_weight_mode": equiv_weight_mode,
        "drop_sft_stats": dict(sorted(drop_sft_stats.items())),
        "success_trace_path": str(success_trace_path) if success_trace_path is not None else None,
        "num_kept_pairs": len(audit_rows),
        "unique_examples": unique_examples,
        "train_example_ids": train_ids,
        "eval_example_ids": eval_ids,
        "train": summarize(train_rows),
        "eval": summarize(eval_rows),
        "sample_rows": train_rows[:3],
    }
    (output_dir / "stage_b_dataset_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return {
        "summary": summary,
        "train_rows": train_rows,
        "eval_rows": eval_rows,
    }


def load_stage_b_rows(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            rows.append(json.loads(line))
    return rows


def _ensure_tokenizer_padding(tokenizer: Any) -> None:
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token


def _encode_prompt_completion(tokenizer: Any, prompt: str, completion: str, max_length: int) -> Dict[str, List[int]]:
    prompt_ids = tokenizer(prompt, add_special_tokens=True)["input_ids"]
    completion_ids = tokenizer(completion, add_special_tokens=False)["input_ids"]
    if not completion_ids:
        raise ValueError("Completion tokenized to empty sequence.")
    total_length = len(prompt_ids) + len(completion_ids)
    if total_length > max_length:
        overflow = total_length - max_length
        if overflow >= len(prompt_ids) - 1:
            raise ValueError("Prompt is too long to fit alongside the completion.")
        prompt_ids = [prompt_ids[0]] + prompt_ids[overflow + 1 :]
    input_ids = prompt_ids + completion_ids
    attention_mask = [1] * len(input_ids)
    labels = [-100] * len(prompt_ids) + completion_ids
    return {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "labels": labels,
    }


def _tensorize(encoded: Dict[str, List[int]], device: str) -> Dict[str, torch.Tensor]:
    return {
        key: torch.tensor([value], device=device, dtype=torch.long)
        for key, value in encoded.items()
    }


def completion_stats(
    model: Any,
    tokenizer: Any,
    prompt: str,
    completion: str,
    device: str,
    max_length: int,
) -> Tuple[torch.Tensor, torch.Tensor]:
    encoded = _encode_prompt_completion(tokenizer=tokenizer, prompt=prompt, completion=completion, max_length=max_length)
    batch = _tensorize(encoded, device=device)
    outputs = model(
        input_ids=batch["input_ids"],
        attention_mask=batch["attention_mask"],
        use_cache=False,
    )
    shift_logits = outputs.logits[:, :-1, :].float()
    shift_labels = batch["labels"][:, 1:]
    mask = shift_labels != -100
    gather_labels = shift_labels.masked_fill(~mask, 0)
    token_log_probs = F.log_softmax(shift_logits, dim=-1).gather(-1, gather_labels.unsqueeze(-1)).squeeze(-1)
    valid_log_probs = token_log_probs[mask]
    if valid_log_probs.numel() == 0:
        raise ValueError("No completion tokens survived masking.")
    average_log_prob = valid_log_probs.mean()
    token_count = mask.sum().float()
    return average_log_prob, token_count


def _normalize_generated_line(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line:
            return _normalize_step_text(line)
    return ""


@torch.no_grad()
def generate_one_step(
    model: Any,
    tokenizer: Any,
    prompt: str,
    device: str,
    max_new_tokens: int,
) -> str:
    encoded = tokenizer(prompt, return_tensors="pt").to(device)
    output = model.generate(
        **encoded,
        max_new_tokens=max_new_tokens,
        do_sample=False,
        pad_token_id=tokenizer.pad_token_id,
    )
    completion_ids = output[0][encoded["input_ids"].shape[1] :]
    text = tokenizer.decode(completion_ids, skip_special_tokens=True)
    return text.strip()


@torch.no_grad()
def evaluate_stage_b_rows(
    model: Any,
    tokenizer: Any,
    rows: Sequence[Dict[str, Any]],
    device: str,
    max_length: int,
    generation_max_new_tokens: int = 48,
) -> Dict[str, Any]:
    pref_margins: List[float] = []
    pref_correct: List[float] = []
    pref_weights: List[float] = []
    protect_margins: List[float] = []
    protect_correct: List[float] = []
    protect_weights: List[float] = []
    equiv_abs_gaps: List[float] = []
    equiv_weights: List[float] = []
    bundle_rank_correct: List[float] = []
    bundle_rank_weights: List[float] = []
    bundle_rank_margins: List[float] = []
    bundle_equiv_abs_gaps: List[float] = []
    bundle_equiv_weights: List[float] = []
    sft_nlls: List[float] = []
    exact_matches: List[float] = []
    task_counts = Counter(row["task_type"] for row in rows)

    for row in rows:
        chosen_lp, _ = completion_stats(
            model=model,
            tokenizer=tokenizer,
            prompt=row["prompt"],
            completion=row["chosen"],
            device=device,
            max_length=max_length,
        )
        if row["task_type"] == "sft":
            sft_nlls.append(float((-chosen_lp).item()))
            generated = generate_one_step(
                model=model,
                tokenizer=tokenizer,
                prompt=row["prompt"],
                device=device,
                max_new_tokens=generation_max_new_tokens,
            )
            exact_matches.append(
                1.0 if _normalize_generated_line(generated) == _normalize_step_text(row["chosen"]) else 0.0
            )
            continue

        rejected_lp, _ = completion_stats(
            model=model,
            tokenizer=tokenizer,
            prompt=row.get("rejected_prompt") or row["prompt"],
            completion=row["rejected"],
            device=device,
            max_length=max_length,
        )
        margin = float((chosen_lp - rejected_lp).item())
        weight = float(row["weight_raw"])
        if row["task_type"] == "pref":
            pref_margins.append(margin)
            pref_correct.append(1.0 if margin > 0.0 else 0.0)
            pref_weights.append(weight)
        elif row["task_type"] == "protect":
            protect_margins.append(margin)
            protect_correct.append(1.0 if margin > 0.0 else 0.0)
            protect_weights.append(weight)
        elif row["task_type"] == "equiv":
            equiv_abs_gaps.append(abs(margin))
            equiv_weights.append(weight)
        elif row["task_type"] == "bundle":
            alt_prompt = row.get("alt_prompt")
            alt_completion = row.get("alt_completion")
            if not alt_prompt or not alt_completion:
                raise ValueError("Bundle row requires alt_prompt and alt_completion.")
            alt_lp, _ = completion_stats(
                model=model,
                tokenizer=tokenizer,
                prompt=alt_prompt,
                completion=alt_completion,
                device=device,
                max_length=max_length,
            )
            alt_margin = float((chosen_lp - alt_lp).item())
            bundle_rank_margins.append(margin)
            bundle_rank_correct.append(1.0 if margin > 0.0 else 0.0)
            bundle_rank_weights.append(weight)
            bundle_equiv_abs_gaps.append(abs(alt_margin))
            bundle_equiv_weights.append(weight)

    def weighted_mean(values: Sequence[float], weights: Sequence[float]) -> float:
        if not values:
            return 0.0
        total_weight = sum(weights)
        if total_weight <= 0.0:
            return _safe_mean(values)
        return sum(value * weight for value, weight in zip(values, weights)) / total_weight

    return {
        "num_rows": len(rows),
        "task_counts": dict(sorted(task_counts.items())),
        "pref_accuracy": _safe_mean(pref_correct),
        "pref_accuracy_weighted": weighted_mean(pref_correct, pref_weights),
        "pref_margin_mean": _safe_mean(pref_margins),
        "pref_margin_weighted_mean": weighted_mean(pref_margins, pref_weights),
        "protect_accuracy": _safe_mean(protect_correct),
        "protect_accuracy_weighted": weighted_mean(protect_correct, protect_weights),
        "protect_margin_mean": _safe_mean(protect_margins),
        "protect_margin_weighted_mean": weighted_mean(protect_margins, protect_weights),
        "equiv_abs_gap_mean": _safe_mean(equiv_abs_gaps),
        "equiv_abs_gap_weighted_mean": weighted_mean(equiv_abs_gaps, equiv_weights),
        "bundle_rank_accuracy": _safe_mean(bundle_rank_correct),
        "bundle_rank_accuracy_weighted": weighted_mean(bundle_rank_correct, bundle_rank_weights),
        "bundle_rank_margin_mean": _safe_mean(bundle_rank_margins),
        "bundle_rank_margin_weighted_mean": weighted_mean(bundle_rank_margins, bundle_rank_weights),
        "bundle_equiv_abs_gap_mean": _safe_mean(bundle_equiv_abs_gaps),
        "bundle_equiv_abs_gap_weighted_mean": weighted_mean(bundle_equiv_abs_gaps, bundle_equiv_weights),
        "sft_nll_mean": _safe_mean(sft_nlls),
        "sft_exact_match": _safe_mean(exact_matches),
    }


def _load_stage_b_model(model_dir: Path, device: str) -> Tuple[Any, Any]:
    tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
    _ensure_tokenizer_padding(tokenizer)
    model = AutoModelForCausalLM.from_pretrained(
        model_dir,
        local_files_only=True,
        torch_dtype=torch.bfloat16,
    )
    model.to(device)
    model.config.use_cache = False
    model.gradient_checkpointing_enable()
    return model, tokenizer


def _row_loss(
    model: Any,
    tokenizer: Any,
    row: Dict[str, Any],
    device: str,
    max_length: int,
    lambda_n: float,
    lambda_inv: float,
    lambda_protect: float,
    lambda_bundle_rank: float,
    lambda_bundle_equiv: float,
    weight_field: str,
    pref_margin_target: float,
    pref_step_multiplier: float,
    pref_rollout_multiplier: float,
    pref_anchor_multiplier: float,
) -> Tuple[torch.Tensor, Dict[str, float]]:
    metrics = {
        "sft": 0.0,
        "pref": 0.0,
        "protect": 0.0,
        "equiv": 0.0,
        "bundle_rank": 0.0,
        "bundle_equiv": 0.0,
        "loss": 0.0,
    }
    zero = torch.zeros((), device=device, dtype=torch.float32, requires_grad=True)
    if row["task_type"] == "pref":
        subtype_multiplier = _pref_subtype_multiplier(
            row.get("task_subtype"),
            pref_step_multiplier=pref_step_multiplier,
            pref_rollout_multiplier=pref_rollout_multiplier,
            pref_anchor_multiplier=pref_anchor_multiplier,
        )
        if lambda_n == 0.0 or subtype_multiplier == 0.0:
            return zero, metrics
    elif row["task_type"] == "protect" and lambda_protect == 0.0:
        return zero, metrics
    elif row["task_type"] == "equiv" and lambda_inv == 0.0:
        return zero, metrics
    elif row["task_type"] == "bundle" and lambda_bundle_rank == 0.0 and lambda_bundle_equiv == 0.0:
        return zero, metrics

    chosen_lp, _ = completion_stats(
        model=model,
        tokenizer=tokenizer,
        prompt=row["prompt"],
        completion=row["chosen"],
        device=device,
        max_length=max_length,
    )
    if row["task_type"] == "sft":
        loss = -chosen_lp
        metrics["sft"] = float(loss.detach().item())
        metrics["loss"] = metrics["sft"]
        return loss, metrics

    weight = float(row[weight_field])
    if row["task_type"] == "pref":
        rejected_lp, _ = completion_stats(
            model=model,
            tokenizer=tokenizer,
            prompt=row.get("rejected_prompt") or row["prompt"],
            completion=row["rejected"],
            device=device,
            max_length=max_length,
        )
        margin = chosen_lp - rejected_lp
        loss = lambda_n * (weight * subtype_multiplier) * F.softplus(pref_margin_target - margin)
        metrics["pref"] = float(loss.detach().item())
    elif row["task_type"] == "protect":
        rejected_lp, _ = completion_stats(
            model=model,
            tokenizer=tokenizer,
            prompt=row.get("rejected_prompt") or row["prompt"],
            completion=row["rejected"],
            device=device,
            max_length=max_length,
        )
        margin = chosen_lp - rejected_lp
        loss = lambda_protect * weight * F.softplus(-margin)
        metrics["protect"] = float(loss.detach().item())
    elif row["task_type"] == "equiv":
        rejected_lp, _ = completion_stats(
            model=model,
            tokenizer=tokenizer,
            prompt=row.get("rejected_prompt") or row["prompt"],
            completion=row["rejected"],
            device=device,
            max_length=max_length,
        )
        margin = chosen_lp - rejected_lp
        loss = lambda_inv * weight * margin.pow(2)
        metrics["equiv"] = float(loss.detach().item())
    elif row["task_type"] == "bundle":
        alt_prompt = row.get("alt_prompt")
        alt_completion = row.get("alt_completion")
        if not alt_prompt or not alt_completion:
            raise ValueError("Bundle row requires alt_prompt and alt_completion.")
        if lambda_bundle_rank > 0.0:
            rejected_lp, _ = completion_stats(
                model=model,
                tokenizer=tokenizer,
                prompt=row.get("rejected_prompt") or row["prompt"],
                completion=row["rejected"],
                device=device,
                max_length=max_length,
            )
            margin = chosen_lp - rejected_lp
            rank_loss = lambda_bundle_rank * weight * F.softplus(-margin)
        else:
            rank_loss = zero
        if lambda_bundle_equiv > 0.0:
            alt_lp, _ = completion_stats(
                model=model,
                tokenizer=tokenizer,
                prompt=alt_prompt,
                completion=alt_completion,
                device=device,
                max_length=max_length,
            )
            equiv_margin = chosen_lp - alt_lp
            equiv_loss = lambda_bundle_equiv * weight * equiv_margin.pow(2)
        else:
            equiv_loss = zero
        loss = rank_loss + equiv_loss
        metrics["bundle_rank"] = float(rank_loss.detach().item())
        metrics["bundle_equiv"] = float(equiv_loss.detach().item())
    else:
        raise ValueError(f"Unsupported task type: {row['task_type']}")
    metrics["loss"] = float(loss.detach().item())
    return loss, metrics


def train_stage_b_model(
    dataset_dir: Path,
    output_dir: Path,
    model_dir: Path = DEFAULT_QWEN3_1P7B,
    device: str = "cuda:0",
    epochs: int = 4,
    learning_rate: float = 1e-6,
    weight_decay: float = 0.01,
    grad_accum_steps: int = 4,
    lambda_n: float = 24.0,
    lambda_inv: float = 8.0,
    lambda_protect: float = 0.0,
    lambda_bundle_rank: float = 0.0,
    lambda_bundle_equiv: float = 0.0,
    weight_field: str = "weight_raw",
    pref_margin_target: float = 0.0,
    pref_step_multiplier: float = 1.0,
    pref_rollout_multiplier: float = 1.0,
    pref_anchor_multiplier: float = 1.0,
    max_length: int = 1024,
    generation_max_new_tokens: int = 48,
    seed: int = 17,
) -> Dict[str, Any]:
    if weight_field not in {"weight_raw", "weight_normalized"}:
        raise ValueError(f"Unsupported weight_field: {weight_field}")
    if pref_margin_target < 0.0:
        raise ValueError("pref_margin_target must be >= 0")
    if lambda_protect < 0.0:
        raise ValueError("lambda_protect must be >= 0")
    if lambda_bundle_rank < 0.0 or lambda_bundle_equiv < 0.0:
        raise ValueError("Bundle lambdas must be >= 0")
    if pref_step_multiplier < 0.0 or pref_rollout_multiplier < 0.0 or pref_anchor_multiplier < 0.0:
        raise ValueError("Pref subtype multipliers must be >= 0")

    train_rows = load_stage_b_rows(dataset_dir / "train_rows.jsonl")
    eval_rows = load_stage_b_rows(dataset_dir / "eval_rows.jsonl")
    dataset_summary = json.loads((dataset_dir / "stage_b_dataset_summary.json").read_text(encoding="utf-8"))

    output_dir.mkdir(parents=True, exist_ok=True)
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    torch.manual_seed(seed)
    random.seed(seed)

    start_time = time.time()
    model, tokenizer = _load_stage_b_model(model_dir=model_dir, device=device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
    total_updates = max(1, math.ceil((len(train_rows) * epochs) / max(1, grad_accum_steps)))
    warmup_updates = max(1, total_updates // 10)
    scheduler = get_linear_schedule_with_warmup(
        optimizer=optimizer,
        num_warmup_steps=warmup_updates,
        num_training_steps=total_updates,
    )

    before_metrics = {
        "train": evaluate_stage_b_rows(
            model=model,
            tokenizer=tokenizer,
            rows=train_rows,
            device=device,
            max_length=max_length,
            generation_max_new_tokens=generation_max_new_tokens,
        ),
        "eval": evaluate_stage_b_rows(
            model=model,
            tokenizer=tokenizer,
            rows=eval_rows,
            device=device,
            max_length=max_length,
            generation_max_new_tokens=generation_max_new_tokens,
        ),
    }

    train_log_rows: List[Dict[str, Any]] = []
    best_eval_pref_accuracy = before_metrics["eval"]["pref_accuracy"]
    optimizer.zero_grad(set_to_none=True)
    global_update = 0

    for epoch in range(1, epochs + 1):
        epoch_rows = list(train_rows)
        random.shuffle(epoch_rows)
        running = {
            "loss": [],
            "sft": [],
            "pref": [],
            "protect": [],
            "equiv": [],
            "bundle_rank": [],
            "bundle_equiv": [],
        }
        model.train()

        for step_index, row in enumerate(epoch_rows, start=1):
            loss, metrics = _row_loss(
                model=model,
                tokenizer=tokenizer,
                row=row,
                device=device,
                max_length=max_length,
                lambda_n=lambda_n,
                lambda_inv=lambda_inv,
                lambda_protect=lambda_protect,
                lambda_bundle_rank=lambda_bundle_rank,
                lambda_bundle_equiv=lambda_bundle_equiv,
                weight_field=weight_field,
                pref_margin_target=pref_margin_target,
                pref_step_multiplier=pref_step_multiplier,
                pref_rollout_multiplier=pref_rollout_multiplier,
                pref_anchor_multiplier=pref_anchor_multiplier,
            )
            (loss / max(1, grad_accum_steps)).backward()
            for name in running:
                running[name].append(metrics[name])
            if step_index % grad_accum_steps == 0 or step_index == len(epoch_rows):
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad(set_to_none=True)
                global_update += 1

        model.eval()
        epoch_metrics = {
            "epoch": epoch,
            "train_loss_mean": _safe_mean(running["loss"]),
            "train_sft_mean": _safe_mean(running["sft"]),
            "train_pref_mean": _safe_mean(running["pref"]),
            "train_protect_mean": _safe_mean(running["protect"]),
            "train_equiv_mean": _safe_mean(running["equiv"]),
            "train_bundle_rank_mean": _safe_mean(running["bundle_rank"]),
            "train_bundle_equiv_mean": _safe_mean(running["bundle_equiv"]),
            "eval": evaluate_stage_b_rows(
                model=model,
                tokenizer=tokenizer,
                rows=eval_rows,
                device=device,
                max_length=max_length,
                generation_max_new_tokens=generation_max_new_tokens,
            ),
        }
        train_log_rows.append(epoch_metrics)
        best_eval_pref_accuracy = max(best_eval_pref_accuracy, epoch_metrics["eval"]["pref_accuracy"])

    after_metrics = {
        "train": evaluate_stage_b_rows(
            model=model,
            tokenizer=tokenizer,
            rows=train_rows,
            device=device,
            max_length=max_length,
            generation_max_new_tokens=generation_max_new_tokens,
        ),
        "eval": evaluate_stage_b_rows(
            model=model,
            tokenizer=tokenizer,
            rows=eval_rows,
            device=device,
            max_length=max_length,
            generation_max_new_tokens=generation_max_new_tokens,
        ),
    }

    model_output_dir = output_dir / "model"
    model.save_pretrained(model_output_dir)
    tokenizer.save_pretrained(model_output_dir)
    with (output_dir / "train_log.jsonl").open("w", encoding="utf-8") as handle:
        for row in train_log_rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")

    summary = {
        "dataset_dir": str(dataset_dir),
        "model_dir": str(model_dir),
        "device": device,
        "epochs": epochs,
        "learning_rate": learning_rate,
        "weight_decay": weight_decay,
        "grad_accum_steps": grad_accum_steps,
        "lambda_n": lambda_n,
        "lambda_inv": lambda_inv,
        "lambda_protect": lambda_protect,
        "lambda_bundle_rank": lambda_bundle_rank,
        "lambda_bundle_equiv": lambda_bundle_equiv,
        "weight_field": weight_field,
        "pref_margin_target": pref_margin_target,
        "pref_step_multiplier": pref_step_multiplier,
        "pref_rollout_multiplier": pref_rollout_multiplier,
        "pref_anchor_multiplier": pref_anchor_multiplier,
        "max_length": max_length,
        "generation_max_new_tokens": generation_max_new_tokens,
        "seed": seed,
        "total_updates": global_update,
        "dataset_summary": dataset_summary,
        "before_metrics": before_metrics,
        "after_metrics": after_metrics,
        "best_eval_pref_accuracy": best_eval_pref_accuracy,
        "epoch_logs": train_log_rows,
        "wall_clock_seconds": time.time() - start_time,
    }
    (output_dir / "stage_b_training_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


ROLLOUT_FAMILIES = ("original", "drop", "paraphrase", "swap_quantity", "swap_operation")


def _score_rollout_style_result(style_result: Dict[str, Any], gold_decimal: Any) -> Dict[str, Any]:
    generated = str(style_result["generated_text"])
    predicted, answer_source = extract_verifiable_answer(generated)
    verified = predicted == gold_decimal if predicted is not None else False
    updated = dict(style_result)
    updated["predicted_answer"] = str(predicted) if predicted is not None else None
    updated["answer_source"] = answer_source
    updated["verified"] = verified
    return updated


def _solve_probability(style_results: Dict[str, Dict[str, Any]], selected_styles: Sequence[str]) -> float:
    return _safe_mean([float(style_results[style]["verified"]) for style in selected_styles])


def _rescore_rollout_record(
    record: Dict[str, Any],
    gold_decimal: Any,
    selected_styles: Sequence[str],
    stability_sigma: float,
) -> Dict[str, Any]:
    rescored = dict(record)
    style_results: Dict[str, Dict[str, Dict[str, Any]]] = {}
    family_scores: Dict[str, float] = {}

    for family in ROLLOUT_FAMILIES:
        family_styles = {
            style: _score_rollout_style_result(record["style_results"][family][style], gold_decimal)
            for style in selected_styles
        }
        style_results[family] = family_styles
        family_scores[family] = _solve_probability(family_styles, selected_styles)

    deltas = [
        family_scores["original"] - family_scores["drop"],
        family_scores["original"] - family_scores["swap_quantity"],
        family_scores["original"] - family_scores["swap_operation"],
    ]
    style_level_deltas: List[float] = []
    for style in selected_styles:
        original_score = float(style_results["original"][style]["verified"])
        style_level_deltas.extend(
            [
                original_score - float(style_results["drop"][style]["verified"]),
                original_score - float(style_results["swap_quantity"][style]["verified"]),
                original_score - float(style_results["swap_operation"][style]["verified"]),
            ]
        )
    stability = math.exp(-torch.tensor(style_level_deltas).float().var(unbiased=False).item() / (stability_sigma**2))
    n_t = _safe_mean(deltas)

    rescored["style_results"] = style_results
    rescored["scores"] = {
        "original": family_scores["original"],
        "drop": family_scores["drop"],
        "paraphrase": family_scores["paraphrase"],
        "swap_quantity": family_scores["swap_quantity"],
        "swap_operation": family_scores["swap_operation"],
        "n_t": n_t,
        "stability": stability,
        "n_t_weighted": n_t * stability,
        "paraphrase_gap": abs(family_scores["original"] - family_scores["paraphrase"]),
    }
    return rescored


def _answer_source_counts(records: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    counts: Counter[str] = Counter()
    for record in records:
        for family in ROLLOUT_FAMILIES:
            for style_result in record["style_results"][family].values():
                counts[str(style_result.get("answer_source", "missing_answer_source"))] += 1
    return dict(sorted(counts.items()))


def evaluate_stage_b_rollout(
    train_records_path: Path,
    audit_kept_path: Path,
    dataset_summary_path: Path,
    data_path: Path,
    output_dir: Path,
    model_dir: Path = DEFAULT_QWEN3_1P7B,
    device: str = "cuda:0",
    split: str = "eval",
    continuation_max_new_tokens: int = 220,
    stability_sigma: float = 0.25,
    styles: Sequence[str] | None = None,
) -> Dict[str, Any]:
    if split not in {"train", "eval", "all"}:
        raise ValueError(f"Unsupported split: {split}")

    selected_styles = tuple(styles or CONTINUATOR_STYLES)
    invalid_styles = sorted(style for style in selected_styles if style not in CONTINUATOR_STYLES)
    if invalid_styles:
        raise ValueError(f"Unsupported continuator styles: {invalid_styles}")

    train_records = load_stage_a_records(train_records_path)
    audit_rows = _load_audit_keep_rows(audit_kept_path)
    dataset_summary = json.loads(dataset_summary_path.read_text(encoding="utf-8"))
    if split == "all":
        selected_example_ids = set(dataset_summary["unique_examples"])
    else:
        selected_example_ids = set(dataset_summary[f"{split}_example_ids"])

    gold_answers = {example.example_id: str(example.gold_answer) for example in load_gsm8k(data_path)}
    missing_gold = sorted(example_id for example_id in selected_example_ids if example_id not in gold_answers)
    if missing_gold:
        raise ValueError(f"Missing gold answers for examples: {missing_gold[:3]}")

    generator = LocalQwenGenerator(model_dir=model_dir, device=device, max_new_tokens=continuation_max_new_tokens)

    def evaluate_prefix_subset(question: str, prefix_steps: Sequence[str], gold_answer: str) -> Dict[str, Any]:
        style_results: Dict[str, Dict[str, Any]] = {}
        gold_decimal = extract_predicted_answer(f"Final answer: {gold_answer}")
        solve_scores: List[float] = []
        for style in selected_styles:
            prompt = build_continuation_prompt(question, prefix_steps, style=style)
            generated, completion_tokens = generator.generate(prompt, max_new_tokens=continuation_max_new_tokens)
            generated = truncate_at_final_answer(generated)
            predicted, answer_source = extract_verifiable_answer(generated)
            verified = predicted == gold_decimal if predicted is not None else False
            solve_scores.append(float(verified))
            style_results[style] = {
                "generated_text": generated,
                "predicted_answer": str(predicted) if predicted is not None else None,
                "answer_source": answer_source,
                "verified": verified,
                "completion_tokens": completion_tokens,
                "step_texts": split_steps(generated),
            }
        return {
            "solve_probability": _safe_mean(solve_scores),
            "style_results": style_results,
        }

    records: List[Dict[str, Any]] = []
    for key in sorted(audit_rows):
        example_id, candidate_step_index = key
        if example_id not in selected_example_ids:
            continue
        train_record = train_records[key]
        gold_answer = gold_answers[example_id]
        original_eval = evaluate_prefix_subset(
            question=train_record["question"],
            prefix_steps=train_record["prefixes"]["original"],
            gold_answer=gold_answer,
        )
        drop_eval = evaluate_prefix_subset(
            question=train_record["question"],
            prefix_steps=train_record["prefixes"]["drop"],
            gold_answer=gold_answer,
        )
        paraphrase_eval = evaluate_prefix_subset(
            question=train_record["question"],
            prefix_steps=train_record["prefixes"]["paraphrase"],
            gold_answer=gold_answer,
        )
        swap_quantity_eval = evaluate_prefix_subset(
            question=train_record["question"],
            prefix_steps=train_record["prefixes"]["swap_quantity"],
            gold_answer=gold_answer,
        )
        swap_operation_eval = evaluate_prefix_subset(
            question=train_record["question"],
            prefix_steps=train_record["prefixes"]["swap_operation"],
            gold_answer=gold_answer,
        )

        deltas = [
            original_eval["solve_probability"] - drop_eval["solve_probability"],
            original_eval["solve_probability"] - swap_quantity_eval["solve_probability"],
            original_eval["solve_probability"] - swap_operation_eval["solve_probability"],
        ]
        style_level_deltas: List[float] = []
        for style in selected_styles:
            original_score = float(original_eval["style_results"][style]["verified"])
            style_level_deltas.extend(
                [
                    original_score - float(drop_eval["style_results"][style]["verified"]),
                    original_score - float(swap_quantity_eval["style_results"][style]["verified"]),
                    original_score - float(swap_operation_eval["style_results"][style]["verified"]),
                ]
            )
        stability = math.exp(-torch.tensor(style_level_deltas).float().var(unbiased=False).item() / (stability_sigma**2))
        n_t = _safe_mean(deltas)
        records.append(
            {
                "example_id": example_id,
                "candidate_step_index": candidate_step_index,
                "question": train_record["question"],
                "original_step": train_record["original_step"],
                "prefixes": train_record["prefixes"],
                "edits": train_record["edits"],
                "reference_train_scores": audit_rows[key]["train_scores"],
                "reference_heldout_scores": audit_rows[key]["heldout_scores"],
                "scores": {
                    "original": original_eval["solve_probability"],
                    "drop": drop_eval["solve_probability"],
                    "paraphrase": paraphrase_eval["solve_probability"],
                    "swap_quantity": swap_quantity_eval["solve_probability"],
                    "swap_operation": swap_operation_eval["solve_probability"],
                    "n_t": n_t,
                    "stability": stability,
                    "n_t_weighted": n_t * stability,
                    "paraphrase_gap": abs(original_eval["solve_probability"] - paraphrase_eval["solve_probability"]),
                },
                "style_results": {
                    "original": original_eval["style_results"],
                    "drop": drop_eval["style_results"],
                    "paraphrase": paraphrase_eval["style_results"],
                    "swap_quantity": swap_quantity_eval["style_results"],
                    "swap_operation": swap_operation_eval["style_results"],
                },
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize_stage_a(records)
    summary.update(
        {
            "train_records_path": str(train_records_path),
            "audit_kept_path": str(audit_kept_path),
            "dataset_summary_path": str(dataset_summary_path),
            "data_path": str(data_path),
            "model_dir": str(model_dir),
            "device": device,
            "split": split,
            "selected_example_ids": sorted(selected_example_ids),
            "continuation_max_new_tokens": continuation_max_new_tokens,
            "continuator_styles": list(selected_styles),
            "verdict_mode": "strict_final_answer_or_blank_final_recovery",
            "answer_source_counts": _answer_source_counts(records),
        }
    )
    (output_dir / "stage_b_rollout_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    with (output_dir / "stage_b_rollout_records.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")
    return {"summary": summary, "records": records}


def rescore_stage_b_rollout_records(
    records_path: Path,
    data_path: Path,
    output_dir: Path,
    stability_sigma: float = 0.25,
    styles: Sequence[str] | None = None,
    summary_path: Path | None = None,
) -> Dict[str, Any]:
    records = load_stage_b_rows(records_path)
    if not records:
        raise ValueError(f"No rollout records found in {records_path}")

    selected_styles = tuple(styles or records[0]["style_results"]["original"].keys())
    gold_answers = {example.example_id: example.gold_answer for example in load_gsm8k(data_path)}
    rescored_records: List[Dict[str, Any]] = []
    for record in records:
        example_id = str(record["example_id"])
        if example_id not in gold_answers:
            raise ValueError(f"Missing gold answer for example_id={example_id}")
        rescored_records.append(
            _rescore_rollout_record(
                record=record,
                gold_decimal=gold_answers[example_id],
                selected_styles=selected_styles,
                stability_sigma=stability_sigma,
            )
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize_stage_a(rescored_records)
    summary_metadata: Dict[str, Any] = {}
    inferred_summary_path = summary_path or records_path.with_name("stage_b_rollout_summary.json")
    if inferred_summary_path.exists():
        previous_summary = json.loads(inferred_summary_path.read_text(encoding="utf-8"))
        for key in (
            "train_records_path",
            "audit_kept_path",
            "dataset_summary_path",
            "data_path",
            "model_dir",
            "device",
            "split",
            "selected_example_ids",
            "continuation_max_new_tokens",
            "continuator_styles",
        ):
            if key in previous_summary:
                summary_metadata[key] = previous_summary[key]
    summary.update(summary_metadata)
    summary.update(
        {
            "records_path": str(records_path),
            "data_path": str(data_path),
            "verdict_mode": "strict_final_answer_or_blank_final_recovery",
            "answer_source_counts": _answer_source_counts(rescored_records),
            "rescored_from_existing_records": True,
        }
    )
    (output_dir / "stage_b_rollout_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    with (output_dir / "stage_b_rollout_records.jsonl").open("w", encoding="utf-8") as handle:
        for record in rescored_records:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")
    return {"summary": summary, "records": rescored_records}
