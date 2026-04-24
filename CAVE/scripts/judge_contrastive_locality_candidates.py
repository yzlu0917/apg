#!/usr/bin/env python3

import argparse
import ast
import json
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SYSTEM_PROMPT = """You are judging candidate pairs for the CAVE contrastive_locality object family.

Your job is not to rewrite or improve the pair. Your job is to decide whether
the pair really instantiates the intended family geometry.

Family definition:
- same question for keep and revise
- revise is caused by a real local error, not by changing the task
- there should be at least one nearby plausible local repair besides the gold repair
- only the gold repair should be checker-correct
- the verifier content should matter more than generic retry or full recomputation

You must be skeptical. If the checker/spec is inconsistent, or if the revise
trace still satisfies the stated constraints, reject the pair.

The candidate may contain misleading framing. Do not trust implied intent,
helpful notes, or claims that a fix is plausible. Judge only from the question,
traces, repair suffix, expected answer, and checker text.

If you notice any of these, reject the pair:
- checker/spec disagreement
- checker undercoverage that leaves a nearby non-gold repair behaviorally valid
- revise trace that does not actually violate the written constraint
- plan geometry that collapses to a single obvious linear order
- gold repair that is behaviorally equivalent to a nearby alternative

Program findings are authoritative for execution and structured-constraint
facts.

- Do not claim a code repair passes tests unless program findings show it, or
  the written checker logically guarantees it.
- Do not claim a plan order is valid or invalid contrary to program findings.
- If program findings already show a decisive failure, keep the verdict aligned
  with them unless the written question itself proves a stronger issue.

Use `borderline` only when the pair is close but one issue remains genuinely
uncertain from the written evidence.

Return JSON only.
"""


REFERENCE_SYSTEM_PROMPT = """You are writing a tiny Python reference implementation for a code task.

Rules:
- Use only the natural-language question as the source of truth.
- Ignore the candidate code, checker notes, and proposed repair.
- Return JSON only.
- Output schema:
  {
    "reference_code": "full python function definition"
  }
- The function must be executable Python and match the task exactly.
"""


REFERENCE_USER_PROMPT_TEMPLATE = """Write a minimal correct reference implementation for this task.

Question:
{question}

Return JSON only.
"""


USER_PROMPT_TEMPLATE = """Judge this contrastive_locality pair.

Pair ID: {pair_id}
Domain: {domain}
Question:
{question}

Keep example:
{keep_json}

Revise example:
{revise_json}

Program findings:
{program_findings_json}

Return a JSON object with this schema:
{{
  "pair_id": "string",
  "verdict": "accept|borderline|reject",
  "checks": {{
    "same_task_local_error": "pass|borderline|fail",
    "checker_disambiguates_repairs": "pass|borderline|fail",
    "gold_repair_informative": "pass|borderline|fail",
    "retry_vulnerable": "pass|borderline|fail"
  }},
  "rationale": {{
    "same_task_local_error": "short string",
    "checker_disambiguates_repairs": "short string",
    "gold_repair_informative": "short string",
    "retry_vulnerable": "short string"
  }},
  "blocking_issues": ["string"],
  "notes": "short string"
}}
"""


