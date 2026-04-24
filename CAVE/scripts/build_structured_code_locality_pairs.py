#!/usr/bin/env python3

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="Output JSONL path.")
    parser.add_argument("--meta-output", help="Optional metadata JSON path.")
    parser.add_argument("--limit", type=int, default=4, help="Maximum number of pairs to emit.")
    parser.add_argument("--seed", type=int, default=3101, help="Seed suffix for pair ids.")
    return parser.parse_args()


def render_count_code(function_name: str, condition: str) -> str:
    return (
        f"def {function_name}(nums):\n"
        "    count = 0\n"
        "    for n in nums:\n"
        f"        if {condition}:\n"
        "            count += 1\n"
        "    return count"
    )


def render_sum_code(function_name: str, condition: str) -> str:
    return (
        f"def {function_name}(nums):\n"
        "    total = 0\n"
        "    for n in nums:\n"
        f"        if {condition}:\n"
        "            total += n\n"
        "    return total"
    )


def run_function(code: str, function_name: str, arg):
    namespace: dict[str, object] = {}
    exec(code, namespace, namespace)
    return namespace[function_name](arg)


def greedy_select_tests(gold_outputs: list[object], candidate_outputs: dict[str, list[object]]) -> list[int]:
    unresolved = set(candidate_outputs)
    selected: list[int] = []
    while unresolved:
        best_index = None
        best_cover: set[str] = set()
        for index, gold_output in enumerate(gold_outputs):
            cover = {name for name in unresolved if candidate_outputs[name][index] != gold_output}
            if len(cover) > len(best_cover):
                best_cover = cover
                best_index = index
        if best_index is None or not best_cover:
            return []
        selected.append(best_index)
        unresolved -= best_cover
    return selected


def make_checker_reference(function_name: str, tests: list[str], repair_candidates: list[str]) -> str:
    payload = {
        "schema": "code_local_repair_v1",
        "entrypoint": function_name,
        "tests": tests,
        "repair_candidates": repair_candidates,
    }
    return json.dumps(payload, ensure_ascii=False)


def build_pair(pair_id: str, spec: dict, revise_condition: str, tests: list[str]) -> list[dict]:
    function_name = spec["function_name"]
    builder = spec["builder"]
    gold_condition = spec["gold_condition"]
    keep_code = builder(function_name, gold_condition)
    revise_code = builder(function_name, revise_condition)
    repair_candidates = list(dict.fromkeys([gold_condition, *spec["candidate_conditions"]]))
    wrong_candidates = [condition for condition in repair_candidates if condition not in {gold_condition, revise_condition}]
    wrong_example = wrong_candidates[0]

    question = spec["question"]
    checker_reference = make_checker_reference(function_name, tests, repair_candidates)
    common = {
        "pair_id": pair_id,
        "domain": "code",
        "question": question,
        "checker": {"type": "unit_test", "reference": checker_reference},
        "candidate_source": "search_constructed",
        "generation_family": "contrastive_locality",
        "review_status": "pending",
    }

    return [
        {
            "id": f"{pair_id}_keep",
            **common,
            "initial_trace": keep_code,
            "gold_fail_span": {"text": "", "kind": "none"},
            "gold_action": "keep",
            "gold_repair_suffix": "",
            "expected_final_answer": keep_code,
            "utility_delta": {"keep": 1.0, "revise": 0.0, "abstain": 0.0},
            "notes": "Structured keep code passes all tests and matches the unique valid local repair target.",
        },
        {
            "id": f"{pair_id}_revise",
            **common,
            "initial_trace": revise_code,
            "gold_fail_span": {"text": revise_condition, "kind": "expression"},
            "gold_action": "revise",
            "gold_repair_suffix": gold_condition,
            "expected_final_answer": keep_code,
            "utility_delta": {"keep": 0.0, "revise": 1.0, "abstain": 0.0},
            "notes": (
                f"Revise code fails the structured checker. "
                f"A nearby wrong repair {wrong_example} still looks plausible but fails the tests. "
                f"The unique valid local repair is {gold_condition}."
            ),
        },
    ]


def make_asserts(function_name: str, input_pool: list[list[int]], outputs: list[object], indices: list[int]) -> list[str]:
    tests: list[str] = []
    for index in indices:
        arg = input_pool[index]
        expected = outputs[index]
        tests.append(f"assert {function_name}({arg!r}) == {expected!r}")
    return tests


