#!/usr/bin/env python3

import argparse
import json
import re
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
MAX_RETRIES = 4


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refine generated intervention candidates for a second-pass batch.")
    parser.add_argument(
        "--input",
        default="artifacts/object_gate/interventions/generated_candidates_v0.jsonl",
        help="Input generated-candidate JSONL.",
    )
    parser.add_argument(
        "--output",
        default="artifacts/object_gate/interventions/generated_candidates_v1.jsonl",
        help="Output refined-candidate JSONL.",
    )
    parser.add_argument(
        "--selection-reasons",
        default="first_step,only_segmented_step",
        help="Comma-separated selection_reason values to keep.",
    )
    parser.add_argument(
        "--family-filter",
        default="",
        help="Optional comma-separated family names to keep.",
    )
    return parser.parse_args()


def load_api_config() -> dict:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    return {
        "base_url": re.search(r"base_url:\s*(\S+)", readme).group(1),
        "endpoint": re.search(r"endpoint:\s*(\S+)", readme).group(1),
        "api_key": re.search(r"api_key:\s*(\S+)", readme).group(1),
    }


def parse_csv_arg(value: str) -> set[str]:
    return {item.strip() for item in value.split(",") if item.strip()}


def keep_row(row: dict, selection_reasons: set[str], families: set[str]) -> bool:
    if row["selection_reason"] not in selection_reasons:
        return False
    if families and row["family"] not in families:
        return False
    return True


def dedupe_rows(rows: list[dict]) -> list[dict]:
    kept = {}
    for row in rows:
        key = (row["family"], row["prompt_id"], row["step_index"], row["selection_reason"])
        current = kept.get(key)
        if current is None:
            kept[key] = row
            continue
        better = row["source_rollout_file"] < current["source_rollout_file"]
        if better:
            kept[key] = row
    return list(kept.values())


