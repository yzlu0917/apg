from __future__ import annotations

import itertools
import json
import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from civic_prm.acceptance import ACCEPTANCE_MODES, summarize_pair_calls
from civic_prm.api_judge import APIJudgeClient
from civic_prm.api_rewrite import rewrite_record_pair_with_api, rewrite_record_with_api
from civic_prm.schema import TraceExample


ROLE_ORDER = [
    "valid_correct",
    "invalid_correct",
    "valid_swapped",
    "invalid_swapped",
]


def _benchmark_verbalizer_id(verbalizer_id: str) -> str:
    return verbalizer_id if verbalizer_id.endswith("_b3") else f"{verbalizer_id}_b3"


@dataclass(frozen=True)
class CandidateTrace:
    candidate_id: str
    source_trace_id: str
    quartet_id: str
    domain: str
    verbalizer_id: str
    counterfactual_role: str
    process_variant: str
    answer_variant: str
    is_valid_process: bool
    answer_is_correct: bool
    problem_text: str
    step_texts: list[str]
    final_answer_line: str
    masked_answer_line: str
    trace_text: str
    masked_trace_text: str
    metadata: dict[str, Any]

    def to_trace_example(self) -> TraceExample:
        return TraceExample(
            trace_id=self.candidate_id,
            quartet_id=self.quartet_id,
            problem_id=self.metadata["problem_id"],
            domain=self.domain,
            verbalizer_id=self.verbalizer_id,
            audited_locus=self.metadata["audited_locus"],
            counterfactual_role=self.counterfactual_role,
            process_variant=self.process_variant,
            answer_variant=self.answer_variant,
            is_valid_process=self.is_valid_process,
            answer_is_correct=self.answer_is_correct,
            problem_text=self.problem_text,
            step_texts=self.step_texts,
            final_answer_line=self.final_answer_line,
            masked_answer_line=self.masked_answer_line,
            trace_text=self.trace_text,
            masked_trace_text=self.masked_trace_text,
            metadata=self.metadata,
        )

    def to_record(self) -> dict[str, Any]:
        return self.to_trace_example().to_record()


def select_quartets_balanced(records: list[TraceExample], quartets_per_domain: int, seed: int) -> list[str]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for quartet_id in sorted({record.quartet_id for record in records}):
        domain = next(record.domain for record in records if record.quartet_id == quartet_id)
        grouped[domain].append(quartet_id)
    rng = random.Random(seed)
    selected: list[str] = []
    for domain in sorted(grouped):
        candidates = list(grouped[domain])
        rng.shuffle(candidates)
        selected.extend(sorted(candidates[:quartets_per_domain]))
    return selected


def select_verbalizers(records: list[TraceExample], selected_quartets: list[str], verbalizers_per_quartet: int, seed: int) -> dict[str, list[str]]:
    rng = random.Random(seed)
    selected: dict[str, list[str]] = {}
    for quartet_id in selected_quartets:
        verbalizer_ids = sorted({record.verbalizer_id for record in records if record.quartet_id == quartet_id})
        rng.shuffle(verbalizer_ids)
        selected[quartet_id] = sorted(verbalizer_ids[:verbalizers_per_quartet])
    return selected


def temperature_schedule(num_candidates: int, base_temperature: float) -> list[float]:
    if num_candidates <= 1:
        return [base_temperature]
    offsets = [-0.2, 0.0, 0.2, -0.1, 0.1]
    temps = []
    for index in range(num_candidates):
        temp = max(0.2, min(1.0, base_temperature + offsets[index % len(offsets)]))
        temps.append(round(temp, 2))
    return temps


def _extract_json_object(text: str) -> dict[str, Any]:
    candidates = re.findall(r"\{.*\}", text, flags=re.DOTALL)
    for candidate in reversed(candidates):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    label_match = re.search(r'"more_artificial"\s*:\s*"(trace_1|trace_2|both|neither)"', text, flags=re.IGNORECASE)
    confidence_match = re.search(r'"confidence"\s*:\s*([1-5])', text)
    if label_match and confidence_match:
        reason_match = re.search(r'"reason"\s*:\s*"([^"]*)', text, flags=re.DOTALL)
        return {
            "more_artificial": label_match.group(1).lower(),
            "confidence": int(confidence_match.group(1)),
            "reason": (reason_match.group(1) if reason_match else "").strip(),
        }
    single_label_match = re.search(r'"looks_artificial"\s*:\s*"(yes|no|unclear)"', text, flags=re.IGNORECASE)
    if single_label_match and confidence_match:
        reason_match = re.search(r'"reason"\s*:\s*"([^"]*)', text, flags=re.DOTALL)
        return {
            "looks_artificial": single_label_match.group(1).lower(),
            "confidence": int(confidence_match.group(1)),
            "reason": (reason_match.group(1) if reason_match else "").strip(),
        }
    raise ValueError(f"could not parse JSON from reviewer response: {text[:200]}")


