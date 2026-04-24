from __future__ import annotations

from dataclasses import dataclass
import random
import re

from triver.envs.common import TraceEvaluation, perturb_new_integer_token


class EquationParseError(ValueError):
    """Raised when an equation cannot be parsed."""


@dataclass(frozen=True)
class LinearExpr:
    x_coeff: int
    const: int


@dataclass(frozen=True)
class LinearEquation:
    left: LinearExpr
    right: LinearExpr


@dataclass(frozen=True)
class LinearEquationSample:
    equation: str
    solution: int


def strip_outer_parentheses(text: str) -> str:
    stripped = text.strip()
    while stripped.startswith("(") and stripped.endswith(")"):
        depth = 0
        balanced = True
        for index, char in enumerate(stripped):
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            if depth == 0 and index != len(stripped) - 1:
                balanced = False
                break
        if not balanced:
            break
        stripped = stripped[1:-1].strip()
    return stripped


def parse_linear_expr(text: str) -> LinearExpr:
    compact = strip_outer_parentheses(text).replace(" ", "")
    if not compact:
        raise EquationParseError("Empty expression")
    compact = compact.replace("−", "-")
    terms = re.findall(r"[+-]?[^+-]+", compact)
    if not terms:
        raise EquationParseError("No terms found")
    x_coeff = 0
    const = 0
    for term in terms:
        if not term:
            continue
        normalized = term.replace("*", "")
        if "x" in normalized:
            match = re.fullmatch(r"([+-]?\d*)x", normalized)
            if match is None:
                raise EquationParseError(f"Invalid x-term: {term}")
            coeff_text = match.group(1)
            if coeff_text in {"", "+"}:
                coeff = 1
            elif coeff_text == "-":
                coeff = -1
            else:
                try:
                    coeff = int(coeff_text)
                except ValueError as error:
                    raise EquationParseError(f"Invalid integer coefficient: {term}") from error
            x_coeff += coeff
        else:
            try:
                const += int(normalized)
            except ValueError as error:
                raise EquationParseError(f"Invalid integer constant: {term}") from error
    return LinearExpr(x_coeff=x_coeff, const=const)


def parse_equation(text: str) -> LinearEquation:
    parts = text.split("=")
    if len(parts) != 2:
        raise EquationParseError("Equation must contain exactly one '='")
    return LinearEquation(
        left=parse_linear_expr(parts[0]),
        right=parse_linear_expr(parts[1]),
    )


def canonicalize_equation(equation: LinearEquation) -> LinearEquation:
    if equation.left.x_coeff == 0 and equation.right.x_coeff != 0:
        return LinearEquation(left=equation.right, right=equation.left)
    return equation


def render_linear_expr(expr: LinearExpr) -> str:
    parts: list[str] = []
    if expr.x_coeff != 0:
        if expr.x_coeff == 1:
            parts.append("x")
        elif expr.x_coeff == -1:
            parts.append("-x")
        else:
            parts.append(f"{expr.x_coeff}*x")
    if expr.const != 0 or not parts:
        if not parts:
            parts.append(str(expr.const))
        elif expr.const > 0:
            parts.append(f"+ {expr.const}")
        else:
            parts.append(f"- {abs(expr.const)}")
    return " ".join(parts)


def render_equation(equation: LinearEquation) -> str:
    equation = canonicalize_equation(equation)
    return f"{render_linear_expr(equation.left)} = {render_linear_expr(equation.right)}"


def normalize_line(line: str) -> str | None:
    stripped = line.strip().strip("`")
    if not stripped:
        return None
    stripped = re.sub(r"^(step|line)\s*\d+\s*[:.)-]\s*", "", stripped, flags=re.IGNORECASE)
    stripped = re.sub(
        r"^(equation|current|next|answer|final)\s*:\s*",
        "",
        stripped,
        flags=re.IGNORECASE,
    )
    stripped = stripped.rstrip(".,;")
    try:
        return render_equation(parse_equation(stripped))
    except EquationParseError:
        return None


def extract_trace_lines(text: str) -> list[str]:
    lines: list[str] = []
    started = False
    for raw_line in text.splitlines():
        normalized = normalize_line(raw_line)
        if normalized is None:
            if started:
                break
            continue
        lines.append(normalized)
        started = True
    return lines


