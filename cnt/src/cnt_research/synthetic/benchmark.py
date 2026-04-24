from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import json
import math
import random
from typing import Dict, Iterable, List, Mapping, Sequence

import numpy as np


TEMPLATE_FAMILIES: Mapping[str, Mapping[str, Sequence[str]]] = {
    "plain": {
        "move": (
            "Walk from {src} to {dst}.",
            "Go from {src} to {dst}.",
        ),
        "pickup": (
            "Pick up the {item} in {room}.",
            "Collect the {item} located in {room}.",
        ),
        "unlock": (
            "Use the {item} to unlock the {gate} leading to {dst}.",
            "Unlock the {gate} toward {dst} with the {item}.",
        ),
        "inspect": (
            "Inspect the marker in {room} for clues.",
            "Check the marker in {room} for any clue.",
        ),
    },
    "tight": {
        "move": (
            "Head from {src} into {dst}.",
            "Step out of {src} and enter {dst}.",
        ),
        "pickup": (
            "Grab the {item} from {room}.",
            "Take the {item} waiting in {room}.",
        ),
        "unlock": (
            "Open the {gate} toward {dst} using the {item}.",
            "With the {item}, open the {gate} into {dst}.",
        ),
        "inspect": (
            "Study the marker in {room}.",
            "Read the marker posted in {room}.",
        ),
    },
    "verbose": {
        "move": (
            "After orienting at {src}, move onward to {dst}.",
            "Leave {src} behind and make your way to {dst}.",
        ),
        "pickup": (
            "Secure the {item} resting inside {room}.",
            "Lift the {item} that has been left in {room}.",
        ),
        "unlock": (
            "Apply the {item} and swing open the {gate} toward {dst}.",
            "Use the {item} so the {gate} into {dst} opens.",
        ),
        "inspect": (
            "Pause to inspect the marker displayed in {room}.",
            "Spend a moment examining the marker inside {room}.",
        ),
    },
}

CORE_ROOMS = (
    "Atrium",
    "Junction",
    "Ruby Vault",
    "Moss Hall",
    "Archive",
    "Sanctum",
)


@dataclass(frozen=True)
class Action:
    kind: str
    src: str
    dst: str | None = None
    item: str | None = None
    gate: str | None = None
    room: str | None = None

    def signature(self) -> str:
        return json.dumps(
            {
                "kind": self.kind,
                "src": self.src,
                "dst": self.dst,
                "item": self.item,
                "gate": self.gate,
                "room": self.room,
            },
            sort_keys=True,
        )


@dataclass(frozen=True)
class State:
    room: str
    inventory: frozenset[str]
    opened_gates: frozenset[str]
    collected_items: frozenset[str]
    inspected_rooms: frozenset[str]


@dataclass(frozen=True)
class Step:
    action: Action
    text: str
    role: str
    template_family: str
    template_variant: int
    note: str


@dataclass(frozen=True)
class Candidate:
    index: int
    step: Step


@dataclass(frozen=True)
class PrefixVariant:
    kind: str
    family: str
    prefix_text: str
    state: State


@dataclass(frozen=True)
class TaskInstance:
    instance_id: str
    primary_path: str
    total_budget: int
    trajectory: Sequence[Step]
    candidate_indices: Sequence[int]


