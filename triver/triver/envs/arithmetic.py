from __future__ import annotations

from dataclasses import dataclass
import random
import re

from triver.envs.common import TraceEvaluation, perturb_new_integer_token


OPS = {"+", "-", "*"}


class ParseError(ValueError):
    """Raised when an arithmetic expression cannot be parsed."""


@dataclass(frozen=True)
class IntExpr:
    value: int


@dataclass(frozen=True)
class BinExpr:
    left: "Expr"
    op: str
    right: "Expr"


Expr = IntExpr | BinExpr


@dataclass(frozen=True)
class ArithmeticSample:
    expression: str
    value: int

def eval_expr(expr: Expr) -> int:
    if isinstance(expr, IntExpr):
        return expr.value
    left = eval_expr(expr.left)
    right = eval_expr(expr.right)
    if expr.op == "+":
        return left + right
    if expr.op == "-":
        return left - right
    if expr.op == "*":
        return left * right
    raise ValueError(f"Unsupported operator: {expr.op}")


def render_expr(expr: Expr) -> str:
    if isinstance(expr, IntExpr):
        return str(expr.value)
    return f"({render_expr(expr.left)} {expr.op} {render_expr(expr.right)})"


def tokenize_expression(text: str) -> list[str]:
    tokens: list[str] = []
    i = 0
    previous: str | None = None
    while i < len(text):
        char = text[i]
        if char.isspace():
            i += 1
            continue
        if char in "()+*":
            tokens.append(char)
            previous = char
            i += 1
            continue
        if char == "-":
            next_is_digit = i + 1 < len(text) and text[i + 1].isdigit()
            unary = previous is None or previous in OPS or previous == "("
            if unary and next_is_digit:
                j = i + 1
                while j < len(text) and text[j].isdigit():
                    j += 1
                tokens.append(text[i:j])
                previous = text[i:j]
                i = j
                continue
            tokens.append(char)
            previous = char
            i += 1
            continue
        if char.isdigit():
            j = i + 1
            while j < len(text) and text[j].isdigit():
                j += 1
            tokens.append(text[i:j])
            previous = text[i:j]
            i = j
            continue
        raise ParseError(f"Unexpected character: {char!r}")
    return tokens


def parse_expression(text: str) -> Expr:
    tokens = tokenize_expression(text)
    if not tokens:
        raise ParseError("Empty expression")
    expr, next_index = _parse_sum(tokens, 0)
    if next_index != len(tokens):
        raise ParseError("Trailing tokens")
    return expr


def _parse_sum(tokens: list[str], index: int) -> tuple[Expr, int]:
    left, index = _parse_product(tokens, index)
    while index < len(tokens) and tokens[index] in {"+", "-"}:
        op = tokens[index]
        right, index = _parse_product(tokens, index + 1)
        left = BinExpr(left=left, op=op, right=right)
    return left, index


def _parse_product(tokens: list[str], index: int) -> tuple[Expr, int]:
    left, index = _parse_factor(tokens, index)
    while index < len(tokens) and tokens[index] == "*":
        op = tokens[index]
        right, index = _parse_factor(tokens, index + 1)
        left = BinExpr(left=left, op=op, right=right)
    return left, index


def _parse_factor(tokens: list[str], index: int) -> tuple[Expr, int]:
    if index >= len(tokens):
        raise ParseError("Unexpected end of expression")
    token = tokens[index]
    if token == "(":
        expr, index = _parse_sum(tokens, index + 1)
        if index >= len(tokens) or tokens[index] != ")":
            raise ParseError("Expected closing parenthesis")
        return expr, index + 1
    if re.fullmatch(r"-?\d+", token):
        return IntExpr(int(token)), index + 1
    raise ParseError(f"Unexpected token: {token}")


def normalize_line(line: str) -> str | None:
    stripped = line.strip().strip("`")
    if not stripped:
        return None
    stripped = re.sub(r"^(step|line)\s*\d+\s*[:.)-]\s*", "", stripped, flags=re.IGNORECASE)
    stripped = re.sub(
        r"^(expression|trace|current|next|answer|final)\s*:\s*",
        "",
        stripped,
        flags=re.IGNORECASE,
    )
    stripped = stripped.rstrip(".,;")
    try:
        return render_expr(parse_expression(stripped))
    except ParseError:
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


