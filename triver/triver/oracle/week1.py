from __future__ import annotations

from dataclasses import dataclass
import math
import statistics
from typing import Any

from triver.envs.common import ExactCheckerEnv, TraceEvaluation
from triver.models.qwen_runner import QwenRunner


ACTIONS = ("continue", "revise_1", "abstain")


@dataclass(frozen=True)
class UtilityConfig:
    lambda_tok: float = 0.002
    gamma_wrong: float = 0.5


@dataclass(frozen=True)
class GenerationConfig:
    max_new_tokens: int = 96
    step_max_new_tokens: int = 24
    num_rollouts: int = 4
    temperature: float = 0.7
    top_p: float = 0.9
    prompt_style: str = "default"


@dataclass(frozen=True)
class RolloutRecord:
    action: str
    utility: float
    success: bool
    unsafe_wrong: bool
    new_tokens: int
    full_trace: list[str]
    trace_evaluation: TraceEvaluation
    raw_text: str


@dataclass(frozen=True)
class ActionEstimate:
    action: str
    mean_utility: float
    std_utility: float
    ci95: float
    success_rate: float
    success_count: int
    rollout_count: int
    wrong_rate: float
    mean_tokens: float
    rollouts: list[RolloutRecord]


@dataclass(frozen=True)
class PrefixOracleRecord:
    env_name: str
    sample_id: int
    problem: str
    target: str
    prefix_lines: list[str]
    prefix_length: int
    budget_tokens: int
    q_t: float
    prefix_invalid: bool
    mu_continue: float
    nu_continue: float
    continue_utility: float
    continue_std_utility: float
    continue_wrong_rate: float
    continue_mean_tokens: float
    revise_utility: float
    abstain_utility: float
    revise_gain: float
    oracle_action: str
    action_gap: float
    ambiguous: bool
    action_estimates: dict[str, ActionEstimate]


def build_solver_prompt(
    env: ExactCheckerEnv,
    sample: Any,
    prefix_lines: list[str],
    action: str,
    prompt_style: str = "default",
) -> tuple[list[dict[str, str]], list[str]]:
    if action not in ACTIONS:
        raise ValueError(f"Unsupported action: {action}")
    if action == "abstain":
        raise ValueError("abstain does not require a generation prompt")
    return env.build_solver_messages(sample, prefix_lines, action, prompt_style=prompt_style)


def merge_generated_trace(prefix_lines: list[str], generated_lines: list[str]) -> list[str]:
    if not generated_lines:
        return list(prefix_lines)
    max_overlap = min(len(prefix_lines), len(generated_lines))
    for overlap in range(max_overlap, 0, -1):
        if prefix_lines[:overlap] == generated_lines[:overlap]:
            return list(prefix_lines) + generated_lines[overlap:]
    for overlap in range(max_overlap, 0, -1):
        if prefix_lines[-overlap:] == generated_lines[:overlap]:
            return list(prefix_lines) + generated_lines[overlap:]
    return list(prefix_lines) + generated_lines


def select_decision_points(
    env: ExactCheckerEnv,
    trace_lines: list[str],
    max_points: int = 3,
) -> list[int]:
    eligible = [
        prefix_length
        for prefix_length in range(2, len(trace_lines) + 1)
        if not env.is_terminal_line(trace_lines[prefix_length - 1])
    ]
    if len(eligible) <= max_points:
        return eligible
    selected: list[int] = []
    for index in range(max_points):
        position = round(index * (len(eligible) - 1) / (max_points - 1))
        selected.append(eligible[position])
    return sorted(set(selected))


def sample_base_trace(
    runner: QwenRunner,
    env: ExactCheckerEnv,
    sample: Any,
    generation_config: GenerationConfig,
    seed: int,
) -> tuple[list[str], list[str]]:
    trace, _, raw_steps = _rollout_policy(
        runner=runner,
        env=env,
        sample=sample,
        action_prefix=env.initial_trace(sample),
        budget_tokens=generation_config.max_new_tokens,
        generation_config=generation_config,
        seed=seed,
    )
    return trace, raw_steps


def estimate_prefix_oracle(
    runner: QwenRunner,
    env: ExactCheckerEnv,
    sample_id: int,
    sample: Any,
    prefix_lines: list[str],
    budget_tokens: int,
    generation_config: GenerationConfig,
    utility_config: UtilityConfig,
    seed: int,
) -> PrefixOracleRecord:
    action_estimates: dict[str, ActionEstimate] = {}
    for action_index, action in enumerate(ACTIONS):
        if action == "abstain":
            action_estimates[action] = ActionEstimate(
                action=action,
                mean_utility=0.0,
                std_utility=0.0,
                ci95=0.0,
                success_rate=0.0,
                success_count=0,
                rollout_count=0,
                wrong_rate=0.0,
                mean_tokens=0.0,
                rollouts=[],
            )
            continue

        _, action_prefix = build_solver_prompt(
            env,
            sample,
            prefix_lines,
            action,
            prompt_style=generation_config.prompt_style,
        )
        raw_rollouts = [
            _rollout_policy(
                runner=runner,
                env=env,
                sample=sample,
                action_prefix=action_prefix,
                budget_tokens=max(8, budget_tokens),
                generation_config=generation_config,
                seed=seed + 17 * (action_index + 1) + rollout_index,
            )
            for rollout_index in range(generation_config.num_rollouts)
        ]
        action_estimates[action] = _summarize_action(action, env, sample, raw_rollouts, utility_config)

    continue_est = action_estimates["continue"]
    revise_est = action_estimates["revise_1"]
    ranked = sorted(action_estimates.values(), key=lambda estimate: estimate.mean_utility, reverse=True)
    top, second = ranked[0], ranked[1]
    action_gap = top.mean_utility - second.mean_utility
    ambiguous = action_gap < 0.05 or _ci_overlap(top, second)
    prefix_eval = env.check_trace(prefix_lines, sample)
    posterior_alpha = 1.0 + continue_est.success_count
    posterior_beta = 1.0 + (continue_est.rollout_count - continue_est.success_count)
    posterior_total = posterior_alpha + posterior_beta
    mu_continue = posterior_alpha / posterior_total
    nu_continue = (posterior_alpha * posterior_beta) / (
        (posterior_total**2) * (posterior_total + 1.0)
    )
    return PrefixOracleRecord(
        env_name=env.name,
        sample_id=sample_id,
        problem=env.problem_text(sample),
        target=env.target_text(sample),
        prefix_lines=list(prefix_lines),
        prefix_length=len(prefix_lines),
        budget_tokens=budget_tokens,
        q_t=env.prefix_invalidity_risk(prefix_lines, sample),
        prefix_invalid=prefix_eval.prefix_invalid,
        mu_continue=mu_continue,
        nu_continue=nu_continue,
        continue_utility=continue_est.mean_utility,
        continue_std_utility=continue_est.std_utility,
        continue_wrong_rate=continue_est.wrong_rate,
        continue_mean_tokens=continue_est.mean_tokens,
        revise_utility=revise_est.mean_utility,
        abstain_utility=action_estimates["abstain"].mean_utility,
        revise_gain=revise_est.mean_utility - continue_est.mean_utility,
        oracle_action=top.action,
        action_gap=action_gap,
        ambiguous=ambiguous,
        action_estimates=action_estimates,
    )


