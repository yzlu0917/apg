from __future__ import annotations

import json
from collections import Counter, defaultdict
from statistics import mean
from statistics import pstdev
from typing import Any

from .benchmark import BenchmarkSuite
from .diagnostics import classify_serialized_record
from .schema import ControlTag, ShiftKind, SplitTag


def build_view_metadata(suite: BenchmarkSuite) -> dict[str, dict[str, str | None]]:
    metadata: dict[str, dict[str, str | None]] = {}
    for example in suite.examples:
        metadata[example.schema_view.view_id] = {
            "case_id": example.case.case_id,
            "family_tag": example.case.family_tag or "none",
            "primary_tool_id": example.case.primary_action.tool_id or "none",
            "transform_name": example.schema_view.transform_name,
            "shift_kind": example.schema_view.shift_kind.value,
            "split_tag": example.split_tag.value,
        }
    return metadata


def flatten_method_records(
    payload: dict[str, Any],
    *,
    regime: str,
    method: str,
    view_metadata: dict[str, dict[str, str | None]],
) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []
    for seed_name, records in sorted(payload[regime][method].items()):
        for record in records:
            meta = view_metadata.get(record["view_id"])
            if meta is None:
                raise KeyError(f"Missing benchmark metadata for view_id={record['view_id']}")
            annotated = dict(record)
            annotated["seed"] = seed_name
            annotated["family_tag"] = meta["family_tag"]
            annotated["primary_tool_id"] = meta["primary_tool_id"]
            diagnosis = classify_serialized_record(record)
            annotated["bucket"] = diagnosis["bucket"]
            annotated["group"] = diagnosis["group"]
            annotated["predicted_control"] = diagnosis["predicted_control"]
            annotated["expected_controls"] = diagnosis["expected_controls"]
            annotated["expected_execute"] = diagnosis["expected_execute"]
            flattened.append(annotated)
    return [
        record
        for record in flattened
        if record["split_tag"] == SplitTag.UNAMBIGUOUS_CORE.value and record["shift_kind"] != ShiftKind.IMPOSSIBLE.value
    ]


def summarize_method_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = _compute_metrics(records)
    summary = {
        "count": len(records),
        "unique_views": len({record["view_id"] for record in records}),
        "unique_cases": len({record["case_id"] for record in records}),
        "seeds": sorted({record["seed"] for record in records}),
        "metrics": metrics,
        "group_counts": dict(Counter(record["group"] for record in records)),
        "bucket_counts": dict(Counter(record["bucket"] for record in records)),
        "control_distribution": dict(Counter(record["predicted_control"] for record in records)),
        "by_transform": _group_summaries(records, "transform_name"),
        "by_shift_kind": _group_summaries(records, "shift_kind"),
        "by_family_tag": _group_summaries(records, "family_tag"),
        "by_primary_tool_id": _group_summaries(records, "primary_tool_id"),
    }
    return summary


def summarize_seeds(records: list[dict[str, Any]]) -> dict[str, Any]:
    per_seed = {
        seed_name: summarize_method_records([record for record in records if record["seed"] == seed_name])
        for seed_name in sorted({record["seed"] for record in records})
    }
    metric_names = sorted(per_seed[next(iter(per_seed))]["metrics"]) if per_seed else []
    metrics_mean = {}
    metrics_std = {}
    for metric_name in metric_names:
        values = [per_seed[seed_name]["metrics"][metric_name] for seed_name in per_seed]
        if any(value is None for value in values):
            metrics_mean[metric_name] = None
            metrics_std[metric_name] = None
            continue
        numeric = [float(value) for value in values]
        metrics_mean[metric_name] = mean(numeric)
        metrics_std[metric_name] = pstdev(numeric) if len(numeric) > 1 else 0.0
    return {
        "per_seed": per_seed,
        "aggregate": summarize_method_records(records),
        "metrics_mean": metrics_mean,
        "metrics_std": metrics_std,
    }