def _reduce_once(expr: Expr) -> list[Expr]:
    reductions: list[Expr] = []
    if isinstance(expr, IntExpr):
        return reductions
    if isinstance(expr.left, IntExpr) and isinstance(expr.right, IntExpr):
        reductions.append(IntExpr(eval_expr(expr)))
    for reduced_left in _reduce_once(expr.left):
        reductions.append(BinExpr(left=reduced_left, op=expr.op, right=expr.right))
    for reduced_right in _reduce_once(expr.right):
        reductions.append(BinExpr(left=expr.left, op=expr.op, right=reduced_right))
    return reductions


def one_step_reductions(expression: str) -> list[str]:
    expr = parse_expression(expression)
    rendered: list[str] = []
    seen: set[str] = set()
    for reduced in _reduce_once(expr):
        candidate = render_expr(reduced)
        if candidate not in seen:
            seen.add(candidate)
            rendered.append(candidate)
    return rendered


def valid_transition(source: str, target: str) -> bool:
    try:
        canonical_target = render_expr(parse_expression(target))
    except ParseError:
        return False
    return canonical_target in one_step_reductions(source)


def is_terminal_expression(expression: str) -> bool:
    return isinstance(parse_expression(expression), IntExpr)


def check_trace(trace: list[str], target_value: int) -> TraceEvaluation:
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

    terminal_expr = parse_expression(trace[-1])
    terminal = isinstance(terminal_expr, IntExpr)
    final_answer = terminal_expr.value if terminal else None
    success = invalid_transition_index is None and terminal and final_answer == target_value
    return TraceEvaluation(
        trace=list(trace),
        valid_prefix_length=valid_prefix_length,
        invalid_transition_index=invalid_transition_index,
        transition_validity=validity,
        terminal=terminal,
        final_answer=final_answer,
        success=success,
    )


def prefix_invalidity_risk(trace: list[str], target_value: int) -> float:
    evaluation = check_trace(trace, target_value)
    return 1.0 if evaluation.prefix_invalid else 0.0


def generate_expression(
    rng: random.Random,
    min_depth: int = 2,
    max_depth: int = 4,
    operand_min: int = 1,
    operand_max: int = 20,
) -> ArithmeticSample:
    depth = rng.randint(min_depth, max_depth)
    expr = _generate_expr(rng, depth, operand_min, operand_max)
    return ArithmeticSample(expression=render_expr(expr), value=eval_expr(expr))


def _generate_expr(
    rng: random.Random,
    depth: int,
    operand_min: int,
    operand_max: int,
) -> Expr:
    if depth <= 0:
        return IntExpr(rng.randint(operand_min, operand_max))
    if depth == 1 and rng.random() < 0.25:
        return IntExpr(rng.randint(operand_min, operand_max))
    left_depth = depth - 1
    right_depth = max(0, depth - 1 - rng.randint(0, 1))
    left = _generate_expr(rng, left_depth, operand_min, operand_max)
    right = _generate_expr(rng, right_depth, operand_min, operand_max)
    op = rng.choice(sorted(OPS))
    return BinExpr(left=left, op=op, right=right)