def one_step_transforms(line: str) -> list[str]:
    equation = parse_equation(line)
    left = equation.left
    right = equation.right
    candidates: list[LinearEquation] = []

    if right.x_coeff != 0:
        candidates.append(
            LinearEquation(
                left=LinearExpr(left.x_coeff - right.x_coeff, left.const),
                right=LinearExpr(0, right.const),
            )
        )
    if left.const != 0:
        candidates.append(
            LinearEquation(
                left=LinearExpr(left.x_coeff, 0),
                right=LinearExpr(right.x_coeff, right.const - left.const),
            )
        )
    if left.x_coeff != 0 and left.const == 0 and right.x_coeff == 0 and right.const % left.x_coeff == 0:
        candidates.append(
            LinearEquation(
                left=LinearExpr(1, 0),
                right=LinearExpr(0, right.const // left.x_coeff),
            )
        )
    if left.x_coeff == 0 and right.x_coeff != 0:
        candidates.append(
            LinearEquation(
                left=right,
                right=left,
            )
        )

    seen: set[str] = set()
    rendered: list[str] = []
    for candidate in candidates:
        rendered_candidate = render_equation(candidate)
        if rendered_candidate not in seen:
            seen.add(rendered_candidate)
            rendered.append(rendered_candidate)
    return rendered


def valid_transition(source: str, target: str) -> bool:
    try:
        canonical_target = render_equation(parse_equation(target))
    except EquationParseError:
        return False
    return canonical_target in one_step_transforms(source)


def is_terminal_equation(line: str) -> bool:
    equation = parse_equation(line)
    return equation.left == LinearExpr(1, 0) and equation.right.x_coeff == 0


def check_trace(trace: list[str], solution: int) -> TraceEvaluation:
    if not trace:
        return TraceEvaluation(
            trace=[],
            valid_prefix_length=0,
            invalid_transition_index=None,
            transition_validity=[],
            terminal=False,
            final_answer=None,
            success=False,
        )

    validity: list[bool] = []
    valid_prefix_length = 1
    invalid_transition_index: int | None = None
    for line_index in range(1, len(trace)):
        is_valid = valid_transition(trace[line_index - 1], trace[line_index])
        validity.append(is_valid)
        if is_valid and invalid_transition_index is None:
            valid_prefix_length = line_index + 1
            continue
        if invalid_transition_index is None:
            invalid_transition_index = line_index

    terminal_equation = parse_equation(trace[-1])
    terminal = is_terminal_equation(trace[-1])
    final_answer = terminal_equation.right.const if terminal else None
    success = invalid_transition_index is None and terminal and final_answer == solution
    return TraceEvaluation(
        trace=list(trace),
        valid_prefix_length=valid_prefix_length,
        invalid_transition_index=invalid_transition_index,
        transition_validity=validity,
        terminal=terminal,
        final_answer=final_answer,
        success=success,
    )


def prefix_invalidity_risk(trace: list[str], solution: int) -> float:
    evaluation = check_trace(trace, solution)
    return 1.0 if evaluation.prefix_invalid else 0.0


def generate_equation_sample(
    rng: random.Random,
    solution_min: int = -9,
    solution_max: int = 9,
    coeff_min: int = -5,
    coeff_max: int = 5,
    const_min: int = -12,
    const_max: int = 12,
) -> LinearEquationSample:
    while True:
        solution = rng.randint(solution_min, solution_max)
        left_x = rng.choice([value for value in range(coeff_min, coeff_max + 1) if value != 0])
        right_x = rng.choice([value for value in range(coeff_min, coeff_max + 1) if value != left_x])
        left_const = rng.randint(const_min, const_max)
        right_const = (left_x - right_x) * solution + left_const
        if right_const < const_min or right_const > const_max:
            continue
        equation = LinearEquation(
            left=LinearExpr(left_x, left_const),
            right=LinearExpr(right_x, right_const),
        )
        return LinearEquationSample(
            equation=render_equation(equation),
            solution=solution,
        )


class LinearEquationEnv:
    name = "linear_equations"

    def generate_sample(self, rng: random.Random) -> LinearEquationSample:
        return generate_equation_sample(rng)

    def problem_text(self, sample: LinearEquationSample) -> str:
        return sample.equation

    def target_text(self, sample: LinearEquationSample) -> str:
        return str(sample.solution)

    def sample_from_record(self, problem: str, target: str) -> LinearEquationSample:
        return LinearEquationSample(equation=problem, solution=int(target))

    def initial_trace(self, sample: LinearEquationSample) -> list[str]:
        return [sample.equation]

    def build_solver_messages(
        self,
        sample: LinearEquationSample,
        prefix_lines: list[str],
        action: str,
        prompt_style: str = "default",
    ) -> tuple[list[dict[str, str]], list[str]]:
        removed_line = prefix_lines[-1] if action == "revise_1" and prefix_lines else None
        use_revise_focus = prompt_style == "api_revise_focus"
        if prompt_style == "api_revise_invalid_focus" and action == "revise_1":
            use_revise_focus = self.check_trace(prefix_lines, sample).prefix_invalid
        if action == "revise_1":
            action_prefix = prefix_lines[:-1]
            rollback_note = (
                "The omitted last line from the original derivation was wrong and has been rolled back. "
                "Replace it by continuing correctly from the rollback trace below."
            )
        else:
            action_prefix = prefix_lines
            rollback_note = "Continue from the current derivation below."

        trace_block = "\n".join(action_prefix)
        if prompt_style == "api_revise_candidates" and action == "revise_1":
            next_candidates = one_step_transforms(action_prefix[-1]) if action_prefix else []
            candidate_block = "\n".join(f"- {candidate}" for candidate in next_candidates) or "- <none>"
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You repair one-variable linear-equation derivations one line at a time.\n"
                        "Choose the best corrected replacement for one removed wrong line.\n"
                        "Rules:\n"
                        "- Output exactly one equation.\n"
                        "- No prose, no bullets, no labels, no code fences.\n"
                        "- The output must be the immediate replacement for the removed line.\n"
                        "- It must match one of the valid one-step candidates from the rollback derivation."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Original equation:\n{sample.equation}\n\n"
                        f"Rollback derivation:\n{trace_block}\n\n"
                        f"Removed wrong line:\n{removed_line}\n\n"
                        "Valid one-step replacement candidates:\n"
                        f"{candidate_block}\n\n"
                        "Return the single best replacement equation only."
                    ),
                },
            ]
        elif use_revise_focus and action == "revise_1":
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You repair one-variable linear-equation derivations one line at a time.\n"
                        "Your job is to replace one wrong removed line with one corrected next equation.\n"
                        "Rules:\n"
                        "- Output exactly one equation.\n"
                        "- No prose, no bullets, no labels, no code fences.\n"
                        "- The output must be the immediate replacement for the removed line, not a later step.\n"
                        "- It must apply exactly one valid algebra step that preserves the solution set.\n"
                        "Example:\n"
                        "Rollback trace: 2*x + 3 = 11\n"
                        "Removed wrong line: 2*x + 3 = 8\n"
                        "Correct replacement: 2*x = 8"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Original equation:\n{sample.equation}\n\n"
                        f"Rollback derivation:\n{trace_block}\n\n"
                        f"Removed wrong line:\n{removed_line}\n\n"
                        "Return one corrected replacement equation only."
                    ),
                },
            ]
        elif prompt_style == "api_strict":
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You solve one-variable linear equations one legal step at a time.\n"
                        "Rules:\n"
                        "- Output exactly one equation.\n"
                        "- No prose, no bullets, no labels, no code fences.\n"
                        "- Apply exactly one algebra step that preserves the solution set.\n"
                        "- Use canonical formatting like '2*x = 8' or 'x = 4'.\n"
                        "- Keep variable x.\n"
                        "Examples:\n"
                        "2*x + 3 = 11 -> 2*x = 8\n"
                        "2*x = 8 -> x = 4"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Original equation:\n{sample.equation}\n\n"
                        f"{rollback_note}\n"
                        f"Visible derivation:\n{trace_block}\n\n"
                        "Return one corrected next equation only."
                    ),
                },
            ]
        else:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You solve one-variable linear equations. Output only equations, one per line. "
                        "Each line must apply exactly one valid algebra step that preserves the solution set. "
                        "Use variable x. Do not explain. When asked for the next line, output exactly one next equation."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Original equation:\n{sample.equation}\n\n"
                        f"{rollback_note}\n"
                        f"Visible derivation:\n{trace_block}\n\n"
                        "Output exactly one next line only."
                    ),
                },
            ]
        return messages, action_prefix

    def extract_trace_lines(self, text: str) -> list[str]:
        return extract_trace_lines(text)

    def is_terminal_line(self, line: str) -> bool:
        return is_terminal_equation(line)

    def check_trace(self, trace: list[str], sample: LinearEquationSample) -> TraceEvaluation:
        return check_trace(trace, sample.solution)

    def prefix_invalidity_risk(self, trace: list[str], sample: LinearEquationSample) -> float:
        return prefix_invalidity_risk(trace, sample.solution)

    def make_recoverable_prefix(
        self,
        prefix_lines: list[str],
        sample: LinearEquationSample,
        rng: random.Random,
        recoverable_style: str = "default",
    ) -> list[str] | None:
        if len(prefix_lines) < 2:
            return None
        if recoverable_style == "local_changed_token":
            rendered = perturb_new_integer_token(prefix_lines[-2], prefix_lines[-1], rng)
            if rendered is None or rendered == prefix_lines[-1]:
                return None
            try:
                render_equation(parse_equation(rendered))
            except EquationParseError:
                return None
            return list(prefix_lines[:-1]) + [rendered]

        equation = parse_equation(prefix_lines[-1])
        deltas = [-2, -1, 1, 2]
        if equation.right.x_coeff == 0:
            corrupted = LinearEquation(
                left=equation.left,
                right=LinearExpr(0, equation.right.const + rng.choice(deltas)),
            )
        else:
            corrupted = LinearEquation(
                left=equation.left,
                right=LinearExpr(equation.right.x_coeff, equation.right.const + rng.choice(deltas)),
            )
        rendered = render_equation(corrupted)
        if rendered == prefix_lines[-1]:
            return None
        return list(prefix_lines[:-1]) + [rendered]
