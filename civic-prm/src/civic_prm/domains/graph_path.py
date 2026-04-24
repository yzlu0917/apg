from __future__ import annotations

import random


def _path_cost_label(path: tuple[str, str, str], cost: int) -> str:
    return f"{path[0]} -> {path[1]} -> {path[2]} with total cost {cost}"


def _standard_instance(rng: random.Random, problem_index: int, blind_audit_safe: bool = False) -> dict:
    mid_nodes = ["A", "B", "C"]
    weights = {}
    totals = {}
    for node in mid_nodes:
        left = rng.randint(1, 8)
        right = rng.randint(1, 8)
        weights[node] = (left, right)
        totals[node] = left + right
    best_mid = min(mid_nodes, key=totals.get)
    sorted_mids = sorted(mid_nodes, key=totals.get)
    second_mid = sorted_mids[1]
    locus = rng.choice([0, 1, 2] if blind_audit_safe else [0, 1, 2, 3])

    valid_steps = []
    invalid_steps = []
    wrong_mid = second_mid
    wrong_totals = totals.copy()

    if blind_audit_safe:
        edited_mid = rng.choice([node for node in mid_nodes if node != best_mid])
        locus = mid_nodes.index(edited_mid)
        while True:
            proposed_total = max(1, totals[edited_mid] + rng.choice([-2, -1, 1, 2]))
            if proposed_total != totals[edited_mid] and proposed_total > totals[best_mid]:
                wrong_totals[edited_mid] = proposed_total
                break
        wrong_mid = best_mid
    elif locus in [0, 1, 2]:
        edited_mid = mid_nodes[locus]
        wrong_totals[edited_mid] = max(1, totals[edited_mid] - rng.choice([2, 3]))
        if wrong_totals[edited_mid] < wrong_totals[best_mid]:
            wrong_mid = edited_mid
    else:
        wrong_mid = second_mid

    for idx, node in enumerate(mid_nodes):
        left, right = weights[node]
        valid_steps.append(
            {
                "statement": (
                    f"The route S -> {node} -> T costs {left} + {right} = {totals[node]}."
                )
            }
        )
        shown_total = wrong_totals[node] if idx == locus and locus < 3 else totals[node]
        invalid_steps.append(
            {
                "statement": (
                    f"The route S -> {node} -> T costs {left} + {right} = {shown_total}."
                )
            }
        )

    valid_steps.append(
        {
            "statement": (
                f"The smallest total is {totals[best_mid]}, so choose S -> {best_mid} -> T."
            )
        }
    )
    invalid_choice_total = wrong_totals[wrong_mid]
    invalid_steps.append(
        {
            "statement": (
                f"The smallest total is {invalid_choice_total}, so choose S -> {wrong_mid} -> T."
            )
        }
    )

    correct_answer = _path_cost_label(("S", best_mid, "T"), totals[best_mid])
    distractor_answer = _path_cost_label(("S", wrong_mid, "T"), totals[wrong_mid])

    verbalizers = [
        {
            "id": "graph_v1",
            "problem_text": (
                "In the weighted graph with edges "
                + ", ".join(
                    f"S-{node}:{weights[node][0]} and {node}-T:{weights[node][1]}"
                    for node in mid_nodes
                )
                + ", find the shortest path from S to T."
            ),
            "render_step": lambda step, i: f"Step {i + 1}: {step['statement']}",
            "answer_correct": f"Final answer: {correct_answer}.",
            "answer_swapped": f"Final answer: {distractor_answer}.",
        },
        {
            "id": "graph_v2",
            "problem_text": (
                "Check the candidate routes from S to T in this graph: "
                + "; ".join(
                    f"S->{node} has weight {weights[node][0]}, {node}->T has weight {weights[node][1]}"
                    for node in mid_nodes
                )
                + "."
            ),
            "render_step": lambda step, i: f"Candidate {i + 1}: {step['statement']}",
            "answer_correct": f"So the best route is {correct_answer}.",
            "answer_swapped": f"So the best route is {distractor_answer}.",
        },
        {
            "id": "graph_v3",
            "problem_text": (
                "Compute the cheapest way to go from S to T using the two-edge options via "
                + ", ".join(mid_nodes)
                + "."
            ),
            "render_step": lambda step, i: f"Reasoning {i + 1}: {step['statement']}",
            "answer_correct": f"Hence the shortest path is {correct_answer}.",
            "answer_swapped": f"Hence the shortest path is {distractor_answer}.",
        },
    ]

    return {
        "domain": "graph_path",
        "problem_id": f"graph-{problem_index:04d}",
        "audited_locus": locus,
        "valid_steps": valid_steps,
        "invalid_steps": invalid_steps,
        "verbalizers": verbalizers,
        "correct_answer": correct_answer,
        "distractor_answer": distractor_answer,
        "metadata": {
            "weights": weights,
            "totals": totals,
            "best_mid": best_mid,
            "wrong_mid": wrong_mid,
            "difficulty": "standard_blindfix" if blind_audit_safe else "standard",
        },
    }