class SyntheticPlanningWorld:
    """Small deterministic planning world with filler, decoys, and a redundant path."""

    def __init__(self, primary_path: str, slack_budget: int = 2) -> None:
        self.start = "Atrium"
        self.fork = "Junction"
        self.goal = "Sanctum"
        self.primary_path = primary_path
        self.alt_path = "green" if primary_path == "red" else "red"
        self.total_budget_slack = slack_budget
        self.key_rooms = {
            "red": "Ruby Vault",
            "green": "Moss Hall",
        }
        self.key_items = {
            "red": "ruby key",
            "green": "moss key",
        }
        self.gates = {
            "red": "ruby gate",
            "green": "moss gate",
        }
        self.decoy_room = "Archive"
        self.decoy_item = "bronze token"
        self.edges = {
            "Atrium": ("Junction",),
            "Junction": ("Atrium", "Ruby Vault", "Moss Hall", "Archive", "Sanctum"),
            "Ruby Vault": ("Junction",),
            "Moss Hall": ("Junction",),
            "Archive": ("Junction",),
            "Sanctum": ("Junction",),
        }
        self.items = {
            self.key_rooms["red"]: self.key_items["red"],
            self.key_rooms["green"]: self.key_items["green"],
            self.decoy_room: self.decoy_item,
        }
        self.room_markers = {
            "Junction": "junction marker",
            self.key_rooms["red"]: "ruby marker",
            self.key_rooms["green"]: "moss marker",
            self.decoy_room: "archive marker",
        }
        self._distance_cache: Dict[tuple[State, int], int | None] = {}
        self._prob_cache: Dict[tuple[str, State, int], float] = {}

    def initial_state(self) -> State:
        return State(
            room=self.start,
            inventory=frozenset(),
            opened_gates=frozenset(),
            collected_items=frozenset(),
            inspected_rooms=frozenset(),
        )

    def is_goal(self, state: State) -> bool:
        return state.room == self.goal

    def gate_open(self, state: State, path: str) -> bool:
        return self.gates[path] in state.opened_gates

    def is_legal(self, state: State, action: Action) -> bool:
        signatures = {candidate.signature() for candidate in self.legal_actions(state)}
        return action.signature() in signatures

    def legal_actions(self, state: State) -> List[Action]:
        actions: List[Action] = []
        for dst in self.edges[state.room]:
            if state.room == "Junction" and dst == "Sanctum":
                for gate_path in ("red", "green"):
                    gate_name = self.gates[gate_path]
                    if gate_name in state.opened_gates:
                        actions.append(
                            Action(
                                kind="move",
                                src=state.room,
                                dst=dst,
                                gate=gate_name,
                            )
                        )
                continue
            if state.room == "Sanctum" and dst == "Junction":
                actions.append(Action(kind="move", src=state.room, dst=dst))
                continue
            actions.append(Action(kind="move", src=state.room, dst=dst))
        item = self.items.get(state.room)
        if item is not None and item not in state.collected_items:
            actions.append(
                Action(
                    kind="pickup",
                    src=state.room,
                    room=state.room,
                    item=item,
                )
            )
        if state.room == "Junction":
            for path in ("red", "green"):
                gate = self.gates[path]
                key = self.key_items[path]
                if gate not in state.opened_gates and key in state.inventory:
                    actions.append(
                        Action(
                            kind="unlock",
                            src="Junction",
                            dst="Sanctum",
                            item=key,
                            gate=gate,
                        )
                    )
        if state.room in self.room_markers:
            actions.append(Action(kind="inspect", src=state.room, room=state.room))
        return actions

    def apply(self, state: State, action: Action) -> State:
        legal_signatures = {legal_action.signature() for legal_action in self.legal_actions(state)}
        if action.signature() not in legal_signatures:
            return state
        if action.kind == "move":
            assert action.dst is not None
            return State(
                room=action.dst,
                inventory=state.inventory,
                opened_gates=state.opened_gates,
                collected_items=state.collected_items,
                inspected_rooms=state.inspected_rooms,
            )
        if action.kind == "pickup":
            assert action.item is not None
            return State(
                room=state.room,
                inventory=state.inventory | {action.item},
                opened_gates=state.opened_gates,
                collected_items=state.collected_items | {action.item},
                inspected_rooms=state.inspected_rooms,
            )
        if action.kind == "unlock":
            assert action.gate is not None
            return State(
                room=state.room,
                inventory=state.inventory,
                opened_gates=state.opened_gates | {action.gate},
                collected_items=state.collected_items,
                inspected_rooms=state.inspected_rooms,
            )
        if action.kind == "inspect":
            assert action.room is not None
            return State(
                room=state.room,
                inventory=state.inventory,
                opened_gates=state.opened_gates,
                collected_items=state.collected_items,
                inspected_rooms=state.inspected_rooms | {action.room},
            )
        raise ValueError(f"Unsupported action kind: {action.kind}")

    def rollout_distance(self, state: State, budget: int) -> int | None:
        key = (state, budget)
        if key in self._distance_cache:
            return self._distance_cache[key]
        if self.is_goal(state):
            self._distance_cache[key] = 0
            return 0
        if budget <= 0:
            self._distance_cache[key] = None
            return None
        best: int | None = None
        for action in self.legal_actions(state):
            next_state = self.apply(state, action)
            remaining = self.rollout_distance(next_state, budget - 1)
            if remaining is None:
                continue
            candidate = 1 + remaining
            if best is None or candidate < best:
                best = candidate
        self._distance_cache[key] = best
        return best

    def reachable(self, state: State, budget: int) -> float:
        return float(self.rollout_distance(state, budget) is not None)

    def action_distribution(self, state: State, policy_name: str) -> Dict[Action, float]:
        legal_actions = self.legal_actions(state)
        if not legal_actions:
            return {}
        scores = []
        current_distance = self.rollout_distance(state, 12)
        for action in legal_actions:
            next_state = self.apply(state, action)
            next_distance = self.rollout_distance(next_state, 12)
            distance_gain = 0.0
            if current_distance is not None and next_distance is not None:
                distance_gain = float(current_distance - next_distance)
            elif next_distance is None:
                distance_gain = -2.0
            else:
                distance_gain = 0.5
            score = 0.0
            if action.kind == "move":
                score += 0.8 * distance_gain
            elif action.kind == "pickup":
                score += 0.5 + 0.9 * distance_gain
                if action.item == self.decoy_item:
                    score -= 1.5
            elif action.kind == "unlock":
                score += 1.2 + 1.1 * distance_gain
            elif action.kind == "inspect":
                score -= 0.8
            if policy_name == "planner":
                score += {
                    "move": 0.4,
                    "pickup": 0.6,
                    "unlock": 0.7,
                    "inspect": -1.1,
                }[action.kind]
            elif policy_name == "repair":
                score += {
                    "move": 0.3,
                    "pickup": 0.3,
                    "unlock": 0.4,
                    "inspect": -0.5,
                }[action.kind]
                if action.item == self.key_items[self.alt_path]:
                    score += 0.7
                if action.dst == self.key_rooms[self.alt_path]:
                    score += 0.5
            elif policy_name == "noisy":
                score += {
                    "move": 0.1,
                    "pickup": 0.2,
                    "unlock": 0.2,
                    "inspect": -0.1,
                }[action.kind]
                if action.item == self.decoy_item:
                    score += 0.3
            else:
                raise ValueError(f"Unknown policy: {policy_name}")
            scores.append(score)
        max_score = max(scores)
        weights = np.exp(np.array(scores, dtype=float) - max_score)
        weights = weights / weights.sum()
        return {action: float(weight) for action, weight in zip(legal_actions, weights)}

    def solve_probability(self, state: State, budget: int, policy_name: str) -> float:
        key = (policy_name, state, budget)
        if key in self._prob_cache:
            return self._prob_cache[key]
        if self.is_goal(state):
            self._prob_cache[key] = 1.0
            return 1.0
        if budget <= 0:
            self._prob_cache[key] = 0.0
            return 0.0
        dist = self.action_distribution(state, policy_name)
        prob = 0.0
        for action, weight in dist.items():
            next_state = self.apply(state, action)
            prob += weight * self.solve_probability(next_state, budget - 1, policy_name)
        self._prob_cache[key] = prob
        return prob

    def action_entropy(self, state: State, policy_name: str) -> float:
        dist = self.action_distribution(state, policy_name)
        if not dist:
            return 0.0
        entropy = 0.0
        for weight in dist.values():
            entropy -= weight * math.log(max(weight, 1e-12))
        return entropy

    def render_action(self, action: Action, family: str, variant_index: int = 0) -> str:
        templates = TEMPLATE_FAMILIES[family][action.kind]
        template = templates[variant_index % len(templates)]
        values = {
            "src": action.src,
            "dst": action.dst,
            "item": action.item,
            "gate": action.gate,
            "room": action.room or action.src,
        }
        return template.format(**values)

    def render_prefix(self, steps: Sequence[Step]) -> str:
        lines = []
        for idx, step in enumerate(steps, start=1):
            lines.append(f"{idx}. {step.text}")
        return "\n".join(lines)

    def make_step(self, action: Action, role: str, note: str, rng: random.Random) -> Step:
        family = rng.choice(list(TEMPLATE_FAMILIES))
        variant_count = len(TEMPLATE_FAMILIES[family][action.kind])
        variant_index = rng.randrange(variant_count)
        return Step(
            action=action,
            text=self.render_action(action, family, variant_index),
            role=role,
            template_family=family,
            template_variant=variant_index,
            note=note,
        )

    def candidate_swap_actions(self, state: State, original_action: Action) -> Dict[str, Action]:
        legal = self.legal_actions(state)
        variants: Dict[str, Action] = {}
        for action in legal:
            if action.signature() == original_action.signature():
                continue
            if action.kind == original_action.kind:
                variants["swap_local"] = action
                break
        for action in legal:
            if action.signature() == original_action.signature():
                continue
            if action.kind in {"inspect", "pickup"}:
                variants["swap_decoy"] = action
                break
        if "swap_local" not in variants:
            for action in legal:
                if action.signature() != original_action.signature():
                    variants["swap_local"] = action
                    break
        if "swap_decoy" not in variants:
            for action in legal:
                if action.signature() != original_action.signature():
                    variants["swap_decoy"] = action
                    break
        fallback = Action(kind="inspect", src=state.room, room=state.room)
        variants.setdefault("swap_local", fallback)
        variants.setdefault("swap_decoy", fallback)
        return variants

    def generate_trajectory(self, rng: random.Random) -> TaskInstance:
        primary_room = self.key_rooms[self.primary_path]
        primary_key = self.key_items[self.primary_path]
        primary_gate = self.gates[self.primary_path]
        steps = [
            self.make_step(Action(kind="move", src="Atrium", dst="Junction"), "core", "enter branch point", rng),
            self.make_step(Action(kind="inspect", src="Junction", room="Junction"), "filler", "junction clue", rng),
            self.make_step(Action(kind="move", src="Junction", dst=primary_room), "core", "commit to primary branch", rng),
            self.make_step(Action(kind="move", src=primary_room, dst="Junction"), "core", "return from branch", rng),
            self.make_step(Action(kind="move", src="Junction", dst=self.decoy_room), "decoy", "visit decoy branch", rng),
            self.make_step(
                Action(kind="pickup", src=self.decoy_room, room=self.decoy_room, item=self.decoy_item),
                "decoy",
                "pick misleading artifact",
                rng,
            ),
            self.make_step(Action(kind="move", src=self.decoy_room, dst="Junction"), "decoy", "return from decoy branch", rng),
            self.make_step(Action(kind="move", src="Junction", dst=primary_room), "core", "re-enter primary branch", rng),
            self.make_step(
                Action(kind="pickup", src=primary_room, room=primary_room, item=primary_key),
                "core",
                "collect required key",
                rng,
            ),
            self.make_step(Action(kind="inspect", src=primary_room, room=primary_room), "filler", "room filler", rng),
            self.make_step(Action(kind="move", src=primary_room, dst="Junction"), "core", "bring key back", rng),
            self.make_step(
                Action(kind="unlock", src="Junction", dst="Sanctum", item=primary_key, gate=primary_gate),
                "core",
                "open primary gate",
                rng,
            ),
            self.make_step(Action(kind="move", src="Junction", dst="Sanctum", gate=primary_gate), "core", "finish", rng),
        ]
        candidate_indices = [1, 5, 8, 10, 11]
        return TaskInstance(
            instance_id=f"task-{rng.randrange(10_000_000):07d}",
            primary_path=self.primary_path,
            total_budget=13,
            trajectory=steps,
            candidate_indices=candidate_indices,
        )