def build_user_prompt(row: dict) -> str:
    family = row["family"]
    step = row["step_text"]
    if family == "tower_of_hanoi":
        if normalize_text(step).startswith("check"):
            family_hint = (
                "Create a one-line distractor that sounds like a plausible Tower of Hanoi legality or goal check, "
                "but asserts one concretely wrong checking rule. Good error modes are: wrong_legality_rule, "
                "wrong_goal_check, ignore_source_target. It must not remain a correct check."
            )
            extra_rules = (
                "- Keep the same role as the selected step: a check or verification statement, not a plan.\n"
                "- Start it with 'Check:' or 'Verify:'.\n"
                "- The distractor must state a specific wrong rule or wrong success criterion.\n"
                "- Return strict JSON with fields: distractor, error_mode.\n"
            )
        else:
            family_hint = (
                "Create a one-line distractor that sounds like a plausible planning statement for Tower of Hanoi, "
                "but commits to one concrete wrong strategy choice. Good error modes are: wrong_split, "
                "ignore_extra_peg, move_largest_too_early, wrong_aux_peg, wrong_subgoal. "
                "It must not still be a correct planning step or a harmless elaboration of the original step."
            )
            extra_rules = (
                "- Keep the same role as the selected step: a planning statement.\n"
                "- Start it with 'Plan:'.\n"
                "- The distractor must state a specific wrong commitment, not just add vague detail.\n"
                "- If you mention Frame-Stewart, pair it with a clearly wrong split or subgoal.\n"
                "- Return strict JSON with fields: distractor, error_mode.\n"
            )
    elif family == "countdown":
        step_norm = normalize_text(step)
        if step_norm.startswith("check") or "used once" in step_norm or step_norm.startswith("verify"):
            family_hint = (
                "Create a one-line distractor that sounds like a plausible Countdown validity check, "
                "but states one concretely wrong checking rule. Good error modes are: allow_reuse, "
                "allow_omission, ignore_target_match. It must not remain a correct check."
            )
            extra_rules = (
                "- Keep the same role as the selected step: a check or verification statement, not a search step.\n"
                "- Start it with 'Check:' or 'Verify:'.\n"
                "- The distractor must allow an invalid solution pattern such as reusing a number, omitting a number, or accepting a near-miss target.\n"
                "- Return strict JSON with fields: distractor, error_mode.\n"
            )
        else:
            family_hint = (
                "Create a one-line distractor that sounds like a plausible initial Countdown planning step, "
                "but commits to one harmful wrong direction. Good error modes are: wrong_target, allow_reuse, "
                "misleading_intermediate. It must not be equivalent to the selected step."
            )
            extra_rules = (
                "- Keep the same role as the selected step: an initial planning or search-direction line.\n"
                "- Start it with 'Plan:' or 'Aim:'.\n"
                "- A wrong_target distractor must mention a concrete target value different from the true target.\n"
                "- An allow_reuse distractor must explicitly allow reusing or repeating a number.\n"
                "- A misleading_intermediate distractor must commit to a concrete but unhelpful intermediate goal, not just generic exploration.\n"
                "- Return strict JSON with fields: distractor, error_mode.\n"
            )
    else:
        family_hint = (
            "Create a one-line distractor that preserves the same arithmetic task style and numbers, "
            "but introduces one subtle harmful mistake via wrong_sign, wrong_operator, or wrong_order. "
            "It must not be mathematically equivalent to the selected step."
        )
        extra_rules = (
            "- Keep the same numbers, but change the arithmetic intent so the resulting computation is different.\n"
            "- If the selected step says 'add -N', your distractor must not say 'subtract N' because that is equivalent.\n"
            "- If the selected step says 'subtract N', your distractor must not say 'add -N' because that is equivalent.\n"
            "- Return strict JSON with fields: distractor, error_mode.\n"
        )
    return (
        "You are refining a matched distractor for a reasoning step.\n\n"
        f"Family: {family}\n"
        f"Selected step:\n{step}\n\n"
        f"Paraphrase candidate:\n{row['paraphrase_candidates'][0]}\n\n"
        f"Current distractor:\n{row['distractor_candidates'][0]}\n\n"
        f"{family_hint}\n"
        "Rules:\n"
        "- Keep it to one short line.\n"
        "- Keep the same general style and role as the selected step.\n"
        "- It should be locally plausible but meaningfully worse for solving the task.\n"
        "- It must not be equivalent to the selected step or the paraphrase.\n"
        "- It must change the implied next action or computation in a way that would hurt correctness.\n"
        f"{extra_rules}"
    )


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def same_text(a: str, b: str) -> bool:
    return normalize_text(a) == normalize_text(b)


def find_add_negative_values(text: str) -> set[str]:
    matches = re.findall(r"add\s*-\s*(\d+)", normalize_text(text))
    return set(matches)


def find_subtract_values(text: str) -> set[str]:
    matches = re.findall(r"subtract\s+(\d+)", normalize_text(text))
    return set(matches)


def find_sign_polarity(text: str) -> str | None:
    lowered = normalize_text(text)
    if "negative sign" in lowered or "negative result" in lowered or "negative." in lowered:
        return "negative"
    if "positive sign" in lowered or "positive result" in lowered or "positive." in lowered:
        return "positive"
    return None


def validate_arithmetic_candidate(row: dict, candidate: str) -> list[str]:
    reasons: list[str] = []
    step = row["step_text"]
    paraphrase = row["paraphrase_candidates"][0]
    step_norm = normalize_text(step)
    cand_norm = normalize_text(candidate)

    if same_text(candidate, step) or same_text(candidate, paraphrase):
        reasons.append("candidate_matches_step_or_paraphrase")

    step_add_neg = find_add_negative_values(step)
    cand_add_neg = find_add_negative_values(candidate)
    step_subtract = find_subtract_values(step)
    cand_subtract = find_subtract_values(candidate)

    if step_add_neg and cand_subtract and step_add_neg.intersection(cand_subtract):
        reasons.append("candidate_is_add_negative_subtract_equivalent")
    if step_subtract and cand_add_neg and step_subtract.intersection(cand_add_neg):
        reasons.append("candidate_is_subtract_add_negative_equivalent")

    if "absolute values" in step_norm and "absolute values" in cand_norm:
        step_sign = find_sign_polarity(step)
        cand_sign = find_sign_polarity(candidate)
        if step_sign is not None and step_sign == cand_sign:
            reasons.append("candidate_keeps_same_absolute_value_sign_rule")

    if step_norm == cand_norm:
        reasons.append("candidate_semantics_unchanged")

    return reasons


