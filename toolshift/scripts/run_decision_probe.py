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
from toolshift.decision_probe import (
    evaluate_linear_probe,
    extract_decision_state,
    fit_linear_probe,
    negative_state_similarity,
    positive_state_similarity,
)
from toolshift.embedding_policy import EmbeddingPolicyConfig, FrozenEmbeddingEncoder, train_embedding_policy_agent
from toolshift.eval import dump_json, evaluate_agent, summarize_records
from toolshift.schema import ShiftKind, SplitTag


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run decision-state probe analysis on the ToolShift dev panel.")
    parser.add_argument("--benchmark", default="data/real_evolution_benchmark.json")
    parser.add_argument("--output-dir", default="artifacts/real_evolution_decision_probe_v1")
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


def _aggregate_metric_dict(values: list[dict[str, float]]) -> dict[str, dict[str, float]]:
    keys = sorted(values[0])
    means = {key: mean(item[key] for item in values) for key in keys}
    stds = {key: pstdev([item[key] for item in values]) if len(values) > 1 else 0.0 for key in keys}
    return {"mean": means, "std": stds}


def _aggregate_seed_runs(seed_runs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    behavior_keys = sorted(seed_runs[next(iter(seed_runs))]["behavior"])
    probe_keys = sorted(seed_runs[next(iter(seed_runs))]["probe"])
    similarity_keys = sorted(seed_runs[next(iter(seed_runs))]["similarity"])
    return {
        "behavior": {
            key: mean(run["behavior"][key] for run in seed_runs.values())
            for key in behavior_keys
        },
        "probe": {
            key: mean(run["probe"][key] for run in seed_runs.values())
            for key in probe_keys
        },
        "similarity": {
            key: mean(run["similarity"][key] for run in seed_runs.values())
            for key in similarity_keys
        },
    }


def _render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Decision-State Probe",
        "",
        f"- benchmark: `{summary['config']['benchmark']}`",
        f"- methods: `{', '.join(summary['config']['methods'])}`",
        f"- seeds: `{', '.join(str(seed) for seed in summary['config']['seeds'])}`",
        "",
    ]
    for method in summary["config"]["methods"]:
        aggregate = summary["methods"][method]["aggregate"]
        behavior = aggregate["behavior"]
        probe = aggregate["probe"]
        similarity = aggregate["similarity"]
        lines.append(f"## `{method}`")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("| --- | ---: |")
        lines.append(f"| `CAA` | {behavior['CAA_overall']:.3f} |")
        lines.append(f"| `CAA+` | {behavior['CAA_positive']:.3f} |")
        lines.append(f"| `NOS` | {behavior['NOS']:.3f} |")
        lines.append(f"| `POC` | {behavior['POC']:.3f} |")
        lines.append(f"| `probe_accuracy` | {probe['accuracy']:.3f} |")
        lines.append(f"| `probe_negative_recall` | {probe['positive_recall']:.3f} |")
        lines.append(f"| `positive_state_similarity` | {similarity['positive_state_similarity']:.3f} |")
        lines.append(f"| `negative_state_similarity` | {similarity['negative_state_similarity']:.3f} |")
        lines.append(f"| `state_separation_gap` | {similarity['state_separation_gap']:.3f} |")
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
        },
        "methods": {},
    }

    for method in args.methods:
        per_seed: dict[str, Any] = {}
        for seed in args.seeds:
            all_behavior_records = []
            probe_metrics = []
            similarity_metrics = []
            train_probe_metrics = []
            for family_id in family_ids:
                held_out_cases = family_groups[family_id]
                train_examples = _core_training_examples(suite, excluded_cases=held_out_cases)
                test_examples = tuple(example for example in suite.examples if example.case.case_id in held_out_cases)
                agent, train_metrics = train_embedding_policy_agent(
                    name=f"{method}_decision_probe_{family_id}_seed{seed}",
                    suite=suite,
                    train_examples=train_examples,
                    feature_lookup=feature_lookup,
                    config=replace(config, seed=seed),
                    method=method,
                    encoder=FrozenEmbeddingEncoder(args.model_path, device=args.device),
                )
                records, _ = evaluate_agent(agent, suite, examples=test_examples)
                all_behavior_records.extend(records)

                train_states = [extract_decision_state(agent, example) for example in train_examples]
                train_labels = [example.schema_view.shift_kind == ShiftKind.NEGATIVE_NEAR_ORBIT for example in train_examples]
                probe, probe_train = fit_linear_probe(train_states, train_labels)
                train_probe_metrics.append({"family_id": family_id, **probe_train, **train_metrics})

                test_states = [extract_decision_state(agent, example) for example in test_examples]
                test_labels = [example.schema_view.shift_kind == ShiftKind.NEGATIVE_NEAR_ORBIT for example in test_examples]
                probe_eval = evaluate_linear_probe(probe, test_states, test_labels)
                probe_metrics.append(probe_eval)

                pos_similarity = positive_state_similarity(test_states, list(test_examples))
                neg_similarity = negative_state_similarity(test_states, list(test_examples))
                similarity_metrics.append(
                    {
                        "positive_state_similarity": 0.0 if pos_similarity is None else pos_similarity,
                        "negative_state_similarity": 0.0 if neg_similarity is None else neg_similarity,
                        "state_separation_gap": 0.0 if pos_similarity is None or neg_similarity is None else pos_similarity - neg_similarity,
                    }
                )

            seed_key = f"seed_{seed}"
            summary = summarize_records(all_behavior_records, suite.tool_lookup)
            behavior_summary = {
                "CAA_overall": summary["metrics"]["CAA_overall"],
                "CAA_positive": summary["metrics"]["CAA_positive"],
                "NOS": summary["metrics"]["NOS"],
                "POC": summary["metrics"]["POC"],
            }
            per_seed[seed_key] = {
                "behavior": behavior_summary,
                "probe": _aggregate_metric_dict(probe_metrics)["mean"],
                "similarity": _aggregate_metric_dict(similarity_metrics)["mean"],
                "fold_train_metrics": train_probe_metrics,
            }
        summary_payload["methods"][method] = {
            "per_seed": per_seed,
            "aggregate": _aggregate_seed_runs(per_seed),
        }

    dump_json(str(output_dir / "summary.json"), summary_payload)
    (output_dir / "summary.md").write_text(_render_markdown(summary_payload) + "\n", encoding="utf-8")

    print("method\tCAA\tCAA+\tNOS\tPOC\tprobe_acc\tprobe_neg_recall\tpos_sim\tneg_sim\tgap")
    for method in args.methods:
        aggregate = summary_payload["methods"][method]["aggregate"]
        print(
            f"{method}\t"
            f"{aggregate['behavior']['CAA_overall']:.3f}\t"
            f"{aggregate['behavior']['CAA_positive']:.3f}\t"
            f"{aggregate['behavior']['NOS']:.3f}\t"
            f"{aggregate['behavior']['POC']:.3f}\t"
            f"{aggregate['probe']['accuracy']:.3f}\t"
            f"{aggregate['probe']['positive_recall']:.3f}\t"
            f"{aggregate['similarity']['positive_state_similarity']:.3f}\t"
            f"{aggregate['similarity']['negative_state_similarity']:.3f}\t"
            f"{aggregate['similarity']['state_separation_gap']:.3f}"
        )


if __name__ == "__main__":
    main()
