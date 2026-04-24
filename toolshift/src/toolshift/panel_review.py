from __future__ import annotations

from typing import Any


_FAMILY_METRIC_ALIASES: dict[str, str] = {
    "CAA_overall": "CAA",
}


def extract_method_metrics(summary_payload: dict[str, Any], *, method: str, regime: str | None = None) -> dict[str, float | None]:
    if regime is None:
        return dict(summary_payload["methods"][method]["aggregate"]["metrics_mean"])
    return dict(summary_payload[regime][method]["aggregate"]["metrics_mean"])


def extract_blind_family_metrics(summary_payload: dict[str, Any], *, method: str) -> dict[str, dict[str, float | int | None]]:
    return {
        family_id: dict(metrics)
        for family_id, metrics in summary_payload["methods"][method]["aggregate"]["family_metrics_mean"].items()
    }


def compute_metric_deltas(
    baseline: dict[str, float | None],
    target: dict[str, float | None],
    *,
    metric_names: tuple[str, ...],
) -> dict[str, float | None]:
    deltas: dict[str, float | None] = {}
    for metric_name in metric_names:
        left = baseline.get(metric_name)
        right = target.get(metric_name)
        if left is None or right is None:
            deltas[metric_name] = None
        else:
            deltas[metric_name] = float(right) - float(left)
    return deltas


def lowest_family_by_metric(
    family_metrics: dict[str, dict[str, float | int | None]],
    metric_name: str,
) -> tuple[str, float] | None:
    resolved_metric = _FAMILY_METRIC_ALIASES.get(metric_name, metric_name)
    ranked = [
        (family_id, float(metrics[resolved_metric]))
        for family_id, metrics in family_metrics.items()
        if metrics.get(resolved_metric) is not None
    ]
    if not ranked:
        return None
    ranked.sort(key=lambda item: item[1])
    return ranked[0]
