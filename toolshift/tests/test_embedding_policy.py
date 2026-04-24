from __future__ import annotations

import unittest

from toolshift import OracleAgent, evaluate_agent, load_seed_suite
from toolshift.embedding_policy import build_tool_vocab, serialize_view


class EmbeddingPolicyUtilsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.suite = load_seed_suite("data/seed_benchmark.json")

    def test_serialize_view_uses_visible_schema_without_transform_labels(self) -> None:
        example = next(item for item in self.suite.examples if item.schema_view.view_id == "weather_shanghai_celsius::positive_combo")
        serialized = serialize_view(example)
        self.assertIn("User request:", serialized)
        self.assertIn("weather_debug_console", serialized)
        self.assertNotIn("positive_combo", serialized)
        self.assertNotIn(example.schema_view.notes, serialized)

    def test_tool_vocab_includes_distractors(self) -> None:
        tool_vocab = build_tool_vocab(self.suite)
        self.assertIn("distractor.weather", tool_vocab)
        self.assertIn("weather.get_current", tool_vocab)

    def test_evaluate_agent_can_run_on_subset_examples(self) -> None:
        subset = tuple(self.suite.examples_for_case("weather_shanghai_celsius"))
        records, summary = evaluate_agent(OracleAgent(), self.suite, examples=subset)
        self.assertEqual(len(records), len(subset))
        self.assertEqual(summary["metrics"]["CAA_overall"], 1.0)


if __name__ == "__main__":
    unittest.main()
