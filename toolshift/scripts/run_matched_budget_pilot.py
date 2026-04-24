#!/usr/bin/env python
from __future__ import annotations

import argparse
from dataclasses import asdict
from dataclasses import replace
from pathlib import Path
from statistics import mean
from statistics import pstdev
from typing import Any
from typing import Sequence

from toolshift import load_seed_suite
from toolshift.embedding_policy import (
    CROSS_ENCODER_RERANKER_DEFAULT_PATH,
    EmbeddingPolicyConfig,
    FrozenEmbeddingEncoder,
    action_state_similarity,
    train_embedding_policy_agent,
)
from toolshift.eval import dump_json, evaluate_agent, summarize_records
from toolshift.schema import ShiftKind, SplitTag


def _fmt(value: float | None) -> str:
    if value is None:
        return "na"
    return f"{value:.3f}"


def _core_training_examples(suite, *, excluded_cases: set[str] | None = None, excluded_transforms: set[str] | None = None):
    excluded_cases = excluded_cases or set()
    excluded_transforms = excluded_transforms or set()
    return [
        example
        for example in suite.examples
        if example.split_tag == SplitTag.UNAMBIGUOUS_CORE
        and example.schema_view.shift_kind != ShiftKind.IMPOSSIBLE
        and example.case.case_id not in excluded_cases
        and example.schema_view.transform_name not in excluded_transforms
    ]


def _examples_for_cases(suite, case_ids: set[str]):
    return tuple(example for example in suite.examples if example.case.case_id in case_ids)


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
    similarity_values = [run["action_state_similarity"] for run in seed_runs.values() if run["action_state_similarity"] is not None]
    return {
        "counts": seed_runs[next(iter(seed_runs))]["summary"]["counts"],
        "metrics_mean": means,
        "metrics_std": stds,
        "action_state_similarity_mean": mean(similarity_values) if similarity_values else None,
        "action_state_similarity_std": pstdev(similarity_values) if len(similarity_values) > 1 else 0.0,
    }


