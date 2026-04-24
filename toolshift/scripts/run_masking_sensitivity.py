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
from toolshift.embedding_policy import EmbeddingPolicyConfig, FrozenEmbeddingEncoder, train_embedding_policy_agent
from toolshift.eval import dump_json, evaluate_agent, summarize_records
from toolshift.masking import MASK_VARIANTS, mask_examples
from toolshift.schema import ShiftKind, SplitTag


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run masking sensitivity analysis on the ToolShift dev panel.")
    parser.add_argument("--benchmark", default="data/real_evolution_benchmark.json")
    parser.add_argument("--output-dir", default="artifacts/real_evolution_masking_sensitivity_v1")
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
    parser.add_argument("--masks", nargs="+", default=list(MASK_VARIANTS))
    parser.add_argument("--torch-threads", type=int, default=8)
    return parser.parse_args()


def _core_training_examples(suite, *, excluded_cases: set[str] | None = None):
    excluded_cases = excluded_cases or set()
    return [
        example
        for example in suite.examples
        if example.split_tag == SplitTag.UNAMBIGUOUS_CORE
        and example.schema_view.shift_kind != ShiftKind.IMPOSSIBLE
        and example.case.case_id not in excluded_cases
    ]


def _primary_family_groups(suite) -> dict[str, set[str]]:
    groups: dict[str, set[str]] = {}
    for case in suite.cases:
        family_id = case.family_tag or case.primary_action.tool_id
        if family_id is None:
            continue
        groups.setdefault(family_id, set()).add(case.case_id)
    return groups


