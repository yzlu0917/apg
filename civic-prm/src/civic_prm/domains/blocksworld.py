from __future__ import annotations

import random
from functools import lru_cache
from collections import deque

BLOCKS = ("A", "B", "C")


def _canonicalize(state: tuple[tuple[str, ...], ...]) -> tuple[tuple[str, ...], ...]:
    cleaned = [stack for stack in state if stack]
    return tuple(sorted(cleaned, key=lambda stack: "".join(stack)))


def _render_state(state: tuple[tuple[str, ...], ...]) -> str:
    return " ".join("[" + " ".join(stack) + "]" for stack in state)


def _moves(
    state: tuple[tuple[str, ...], ...],
    blocks: tuple[str, ...] | None = None,
) -> list[tuple[str, tuple[tuple[str, ...], ...]]]:
    results = []
    for src_index, src_stack in enumerate(state):
        block = src_stack[-1]
        base = [list(stack) for stack in state]
        base[src_index].pop()
        for dst_index, dst_stack in enumerate(state):
            if src_index == dst_index:
                continue
            candidate = [stack[:] for stack in base]
            candidate[dst_index].append(block)
            next_state = _canonicalize(tuple(tuple(stack) for stack in candidate))
            action = f"move block {block} onto block {dst_stack[-1]}"
            results.append((action, next_state))
        candidate = [stack[:] for stack in base]
        candidate.append([block])
        next_state = _canonicalize(tuple(tuple(stack) for stack in candidate))
        if next_state == state:
            continue
        action = f"move block {block} to the table"
        results.append((action, next_state))
    dedup = {}
    for action, next_state in results:
        dedup[(action, next_state)] = None
    return list(dedup.keys())


@lru_cache(maxsize=None)
def _all_states(blocks: tuple[str, ...]) -> list[tuple[tuple[str, ...], ...]]:
    start = _canonicalize(tuple((block,) for block in blocks))
    seen = {start}
    queue = deque([start])
    while queue:
        state = queue.popleft()
        for _, next_state in _moves(state, blocks):
            if next_state not in seen:
                seen.add(next_state)
                queue.append(next_state)
    return sorted(seen, key=_render_state)


def _shortest_plan(
    start: tuple[tuple[str, ...], ...],
    goal: tuple[tuple[str, ...], ...],
    blocks: tuple[str, ...],
) -> list[tuple[str, tuple[tuple[str, ...], ...]]]:
    queue = deque([(start, [])])
    seen = {start}
    while queue:
        state, path = queue.popleft()
        if state == goal:
            return path
        for action, next_state in _moves(state, blocks):
            if next_state in seen:
                continue
            seen.add(next_state)
            queue.append((next_state, path + [(action, next_state)]))
    raise ValueError("goal is unreachable")


def _sample_start_goal(
    rng: random.Random,
    blocks: tuple[str, ...],
    min_length: int,
    max_length: int,
) -> tuple[tuple[tuple[str, ...], ...], tuple[tuple[tuple[str, ...], ...], ...], list[tuple[str, tuple[tuple[str, ...], ...]]]]:
    states = _all_states(blocks)
    while True:
        start = rng.choice(states)
        goal = rng.choice(states)
        if start == goal:
            continue
        plan = _shortest_plan(start, goal, blocks)
        if min_length <= len(plan) <= max_length:
            return start, goal, plan


def _similarity_score(state: tuple[tuple[str, ...], ...], goal: tuple[tuple[str, ...], ...]) -> int:
    state_positions = {}
    goal_positions = {}
    for stack_index, stack in enumerate(state):
        for height, block in enumerate(stack):
            state_positions[block] = (stack_index, height)
    for stack_index, stack in enumerate(goal):
        for height, block in enumerate(stack):
            goal_positions[block] = (stack_index, height)
    return sum(int(state_positions[block] == goal_positions[block]) for block in goal_positions)


def _path_with_exact_length(
    start: tuple[tuple[str, ...], ...],
    blocks: tuple[str, ...],
    length: int,
    goal: tuple[tuple[str, ...], ...],
    end_in_goal: bool = False,
) -> list[tuple[str, tuple[tuple[str, ...], ...]]]:
    if length == 0:
        if end_in_goal:
            if start == goal:
                return []
            raise ValueError("start does not match goal at length zero")
        if start != goal:
            return []
        raise ValueError("goal continuation collapsed")
    queue = deque([(start, [])])
    candidates = []
    while queue:
        state, path = queue.popleft()
        if len(path) == length:
            if end_in_goal:
                if state == goal:
                    candidates.append(path)
            elif state != goal:
                candidates.append(path)
            continue
        for action, next_state in _moves(state, blocks):
            queue.append((next_state, path + [(action, next_state)]))
    if not candidates:
        raise ValueError("no exact-length continuation found")
    if end_in_goal:
        candidates.sort(key=lambda path: tuple((action, _render_state(state)) for action, state in path))
    else:
        candidates.sort(key=lambda path: _similarity_score(path[-1][1], goal), reverse=True)
    return candidates[0]


