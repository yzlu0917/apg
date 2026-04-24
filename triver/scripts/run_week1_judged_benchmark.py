from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import random

from datasets import load_dataset

from triver.models.api_runner import runner_from_env
from triver.oracle.judged_benchmark import (
    GenerationConfig,
    JudgeConfig,
    UtilityConfig,
    build_summary,
    estimate_prefix_oracle,
    extract_gsm8k_answer,
    format_summary,
    make_recoverable_prefix,
    sample_base_trace,
    select_decision_points,
)


CSV_FIELDS = [
    "dataset",
    "benchmark_tier",
    "sample_id",
    "problem",
    "target",
    "prefix_variant",
    "prefix_length",
    "budget_tokens",
    "q_t",
    "prefix_invalid",
    "mu_continue",
    "nu_continue",
    "continue_utility",
    "continue_std_utility",
    "continue_wrong_rate",
    "continue_mean_tokens",
    "revise_utility",
    "abstain_utility",
    "revise_gain",
    "oracle_action",
    "action_gap",
    "ambiguous",
    "prefix_trace",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a judge-based broad prefix benchmark.")
    parser.add_argument("--dataset", default="gsm8k")
    parser.add_argument("--dataset-config", default="main")
    parser.add_argument("--dataset-split", default="test")
    parser.add_argument("--num-samples", type=int, default=3)
    parser.add_argument("--max-decision-points", type=int, default=2)
    parser.add_argument("--num-rollouts", type=int, default=2)
    parser.add_argument("--total-budget-tokens", type=int, default=160)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top-p", type=float, default=0.9)
    parser.add_argument(
        "--generation-style",
        choices=("default", "compact_final"),
        default="default",
        help="Generation-side prompt style for base traces and action rollouts.",
    )
    parser.add_argument("--lambda-tok", type=float, default=0.002)
    parser.add_argument("--gamma-wrong", type=float, default=0.5)
    parser.add_argument("--judge-invalid-threshold", type=float, default=0.5)
    parser.add_argument(
        "--judge-ensemble-mode",
        choices=("single", "dual", "dual_consensus"),
        default="single",
        help="Judge aggregation mode for prefix-risk and correctness prompts.",
    )
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--augment-revise-prefixes", action="store_true")
    parser.add_argument("--model-path", default="/cephfs/shared/hf_cache/hub/Qwen3-4B")
    parser.add_argument("--tokenizer-path", default="", help="Optional tokenizer path for API token counting.")
    parser.add_argument("--api-model", default=os.environ.get("TRIVER_API_MODEL", ""))
    parser.add_argument("--api-base-url", default=os.environ.get("TRIVER_API_BASE_URL", ""))
    parser.add_argument("--api-key", default=os.environ.get("TRIVER_API_KEY", ""))
    parser.add_argument("--judge-api-model", default=os.environ.get("TRIVER_JUDGE_API_MODEL", ""))
    parser.add_argument("--judge-api-base-url", default=os.environ.get("TRIVER_JUDGE_API_BASE_URL", ""))
    parser.add_argument("--judge-api-key", default=os.environ.get("TRIVER_JUDGE_API_KEY", ""))
    parser.add_argument("--api-timeout-sec", type=float, default=120.0)
    parser.add_argument(
        "--base-traces-json",
        default="",
        help="Optional path to a cached base_traces.json file. When set, reuse those base traces instead of regenerating them.",
    )
    parser.add_argument("--output-dir", default="outputs/week1_gsm8k_judged_smoke")
    return parser.parse_args()


def build_runner(args: argparse.Namespace):
    return runner_from_env(
        model=args.api_model,
        api_key=args.api_key,
        base_url=args.api_base_url,
        tokenizer_path=args.tokenizer_path or None,
        timeout_sec=args.api_timeout_sec,
    )


def build_judge_runner(args: argparse.Namespace):
    return runner_from_env(
        model=args.judge_api_model or args.api_model,
        api_key=args.judge_api_key or args.api_key,
        base_url=args.judge_api_base_url or args.api_base_url,
        tokenizer_path=args.tokenizer_path or None,
        timeout_sec=args.api_timeout_sec,
    )


def load_samples(args: argparse.Namespace, rng: random.Random) -> list[dict[str, str]]:
    dataset = load_dataset(args.dataset, args.dataset_config, split=args.dataset_split)
    if len(dataset) < args.num_samples:
        raise ValueError(f"Requested {args.num_samples} samples but split has only {len(dataset)}")
    indices = list(range(len(dataset)))
    rng.shuffle(indices)
    selected = indices[: args.num_samples]
    rows: list[dict[str, str]] = []
    for dataset_index in selected:
        item = dataset[dataset_index]
        question = str(item["question"])
        answer = extract_gsm8k_answer(str(item["answer"]))
        rows.append({"question": question, "answer": answer})
    return rows


def load_cached_base_traces(path: str) -> list[dict[str, object]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Expected a list in cached base traces: {path}")
    rows: list[dict[str, object]] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError(f"Malformed base trace entry in {path}")
        question = str(item.get("question", ""))
        answer = str(item.get("answer", ""))
        base_trace = item.get("base_trace", [])
        raw_generation = str(item.get("raw_generation", ""))
        sample_id = int(item.get("sample_id", len(rows)))
        if not question or not answer or not isinstance(base_trace, list):
            raise ValueError(f"Incomplete base trace entry for sample_id={sample_id} in {path}")
        rows.append(
            {
                "sample_id": sample_id,
                "question": question,
                "answer": answer,
                "base_trace": list(base_trace),
                "raw_generation": raw_generation,
            }
        )
    return rows


def write_records_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def summarize_base_traces(base_traces: list[dict[str, object]]) -> dict[str, float]:
    total = len(base_traces)
    if total == 0:
        return {
            "base_trace_terminal_rate": 0.0,
            "base_trace_nonterminal_count": 0.0,
            "base_trace_mean_steps": 0.0,
        }
    terminal_count = 0
    total_steps = 0
    for row in base_traces:
        trace = list(row.get("base_trace", []))
        total_steps += max(0, len(trace) - 1)
        if trace and trace[-1].lower().startswith("final answer:"):
            terminal_count += 1
    return {
        "base_trace_terminal_rate": terminal_count / total,
        "base_trace_nonterminal_count": float(total - terminal_count),
        "base_trace_mean_steps": total_steps / total,
    }


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    runner = build_runner(args)
    judge_runner = build_judge_runner(args)
    generation_config = GenerationConfig(
        max_new_tokens=args.total_budget_tokens,
        num_rollouts=args.num_rollouts,
        temperature=args.temperature,
        top_p=args.top_p,
        style=args.generation_style,
    )
    utility_config = UtilityConfig(lambda_tok=args.lambda_tok, gamma_wrong=args.gamma_wrong)
    judge_config = JudgeConfig(
        invalid_threshold=args.judge_invalid_threshold,
        ensemble_mode=args.judge_ensemble_mode,
    )

    rows: list[dict[str, object]] = []
    base_traces: list[dict[str, object]] = []
    if args.base_traces_json:
        cached_samples = load_cached_base_traces(args.base_traces_json)
        samples = [{"question": row["question"], "answer": row["answer"]} for row in cached_samples]
        base_traces = [
            {
                "dataset": args.dataset,
                "sample_id": row["sample_id"],
                "question": row["question"],
                "answer": row["answer"],
                "base_trace": row["base_trace"],
                "raw_generation": row["raw_generation"],
                "generation_style": args.generation_style,
                "reused_base_trace": True,
                "base_traces_source": args.base_traces_json,
            }
            for row in cached_samples
        ]
    else:
        samples = load_samples(args, rng)
        for sample_id, sample in enumerate(samples):
            base_trace, raw_generation, _ = sample_base_trace(
                runner=runner,
                question=sample["question"],
                generation_config=generation_config,
                seed=args.seed + sample_id,
            )
            base_traces.append(
                {
                    "dataset": args.dataset,
                    "sample_id": sample_id,
                    "question": sample["question"],
                    "answer": sample["answer"],
                    "base_trace": base_trace,
                    "raw_generation": raw_generation,
                    "generation_style": args.generation_style,
                    "reused_base_trace": False,
                    "base_traces_source": "",
                }
            )
    for sample_id, sample in enumerate(samples):
        base_entry = next(row for row in base_traces if int(row["sample_id"]) == sample_id)
        base_trace = list(base_entry["base_trace"])
        for prefix_length in select_decision_points(base_trace, max_points=args.max_decision_points):
            prefix_lines = base_trace[:prefix_length]
            candidates = [("base", prefix_lines)]
            if args.augment_revise_prefixes:
                perturbed = make_recoverable_prefix(prefix_lines, rng)
                if perturbed is not None:
                    candidates.append(("perturbed_last_line", perturbed))

            for variant, candidate_prefix in candidates:
                used_tokens = runner.count_tokens("\n".join(candidate_prefix[1:])) if len(candidate_prefix) > 1 else 0
                budget_tokens = max(48, args.total_budget_tokens - used_tokens)
                record = estimate_prefix_oracle(
                    runner=runner,
                    judge_runner=judge_runner,
                    dataset_name=args.dataset,
                    sample_id=sample_id,
                    question=sample["question"],
                    gold_answer=sample["answer"],
                    prefix_lines=candidate_prefix,
                    budget_tokens=budget_tokens,
                    generation_config=generation_config,
                    utility_config=utility_config,
                    judge_config=judge_config,
                    seed=args.seed + 100 * sample_id + prefix_length + (13 if variant != "base" else 0),
                )
                rows.append(
                    {
                        "dataset": args.dataset,
                        "benchmark_tier": "judge_based_supporting",
                        "sample_id": record.sample_id,
                        "problem": record.problem,
                        "target": record.target,
                        "prefix_variant": variant,
                        "prefix_length": record.prefix_length,
                        "budget_tokens": record.budget_tokens,
                        "q_t": record.q_t,
                        "prefix_invalid": record.prefix_invalid,
                        "mu_continue": record.mu_continue,
                        "nu_continue": record.nu_continue,
                        "continue_utility": record.continue_utility,
                        "continue_std_utility": record.continue_std_utility,
                        "continue_wrong_rate": record.continue_wrong_rate,
                        "continue_mean_tokens": record.continue_mean_tokens,
                        "revise_utility": record.revise_utility,
                        "abstain_utility": record.abstain_utility,
                        "revise_gain": record.revise_gain,
                        "oracle_action": record.oracle_action,
                        "action_gap": record.action_gap,
                        "ambiguous": record.ambiguous,
                        "prefix_trace": " | ".join(record.prefix_lines),
                    }
                )

    write_records_csv(output_dir / "prefix_oracle_records.csv", rows)
    with (output_dir / "base_traces.json").open("w", encoding="utf-8") as handle:
        json.dump(base_traces, handle, ensure_ascii=False, indent=2)
    summary = build_summary(rows)
    summary.update(summarize_base_traces(base_traces))
    summary["dataset"] = args.dataset
    summary["benchmark_tier"] = "judge_based_supporting"
    summary["num_samples"] = args.num_samples
    summary["judge_ensemble_mode"] = args.judge_ensemble_mode
    summary["generation_style"] = args.generation_style
    summary["reused_base_trace"] = bool(args.base_traces_json)
    summary["base_traces_source"] = args.base_traces_json
    with (output_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
    (output_dir / "summary.txt").write_text(format_summary(summary), encoding="utf-8")
    print(format_summary(summary))


if __name__ == "__main__":
    main()