def _build_pair_review_messages(problem_text: str, left_trace: str, right_trace: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are reviewing two hidden-label reasoning traces. "
                "Do not judge correctness. Judge only which trace looks more artificially templated, hand-edited, or patched. "
                "Keep the reason under 12 words. "
                'Reply with JSON only: {"more_artificial":"trace_1|trace_2|both|neither","confidence":1-5,"reason":"..."}'
            ),
        },
        {
            "role": "user",
            "content": (
                "/no_think\n"
                f"Problem:\n{problem_text}\n\n"
                f"Trace 1:\n{left_trace}\n\n"
                f"Trace 2:\n{right_trace}\n"
            ),
        },
    ]


def _build_single_review_messages(problem_text: str, trace_text: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are reviewing one hidden-label reasoning trace. "
                "Do not judge correctness. Judge only whether the trace itself looks artificially templated, hand-edited, or patched. "
                "Keep the reason under 10 words. "
                'Reply with JSON only: {"looks_artificial":"yes|no|unclear","confidence":1-5,"reason":"..."}'
            ),
        },
        {
            "role": "user",
            "content": (
                "/no_think\n"
                f"Problem:\n{problem_text}\n\n"
                f"Trace:\n{trace_text}\n"
            ),
        },
    ]


def _call_reviewer(client: APIJudgeClient, problem_text: str, left_trace: str, right_trace: str) -> dict[str, Any]:
    payload = {
        "messages": _build_pair_review_messages(problem_text, left_trace, right_trace),
        "temperature": 0,
        "max_tokens": 96,
    }
    if hasattr(client, "model"):
        payload["model"] = client.model
    response = client._post_json(payload)
    content = response["choices"][0]["message"]["content"]
    parsed = _extract_json_object(content)
    label = str(parsed.get("more_artificial", "")).strip().lower()
    if label not in {"trace_1", "trace_2", "both", "neither"}:
        raise ValueError(f"unexpected reviewer label: {label}")
    confidence = int(parsed.get("confidence", 3))
    return {
        "more_artificial": label,
        "confidence": max(1, min(5, confidence)),
        "reason": str(parsed.get("reason", "")).strip(),
        "raw_response": content,
        "usage": response.get("usage", {}),
    }


def _call_single_reviewer(client: APIJudgeClient, problem_text: str, trace_text: str) -> dict[str, Any]:
    payload = {
        "messages": _build_single_review_messages(problem_text, trace_text),
        "temperature": 0,
        "max_tokens": 72,
    }
    if hasattr(client, "model"):
        payload["model"] = client.model
    response = client._post_json(payload)
    content = response["choices"][0]["message"]["content"]
    parsed = _extract_json_object(content)
    label = str(parsed.get("looks_artificial", "")).strip().lower()
    if label not in {"yes", "no", "unclear"}:
        label_match = re.search(r'"looks_artificial"\s*:\s*"(yes|no|unclear)"', content, flags=re.IGNORECASE)
        if label_match:
            label = label_match.group(1).lower()
        else:
            raise ValueError(f"unexpected single-review label: {label}")
    confidence = int(parsed.get("confidence", 3))
    return {
        "looks_artificial": label,
        "confidence": max(1, min(5, confidence)),
        "reason": str(parsed.get("reason", "")).strip(),
        "raw_response": content,
        "usage": response.get("usage", {}),
    }


def _detectability_penalty(label: str, confidence: int) -> float:
    if label == "neither":
        return 0.0
    if label == "both":
        return 0.5
    return 0.5 + 0.1 * confidence


def _single_detectability_penalty(label: str, confidence: int) -> float:
    if label == "no":
        return 0.0
    if label == "unclear":
        return 0.25
    return 0.5 + 0.1 * confidence


