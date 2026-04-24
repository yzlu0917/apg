from __future__ import annotations

import unittest

from toolshift import OracleAgent, evaluate_agent, load_seed_suite
from scripts.run_matched_budget_pilot import _primary_family_groups


class RealEvolutionBenchmarkTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.suite = load_seed_suite("data/real_evolution_benchmark.json")

    def test_real_suite_loads_explicit_views(self) -> None:
        self.assertEqual(len(self.suite.cases), 36)
        self.assertEqual(len(self.suite.examples), 72)
        view_ids = {example.schema_view.view_id for example in self.suite.examples}
        self.assertIn("notion_append_paragraph_block::positive_version_migration", view_ids)
        self.assertIn("slack_upload_file_to_channel::negative_deprecate", view_ids)
        self.assertIn("stripe_update_subscription_source::negative_source_removed", view_ids)
        self.assertIn("drive_add_file_to_second_folder::negative_shortcut_replacement", view_ids)
        self.assertIn("jira_search_assignable_user_legacy_username::negative_legacy_identifier_removed", view_ids)
        self.assertIn("sheets_list_accessible_spreadsheets::negative_drive_scope_replacement", view_ids)
        self.assertIn("people_update_other_contact_email::negative_other_contacts_read_only", view_ids)
        self.assertIn("confluence_list_pages_by_space_key::negative_space_key_lookup_split", view_ids)
        self.assertIn("bitbucket_get_legacy_account::negative_account_object_removed", view_ids)

    def test_real_suite_is_all_core(self) -> None:
        _, summary = evaluate_agent(OracleAgent(), self.suite)
        self.assertEqual(summary["counts"]["core"], 72)
        self.assertEqual(summary["counts"]["ambiguous"], 0)
        self.assertEqual(summary["counts"]["impossible"], 0)

    def test_family_groups_use_vendor_family_tags(self) -> None:
        groups = _primary_family_groups(self.suite)
        self.assertEqual(
            set(groups),
            {"bitbucket", "confluence", "drive", "jira", "notion", "people", "sheets", "slack", "stripe"},
        )
        self.assertEqual({len(case_ids) for case_ids in groups.values()}, {4})

    def test_positive_migration_uses_new_rendered_argument_names(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "stripe_create_customer_with_tax_id::positive_version_migration"
        )
        rendered_arguments = [argument.rendered_name for argument in example.schema_view.tools[0].arguments]
        self.assertEqual(rendered_arguments, ["email", "tax_id_data.type", "tax_id_data.value"])

    def test_drive_positive_migration_uses_shared_drive_argument_names(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "drive_list_shared_drive_items::positive_version_migration"
        )
        rendered_arguments = [argument.rendered_name for argument in example.schema_view.tools[0].arguments]
        self.assertEqual(rendered_arguments, ["driveId", "includeItemsFromAllDrives", "supportsAllDrives"])

    def test_jira_positive_migration_uses_query_parameter(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "jira_search_assignable_user_query::positive_version_migration"
        )
        rendered_arguments = [argument.rendered_name for argument in example.schema_view.tools[0].arguments]
        self.assertEqual(rendered_arguments, ["project", "query"])

    def test_sheets_positive_migration_uses_value_range_arguments(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "sheets_append_row::positive_version_migration"
        )
        rendered_arguments = [argument.rendered_name for argument in example.schema_view.tools[0].arguments]
        self.assertEqual(rendered_arguments, ["spreadsheetId", "range", "values"])

    def test_people_positive_migration_uses_people_api_argument_names(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "people_create_contact::positive_version_migration"
        )
        rendered_arguments = [argument.rendered_name for argument in example.schema_view.tools[0].arguments]
        self.assertEqual(rendered_arguments, ["names", "emailAddresses"])

    def test_confluence_negative_current_schema_uses_spaceid_argument(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "confluence_list_pages_by_space_key::negative_space_key_lookup_split"
        )
        rendered_arguments = [argument.rendered_name for argument in example.schema_view.tools[0].arguments]
        self.assertEqual(rendered_arguments, ["spaceId"])

    def test_bitbucket_positive_migration_uses_workspace_argument_name(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "bitbucket_get_workspace::positive_version_migration"
        )
        rendered_arguments = [argument.rendered_name for argument in example.schema_view.tools[0].arguments]
        self.assertEqual(rendered_arguments, ["workspace"])

    def test_negative_deprecate_is_abstain_only(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "slack_upload_file_to_channel::negative_deprecate"
        )
        self.assertEqual([action.control.value for action in example.admissible_actions], ["abstain"])


if __name__ == "__main__":
    unittest.main()
