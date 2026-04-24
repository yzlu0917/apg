from __future__ import annotations

import unittest

try:
    import torch
except ModuleNotFoundError:  # pragma: no cover
    torch = None

from toolshift import load_seed_suite
from toolshift.decision_probe import evaluate_linear_probe, extract_decision_state, fit_linear_probe
from toolshift.embedding_policy import EmbeddingPolicyConfig, train_embedding_policy_agent


@unittest.skipIf(torch is None, "torch not available")
class DecisionProbeTest(unittest.TestCase):
    def test_fit_linear_probe_separates_simple_binary_states(self) -> None:
        states = [
            torch.tensor([2.0, 2.0]),
            torch.tensor([1.5, 1.5]),
            torch.tensor([-2.0, -2.0]),
            torch.tensor([-1.5, -1.0]),
        ]
        labels = [True, True, False, False]
        probe, train_stats = fit_linear_probe(states, labels, epochs=200, learning_rate=0.1)
        metrics = evaluate_linear_probe(probe, states, labels)
        self.assertGreaterEqual(train_stats["train_accuracy"], 0.99)
        self.assertGreaterEqual(metrics["accuracy"], 0.99)

    def test_extract_decision_state_supports_embedding_policy_agent(self) -> None:
        suite = load_seed_suite("data/family_benchmark.json")
        train_examples = tuple(example for example in suite.examples if example.case.case_id == "fx_eur_to_gbp")
        feature_lookup = {
            example.schema_view.view_id: torch.tensor([float(index + 1)] * 6, dtype=torch.float32)
            for index, example in enumerate(train_examples)
        }
        agent, _ = train_embedding_policy_agent(
            name="decision_probe_aug_only",
            suite=suite,
            train_examples=train_examples,
            feature_lookup=feature_lookup,
            config=EmbeddingPolicyConfig(epochs=1, bottleneck_dim=4, learning_rate=1e-2, weight_decay=0.0),
            method="aug_only",
            encoder=None,
        )
        state = extract_decision_state(agent, train_examples[0])
        self.assertEqual(state.ndim, 1)
        self.assertGreater(state.numel(), 4)


if __name__ == "__main__":
    unittest.main()
