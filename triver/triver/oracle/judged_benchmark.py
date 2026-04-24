from __future__ import annotations

from dataclasses import dataclass
import json
import math
import random
import re
import statistics
from typing import Any, Sequence


ACTIONS = ("continue", "revise_1", "abstain")


@dataclass(frozen=True)
class UtilityConfig:
    lambda_tok: float = 0.002
    gamma_wrong: float = 0.5


@dataclass(frozen=True)
class GenerationConfig:
    max_new_tokens: int = 160
    num_rollouts: int = 2
    temperature: float = 0.0
    top_p: float = 0.9
    style: str = "default"


@dataclass(frozen=True)
class JudgeConfig:
    invalid_threshold: float = 0.5
    ensemble_mode: str = "single"


@dataclass(frozen=True)
class JudgedRollout:
    action: str
    utility: float
    success: bool
    unsafe_wrong: bool
    new_tokens: int
    full_trace: list[str]
    raw_text: str
    extracted_final_answer: str
    judge_raw: str


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
    rollouts: list[JudgedRollout]


@dataclass(frozen=True)
class PrefixOracleRecord:
    dataset_name: str
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


def extract_gsm8k_answer(answer_text: str) -> str:
    match = re.search(r"####\s*(.+)$", answer_text, flags=re.MULTILINE)
    if match:
        return match.group(1).strip()
    lines = [line.strip() for line in answer_text.splitlines() if line.strip()]
    return lines[-1] if lines else answer_text.strip()


def normalize_trace_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip().strip("`")
        if not line:
            continue
        line = re.sub(r"^(step|line)\s*\d+\s*[:.)-]\s*", "", line, flags=re.IGNORECASE)
        line = re.sub(r"^-+\s*", "", line)
        lines.append(line)
        if is_terminal_line(line):
            break
    return lines


def is_terminal_line(line: str) -> bool:
    return line.lower().startswith("final answer:")


def merge_generated_trace(prefix_lines: list[str], generated_lines: list[str]) -> list[str]:
    if not generated_lines:
        return list(prefix_lines)
    max_overlap = min(len(prefix_lines), len(generated_lines))
    for overlap in range(max_overlap, 0, -1):
        if prefix_lines[-overlap:] == generated_lines[:overlap]:
            return list(prefix_lines) + generated_lines[overlap:]
    return list(prefix_lines) + generated_lines


def select_decision_points(trace_lines: list[str], max_points: int = 2) -> list[int]:
    eligible = [
        prefix_length
        for prefix_length in range(2, len(trace_lines) + 1)
        if not is_terminal_line(trace_lines[prefix_length - 1])
    ]
    if len(eligible) <= max_points:
        return eligible
    selected: list[int] = []
    for index in range(max_points):
        position = round(index * (len(eligible) - 1) / (max_points - 1))
        selected.append(eligible[position])
    return sorted(set(selected))


def make_recoverable_prefix(prefix_lines: list[str], rng: random.Random) -> list[str] | None:
    if len(prefix_lines) < 3:
        return None
    target = prefix_lines[-1]
    matches = list(re.finditer(r"-?\d+(?:\.\d+)?", target))
    if not matches:
        return None
    match = matches[-1]
    token = match.group(0)
    replacement = str(int(float(token)) + rng.choice([-2, -1, 1, 2]))
    corrupted = f"{target[:match.start()]}{replacement}{target[match.end():]}"
    if corrupted == target:
        return None
    return list(prefix_lines[:-1]) + [corrupted]


