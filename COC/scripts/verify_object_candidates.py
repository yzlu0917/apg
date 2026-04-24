#!/usr/bin/env python
import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-file", required=True)
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output-file", default="")
    return parser.parse_args()


def load_seed_map(seed_file: str) -> Dict[str, Dict]:
    seeds = json.loads(Path(seed_file).read_text())
    return {seed["source_task_id"]: seed for seed in seeds}


def extract_numeric_answer(text: str) -> float | None:
    matches = re.findall(r"-?\d+(?:\.\d+)?", text)
    if not matches:
        return None
    return float(matches[-1])


def verify_math(answer: str, verifier_note: str) -> Tuple[bool, str]:
    expected = extract_numeric_answer(verifier_note)
    actual = extract_numeric_answer(answer)
    if expected is None:
        return False, "expected_value_missing"
    if actual is None:
        return False, "answer_value_missing"
    passed = abs(actual - expected) < 1e-9
    return passed, f"expected={expected}, actual={actual}"


def run_function(code: str, fn_name: str):
    namespace: Dict[str, object] = {}
    exec(code, namespace, namespace)
    if fn_name not in namespace:
        raise KeyError(f"function_not_found:{fn_name}")
    return namespace[fn_name]


def verify_code(answer: str, source_task_id: str) -> Tuple[bool, str]:
    try:
        if source_task_id == "code_sum_even_001":
            fn = run_function(answer, "sum_even")
            tests = [
                ("sum_even([1,2,3,4])", fn([1, 2, 3, 4]), 6),
                ("sum_even([1,3,5])", fn([1, 3, 5]), 0),
                ("sum_even([-2,5,8])", fn([-2, 5, 8]), 6),
            ]
        elif source_task_id == "code_reverse_string_001":
            fn = run_function(answer, "reverse_string")
            tests = [
                ("reverse_string('abc')", fn("abc"), "cba"),
                ("reverse_string('')", fn(""), ""),
                ("reverse_string('aa!')", fn("aa!"), "!aa"),
            ]
        elif source_task_id == "code_unique_preserve_order_001":
            fn = run_function(answer, "unique_preserve_order")
            tests = [
                ("unique_preserve_order([3,1,3,2,1])", fn([3, 1, 3, 2, 1]), [3, 1, 2]),
                ("unique_preserve_order(['b','a','b'])", fn(["b", "a", "b"]), ["b", "a"]),
                ("unique_preserve_order([])", fn([]), []),
            ]
        elif source_task_id == "code_count_uppercase_001":
            fn = run_function(answer, "count_uppercase")
            tests = [
                ("count_uppercase('AbC')", fn("AbC"), 2),
                ("count_uppercase('abc')", fn("abc"), 0),
                ("count_uppercase('HELlo!')", fn("HELlo!"), 3),
            ]
        elif source_task_id == "code_first_nonzero_001":
            fn = run_function(answer, "first_nonzero")
            tests = [
                ("first_nonzero([0,0,5,0])", fn([0, 0, 5, 0]), 5),
                ("first_nonzero([0,0,0])", fn([0, 0, 0]), None),
                ("first_nonzero([-3,0,2])", fn([-3, 0, 2]), -3),
            ]
        elif source_task_id == "code_count_negatives_001":
            fn = run_function(answer, "count_negatives")
            tests = [
                ("count_negatives([1,-2,3,-4])", fn([1, -2, 3, -4]), 2),
                ("count_negatives([0,2,5])", fn([0, 2, 5]), 0),
                ("count_negatives([-1,-1,-1])", fn([-1, -1, -1]), 3),
            ]
        elif source_task_id == "code_last_even_001":
            fn = run_function(answer, "last_even")
            tests = [
                ("last_even([1,2,3,4,5])", fn([1, 2, 3, 4, 5]), 4),
                ("last_even([1,3,5])", fn([1, 3, 5]), None),
                ("last_even([8,7,6,5])", fn([8, 7, 6, 5]), 6),
            ]
        elif source_task_id == "code_count_positives_001":
            fn = run_function(answer, "count_positives")
            tests = [
                ("count_positives([1,-2,3,0])", fn([1, -2, 3, 0]), 2),
                ("count_positives([0,0,0])", fn([0, 0, 0]), 0),
                ("count_positives([-1,2,5])", fn([-1, 2, 5]), 2),
            ]
        elif source_task_id == "code_first_even_001":
            fn = run_function(answer, "first_even")
            tests = [
                ("first_even([1,3,4,6])", fn([1, 3, 4, 6]), 4),
                ("first_even([1,3,5])", fn([1, 3, 5]), None),
                ("first_even([8,7,6])", fn([8, 7, 6]), 8),
            ]
        elif source_task_id == "code_count_odds_001":
            fn = run_function(answer, "count_odds")
            tests = [
                ("count_odds([1,2,3,4])", fn([1, 2, 3, 4]), 2),
                ("count_odds([2,4,6])", fn([2, 4, 6]), 0),
                ("count_odds([5,7,8])", fn([5, 7, 8]), 2),
            ]
        elif source_task_id == "code_last_positive_001":
            fn = run_function(answer, "last_positive")
            tests = [
                ("last_positive([-1,2,-3,4])", fn([-1, 2, -3, 4]), 4),
                ("last_positive([-5,0,-1])", fn([-5, 0, -1]), None),
                ("last_positive([3,-2,1])", fn([3, -2, 1]), 1),
            ]
        else:
            return False, f"unsupported_source_task_id:{source_task_id}"
    except Exception as exc:
        return False, f"execution_error:{type(exc).__name__}:{exc}"

    failed = []
    for name, actual, expected in tests:
        if actual != expected:
            failed.append(f"{name}: expected={expected!r}, actual={actual!r}")
    if failed:
        return False, "; ".join(failed)
    return True, "all_tests_passed"


def verify_answer(answer: str, seed: Dict) -> Tuple[bool, str]:
    if seed["domain"] == "math":
        return verify_math(answer, seed["verifier_note"])
    if seed["domain"] == "code":
        return verify_code(answer, seed["source_task_id"])
    return False, "unsupported_domain"


def preferred_label(a_pass: bool, b_pass: bool) -> str:
    if a_pass and not b_pass:
        return "A"
    if b_pass and not a_pass:
        return "B"
    if a_pass and b_pass:
        return "tie"
    return "neither"


def main():
    args = parse_args()
    seed_map = load_seed_map(args.seed_file)
    rows = [json.loads(line) for line in Path(args.input_file).read_text().splitlines() if line.strip()]
    verified_rows: List[Dict] = []
    for row in rows:
        seed = seed_map[row["source_task_id"]]
        a_pass, a_note = verify_answer(row["answer_a"], seed)
        b_pass, b_note = verify_answer(row["answer_b"], seed)
        verifier_pref = preferred_label(a_pass, b_pass)
        row["verifier_a_pass"] = a_pass
        row["verifier_a_note"] = a_note
        row["verifier_b_pass"] = b_pass
        row["verifier_b_note"] = b_note
        row["verifier_preferred_label"] = verifier_pref
        row["verifier_gold_consistent"] = verifier_pref == row["gold_label"]
        verified_rows.append(row)

    if args.output_file:
        output_path = Path(args.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w") as f:
            for row in verified_rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
    else:
        for row in verified_rows:
            print(json.dumps(row, ensure_ascii=False))


if __name__ == "__main__":
    main()
