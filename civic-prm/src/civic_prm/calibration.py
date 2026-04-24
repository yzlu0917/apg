from __future__ import annotations

import math


def brier_score(labels: list[int], scores: list[float]) -> float:
    if not labels:
        return math.nan
    return sum((score - label) ** 2 for label, score in zip(labels, scores, strict=True)) / len(labels)


def expected_calibration_error(labels: list[int], scores: list[float], num_bins: int = 10) -> float:
    if not labels:
        return math.nan
    total = len(labels)
    error = 0.0
    for bin_index in range(num_bins):
        lower = bin_index / num_bins
        upper = (bin_index + 1) / num_bins
        def in_bucket(score: float) -> bool:
            if bin_index == num_bins - 1:
                return lower <= score <= upper
            return lower <= score < upper

        bucket = [
            (label, score)
            for label, score in zip(labels, scores, strict=True)
            if in_bucket(score)
        ]
        if not bucket:
            continue
        avg_label = sum(label for label, _ in bucket) / len(bucket)
        avg_score = sum(score for _, score in bucket) / len(bucket)
        error += abs(avg_label - avg_score) * (len(bucket) / total)
    return error


def area_under_risk_coverage(labels: list[int], scores: list[float]) -> float:
    if not labels:
        return math.nan
    confidences = [max(score, 1.0 - score) for score in scores]
    correctness = [int((score >= 0.5) == bool(label)) for label, score in zip(labels, scores, strict=True)]
    ordered = sorted(zip(confidences, correctness, strict=True), key=lambda item: item[0], reverse=True)
    cumulative_errors = 0.0
    risks = []
    for rank, (_, is_correct) in enumerate(ordered, start=1):
        cumulative_errors += 1.0 - is_correct
        risks.append(cumulative_errors / rank)
    return sum(risks) / len(risks)


def negative_log_likelihood(labels: list[int], scores: list[float]) -> float:
    if not labels:
        return math.nan
    eps = 1e-6
    return -sum(
        label * math.log(max(score, eps)) + (1 - label) * math.log(max(1.0 - score, eps))
        for label, score in zip(labels, scores, strict=True)
    ) / len(labels)


def compute_calibration_metrics(rows: list[dict], num_bins: int = 10) -> dict:
    labels = [row["gold_valid"] for row in rows]
    scores = [row["score"] for row in rows]
    if not rows:
        return {
            "num_scored_traces": 0,
            "brier": math.nan,
            "ece": math.nan,
            "aurc": math.nan,
            "nll": math.nan,
            "by_domain": {},
        }

    by_domain = {}
    for domain in sorted({row["domain"] for row in rows}):
        domain_rows = [row for row in rows if row["domain"] == domain]
        domain_labels = [row["gold_valid"] for row in domain_rows]
        domain_scores = [row["score"] for row in domain_rows]
        by_domain[domain] = {
            "brier": round(brier_score(domain_labels, domain_scores), 4),
            "ece": round(expected_calibration_error(domain_labels, domain_scores, num_bins=num_bins), 4),
            "aurc": round(area_under_risk_coverage(domain_labels, domain_scores), 4),
            "nll": round(negative_log_likelihood(domain_labels, domain_scores), 4),
        }

    return {
        "num_scored_traces": len(rows),
        "brier": round(brier_score(labels, scores), 4),
        "ece": round(expected_calibration_error(labels, scores, num_bins=num_bins), 4),
        "aurc": round(area_under_risk_coverage(labels, scores), 4),
        "nll": round(negative_log_likelihood(labels, scores), 4),
        "by_domain": by_domain,
    }
