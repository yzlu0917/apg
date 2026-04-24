from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate ProcessBench trace/prefix baselines and reranker results into a paper-facing main table."
    )
    parser.add_argument(
        "--frozen-artifact",
        type=Path,
        default=Path("artifacts/external_datasets/processbench_frozen_baselines.json"),
    )
    parser.add_argument(
        "--reranker-artifact",
        type=Path,
        default=Path("artifacts/external_datasets/processbench_reranker_8b.json"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("artifacts/external_datasets/processbench_main_table.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("artifacts/external_datasets/processbench_main_table.md"),
    )
    return parser.parse_args()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _freeze_trace_rows(frozen: dict) -> list[dict]:
    rows = []
    for view_name in ["visible", "masked", "step_only"]:
        metrics = frozen["trace"][view_name]["metrics"]
        rows.append(
            {
                "model": f"frozen_{view_name}",
                "family": "frozen",
                "task": "PB-Trace",
                "ordinary_accuracy": metrics["ordinary_accuracy"],
                "ordinary_auroc": metrics["ordinary_auroc"],
                "invalid_answer_gap": metrics["invalid_answer_gap"],
            }
        )
    return rows


def _freeze_prefix_rows(frozen: dict) -> list[dict]:
    rows = []
    for view_name in ["visible", "masked", "step_only"]:
        metrics = frozen["prefix"][view_name]["metrics"]
        rows.append(
            {
                "model": f"frozen_{view_name}",
                "family": "frozen",
                "task": "PB-Prefix",
                "ordinary_accuracy": metrics["ordinary_accuracy"],
                "ordinary_auroc": metrics["ordinary_auroc"],
                "boundary_drop_mean": metrics["boundary_drop_mean"],
                "invalid_answer_gap": metrics["invalid_answer_gap"],
            }
        )
    return rows


def _reranker_trace_rows(reranker: dict) -> list[dict]:
    rows = []
    for view_name in ["visible", "masked"]:
        payload = reranker["views"][view_name]
        metrics = payload["metrics"]
        threshold = payload["threshold_analysis"]
        calibration = payload["calibration"]
        rows.append(
            {
                "model": f"reranker8_{view_name}",
                "family": "reranker",
                "task": "PB-Trace",
                "ordinary_accuracy_default": metrics["ordinary_accuracy"],
                "ordinary_accuracy_tuned": threshold["test_accuracy_at_selected_threshold"],
                "ordinary_auroc": metrics["ordinary_auroc"],
                "invalid_answer_gap": metrics["invalid_answer_gap"],
                "selected_threshold": threshold["threshold"],
                "ece": calibration["ece"],
                "brier": calibration["brier"],
            }
        )
    return rows


def _build_summary(frozen: dict, reranker: dict, frozen_artifact: Path, reranker_artifact: Path) -> dict:
    trace_rows = _freeze_trace_rows(frozen) + _reranker_trace_rows(reranker)
    prefix_rows = _freeze_prefix_rows(frozen)

    best_trace_by_auroc = max(trace_rows, key=lambda row: row["ordinary_auroc"])
    best_prefix_by_auroc = max(prefix_rows, key=lambda row: row["ordinary_auroc"])
    best_reranker = max(
        [row for row in trace_rows if row["family"] == "reranker"],
        key=lambda row: row["ordinary_auroc"],
    )

    return {
        "config": {
            "frozen_artifact": str(frozen_artifact),
            "reranker_artifact": str(reranker_artifact),
        },
        "trace_rows": trace_rows,
        "prefix_rows": prefix_rows,
        "takeaways": {
            "best_trace_by_auroc": {
                "model": best_trace_by_auroc["model"],
                "ordinary_auroc": best_trace_by_auroc["ordinary_auroc"],
            },
            "best_prefix_by_auroc": {
                "model": best_prefix_by_auroc["model"],
                "ordinary_auroc": best_prefix_by_auroc["ordinary_auroc"],
                "boundary_drop_mean": best_prefix_by_auroc["boundary_drop_mean"],
            },
            "best_reranker_by_auroc": {
                "model": best_reranker["model"],
                "ordinary_auroc": best_reranker["ordinary_auroc"],
                "ordinary_accuracy_default": best_reranker["ordinary_accuracy_default"],
                "ordinary_accuracy_tuned": best_reranker["ordinary_accuracy_tuned"],
            },
            "trace_order_by_auroc": [
                row["model"]
                for row in sorted(trace_rows, key=lambda row: row["ordinary_auroc"], reverse=True)
            ],
        },
    }


def _format_float(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.4f}"


def _render_markdown(summary: dict) -> str:
    lines = [
        "# ProcessBench Main Table",
        "",
        "## PB-Trace",
        "",
        "| model | family | acc@0.5 | acc@val-thr | auroc | invalid_answer_gap | ece | brier |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary["trace_rows"]:
        lines.append(
            "| {model} | {family} | {acc_default} | {acc_tuned} | {auroc} | {gap} | {ece} | {brier} |".format(
                model=row["model"],
                family=row["family"],
                acc_default=_format_float(row.get("ordinary_accuracy", row.get("ordinary_accuracy_default"))),
                acc_tuned=_format_float(row.get("ordinary_accuracy_tuned")),
                auroc=_format_float(row["ordinary_auroc"]),
                gap=_format_float(row["invalid_answer_gap"]),
                ece=_format_float(row.get("ece")),
                brier=_format_float(row.get("brier")),
            )
        )

    lines.extend(
        [
            "",
            "## PB-Prefix",
            "",
            "| model | family | ordinary_accuracy | ordinary_auroc | boundary_drop_mean | invalid_answer_gap |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in summary["prefix_rows"]:
        lines.append(
            "| {model} | {family} | {acc} | {auroc} | {drop} | {gap} |".format(
                model=row["model"],
                family=row["family"],
                acc=_format_float(row["ordinary_accuracy"]),
                auroc=_format_float(row["ordinary_auroc"]),
                drop=_format_float(row["boundary_drop_mean"]),
                gap=_format_float(row["invalid_answer_gap"]),
            )
        )

    takeaways = summary["takeaways"]
    lines.extend(
        [
            "",
            "## Takeaways",
            "",
            f"- Best `PB-Trace` model by AUROC: `{takeaways['best_trace_by_auroc']['model']}` (`{takeaways['best_trace_by_auroc']['ordinary_auroc']:.4f}`).",
            f"- Best `PB-Prefix` model by AUROC: `{takeaways['best_prefix_by_auroc']['model']}` (`{takeaways['best_prefix_by_auroc']['ordinary_auroc']:.4f}`) with boundary drop `{takeaways['best_prefix_by_auroc']['boundary_drop_mean']:.4f}`.",
            f"- Best reranker by AUROC: `{takeaways['best_reranker_by_auroc']['model']}` (`AUROC {takeaways['best_reranker_by_auroc']['ordinary_auroc']:.4f}`), but its default-threshold accuracy (`{takeaways['best_reranker_by_auroc']['ordinary_accuracy_default']:.4f}`) only becomes reasonable after validation-threshold tuning (`{takeaways['best_reranker_by_auroc']['ordinary_accuracy_tuned']:.4f}`).",
            f"- Overall `PB-Trace` AUROC order: `{', '.join(takeaways['trace_order_by_auroc'])}`.",
        ]
    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    args = parse_args()
    frozen = _load_json(args.frozen_artifact)
    reranker = _load_json(args.reranker_artifact)
    summary = _build_summary(
        frozen,
        reranker,
        frozen_artifact=args.frozen_artifact,
        reranker_artifact=args.reranker_artifact,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    args.output_md.write_text(_render_markdown(summary), encoding="utf-8")
    print(json.dumps(summary["takeaways"], indent=2))