def build_base_messages(question: str, style: str = "default") -> list[dict[str, str]]:
    if style == "default":
        system = (
            "Solve the math word problem step by step.\n"
            "Rules:\n"
            "- Write one short reasoning step per line.\n"
            "- Do not use bullets or markdown.\n"
            "- End with exactly one line in the format 'Final answer: <answer>'."
        )
        user = f"Problem:\n{question}\n\nSolve it."
    elif style == "compact_final":
        system = (
            "Solve the math word problem with a short plain-text trace.\n"
            "Rules:\n"
            "- Use plain text only; do not use LaTeX, bullets, or markdown.\n"
            "- Write at most 6 short reasoning lines before the final answer.\n"
            "- Each line should be a complete sentence or equation.\n"
            "- End with exactly one line in the format 'Final answer: <answer>'.\n"
            "- Do not stop early or leave the last line unfinished."
        )
        user = f"Problem:\n{question}\n\nGive a concise complete solution."
    else:
        raise ValueError(f"Unsupported generation style: {style}")
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def build_action_messages(
    question: str,
    prefix_lines: list[str],
    action: str,
    style: str = "default",
) -> tuple[list[dict[str, str]], list[str]]:
    if action == "continue":
        action_prefix = prefix_lines
        instruction = "Continue the current reasoning trace from the visible prefix below."
    elif action == "revise_1":
        action_prefix = prefix_lines[:-1]
        removed = prefix_lines[-1]
        instruction = (
            "The omitted last line from the original trace may be wrong and has been rolled back.\n"
            "Replace it by continuing correctly from the rollback prefix below."
        )
    else:
        raise ValueError(f"Unsupported action: {action}")

    trace_block = "\n".join(action_prefix[1:])
    user_lines = [f"Problem:\n{question}", instruction, f"Visible trace:\n{trace_block}"]
    if action == "revise_1":
        user_lines.append(f"Removed line:\n{removed}")
    if style == "default":
        system = (
            "You continue or repair a math solution trace.\n"
            "Keep previous visible lines fixed.\n"
            "Output only the missing continuation lines.\n"
            "End with exactly one line in the format 'Final answer: <answer>'."
        )
        user_lines.append("Output only continuation lines, one per line, and end with 'Final answer: <answer>'.")
    elif style == "compact_final":
        system = (
            "You continue or repair a short math solution trace.\n"
            "Keep previous visible lines fixed.\n"
            "Use plain text only; no LaTeX, bullets, or markdown.\n"
            "Output only the missing continuation lines.\n"
            "Write at most 4 short lines before the final answer.\n"
            "End with exactly one line in the format 'Final answer: <answer>'.\n"
            "Do not stop early or leave the last line unfinished."
        )
        user_lines.append(
            "Output only the missing continuation lines in plain text, keep them short, "
            "and end with 'Final answer: <answer>'."
        )
    else:
        raise ValueError(f"Unsupported generation style: {style}")
    return (
        [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": "\n\n".join(user_lines),
            },
        ],
        action_prefix,
    )


def build_prefix_risk_messages(
    question: str,
    gold_answer: str,
    prefix_lines: list[str],
    style: str = "strict_process",
) -> list[dict[str, str]]:
    trace_block = "\n".join(prefix_lines[1:])
    if style == "strict_process":
        system = (
            "You are a strict process judge for math reasoning.\n"
            "Estimate how likely it is that the current reasoning prefix already contains a substantive error\n"
            "that would likely prevent a correct completion without revision.\n"
            "Return JSON only: {\"risk\": <float between 0 and 1>}."
        )
    elif style == "revision_need":
        system = (
            "You are a verifier for partial math solutions.\n"
            "Estimate the probability that the current prefix should be revised rather than simply continued.\n"
            "High risk means the prefix likely contains a material mistake or misleading step.\n"
            "Return JSON only: {\"risk\": <float between 0 and 1>}."
        )
    else:
        raise ValueError(f"Unsupported prefix-risk judge style: {style}")
    return [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": (
                f"Problem:\n{question}\n\n"
                f"Gold final answer:\n{gold_answer}\n\n"
                f"Current prefix:\n{trace_block}\n\n"
                "Return JSON only."
            ),
        },
    ]


def build_correctness_judge_messages(
    question: str,
    gold_answer: str,
    full_trace: list[str],
    style: str = "strict_grade",
) -> list[dict[str, str]]:
    trace_block = "\n".join(full_trace[1:])
    if style == "strict_grade":
        system = (
            "You are a strict grader for grade-school math solutions.\n"
            "Decide whether the candidate final answer is mathematically equivalent to the gold answer.\n"
            "Return JSON only with keys:\n"
            "- correct: 0 or 1\n"
            "- extracted_final_answer: short string\n"
            "- final_answer_present: 0 or 1"
        )
    elif style == "extract_then_compare":
        system = (
            "You are a careful answer extractor and comparer for math solutions.\n"
            "First identify the candidate final answer, then decide whether it matches the gold answer.\n"
            "If the trace does not end with a clear final answer, set final_answer_present to 0.\n"
            "Return JSON only with keys:\n"
            "- correct: 0 or 1\n"
            "- extracted_final_answer: short string\n"
            "- final_answer_present: 0 or 1"
        )
    else:
        raise ValueError(f"Unsupported correctness judge style: {style}")
    return [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": (
                f"Problem:\n{question}\n\n"
                f"Gold final answer:\n{gold_answer}\n\n"
                f"Candidate solution:\n{trace_block}\n\n"
                "Return JSON only."
            ),
        },
    ]


def parse_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return json.loads(stripped)
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        return json.loads(match.group(0))
    raise ValueError(f"Could not parse JSON object from judge text: {text[:200]!r}")