def _render_three_edge_path(path: tuple[str, str, str, str], cost: int) -> str:
    return f"{path[0]} -> {path[1]} -> {path[2]} -> {path[3]} with total cost {cost}"


def _hard_instance(
    rng: random.Random,
    problem_index: int,
    blind_audit_safe: bool = False,
    blind_audit_v2: bool = False,
    blind_audit_v3: bool = False,
) -> dict:
    route_defs = [
        ("A", "B"),
        ("C", "D"),
        ("E", "F"),
        ("G", "H"),
    ]
    while True:
        weights = {}
        totals = {}
        for left_node, right_node in route_defs:
            first = rng.randint(1, 7)
            second = rng.randint(1, 7)
            third = rng.randint(1, 7)
            weights[(left_node, right_node)] = (first, second, third)
            totals[(left_node, right_node)] = first + second + third
        sorted_routes = sorted(route_defs, key=lambda route: totals[route])
        best_route = sorted_routes[0]
        second_route = sorted_routes[1]
        if totals[second_route] - totals[best_route] in {1, 2, 3}:
            break

    locus = rng.choice([0, 1, 4] if not blind_audit_safe else [1, 2, 3])
    critical_route = best_route if locus == 0 else second_route
    routes_in_order = [best_route, second_route, sorted_routes[2], sorted_routes[3]]
    wrong_totals = totals.copy()

    if blind_audit_safe:
        edited_route = routes_in_order[locus]
        while True:
            proposed_total = max(1, totals[edited_route] + rng.choice([-2, -1, 1, 2]))
            if proposed_total != totals[edited_route] and proposed_total > totals[best_route]:
                wrong_totals[edited_route] = proposed_total
                break
        wrong_route = best_route
        critical_route = edited_route
    elif locus in [0, 1]:
        gap = totals[second_route] - totals[best_route]
        if critical_route == best_route:
            wrong_totals[best_route] = totals[best_route] + gap + rng.choice([1, 2])
        else:
            wrong_totals[second_route] = max(1, totals[second_route] - gap - rng.choice([1, 2]))
        wrong_route = min(routes_in_order, key=lambda route: wrong_totals[route])
    else:
        wrong_route = second_route

    valid_steps = []
    invalid_steps = []
    for step_index, route in enumerate(routes_in_order):
        left_node, right_node = route
        first, second, third = weights[route]
        valid_total = totals[route]
        show_wrong_total = route == critical_route and (blind_audit_safe or locus in [0, 1])
        shown_total = wrong_totals[route] if show_wrong_total else valid_total
        if blind_audit_v3:
            valid_statement = (
                f"For route S -> {left_node} -> {right_node} -> T, record a total cost of {valid_total}."
            )
            invalid_statement = (
                f"For route S -> {left_node} -> {right_node} -> T, record a total cost of {shown_total}."
            )
        else:
            valid_statement = (
                f"The route S -> {left_node} -> {right_node} -> T costs "
                f"{first} + {second} + {third} = {valid_total}."
            )
            invalid_statement = (
                f"The route S -> {left_node} -> {right_node} -> T costs "
                f"{first} + {second} + {third} = {shown_total}."
            )
        valid_steps.append(
            {
                "statement": valid_statement
            }
        )
        invalid_steps.append(
            {
                "statement": invalid_statement
            }
        )

    comparison_text = ", ".join(
        f"{route[0]}-{route[1]}:{totals[route]}" for route in routes_in_order
    )
    wrong_comparison_text = ", ".join(
        f"{route[0]}-{route[1]}:{wrong_totals[route] if route in wrong_totals else totals[route]}"
        for route in routes_in_order
    )
    valid_steps.append(
        {
            "statement": (
                f"Comparing totals {comparison_text}, the cheapest route is S -> {best_route[0]} -> {best_route[1]} -> T."
            )
        }
    )
    invalid_steps.append(
        {
            "statement": (
                f"Comparing totals {wrong_comparison_text}, the cheapest route is S -> {wrong_route[0]} -> {wrong_route[1]} -> T."
            )
        }
    )

    correct_answer = _render_three_edge_path(("S", best_route[0], best_route[1], "T"), totals[best_route])
    distractor_answer = _render_three_edge_path(("S", wrong_route[0], wrong_route[1], "T"), totals[wrong_route])
    locus_index = routes_in_order.index(critical_route) if locus in [0, 1] else len(routes_in_order)

    verbalizers = [
        {
            "id": "graph_v1",
            "problem_text": (
                "In the weighted graph with candidate routes "
                + ", ".join(
                    f"S-{left}:{weights[(left, right)][0]}, {left}-{right}:{weights[(left, right)][1]}, {right}-T:{weights[(left, right)][2]}"
                    for left, right in routes_in_order
                )
                + ", find the shortest path from S to T."
            ),
            "render_step": lambda step, i: f"Step {i + 1}: {step['statement']}",
            "answer_correct": f"Final answer: {correct_answer}.",
            "answer_swapped": f"Final answer: {distractor_answer}.",
        },
        {
            "id": "graph_v2",
            "problem_text": (
                "Check the candidate three-edge routes from S to T: "
                + "; ".join(
                    f"S->{left} has weight {weights[(left, right)][0]}, {left}->{right} has weight {weights[(left, right)][1]}, {right}->T has weight {weights[(left, right)][2]}"
                    for left, right in routes_in_order
                )
                + "."
            ),
            "render_step": lambda step, i: f"Candidate {i + 1}: {step['statement']}",
            "answer_correct": f"So the best route is {correct_answer}.",
            "answer_swapped": f"So the best route is {distractor_answer}.",
        },
        {
            "id": "graph_v3",
            "problem_text": (
                "Compute the cheapest way to go from S to T among the four listed three-hop routes."
            ),
            "render_step": lambda step, i: f"Reasoning {i + 1}: {step['statement']}",
            "answer_correct": f"Hence the shortest path is {correct_answer}.",
            "answer_swapped": f"Hence the shortest path is {distractor_answer}.",
        },
    ]

    return {
        "domain": "graph_path",
        "problem_id": f"graph-hard-{problem_index:04d}",
        "audited_locus": locus_index,
        "valid_steps": valid_steps,
        "invalid_steps": invalid_steps,
        "verbalizers": verbalizers,
        "correct_answer": correct_answer,
        "distractor_answer": distractor_answer,
        "metadata": {
            "difficulty": (
                "hard_blindfix_v3"
                if blind_audit_v3
                else ("hard_blindfix_v2" if blind_audit_v2 else ("hard_blindfix" if blind_audit_safe else "hard"))
            ),
            "weights": {f"{left}-{right}": weights[(left, right)] for left, right in routes_in_order},
            "totals": {f"{left}-{right}": totals[(left, right)] for left, right in routes_in_order},
            "best_route": f"{best_route[0]}-{best_route[1]}",
            "wrong_route": f"{wrong_route[0]}-{wrong_route[1]}",
        },
    }


def sample_graph_instance(rng: random.Random, problem_index: int, difficulty: str = "standard") -> dict:
    if difficulty == "hard_blindfix_v4":
        instance = _hard_instance(rng, problem_index, blind_audit_safe=True, blind_audit_v2=True, blind_audit_v3=True)
        instance["metadata"]["difficulty"] = "hard_blindfix_v4"
        return instance
    if difficulty == "hard_blindfix_v3":
        return _hard_instance(rng, problem_index, blind_audit_safe=True, blind_audit_v2=True, blind_audit_v3=True)
    if difficulty == "hard_blindfix_v2":
        return _hard_instance(rng, problem_index, blind_audit_safe=True, blind_audit_v2=True)
    if difficulty == "hard_blindfix":
        return _hard_instance(rng, problem_index, blind_audit_safe=True)
    if difficulty == "hard":
        return _hard_instance(rng, problem_index)
    return _standard_instance(rng, problem_index)
