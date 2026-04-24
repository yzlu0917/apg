from __future__ import annotations

import unittest

from toolshift import load_seed_suite
from toolshift.execution_sanity import run_execution_sanity, simulate_primary_action


class ExecutionSanityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.suite = load_seed_suite("data/real_evolution_benchmark.json")

    def test_clean_execute_case_satisfies_request(self) -> None:
        example = next(
            item for item in self.suite.examples if item.schema_view.view_id == "notion_append_paragraph_block::clean"
        )
        outcome = simulate_primary_action(example)
        self.assertTrue(outcome.executed)
        self.assertTrue(outcome.request_satisfied)

    def test_positive_version_migration_preserves_effect(self) -> None:
        clean_example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "stripe_create_checkout_session_with_coupon::clean"
        )
        positive_example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "stripe_create_checkout_session_with_coupon::positive_version_migration"
        )
        clean_outcome = simulate_primary_action(clean_example)
        positive_outcome = simulate_primary_action(positive_example)
        self.assertTrue(clean_outcome.request_satisfied)
        self.assertTrue(positive_outcome.request_satisfied)
        self.assertEqual(clean_outcome.effect["price_id"], positive_outcome.effect["price_id"])
        self.assertEqual(clean_outcome.effect["coupon_id"], positive_outcome.effect["coupon_id"])

    def test_negative_capability_gap_blocks_old_action(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "stripe_update_subscription_source::negative_source_removed"
        )
        outcome = simulate_primary_action(example)
        self.assertFalse(outcome.executed)
        self.assertFalse(outcome.request_satisfied)

    def test_negative_parent_scope_change_blocks_old_action(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "notion_create_page_in_database::negative_parent_scope_change"
        )
        outcome = simulate_primary_action(example)
        self.assertFalse(outcome.executed)
        self.assertFalse(outcome.request_satisfied)

    def test_drive_positive_version_migration_preserves_effect(self) -> None:
        clean_example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "drive_add_parent_to_file::clean"
        )
        positive_example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "drive_add_parent_to_file::positive_version_migration"
        )
        clean_outcome = simulate_primary_action(clean_example)
        positive_outcome = simulate_primary_action(positive_example)
        self.assertTrue(clean_outcome.request_satisfied)
        self.assertTrue(positive_outcome.request_satisfied)
        self.assertEqual(clean_outcome.effect["parent_ids"], positive_outcome.effect["parent_ids"])

    def test_drive_negative_shortcut_replacement_blocks_old_action(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "drive_add_file_to_second_folder::negative_shortcut_replacement"
        )
        outcome = simulate_primary_action(example)
        self.assertFalse(outcome.executed)
        self.assertFalse(outcome.request_satisfied)

    def test_jira_positive_version_migration_preserves_search_effect(self) -> None:
        clean_example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "jira_search_assignable_user_query::clean"
        )
        positive_example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "jira_search_assignable_user_query::positive_version_migration"
        )
        clean_outcome = simulate_primary_action(clean_example)
        positive_outcome = simulate_primary_action(positive_example)
        self.assertTrue(clean_outcome.request_satisfied)
        self.assertTrue(positive_outcome.request_satisfied)
        self.assertEqual(clean_outcome.effect["matched_user_ref"], positive_outcome.effect["matched_user_ref"])

    def test_jira_negative_legacy_identifier_blocks_old_action(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "jira_search_assignable_user_legacy_username::negative_legacy_identifier_removed"
        )
        outcome = simulate_primary_action(example)
        self.assertFalse(outcome.executed)
        self.assertFalse(outcome.request_satisfied)

    def test_sheets_positive_version_migration_preserves_append_effect(self) -> None:
        clean_example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "sheets_append_row::clean"
        )
        positive_example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "sheets_append_row::positive_version_migration"
        )
        clean_outcome = simulate_primary_action(clean_example)
        positive_outcome = simulate_primary_action(positive_example)
        self.assertTrue(clean_outcome.request_satisfied)
        self.assertTrue(positive_outcome.request_satisfied)
        self.assertEqual(clean_outcome.effect["row_values"], positive_outcome.effect["row_values"])

    def test_sheets_negative_drive_scope_replacement_blocks_old_action(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "sheets_list_accessible_spreadsheets::negative_drive_scope_replacement"
        )
        outcome = simulate_primary_action(example)
        self.assertFalse(outcome.executed)
        self.assertFalse(outcome.request_satisfied)

    def test_people_positive_version_migration_preserves_contact_creation_effect(self) -> None:
        clean_example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "people_create_contact::clean"
        )
        positive_example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "people_create_contact::positive_version_migration"
        )
        clean_outcome = simulate_primary_action(clean_example)
        positive_outcome = simulate_primary_action(positive_example)
        self.assertTrue(clean_outcome.request_satisfied)
        self.assertTrue(positive_outcome.request_satisfied)
        self.assertEqual(clean_outcome.effect["given_name"], positive_outcome.effect["given_name"])
        self.assertEqual(clean_outcome.effect["email"], positive_outcome.effect["email"])

    def test_people_negative_other_contacts_read_only_blocks_old_action(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "people_update_other_contact_email::negative_other_contacts_read_only"
        )
        outcome = simulate_primary_action(example)
        self.assertFalse(outcome.executed)
        self.assertFalse(outcome.request_satisfied)

    def test_confluence_positive_version_migration_preserves_page_storage_effect(self) -> None:
        clean_example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "confluence_get_page_storage::clean"
        )
        positive_example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "confluence_get_page_storage::positive_version_migration"
        )
        clean_outcome = simulate_primary_action(clean_example)
        positive_outcome = simulate_primary_action(positive_example)
        self.assertTrue(clean_outcome.request_satisfied)
        self.assertTrue(positive_outcome.request_satisfied)
        self.assertEqual(clean_outcome.effect["page_id"], positive_outcome.effect["page_id"])
        self.assertEqual(clean_outcome.effect["body_html"], positive_outcome.effect["body_html"])

    def test_confluence_negative_space_key_lookup_split_blocks_old_action(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "confluence_list_pages_by_space_key::negative_space_key_lookup_split"
        )
        outcome = simulate_primary_action(example)
        self.assertFalse(outcome.executed)
        self.assertFalse(outcome.request_satisfied)

    def test_bitbucket_positive_version_migration_preserves_workspace_profile_effect(self) -> None:
        clean_example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "bitbucket_get_workspace::clean"
        )
        positive_example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "bitbucket_get_workspace::positive_version_migration"
        )
        clean_outcome = simulate_primary_action(clean_example)
        positive_outcome = simulate_primary_action(positive_example)
        self.assertTrue(clean_outcome.request_satisfied)
        self.assertTrue(positive_outcome.request_satisfied)
        self.assertEqual(clean_outcome.effect["workspace_slug"], positive_outcome.effect["workspace_slug"])
        self.assertEqual(clean_outcome.effect["display_name"], positive_outcome.effect["display_name"])

    def test_bitbucket_negative_account_object_removed_blocks_old_action(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "bitbucket_get_legacy_account::negative_account_object_removed"
        )
        outcome = simulate_primary_action(example)
        self.assertFalse(outcome.executed)
        self.assertFalse(outcome.request_satisfied)

    def test_expanded_real_suite_execution_sanity_is_consistent(self) -> None:
        records, summary = run_execution_sanity(self.suite)
        self.assertEqual(len(records), 72)
        self.assertEqual(summary["pass_rate"], 1.0)
        self.assertEqual(summary["execute_expected_pass_rate"], 1.0)
        self.assertEqual(summary["negative_guard_pass_rate"], 1.0)
        self.assertEqual(summary["positive_equivalence_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()
