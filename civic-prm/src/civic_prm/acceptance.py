from __future__ import annotations

from typing import Any


ACCEPTANCE_MODES = (
    "strict",
    "ignore_semantic_only",
    "surface_or_mixed_only",
)


ARTIFACT_FEEDBACK_HINTS = {
    "templated",
    "template",
    "patched",
    "patch",
    "copy",
    "copied",
    "near-copy",
    "shell",
    "scaffold",
    "scaffolded",
    "phrasing",
    "wording",
    "style",
    "surface",
    "polished",
    "compressed",
    "asymmetry",
    "asymmetric",
    "marker",
    "markers",
    "discourse",
}

SEMANTIC_FEEDBACK_HINTS = {
    "arithmetic",
    "equation",
    "calculation",
    "math",
    "incorrect",
    "inconsistent",
    "wrong",
    "illegal",
    "route",
    "path",
    "total",
    "state",
    "move",
    "moves",
    "movement",
    "forced",
    "sequence",
    "flow",
    "order",
    "intermediate",
    "direct",
    "efficient",
    "systematic",
    "table",
    "clearing",
    "linear",
    "methodical",
    "repetitive",
    "unnecessary",
    "steps",
}


def classify_feedback_reason(reason: str) -> str:
    lowered = reason.strip().lower()
    has_artifact_hint = any(hint in lowered for hint in ARTIFACT_FEEDBACK_HINTS)
    has_semantic_hint = any(hint in lowered for hint in SEMANTIC_FEEDBACK_HINTS)
    if has_artifact_hint and has_semantic_hint:
        return "mixed"
    if has_artifact_hint:
        return "surface_only"
    if has_semantic_hint:
        return "semantic_only"
    return "other"


def filter_surface_feedback(feedback: list[str]) -> list[str]:
    kept: list[str] = []
    for item in feedback:
        normalized = item.strip()
        if not normalized:
            continue
        bucket = classify_feedback_reason(normalized)
        if bucket != "semantic_only":
            kept.append(normalized)
    return kept[:4]


def detectability_penalty(label: str, confidence: int) -> float:
    if label == "neither":
        return 0.0
    if label == "both":
        return 0.5
    return 0.5 + 0.1 * confidence


def acceptance_penalty(bucket: str, label: str, confidence: int, mode: str) -> float:
    penalty = detectability_penalty(label, confidence)
    if mode == "strict":
        return penalty
    if mode == "ignore_semantic_only":
        return 0.0 if bucket == "semantic_only" else penalty
    if mode == "surface_or_mixed_only":
        return penalty if bucket in {"surface_only", "mixed"} else 0.0
    raise ValueError(f"unknown acceptance mode: {mode}")


def summarize_pair_calls(calls: list[dict[str, Any]], mode: str = "strict") -> dict[str, Any]:
    buckets = [classify_feedback_reason(str(call.get("reason", ""))) for call in calls]
    penalties = [
        acceptance_penalty(bucket, str(call.get("label", "")), int(call.get("confidence", 0)), mode)
        for bucket, call in zip(buckets, calls, strict=True)
    ]
    invalid_pick_rate = sum(1 for call in calls if call.get("picked_invalid")) / len(calls)
    return {
        "avg_detectability_penalty": sum(penalties) / len(penalties),
        "invalid_pick_rate": invalid_pick_rate,
        "avg_confidence": sum(int(call.get("confidence", 0)) for call in calls) / len(calls),
        "review_buckets": buckets,
    }