def validate_hanoi_candidate(row: dict, candidate: str, error_mode: str) -> list[str]:
    reasons: list[str] = []
    step = row["step_text"]
    paraphrase = row["paraphrase_candidates"][0]
    cand_norm = normalize_text(candidate)
    step_norm = normalize_text(step)
    is_check_step = step_norm.startswith("check") or step_norm.startswith("verify")

    if same_text(candidate, step) or same_text(candidate, paraphrase):
        reasons.append("candidate_matches_step_or_paraphrase")

    if is_check_step:
        if not (cand_norm.startswith("check:") or cand_norm.startswith("verify:")):
            reasons.append("candidate_missing_check_prefix")
    else:
        if not cand_norm.startswith("plan:"):
            reasons.append("candidate_missing_plan_prefix")
        if "frame-stewart" in cand_norm:
            wrong_markers = [
                "three pegs",
                "3 pegs",
                "ignore the extra peg",
                "largest disk",
                "split",
                "group",
                "peg ",
                "source peg",
                "destination peg",
            ]
            if not any(marker in cand_norm for marker in wrong_markers):
                reasons.append("frame_stewart_without_explicit_wrong_commitment")

    error_mode_markers = {
        "wrong_split": ["split", "group"],
        "ignore_extra_peg": ["three pegs", "3 pegs", "ignore the extra peg"],
        "move_largest_too_early": ["largest disk"],
        "wrong_aux_peg": ["peg "],
        "wrong_subgoal": ["smallest", "largest", "source peg", "destination peg"],
        "wrong_legality_rule": ["larger", "smaller", "largest", "top disk", "size order", "legal", "allowed"],
        "wrong_goal_check": ["all", "peg", "target", "goal"],
        "ignore_source_target": ["source", "target", "peg"],
    }
    markers = error_mode_markers.get(error_mode, [])
    if markers and not any(marker in cand_norm for marker in markers):
        reasons.append(f"candidate_missing_error_mode_marker:{error_mode}")

    return reasons


def extract_first_int(text: str) -> int | None:
    match = re.search(r"\d+", text)
    if not match:
        return None
    return int(match.group(0))


def validate_countdown_candidate(row: dict, candidate: str, error_mode: str) -> list[str]:
    reasons: list[str] = []
    step = row["step_text"]
    paraphrase = row["paraphrase_candidates"][0]
    cand_norm = normalize_text(candidate)
    step_norm = normalize_text(step)
    is_check_step = step_norm.startswith("check") or "used once" in step_norm or step_norm.startswith("verify")

    if same_text(candidate, step) or same_text(candidate, paraphrase):
        reasons.append("candidate_matches_step_or_paraphrase")

    if is_check_step:
        if not (cand_norm.startswith("check:") or cand_norm.startswith("verify:")):
            reasons.append("candidate_missing_check_prefix")
        error_mode_markers = {
            "allow_reuse": ["reuse", "repeat", "twice", "more than once", "at least once"],
            "allow_omission": ["omit", "leave out", "skip", "not all"],
            "ignore_target_match": ["close enough", "near the target", "does not need to equal", "doesn't need to equal", "within", "near-miss"],
        }
    else:
        if not (
            cand_norm.startswith("plan:")
            or cand_norm.startswith("aim:")
            or cand_norm.startswith("try ")
        ):
            reasons.append("candidate_missing_plan_prefix")
        true_target = extract_first_int(step)
        error_mode_markers = {
            "allow_reuse": ["reuse", "repeat", "twice", "more than once"],
            "misleading_intermediate": ["start from", "aim for", "make", "then fit the rest", "adjust later", "adjust with", "then adjust"],
        }
        if error_mode == "wrong_target":
            numbers = [int(match) for match in re.findall(r"\d+", candidate)]
            if true_target is None or not any(number != true_target for number in numbers):
                reasons.append("candidate_missing_wrong_target_value")

    markers = error_mode_markers.get(error_mode, [])
    if markers and not any(marker in cand_norm for marker in markers):
        reasons.append(f"candidate_missing_error_mode_marker:{error_mode}")

    return reasons


