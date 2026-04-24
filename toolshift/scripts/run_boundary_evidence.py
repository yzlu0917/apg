#!/usr/bin/env python
from __future__ import annotations

import argparse
from dataclasses import asdict
from dataclasses import replace
from pathlib import Path
from statistics import mean
from typing import Any

from toolshift import load_seed_suite
from toolshift.boundary import build_impossible_shadow_examples, summarize_impossible_shadow_records
from toolshift.embedding_policy import EmbeddingPolicyConfig, FrozenEmbeddingEncoder, train_embedding_policy_agent
from toolshift.eval import dump_json, evaluate_agent, summarize_records
from toolshift.schema import ShiftKind, SplitTag


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run counterfactual impossible-shadow boundary analysis on the ToolShift dev panel.")
    parser.add_argument("--benchmark", default="data/real_evolution_benchmark.json")
    parser.add_argument("--output-dir", default="artifacts/real_evolution_boundary_evidence_v1")
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
    behavior_keys = sorted(seed_runs[next(iter(seed_runs))]["behavior"])
    impossible_keys = sorted(seed_runs[next(iter(seed_runs))]["impossible"])
    aggregate = {
        "behavior": {
            key: mean(float(run["behavior"][key]) for run in seed_runs.values())
            for key in behavior_keys
        },
        "impossible": {
            key: mean(float(run["impossible"][key]) for run in seed_runs.values())
            for key in impossible_keys
        },
    }
    aggregate["boundary_gap"] = aggregate["behavior"]["NOS"] - aggregate["impossible"]["impossible_CAA"]
    return aggregate


def _render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Boundary Evidence",
        "",
        f"- benchmark: `{summary['config']['benchmark']}`",
        f"- methods: `{', '.join(summary['config']['methods'])}`",
        f"- seeds: `{', '.join(str(seed) for seed in summary['config']['seeds'])}`",
        "",
        "Counterfactual impossible shadows reuse each case's clean surface while swapping in the held-out negative admissible action.",
        "",
    ]
    for method in summary["config"]["methods"]:
        aggregate = summary["methods"][method]["aggregate"]
        behavior = aggregate["behavior"]
        impossible = aggregate["impossible"]
        lines.append(f"## `{method}`")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("| --- | ---: |")
        lines.append(f"| `CAA` | {behavior['CAA_overall']:.3f} |")
        lines.append(f"| `CAA+` | {behavior['CAA_positive']:.3f} |")
        lines.append(f"| `NOS` | {behavior['NOS']:.3f} |")
        lines.append(f"| `POC` | {behavior['POC']:.3f} |")
        lines.append(f"| `impossible_shadow_CAA` | {impossible['impossible_CAA']:.3f} |")
        lines.append(f"| `impossible_execute_rate` | {impossible['execute_rate']:.3f} |")
        lines.append(f"| `impossible_abstain_rate` | {impossible['abstain_rate']:.3f} |")
        lines.append(f"| `impossible_ask_clarification_rate` | {impossible['ask_clarification_rate']:.3f} |")
        lines.append(f"| `visible_minus_impossible_gap` | {aggregate['boundary_gap']:.3f} |")
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

    suite = load_seed_suite(args.benchmark)
    impossible_shadows = build_impossible_shadow_examples(suite)
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
            "seeds": args.seeds,
            "torch_threads": args.torch_threads,
            "training": asdict(config),
            "impossible_shadow_count": len(impossible_shadows),
        },
        "methods": {},
    }
    records_payload: dict[str, dict[str, Any]] = {}

    for method in args.methods:
        per_seed: dict[str, Any] = {}
        method_records: dict[str, Any] = {}
        for seed in args.seeds:
            all_records = []
            fold_train_metrics = []
            for family_id in family_ids:
                held_out_cases = family_groups[family_id]
                train_examples = _core_training_examples(suite, excluded_cases=held_out_cases)
                test_examples = tuple(example for example in suite.examples if example.case.case_id in held_out_cases)
                shadow_examples = tuple(example for example in impossible_shadows if example.case.case_id in held_out_cases)
                agent, train_metrics = train_embedding_policy_agent(
                    name=f"{method}_boundary_{family_id}_seed{seed}",
                    suite=suite,
                    train_examples=train_examples,
                    feature_lookup=feature_lookup,
                    config=replace(config, seed=seed),
                    method=method,
                    encoder=FrozenEmbeddingEncoder(args.model_path, device=args.device),
                )
                fold_train_metrics.append({"family_id": family_id, **train_metrics})
                records, _ = evaluate_agent(agent, suite, examples=test_examples + shadow_examples)
                all_records.extend(records)
            seed_key = f"seed_{seed}"
            summary = summarize_records(all_records, suite.tool_lookup)
            impossible_summary = summarize_impossible_shadow_records(all_records)
            per_seed[seed_key] = {
                "behavior": {
                    "CAA_overall": summary["metrics"]["CAA_overall"],
                    "CAA_positive": summary["metrics"]["CAA_positive"],
                    "NOS": summary["metrics"]["NOS"],
                    "POC": summary["metrics"]["POC"],
                },
                "impossible": impossible_summary,
                "fold_train_metrics": fold_train_metrics,
            }
            method_records[seed_key] = [record.to_dict(suite.tool_lookup) for record in all_records]

        summary_payload["methods"][method] = {
            "per_seed": per_seed,
            "aggregate": _aggregate_seed_runs(per_seed),
        }
        records_payload[method] = method_records

    dump_json(str(output_dir / "summary.json"), summary_payload)
    dump_json(str(output_dir / "records.json"), records_payload)
    (output_dir / "summary.md").write_text(_render_markdown(summary_payload) + "\n", encoding="utf-8")

    print("method\tCAA\tCAA+\tNOS\tPOC\timpossible_CAA\timp_exec\tgap")
    for method in args.methods:
        aggregate = summary_payload["methods"][method]["aggregate"]
        print(
            f"{method}\t"
            f"{aggregate['behavior']['CAA_overall']:.3f}\t"
            f"{aggregate['behavior']['CAA_positive']:.3f}\t"
            f"{aggregate['behavior']['NOS']:.3f}\t"
            f"{aggregate['behavior']['POC']:.3f}\t"
            f"{aggregate['impossible']['impossible_CAA']:.3f}\t"
            f"{aggregate['impossible']['execute_rate']:.3f}\t"
            f"{aggregate['boundary_gap']:.3f}"
        )


if __name__ == "__main__":
    main()
