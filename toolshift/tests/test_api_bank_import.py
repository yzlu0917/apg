from __future__ import annotations

import unittest

from toolshift import OracleAgent, evaluate_agent, load_seed_suite


class ApiBankImportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.suite = load_seed_suite("data/api_bank_toolshift_benchmark.json")

    def test_api_bank_bridge_suite_loads(self) -> None:
        self.assertEqual(len(self.suite.cases), 12)
        self.assertEqual(len(self.suite.examples), 84)

    def test_api_bank_bridge_family_tags(self) -> None:
        family_tags = {case.family_tag for case in self.suite.cases}
        self.assertEqual(family_tags, {"api_bank_organizer", "api_bank_service", "api_bank_utility"})

    def test_api_bank_bridge_add_agenda_case_uses_transcript_context(self) -> None:
        case = next(case for case in self.suite.cases if case.case_id == "api_bank_add_agenda_level_1_1")
        self.assertIn("Dialogue context before the final API action:", case.request)
        self.assertIn("API[GetUserToken] output", case.request)
        self.assertEqual(case.primary_action.tool_id, "api_bank.add_agenda")

    def test_api_bank_bridge_view_generation_creates_negative_near_orbit(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "api_bank_translate_level_1_1::negative_contract"
        )
        self.assertEqual(example.schema_view.shift_kind.value, "negative_near_orbit")
        self.assertEqual([action.control.value for action in example.admissible_actions], ["ask_clarification"])

    def test_api_bank_bridge_oracle_is_perfect_on_core(self) -> None:
        _, summary = evaluate_agent(OracleAgent(), self.suite)
        self.assertEqual(summary["counts"]["core"], 72)
        self.assertEqual(summary["counts"]["impossible"], 12)
        self.assertAlmostEqual(summary["metrics"]["CAA_overall"], 1.0)
        self.assertAlmostEqual(summary["metrics"]["CAA_positive"], 1.0)
        self.assertAlmostEqual(summary["metrics"]["NOS"], 1.0)


if __name__ == "__main__":
    unittest.main()
