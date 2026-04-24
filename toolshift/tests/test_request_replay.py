from __future__ import annotations

import unittest

from toolshift import load_seed_suite
from toolshift.request_replay import replay_primary_action, run_request_replay_sanity


class RequestReplayTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.suite = load_seed_suite("data/real_evolution_benchmark.json")

    def test_drive_positive_migration_uses_v3_request_shape(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "drive_add_parent_to_file::positive_version_migration"
        )
        outcome = replay_primary_action(example)
        self.assertTrue(outcome.emitted)
        assert outcome.request is not None
        self.assertEqual(outcome.request.method, "PATCH")
        self.assertEqual(outcome.request.path, "/drive/v3/files/file_brief")
        self.assertEqual(outcome.request.query, {"addParents": "fld_reports"})

    def test_jira_positive_migration_uses_accountid_request_shape(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "jira_assign_issue_user_ref::positive_version_migration"
        )
        outcome = replay_primary_action(example)
        self.assertTrue(outcome.emitted)
        assert outcome.request is not None
        self.assertEqual(outcome.request.path, "/rest/api/3/issue/ENG-7/assignee")
        self.assertEqual(outcome.request.body, {"accountId": "acct_alice"})

    def test_jira_negative_legacy_identifier_replay_is_blocked(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "jira_search_assignable_user_legacy_username::negative_legacy_identifier_removed"
        )
        outcome = replay_primary_action(example)
        self.assertFalse(outcome.emitted)
        self.assertIn("capability gap", outcome.reason)

    def test_sheets_positive_migration_uses_values_append_request_shape(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "sheets_append_row::positive_version_migration"
        )
        outcome = replay_primary_action(example)
        self.assertTrue(outcome.emitted)
        assert outcome.request is not None
        self.assertEqual(outcome.request.method, "POST")
        self.assertEqual(outcome.request.path, "/v4/spreadsheets/sh_budget/values/ws_hours:append")
        self.assertEqual(outcome.request.query, {"valueInputOption": "RAW"})

    def test_sheets_negative_drive_scope_replay_is_blocked(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "sheets_list_accessible_spreadsheets::negative_drive_scope_replacement"
        )
        outcome = replay_primary_action(example)
        self.assertFalse(outcome.emitted)
        self.assertIn("capability gap", outcome.reason)

    def test_people_positive_migration_uses_connections_request_shape(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "people_list_my_contacts::positive_version_migration"
        )
        outcome = replay_primary_action(example)
        self.assertTrue(outcome.emitted)
        assert outcome.request is not None
        self.assertEqual(outcome.request.method, "GET")
        self.assertEqual(outcome.request.path, "/v1/people/me/connections")
        self.assertEqual(outcome.request.query, {"pageSize": 10, "personFields": "names,emailAddresses"})

    def test_people_negative_other_contacts_replay_is_blocked(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "people_update_other_contact_email::negative_other_contacts_read_only"
        )
        outcome = replay_primary_action(example)
        self.assertFalse(outcome.emitted)
        self.assertIn("capability gap", outcome.reason)

    def test_confluence_positive_migration_uses_v2_request_shape(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "confluence_get_page_storage::positive_version_migration"
        )
        outcome = replay_primary_action(example)
        self.assertTrue(outcome.emitted)
        assert outcome.request is not None
        self.assertEqual(outcome.request.method, "GET")
        self.assertEqual(outcome.request.path, "/wiki/api/v2/pages/2001")
        self.assertEqual(outcome.request.query, {"body-format": "storage"})

    def test_confluence_negative_space_key_lookup_replay_is_blocked(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "confluence_list_pages_by_space_key::negative_space_key_lookup_split"
        )
        outcome = replay_primary_action(example)
        self.assertFalse(outcome.emitted)
        self.assertIn("capability gap", outcome.reason)

    def test_bitbucket_positive_migration_uses_workspace_request_shape(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "bitbucket_get_workspace::positive_version_migration"
        )
        outcome = replay_primary_action(example)
        self.assertTrue(outcome.emitted)
        assert outcome.request is not None
        self.assertEqual(outcome.request.method, "GET")
        self.assertEqual(outcome.request.path, "/2.0/workspaces/eng-team")
        self.assertEqual(outcome.request.query, {})

    def test_bitbucket_negative_account_object_replay_is_blocked(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "bitbucket_get_legacy_account::negative_account_object_removed"
        )
        outcome = replay_primary_action(example)
        self.assertFalse(outcome.emitted)
        self.assertIn("capability gap", outcome.reason)

    def test_full_real_suite_request_replay_is_consistent(self) -> None:
        records, summary = run_request_replay_sanity(self.suite)
        self.assertEqual(len(records), 72)
        self.assertEqual(summary["pass_rate"], 1.0)
        self.assertEqual(summary["execute_render_pass_rate"], 1.0)
        self.assertEqual(summary["negative_block_pass_rate"], 1.0)
        self.assertEqual(summary["positive_equivalence_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()