def _aggregate_seed_runs(seed_runs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    metric_names = sorted(seed_runs[next(iter(seed_runs))]["summary"]["metrics"])
    means = {}
    stds = {}
    for name in metric_names:
        values = [run["summary"]["metrics"][name] for run in seed_runs.values()]
        if any(value is None for value in values):
            means[name] = None
            stds[name] = None
            continue
        numeric_values = [float(value) for value in values]
        means[name] = mean(numeric_values)
        stds[name] = pstdev(numeric_values) if len(numeric_values) > 1 else 0.0
    return {
        "counts": seed_runs[next(iter(seed_runs))]["summary"]["counts"],
        "metrics_mean": means,
        "metrics_std": stds,
    }


def _fmt(value: float | None) -> str:
    if value is None:
        return "na"
    return f"{value:.3f}"


def _render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Masking Sensitivity",
        "",
        f"- benchmark: `{summary['config']['benchmark']}`",
        f"- methods: `{', '.join(summary['config']['methods'])}`",
        f"- masks: `{', '.join(summary['config']['masks'])}`",
        f"- seeds: `{', '.join(str(seed) for seed in summary['config']['seeds'])}`",
        "",
    ]
    for method in summary["config"]["methods"]:
        lines.append(f"## `{method}`")
        lines.append("")
        lines.append("| Mask | CAA | CAA+ | NOS | POC | Coverage | dCAA | dCAA+ | dNOS | dPOC |")
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
        baseline = summary["masking_sensitivity"][method]["aggregate"]["unmasked"]["metrics_mean"]
        for mask_name in summary["config"]["masks"]:
            metrics = summary["masking_sensitivity"][method]["aggregate"][mask_name]["metrics_mean"]
            delta = summary["masking_sensitivity"][method]["deltas"][mask_name]
            lines.append(
                f"| `{mask_name}` | {_fmt(metrics['CAA_overall'])} | {_fmt(metrics['CAA_positive'])} | {_fmt(metrics['NOS'])} | {_fmt(metrics['POC'])} | {_fmt(metrics['coverage'])} | "
                f"{_fmt(delta['CAA_overall'])} | {_fmt(delta['CAA_positive'])} | {_fmt(delta['NOS'])} | {_fmt(delta['POC'])} |"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = _parse_args()
    if any(mask_name not in MASK_VARIANTS for mask_name in args.masks):
        invalid = sorted(set(args.masks) - set(MASK_VARIANTS))
        raise ValueError(f"unsupported masks: {invalid}")

    try:
        import torch
    except ModuleNotFoundError:
        torch = None
    if torch is not None:
        torch.set_num_threads(args.torch_threads)
        if hasattr(torch, "set_num_interop_threads"):
            torch.set_num_interop_threads(args.torch_threads)

    suite = load_seed_suite(args.benchmark)
    family_groups = _primary_family_groups(suite)
    family_ids = sorted(family_groups)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    config = EmbeddingPolicyConfig(
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        cross_encoder_model_path=args.cross_encoder_model_path,
    )
    encoder = FrozenEmbeddingEncoder(args.model_path, device=args.device)
    feature_lookup = encoder.encode_examples(suite.examples)

    summary_payload: dict[str, Any] = {
        "config": {
            "benchmark": args.benchmark,
            "model_path": args.model_path,
            "cross_encoder_model_path": args.cross_encoder_model_path,
            "device": args.device,
            "methods": args.methods,
            "masks": args.masks,
            "seeds": args.seeds,
            "torch_threads": args.torch_threads,
            "training": asdict(config),
        },
        "masking_sensitivity": {},
    }
    records_payload: dict[str, Any] = {}

    for method in args.methods:
        method_seed_runs: dict[str, dict[str, Any]] = {mask_name: {} for mask_name in args.masks}
        method_records: dict[str, dict[str, Any]] = {mask_name: {} for mask_name in args.masks}
        for seed in args.seeds:
            per_mask_records: dict[str, list[Any]] = {mask_name: [] for mask_name in args.masks}
            fold_train_metrics = []
            for family_id in family_ids:
                held_out_cases = family_groups[family_id]
                train_examples = _core_training_examples(suite, excluded_cases=held_out_cases)
                test_examples = tuple(example for example in suite.examples if example.case.case_id in held_out_cases)
                agent, train_metrics = train_embedding_policy_agent(
                    name=f"{method}_masking_{family_id}_seed{seed}",
                    suite=suite,
                    train_examples=train_examples,
                    feature_lookup=feature_lookup,
                    config=replace(config, seed=seed),
                    method=method,
                    encoder=FrozenEmbeddingEncoder(args.model_path, device=args.device),
                )
                fold_train_metrics.append({"family_id": family_id, **train_metrics})
                for mask_name in args.masks:
                    eval_examples = test_examples if mask_name == "unmasked" else mask_examples(test_examples, mask_name)
                    records, _ = evaluate_agent(agent, suite, examples=eval_examples)
                    per_mask_records[mask_name].extend(records)
            seed_key = f"seed_{seed}"
            for mask_name in args.masks:
                summary = summarize_records(per_mask_records[mask_name], suite.tool_lookup)
                method_seed_runs[mask_name][seed_key] = {
                    "summary": summary,
                    "fold_train_metrics": fold_train_metrics,
                }
                method_records[mask_name][seed_key] = [record.to_dict(suite.tool_lookup) for record in per_mask_records[mask_name]]

        aggregate = {mask_name: _aggregate_seed_runs(seed_runs) for mask_name, seed_runs in method_seed_runs.items()}
        baseline_metrics = aggregate["unmasked"]["metrics_mean"]
        deltas = {}
        for mask_name, mask_summary in aggregate.items():
            metrics = mask_summary["metrics_mean"]
            deltas[mask_name] = {
                metric_name: None
                if metric_name not in baseline_metrics or baseline_metrics[metric_name] is None or metrics[metric_name] is None
                else float(metrics[metric_name]) - float(baseline_metrics[metric_name])
                for metric_name in ("CAA_overall", "CAA_positive", "NOS", "POC")
            }

        summary_payload["masking_sensitivity"][method] = {
            "per_mask_per_seed": method_seed_runs,
            "aggregate": aggregate,
            "deltas": deltas,
        }
        records_payload[method] = method_records

    dump_json(str(output_dir / "summary.json"), summary_payload)
    dump_json(str(output_dir / "records.json"), records_payload)
    (output_dir / "summary.md").write_text(_render_markdown(summary_payload) + "\n", encoding="utf-8")

    print("method\tmask\tCAA\tCAA+\tNOS\tPOC\tcoverage\tdCAA\tdCAA+\tdNOS\tdPOC")
    for method in args.methods:
        for mask_name in args.masks:
            metrics = summary_payload["masking_sensitivity"][method]["aggregate"][mask_name]["metrics_mean"]
            delta = summary_payload["masking_sensitivity"][method]["deltas"][mask_name]
            print(
                f"{method}\t{mask_name}\t{_fmt(metrics['CAA_overall'])}\t{_fmt(metrics['CAA_positive'])}\t"
                f"{_fmt(metrics['NOS'])}\t{_fmt(metrics['POC'])}\t{_fmt(metrics['coverage'])}\t"
                f"{_fmt(delta['CAA_overall'])}\t{_fmt(delta['CAA_positive'])}\t{_fmt(delta['NOS'])}\t{_fmt(delta['POC'])}"
            )


if __name__ == "__main__":
    main()