def _rollout_policy(
    runner: QwenRunner,
    env: ExactCheckerEnv,
    sample: Any,
    action_prefix: list[str],
    budget_tokens: int,
    generation_config: GenerationConfig,
    seed: int,
) -> tuple[list[str], int, list[str]]:
    trace = list(action_prefix)
    raw_steps: list[str] = []
    total_new_tokens = 0
    step = 0
    while (
        total_new_tokens < budget_tokens
        and step < generation_config.max_new_tokens
        and not env.is_terminal_line(trace[-1])
    ):
        prompt, visible_prefix = build_solver_prompt(
            env,
            sample,
            trace,
            "continue",
            prompt_style=generation_config.prompt_style,
        )
        generation = runner.generate(
            prompt=prompt,
            max_new_tokens=min(generation_config.step_max_new_tokens, budget_tokens - total_new_tokens),
            num_return_sequences=1,
            temperature=generation_config.temperature,
            top_p=generation_config.top_p,
            seed=seed + step,
        )[0]
        raw_steps.append(generation.text)
        generated_lines = env.extract_trace_lines(generation.text)
        merged_trace = merge_generated_trace(visible_prefix, generated_lines)
        appended = merged_trace[len(visible_prefix) :]
        if not appended:
            break
        trace.append(appended[0])
        total_new_tokens += generation.new_tokens
        step += 1
    return trace, total_new_tokens, raw_steps


def _summarize_action(
    action: str,
    env: ExactCheckerEnv,
    sample: Any,
    raw_rollouts: list[tuple[list[str], int, list[str]]],
    utility_config: UtilityConfig,
) -> ActionEstimate:
    rollouts = [
        _build_rollout_record(
            env=env,
            sample=sample,
            action=action,
            full_trace=full_trace,
            total_new_tokens=total_new_tokens,
            raw_steps=raw_steps,
            utility_config=utility_config,
        )
        for full_trace, total_new_tokens, raw_steps in raw_rollouts
    ]
    utilities = [rollout.utility for rollout in rollouts]
    successes = [1.0 if rollout.success else 0.0 for rollout in rollouts]
    wrongs = [1.0 if rollout.unsafe_wrong else 0.0 for rollout in rollouts]
    tokens = [rollout.new_tokens for rollout in rollouts]
    if len(utilities) == 1:
        std = 0.0
    else:
        std = statistics.stdev(utilities)
    ci95 = 0.0 if not utilities else 1.96 * std / math.sqrt(len(utilities))
    return ActionEstimate(
        action=action,
        mean_utility=statistics.fmean(utilities) if utilities else 0.0,
        std_utility=std,
        ci95=ci95,
        success_rate=statistics.fmean(successes) if successes else 0.0,
        success_count=int(sum(successes)),
        rollout_count=len(rollouts),
        wrong_rate=statistics.fmean(wrongs) if wrongs else 0.0,
        mean_tokens=statistics.fmean(tokens) if tokens else 0.0,
        rollouts=rollouts,
    )


def _build_rollout_record(
    env: ExactCheckerEnv,
    sample: Any,
    action: str,
    full_trace: list[str],
    total_new_tokens: int,
    raw_steps: list[str],
    utility_config: UtilityConfig,
) -> RolloutRecord:
    trace_eval = env.check_trace(full_trace, sample)
    unsafe_wrong = trace_eval.final_answer is not None and not trace_eval.success
    utility = (1.0 if trace_eval.success else 0.0) - utility_config.lambda_tok * total_new_tokens
    if unsafe_wrong:
        utility -= utility_config.gamma_wrong
    return RolloutRecord(
        action=action,
        utility=utility,
        success=trace_eval.success,
        unsafe_wrong=unsafe_wrong,
        new_tokens=total_new_tokens,
        full_trace=full_trace,
        trace_evaluation=trace_eval,
        raw_text="\n---\n".join(raw_steps),
    )


def _ci_overlap(first: ActionEstimate, second: ActionEstimate) -> bool:
    first_low = first.mean_utility - first.ci95
    first_high = first.mean_utility + first.ci95
    second_low = second.mean_utility - second.ci95
    second_high = second.mean_utility + second.ci95
    return not (first_low > second_high or second_low > first_high)