def prefix_state(world: SyntheticPlanningWorld, trajectory: Sequence[Step], stop: int) -> State:
    state = world.initial_state()
    for step in trajectory[:stop]:
        if not world.is_legal(state, step.action):
            raise ValueError(f"Illegal action in prefix: {step.action}")
        state = world.apply(state, step.action)
    return state


def build_prefix_variants(
    world: SyntheticPlanningWorld,
    trajectory: Sequence[Step],
    candidate_index: int,
) -> Dict[str, PrefixVariant]:
    prefix = list(trajectory[: candidate_index + 1])
    original_state = prefix_state(world, trajectory, candidate_index + 1)
    variants: Dict[str, PrefixVariant] = {
        "original": PrefixVariant(
            kind="original",
            family=prefix[-1].template_family,
            prefix_text=world.render_prefix(prefix),
            state=original_state,
        )
    }
    base_prefix = list(trajectory[:candidate_index])
    base_state = prefix_state(world, trajectory, candidate_index)
    variants["drop"] = PrefixVariant(
        kind="drop",
        family="drop",
        prefix_text=world.render_prefix(base_prefix),
        state=base_state,
    )
    swap_actions = world.candidate_swap_actions(base_state, trajectory[candidate_index].action)
    original_family = trajectory[candidate_index].template_family
    for family, action in swap_actions.items():
        text_family = original_family
        swapped = Step(
            action=action,
            text=world.render_action(action, text_family, 1),
            role="edited",
            template_family=text_family,
            template_variant=1,
            note=family,
        )
        swapped_prefix = base_prefix + [swapped]
        variants[family] = PrefixVariant(
            kind="swap",
            family=family,
            prefix_text=world.render_prefix(swapped_prefix),
            state=prefix_state(world, swapped_prefix, len(swapped_prefix)),
        )
    original_action = trajectory[candidate_index].action
    original_variant = trajectory[candidate_index].template_variant
    para_family = original_family
    variant_count = len(TEMPLATE_FAMILIES[para_family][original_action.kind])
    para_variant = (original_variant + 1) % variant_count
    paraphrased = Step(
        action=original_action,
        text=world.render_action(original_action, para_family, para_variant),
        role=trajectory[candidate_index].role,
        template_family=para_family,
        template_variant=para_variant,
        note="paraphrase",
    )
    variants["paraphrase"] = PrefixVariant(
        kind="paraphrase",
        family=para_family,
        prefix_text=world.render_prefix(base_prefix + [paraphrased]),
        state=original_state,
    )
    return variants