def _run_combo_holdout(
    *,
    suite,
    feature_lookup,
    base_config: EmbeddingPolicyConfig,
    seeds: list[int],
    model_path: str,
    device: str,
    methods: Sequence[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    summary_payload: dict[str, Any] = {}
    records_payload: dict[str, Any] = {}
    train_examples = _core_training_examples(suite, excluded_transforms={"positive_combo"})
    positive_eval = [
        example
        for example in suite.examples
        if example.split_tag == SplitTag.UNAMBIGUOUS_CORE and example.schema_view.shift_kind in {ShiftKind.CLEAN, ShiftKind.POSITIVE_ORBIT}
    ]
    for method in methods:
        seed_runs = {}
        method_records = {}
        for seed in seeds:
            print(f"[combo_holdout] method={method} seed={seed}", flush=True)
            config = replace(base_config, seed=seed)
            agent, train_metrics = train_embedding_policy_agent(
                name=f"{method}_combo_seed{seed}",
                suite=suite,
                train_examples=train_examples,
                feature_lookup=feature_lookup,
                config=config,
                method=method,
                encoder=FrozenEmbeddingEncoder(model_path, device=device),
            )
            records, summary = evaluate_agent(agent, suite)
            similarity = action_state_similarity(agent, positive_eval, feature_lookup)
            seed_key = f"seed_{seed}"
            seed_runs[seed_key] = {
                "summary": summary,
                "train_metrics": train_metrics,
                "action_state_similarity": similarity,
            }
            method_records[seed_key] = [record.to_dict(suite.tool_lookup) for record in records]
        summary_payload[method] = {
            "train_split": {
                "excluded_transforms": ["positive_combo"],
                "train_examples": len(train_examples),
            },
            "per_seed": seed_runs,
            "aggregate": _aggregate_seed_runs(seed_runs),
        }
        records_payload[method] = method_records
    return summary_payload, records_payload


def _run_case_holdout_cv(
    *,
    suite,
    feature_lookup,
    base_config: EmbeddingPolicyConfig,
    seeds: list[int],
    model_path: str,
    device: str,
    methods: Sequence[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    summary_payload: dict[str, Any] = {}
    records_payload: dict[str, Any] = {}
    case_ids = [case.case_id for case in suite.cases]
    for method in methods:
        seed_runs = {}
        method_records = {}
        for seed in seeds:
            print(f"[case_holdout_cv] method={method} seed={seed}", flush=True)
            fold_metrics = []
            fold_similarities = []
            all_records = []
            for case_id in case_ids:
                print(f"  fold={case_id}", flush=True)
                config = replace(base_config, seed=seed)
                train_examples = _core_training_examples(suite, excluded_cases={case_id})
                test_examples = tuple(example for example in suite.examples if example.case.case_id == case_id)
                agent, train_metrics = train_embedding_policy_agent(
                    name=f"{method}_case_holdout_{case_id}_seed{seed}",
                    suite=suite,
                    train_examples=train_examples,
                    feature_lookup=feature_lookup,
                    config=config,
                    method=method,
                    encoder=FrozenEmbeddingEncoder(model_path, device=device),
                )
                records, _ = evaluate_agent(agent, suite, examples=test_examples)
                all_records.extend(records)
                fold_metrics.append({"case_id": case_id, **train_metrics})
                core_positive = [
                    example
                    for example in test_examples
                    if example.split_tag == SplitTag.UNAMBIGUOUS_CORE
                    and example.schema_view.shift_kind in {ShiftKind.CLEAN, ShiftKind.POSITIVE_ORBIT}
                ]
                fold_similarities.append(
                    {
                        "case_id": case_id,
                        "value": action_state_similarity(agent, core_positive, feature_lookup),
                    }
                )
            summary = summarize_records(all_records, suite.tool_lookup)
            similarity_values = [entry["value"] for entry in fold_similarities if entry["value"] is not None]
            seed_key = f"seed_{seed}"
            seed_runs[seed_key] = {
                "summary": summary,
                "fold_train_metrics": fold_metrics,
                "fold_action_state_similarity": fold_similarities,
                "action_state_similarity": mean(similarity_values) if similarity_values else None,
            }
            method_records[seed_key] = [record.to_dict(suite.tool_lookup) for record in all_records]
        summary_payload[method] = {
            "train_split": {
                "excluded_cases": case_ids,
                "folds": len(case_ids),
            },
            "per_seed": seed_runs,
            "aggregate": _aggregate_seed_runs(seed_runs),
        }
        records_payload[method] = method_records
    return summary_payload, records_payload


def _run_family_holdout_cv(
    *,
    suite,
    feature_lookup,
    base_config: EmbeddingPolicyConfig,
    seeds: list[int],
    model_path: str,
    device: str,
    methods: Sequence[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    summary_payload: dict[str, Any] = {}
    records_payload: dict[str, Any] = {}
    family_groups = _primary_family_groups(suite)
    family_ids = sorted(family_groups)
    all_case_ids = {case.case_id for case in suite.cases}
    for method in methods:
        seed_runs = {}
        method_records = {}
        for seed in seeds:
            print(f"[family_holdout_cv] method={method} seed={seed}", flush=True)
            fold_metrics = []
            fold_similarities = []
            all_records = []
            for family_id in family_ids:
                print(f"  fold={family_id}", flush=True)
                held_out_cases = family_groups[family_id]
                train_examples = _core_training_examples(suite, excluded_cases=held_out_cases)
                test_examples = _examples_for_cases(suite, held_out_cases)
                config = replace(base_config, seed=seed)
                agent, train_metrics = train_embedding_policy_agent(
                    name=f"{method}_family_holdout_{family_id}_seed{seed}",
                    suite=suite,
                    train_examples=train_examples,
                    feature_lookup=feature_lookup,
                    config=config,
                    method=method,
                    encoder=FrozenEmbeddingEncoder(model_path, device=device),
                )
                records, _ = evaluate_agent(agent, suite, examples=test_examples)
                all_records.extend(records)
                fold_metrics.append(
                    {
                        "family_id": family_id,
                        "held_out_cases": sorted(held_out_cases),
                        "train_case_count": len(all_case_ids - held_out_cases),
                        **train_metrics,
                    }
                )
                core_positive = [
                    example
                    for example in test_examples
                    if example.split_tag == SplitTag.UNAMBIGUOUS_CORE
                    and example.schema_view.shift_kind in {ShiftKind.CLEAN, ShiftKind.POSITIVE_ORBIT}
                ]
                fold_similarities.append(
                    {
                        "family_id": family_id,
                        "value": action_state_similarity(agent, core_positive, feature_lookup),
                    }
                )
            summary = summarize_records(all_records, suite.tool_lookup)
            similarity_values = [entry["value"] for entry in fold_similarities if entry["value"] is not None]
            seed_key = f"seed_{seed}"
            seed_runs[seed_key] = {
                "summary": summary,
                "fold_train_metrics": fold_metrics,
                "fold_action_state_similarity": fold_similarities,
                "action_state_similarity": mean(similarity_values) if similarity_values else None,
            }
            method_records[seed_key] = [record.to_dict(suite.tool_lookup) for record in all_records]
        summary_payload[method] = {
            "train_split": {
                "held_out_families": family_ids,
                "folds": len(family_ids),
            },
            "per_seed": seed_runs,
            "aggregate": _aggregate_seed_runs(seed_runs),
        }
        records_payload[method] = method_records
    return summary_payload, records_payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the ToolShift matched-budget AugOnly vs SCC-lite pilot.")
    parser.add_argument("--benchmark", default="data/seed_benchmark.json")
    parser.add_argument("--output-dir", default="artifacts/matched_budget_pilot")
    parser.add_argument("--model-path", default="/cephfs/shared/hf_cache/hub/Qwen3-Embedding-0.6B")
    parser.add_argument("--cross-encoder-model-path", default=CROSS_ENCODER_RERANKER_DEFAULT_PATH)
    parser.add_argument("--cross-encoder-batch-size", type=int, default=4)
    parser.add_argument("--cross-encoder-max-length", type=int, default=4096)
    parser.add_argument("--cross-encoder-class-balance-power", type=float, default=0.5)
    parser.add_argument("--cross-encoder-hard-negative-multiplier", type=float, default=1.5)
    parser.add_argument("--cross-encoder-positive-retention-target", type=float, default=0.95)
    parser.add_argument("--cross-encoder-execute-margin", type=float, default=0.0)
    parser.add_argument("--cross-encoder-execute-margin-weight", type=float, default=0.5)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--bottleneck-dim", type=int, default=128)
    parser.add_argument("--learning-rate", type=float, default=1e-2)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--lambda-inv", type=float, default=0.1)
    parser.add_argument("--lambda-ctr", type=float, default=0.1)
    parser.add_argument("--lambda-slot", type=float, default=0.25)
    parser.add_argument("--lambda-distill-control", type=float, default=0.25)
    parser.add_argument("--lambda-distill-tool", type=float, default=0.25)
    parser.add_argument("--lambda-distill-slot", type=float, default=0.1)
    parser.add_argument("--lambda-distill-gap", type=float, default=0.1)
    parser.add_argument("--contrastive-margin", type=float, default=0.2)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    parser.add_argument("--torch-threads", type=int, default=8)
    parser.add_argument("--methods", nargs="+", default=["aug_only", "scc_lite"])
    parser.add_argument(
        "--regimes",
        nargs="+",
        default=["combo_holdout", "case_holdout_cv", "family_holdout_cv"],
        choices=["combo_holdout", "case_holdout_cv", "family_holdout_cv"],
    )
    args = parser.parse_args()

    try:
        import torch
    except ModuleNotFoundError:
        torch = None
    if torch is not None:
        torch.set_num_threads(args.torch_threads)
        if hasattr(torch, "set_num_interop_threads"):
            torch.set_num_interop_threads(args.torch_threads)

    suite = load_seed_suite(args.benchmark)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    config = EmbeddingPolicyConfig(
        bottleneck_dim=args.bottleneck_dim,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        lambda_inv=args.lambda_inv,
        lambda_ctr=args.lambda_ctr,
        lambda_slot=args.lambda_slot,
        lambda_distill_control=args.lambda_distill_control,
        lambda_distill_tool=args.lambda_distill_tool,
        lambda_distill_slot=args.lambda_distill_slot,
        lambda_distill_gap=args.lambda_distill_gap,
        contrastive_margin=args.contrastive_margin,
        cross_encoder_model_path=args.cross_encoder_model_path,
        cross_encoder_batch_size=args.cross_encoder_batch_size,
        cross_encoder_max_length=args.cross_encoder_max_length,
        cross_encoder_class_balance_power=args.cross_encoder_class_balance_power,
        cross_encoder_hard_negative_multiplier=args.cross_encoder_hard_negative_multiplier,
        cross_encoder_positive_retention_target=args.cross_encoder_positive_retention_target,
        cross_encoder_execute_margin=args.cross_encoder_execute_margin,
        cross_encoder_execute_margin_weight=args.cross_encoder_execute_margin_weight,
    )
    encoder = FrozenEmbeddingEncoder(args.model_path, device=args.device)
    feature_lookup = encoder.encode_examples(suite.examples)

    summary_payload = {
        "config": {
            "benchmark": args.benchmark,
            "model_path": args.model_path,
            "cross_encoder_model_path": args.cross_encoder_model_path,
            "device": args.device,
            "seeds": args.seeds,
            "methods": args.methods,
            "regimes": args.regimes,
            "torch_threads": args.torch_threads,
            "training": asdict(config),
        },
    }
    records_payload = {}

    if "combo_holdout" in args.regimes:
        combo_summary, combo_records = _run_combo_holdout(
            suite=suite,
            feature_lookup=feature_lookup,
            base_config=config,
            seeds=args.seeds,
            model_path=args.model_path,
            device=args.device,
            methods=args.methods,
        )
        summary_payload["combo_holdout"] = combo_summary
        records_payload["combo_holdout"] = combo_records
    if "case_holdout_cv" in args.regimes:
        case_summary, case_records = _run_case_holdout_cv(
            suite=suite,
            feature_lookup=feature_lookup,
            base_config=config,
            seeds=args.seeds,
            model_path=args.model_path,
            device=args.device,
            methods=args.methods,
        )
        summary_payload["case_holdout_cv"] = case_summary
        records_payload["case_holdout_cv"] = case_records
    if "family_holdout_cv" in args.regimes:
        family_summary, family_records = _run_family_holdout_cv(
            suite=suite,
            feature_lookup=feature_lookup,
            base_config=config,
            seeds=args.seeds,
            model_path=args.model_path,
            device=args.device,
            methods=args.methods,
        )
        summary_payload["family_holdout_cv"] = family_summary
        records_payload["family_holdout_cv"] = family_records

    dump_json(str(output_dir / "summary.json"), summary_payload)
    dump_json(str(output_dir / "records.json"), records_payload)

    print("regime\tmethod\tCAA\tCAA+\tNOS\tPOC\tcoverage\taction_state_sim")
    for regime_name in args.regimes:
        regime_payload = summary_payload[regime_name]
        for method in args.methods:
            aggregate = regime_payload[method]["aggregate"]
            metrics = aggregate["metrics_mean"]
            print(
                f"{regime_name}\t{method}\t"
                f"{_fmt(metrics['CAA_overall'])}\t"
                f"{_fmt(metrics['CAA_positive'])}\t"
                f"{_fmt(metrics['NOS'])}\t"
                f"{_fmt(metrics['POC'])}\t"
                f"{_fmt(metrics['coverage'])}\t"
                f"{_fmt(aggregate['action_state_similarity_mean'])}"
            )


if __name__ == "__main__":
    main()