def review_pair_bidirectional(
    client: APIJudgeClient,
    valid_candidate: CandidateTrace,
    invalid_candidate: CandidateTrace,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    calls: list[dict[str, Any]] = []
    for order_name, left, right in [
        ("forward", valid_candidate, invalid_candidate),
        ("reverse", invalid_candidate, valid_candidate),
    ]:
        review = _call_reviewer(client, left.problem_text, left.masked_trace_text, right.masked_trace_text)
        picked_candidate = None
        if review["more_artificial"] == "trace_1":
            picked_candidate = left.candidate_id
        elif review["more_artificial"] == "trace_2":
            picked_candidate = right.candidate_id
        calls.append(
            {
                "order": order_name,
                "label": review["more_artificial"],
                "confidence": review["confidence"],
                "picked_candidate_id": picked_candidate,
                "picked_invalid": picked_candidate == invalid_candidate.candidate_id,
                "reason": review["reason"],
                "usage": review["usage"],
                "raw_response": review["raw_response"],
            }
        )
    strict_summary = summarize_pair_calls(calls, mode="strict")
    summary = {
        **strict_summary,
        "avg_detectability_penalty_by_mode": {
            mode: summarize_pair_calls(calls, mode=mode)["avg_detectability_penalty"]
            for mode in ACCEPTANCE_MODES
        },
    }
    return summary, calls


def prune_candidates_with_reviewer(
    reviewer_client: APIJudgeClient,
    quartet_id: str,
    domain: str,
    verbalizer_id: str,
    candidate_map: dict[str, list[CandidateTrace]],
    candidate_max_detectability: float | None = None,
    max_candidates_per_role_after_prune: int | None = None,
) -> tuple[dict[str, list[CandidateTrace]], list[dict[str, Any]], dict[str, Any], Counter]:
    usage_totals = Counter()
    review_rows: list[dict[str, Any]] = []
    pruned_candidate_map: dict[str, list[CandidateTrace]] = {}
    role_counts_before = {role: len(candidate_map[role]) for role in ROLE_ORDER}
    role_counts_after: dict[str, int] = {}
    role_candidate_summaries: dict[str, list[dict[str, Any]]] = {}

    for role in ROLE_ORDER:
        candidates = candidate_map[role]
        candidate_penalties: dict[str, list[float]] = {candidate.candidate_id: [] for candidate in candidates}
        candidate_confidences: dict[str, list[int]] = {candidate.candidate_id: [] for candidate in candidates}
        if len(candidates) >= 2:
            for left, right in itertools.combinations(candidates, 2):
                for order_name, first, second in [("forward", left, right), ("reverse", right, left)]:
                    review = _call_reviewer(
                        reviewer_client,
                        first.problem_text,
                        first.masked_trace_text,
                        second.masked_trace_text,
                    )
                    usage = review.get("usage", {})
                    usage_totals["prompt_tokens"] += usage.get("prompt_tokens", 0)
                    usage_totals["completion_tokens"] += usage.get("completion_tokens", 0)
                    usage_totals["total_tokens"] += usage.get("total_tokens", 0)
                    usage_totals["num_calls"] += 1
                    penalty = _detectability_penalty(review["more_artificial"], review["confidence"])
                    first_penalty = 0.0
                    second_penalty = 0.0
                    picked_candidate_id = None
                    if review["more_artificial"] == "both":
                        first_penalty = 0.5
                        second_penalty = 0.5
                    elif review["more_artificial"] == "trace_1":
                        first_penalty = penalty
                        picked_candidate_id = first.candidate_id
                    elif review["more_artificial"] == "trace_2":
                        second_penalty = penalty
                        picked_candidate_id = second.candidate_id
                    candidate_penalties[first.candidate_id].append(first_penalty)
                    candidate_penalties[second.candidate_id].append(second_penalty)
                    candidate_confidences[first.candidate_id].append(review["confidence"])
                    candidate_confidences[second.candidate_id].append(review["confidence"])
                    review_rows.append(
                        {
                            "review_stage": "candidate_prune_pairwise",
                            "quartet_id": quartet_id,
                            "domain": domain,
                            "verbalizer_id": verbalizer_id,
                            "counterfactual_role": role,
                            "order": order_name,
                            "left_candidate_id": first.candidate_id,
                            "right_candidate_id": second.candidate_id,
                            "label": review["more_artificial"],
                            "confidence": review["confidence"],
                            "picked_candidate_id": picked_candidate_id,
                            "left_penalty": first_penalty,
                            "right_penalty": second_penalty,
                            "reason": review["reason"],
                            "raw_response": review["raw_response"],
                        }
                    )

        scored_candidates: list[tuple[tuple[float, float, float, str], CandidateTrace]] = []
        role_candidate_summaries[role] = []
        for candidate in candidates:
            penalties = candidate_penalties[candidate.candidate_id]
            confidences = candidate_confidences[candidate.candidate_id]
            mean_penalty = sum(penalties) / len(penalties) if penalties else 0.0
            picked_rate = sum(1 for penalty in penalties if penalty > 0) / len(penalties) if penalties else 0.0
            mean_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            candidate_summary = {
                "candidate_id": candidate.candidate_id,
                "mean_detectability_penalty": mean_penalty,
                "picked_as_more_artificial_rate": picked_rate,
                "mean_confidence": mean_confidence,
            }
            role_candidate_summaries[role].append(candidate_summary)
            scored_candidates.append(((mean_penalty, picked_rate, mean_confidence, candidate.candidate_id), candidate))

        scored_candidates.sort(key=lambda item: item[0])
        filtered = [
            candidate
            for (rank_key, candidate) in scored_candidates
            if candidate_max_detectability is None or rank_key[0] <= candidate_max_detectability
        ]
        if max_candidates_per_role_after_prune is not None:
            filtered = filtered[:max_candidates_per_role_after_prune]
        pruned_candidate_map[role] = filtered
        role_counts_after[role] = len(filtered)

    summary = {
        "quartet_id": quartet_id,
        "domain": domain,
        "verbalizer_id": verbalizer_id,
        "candidate_max_detectability": candidate_max_detectability,
        "max_candidates_per_role_after_prune": max_candidates_per_role_after_prune,
        "role_counts_before": role_counts_before,
        "role_counts_after": role_counts_after,
        "role_candidate_summaries": role_candidate_summaries,
        "all_roles_survive": all(role_counts_after[role] > 0 for role in ROLE_ORDER),
    }
    return pruned_candidate_map, review_rows, summary, usage_totals


def build_candidates_for_record(
    client: APIJudgeClient,
    record: TraceExample,
    num_candidates: int,
    base_temperature: float,
    max_tokens: int = 320,
) -> tuple[list[CandidateTrace], Counter]:
    usage_totals = Counter()
    candidates: list[CandidateTrace] = []
    for candidate_index, temperature in enumerate(temperature_schedule(num_candidates, base_temperature), start=1):
        rewrite = rewrite_record_with_api(client, record.to_record(), temperature=temperature, max_tokens=max_tokens)
        usage = rewrite.get("usage", {})
        usage_totals["prompt_tokens"] += usage.get("prompt_tokens", 0)
        usage_totals["completion_tokens"] += usage.get("completion_tokens", 0)
        usage_totals["total_tokens"] += usage.get("total_tokens", 0)
        usage_totals["num_calls"] += rewrite.get("api_calls", 1)
        metadata = dict(record.metadata)
        metadata.update(
            {
                "problem_id": record.problem_id,
                "audited_locus": record.audited_locus,
                "benchmark_v3": True,
                "benchmark_v3_source_trace_id": record.trace_id,
                "benchmark_v3_candidate_index": candidate_index,
                "benchmark_v3_rewriter_name": rewrite["rewriter_name"],
                "benchmark_v3_temperature": temperature,
            }
        )
        candidates.append(
            CandidateTrace(
                candidate_id=f"{record.trace_id}-b3c{candidate_index:02d}",
                source_trace_id=record.trace_id,
                quartet_id=record.quartet_id,
                domain=record.domain,
                verbalizer_id=_benchmark_verbalizer_id(record.verbalizer_id),
                counterfactual_role=record.counterfactual_role,
                process_variant=record.process_variant,
                answer_variant=record.answer_variant,
                is_valid_process=record.is_valid_process,
                answer_is_correct=record.answer_is_correct,
                problem_text=rewrite["problem_text"],
                step_texts=rewrite["step_texts"],
                final_answer_line=record.final_answer_line,
                masked_answer_line=record.masked_answer_line,
                trace_text="\n".join(rewrite["step_texts"] + [record.final_answer_line]),
                masked_trace_text="\n".join(rewrite["step_texts"] + [record.masked_answer_line]),
                metadata=metadata,
            )
        )
    return candidates, usage_totals


def build_pair_conditioned_candidates(
    client: APIJudgeClient,
    record_a: TraceExample,
    record_b: TraceExample,
    num_candidates: int,
    base_temperature: float,
    max_tokens: int = 480,
    contrast_aware: bool = False,
    reviewer_client: Any | None = None,
    regeneration_rounds: int = 0,
    regeneration_top_k: int = 1,
    regeneration_threshold: float | None = None,
) -> tuple[list[CandidateTrace], list[CandidateTrace], Counter]:
    usage_totals = Counter()
    candidates_a: list[CandidateTrace] = []
    candidates_b: list[CandidateTrace] = []
    next_candidate_index = 1

    def _append_candidate_pair(
        source_a: TraceExample | CandidateTrace,
        source_b: TraceExample | CandidateTrace,
        candidate_index: int,
        temperature: float,
        feedback: list[str] | None = None,
        round_index: int = 0,
    ) -> None:
        rewrite = rewrite_record_pair_with_api(
            client,
            source_a.to_record(),
            source_b.to_record(),
            temperature=temperature,
            max_tokens=max_tokens,
            contrast_aware=contrast_aware,
            feedback=feedback,
        )
        usage = rewrite.get("usage", {})
        usage_totals["prompt_tokens"] += usage.get("prompt_tokens", 0)
        usage_totals["completion_tokens"] += usage.get("completion_tokens", 0)
        usage_totals["total_tokens"] += usage.get("total_tokens", 0)
        usage_totals["num_calls"] += rewrite.get("api_calls", 1)

        for record, partner, step_texts, bucket in [
            (source_a, source_b, rewrite["trace_1_steps"], candidates_a),
            (source_b, source_a, rewrite["trace_2_steps"], candidates_b),
        ]:
            metadata = dict(record.metadata)
            problem_id = getattr(record, "problem_id", metadata.get("problem_id"))
            audited_locus = getattr(record, "audited_locus", metadata.get("audited_locus"))
            trace_id = getattr(record, "trace_id", getattr(record, "candidate_id", None))
            partner_trace_id = getattr(partner, "trace_id", getattr(partner, "candidate_id", None))
            metadata.update(
                {
                    "problem_id": problem_id,
                    "audited_locus": audited_locus,
                    "benchmark_v3": True,
                    "benchmark_v3_source_trace_id": trace_id,
                    "benchmark_v3_candidate_index": candidate_index,
                    "benchmark_v3_rewriter_name": rewrite["rewriter_name"],
                    "benchmark_v3_temperature": temperature,
                    "benchmark_v3_pair_conditioned": True,
                    "benchmark_v3_pair_partner_trace_id": partner_trace_id,
                    "benchmark_v3_regeneration_round": round_index,
                    "benchmark_v3_feedback": feedback or [],
                }
            )
            bucket.append(
                CandidateTrace(
                    candidate_id=f"{trace_id}-b3pc{candidate_index:02d}",
                    source_trace_id=str(trace_id),
                    quartet_id=record.quartet_id,
                    domain=record.domain,
                    verbalizer_id=_benchmark_verbalizer_id(record.verbalizer_id),
                    counterfactual_role=record.counterfactual_role,
                    process_variant=record.process_variant,
                    answer_variant=record.answer_variant,
                    is_valid_process=record.is_valid_process,
                    answer_is_correct=record.answer_is_correct,
                    problem_text=rewrite["problem_text"],
                    step_texts=step_texts,
                    final_answer_line=record.final_answer_line,
                    masked_answer_line=record.masked_answer_line,
                    trace_text="\n".join(step_texts + [record.final_answer_line]),
                    masked_trace_text="\n".join(step_texts + [record.masked_answer_line]),
                    metadata=metadata,
                )
            )

    for temperature in temperature_schedule(num_candidates, base_temperature):
        _append_candidate_pair(record_a, record_b, next_candidate_index, temperature=temperature, round_index=0)
        next_candidate_index += 1

    for round_index in range(1, regeneration_rounds + 1):
        if reviewer_client is None:
            break
        valid_by_index = {
            int(candidate.metadata["benchmark_v3_candidate_index"]): candidate
            for candidate in candidates_a
        }
        invalid_by_index = {
            int(candidate.metadata["benchmark_v3_candidate_index"]): candidate
            for candidate in candidates_b
        }
        shared_indexes = sorted(set(valid_by_index) & set(invalid_by_index))
        ranked_pairs: list[tuple[float, int, list[str], CandidateTrace, CandidateTrace]] = []
        for candidate_index in shared_indexes:
            candidate_a = valid_by_index[candidate_index]
            candidate_b = invalid_by_index[candidate_index]
            summary, calls = review_pair_bidirectional(reviewer_client, candidate_a, candidate_b)
            for call in calls:
                usage = call.get("usage", {})
                usage_totals["prompt_tokens"] += usage.get("prompt_tokens", 0)
                usage_totals["completion_tokens"] += usage.get("completion_tokens", 0)
                usage_totals["total_tokens"] += usage.get("total_tokens", 0)
                usage_totals["num_calls"] += 1
            if regeneration_threshold is not None and summary["avg_detectability_penalty"] <= regeneration_threshold:
                continue
            feedback = [call["reason"] for call in calls if str(call.get("reason", "")).strip()]
            ranked_pairs.append(
                (
                    summary["avg_detectability_penalty"],
                    candidate_index,
                    feedback,
                    candidate_a,
                    candidate_b,
                )
            )
        ranked_pairs.sort(key=lambda item: item[0])
        for _, _, feedback, candidate_a, candidate_b in ranked_pairs[:regeneration_top_k]:
            _append_candidate_pair(
                candidate_a,
                candidate_b,
                next_candidate_index,
                temperature=max(0.4, base_temperature - 0.1),
                feedback=feedback,
                round_index=round_index,
            )
            next_candidate_index += 1

    return candidates_a, candidates_b, usage_totals


def prune_pair_candidates_with_reviewer(
    reviewer_client: APIJudgeClient,
    quartet_id: str,
    domain: str,
    verbalizer_id: str,
    candidate_map: dict[str, list[CandidateTrace]],
    acceptance_mode: str = "strict",
    max_pairs_per_answer_variant_after_prune: int | None = None,
    pair_prune_max_detectability: float | None = None,
) -> tuple[
    dict[str, list[CandidateTrace]],
    list[dict[str, Any]],
    dict[str, Any],
    Counter,
    dict[tuple[str, str], dict[str, Any]],
]:
    usage_totals = Counter()
    review_rows: list[dict[str, Any]] = []
    pruned_candidate_map: dict[str, list[CandidateTrace]] = {role: [] for role in ROLE_ORDER}
    pair_candidate_summaries: dict[str, list[dict[str, Any]]] = {}
    pair_review_cache: dict[tuple[str, str], dict[str, Any]] = {}
    pair_specs = [
        ("correct", "valid_correct", "invalid_correct"),
        ("swapped", "valid_swapped", "invalid_swapped"),
    ]

    for answer_variant, valid_role, invalid_role in pair_specs:
        valid_by_index = {
            int(candidate.metadata["benchmark_v3_candidate_index"]): candidate
            for candidate in candidate_map[valid_role]
        }
        invalid_by_index = {
            int(candidate.metadata["benchmark_v3_candidate_index"]): candidate
            for candidate in candidate_map[invalid_role]
        }
        shared_indexes = sorted(set(valid_by_index) & set(invalid_by_index))
        pair_summaries: list[dict[str, Any]] = []
        ranked_pairs: list[tuple[tuple[float, float, float, int], int, CandidateTrace, CandidateTrace]] = []
        for candidate_index in shared_indexes:
            valid_candidate = valid_by_index[candidate_index]
            invalid_candidate = invalid_by_index[candidate_index]
            summary, calls = review_pair_bidirectional(
                reviewer_client,
                valid_candidate,
                invalid_candidate,
            )
            pair_review_cache[(valid_candidate.candidate_id, invalid_candidate.candidate_id)] = {
                "summary": summary,
                "calls": calls,
            }
            for call in calls:
                usage = call.get("usage", {})
                usage_totals["prompt_tokens"] += usage.get("prompt_tokens", 0)
                usage_totals["completion_tokens"] += usage.get("completion_tokens", 0)
                usage_totals["total_tokens"] += usage.get("total_tokens", 0)
                usage_totals["num_calls"] += 1
                review_rows.append(
                    {
                        "review_stage": "pair_candidate_prune",
                        "quartet_id": quartet_id,
                        "domain": domain,
                        "verbalizer_id": verbalizer_id,
                        "answer_variant_group": answer_variant,
                        "candidate_index": candidate_index,
                        "valid_candidate_id": valid_candidate.candidate_id,
                        "invalid_candidate_id": invalid_candidate.candidate_id,
                        **call,
                    }
                )
            pair_summary = {
                "candidate_index": candidate_index,
                "valid_candidate_id": valid_candidate.candidate_id,
                "invalid_candidate_id": invalid_candidate.candidate_id,
                "avg_detectability_penalty": summary["avg_detectability_penalty"],
                "avg_detectability_penalty_selected_mode": summary["avg_detectability_penalty_by_mode"][acceptance_mode],
                "avg_detectability_penalty_by_mode": summary["avg_detectability_penalty_by_mode"],
                "invalid_pick_rate": summary["invalid_pick_rate"],
                "avg_confidence": summary["avg_confidence"],
                "review_buckets": summary["review_buckets"],
                "acceptance_mode": acceptance_mode,
                "eligible_under_threshold": pair_prune_max_detectability is None or summary["avg_detectability_penalty_by_mode"][acceptance_mode] <= pair_prune_max_detectability,
            }
            pair_summaries.append(pair_summary)
            rank_key = (
                summary["avg_detectability_penalty_by_mode"][acceptance_mode],
                summary["invalid_pick_rate"],
                summary["avg_confidence"],
                candidate_index,
            )
            ranked_pairs.append((rank_key, candidate_index, valid_candidate, invalid_candidate))
        ranked_pairs.sort(key=lambda item: item[0])
        filtered_pairs = [
            item
            for item in ranked_pairs
            if pair_prune_max_detectability is None or item[0][0] <= pair_prune_max_detectability
        ]
        if max_pairs_per_answer_variant_after_prune is not None:
            filtered_pairs = filtered_pairs[:max_pairs_per_answer_variant_after_prune]
        pruned_candidate_map[valid_role] = [item[2] for item in filtered_pairs]
        pruned_candidate_map[invalid_role] = [item[3] for item in filtered_pairs]
        pair_candidate_summaries[answer_variant] = pair_summaries

    summary = {
        "quartet_id": quartet_id,
        "domain": domain,
        "verbalizer_id": verbalizer_id,
        "acceptance_mode": acceptance_mode,
        "max_pairs_per_answer_variant_after_prune": max_pairs_per_answer_variant_after_prune,
        "pair_prune_max_detectability": pair_prune_max_detectability,
        "role_counts_after": {role: len(pruned_candidate_map[role]) for role in ROLE_ORDER},
        "pair_candidate_summaries": pair_candidate_summaries,
        "all_roles_survive": all(len(pruned_candidate_map[role]) > 0 for role in ROLE_ORDER),
    }
    return pruned_candidate_map, review_rows, summary, usage_totals, pair_review_cache


def enumerate_family_combinations(candidate_map: dict[str, list[CandidateTrace]]) -> list[dict[str, CandidateTrace]]:
    role_lists = [candidate_map[role] for role in ROLE_ORDER]
    families = []
    for combo in itertools.product(*role_lists):
        families.append({role: candidate for role, candidate in zip(ROLE_ORDER, combo, strict=True)})
    return families


def select_best_family(
    reviewer_client: APIJudgeClient,
    quartet_id: str,
    domain: str,
    verbalizer_id: str,
    candidate_map: dict[str, list[CandidateTrace]],
    acceptance_mode: str = "strict",
    max_pair_detectability: float | None = 0.8,
    allow_fallback_selection: bool = False,
    pair_review_cache: dict[tuple[str, str], dict[str, Any]] | None = None,
) -> tuple[dict[str, CandidateTrace] | None, dict[str, Any], list[dict[str, Any]], Counter]:
    best_eligible_family: dict[str, CandidateTrace] | None = None
    best_eligible_summary: dict[str, Any] | None = None
    best_eligible_reviews: list[dict[str, Any]] = []
    best_eligible_rank_key: tuple[float, float, float, float, float] | None = None
    best_overall_family: dict[str, CandidateTrace] | None = None
    best_overall_summary: dict[str, Any] | None = None
    best_overall_reviews: list[dict[str, Any]] = []
    best_overall_rank_key: tuple[float, float, float, float, float] | None = None
    usage_totals = Counter()
    family_count = 0
    eligible_count = 0
    for family_index, family in enumerate(enumerate_family_combinations(candidate_map), start=1):
        family_count += 1
        pair_payloads = []
        for valid_role, invalid_role in [("valid_correct", "invalid_correct"), ("valid_swapped", "invalid_swapped")]:
            valid_candidate = family[valid_role]
            invalid_candidate = family[invalid_role]
            cached_payload = None
            if pair_review_cache is not None:
                cached_payload = pair_review_cache.get((valid_candidate.candidate_id, invalid_candidate.candidate_id))
            if cached_payload is None:
                summary, calls = review_pair_bidirectional(
                    reviewer_client,
                    valid_candidate,
                    invalid_candidate,
                )
                for call in calls:
                    usage = call.get("usage", {})
                    usage_totals["prompt_tokens"] += usage.get("prompt_tokens", 0)
                    usage_totals["completion_tokens"] += usage.get("completion_tokens", 0)
                    usage_totals["total_tokens"] += usage.get("total_tokens", 0)
                    usage_totals["num_calls"] += 1
            else:
                summary = cached_payload["summary"]
                calls = cached_payload["calls"]
            pair_payloads.append((summary, calls))

        (correct_summary, correct_calls), (swapped_summary, swapped_calls) = pair_payloads
        pair_detectabilities = [
            correct_summary["avg_detectability_penalty_by_mode"][acceptance_mode],
            swapped_summary["avg_detectability_penalty_by_mode"][acceptance_mode],
        ]
        strict_pair_detectabilities = [
            correct_summary["avg_detectability_penalty"],
            swapped_summary["avg_detectability_penalty"],
        ]
        pair_invalid_pick_rates = [
            correct_summary["invalid_pick_rate"],
            swapped_summary["invalid_pick_rate"],
        ]
        pair_confidences = [
            correct_summary["avg_confidence"],
            swapped_summary["avg_confidence"],
        ]
        rank_key = (
            max(pair_detectabilities),
            sum(pair_detectabilities) / len(pair_detectabilities),
            max(pair_invalid_pick_rates),
            sum(pair_invalid_pick_rates) / len(pair_invalid_pick_rates),
            sum(pair_confidences) / len(pair_confidences),
        )
        eligible = max_pair_detectability is None or rank_key[0] <= max_pair_detectability
        if eligible:
            eligible_count += 1
        summary = {
            "quartet_id": quartet_id,
            "domain": domain,
            "verbalizer_id": verbalizer_id,
            "family_index": family_index,
            "acceptance_mode": acceptance_mode,
            "selection_rank_key": list(rank_key),
            "max_pair_detectability_threshold": max_pair_detectability,
            "eligible_under_threshold": eligible,
            "family_max_detectability": max(strict_pair_detectabilities),
            "family_mean_detectability": sum(strict_pair_detectabilities) / len(strict_pair_detectabilities),
            "family_max_detectability_selected_mode": rank_key[0],
            "family_mean_detectability_selected_mode": rank_key[1],
            "family_max_invalid_pick_rate": rank_key[2],
            "family_mean_invalid_pick_rate": rank_key[3],
            "family_mean_confidence": rank_key[4],
            "correct_pair": correct_summary,
            "swapped_pair": swapped_summary,
        }
        reviews = []
        for pair_name, calls in [("correct_pair", correct_calls), ("swapped_pair", swapped_calls)]:
            for call in calls:
                reviews.append(
                    {
                        "quartet_id": quartet_id,
                        "domain": domain,
                        "verbalizer_id": verbalizer_id,
                        "family_index": family_index,
                        "pair_name": pair_name,
                        **call,
                    }
                )
        if best_overall_rank_key is None or rank_key < best_overall_rank_key:
            best_overall_rank_key = rank_key
            best_overall_family = family
            best_overall_summary = summary
            best_overall_reviews = reviews
        if eligible and (best_eligible_rank_key is None or rank_key < best_eligible_rank_key):
            best_eligible_rank_key = rank_key
            best_eligible_family = family
            best_eligible_summary = summary
            best_eligible_reviews = reviews

    assert best_overall_summary is not None
    if best_eligible_family is not None and best_eligible_summary is not None:
        best_eligible_summary["selection_status"] = "selected_under_threshold"
        best_eligible_summary["num_families_evaluated"] = family_count
        best_eligible_summary["num_eligible_families"] = eligible_count
        return best_eligible_family, best_eligible_summary, best_eligible_reviews, usage_totals

    if allow_fallback_selection:
        assert best_overall_family is not None
        best_overall_summary["selection_status"] = "fallback_selected"
        best_overall_summary["num_families_evaluated"] = family_count
        best_overall_summary["num_eligible_families"] = eligible_count
        return best_overall_family, best_overall_summary, best_overall_reviews, usage_totals

    best_overall_summary["selection_status"] = "rejected_all_families"
    best_overall_summary["num_families_evaluated"] = family_count
    best_overall_summary["num_eligible_families"] = eligible_count
    return None, best_overall_summary, best_overall_reviews, usage_totals


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def candidate_from_record(row: dict[str, Any]) -> CandidateTrace:
    metadata = dict(row.get("metadata", {}))
    return CandidateTrace(
        candidate_id=row["trace_id"],
        source_trace_id=str(metadata.get("benchmark_v3_source_trace_id", row["trace_id"])),
        quartet_id=row["quartet_id"],
        domain=row["domain"],
        verbalizer_id=row["verbalizer_id"],
        counterfactual_role=row["counterfactual_role"],
        process_variant=row["process_variant"],
        answer_variant=row["answer_variant"],
        is_valid_process=bool(row["is_valid_process"]),
        answer_is_correct=bool(row["answer_is_correct"]),
        problem_text=row["problem_text"],
        step_texts=list(row["step_texts"]),
        final_answer_line=row["final_answer_line"],
        masked_answer_line=row["masked_answer_line"],
        trace_text=row["trace_text"],
        masked_trace_text=row["masked_trace_text"],
        metadata=metadata,
    )
