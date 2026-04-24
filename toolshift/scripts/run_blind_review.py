#!/usr/bin/env python
from __future__ import annotations

import argparse
from dataclasses import asdict
from dataclasses import replace
from pathlib import Path
from statistics import mean
from statistics import pstdev
from typing import Any

from toolshift import load_seed_suite
from toolshift.blind_panel import validate_blind_panel
from toolshift.blind_review import core_training_examples, summarize_records_by_family
from toolshift.embedding_policy import EmbeddingPolicyConfig, FrozenEmbeddingEncoder, train_embedding_policy_agent
from toolshift.eval import dump_json, evaluate_agent


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run frozen blind-panel final review for the retained ToolShift method line.")
    parser.add_argument("--dev-benchmark", default="data/real_evolution_benchmark.json")
    parser.add_argument("--blind-benchmark", default="data/real_evolution_blind_benchmark.json")
    parser.add_argument("--output-dir", default="artifacts/real_evolution_blind_review_v1")
    parser.add_argument("--model-path", default="/cephfs/shared/hf_cache/hub/Qwen3-Embedding-0.6B")
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--learning-rate", type=float, default=1e-2)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--cross-encoder-model-path", default="/cephfs/shared/hf_cache/hub/Qwen3-Reranker-0.6B")
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1])
    parser.add_argument(
        "--methods",
        nargs="+",
        default=["semantic_embedding_capability_gate", "semantic_clause_localization_capability_gate"],
    )
    parser.add_argument("--torch-threads", type=int, default=8)
    return parser.parse_args()


def _aggregate_metric_dict(metric_dicts: list[dict[str, float | int | None]]) -> dict[str, float | int | None]:
    keys = sorted(metric_dicts[0])
    aggregate: dict[str, float | int | None] = {}
    for key in keys:
        values = [entry[key] for entry in metric_dicts]
        if any(value is None for value in values):
            aggregate[key] = None
            continue
        if key.endswith("_count") or key == "view_count":
            aggregate[key] = int(values[0])
            continue
        aggregate[key] = mean(float(value) for value in values)
    return aggregate


