from __future__ import annotations

import unittest

from toolshift import DescriptionGroundedAgent, LexicalShortcutAgent, OracleAgent, evaluate_agent, load_seed_suite


class SeedPilotTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.suite = load_seed_suite("data/seed_benchmark.json")

    def test_oracle_is_perfect_on_main_splits(self) -> None:
        _, summary = evaluate_agent(OracleAgent(), self.suite)
        self.assertEqual(summary["metrics"]["CAA_overall"], 1.0)
        self.assertEqual(summary["metrics"]["POC"], 1.0)
        self.assertEqual(summary["metrics"]["NOS"], 1.0)

    def test_description_agent_beats_lexical_on_positive_shift(self) -> None:
        _, lexical_summary = evaluate_agent(LexicalShortcutAgent(), self.suite)
        _, description_summary = evaluate_agent(DescriptionGroundedAgent(), self.suite)
        self.assertGreater(
            description_summary["metrics"]["CAA_positive"],
            lexical_summary["metrics"]["CAA_positive"],
        )


if __name__ == "__main__":
    unittest.main()