class ArithmeticEnv:
    name = "arithmetic"

    def generate_sample(self, rng: random.Random) -> ArithmeticSample:
        return generate_expression(rng)

    def problem_text(self, sample: ArithmeticSample) -> str:
        return sample.expression

    def target_text(self, sample: ArithmeticSample) -> str:
        return str(sample.value)

    def sample_from_record(self, problem: str, target: str) -> ArithmeticSample:
        return ArithmeticSample(expression=problem, value=int(target))

    def initial_trace(self, sample: ArithmeticSample) -> list[str]:
        return [sample.expression]

    def build_solver_messages(
        self,
        sample: ArithmeticSample,
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
                "The omitted last line from the original trace was wrong and has been rolled back. "
                "Replace it by continuing correctly from the rollback trace below."
            )
        else:
            action_prefix = prefix_lines
            rollback_note = "Continue from the current trace below."

        trace_block = "\n".join(action_prefix)
        if prompt_style == "api_revise_candidates" and action == "revise_1":
            next_candidates = one_step_reductions(action_prefix[-1]) if action_prefix else []
            candidate_block = "\n".join(f"- {candidate}" for candidate in next_candidates) or "- <none>"
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You repair arithmetic traces one line at a time.\n"
                        "Choose the best corrected replacement for one removed wrong line.\n"
                        "Rules:\n"
                        "- Output exactly one arithmetic expression.\n"
                        "- No prose, no bullets, no labels, no code fences.\n"
                        "- The output must be the immediate replacement for the removed line.\n"
                        "- It must match one of the valid one-step candidates from the rollback trace."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Original expression:\n{sample.expression}\n\n"
                        f"Rollback trace:\n{trace_block}\n\n"
                        f"Removed wrong line:\n{removed_line}\n\n"
                        "Valid one-step replacement candidates:\n"
                        f"{candidate_block}\n\n"
                        "Return the single best replacement line only."
                    ),
                },
            ]
        elif use_revise_focus and action == "revise_1":
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You repair arithmetic traces one line at a time.\n"
                        "Your job is to replace one wrong removed line with one corrected next expression.\n"
                        "Rules:\n"
                        "- Output exactly one arithmetic expression.\n"
                        "- No prose, no bullets, no labels, no code fences.\n"
                        "- The output must be the immediate replacement for the removed line, not a later step.\n"
                        "- It must be a valid one-step reduction of the rollback trace.\n"
                        "Example:\n"
                        "Rollback trace: (2 + 3) * 4\n"
                        "Removed wrong line: 2 + 12\n"
                        "Correct replacement: 5 * 4"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Original expression:\n{sample.expression}\n\n"
                        f"Rollback trace:\n{trace_block}\n\n"
                        f"Removed wrong line:\n{removed_line}\n\n"
                        "Return one corrected replacement line only."
                    ),
                },
            ]
        elif prompt_style == "api_strict":
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You reduce arithmetic expressions one legal step at a time.\n"
                        "Rules:\n"
                        "- Output exactly one arithmetic expression.\n"
                        "- No prose, no bullets, no labels, no code fences.\n"
                        "- The expression must be a single valid next line.\n"
                        "- Reduce exactly one integer operation and keep the rest unchanged.\n"
                        "- Preserve canonical formatting with parentheses and spaces like '(2 + 3) * 4'.\n"
                        "Examples:\n"
                        "(2 + 3) * 4 -> 5 * 4\n"
                        "5 * 4 -> 20"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Original expression:\n{sample.expression}\n\n"
                        f"{rollback_note}\n"
                        f"Visible trace:\n{trace_block}\n\n"
                        "Return one corrected next expression only."
                    ),
                },
            ]
        else:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You reduce arithmetic expressions. Output only arithmetic expressions, one per line. "
                        "Each line must reduce exactly one integer operation. Do not explain. "
                        "When asked for the next line, output exactly one next expression and nothing else."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Original expression:\n{sample.expression}\n\n"
                        f"{rollback_note}\n"
                        f"Visible trace:\n{trace_block}\n\n"
                        "Output exactly one next line only."
                    ),
                },
            ]
        return messages, action_prefix

    def extract_trace_lines(self, text: str) -> list[str]:
        return extract_trace_lines(text)

    def is_terminal_line(self, line: str) -> bool:
        return is_terminal_expression(line)

    def check_trace(self, trace: list[str], sample: ArithmeticSample) -> TraceEvaluation:
        return check_trace(trace, sample.value)

    def prefix_invalidity_risk(self, trace: list[str], sample: ArithmeticSample) -> float:
        return prefix_invalidity_risk(trace, sample.value)

    def make_recoverable_prefix(
        self,
        prefix_lines: list[str],
        sample: ArithmeticSample,
        rng: random.Random,
        recoverable_style: str = "default",
    ) -> list[str] | None:
        if len(prefix_lines) < 2:
            return None
        if recoverable_style == "local_changed_token":
            corrupted = perturb_new_integer_token(prefix_lines[-2], prefix_lines[-1], rng)
        else:
            corrupted = re.sub(
                r"-?\d+",
                lambda match: str(int(match.group(0)) + rng.choice([-2, -1, 1, 2])),
                prefix_lines[-1],
                count=1,
            )
        if corrupted is None:
            return None
        if corrupted == prefix_lines[-1]:
            return None
        try:
            render_expr(parse_expression(corrupted))
        except ParseError:
            return None
        return list(prefix_lines[:-1]) + [corrupted]