def parse_json_payload(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        for index, char in enumerate(text):
            if char != "{":
                continue
            try:
                payload, _ = decoder.raw_decode(text[index:])
                return payload
            except json.JSONDecodeError:
                continue
    raise ValueError(f"could not parse JSON payload from model output: {text[:200]!r}")


def load_records(paths: list[Path]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in paths:
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                record["_source_path"] = str(path)
                record["_line_no"] = line_no
                records.append(record)
    return records


def group_pairs(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_pair: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        key = (record["_source_path"], record["pair_id"])
        by_pair[key].append(record)

    pairs: list[dict[str, Any]] = []
    for source_path, pair_id in sorted(by_pair):
        items = by_pair[(source_path, pair_id)]
        if len(items) != 2:
            raise ValueError(
                f"pair {pair_id!r} from {source_path!r} does not contain exactly 2 records"
            )
        by_action = {item["gold_action"]: item for item in items}
        if set(by_action) != {"keep", "revise"}:
            raise ValueError(
                f"pair {pair_id!r} from {source_path!r} does not contain one keep and one revise record"
            )
        keep = by_action["keep"]
        revise = by_action["revise"]
        pairs.append(
            {
                "pair_id": pair_id,
                "domain": keep["domain"],
                "question": keep["question"],
                "keep": keep,
                "revise": revise,
                "source_path": source_path,
            }
        )
    return pairs


def build_user_prompt(pair: dict[str, Any]) -> str:
    keep_view = {
        "initial_trace": pair["keep"]["initial_trace"],
        "expected_final_answer": pair["keep"]["expected_final_answer"],
        "checker": pair["keep"]["checker"],
    }
    revise_view = {
        "initial_trace": pair["revise"]["initial_trace"],
        "gold_fail_span": pair["revise"]["gold_fail_span"],
        "gold_repair_suffix": pair["revise"]["gold_repair_suffix"],
        "expected_final_answer": pair["revise"]["expected_final_answer"],
        "checker": pair["revise"]["checker"],
    }
    return USER_PROMPT_TEMPLATE.format(
        pair_id=pair["pair_id"],
        domain=pair["domain"],
        question=pair["question"],
        keep_json=json.dumps(keep_view, ensure_ascii=False, indent=2),
        revise_json=json.dumps(revise_view, ensure_ascii=False, indent=2),
        program_findings_json=json.dumps(pair["program_findings"], ensure_ascii=False, indent=2),
    )


@dataclass
class JudgeResult:
    payload: dict[str, Any]
    usage: dict[str, Any] | None
    raw_text: str


def run_code_with_tests(code: str, tests: str) -> tuple[bool, str | None]:
    namespace: dict[str, Any] = {}
    try:
        exec(code, namespace, namespace)
        for line in tests.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            exec(stripped, namespace, namespace)
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"
    return True, None


def generate_code_alternative_spans(fail_span: str) -> list[str]:
    alternatives: set[str] = set()

    special_replacements = [
        (r"%\s*2\s*==\s*0", ["% 2 == 1", "% 2 != 0"]),
        (r"%\s*2\s*==\s*1", ["% 2 == 0", "% 2 != 0"]),
        (r"%\s*2\s*!=\s*0", ["% 2 == 0", "% 2 == 1"]),
    ]
    for pattern, replacements in special_replacements:
        if re.search(pattern, fail_span):
            for repl in replacements:
                alternatives.add(re.sub(pattern, repl, fail_span))

    generic_swaps = [
        (" or ", [" and "]),
        (" and ", [" or "]),
        (" == ", [" != "]),
        (" != ", [" == "]),
        (" + ", [" - ", " * "]),
        (" - ", [" + ", " * "]),
        (" * ", [" + ", " - "]),
        (" / ", [" + ", " * "]),
        (" += 2", [" += 1", " -= 1"]),
    ]
    for needle, replacements in generic_swaps:
        if needle in fail_span:
            for repl in replacements:
                alternatives.add(fail_span.replace(needle, repl))

    return sorted(alt for alt in alternatives if alt != fail_span)


def allows_negative_inputs(question: str) -> bool:
    lowered = question.lower()
    return not any(
        phrase in lowered
        for phrase in (
            "positive integer",
            "positive integers",
            "positive number",
            "positive numbers",
            "non-negative",
        )
    )


def parse_assert_calls(tests: str) -> list[tuple[str, list[Any]]]:
    calls: list[tuple[str, list[Any]]] = []
    for line in tests.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            node = ast.parse(stripped, mode="exec")
        except SyntaxError:
            continue
        if not node.body or not isinstance(node.body[0], ast.Assert):
            continue
        test_expr = node.body[0].test
        if not isinstance(test_expr, ast.Compare) or not isinstance(test_expr.left, ast.Call):
            continue
        func = test_expr.left.func
        if not isinstance(func, ast.Name):
            continue
        try:
            args = [ast.literal_eval(arg) for arg in test_expr.left.args]
        except Exception:  # noqa: BLE001
            continue
        calls.append((func.id, args))
    return calls


def mutate_value(value: Any, *, allow_negative: bool) -> list[Any]:
    variants: list[Any] = []
    if isinstance(value, int):
        variants.extend([value + 1, value - 1])
        if allow_negative and value != 0:
            variants.append(-value)
    elif isinstance(value, list) and all(isinstance(item, int) for item in value):
        variants.append(list(reversed(value)))
        if value:
            variants.append(value + [value[-1] + 1])
            variants.append(value[:-1] or value)
            if allow_negative:
                variants.append([-item for item in value])
        else:
            variants.append([1])
            if allow_negative:
                variants.append([-1])
    return variants


def build_probe_inputs(question: str, tests: str) -> list[list[Any]]:
    allow_negative = allows_negative_inputs(question)
    seen: set[str] = set()
    probes: list[list[Any]] = []
    for _, args in parse_assert_calls(tests):
        key = json.dumps(args, ensure_ascii=False, sort_keys=True)
        if key not in seen:
            probes.append(args)
            seen.add(key)
        for index, arg in enumerate(args):
            for variant in mutate_value(arg, allow_negative=allow_negative):
                mutated = list(args)
                mutated[index] = variant
                key = json.dumps(mutated, ensure_ascii=False, sort_keys=True)
                if key not in seen:
                    probes.append(mutated)
                    seen.add(key)
                if len(probes) >= 12:
                    return probes
    return probes[:12]


def load_callable(code: str) -> tuple[str, Any]:
    namespace: dict[str, Any] = {}
    exec(code, namespace, namespace)
    funcs = [name for name, obj in namespace.items() if callable(obj) and not name.startswith("__")]
    if not funcs:
        raise ValueError("no callable found in code")
    return funcs[0], namespace[funcs[0]]


def run_function_on_inputs(code: str, probe_inputs: list[list[Any]]) -> tuple[dict[str, Any], str | None]:
    try:
        _, fn = load_callable(code)
    except Exception as exc:  # noqa: BLE001
        return {}, f"{type(exc).__name__}: {exc}"
    outputs: dict[str, Any] = {}
    for args in probe_inputs:
        key = json.dumps(args, ensure_ascii=False)
        try:
            outputs[key] = {"ok": True, "value": fn(*args)}
        except Exception as exc:  # noqa: BLE001
            outputs[key] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return outputs, None


def analyze_code_pair(pair: dict[str, Any]) -> dict[str, Any]:
    checker = pair["keep"]["checker"]
    if checker.get("type") != "unit_test":
        return {"supported": False, "reason": "checker_type_not_supported"}

    structured = try_parse_reference_json(checker["reference"])
    tests = checker["reference"]
    repair_candidates: list[str] | None = None
    representation = "standard"
    if structured and structured.get("schema") == "code_local_repair_v1":
        tests_list = structured.get("tests")
        repair_candidates = structured.get("repair_candidates")
        if (
            not isinstance(tests_list, list)
            or not tests_list
            or not all(isinstance(item, str) and item.strip() for item in tests_list)
        ):
            return {"supported": False, "reason": "structured_code_tests_missing"}
        if (
            not isinstance(repair_candidates, list)
            or len(repair_candidates) < 3
            or not all(isinstance(item, str) and item.strip() for item in repair_candidates)
        ):
            return {"supported": False, "reason": "structured_code_repair_candidates_missing"}
        tests = "\n".join(tests_list)
        representation = "structured_local_repair_code"

    keep_code = pair["keep"]["initial_trace"]
    revise_code = pair["revise"]["initial_trace"]
    fail_span = pair["revise"]["gold_fail_span"]["text"]
    probe_inputs = build_probe_inputs(pair["question"], tests)
    reference_code, reference_usage, reference_error = synthesize_reference_code(pair)

    keep_passes, keep_error = run_code_with_tests(keep_code, tests)
    revise_passes, revise_error = run_code_with_tests(revise_code, tests)
    keep_probe_outputs, keep_probe_error = run_function_on_inputs(keep_code, probe_inputs)
    revise_probe_outputs, revise_probe_error = run_function_on_inputs(revise_code, probe_inputs)
    reference_probe_outputs = {}
    reference_probe_error = reference_error
    keep_vs_reference_mismatches: list[str] = []
    revise_vs_reference_mismatches: list[str] = []
    if reference_code is not None:
        reference_probe_outputs, run_error = run_function_on_inputs(reference_code, probe_inputs)
        if run_error is not None:
            reference_probe_error = run_error
        else:
            for key, expected in reference_probe_outputs.items():
                if keep_probe_outputs.get(key) != expected:
                    keep_vs_reference_mismatches.append(key)
                if revise_probe_outputs.get(key) != expected:
                    revise_vs_reference_mismatches.append(key)

    alternative_results = []
    if fail_span and fail_span in revise_code:
        candidate_spans = repair_candidates or generate_code_alternative_spans(fail_span)
        for alt_span in candidate_spans:
            if alt_span == fail_span:
                continue
            alt_code = revise_code.replace(fail_span, alt_span, 1)
            alt_passes, alt_error = run_code_with_tests(alt_code, tests)
            alt_probe_outputs, alt_probe_error = run_function_on_inputs(alt_code, probe_inputs)
            alternative_results.append(
                {
                    "alt_span": alt_span,
                    "passes": alt_passes,
                    "error": alt_error,
                    "matches_keep_text": alt_code == keep_code,
                    "probe_outputs": alt_probe_outputs,
                    "probe_error": alt_probe_error,
                    "matches_reference_probes": (
                        reference_code is not None
                        and alt_probe_error is None
                        and reference_probe_error is None
                        and alt_probe_outputs == reference_probe_outputs
                    ),
                }
            )

    return {
        "supported": True,
        "checker_type": "unit_test",
        "representation": representation,
        "keep_passes": keep_passes,
        "keep_error": keep_error,
        "revise_passes": revise_passes,
        "revise_error": revise_error,
        "probe_inputs": probe_inputs,
        "keep_probe_outputs": keep_probe_outputs,
        "keep_probe_error": keep_probe_error,
        "revise_probe_outputs": revise_probe_outputs,
        "revise_probe_error": revise_probe_error,
        "reference_code": reference_code,
        "reference_usage": reference_usage,
        "reference_probe_outputs": reference_probe_outputs,
        "reference_probe_error": reference_probe_error,
        "keep_vs_reference_mismatches": keep_vs_reference_mismatches,
        "revise_vs_reference_mismatches": revise_vs_reference_mismatches,
        "alternative_results": alternative_results,
    }


def extract_order(trace: str) -> list[str]:
    return re.findall(r"\b[A-Z]\b", trace)


def try_parse_reference_json(reference: str) -> dict[str, Any] | None:
    if not isinstance(reference, str):
        return None
    stripped = reference.strip()
    if not stripped.startswith("{"):
        return None
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def parse_order_from_tasks(trace: str, tasks: list[str]) -> list[str]:
    hits: list[tuple[int, str]] = []
    for task in tasks:
        for match in re.finditer(rf"\b{re.escape(task)}\b", trace):
            hits.append((match.start(), task))
    hits.sort()
    seen: set[str] = set()
    order: list[str] = []
    for _, task in hits:
        if task in seen:
            continue
        seen.add(task)
        order.append(task)
    return order


def enumerate_adjacent_swap_neighbors(order: list[str]) -> list[list[str]]:
    neighbors: list[list[str]] = []
    for index in range(len(order) - 1):
        swapped = list(order)
        swapped[index], swapped[index + 1] = swapped[index + 1], swapped[index]
        neighbors.append(swapped)
    return neighbors


def parse_precedence_constraints(reference: str) -> list[tuple[str, str]]:
    edges: set[tuple[str, str]] = set()
    clauses = re.split(r"[;\n.]+", reference)
    for clause in clauses:
        text = clause.strip()
        if not text:
            continue
        before_match = re.search(r"\b([A-Z])\b.*\bbefore\b.*\b([A-Z])\b", text, flags=re.IGNORECASE)
        after_match = re.search(r"\b([A-Z])\b.*\bafter\b.*\b([A-Z])\b", text, flags=re.IGNORECASE)
        if before_match:
            edges.add((before_match.group(1), before_match.group(2)))
        elif after_match:
            edges.add((after_match.group(2), after_match.group(1)))
    return sorted(edges)


def parse_task_durations(question: str) -> dict[str, int]:
    durations: dict[str, int] = {}
    for task, minutes in re.findall(r"\b([A-Z])\s*\([^)]*?(\d+)\s*min", question):
        durations[task] = int(minutes)
    return durations


def infer_schedule_starts(trace: str, durations: dict[str, int]) -> dict[str, int]:
    starts = {task: int(value) for task, value in re.findall(r"\b([A-Z])\s+at\s+(\d+)", trace)}

    together_match = re.search(
        r"\b([A-Z])\b.*?\band\b.*?\b([A-Z])\b.*?can start together",
        trace,
        flags=re.IGNORECASE,
    )
    if together_match:
        starts.setdefault(together_match.group(1), 0)
        starts.setdefault(together_match.group(2), 0)

    def finish(task: str) -> int | None:
        if task not in starts or task not in durations:
            return None
        return starts[task] + durations[task]

    changed = True
    while changed:
        changed = False
        for task, left, right in re.findall(
            r"\b([A-Z])\b[^.]*?must wait for both\s+\b([A-Z])\b\s+and\s+\b([A-Z])\b",
            trace,
            flags=re.IGNORECASE,
        ):
            left_finish = finish(left)
            right_finish = finish(right)
            if left_finish is not None and right_finish is not None and task not in starts:
                starts[task] = max(left_finish, right_finish)
                changed = True
        for task, dep in re.findall(
            r"\b([A-Z])\b[^.]*?must wait for\s+\b([A-Z])\b",
            trace,
            flags=re.IGNORECASE,
        ):
            dep_finish = finish(dep)
            if dep_finish is not None and task not in starts:
                starts[task] = dep_finish
                changed = True
    return starts


def compute_minimal_makespan(tasks: set[str], edges: list[tuple[str, str]], durations: dict[str, int]) -> int | None:
    if not tasks or any(task not in durations for task in tasks):
        return None
    incoming: dict[str, list[str]] = {task: [] for task in tasks}
    outgoing: dict[str, list[str]] = {task: [] for task in tasks}
    indegree = {task: 0 for task in tasks}
    for left, right in edges:
        if left in tasks and right in tasks:
            incoming[right].append(left)
            outgoing[left].append(right)
            indegree[right] += 1
    queue = sorted(task for task in tasks if indegree[task] == 0)
    topo: list[str] = []
    while queue:
        task = queue.pop(0)
        topo.append(task)
        for neighbor in sorted(outgoing[task]):
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)
                queue.sort()
    if len(topo) != len(tasks):
        return None

    earliest_start = {task: 0 for task in tasks}
    for task in topo:
        if incoming[task]:
            earliest_start[task] = max(earliest_start[parent] + durations[parent] for parent in incoming[task])
    return max(earliest_start[task] + durations[task] for task in tasks)


def validate_schedule(
    *,
    starts: dict[str, int],
    tasks: set[str],
    durations: dict[str, int],
    edges: list[tuple[str, str]],
    sequential: bool,
    minimal_makespan: int | None,
    require_minimal: bool,
) -> tuple[bool, list[str], int | None]:
    issues: list[str] = []
    if any(task not in starts for task in tasks):
        issues.append("missing start times for one or more tasks")
        return False, issues, None

    finishes = {task: starts[task] + durations[task] for task in tasks}
    makespan = max(finishes.values()) if finishes else None

    for left, right in edges:
        if starts[right] < finishes[left]:
            issues.append(f"{right} starts before {left} finishes")

    if sequential:
        ordered = sorted(tasks, key=lambda task: starts[task])
        for prev, curr in zip(ordered, ordered[1:]):
            if starts[curr] < finishes[prev]:
                issues.append(f"{curr} overlaps with {prev} in sequential schedule")
                break

    if require_minimal and minimal_makespan is not None and makespan != minimal_makespan:
        issues.append(f"makespan {makespan} is not minimal {minimal_makespan}")

    return not issues, issues, makespan


def looks_like_simple_order(trace: str) -> bool:
    order = extract_order(trace)
    return (
        len(order) >= 2
        and len(order) == len(set(order))
        and len(order) <= 8
        and ("->" in trace or "," in trace)
    )


def is_order_style_pair(pair: dict[str, Any]) -> bool:
    question = pair["question"].lower()
    keep_trace = pair["keep"]["initial_trace"]
    revise_trace = pair["revise"]["initial_trace"]
    if "total order" in question or "valid order" in question:
        return looks_like_simple_order(keep_trace) and looks_like_simple_order(revise_trace)
    return looks_like_simple_order(keep_trace) and looks_like_simple_order(revise_trace)


def validate_order(order: list[str], tasks: set[str], edges: list[tuple[str, str]]) -> bool:
    if set(order) != tasks or len(order) != len(tasks):
        return False
    position = {task: index for index, task in enumerate(order)}
    return all(position[left] < position[right] for left, right in edges)


def count_topological_orders(tasks: set[str], edges: list[tuple[str, str]], limit: int = 3) -> int:
    adjacency = {task: set() for task in tasks}
    indegree = {task: 0 for task in tasks}
    for left, right in edges:
        if right not in adjacency[left]:
            adjacency[left].add(right)
            indegree[right] += 1

    count = 0

    def dfs(current_order: list[str], current_indegree: dict[str, int]) -> None:
        nonlocal count
        if count >= limit:
            return
        if len(current_order) == len(tasks):
            count += 1
            return
        available = sorted(task for task in tasks if task not in current_order and current_indegree[task] == 0)
        for task in available:
            next_indegree = dict(current_indegree)
            for neighbor in adjacency[task]:
                next_indegree[neighbor] -= 1
            dfs(current_order + [task], next_indegree)

    dfs([], indegree)
    return count


def analyze_plan_pair(pair: dict[str, Any]) -> dict[str, Any]:
    checker = pair["keep"]["checker"]
    if checker.get("type") != "constraint_check":
        return {"supported": False, "reason": "checker_type_not_supported"}

    structured = try_parse_reference_json(checker["reference"])
    if structured and structured.get("schema") == "plan_local_repair_v1":
        tasks = structured.get("tasks", [])
        raw_edges = structured.get("edges", [])
        locality = structured.get("locality", {})
        if (
            not isinstance(tasks, list)
            or len(tasks) < 4
            or not all(isinstance(task, str) and task for task in tasks)
            or not isinstance(raw_edges, list)
        ):
            return {"supported": False, "reason": "structured_checker_malformed"}
        edges: list[tuple[str, str]] = []
        for edge in raw_edges:
            if (
                not isinstance(edge, list | tuple)
                or len(edge) != 2
                or not all(isinstance(item, str) and item for item in edge)
            ):
                return {"supported": False, "reason": "structured_checker_bad_edge"}
            edges.append((edge[0], edge[1]))
        if locality.get("kind") != "adjacent_swap" or locality.get("max_swaps", 1) != 1:
            return {"supported": False, "reason": "structured_locality_not_supported"}

        keep_order = parse_order_from_tasks(pair["keep"]["initial_trace"], tasks)
        revise_order = parse_order_from_tasks(pair["revise"]["initial_trace"], tasks)
        task_set = set(tasks)
        candidate_neighbors = enumerate_adjacent_swap_neighbors(revise_order)
        valid_neighbors = [order for order in candidate_neighbors if validate_order(order, task_set, edges)]
        findings = {
            "supported": True,
            "checker_type": "constraint_check",
            "representation": "structured_local_repair",
            "tasks": tasks,
            "edges": edges,
            "keep_order": keep_order,
            "revise_order": revise_order,
            "locality": locality,
            "candidate_neighbors": candidate_neighbors,
            "valid_local_repairs": valid_neighbors,
            "keep_valid": validate_order(keep_order, task_set, edges),
            "revise_valid": validate_order(revise_order, task_set, edges),
            "valid_order_count_limited": count_topological_orders(task_set, edges, limit=3),
        }
        findings["neighbor_count"] = len(candidate_neighbors)
        findings["valid_local_repair_count"] = len(valid_neighbors)
        findings["keep_is_unique_local_repair"] = len(valid_neighbors) == 1 and keep_order == valid_neighbors[0]
        return findings

    edges = parse_precedence_constraints(checker["reference"])
    keep_order = extract_order(pair["keep"]["initial_trace"])
    revise_order = extract_order(pair["revise"]["initial_trace"])
    tasks = set(keep_order) | set(revise_order) | {task for edge in edges for task in edge}

    durations = parse_task_durations(pair["question"])

    findings = {
        "supported": True,
        "checker_type": "constraint_check",
        "representation": "order_sequence" if is_order_style_pair(pair) else "other",
        "edges": edges,
        "keep_order": keep_order,
        "revise_order": revise_order,
        "durations": durations,
    }

    if findings["representation"] == "order_sequence" and edges and tasks:
        findings["keep_valid"] = validate_order(keep_order, tasks, edges)
        findings["revise_valid"] = validate_order(revise_order, tasks, edges)
        findings["valid_order_count_limited"] = count_topological_orders(tasks, edges, limit=3)
    elif durations and edges:
        sequential = "sequential" in pair["question"].lower() or "sequential" in checker["reference"].lower()
        require_minimal = (
            "minimum total time" in pair["question"].lower()
            or "must be minimized" in pair["question"].lower()
            or "no unnecessary delays" in checker["reference"].lower()
            or "immediately after" in checker["reference"].lower()
        )
        keep_starts = infer_schedule_starts(pair["keep"]["initial_trace"], durations)
        revise_starts = infer_schedule_starts(pair["revise"]["initial_trace"], durations)
        minimal_makespan = compute_minimal_makespan(tasks, edges, durations)
        keep_valid, keep_issues, keep_makespan = validate_schedule(
            starts=keep_starts,
            tasks=tasks,
            durations=durations,
            edges=edges,
            sequential=sequential,
            minimal_makespan=minimal_makespan,
            require_minimal=require_minimal,
        )
        revise_valid, revise_issues, revise_makespan = validate_schedule(
            starts=revise_starts,
            tasks=tasks,
            durations=durations,
            edges=edges,
            sequential=sequential,
            minimal_makespan=minimal_makespan,
            require_minimal=require_minimal,
        )
        findings["representation"] = "schedule"
        findings["keep_starts"] = keep_starts
        findings["revise_starts"] = revise_starts
        findings["minimal_makespan"] = minimal_makespan
        findings["keep_valid"] = keep_valid
        findings["revise_valid"] = revise_valid
        findings["keep_issues"] = keep_issues
        findings["revise_issues"] = revise_issues
        findings["keep_makespan"] = keep_makespan
        findings["revise_makespan"] = revise_makespan
        findings["valid_order_count_limited"] = None
    else:
        findings["keep_valid"] = None
        findings["revise_valid"] = None
        findings["valid_order_count_limited"] = None
    return findings


def build_program_findings(pair: dict[str, Any]) -> dict[str, Any]:
    if pair["domain"] == "code":
        return {"domain": "code", "analysis": analyze_code_pair(pair)}
    if pair["domain"] == "plan":
        return {"domain": "plan", "analysis": analyze_plan_pair(pair)}
    return {"domain": pair["domain"], "analysis": {"supported": False, "reason": "domain_not_supported"}}


def auto_decide_from_findings(pair: dict[str, Any]) -> dict[str, Any] | None:
    analysis = pair["program_findings"]["analysis"]
    if pair["domain"] == "code" and analysis.get("supported"):
        if analysis.get("representation") == "structured_local_repair_code":
            passing_alternatives = [
                item for item in analysis["alternative_results"] if item["passes"]
            ]
            non_keep_passing = [
                item for item in passing_alternatives if not item["matches_keep_text"]
            ]
            if (
                analysis["keep_passes"]
                and not analysis["revise_passes"]
                and len(passing_alternatives) == 1
                and passing_alternatives[0]["matches_keep_text"]
                and not non_keep_passing
                and len(analysis["alternative_results"]) >= 3
            ):
                return {
                    "verdict": "accept",
                    "checks": {
                        "same_task_local_error": "pass",
                        "checker_disambiguates_repairs": "pass",
                        "gold_repair_informative": "pass",
                        "retry_vulnerable": "borderline",
                    },
                    "rationale": {
                        "same_task_local_error": "Structured code pair changes one local condition while keeping the same function task.",
                        "checker_disambiguates_repairs": "Execution shows keep passes, revise fails, and every non-gold listed local repair still fails.",
                        "gold_repair_informative": "The gold repair is the only listed local repair that restores the passing implementation.",
                        "retry_vulnerable": "The exact local-repair geometry is strong, though generic retry risk still needs human review rather than pure execution.",
                    },
                    "blocking_issues": [],
                    "notes": "Auto-accepted from structured local-repair code findings.",
                    "judging_mode": "auto_accept",
                }
        blocking = []
        if not analysis["keep_passes"]:
            blocking.append("keep trace fails the written unit tests")
        if analysis["revise_passes"]:
            blocking.append("revise trace already passes the written unit tests")
        alt_passes = [
            item["alt_span"]
            for item in analysis["alternative_results"]
            if item["passes"] and not item["matches_keep_text"]
        ]
        if alt_passes:
            blocking.append(
                "heuristic alternative repairs also pass unit tests: " + ", ".join(alt_passes[:3])
            )
        if analysis.get("keep_vs_reference_mismatches"):
            blocking.append(
                "keep trace disagrees with synthesized reference on probes: "
                + ", ".join(analysis["keep_vs_reference_mismatches"][:3])
            )
        alt_probe_matches = [
            item["alt_span"]
            for item in analysis["alternative_results"]
            if item.get("matches_reference_probes") and not item["matches_keep_text"]
        ]
        if alt_probe_matches:
            blocking.append(
                "heuristic alternative repairs match synthesized reference probes: "
                + ", ".join(alt_probe_matches[:3])
            )
        if blocking:
            return {
                "verdict": "reject",
                "checks": {
                    "same_task_local_error": "pass",
                    "checker_disambiguates_repairs": "fail",
                    "gold_repair_informative": "borderline",
                    "retry_vulnerable": "pass",
                },
                "rationale": {
                    "same_task_local_error": "Pair still represents the same code task with a local trace change.",
                    "checker_disambiguates_repairs": "; ".join(blocking),
                    "gold_repair_informative": "Gold repair may still be locally meaningful, but deterministic checks already show checker weakness.",
                    "retry_vulnerable": "Execution-backed checks do not suggest the issue is only generic retry.",
                },
                "blocking_issues": blocking,
                "notes": "Auto-rejected from execution-backed code findings.",
                "judging_mode": "auto_reject",
            }

    if pair["domain"] == "plan" and analysis.get("supported") and analysis.get("representation") == "order_sequence":
        blocking = []
        if analysis["keep_valid"] is False:
            blocking.append("keep trace does not satisfy the written precedence constraints")
        if analysis["revise_valid"] is True:
            blocking.append("revise trace already satisfies the written precedence constraints")
        if analysis["valid_order_count_limited"] and analysis["valid_order_count_limited"] > 1:
            blocking.append("written constraints allow multiple valid total orders")
        if blocking:
            return {
                "verdict": "reject",
                "checks": {
                    "same_task_local_error": "pass",
                    "checker_disambiguates_repairs": "fail",
                    "gold_repair_informative": "fail",
                    "retry_vulnerable": "pass",
                },
                "rationale": {
                    "same_task_local_error": "Pair still targets the same planning task with a local order edit.",
                    "checker_disambiguates_repairs": "; ".join(blocking),
                    "gold_repair_informative": "Gold repair is not uniquely identified when the written constraints already permit other orders or the revise trace is valid.",
                    "retry_vulnerable": "Structured constraint checks show the main issue is boundary mismatch rather than retry alone.",
                },
                "blocking_issues": blocking,
                "notes": "Auto-rejected from structured plan findings.",
                "judging_mode": "auto_reject",
            }
    if pair["domain"] == "plan" and analysis.get("supported") and analysis.get("representation") == "schedule":
        blocking = []
        if analysis["keep_valid"] is False:
            blocking.append("keep schedule violates parsed constraints: " + "; ".join(analysis.get("keep_issues", [])[:3]))
        if analysis["revise_valid"] is True:
            blocking.append("revise schedule satisfies parsed constraints")
        if blocking:
            return {
                "verdict": "reject",
                "checks": {
                    "same_task_local_error": "pass",
                    "checker_disambiguates_repairs": "fail",
                    "gold_repair_informative": "fail",
                    "retry_vulnerable": "pass",
                },
                "rationale": {
                    "same_task_local_error": "Pair still targets the same scheduling task with a local trace change.",
                    "checker_disambiguates_repairs": "; ".join(blocking),
                    "gold_repair_informative": "Gold repair is not usable if the written schedule facts already make keep invalid or revise valid.",
                    "retry_vulnerable": "Schedule semantics expose a boundary mismatch before any retry story matters.",
                },
                "blocking_issues": blocking,
                "notes": "Auto-rejected from schedule-style plan findings.",
                "judging_mode": "auto_reject",
            }
    if pair["domain"] == "plan" and analysis.get("supported") and analysis.get("representation") == "structured_local_repair":
        blocking = []
        if analysis["keep_valid"] is False:
            blocking.append("keep order does not satisfy structured precedence constraints")
        if analysis["revise_valid"] is True:
            blocking.append("revise order already satisfies structured precedence constraints")
        if analysis["neighbor_count"] < 2:
            blocking.append("local repair neighborhood is too small to support contrastive locality")
        if analysis["valid_local_repair_count"] != 1:
            blocking.append(
                f"structured local neighborhood has {analysis['valid_local_repair_count']} valid repairs instead of exactly 1"
            )
        if not analysis["keep_is_unique_local_repair"]:
            blocking.append("keep order is not the unique valid local repair from revise order")
        if blocking:
            return {
                "verdict": "reject",
                "checks": {
                    "same_task_local_error": "pass",
                    "checker_disambiguates_repairs": "fail",
                    "gold_repair_informative": "fail",
                    "retry_vulnerable": "pass",
                },
                "rationale": {
                    "same_task_local_error": "Pair still targets the same structured planning task with a local order edit.",
                    "checker_disambiguates_repairs": "; ".join(blocking),
                    "gold_repair_informative": "Gold repair is only useful if the structured checker leaves exactly one valid local repair.",
                    "retry_vulnerable": "Structured locality failed before any retry advantage could matter.",
                },
                "blocking_issues": blocking,
                "notes": "Auto-rejected from structured local-repair plan findings.",
                "judging_mode": "auto_reject",
            }
    return None


def call_api(
    *,
    model: str,
    base_url: str,
    api_key: str,
    user_prompt: str,
    system_prompt: str = SYSTEM_PROMPT,
    temperature: float,
    max_output_tokens: int,
    request_timeout: float,
) -> JudgeResult:
    import httpx
    from openai import OpenAI

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        http_client=httpx.Client(trust_env=False, timeout=request_timeout),
    )
    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        max_completion_tokens=max_output_tokens,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    text = response.choices[0].message.content
    return JudgeResult(
        payload=parse_json_payload(text),
        usage=response.usage.model_dump() if response.usage else None,
        raw_text=text,
    )


def synthesize_reference_code(pair: dict[str, Any]) -> tuple[str | None, dict[str, Any] | None, str | None]:
    try:
        result = call_api(
            model=pair["_judge_args"]["model"],
            base_url=pair["_judge_args"]["base_url"],
            api_key=pair["_judge_args"]["api_key"],
            user_prompt=REFERENCE_USER_PROMPT_TEMPLATE.format(question=pair["question"]),
            system_prompt=REFERENCE_SYSTEM_PROMPT,
            temperature=0.0,
            max_output_tokens=700,
            request_timeout=pair["_judge_args"]["request_timeout"],
        )
    except Exception as exc:  # noqa: BLE001
        return None, None, f"{type(exc).__name__}: {exc}"

    reference_code = result.payload.get("reference_code")
    if not isinstance(reference_code, str) or not reference_code.strip():
        return None, result.usage, "missing reference_code"
    return reference_code, result.usage, None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_jsonl", nargs="+", help="One or more JSONL candidate files.")
    parser.add_argument("--output-jsonl", required=True, help="Path to write per-pair judge results.")
    parser.add_argument("--output-summary-json", required=True, help="Path to write aggregate summary JSON.")
    parser.add_argument("--output-md", help="Optional markdown summary path.")
    parser.add_argument("--provider", choices=["api"], default="api", help="Judge backend.")
    parser.add_argument("--model", default="ep-20251213141929-gk2jb", help="Judge model name.")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("CAVE_API_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
        help="API base URL.",
    )
    parser.add_argument("--api-key", default=os.environ.get("CAVE_API_KEY"), help="API key.")
    parser.add_argument("--temperature", type=float, default=0.0, help="Judge temperature.")
    parser.add_argument("--max-output-tokens", type=int, default=700, help="Max completion tokens.")
    parser.add_argument("--request-timeout", type=float, default=60.0, help="Per-request timeout in seconds.")
    return parser.parse_args()


def validate_judge_payload(payload: dict[str, Any], expected_pair_id: str) -> None:
    if payload.get("pair_id") != expected_pair_id:
        raise ValueError(
            f"judge pair_id mismatch: expected {expected_pair_id!r}, got {payload.get('pair_id')!r}"
        )
    if payload.get("verdict") not in {"accept", "borderline", "reject"}:
        raise ValueError(f"invalid verdict for {expected_pair_id!r}")
    checks = payload.get("checks")
    rationale = payload.get("rationale")
    required_checks = {
        "same_task_local_error",
        "checker_disambiguates_repairs",
        "gold_repair_informative",
        "retry_vulnerable",
    }
    if not isinstance(checks, dict) or set(checks) != required_checks:
        raise ValueError(f"judge checks missing or malformed for {expected_pair_id!r}")
    if not isinstance(rationale, dict) or set(rationale) != required_checks:
        raise ValueError(f"judge rationale missing or malformed for {expected_pair_id!r}")
    for key in required_checks:
        if checks[key] not in {"pass", "borderline", "fail"}:
            raise ValueError(f"invalid check value {checks[key]!r} for {expected_pair_id!r}/{key}")
        if not isinstance(rationale[key], str) or not rationale[key].strip():
            raise ValueError(f"empty rationale for {expected_pair_id!r}/{key}")
    blocking_issues = payload.get("blocking_issues")
    if not isinstance(blocking_issues, list):
        raise ValueError(f"blocking_issues must be a list for {expected_pair_id!r}")
    if not isinstance(payload.get("notes"), str):
        raise ValueError(f"notes must be a string for {expected_pair_id!r}")


def build_markdown(results: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines = [
        "# Contrastive Locality Judge Summary",
        "",
        f"Pairs judged: `{summary['pairs_judged']}`",
        f"Verdicts: `{summary['verdict_counts']}`",
        "",
        "## Per Pair",
    ]
    for item in results:
        lines.extend(
            [
                "",
                f"### {item['pair_id']}",
                "",
                f"- Source: `{item['source_path']}`",
                f"- Verdict: `{item['verdict']}`",
                f"- Mode: `{item['judging_mode']}`",
                f"- Checks: `{item['checks']}`",
                f"- Blocking issues: `{item['blocking_issues']}`",
                f"- Program findings: `{item['program_findings']}`",
                f"- Notes: {item['notes']}",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()

    input_paths = [Path(path) for path in args.input_jsonl]
    records = load_records(input_paths)
    pairs = group_pairs(records)

    output_jsonl = Path(args.output_jsonl)
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    output_jsonl.write_text("", encoding="utf-8")

    results: list[dict[str, Any]] = []
    usage_log: list[dict[str, Any]] = []

    for pair in pairs:
        pair["_judge_args"] = {
            "model": args.model,
            "base_url": args.base_url,
            "api_key": args.api_key,
            "request_timeout": args.request_timeout,
        }
        pair["program_findings"] = build_program_findings(pair)
        auto_result = auto_decide_from_findings(pair)
        result = None
        if auto_result is None:
            if args.provider == "api" and not args.api_key:
                print(
                    f"error: --api-key or CAVE_API_KEY is required for provider=api when pair {pair['pair_id']} needs model judging",
                    file=sys.stderr,
                )
                return 2
            prompt = build_user_prompt(pair)
            result = call_api(
                model=args.model,
                base_url=args.base_url,
                api_key=args.api_key,
                user_prompt=prompt,
                temperature=args.temperature,
                max_output_tokens=args.max_output_tokens,
                request_timeout=args.request_timeout,
            )
            validate_judge_payload(result.payload, pair["pair_id"])
            item = {
                "pair_id": pair["pair_id"],
                "domain": pair["domain"],
                "source_path": pair["source_path"],
                "verdict": result.payload["verdict"],
                "checks": result.payload["checks"],
                "rationale": result.payload["rationale"],
                "blocking_issues": result.payload["blocking_issues"],
                "notes": result.payload["notes"],
                "judging_mode": "model_with_program_findings",
                "program_findings": pair["program_findings"]["analysis"],
            }
        else:
            item = {
                "pair_id": pair["pair_id"],
                "domain": pair["domain"],
                "source_path": pair["source_path"],
                "verdict": auto_result["verdict"],
                "checks": auto_result["checks"],
                "rationale": auto_result["rationale"],
                "blocking_issues": auto_result["blocking_issues"],
                "notes": auto_result["notes"],
                "judging_mode": auto_result["judging_mode"],
                "program_findings": pair["program_findings"]["analysis"],
            }
        results.append(item)
        if result is not None:
            usage_log.append(
                {
                    "pair_id": pair["pair_id"],
                    "usage": result.usage,
                    "raw_text": result.raw_text,
                }
            )
        with output_jsonl.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"judged {pair['pair_id']} -> {item['verdict']} ({item['judging_mode']})", flush=True)

    verdict_counts = Counter(item["verdict"] for item in results)
    check_counts = {
        key: Counter(item["checks"][key] for item in results)
        for key in (
            "same_task_local_error",
            "checker_disambiguates_repairs",
            "gold_repair_informative",
            "retry_vulnerable",
        )
    }
    summary = {
        "pairs_judged": len(results),
        "verdict_counts": dict(sorted(verdict_counts.items())),
        "check_counts": {key: dict(sorted(counter.items())) for key, counter in sorted(check_counts.items())},
        "judging_mode_counts": dict(sorted(Counter(item["judging_mode"] for item in results).items())),
        "usage_log": usage_log,
    }

    summary_path = Path(args.output_summary_json)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.output_md:
        output_md = Path(args.output_md)
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(build_markdown(results, summary), encoding="utf-8")

    print(f"wrote judge jsonl to {output_jsonl}")
    print(f"wrote judge summary json to {summary_path}")
    if args.output_md:
        print(f"wrote judge markdown to {args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
