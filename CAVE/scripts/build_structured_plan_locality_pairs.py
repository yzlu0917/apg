#!/usr/bin/env python3

import argparse
import itertools
import json
from pathlib import Path


TASKS = ["A", "B", "C", "D"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="Output JSONL path.")
    parser.add_argument("--meta-output", help="Optional metadata JSON path.")
    parser.add_argument("--limit", type=int, default=3, help="Number of pairs to emit.")
    parser.add_argument("--seed", type=int, default=2101, help="Seed suffix for pair ids.")
    return parser.parse_args()


def order_to_text(order: list[str]) -> str:
    return " -> ".join(order)


def validate_order(order: list[str], tasks: set[str], edges: list[tuple[str, str]]) -> bool:
    if set(order) != tasks or len(order) != len(tasks):
        return False
    position = {task: index for index, task in enumerate(order)}
    return all(position[left] < position[right] for left, right in edges)


def enumerate_adjacent_swap_neighbors(order: list[str]) -> list[list[str]]:
    neighbors: list[list[str]] = []
    for index in range(len(order) - 1):
        swapped = list(order)
        swapped[index], swapped[index + 1] = swapped[index + 1], swapped[index]
        neighbors.append(swapped)
    return neighbors


def count_topological_orders(tasks: set[str], edges: list[tuple[str, str]], limit: int = 10) -> int:
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


def describe_edges(edges: list[tuple[str, str]]) -> str:
    return "; ".join(f"{left} before {right}" for left, right in edges)


def make_checker_reference(edges: list[tuple[str, str]]) -> str:
    payload = {
        "schema": "plan_local_repair_v1",
        "tasks": TASKS,
        "edges": [[left, right] for left, right in edges],
        "locality": {"kind": "adjacent_swap", "max_swaps": 1},
    }
    return json.dumps(payload, ensure_ascii=False)


def find_swap_text(revise: list[str], keep: list[str]) -> str:
    for index in range(len(revise) - 1):
        swapped = list(revise)
        swapped[index], swapped[index + 1] = swapped[index + 1], swapped[index]
        if swapped == keep:
            return f"{revise[index]} -> {revise[index + 1]}"
    raise ValueError("keep is not an adjacent swap from revise")


def build_pair(pair_id: str, keep: list[str], revise: list[str], edges: list[tuple[str, str]]) -> list[dict]:
    wrong_neighbors = [
        neighbor
        for neighbor in enumerate_adjacent_swap_neighbors(revise)
        if neighbor != keep and not validate_order(neighbor, set(TASKS), edges)
    ]
    wrong_neighbor = wrong_neighbors[0] if wrong_neighbors else enumerate_adjacent_swap_neighbors(revise)[0]
    question = (
        f"Given tasks {', '.join(TASKS)} with dependencies {describe_edges(edges)}, "
        "provide a valid total order. Output as a compact order string like "
        f"'{order_to_text(keep)}'."
    )
    checker_reference = make_checker_reference(edges)
    keep_text = order_to_text(keep)
    revise_text = order_to_text(revise)
    fail_span = find_swap_text(revise, keep)
    wrong_text = order_to_text(wrong_neighbor)

    common = {
        "pair_id": pair_id,
        "domain": "plan",
        "question": question,
        "expected_final_answer": keep_text,
        "checker": {"type": "constraint_check", "reference": checker_reference},
        "candidate_source": "search_constructed",
        "generation_family": "contrastive_locality",
        "review_status": "pending",
    }

    return [
        {
            "id": f"{pair_id}_keep",
            **common,
            "initial_trace": keep_text,
            "gold_fail_span": {"text": "", "kind": "none"},
            "gold_action": "keep",
            "gold_repair_suffix": "",
            "utility_delta": {"keep": 1.0, "revise": 0.0, "abstain": 0.0},
            "notes": "Structured keep order satisfies all precedence edges and is the unique valid adjacent-swap repair target.",
        },
        {
            "id": f"{pair_id}_revise",
            **common,
            "initial_trace": revise_text,
            "gold_fail_span": {"text": fail_span, "kind": "adjacent_pair"},
            "gold_action": "revise",
            "gold_repair_suffix": keep_text,
            "utility_delta": {"keep": 0.0, "revise": 1.0, "abstain": 0.0},
            "notes": (
                f"Revise order violates the structured checker. "
                f"A nearby wrong adjacent-swap repair {wrong_text} still looks plausible but fails the checker. "
                f"The unique valid adjacent-swap repair is {keep_text}."
            ),
        },
    ]