def candidate_specs() -> list[dict]:
    return [
        {
            "name": "count_positive_even",
            "function_name": "count_positive_even",
            "builder": render_count_code,
            "question": "Write a function count_positive_even(nums) that counts numbers in nums that are positive and even.",
            "gold_condition": "n > 0 and n % 2 == 0",
            "candidate_conditions": [
                "n >= 0 and n % 2 == 0",
                "n > 0 or n % 2 == 0",
                "n > 0 and n % 2 != 0",
                "n >= 0 or n % 2 == 0",
            ],
            "input_pool": [[2, 4, -2, 0], [1, 3, 5], [-4, -2, 0], [6, 7, 8, -8], [0, 2, 3]],
        },
        {
            "name": "count_positive_multiples_of_three",
            "function_name": "count_positive_multiples_of_three",
            "builder": render_count_code,
            "question": "Write a function count_positive_multiples_of_three(nums) that counts numbers in nums that are positive multiples of 3.",
            "gold_condition": "n > 0 and n % 3 == 0",
            "candidate_conditions": [
                "n >= 0 and n % 3 == 0",
                "n > 0 or n % 3 == 0",
                "n < 0 and n % 3 == 0",
                "n > 0 and n % 2 == 0",
            ],
            "input_pool": [[3, 6, -3, 0], [1, 2, 4], [-6, -3, 9], [12, 15, -12], [0, 3, 5]],
        },
        {
            "name": "count_negative_odd",
            "function_name": "count_negative_odd",
            "builder": render_count_code,
            "question": "Write a function count_negative_odd(nums) that counts numbers in nums that are negative odd integers.",
            "gold_condition": "n < 0 and n % 2 != 0",
            "candidate_conditions": [
                "n < 0 and n % 2 == 0",
                "n < 0 or n % 2 != 0",
                "n <= 0 or n % 2 != 0",
                "n > 0 and n % 2 != 0",
            ],
            "input_pool": [[-1, -3, 2, 4], [0, -5, -4, 5], [1, 3, 7], [-7, -2, -9], [0, -1, 2]],
        },
        {
            "name": "count_positive_divisible_by_four",
            "function_name": "count_positive_divisible_by_four",
            "builder": render_count_code,
            "question": "Write a function count_positive_divisible_by_four(nums) that counts numbers in nums that are positive and divisible by 4.",
            "gold_condition": "n > 0 and n % 4 == 0",
            "candidate_conditions": [
                "n < 0 and n % 4 == 0",
                "n > 0 or n % 4 == 0",
                "n > 0 and n % 2 == 0",
                "n >= 0 or n % 4 == 0",
            ],
            "input_pool": [[4, 8, -4, 0], [2, 6, 10], [-8, -4, 12], [16, 3, 5], [0, 4, 5]],
        },
        {
            "name": "sum_negative_odd_strict",
            "function_name": "sum_negative_odd_strict",
            "builder": render_sum_code,
            "question": "Write a function sum_negative_odd_strict(nums) that returns the sum of numbers in nums that are negative odd integers.",
            "gold_condition": "n < 0 and n % 2 != 0",
            "candidate_conditions": [
                "n < 0 and n % 2 == 0",
                "n < 0 or n % 2 != 0",
                "n <= 0 or n % 2 != 0",
                "n > 0 and n % 2 != 0",
            ],
            "input_pool": [[-1, -3, 2, 4], [0, -5, -4, 5], [1, 3, 7], [-7, -2, -9], [0, -1, 2]],
        },
        {
            "name": "count_nonzero_multiples_of_five",
            "function_name": "count_nonzero_multiples_of_five",
            "builder": render_count_code,
            "question": "Write a function count_nonzero_multiples_of_five(nums) that counts numbers in nums that are nonzero multiples of 5.",
            "gold_condition": "n != 0 and n % 5 == 0",
            "candidate_conditions": [
                "n >= 0 and n % 5 == 0",
                "n != 0 or n % 5 == 0",
                "n == 0 and n % 5 == 0",
                "n != 0 and n % 5 != 0",
            ],
            "input_pool": [[5, 10, 0, -5], [1, 2, 3], [0, 5, 7], [-10, -5, 0], [15, 20, 1]],
        },
    ]


def search_pairs(limit: int, seed: int) -> list[dict]:
    found: list[dict] = []
    pair_index = 0

    for spec in candidate_specs():
        function_name = spec["function_name"]
        builder = spec["builder"]
        gold_condition = spec["gold_condition"]
        gold_code = builder(function_name, gold_condition)
        input_pool = spec["input_pool"]
        gold_outputs = [run_function(gold_code, function_name, arg) for arg in input_pool]

        candidate_outputs = {}
        for condition in spec["candidate_conditions"]:
            code = builder(function_name, condition)
            candidate_outputs[condition] = [run_function(code, function_name, arg) for arg in input_pool]

        selected_indices = greedy_select_tests(gold_outputs, candidate_outputs)
        if not selected_indices:
            continue
        tests = make_asserts(function_name, input_pool, gold_outputs, selected_indices)

        for revise_condition in spec["candidate_conditions"]:
            if candidate_outputs[revise_condition] == gold_outputs:
                continue
            pair_id = f"code_structured_search_{seed + pair_index}"
            found.extend(build_pair(pair_id, spec, revise_condition, tests))
            pair_index += 1
            break
        if pair_index >= limit:
            return found
    return found


def main() -> int:
    args = parse_args()
    records = search_pairs(args.limit, args.seed)
    if len(records) != args.limit * 2:
        raise SystemExit(f"failed to construct requested number of pairs: wanted {args.limit}, got {len(records) // 2}")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    if args.meta_output:
        meta = {
            "builder": "structured_code_search",
            "limit": args.limit,
            "seed": args.seed,
            "pair_ids": sorted({record["pair_id"] for record in records}),
        }
        meta_path = Path(args.meta_output)
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"wrote {len(records)} records to {output_path}")
    if args.meta_output:
        print(f"wrote metadata to {args.meta_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