def sample_blocksworld_instance(rng: random.Random, problem_index: int, difficulty: str = "standard") -> dict:
    blind_audit_safe = difficulty in {"hard_blindfix", "hard_blindfix_v2", "hard_blindfix_v3", "hard_blindfix_v4"}
    if difficulty in {"hard", "hard_blindfix", "hard_blindfix_v2", "hard_blindfix_v3", "hard_blindfix_v4"}:
        blocks = ("A", "B", "C", "D")
        min_length, max_length = 4, 5
        problem_prefix = "blocksworld-hard"
    else:
        blocks = BLOCKS
        min_length, max_length = 2, 3
        problem_prefix = "blocksworld"
    while True:
        start, goal, plan = _sample_start_goal(rng, blocks, min_length, max_length)
        states_before = [start]
        current = start
        for _, next_state in plan[:-1]:
            current = next_state
            states_before.append(current)
        viable_loci = [
            idx
            for idx, (_, next_state) in enumerate(plan)
            if any(alt_state != next_state for _, alt_state in _moves(states_before[idx], blocks))
        ]
        if blind_audit_safe:
            filtered_loci = []
            for idx in viable_loci:
                current_state = states_before[idx]
                next_state = plan[idx][1]
                for _, alt_state in _moves(current_state, blocks):
                    if alt_state == next_state:
                        continue
                    remaining_steps = len(plan) - idx - 1
                    try:
                        _path_with_exact_length(
                            alt_state,
                            blocks,
                            remaining_steps,
                            goal,
                            end_in_goal=True,
                        )
                        filtered_loci.append(idx)
                        break
                    except ValueError:
                        continue
            viable_loci = filtered_loci
        if viable_loci:
            locus = rng.choice(viable_loci)
            break
    valid_steps = []
    invalid_steps = []

    invalid_state = start
    for step_index, (action, next_state) in enumerate(plan):
        valid_steps.append(
            {
                "statement": (
                    f"{action}, reaching state {_render_state(next_state)}."
                )
            }
        )
        if step_index < locus:
            invalid_steps.append(
                {
                    "statement": (
                        f"{action}, reaching state {_render_state(next_state)}."
                    )
                }
            )
            invalid_state = next_state
        elif step_index == locus:
            alternatives = []
            for alt_action, alt_state in _moves(invalid_state, blocks):
                if alt_state == next_state:
                    continue
                if blind_audit_safe:
                    remaining_steps = len(plan) - step_index - 1
                    try:
                        continuation = _path_with_exact_length(
                            alt_state,
                            blocks,
                            remaining_steps,
                            goal,
                            end_in_goal=True,
                        )
                    except ValueError:
                        continue
                    alternatives.append((alt_action, alt_state, continuation))
                else:
                    alternatives.append((alt_action, alt_state, None))
            alt_action, alt_state, goal_continuation = rng.choice(alternatives)
            invalid_steps.append(
                {
                    "statement": (
                        f"{alt_action}, reaching state {_render_state(alt_state)}."
                    )
                }
            )
            invalid_state = alt_state
        else:
            if blind_audit_safe:
                chosen_action, chosen_state = goal_continuation[step_index - locus - 1]
            else:
                remaining_steps = len(plan) - step_index
                continuation = _path_with_exact_length(invalid_state, blocks, remaining_steps, goal)
                chosen_action, chosen_state = continuation[0]
            invalid_steps.append(
                {
                    "statement": (
                        f"{chosen_action}, reaching state {_render_state(chosen_state)}."
                    )
                }
            )
            invalid_state = chosen_state

    distractor_state = invalid_state if invalid_state != goal else start
    correct_answer = _render_state(goal)
    distractor_answer = _render_state(distractor_state)

    verbalizers = [
        {
            "id": "bw_v1",
            "problem_text": (
                f"Starting from {_render_state(start)}, reach the goal state {_render_state(goal)}."
            ),
            "render_step": lambda step, i: f"Step {i + 1}: {step['statement']}",
            "answer_correct": f"Final answer: the plan reaches {_render_state(goal)}.",
            "answer_swapped": f"Final answer: the plan reaches {distractor_answer}.",
        },
        {
            "id": "bw_v2",
            "problem_text": (
                f"Plan block moves from start {_render_state(start)} to goal {_render_state(goal)}."
            ),
            "render_step": lambda step, i: f"Move {i + 1}: {step['statement']}",
            "answer_correct": f"So the final state is {correct_answer}.",
            "answer_swapped": f"So the final state is {distractor_answer}.",
        },
        {
            "id": "bw_v3",
            "problem_text": (
                f"Transform {_render_state(start)} into {_render_state(goal)} using legal top-block moves."
            ),
            "render_step": lambda step, i: f"Reasoning {i + 1}: {step['statement']}",
            "answer_correct": f"Hence the target state is {correct_answer}.",
            "answer_swapped": f"Hence the target state is {distractor_answer}.",
        },
    ]

    return {
        "domain": "blocksworld",
        "problem_id": f"{problem_prefix}-{problem_index:04d}",
        "audited_locus": locus,
        "valid_steps": valid_steps,
        "invalid_steps": invalid_steps,
        "verbalizers": verbalizers,
        "correct_answer": correct_answer,
        "distractor_answer": distractor_answer,
        "metadata": {
            "difficulty": difficulty,
            "start_state": _render_state(start),
            "goal_state": _render_state(goal),
            "plan_length": len(plan),
            "num_blocks": len(blocks),
        },
    }