def judge_prefix_risk(
    judge_runner,
    judge_config: JudgeConfig,
    question: str,
    gold_answer: str,
    prefix_lines: list[str],
    seed: int,
) -> float:
    styles = ["strict_process"]
    if judge_config.ensemble_mode in {"dual", "dual_consensus"}:
        styles.append("revision_need")
    risks: list[float] = []
    for style_index, style in enumerate(styles):
        result = judge_runner.generate(
            prompt=build_prefix_risk_messages(question, gold_answer, prefix_lines, style=style),
            max_new_tokens=64,
            num_return_sequences=1,
            temperature=0.0,
            top_p=1.0,
            seed=seed + style_index,
        )[0]
        payload = parse_json_object(result.text)
        risk = float(payload.get("risk", 0.5))
        risks.append(min(max(risk, 0.0), 1.0))
    return statistics.fmean(risks)


def judge_correctness(
    judge_runner,
    judge_config: JudgeConfig,
    question: str,
    gold_answer: str,
    full_trace: list[str],
    seed: int,
) -> tuple[bool, bool, str, str]:
    styles = ["strict_grade"]
    if judge_config.ensemble_mode in {"dual", "dual_consensus"}:
        styles.append("extract_then_compare")
    correctness_votes: list[int] = []
    present_votes: list[int] = []
    extracted_answers: list[str] = []
    judge_texts: list[str] = []
    for style_index, style in enumerate(styles):
        result = judge_runner.generate(
            prompt=build_correctness_judge_messages(question, gold_answer, full_trace, style=style),
            max_new_tokens=96,
            num_return_sequences=1,
            temperature=0.0,
            top_p=1.0,
            seed=seed + style_index,
        )[0]
        judge_texts.append(f"[{style}]\n{result.text}")
        payload = parse_json_object(result.text)
        correctness_votes.append(int(payload.get("correct", 0)))
        present_votes.append(int(payload.get("final_answer_present", 0)))
        extracted = str(payload.get("extracted_final_answer", "")).strip()
        if extracted:
            extracted_answers.append(extracted)
    if judge_config.ensemble_mode == "dual_consensus":
        correct = all(vote == 1 for vote in correctness_votes)
        final_answer_present = all(vote == 1 for vote in present_votes)
    else:
        correct = statistics.fmean(correctness_votes) >= 0.5
        final_answer_present = statistics.fmean(present_votes) >= 0.5
    extracted = extracted_answers[0] if extracted_answers else ""
    return correct, final_answer_present, extracted, "\n---\n".join(judge_texts)


def sample_base_trace(runner, question: str, generation_config: GenerationConfig, seed: int) -> tuple[list[str], str, int]:
    generation = runner.generate(
        prompt=build_base_messages(question, style=generation_config.style),
        max_new_tokens=generation_config.max_new_tokens,
        num_return_sequences=1,
        temperature=generation_config.temperature,
        top_p=generation_config.top_p,
        seed=seed,
    )[0]
    trace = ["Question: " + question] + normalize_trace_lines(generation.text)
    return trace, generation.text, generation.new_tokens


def rollout_action(
    runner,
    question: str,
    prefix_lines: list[str],
    action: str,
    budget_tokens: int,
    generation_config: GenerationConfig,
    seed: int,
) -> tuple[list[str], int, str]:
    prompt, action_prefix = build_action_messages(question, prefix_lines, action, style=generation_config.style)
    generation = runner.generate(
        prompt=prompt,
        max_new_tokens=budget_tokens,
        num_return_sequences=1,
        temperature=generation_config.temperature,
        top_p=generation_config.top_p,
        seed=seed,
    )[0]
    generated_lines = normalize_trace_lines(generation.text)
    full_trace = merge_generated_trace(action_prefix, generated_lines)
    return full_trace, generation.new_tokens, generation.text


