from __future__ import annotations

import unittest
from collections import Counter

from toolshift import OracleAgent, evaluate_agent, load_seed_suite
from scripts.run_matched_budget_pilot import _primary_family_groups


class FamilyBenchmarkTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.suite = load_seed_suite("data/family_benchmark.json")

    def test_family_suite_has_same_family_support(self) -> None:
        family_counts = Counter(case.primary_action.tool_id for case in self.suite.cases)
        self.assertEqual(len(self.suite.cases), 18)
        self.assertEqual(set(family_counts.values()), {3})

    def test_family_suite_is_all_core(self) -> None:
        _, summary = evaluate_agent(OracleAgent(), self.suite)
        self.assertEqual(summary["counts"]["core"], 108)
        self.assertEqual(summary["counts"]["ambiguous"], 0)
        self.assertEqual(summary["counts"]["impossible"], 18)

    def test_family_audit_makes_negative_deprecate_abstain_only(self) -> None:
        example = next(item for item in self.suite.examples if item.schema_view.view_id == "email_weekly_status::negative_deprecate")
        self.assertEqual([action.control.value for action in example.admissible_actions], ["abstain"])

    def test_primary_family_groups_support_family_holdout(self) -> None:
        groups = _primary_family_groups(self.suite)
        self.assertEqual(len(groups), 6)
        self.assertEqual({len(case_ids) for case_ids in groups.values()}, {3})


if __name__ == "__main__":
    unittest.main()
