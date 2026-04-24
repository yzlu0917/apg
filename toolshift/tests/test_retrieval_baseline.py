from __future__ import annotations

import unittest

from toolshift import DocumentRetrievalRerankAgent, load_seed_suite
from toolshift.schema import ControlTag


class RetrievalBaselineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.suite = load_seed_suite("data/seed_benchmark.json")
        cls.agent = DocumentRetrievalRerankAgent()

    def _example(self, view_id: str):
        for example in self.suite.examples:
            if example.schema_view.view_id == view_id:
                return example
        raise KeyError(view_id)

    def test_executes_clean_weather_view(self) -> None:
        example = self._example("weather_shanghai_celsius::clean")
        prediction = self.agent.predict(example)
        self.assertEqual(prediction.control, ControlTag.EXECUTE)
        self.assertEqual(prediction.rendered_tool_name, "get_current")
        self.assertEqual(prediction.arguments["city"], "Shanghai")

    def test_returns_non_execute_on_negative_deprecate_view(self) -> None:
        example = self._example("weather_shanghai_celsius::negative_deprecate")
        prediction = self.agent.predict(example)
        self.assertIn(prediction.control, {ControlTag.ABSTAIN, ControlTag.ASK_CLARIFICATION})


if __name__ == "__main__":
    unittest.main()
