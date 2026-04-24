from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

from civic_prm.baselines import compute_verifier_metrics
from civic_prm.downstream import compute_selection_metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize benchmark-v3 seed stability for frozen-head baselines and bootstrap the visible-vs-masked reranker gap."
    )
    parser.add_argument(
        "--baseline-artifacts",
        type=Path,
        nargs="+",
        required=True,
    )
    parser.add_argument(
        "--reranker-artifact",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
    )
    parser.add_argument("--bootstrap-samples", type=int, default=2000)
    parser.add_argument("--bootstrap-seed", type=int, default=123)
    return parser.parse_args()


def _sanitize_utility(metrics: dict) -> dict:
    return {key: value for key, value in metrics.items() if key != "quartet_rows"}


def _round_nested(value):
    if isinstance(value, float):
        return round(value, 4)
    if isinstance(value, dict):
        return {key: _round_nested(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_round_nested(item) for item in value]
    return value


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


def _std(values: list[float]) -> float:
    if len(values) <= 1:
        return 0.0
    mean_value = _mean(values)
    variance = sum((value - mean_value) ** 2 for value in values) / len(values)
    return math.sqrt(variance)


def _aggregate_dicts(dicts: list[dict], reducer) -> dict:
    keys = set()
    for item in dicts:
        keys.update(item.keys())
    result = {}
    for key in keys:
        values = [item[key] for item in dicts if key in item]
        if not values:
            continue
        first = values[0]
        if isinstance(first, dict):
            result[key] = _aggregate_dicts(values, reducer)
        else:
            result[key] = reducer(values)
    return result


def _metric_value(rows: list[dict], metric_name: str) -> float:
    if metric_name in {"ordinary_auroc", "amcd", "ass_total"}:
        return compute_verifier_metrics(rows)[metric_name]
    utility = compute_selection_metrics(rows)
    return utility[metric_name]


def _paired_bootstrap(
    rows_a: list[dict],
    rows_b: list[dict],
    metric_name: str,
    num_samples: int,
    seed: int,
) -> dict:
    grouped_a = {}
    grouped_b = {}
    for row in rows_a:
        grouped_a.setdefault(row["quartet_id"], []).append(row)
    for row in rows_b:
        grouped_b.setdefault(row["quartet_id"], []).append(row)
    quartet_ids = sorted(set(grouped_a) & set(grouped_b))
    rng = random.Random(seed)
    diffs = []
    for _ in range(num_samples):
        sampled_ids = [rng.choice(quartet_ids) for _ in quartet_ids]
        sampled_a = []
        sampled_b = []
        for quartet_id in sampled_ids:
            sampled_a.extend(grouped_a[quartet_id])
            sampled_b.extend(grouped_b[quartet_id])
        diffs.append(_metric_value(sampled_a, metric_name) - _metric_value(sampled_b, metric_name))
    diffs.sort()
    low_index = int(0.025 * len(diffs))
    high_index = int(0.975 * len(diffs))
    observed = _metric_value(rows_a, metric_name) - _metric_value(rows_b, metric_name)
    return {
        "metric": metric_name,
        "observed_diff": round(observed, 4),
        "ci_low": round(diffs[low_index], 4),
        "ci_high": round(diffs[min(high_index, len(diffs) - 1)], 4),
        "bootstrap_win_rate": round(sum(diff > 0 for diff in diffs) / len(diffs), 4),
    }


def _baseline_protocol_summary(artifacts: list[dict], protocol_name: str) -> dict:
    baseline_names = list(artifacts[0]["protocols"][protocol_name]["baselines"].keys())
    summary = {}
    for baseline_name in baseline_names:
        metric_rows = []
        for artifact in artifacts:
            payload = artifact["protocols"][protocol_name]["baselines"][baseline_name]
            metrics = dict(payload["metrics"])
            if "test_rows" in payload:
                metrics.update(_sanitize_utility(compute_selection_metrics(payload["test_rows"])))
            metric_rows.append(metrics)
        summary[baseline_name] = {
            "seed_metrics": [
                {
                    "seed": artifact["config"]["seed"],
                    "metrics": _round_nested(metric_row),
                }
                for artifact, metric_row in zip(artifacts, metric_rows)
            ],
            "mean_metrics": _round_nested(_aggregate_dicts(metric_rows, _mean)),
            "std_metrics": _round_nested(_aggregate_dicts(metric_rows, _std)),
        }
    return summary


def main() -> None:
    args = parse_args()
    baseline_artifacts = [
        json.loads(path.read_text(encoding="utf-8")) for path in args.baseline_artifacts
    ]
    reranker_artifact = json.loads(args.reranker_artifact.read_text(encoding="utf-8"))

    reranker_visible = reranker_artifact["views"]["visible"]["rows"]
    reranker_masked = reranker_artifact["views"]["masked"]["rows"]

    paired_bootstrap = {}
    for metric_name in [
        "ordinary_auroc",
        "amcd",
        "ass_total",
        "selection_gain_at4",
        "exploitability_rate",
    ]:
        paired_bootstrap[metric_name] = _paired_bootstrap(
            reranker_masked,
            reranker_visible,
            metric_name=metric_name,
            num_samples=args.bootstrap_samples,
            seed=args.bootstrap_seed,
        )

    output = {
        "config": {
            "baseline_artifacts": [str(path) for path in args.baseline_artifacts],
            "reranker_artifact": str(args.reranker_artifact),
            "bootstrap_samples": args.bootstrap_samples,
            "bootstrap_seed": args.bootstrap_seed,
        },
        "baseline_seed_summary": {
            "quartet": _baseline_protocol_summary(baseline_artifacts, "quartet"),
            "verbalizer_holdout": _baseline_protocol_summary(baseline_artifacts, "verbalizer_holdout"),
        },
        "reranker_same_dataset_summary": {
            "visible": _round_nested(
                {
                    **compute_verifier_metrics(reranker_visible),
                    **_sanitize_utility(compute_selection_metrics(reranker_visible)),
                }
            ),
            "masked": _round_nested(
                {
                    **compute_verifier_metrics(reranker_masked),
                    **_sanitize_utility(compute_selection_metrics(reranker_masked)),
                }
            ),
        },
        "paired_bootstrap_reranker_masked_vs_visible": paired_bootstrap,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(_round_nested(output), indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "quartet_visible_bce_mean_amcd": output["baseline_seed_summary"]["quartet"]["visible_bce"]["mean_metrics"]["amcd"],
                "quartet_masked_bce_mean_amcd": output["baseline_seed_summary"]["quartet"]["masked_bce"]["mean_metrics"]["amcd"],
                "reranker_masked_minus_visible_amcd_diff": output["paired_bootstrap_reranker_masked_vs_visible"]["amcd"]["observed_diff"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
