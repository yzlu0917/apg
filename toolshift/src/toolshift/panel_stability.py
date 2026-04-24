from __future__ import annotations

import random
from collections import defaultdict
from statistics import mean
from typing import Any

from .benchmark import BenchmarkSuite
from .eval import EvalRecord, summarize_records
from .reliability import build_case_vendor_map

BOOTSTRAP_METRICS = ("CAA_overall", "CAA_clean", "CAA_positive", "NOS", "POC", "coverage")


def build_case_group_maps(payload: dict[str, Any]) -> dict[str, dict[str, str]]:
    case_to_family = {case["case_id"]: case.get("family_tag") or "unknown" for case in payload["cases"]}
    case_to_vendor = build_case_vendor_map(payload)
    return {
        "family": case_to_family,
        "vendor": case_to_vendor,
    }


def summarize_seed_records(records: list[EvalRecord], suite: BenchmarkSuite) -> dict[str, float | None]:
    return summarize_records(records, suite.tool_lookup)["metrics"]


def aggregate_seed_metrics(seed_records: dict[str, list[EvalRecord]], suite: BenchmarkSuite) -> dict[str, float | None]:
    metric_dicts = [summarize_seed_records(records, suite) for records in seed_records.values()]
    return _mean_metric_dicts(metric_dicts)


def cluster_bootstrap_metrics(
    seed_records: dict[str, list[EvalRecord]],
    suite: BenchmarkSuite,
    *,
    case_to_group: dict[str, str],
    replicates: int,
    seed: int,
) -> dict[str, dict[str, float | None]]:
    rng = random.Random(seed)
    grouped_seed_records = {
        seed_name: _group_records_by(case_records, case_to_group)
        for seed_name, case_records in seed_records.items()
    }
    groups = sorted({group for group in case_to_group.values()})
    metric_samples: dict[str, list[float]] = defaultdict(list)
    for _ in range(replicates):
        sampled_groups = [rng.choice(groups) for _ in groups]
        metric_dicts = []
        for seed_name, by_group in grouped_seed_records.items():
            sampled_records: list[EvalRecord] = []
            for group in sampled_groups:
                sampled_records.extend(by_group[group])
            metric_dicts.append(summarize_seed_records(sampled_records, suite))
        aggregate = _mean_metric_dicts(metric_dicts)
        for metric_name in BOOTSTRAP_METRICS:
            value = aggregate.get(metric_name)
            if value is not None:
                metric_samples[metric_name].append(float(value))
    return {
        metric_name: {
            "mean": mean(values) if values else None,
            "lo": _quantile(values, 0.025),
            "hi": _quantile(values, 0.975),
        }
        for metric_name, values in metric_samples.items()
    }


def leave_one_group_out_metrics(
    seed_records: dict[str, list[EvalRecord]],
    suite: BenchmarkSuite,
    *,
    case_to_group: dict[str, str],
) -> dict[str, dict[str, float | None]]:
    groups = sorted({group for group in case_to_group.values()})
    result: dict[str, dict[str, float | None]] = {}
    for group in groups:
        metric_dicts = []
        for records in seed_records.values():
            retained = [record for record in records if case_to_group[record.case_id] != group]
            metric_dicts.append(summarize_seed_records(retained, suite))
        result[group] = _mean_metric_dicts(metric_dicts)
    return result


def lowest_group_by_metric(
    leave_one_group_metrics: dict[str, dict[str, float | None]],
    metric_name: str,
) -> tuple[str, float] | None:
    ranked = [
        (group, float(metrics[metric_name]))
        for group, metrics in leave_one_group_metrics.items()
        if metrics.get(metric_name) is not None
    ]
    if not ranked:
        return None
    ranked.sort(key=lambda item: item[1])
    return ranked[0]


def _group_records_by(records: list[EvalRecord], case_to_group: dict[str, str]) -> dict[str, list[EvalRecord]]:
    grouped: dict[str, list[EvalRecord]] = defaultdict(list)
    for record in records:
        grouped[case_to_group[record.case_id]].append(record)
    return grouped


def _mean_metric_dicts(metric_dicts: list[dict[str, float | None]]) -> dict[str, float | None]:
    keys = metric_dicts[0].keys()
    aggregate: dict[str, float | None] = {}
    for key in keys:
        values = [metric_dict[key] for metric_dict in metric_dicts]
        if any(value is None for value in values):
            aggregate[key] = None
        else:
            aggregate[key] = sum(float(value) for value in values) / len(values)
    return aggregate


def _quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ranked = sorted(values)
    if len(ranked) == 1:
        return ranked[0]
    position = q * (len(ranked) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ranked) - 1)
    if lower == upper:
        return ranked[lower]
    weight = position - lower
    return ranked[lower] * (1.0 - weight) + ranked[upper] * weight
