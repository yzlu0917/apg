from __future__ import annotations

import random


def _format_linear_equation(a: int, b: int, c: int) -> str:
    sign = "+" if b >= 0 else "-"
    return f"{a}x {sign} {abs(b)} = {c}"


def _pick_distractor(rng: random.Random, answer: int) -> int:
    offset = rng.choice([-3, -2, -1, 1, 2, 3])
    return answer + offset


def _cancel_bias_text(bias: int) -> str:
    if bias >= 0:
        return f"Subtract {bias} from both sides"
    return f"Add {abs(bias)} to both sides"


def _undo_shift_text(shift: int) -> str:
    if shift >= 0:
        return f"Subtract {shift} from both sides"
    return f"Add {abs(shift)} to both sides"


def _cancel_multiplier_text(multiplier: int) -> str:
    return f"Cancel the {multiplier}"


def _standard_instance(rng: random.Random, problem_index: int) -> dict:
    a = rng.randint(2, 8)
    x = rng.randint(-5, 6)
    b = rng.randint(-9, 9)
    c = a * x + b
    distractor = _pick_distractor(rng, x)
    locus = rng.choice([0, 1])

    wrong_delta = rng.choice([-2, -1, 1, 2])
    rhs_after_subtract = c - b
    wrong_rhs = rhs_after_subtract + wrong_delta
    wrong_x = x + wrong_delta / a
    if locus == 0:
        invalid_steps = [
            {
                "statement": f"{a}x = {wrong_rhs}",
                "explanation": f"{_cancel_bias_text(b)} and get {a}x = {wrong_rhs}.",
            },
            {
                "statement": f"x = {wrong_x:g}",
                "explanation": f"Now divide by {a}, so x = {wrong_x:g}.",
            },
        ]
    else:
        invalid_steps = [
            {
                "statement": f"{a}x = {rhs_after_subtract}",
                "explanation": f"{_cancel_bias_text(b)} to obtain {a}x = {rhs_after_subtract}.",
            },
            {
                "statement": f"x = {wrong_x:g}",
                "explanation": f"Divide both sides by {a}, concluding x = {wrong_x:g}.",
            },
        ]

    valid_steps = [
        {
            "statement": f"{a}x = {rhs_after_subtract}",
            "explanation": f"{_cancel_bias_text(b)} to obtain {a}x = {rhs_after_subtract}.",
        },
        {
            "statement": f"x = {x}",
            "explanation": f"Divide both sides by {a}, concluding x = {x}.",
        },
    ]

    verbalizers = [
        {
            "id": "alg_v1",
            "problem_text": f"Solve the equation {_format_linear_equation(a, b, c)}.",
            "render_step": lambda step, i: f"Step {i + 1}: {step['explanation']}",
            "answer_correct": f"Therefore, the final answer is x = {x}.",
            "answer_swapped": f"Therefore, the final answer is x = {distractor}.",
        },
        {
            "id": "alg_v2",
            "problem_text": f"Find x in {_format_linear_equation(a, b, c)}.",
            "render_step": lambda step, i: (
                f"Line {i + 1}: rewrite the equation as {step['statement']}."
            ),
            "answer_correct": f"So the solution is x = {x}.",
            "answer_swapped": f"So the solution is x = {distractor}.",
        },
        {
            "id": "alg_v3",
            "problem_text": f"Determine the value of x if {_format_linear_equation(a, b, c)}.",
            "render_step": lambda step, i: (
                f"Reasoning {i + 1}: after balancing the equation, we have {step['statement']}."
            ),
            "answer_correct": f"Hence x equals {x}.",
            "answer_swapped": f"Hence x equals {distractor}.",
        },
    ]

    return {
        "domain": "algebra",
        "problem_id": f"algebra-{problem_index:04d}",
        "audited_locus": locus,
        "valid_steps": valid_steps,
        "invalid_steps": invalid_steps,
        "verbalizers": verbalizers,
        "correct_answer": f"x = {x}",
        "distractor_answer": f"x = {distractor}",
        "metadata": {
            "equation": _format_linear_equation(a, b, c),
            "coeff_a": a,
            "bias_b": b,
            "rhs_c": c,
            "solution_x": x,
            "distractor_x": distractor,
        },
    }


