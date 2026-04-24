from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import random

from triver.envs.arithmetic import ArithmeticEnv
from triver.envs.linear_equations import LinearEquationEnv
from triver.models.api_runner import runner_from_env
from triver.models.qwen_runner import QwenRunner
from triver.oracle.week1 import (
    GenerationConfig,
    UtilityConfig,
    estimate_prefix_oracle,
    sample_base_trace,
    select_decision_points,
)


CSV_FIELDS = [
    "env",
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
INT_FIELDS = {"sample_id", "prefix_length", "budget_tokens"}
FLOAT_FIELDS = {
    "q_t",
    "mu_continue",
    "nu_continue",
    "continue_utility",
    "continue_std_utility",
    "continue_wrong_rate",
    "continue_mean_tokens",
    "revise_utility",
    "abstain_utility",
    "revise_gain",
    "action_gap",
}
BOOL_FIELDS = {"prefix_invalid", "ambiguous"}
ENVS = {
    "arithmetic": ArithmeticEnv(),
    "linear_equations": LinearEquationEnv(),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run TriVer Week-1 oracle experiment.")
    parser.add_argument(
        "--backend",
        choices=("local", "api"),
        default="local",
        help="Generation backend for rollout/continue/revise execution.",
    )
    parser.add_argument(
        "--model-path",
        default="/cephfs/shared/hf_cache/hub/Qwen3-4B",
        help="Local HF model path. Also used as tokenizer fallback for API mode unless --tokenizer-path is set.",
    )
    parser.add_argument("--tokenizer-path", default="", help="Optional tokenizer path used for token counting in API mode.")
    parser.add_argument("--api-model", default=os.environ.get("TRIVER_API_MODEL", ""), help="OpenAI-compatible model/endpoint name for --backend api.")
    parser.add_argument("--api-base-url", default=os.environ.get("TRIVER_API_BASE_URL", ""), help="OpenAI-compatible base URL for --backend api.")
    parser.add_argument("--api-key", default=os.environ.get("TRIVER_API_KEY", ""), help="API key for --backend api. Prefer env vars in practice.")
    parser.add_argument("--api-timeout-sec", type=float, default=120.0, help="HTTP timeout in seconds for API mode.")
    parser.add_argument(
        "--env",
        choices=sorted(ENVS),
        default="arithmetic",
        help="Exact-checker environment to run.",
    )
    parser.add_argument("--num-samples", type=int, default=12)
    parser.add_argument("--num-rollouts", type=int, default=4)
    parser.add_argument("--max-decision-points", type=int, default=3)
    parser.add_argument("--total-budget-tokens", type=int, default=96)
    parser.add_argument("--step-max-new-tokens", type=int, default=24)
    parser.add_argument(
        "--prompt-style",
        choices=("default", "api_strict", "api_revise_focus", "api_revise_candidates", "api_revise_invalid_focus"),
        default="default",
        help="Prompt/action construction style for rollout generation.",
    )
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--top-p", type=float, default=0.9)
    parser.add_argument("--lambda-tok", type=float, default=0.002)
    parser.add_argument("--gamma-wrong", type=float, default=0.5)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument(
        "--augment-revise-prefixes",
        action="store_true",
        help="Inject controlled one-step prefix corruptions to cover recoverable revise states.",
    )
    parser.add_argument(
        "--recoverable-style",
        choices=("default", "local_changed_token"),
        default="default",
        help="Style used to perturb correct next lines when constructing recoverable revise prefixes.",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/week1_arithmetic",
        help="Where to save CSV/plots/summary.",
    )
    parser.add_argument(
        "--skip-plots",
        action="store_true",
        help="Skip plot generation. Useful inside envs without matplotlib.",
    )
    parser.add_argument(
        "--plot-only",
        action="store_true",
        help="Only read an existing CSV and render summary/plots.",
    )
    parser.add_argument(
        "--input-csv",
        default="",
        help="Existing prefix_oracle_records.csv path for --plot-only mode.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.plot_only:
        if not args.input_csv:
            raise ValueError("--plot-only requires --input-csv")
        rows = read_records_csv(Path(args.input_csv))
    else:
        rows, base_traces = run_generation_phase(args)
        write_records_csv(output_dir / "prefix_oracle_records.csv", rows)
        with (output_dir / "base_traces.json").open("w", encoding="utf-8") as handle:
            json.dump(base_traces, handle, ensure_ascii=False, indent=2)

    summary = build_summary(rows)
    with (output_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
    (output_dir / "summary.txt").write_text(format_summary(summary), encoding="utf-8")

    if rows and not args.skip_plots:
        try:
            plot_action_atlas(rows, output_dir / "oracle_action_atlas.png")
            plot_scalar_crossing(rows, output_dir / "scalar_crossing.png")
            plot_action_gap_histogram(rows, output_dir / "action_gap_histogram.png")
        except ModuleNotFoundError as error:
            if error.name != "matplotlib":
                raise
            print("Skipping plots because matplotlib is not installed.")

    print(format_summary(summary))


def run_generation_phase(args: argparse.Namespace) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rng = random.Random(args.seed)
    runner = build_runner(args)
    env = ENVS[args.env]
    generation_config = GenerationConfig(
        max_new_tokens=args.total_budget_tokens,
        step_max_new_tokens=args.step_max_new_tokens,
        num_rollouts=args.num_rollouts,
        temperature=args.temperature,
        top_p=args.top_p,
        prompt_style=args.prompt_style,
    )
    utility_config = UtilityConfig(
        lambda_tok=args.lambda_tok,
        gamma_wrong=args.gamma_wrong,
    )

    rows: list[dict[str, object]] = []
    base_traces: list[dict[str, object]] = []
    for sample_id in range(args.num_samples):
        sample = env.generate_sample(rng)
        base_trace, base_generations = sample_base_trace(
            runner=runner,
            env=env,
            sample=sample,
            generation_config=generation_config,
            seed=args.seed + sample_id,
        )
        base_traces.append(
            {
                "env": env.name,
                "sample_id": sample_id,
                "problem": env.problem_text(sample),
                "target": env.target_text(sample),
                "base_trace": base_trace,
                "raw_generations": base_generations,
            }
        )

        used_prefix_tokens = [0]
        running_trace = env.initial_trace(sample)
        for line in base_trace[1:]:
            running_trace.append(line)
            used_prefix_tokens.append(runner.count_tokens("\n".join(running_trace[1:])))

        for prefix_length in select_decision_points(env, base_trace, max_points=args.max_decision_points):
            prefix_lines = base_trace[:prefix_length]
            candidates = [("base", prefix_lines)]
            if args.augment_revise_prefixes:
                perturbed = env.make_recoverable_prefix(
                    prefix_lines,
                    sample,
                    rng,
                    recoverable_style=args.recoverable_style,
                )
                if perturbed is not None:
                    candidates.append(("perturbed_last_line", perturbed))

            for variant, candidate_prefix in candidates:
                used_tokens = runner.count_tokens("\n".join(candidate_prefix[1:])) if len(candidate_prefix) > 1 else 0
                budget_tokens = max(24, args.total_budget_tokens - used_tokens)
                record = estimate_prefix_oracle(
                    runner=runner,
                    env=env,
                    sample_id=sample_id,
                    sample=sample,
                    prefix_lines=candidate_prefix,
                    budget_tokens=budget_tokens,
                    generation_config=generation_config,
                    utility_config=utility_config,
                    seed=args.seed + 101 * sample_id + prefix_length + (13 if variant != "base" else 0),
                )
                rows.append(
                    {
                        "env": record.env_name,
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
    return rows, base_traces


def build_runner(args: argparse.Namespace):
    if args.backend == "local":
        return QwenRunner(model_path=args.model_path)
    tokenizer_path = args.tokenizer_path or args.model_path
    return runner_from_env(
        model=args.api_model,
        api_key=args.api_key,
        base_url=args.api_base_url,
        tokenizer_path=tokenizer_path,
        timeout_sec=args.api_timeout_sec,
    )


def write_records_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def read_records_csv(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw_row in reader:
            row: dict[str, object] = {}
            for key, value in raw_row.items():
                if value is None:
                    row[key] = value
                elif key in INT_FIELDS:
                    row[key] = int(value)
                elif key in FLOAT_FIELDS:
                    row[key] = float(value)
                elif key in BOOL_FIELDS:
                    row[key] = value.lower() == "true"
                else:
                    row[key] = value
            rows.append(row)
    return rows


def build_summary(rows: list[dict[str, object]]) -> dict[str, float | int]:
    if not rows:
        return {
            "num_prefixes": 0,
            "oracle_determinacy_rate": 0.0,
            "crossing_mass_all": 0.0,
            "crossing_mass_high_determinacy": 0.0,
            "invalid_prefix_rate": 0.0,
            "mean_action_gap": 0.0,
        }
    high_det = [row for row in rows if not bool(row["ambiguous"])]
    return {
        "num_prefixes": len(rows),
        "oracle_determinacy_rate": sum(not bool(row["ambiguous"]) for row in rows) / len(rows),
        "crossing_mass_all": compute_crossing_mass(rows),
        "crossing_mass_high_determinacy": compute_crossing_mass(high_det),
        "invalid_prefix_rate": sum(bool(row["prefix_invalid"]) for row in rows) / len(rows),
        "mean_action_gap": sum(float(row["action_gap"]) for row in rows) / len(rows),
    }


def compute_crossing_mass(rows: list[dict[str, object]], bins: int = 8) -> float:
    if not rows:
        return 0.0

    bin_actions: dict[int, set[str]] = {bin_index: set() for bin_index in range(bins)}
    row_bins: list[int] = []
    for row in rows:
        score = float(row["mu_continue"])
        clipped = min(max(score, 0.0), 1.0)
        bin_index = min(bins - 1, int(clipped * bins))
        row_bins.append(bin_index)
        bin_actions[bin_index].add(str(row["oracle_action"]))

    crossing_count = 0
    for row_bin in row_bins:
        if len(bin_actions[row_bin]) > 1:
            crossing_count += 1
    return crossing_count / len(rows)


def plot_action_atlas(rows: list[dict[str, object]], path: Path) -> None:
    import matplotlib.pyplot as plt

    colors = {"continue": "#1f77b4", "revise_1": "#d62728", "abstain": "#2ca02c"}
    jitter_rng = random.Random(0)
    jitter = [jitter_rng.uniform(-0.06, 0.06) for _ in rows]
    fig, ax = plt.subplots(figsize=(8, 5))
    for action in colors:
        for ambiguous in (False, True):
            xs = []
            ys = []
            sizes = []
            for index, row in enumerate(rows):
                if row["oracle_action"] != action or bool(row["ambiguous"]) != ambiguous:
                    continue
                xs.append(float(row["q_t"]) + jitter[index])
                ys.append(float(row["revise_gain"]))
                sizes.append(40 + 120 * float(row["mu_continue"]))
            if xs:
                ax.scatter(
                    xs,
                    ys,
                    s=sizes,
                    c=colors[action],
                    alpha=0.35 if ambiguous else 0.85,
                    edgecolors="black",
                    linewidths=0.4,
                    label=action if not ambiguous else None,
                )
    ax.set_xlabel("q_t: exact local invalidity risk")
    ax.set_ylabel("revise_gain = U(revise_1) - U(continue)")
    ax.set_title("Oracle Action Atlas on Arithmetic Exact-Checker Domain")
    ax.set_xlim(-0.15, 1.15)
    ax.axvline(0.5, color="gray", linestyle="--", linewidth=0.8, alpha=0.6)
    ax.legend()
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def plot_scalar_crossing(rows: list[dict[str, object]], path: Path) -> None:
    import matplotlib.pyplot as plt

    colors = {"continue": "#1f77b4", "revise_1": "#d62728", "abstain": "#2ca02c"}
    fig, ax = plt.subplots(figsize=(8, 5))
    for action in colors:
        for ambiguous in (False, True):
            xs = []
            ys = []
            for row in rows:
                if row["oracle_action"] != action or bool(row["ambiguous"]) != ambiguous:
                    continue
                xs.append(float(row["mu_continue"]))
                ys.append(float(row["revise_gain"]))
            if xs:
                ax.scatter(
                    xs,
                    ys,
                    c=colors[action],
                    alpha=0.35 if ambiguous else 0.85,
                    edgecolors="black",
                    linewidths=0.4,
                    s=70,
                    label=action if not ambiguous else None,
                )
    ax.set_xlabel("Scalar score s_t = mu_continue")
    ax.set_ylabel("revise_gain = U(revise_1) - U(continue)")
    ax.set_title("Scalar Crossing View")
    ax.grid(alpha=0.2)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def plot_action_gap_histogram(rows: list[dict[str, object]], path: Path) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(
        [float(row["action_gap"]) for row in rows],
        bins=12,
        color="#4c78a8",
        edgecolor="black",
        alpha=0.85,
    )
    ax.set_xlabel("top-1 minus top-2 action utility gap")
    ax.set_ylabel("count")
    ax.set_title("Oracle Action Gap Histogram")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def format_summary(summary: dict[str, float | int]) -> str:
    lines = ["TriVer Week-1 summary"]
    for key, value in summary.items():
        if isinstance(value, float):
            lines.append(f"- {key}: {value:.4f}")
        else:
            lines.append(f"- {key}: {value}")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