def compare_methods(
    baseline_records: list[dict[str, Any]],
    candidate_records: list[dict[str, Any]],
) -> dict[str, Any]:
    baseline_by_key = {(record["seed"], record["view_id"]): record for record in baseline_records}
    candidate_by_key = {(record["seed"], record["view_id"]): record for record in candidate_records}
    shared_keys = sorted(set(baseline_by_key) & set(candidate_by_key))

    improvements: list[dict[str, Any]] = []
    regressions: list[dict[str, Any]] = []
    unchanged_correct = 0
    unchanged_incorrect = 0

    for key in shared_keys:
        baseline = baseline_by_key[key]
        candidate = candidate_by_key[key]
        if not baseline["admissible"] and candidate["admissible"]:
            improvements.append(_transition_entry(baseline, candidate))
        elif baseline["admissible"] and not candidate["admissible"]:
            regressions.append(_transition_entry(baseline, candidate))
        elif baseline["admissible"] and candidate["admissible"]:
            unchanged_correct += 1
        else:
            unchanged_incorrect += 1

    return {
        "paired_count": len(shared_keys),
        "improved_pair_count": len(improvements),
        "regressed_pair_count": len(regressions),
        "unchanged_correct_pair_count": unchanged_correct,
        "unchanged_incorrect_pair_count": unchanged_incorrect,
        "improved_distinct_views": len({entry["view_id"] for entry in improvements}),
        "regressed_distinct_views": len({entry["view_id"] for entry in regressions}),
        "delta_metrics": _delta_metrics(
            summarize_method_records(candidate_records)["metrics"],
            summarize_method_records(baseline_records)["metrics"],
        ),
        "improvements": _transition_summary(improvements),
        "regressions": _transition_summary(regressions),
        "strictly_fixed_views": _strict_transition_views(shared_keys, baseline_by_key, candidate_by_key, want="improvement"),
        "strictly_regressed_views": _strict_transition_views(shared_keys, baseline_by_key, candidate_by_key, want="regression"),
    }