def estimate_prefix_oracle(
    runner,
    judge_runner,
    dataset_name: str,
    sample_id: int,
    question: str,
    gold_answer: str,
    prefix_lines: list[str],
    budget_tokens: int,
    generation_config: GenerationConfig,
    utility_config: UtilityConfig,
    judge_config: JudgeConfig,
    seed: int,
) -> PrefixOracleRecord:
    q_t = judge_prefix_risk(judge_runner, judge_config, question, gold_answer, prefix_lines, seed=seed + 7)
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

        raw_rollouts = [
            rollout_action(
                runner=runner,
                question=question,
                prefix_lines=prefix_lines,
                action=action,
                budget_tokens=max(32, budget_tokens),
                generation_config=generation_config,
                seed=seed + 101 * (action_index + 1) + rollout_index,
            )
            for rollout_index in range(generation_config.num_rollouts)
        ]
        action_estimates[action] = summarize_action(
            judge_runner=judge_runner,
            judge_config=judge_config,
            question=question,
            gold_answer=gold_answer,
            action=action,
            raw_rollouts=raw_rollouts,
            utility_config=utility_config,
            seed=seed + 1000 * (action_index + 1),
        )

    continue_est = action_estimates["continue"]
    revise_est = action_estimates["revise_1"]
    ranked = sorted(action_estimates.values(), key=lambda estimate: estimate.mean_utility, reverse=True)
    top, second = ranked[0], ranked[1]
    action_gap = top.mean_utility - second.mean_utility
    ambiguous = action_gap < 0.05 or ci_overlap(top, second)
    posterior_alpha = 1.0 + continue_est.success_count
    posterior_beta = 1.0 + (continue_est.rollout_count - continue_est.success_count)
    posterior_total = posterior_alpha + posterior_beta
    mu_continue = posterior_alpha / posterior_total
    nu_continue = (posterior_alpha * posterior_beta) / ((posterior_total**2) * (posterior_total + 1.0))
    return PrefixOracleRecord(
        dataset_name=dataset_name,
        sample_id=sample_id,
        problem=question,
        target=gold_answer,
        prefix_lines=list(prefix_lines),
        prefix_length=len(prefix_lines),
        budget_tokens=budget_tokens,
        q_t=q_t,
        prefix_invalid=q_t >= judge_config.invalid_threshold,
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


def summarize_action(
    judge_runner,
    judge_config: JudgeConfig,
    question: str,
    gold_answer: str,
    action: str,
    raw_rollouts: list[tuple[list[str], int, str]],
    utility_config: UtilityConfig,
    seed: int,
) -> ActionEstimate:
    rollouts = [
        build_rollout_record(
            judge_runner=judge_runner,
            judge_config=judge_config,
            question=question,
            gold_answer=gold_answer,
            action=action,
            full_trace=full_trace,
            total_new_tokens=total_new_tokens,
            raw_text=raw_text,
            utility_config=utility_config,
            seed=seed + index,
        )
        for index, (full_trace, total_new_tokens, raw_text) in enumerate(raw_rollouts)
    ]
    utilities = [rollout.utility for rollout in rollouts]
    successes = [1.0 if rollout.success else 0.0 for rollout in rollouts]
    wrongs = [1.0 if rollout.unsafe_wrong else 0.0 for rollout in rollouts]
    tokens = [rollout.new_tokens for rollout in rollouts]
    std = 0.0 if len(utilities) <= 1 else statistics.stdev(utilities)
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


def build_rollout_record(
    judge_runner,
    judge_config: JudgeConfig,
    question: str,
    gold_answer: str,
    action: str,
    full_trace: list[str],
    total_new_tokens: int,
    raw_text: str,
    utility_config: UtilityConfig,
    seed: int,
) -> JudgedRollout:
    success, final_answer_present, extracted, judge_raw = judge_correctness(
        judge_runner=judge_runner,
        judge_config=judge_config,
        question=question,
        gold_answer=gold_answer,
        full_trace=full_trace,
        seed=seed,
    )
    unsafe_wrong = final_answer_present and not success
    utility = (1.0 if success else 0.0) - utility_config.lambda_tok * total_new_tokens
    if unsafe_wrong:
        utility -= utility_config.gamma_wrong
    return JudgedRollout(
        action=action,
        utility=utility,
        success=success,
        unsafe_wrong=unsafe_wrong,
        new_tokens=total_new_tokens,
        full_trace=full_trace,
        raw_text=raw_text,
        extracted_final_answer=extracted,
        judge_raw=judge_raw,
    )


def ci_overlap(first: ActionEstimate, second: ActionEstimate) -> bool:
    first_low = first.mean_utility - first.ci95
    first_high = first.mean_utility + first.ci95
    second_low = second.mean_utility - second.ci95
    second_high = second.mean_utility + second.ci95
    return not (first_low > second_high or second_low > first_high)


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
    crossing_count = sum(1 for row_bin in row_bins if len(bin_actions[row_bin]) > 1)
    return crossing_count / len(rows)


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


def format_summary(summary: dict[str, float | int]) -> str:
    return "\n".join(
        [
            "TriVer judged-benchmark summary",
            f"- num_prefixes: {summary['num_prefixes']}",
            f"- oracle_determinacy_rate: {summary['oracle_determinacy_rate']:.4f}",
            f"- crossing_mass_all: {summary['crossing_mass_all']:.4f}",
            f"- crossing_mass_high_determinacy: {summary['crossing_mass_high_determinacy']:.4f}",
            f"- invalid_prefix_rate: {summary['invalid_prefix_rate']:.4f}",
            f"- mean_action_gap: {summary['mean_action_gap']:.4f}",
        ]
    )