def _hard_instance(
    rng: random.Random,
    problem_index: int,
    blind_audit_safe: bool = False,
    blind_audit_v3: bool = False,
    blind_audit_v4: bool = False,
) -> dict:
    a = rng.randint(2, 6)
    x = rng.randint(-6, 6)
    shift = rng.choice([value for value in range(-4, 5) if value != 0])
    b = rng.randint(-8, 8)
    inner_value = x + shift
    rhs_after_subtract = a * inner_value
    rhs_after_divide = inner_value
    c = rhs_after_subtract + b
    distractor = _pick_distractor(rng, x)
    locus = rng.choice([0, 1] if blind_audit_safe else [0, 1, 2])
    wrong_delta = rng.choice([-2, -1, 1, 2])
    wrong_divide = rhs_after_divide + wrong_delta
    wrong_rhs = a * wrong_divide
    wrong_x = wrong_divide - shift

    valid_steps = [
        {
            "statement": f"{a}(x {'+' if shift >= 0 else '-'} {abs(shift)}) = {rhs_after_subtract}",
            "explanation": f"{_cancel_bias_text(b)} to get {a}(x {'+' if shift >= 0 else '-'} {abs(shift)}) = {rhs_after_subtract}.",
        },
        {
            "statement": f"x {'+' if shift >= 0 else '-'} {abs(shift)} = {rhs_after_divide}",
            "explanation": f"Divide both sides by {a}, so x {'+' if shift >= 0 else '-'} {abs(shift)} = {rhs_after_divide}.",
        },
        {
            "statement": f"x = {x}",
            "explanation": f"{_undo_shift_text(shift)}, giving x = {x}.",
        },
    ]

    if blind_audit_v4 and locus == 0:
        invalid_steps = [
            {
                "statement": f"{a}(x {'+' if shift >= 0 else '-'} {abs(shift)}) = {wrong_rhs}",
                "explanation": f"{_cancel_bias_text(b)} to get {a}(x {'+' if shift >= 0 else '-'} {abs(shift)}) = {wrong_rhs}.",
            },
            {
                "statement": f"x {'+' if shift >= 0 else '-'} {abs(shift)} = {rhs_after_divide}",
                "explanation": f"{_cancel_multiplier_text(a)} and get x {'+' if shift >= 0 else '-'} {abs(shift)} = {rhs_after_divide}.",
            },
            {
                "statement": f"x = {x}",
                "explanation": f"{_undo_shift_text(shift)}, giving x = {x}.",
            },
        ]
    elif blind_audit_v4 and locus == 1:
        invalid_steps = [
            valid_steps[0],
            {
                "statement": f"x {'+' if shift >= 0 else '-'} {abs(shift)} = {rhs_after_divide}",
                "explanation": f"{_cancel_multiplier_text(a)} and get x {'+' if shift >= 0 else '-'} {abs(shift)} = {rhs_after_divide}.",
            },
            {
                "statement": f"x = {x}",
                "explanation": f"{_undo_shift_text(shift)}, giving x = {x}.",
            },
        ]
    elif blind_audit_safe and locus == 0:
        invalid_steps = [
            {
                "statement": f"{a}(x {'+' if shift >= 0 else '-'} {abs(shift)}) = {wrong_rhs}",
                "explanation": f"{_cancel_bias_text(b)} to get {a}(x {'+' if shift >= 0 else '-'} {abs(shift)}) = {wrong_rhs}.",
            },
            {
                "statement": f"x {'+' if shift >= 0 else '-'} {abs(shift)} = {wrong_divide}",
                "explanation": f"Divide both sides by {a}, so x {'+' if shift >= 0 else '-'} {abs(shift)} = {wrong_divide}.",
            },
            {
                "statement": f"x = {x}",
                "explanation": f"Carry the shifted form through and conclude x = {x}.",
            },
        ]
    elif blind_audit_safe and locus == 1:
        invalid_steps = [
            valid_steps[0],
            {
                "statement": f"x {'+' if shift >= 0 else '-'} {abs(shift)} = {wrong_divide}",
                "explanation": f"Divide both sides by {a}, so x {'+' if shift >= 0 else '-'} {abs(shift)} = {wrong_divide}.",
            },
            {
                "statement": f"x = {x}",
                "explanation": f"Use the shifted form to conclude x = {x}.",
            },
        ]
    elif locus == 0:
        invalid_steps = [
            {
                "statement": f"{a}(x {'+' if shift >= 0 else '-'} {abs(shift)}) = {wrong_rhs}",
                "explanation": f"{_cancel_bias_text(b)} to get {a}(x {'+' if shift >= 0 else '-'} {abs(shift)}) = {wrong_rhs}.",
            },
            {
                "statement": f"x {'+' if shift >= 0 else '-'} {abs(shift)} = {wrong_divide}",
                "explanation": f"Divide both sides by {a}, so x {'+' if shift >= 0 else '-'} {abs(shift)} = {wrong_divide}.",
            },
            {
                "statement": f"x = {wrong_x}",
                "explanation": f"{_undo_shift_text(shift)}, giving x = {wrong_x}.",
            },
        ]
    elif locus == 1:
        invalid_steps = [
            valid_steps[0],
            {
                "statement": f"x {'+' if shift >= 0 else '-'} {abs(shift)} = {wrong_divide}",
                "explanation": f"Divide both sides by {a}, so x {'+' if shift >= 0 else '-'} {abs(shift)} = {wrong_divide}.",
            },
            {
                "statement": f"x = {wrong_x}",
                "explanation": f"{_undo_shift_text(shift)}, giving x = {wrong_x}.",
            },
        ]
    else:
        invalid_steps = [
            valid_steps[0],
            valid_steps[1],
            {
                "statement": f"x = {wrong_x}",
                "explanation": f"{_undo_shift_text(shift)}, giving x = {wrong_x}.",
            },
        ]

    equation = f"{a}(x {'+' if shift >= 0 else '-'} {abs(shift)}) {'+' if b >= 0 else '-'} {abs(b)} = {c}"
    verbalizers = [
        {
            "id": "alg_v1",
            "problem_text": f"Solve the equation {equation}.",
            "render_step": lambda step, i: f"Step {i + 1}: {step['explanation']}",
            "answer_correct": f"Therefore, the final answer is x = {x}.",
            "answer_swapped": f"Therefore, the final answer is x = {distractor}.",
        },
        {
            "id": "alg_v2",
            "problem_text": f"Find x in {equation}.",
            "render_step": (
                (lambda step, i: f"Line {i + 1}: {step['explanation']}")
                if blind_audit_v3 or blind_audit_v4
                else (lambda step, i: f"Line {i + 1}: rewrite the equation as {step['statement']}.")
            ),
            "answer_correct": f"So the solution is x = {x}.",
            "answer_swapped": f"So the solution is x = {distractor}.",
        },
        {
            "id": "alg_v3",
            "problem_text": f"Determine x if {equation}.",
            "render_step": (
                (lambda step, i: f"Reasoning {i + 1}: {step['explanation']}")
                if blind_audit_v3 or blind_audit_v4
                else (lambda step, i: f"Reasoning {i + 1}: after isolating terms, we have {step['statement']}.")
            ),
            "answer_correct": f"Hence x equals {x}.",
            "answer_swapped": f"Hence x equals {distractor}.",
        },
    ]

    return {
        "domain": "algebra",
        "problem_id": f"algebra-hard-{problem_index:04d}",
        "audited_locus": locus,
        "valid_steps": valid_steps,
        "invalid_steps": invalid_steps,
        "verbalizers": verbalizers,
        "correct_answer": f"x = {x}",
        "distractor_answer": f"x = {distractor}",
        "metadata": {
            "difficulty": (
                "hard_blindfix_v4"
                if blind_audit_v4
                else ("hard_blindfix_v3" if blind_audit_v3 else ("hard_blindfix" if blind_audit_safe else "hard"))
            ),
            "equation": equation,
            "coeff_a": a,
            "shift": shift,
            "bias_b": b,
            "rhs_c": c,
            "solution_x": x,
            "distractor_x": distractor,
        },
    }


def sample_algebra_instance(rng: random.Random, problem_index: int, difficulty: str = "standard") -> dict:
    if difficulty == "hard_blindfix_v4":
        return _hard_instance(rng, problem_index, blind_audit_safe=True, blind_audit_v4=True)
    if difficulty == "hard_blindfix_v3":
        return _hard_instance(rng, problem_index, blind_audit_safe=True, blind_audit_v3=True)
    if difficulty == "hard_blindfix_v2":
        return _hard_instance(rng, problem_index, blind_audit_safe=True)
    if difficulty == "hard_blindfix":
        return _hard_instance(rng, problem_index, blind_audit_safe=True)
    if difficulty == "hard":
        return _hard_instance(rng, problem_index)
    return _standard_instance(rng, problem_index)