def render_markdown(
    *,
    records_path: str,
    benchmark_path: str,
    regime: str,
    methods: list[str],
    method_summaries: dict[str, dict[str, Any]],
    comparisons: dict[str, dict[str, Any]],
) -> str:
    lines = [
        "# Fixed Panel Method Comparison",
        "",
        f"- Records: `{records_path}`",
        f"- Benchmark: `{benchmark_path}`",
        f"- Regime: `{regime}`",
        f"- Methods: `{', '.join(methods)}`",
        "",
        "## Overall Metrics",
        "",
        "| method | CAA | CAA+ | NOS | POC | coverage | selective_risk | contract_validity |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for method in methods:
        metrics = method_summaries[method]["metrics_mean"]
        lines.append(
            "| "
            + " | ".join(
                [
                    method,
                    _fmt(metrics["CAA_overall"]),
                    _fmt(metrics["CAA_positive"]),
                    _fmt(metrics["NOS"]),
                    _fmt(metrics["POC"]),
                    _fmt(metrics["coverage"]),
                    _fmt(metrics["selective_risk"]),
                    _fmt(metrics["contract_validity"]),
                ]
            )
            + " |"
        )

    for comparison_name, comparison in comparisons.items():
        lines.extend(
            [
                "",
                f"## {comparison_name}",
                "",
                f"- improved_pair_count: `{comparison['improved_pair_count']}`",
                f"- regressed_pair_count: `{comparison['regressed_pair_count']}`",
                f"- improved_distinct_views: `{comparison['improved_distinct_views']}`",
                f"- regressed_distinct_views: `{comparison['regressed_distinct_views']}`",
                f"- strictly_fixed_views: `{json.dumps(comparison['strictly_fixed_views'], ensure_ascii=False)}`",
                "",
                "### Delta Metrics",
                "",
            ]
        )
        for metric_name, value in comparison["delta_metrics"].items():
            lines.append(f"- {metric_name}: `{_fmt(value)}`")
        lines.extend(
            [
                "",
                "### Incremental Fixes",
                "",
                f"- by_transform: `{json.dumps(comparison['improvements']['by_transform'], ensure_ascii=False, sort_keys=True)}`",
                f"- by_family_tag: `{json.dumps(comparison['improvements']['by_family_tag'], ensure_ascii=False, sort_keys=True)}`",
                f"- by_primary_tool_id: `{json.dumps(comparison['improvements']['by_primary_tool_id'], ensure_ascii=False, sort_keys=True)}`",
                f"- from_group: `{json.dumps(comparison['improvements']['from_group'], ensure_ascii=False, sort_keys=True)}`",
                f"- from_bucket: `{json.dumps(comparison['improvements']['from_bucket'], ensure_ascii=False, sort_keys=True)}`",
                "",
                "### Regressions",
                "",
                f"- by_transform: `{json.dumps(comparison['regressions']['by_transform'], ensure_ascii=False, sort_keys=True)}`",
                f"- by_family_tag: `{json.dumps(comparison['regressions']['by_family_tag'], ensure_ascii=False, sort_keys=True)}`",
                f"- from_bucket: `{json.dumps(comparison['regressions']['from_bucket'], ensure_ascii=False, sort_keys=True)}`",
                "",
                "### Representative Fixes",
                "",
            ]
        )
        representatives = comparison["improvements"]["examples"][:10]
        if representatives:
            for entry in representatives:
                lines.append(
                    "- "
                    f"`{entry['view_id']}` "
                    f"({entry['family_tag']} / {entry['transform_name']} / {entry['primary_tool_id']}): "
                    f"`{entry['baseline_bucket']} -> {entry['candidate_bucket']}`"
                )
        else:
            lines.append("- none")

    lines.extend(["", "## By Family", ""])
    for method in methods:
        lines.append(f"### {method}")
        lines.append("")
        for family_tag, family_summary in sorted(method_summaries[method]["aggregate"]["by_family_tag"].items()):
            metrics = family_summary["metrics"]
            lines.append(
                "- "
                f"`{family_tag}`: "
                f"`CAA={_fmt(metrics['CAA_overall'])}` "
                f"`CAA+={_fmt(metrics['CAA_positive'])}` "
                f"`NOS={_fmt(metrics['NOS'])}` "
                f"`count={family_summary['count']}`"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _group_summaries(records: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[str(record.get(key, "none"))].append(record)
    return {
        group_name: {
            "count": len(group_records),
            "unique_views": len({record["view_id"] for record in group_records}),
            "metrics": _compute_metrics(group_records),
            "group_counts": dict(Counter(record["group"] for record in group_records)),
            "bucket_counts": dict(Counter(record["bucket"] for record in group_records)),
        }
        for group_name, group_records in sorted(grouped.items())
    }


def _compute_metrics(records: list[dict[str, Any]]) -> dict[str, float | None]:
    positive_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if record["shift_kind"] == ShiftKind.POSITIVE_ORBIT.value:
            positive_groups[(record["seed"], record["case_id"])].append(record)

    poc_values = []
    for case_records in positive_groups.values():
        fingerprints = {_action_fingerprint(record["predicted_action"]) for record in case_records}
        poc_values.append(1.0 if all(record["admissible"] for record in case_records) and len(fingerprints) == 1 else 0.0)

    covered = [record for record in records if record["predicted_action"]["control"] != ControlTag.ABSTAIN.value]
    return {
        "CAA_overall": _mean_or_none(record["admissible"] for record in records),
        "CAA_clean": _mean_or_none(record["admissible"] for record in records if record["shift_kind"] == ShiftKind.CLEAN.value),
        "CAA_positive": _mean_or_none(record["admissible"] for record in records if record["shift_kind"] == ShiftKind.POSITIVE_ORBIT.value),
        "CAA_negative": _mean_or_none(record["admissible"] for record in records if record["shift_kind"] == ShiftKind.NEGATIVE_NEAR_ORBIT.value),
        "POC": _mean_or_none(poc_values),
        "NOS": _mean_or_none(record["admissible"] for record in records if record["shift_kind"] == ShiftKind.NEGATIVE_NEAR_ORBIT.value),
        "coverage": _mean_or_none(record["predicted_action"]["control"] != ControlTag.ABSTAIN.value for record in records),
        "negative_coverage": _mean_or_none(
            record["predicted_action"]["control"] != ControlTag.ABSTAIN.value
            for record in records
            if record["shift_kind"] == ShiftKind.NEGATIVE_NEAR_ORBIT.value
        ),
        "selective_risk": 0.0 if not covered else 1.0 - _mean(record["admissible"] for record in covered),
        "contract_validity": _mean_or_none(record["contract_ok"] for record in records),
    }


def _transition_entry(baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "seed": baseline["seed"],
        "case_id": baseline["case_id"],
        "view_id": baseline["view_id"],
        "transform_name": baseline["transform_name"],
        "shift_kind": baseline["shift_kind"],
        "family_tag": baseline["family_tag"],
        "primary_tool_id": baseline["primary_tool_id"],
        "baseline_bucket": baseline["bucket"],
        "baseline_group": baseline["group"],
        "baseline_control": baseline["predicted_control"],
        "candidate_bucket": candidate["bucket"],
        "candidate_group": candidate["group"],
        "candidate_control": candidate["predicted_control"],
    }


def _transition_summary(entries: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "count": len(entries),
        "by_transform": dict(Counter(entry["transform_name"] for entry in entries)),
        "by_shift_kind": dict(Counter(entry["shift_kind"] for entry in entries)),
        "by_family_tag": dict(Counter(entry["family_tag"] for entry in entries)),
        "by_primary_tool_id": dict(Counter(entry["primary_tool_id"] for entry in entries)),
        "from_group": dict(Counter(entry["baseline_group"] for entry in entries)),
        "from_bucket": dict(Counter(entry["baseline_bucket"] for entry in entries)),
        "to_bucket": dict(Counter(entry["candidate_bucket"] for entry in entries)),
        "examples": sorted(
            entries,
            key=lambda entry: (
                entry["family_tag"],
                entry["transform_name"],
                entry["primary_tool_id"],
                entry["view_id"],
                entry["seed"],
            ),
        ),
    }


def _strict_transition_views(
    shared_keys: list[tuple[str, str]],
    baseline_by_key: dict[tuple[str, str], dict[str, Any]],
    candidate_by_key: dict[tuple[str, str], dict[str, Any]],
    *,
    want: str,
) -> list[str]:
    view_pairs: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = defaultdict(list)
    for key in shared_keys:
        view_pairs[key[1]].append((baseline_by_key[key], candidate_by_key[key]))

    selected = []
    for view_id, pairs in sorted(view_pairs.items()):
        if want == "improvement":
            if all(candidate["admissible"] for _, candidate in pairs) and any(not baseline["admissible"] for baseline, _ in pairs):
                selected.append(view_id)
        else:
            if all(baseline["admissible"] for baseline, _ in pairs) and any(not candidate["admissible"] for _, candidate in pairs):
                selected.append(view_id)
    return selected


def _delta_metrics(candidate_metrics: dict[str, float | None], baseline_metrics: dict[str, float | None]) -> dict[str, float | None]:
    deltas = {}
    for metric_name in sorted(candidate_metrics):
        candidate_value = candidate_metrics[metric_name]
        baseline_value = baseline_metrics[metric_name]
        if candidate_value is None or baseline_value is None:
            deltas[metric_name] = None
        else:
            deltas[metric_name] = candidate_value - baseline_value
    return deltas


def _action_fingerprint(action: dict[str, Any]) -> str:
    return json.dumps(action, sort_keys=True, ensure_ascii=False)


def _mean(values) -> float:
    items = list(values)
    if not items:
        return 0.0
    return sum(float(item) for item in items) / len(items)


def _mean_or_none(values) -> float | None:
    items = list(values)
    if not items:
        return None
    return _mean(items)


def _fmt(value: float | None) -> str:
    if value is None:
        return "na"
    return f"{value:.3f}"