def observational_score(step: Step) -> float:
    base = 0.0
    token_count = len(step.text.split())
    base += 0.08 * token_count
    if step.action.kind == "unlock":
        base += 1.3
    elif step.action.kind == "pickup":
        base += 1.0
    elif step.action.kind == "move":
        base += 0.6
    elif step.action.kind == "inspect":
        base += 0.7
    if step.role == "decoy":
        base += 0.6
    return base


def pearson(x: Sequence[float], y: Sequence[float]) -> float:
    if len(x) < 2 or len(y) < 2:
        return 0.0
    x_arr = np.asarray(x, dtype=float)
    y_arr = np.asarray(y, dtype=float)
    if np.std(x_arr) < 1e-9 or np.std(y_arr) < 1e-9:
        return 0.0
    return float(np.corrcoef(x_arr, y_arr)[0, 1])


class NaiveBayesDetector:
    def __init__(self) -> None:
        self.class_log_prior: Dict[int, float] = {}
        self.token_log_prob: Dict[int, Dict[str, float]] = {}
        self.default_log_prob: Dict[int, float] = {}
        self.vocab: set[str] = set()

    @staticmethod
    def tokenize(text: str) -> List[str]:
        return [token.lower() for token in text.replace("\n", " ").split()]

    def fit(self, texts: Sequence[str], labels: Sequence[int]) -> None:
        label_to_counts: Dict[int, Counter[str]] = defaultdict(Counter)
        doc_counts: Counter[int] = Counter()
        for text, label in zip(texts, labels):
            doc_counts[label] += 1
            for token in self.tokenize(text):
                self.vocab.add(token)
                label_to_counts[label][token] += 1
        total_docs = max(1, len(texts))
        vocab_size = max(1, len(self.vocab))
        for label, counts in label_to_counts.items():
            token_total = sum(counts.values())
            self.class_log_prior[label] = math.log(doc_counts[label] / total_docs)
            self.token_log_prob[label] = {}
            for token in self.vocab:
                value = (counts[token] + 1.0) / (token_total + vocab_size)
                self.token_log_prob[label][token] = math.log(value)
            self.default_log_prob[label] = math.log(1.0 / (token_total + vocab_size))

    def predict_log_odds(self, text: str) -> float:
        scores = {}
        tokens = self.tokenize(text)
        for label, prior in self.class_log_prior.items():
            score = prior
            default = self.default_log_prob[label]
            token_probs = self.token_log_prob[label]
            for token in tokens:
                score += token_probs.get(token, default)
            scores[label] = score
        return scores.get(1, -1e9) - scores.get(0, -1e9)

    def predict(self, text: str) -> int:
        return int(self.predict_log_odds(text) >= 0.0)

    def accuracy(self, texts: Sequence[str], labels: Sequence[int]) -> float:
        if not texts:
            return 0.0
        correct = sum(int(self.predict(text) == label) for text, label in zip(texts, labels))
        return correct / len(texts)