def _aggregate_seed_runs(seed_runs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    summary_keys = sorted(seed_runs[next(iter(seed_runs))]["summary"]["metrics"])
    summary_mean = {}
    summary_std = {}
    for key in summary_keys:
        values = [run["summary"]["metrics"][key] for run in seed_runs.values()]
        if any(value is None for value in values):
            summary_mean[key] = None
            summary_std[key] = None
            continue
        numeric_values = [float(value) for value in values]
        summary_mean[key] = mean(numeric_values)
        summary_std[key] = pstdev(numeric_values) if len(numeric_values) > 1 else 0.0
    family_ids = sorted(seed_runs[next(iter(seed_runs))]["family_metrics"])
    family_mean = {
        family_id: _aggregate_metric_dict([run["family_metrics"][family_id] for run in seed_runs.values()])
        for family_id in family_ids
    }
    return {
        "metrics_mean": summary_mean,
        "metrics_std": summary_std,
        "family_metrics_mean": family_mean,
    }


def _fmt(value: float | int | None) -> str:
    if value is None:
        return "na"
    if isinstance(value, int):
        return str(value)
    return f"{value:.3f}"


def _render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Blind Review",
        "",
        f"- dev benchmark: `{summary['config']['dev_benchmark']}`",
        f"- blind benchmark: `{summary['config']['blind_benchmark']}`",
        f"- methods: `{', '.join(summary['config']['methods'])}`",
        f"- seeds: `{', '.join(str(seed) for seed in summary['config']['seeds'])}`",
        "",
        "Frozen blind panel is used here only for final review; no method selection is performed on these results.",
        "",
    ]
    for method in summary["config"]["methods"]:
        aggregate = summary["methods"][method]["aggregate"]
        metrics = aggregate["metrics_mean"]
        lines.append(f"## `{method}`")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("| --- | ---: |")
        lines.append(f"| `CAA` | {_fmt(metrics['CAA_overall'])} |")
        lines.append(f"| `CAA_clean` | {_fmt(metrics['CAA_clean'])} |")
        lines.append(f"| `CAA+` | {_fmt(metrics['CAA_positive'])} |")
        lines.append(f"| `NOS` | {_fmt(metrics['NOS'])} |")
        lines.append(f"| `POC` | {_fmt(metrics['POC'])} |")
        lines.append(f"| `coverage` | {_fmt(metrics['coverage'])} |")
        lines.append("")
        lines.append("| Family | CAA | CAA+ | NOS | POC | Coverage | Views |")
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
        for family_id, family_metrics in aggregate["family_metrics_mean"].items():
            lines.append(
                f"| `{family_id}` | {_fmt(family_metrics['CAA'])} | {_fmt(family_metrics['CAA_positive'])} | "
                f"{_fmt(family_metrics['NOS'])} | {_fmt(family_metrics['POC'])} | {_fmt(family_metrics['coverage'])} | "
                f"{_fmt(family_metrics['view_count'])} |"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = _parse_args()

    try:
        import torch
    except ModuleNotFoundError:
        torch = None
    if torch is not None:
        torch.set_num_threads(args.torch_threads)
        if hasattr(torch, "set_num_interop_threads"):
            torch.set_num_interop_threads(args.torch_threads)

    validate_blind_panel(args.blind_benchmark)
    dev_suite = load_seed_suite(args.dev_benchmark)
    blind_suite = load_seed_suite(args.blind_benchmark)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    config = EmbeddingPolicyConfig(
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        cross_encoder_model_path=args.cross_encoder_model_path,
    )
    encoder = FrozenEmbeddingEncoder(args.model_path, device=args.device)
    dev_feature_lookup = encoder.encode_examples(dev_suite.examples)
    train_examples = core_training_examples(dev_suite)

    summary_payload: dict[str, Any] = {
        "config": {
            "dev_benchmark": args.dev_benchmark,
            "blind_benchmark": args.blind_benchmark,
            "model_path": args.model_path,
            "cross_encoder_model_path": args.cross_encoder_model_path,
            "device": args.device,
            "methods": args.methods,
            "seeds": args.seeds,
            "torch_threads": args.torch_threads,
            "training": asdict(config),
            "train_example_count": len(train_examples),
        },
        "methods": {},
    }
    records_payload: dict[str, Any] = {}

    for method in args.methods:
        per_seed: dict[str, Any] = {}
        method_records: dict[str, Any] = {}
        for seed in args.seeds:
            agent, train_metrics = train_embedding_policy_agent(
                name=f"{method}_blind_review_seed{seed}",
                suite=dev_suite,
                train_examples=train_examples,
                feature_lookup=dev_feature_lookup,
                config=replace(config, seed=seed),
                method=method,
                encoder=FrozenEmbeddingEncoder(args.model_path, device=args.device),
            )
            records, summary = evaluate_agent(agent, blind_suite)
            seed_key = f"seed_{seed}"
            per_seed[seed_key] = {
                "summary": summary,
                "family_metrics": summarize_records_by_family(blind_suite, records),
                "train_metrics": train_metrics,
            }
            method_records[seed_key] = [record.to_dict(blind_suite.tool_lookup) for record in records]
        summary_payload["methods"][method] = {
            "per_seed": per_seed,
            "aggregate": _aggregate_seed_runs(per_seed),
        }
        records_payload[method] = method_records

    dump_json(str(output_dir / "summary.json"), summary_payload)
    dump_json(str(output_dir / "records.json"), records_payload)
    (output_dir / "summary.md").write_text(_render_markdown(summary_payload) + "\n", encoding="utf-8")

    print("method\tCAA\tCAA+\tNOS\tPOC\tcoverage")
    for method in args.methods:
        metrics = summary_payload["methods"][method]["aggregate"]["metrics_mean"]
        print(
            f"{method}\t"
            f"{_fmt(metrics['CAA_overall'])}\t"
            f"{_fmt(metrics['CAA_positive'])}\t"
            f"{_fmt(metrics['NOS'])}\t"
            f"{_fmt(metrics['POC'])}\t"
            f"{_fmt(metrics['coverage'])}"
        )


if __name__ == "__main__":
    main()
