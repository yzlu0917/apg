from __future__ import annotations

import unittest

from toolshift import OracleAgent, evaluate_agent, load_seed_suite


class ToolEVOBridgeBenchmarkTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.suite = load_seed_suite("data/toolevo_bridge_benchmark.json")

    def test_bridge_suite_loads_expected_counts(self) -> None:
        self.assertEqual(len(self.suite.cases), 8)
        self.assertEqual(len(self.suite.examples), 32)
        view_ids = {example.schema_view.view_id for example in self.suite.examples}
        self.assertIn("toolevo_load_airbnb_db::positive_version_v1", view_ids)
        self.assertIn("toolevo_filter_by_author_name::positive_version_v2", view_ids)
        self.assertIn("toolevo_execute_sql_query::negative_legacy_deprecate", view_ids)

    def test_bridge_suite_is_all_core(self) -> None:
        _, summary = evaluate_agent(OracleAgent(), self.suite)
        self.assertEqual(summary["counts"]["core"], 32)
        self.assertEqual(summary["counts"]["ambiguous"], 0)
        self.assertEqual(summary["counts"]["impossible"], 0)

    def test_database_loader_versions_change_name_and_argument(self) -> None:
        clean = next(
            example
            for example in self.suite.examples
            if example.schema_view.view_id == "toolevo_load_airbnb_db::clean"
        )
        v1 = next(
            example
            for example in self.suite.examples
            if example.schema_view.view_id == "toolevo_load_airbnb_db::positive_version_v1"
        )
        v2 = next(
            example
            for example in self.suite.examples
            if example.schema_view.view_id == "toolevo_load_airbnb_db::positive_version_v2"
        )
        self.assertEqual(clean.schema_view.tools[0].rendered_name, "LoadDB")
        self.assertEqual(v1.schema_view.tools[0].rendered_name, "InitializeDatabase")
        self.assertEqual(v2.schema_view.tools[0].rendered_name, "Init_DB")
        self.assertEqual([arg.rendered_name for arg in clean.schema_view.tools[0].arguments], ["DBName"])
        self.assertEqual([arg.rendered_name for arg in v1.schema_view.tools[0].arguments], ["DatabaseName"])
        self.assertEqual([arg.rendered_name for arg in v2.schema_view.tools[0].arguments], ["databaseIdentifier"])

    def test_negative_legacy_view_allows_control_only(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "toolevo_filter_by_author_name::negative_legacy_deprecate"
        )
        self.assertEqual(example.schema_view.tools[0].status, "deprecated")
        self.assertEqual([action.control.value for action in example.admissible_actions], ["ask_clarification", "abstain"])

    def test_sql_versions_keep_same_canonical_tool(self) -> None:
        clean = next(
            example
            for example in self.suite.examples
            if example.schema_view.view_id == "toolevo_execute_sql_query::clean"
        )
        v2 = next(
            example
            for example in self.suite.examples
            if example.schema_view.view_id == "toolevo_execute_sql_query::positive_version_v2"
        )
        self.assertEqual(clean.case.admissible_actions[0].tool_id, "toolevo.sql.execute")
        self.assertEqual(v2.case.admissible_actions[0].tool_id, "toolevo.sql.execute")
        self.assertEqual(v2.schema_view.tools[0].rendered_name, "ProcessSQLQuery")
        self.assertEqual([arg.rendered_name for arg in v2.schema_view.tools[0].arguments], ["SQL_Query"])


if __name__ == "__main__":
    unittest.main()