def validate_candidate(row: dict, candidate: str, error_mode: str) -> list[str]:
    if row["family"] == "tower_of_hanoi":
        return validate_hanoi_candidate(row, candidate, error_mode)
    if row["family"] == "countdown":
        return validate_countdown_candidate(row, candidate, error_mode)
    return validate_arithmetic_candidate(row, candidate)


def regenerate_distractor(api_cfg: dict, row: dict) -> tuple[str, str, dict]:
    url = api_cfg["base_url"].rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_cfg['api_key']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": api_cfg["endpoint"],
        "messages": [
            {"role": "system", "content": "Respond with valid JSON only."},
            {"role": "user", "content": build_user_prompt(row)},
        ],
        "temperature": 0.2,
        "max_tokens": 120,
        "response_format": {"type": "json_object"},
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    return parsed["distractor"].strip(), parsed["error_mode"].strip(), data.get("usage", {})


def main() -> None:
    args = parse_args()
    api_cfg = load_api_config()
    input_path = ROOT / args.input
    output_path = ROOT / args.output
    selection_reasons = parse_csv_arg(args.selection_reasons)
    families = parse_csv_arg(args.family_filter)

    rows = [json.loads(line) for line in input_path.open("r", encoding="utf-8")]
    rows = [row for row in rows if keep_row(row, selection_reasons, families)]
    rows = sorted(dedupe_rows(rows), key=lambda r: (r["family"], r["prompt_id"], r["step_index"]))

    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            accepted_distractor = None
            accepted_error_mode = None
            usage_log = []
            reject_reasons = []
            last_candidate = None
            last_error_mode = None

            for _ in range(MAX_RETRIES):
                new_distractor, error_mode, usage = regenerate_distractor(api_cfg, row)
                last_candidate = new_distractor
                last_error_mode = error_mode
                total_prompt_tokens += usage.get("prompt_tokens", 0)
                total_completion_tokens += usage.get("completion_tokens", 0)
                total_tokens += usage.get("total_tokens", 0)
                usage_log.append(usage)

                reject_reasons = validate_candidate(row, new_distractor, error_mode)
                if not reject_reasons:
                    accepted_distractor = new_distractor
                    accepted_error_mode = error_mode
                    break

            if accepted_distractor is None:
                raise RuntimeError(
                    f"Failed to generate a valid distractor for {row['prompt_id']} step {row['step_index']}: "
                    + ",".join(reject_reasons)
                    + f" | last_error_mode={last_error_mode} | last_candidate={last_candidate}"
                )

            updated = dict(row)
            updated["distractor_candidates"] = [accepted_distractor]
            updated["distractor_error_mode"] = accepted_error_mode
            updated["refinement_version"] = "v2_focus_early_steps_validated_distractors"
            updated["refinement_note"] = (
                "Kept first/only steps and regenerated the distractor with stronger family-aware constraints plus "
                "local rejection checks for equivalence and missing error commitments."
            )
            updated["refinement_usage"] = usage_log[-1]
            updated["refinement_attempts"] = len(usage_log)
            updated["refinement_usage_log"] = usage_log
            handle.write(json.dumps(updated, ensure_ascii=True) + "\n")

    summary = {
        "output": str(output_path.relative_to(ROOT)),
        "count": len(rows),
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "total_tokens": total_tokens,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