def best_length_only_accuracy(texts: Sequence[str], labels: Sequence[int]) -> float:
    if not texts:
        return 0.0
    lengths = [len(text.split()) for text in texts]
    candidates = sorted(set(lengths))
    best = 0.0
    for threshold in candidates:
        preds = [int(length >= threshold) for length in lengths]
        accuracy = sum(int(pred == label) for pred, label in zip(preds, labels)) / len(labels)
        best = max(best, accuracy, 1.0 - accuracy)
    return best


def rank_overlap(top_a: Sequence[int], top_b: Sequence[int]) -> float:
    if not top_a or not top_b:
        return 0.0
    a = set(top_a)
    b = set(top_b)
    return len(a & b) / len(a | b)


def run_synthetic_benchmark(
    num_instances: int = 48,
    sigma: float = 0.35,
) -> Dict[str, object]:
    policies = ("planner", "repair", "noisy")
    results: List[Dict[str, object]] = []
    detectability_rows: Dict[str, Dict[str, List[object]]] = {
        "drop": {"texts": [], "labels": [], "edited_texts": [], "edited_scores": []},
        "swap_local": {"texts": [], "labels": [], "edited_texts": [], "edited_scores": []},
        "swap_decoy": {"texts": [], "labels": [], "edited_texts": [], "edited_scores": []},
        "paraphrase": {"texts": [], "labels": [], "edited_texts": [], "edited_scores": []},
    }
    ctf_scores: Dict[str, List[float]] = defaultdict(list)
    asymmetry_deltas: List[float] = []
    mstl_values: List[float] = []
    necessity_recovery_gt: List[float] = []
    necessity_recovery_cnt: List[float] = []
    necessity_recovery_obs: List[float] = []
    necessity_recovery_entropy: List[float] = []
    necessity_recovery_future: List[float] = []

    for instance_idx in range(num_instances):
        primary = "red" if instance_idx % 2 == 0 else "green"
        world = SyntheticPlanningWorld(primary_path=primary)
        rng = random.Random(1000 + instance_idx)
        task = world.generate_trajectory(rng)
        instance_rows: List[Dict[str, object]] = []
        cnt_scores = []
        obs_scores = []
        entropy_scores = []
        future_scores = []
        gt_scores = []
        for candidate_index in task.candidate_indices:
            step = task.trajectory[candidate_index]
            variants = build_prefix_variants(world, task.trajectory, candidate_index)
            remaining_budget = task.total_budget - (candidate_index + 1)
            policy_deltas = []
            per_editor_deltas = []
            candidate_entropy_scores = []
            candidate_future_scores = []
            for policy in policies:
                original_prob = world.solve_probability(variants["original"].state, remaining_budget, policy)
                drop_prob = world.solve_probability(variants["drop"].state, remaining_budget, policy)
                local_prob = world.solve_probability(variants["swap_local"].state, remaining_budget, policy)
                decoy_prob = world.solve_probability(variants["swap_decoy"].state, remaining_budget, policy)
                candidate_future_scores.append(original_prob)
                candidate_entropy_scores.append(world.action_entropy(prefix_state(world, task.trajectory, candidate_index), policy))
                policy_deltas.append(float(np.mean([original_prob - drop_prob, original_prob - local_prob, original_prob - decoy_prob])))
                per_editor_deltas.extend(
                    [
                        original_prob - drop_prob,
                        original_prob - local_prob,
                        original_prob - decoy_prob,
                    ]
                )
            cnt = float(np.mean(policy_deltas))
            stability = float(math.exp(-np.var(per_editor_deltas) / max(sigma**2, 1e-9)))
            weighted_cnt = float(max(0.0, min(1.0, cnt * stability)))
            gt = float(
                np.mean(
                    [
                        world.reachable(variants["original"].state, remaining_budget) - world.reachable(variants["drop"].state, remaining_budget),
                        world.reachable(variants["original"].state, remaining_budget) - world.reachable(variants["swap_local"].state, remaining_budget),
                        world.reachable(variants["original"].state, remaining_budget) - world.reachable(variants["swap_decoy"].state, remaining_budget),
                    ]
                )
            )
            paraphrase_gap = float(
                np.mean(
                    [
                        world.solve_probability(variants["original"].state, remaining_budget, policy)
                        - world.solve_probability(variants["paraphrase"].state, remaining_budget, policy)
                        for policy in policies
                    ]
                )
            )
            random_step_idx = task.candidate_indices[0]
            random_variants = build_prefix_variants(world, task.trajectory, random_step_idx)
            random_budget = task.total_budget - (random_step_idx + 1)
            random_drop = float(
                np.mean(
                    [
                        world.solve_probability(random_variants["original"].state, random_budget, policy)
                        - world.solve_probability(random_variants["drop"].state, random_budget, policy)
                        for policy in policies
                    ]
                )
            )
            asymmetry_deltas.append(cnt - paraphrase_gap)
            obs = observational_score(step)
            entropy = float(np.mean(candidate_entropy_scores))
            future = float(np.mean(candidate_future_scores))
            cnt_scores.append(weighted_cnt)
            obs_scores.append(obs)
            entropy_scores.append(entropy)
            future_scores.append(future)
            gt_scores.append(gt)
            instance_rows.append(
                {
                    "instance_id": task.instance_id,
                    "candidate_index": candidate_index,
                    "role": step.role,
                    "step_text": step.text,
                    "gt_necessity": gt,
                    "cnt_score": weighted_cnt,
                    "observational_score": obs,
                    "entropy_score": entropy,
                    "future_success": future,
                    "paraphrase_gap": paraphrase_gap,
                    "random_drop_reference": random_drop,
                    "remaining_budget": remaining_budget,
                }
            )
            necessity_recovery_gt.append(gt)
            necessity_recovery_cnt.append(weighted_cnt)
            necessity_recovery_obs.append(obs)
            necessity_recovery_entropy.append(entropy)
            necessity_recovery_future.append(future)
            for family, variant in variants.items():
                if family == "original":
                    detectability_rows["drop"]["texts"].append(variant.prefix_text)
                    detectability_rows["drop"]["labels"].append(0)
                    detectability_rows["swap_local"]["texts"].append(variant.prefix_text)
                    detectability_rows["swap_local"]["labels"].append(0)
                    detectability_rows["swap_decoy"]["texts"].append(variant.prefix_text)
                    detectability_rows["swap_decoy"]["labels"].append(0)
                    detectability_rows["paraphrase"]["texts"].append(variant.prefix_text)
                    detectability_rows["paraphrase"]["labels"].append(0)
                    continue
                detectability_rows[family]["texts"].append(variant.prefix_text)
                detectability_rows[family]["labels"].append(1)
                detectability_rows[family]["edited_texts"].append(variant.prefix_text)
                detectability_rows[family]["edited_scores"].append(weighted_cnt)
        results.extend(instance_rows)
        top_cnt = sorted(range(len(cnt_scores)), key=lambda idx: cnt_scores[idx], reverse=True)[:2]
        top_obs = sorted(range(len(obs_scores)), key=lambda idx: obs_scores[idx], reverse=True)[:2]
        top_entropy = sorted(range(len(entropy_scores)), key=lambda idx: entropy_scores[idx], reverse=True)[:2]
        top_future = sorted(range(len(future_scores)), key=lambda idx: future_scores[idx], reverse=True)[:2]
        ctf_scores["cnt"].append(float(np.mean([gt_scores[idx] for idx in top_cnt])))
        ctf_scores["obs"].append(float(np.mean([gt_scores[idx] for idx in top_obs])))
        ctf_scores["entropy"].append(float(np.mean([gt_scores[idx] for idx in top_entropy])))
        ctf_scores["future"].append(float(np.mean([gt_scores[idx] for idx in top_future])))
        random_top = rng.sample(range(len(gt_scores)), k=min(2, len(gt_scores)))
        ctf_scores["random"].append(float(np.mean([gt_scores[idx] for idx in random_top])))
        sorted_indices = sorted(range(len(cnt_scores)), key=lambda idx: cnt_scores[idx])
        kept: List[int] = []
        dropped_candidates = {task.candidate_indices[i] for i in sorted_indices[:2]}
        for idx, step in enumerate(task.trajectory):
            if idx not in dropped_candidates:
                kept.append(idx)
        reduced_traj = [task.trajectory[idx] for idx in kept]
        try:
            final_state = prefix_state(world, reduced_traj, len(reduced_traj))
            mstl = len(reduced_traj) if world.reachable(final_state, max(0, task.total_budget - len(reduced_traj))) else len(task.trajectory)
        except ValueError:
            mstl = len(task.trajectory)
        mstl_values.append(mstl / len(task.trajectory))

    detectability_summary = {}
    detectability_corrs = []
    for family, payload in detectability_rows.items():
        texts = payload["texts"]
        labels = payload["labels"]
        split = max(4, len(texts) // 2)
        train_texts = texts[:split]
        train_labels = labels[:split]
        test_texts = texts[split:]
        test_labels = labels[split:]
        detector = NaiveBayesDetector()
        detector.fit(train_texts, train_labels)
        shallow_acc = detector.accuracy(test_texts, test_labels)
        length_acc = best_length_only_accuracy(test_texts, test_labels)
        edited_texts = payload["edited_texts"]
        edited_scores = payload["edited_scores"]
        edited_split = max(2, len(edited_texts) // 2)
        margins = [abs(detector.predict_log_odds(text)) for text in edited_texts[edited_split:]]
        sample_scores = edited_scores[edited_split:]
        corr = pearson(sample_scores, margins) if sample_scores else 0.0
        detectability_corrs.append(corr)
        detectability_summary[family] = {
            "shallow_accuracy": shallow_acc,
            "length_only_accuracy": length_acc,
            "corr_with_cnt": corr,
        }

    summary = {
        "num_instances": num_instances,
        "num_scored_steps": len(results),
        "synthetic_necessity_recovery": {
            "cnt_vs_gt_corr": pearson(necessity_recovery_cnt, necessity_recovery_gt),
            "observational_vs_gt_corr": pearson(necessity_recovery_obs, necessity_recovery_gt),
            "entropy_vs_gt_corr": pearson(necessity_recovery_entropy, necessity_recovery_gt),
            "future_success_vs_gt_corr": pearson(necessity_recovery_future, necessity_recovery_gt),
        },
        "detectability_audit": detectability_summary,
        "mean_detectability_corr": float(np.mean(detectability_corrs)),
        "ctf_proxy": {name: float(np.mean(values)) for name, values in ctf_scores.items()},
        "deletion_paraphrase_asymmetry": float(np.mean(asymmetry_deltas)),
        "mstl_ratio": float(np.mean(mstl_values)),
        "sample_rows": results[:6],
    }
    return {
        "summary": summary,
        "rows": results,
    }
