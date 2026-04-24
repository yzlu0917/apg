from __future__ import annotations

import unittest
from collections import Counter

from toolshift import OracleAgent, evaluate_agent, load_seed_suite


class BFCLBridgeBenchmarkTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.suite = load_seed_suite("data/bfcl_bridge_benchmark.json")

    def test_bridge_suite_loads_expected_counts(self) -> None:
        self.assertEqual(len(self.suite.cases), 50)
        self.assertEqual(len(self.suite.examples), 50)
        case_ids = {case.case_id for case in self.suite.cases}
        self.assertIn("bfcl_simple_python_simple_python_0", case_ids)
        self.assertIn("bfcl_live_simple_live_simple_0-0-0", case_ids)
        self.assertIn("bfcl_irrelevance_irrelevance_0", case_ids)
        self.assertIn("bfcl_live_irrelevance_live_irrelevance_10-1-0", case_ids)

    def test_bridge_suite_preserves_category_balance(self) -> None:
        counts = Counter(case.family_tag for case in self.suite.cases)
        self.assertEqual(
            counts,
            {
                "simple_python": 10,
                "multiple": 10,
                "live_simple": 10,
                "irrelevance": 10,
                "live_irrelevance": 10,
            },
        )

    def test_execute_case_keeps_set_valued_admissible_actions(self) -> None:
        example = next(item for item in self.suite.examples if item.case.case_id == "bfcl_simple_python_simple_python_0")
        self.assertEqual(example.schema_view.tools[0].rendered_name, "calculate_triangle_area")
        self.assertEqual(len(example.admissible_actions), 2)
        self.assertEqual(
            {tuple(sorted(action.arguments.items())) for action in example.admissible_actions},
            {
                (("base", 10), ("height", 5)),
                (("base", 10), ("height", 5), ("unit", "units")),
            },
        )

    def test_irrelevance_case_maps_to_abstain(self) -> None:
        example = next(item for item in self.suite.examples if item.case.case_id == "bfcl_irrelevance_irrelevance_0")
        self.assertEqual([action.control.value for action in example.admissible_actions], ["abstain"])

    def test_oracle_is_perfect_on_bridge_suite(self) -> None:
        _, summary = evaluate_agent(OracleAgent(), self.suite)
        self.assertEqual(summary["metrics"]["CAA_overall"], 1.0)
        self.assertEqual(summary["metrics"]["CAA_clean"], 1.0)
        self.assertEqual(summary["metrics"]["contract_validity"], 1.0)


if __name__ == "__main__":
    unittest.main()