def build_candidate(keep: list[str], revise: list[str], edges: list[tuple[str, str]]) -> dict:
    return {
        "keep": keep,
        "revise": revise,
        "edges": edges,
        "keep_text": order_to_text(keep),
        "revise_text": order_to_text(revise),
        "fail_span": find_swap_text(revise, keep),
        "edge_signature": tuple(edges),
    }


def select_diverse_candidates(candidates: list[dict], limit: int) -> list[dict]:
    selected: list[dict] = []
    used_keep: set[str] = set()
    used_fail_span: set[str] = set()
    used_edge_sig: set[tuple[tuple[str, str], ...]] = set()

    remaining = list(candidates)
    while remaining and len(selected) < limit:
        best_index = 0
        best_score = -1
        for index, candidate in enumerate(remaining):
            score = 0
            if candidate["keep_text"] not in used_keep:
                score += 3
            if candidate["fail_span"] not in used_fail_span:
                score += 2
            if candidate["edge_signature"] not in used_edge_sig:
                score += 2
            if candidate["revise_text"] not in {item["revise_text"] for item in selected}:
                score += 1
            if score > best_score:
                best_score = score
                best_index = index
        choice = remaining.pop(best_index)
        selected.append(choice)
        used_keep.add(choice["keep_text"])
        used_fail_span.add(choice["fail_span"])
        used_edge_sig.add(choice["edge_signature"])
    return selected


def search_pairs(limit: int, seed: int) -> list[dict]:
    candidates: list[dict] = []
    seen_signatures: set[tuple[tuple[str, ...], tuple[tuple[str, str], ...], tuple[str, ...]]] = set()

    for keep in itertools.permutations(TASKS):
        keep_list = list(keep)
        allowed_edges = [(keep_list[i], keep_list[j]) for i in range(len(keep_list)) for j in range(i + 1, len(keep_list))]
        for edge_count in range(2, 5):
            for edge_subset in itertools.combinations(allowed_edges, edge_count):
                edges = list(edge_subset)
                topo_count = count_topological_orders(set(TASKS), edges, limit=10)
                if topo_count < 2:
                    continue
                for revise in itertools.permutations(TASKS):
                    revise_list = list(revise)
                    if revise_list == keep_list:
                        continue
                    if validate_order(revise_list, set(TASKS), edges):
                        continue
                    neighbors = enumerate_adjacent_swap_neighbors(revise_list)
                    valid_neighbors = [neighbor for neighbor in neighbors if validate_order(neighbor, set(TASKS), edges)]
                    if len(valid_neighbors) != 1:
                        continue
                    if valid_neighbors[0] != keep_list:
                        continue
                    signature = (tuple(keep_list), tuple(edges), tuple(revise_list))
                    if signature in seen_signatures:
                        continue
                    seen_signatures.add(signature)
                    candidates.append(build_candidate(keep_list, revise_list, edges))

    selected = select_diverse_candidates(candidates, limit)
    records: list[dict] = []
    for index, candidate in enumerate(selected):
        pair_id = f"plan_structured_search_{seed + index}"
        records.extend(build_pair(pair_id, candidate["keep"], candidate["revise"], candidate["edges"]))
    return records


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
            "builder": "structured_plan_search",
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
