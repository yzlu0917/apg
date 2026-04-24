from __future__ import annotations

import unittest

from scripts.run_matched_budget_pilot import _primary_family_groups
from toolshift import OracleAgent, evaluate_agent, load_seed_suite


class RealEvolutionBlindBenchmarkTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.suite = load_seed_suite("data/real_evolution_blind_benchmark.json")

    def test_blind_suite_loads_explicit_views(self) -> None:
        self.assertEqual(len(self.suite.cases), 24)
        self.assertEqual(len(self.suite.examples), 48)
        view_ids = {example.schema_view.view_id for example in self.suite.examples}
        self.assertIn("trello_poll_member_privacy_since::positive_version_migration", view_ids)
        self.assertIn("trello_poll_member_privacy_window::positive_version_migration", view_ids)
        self.assertIn("trello_list_scim_groups::negative_workspace_listing_replacement", view_ids)
        self.assertIn("trello_list_scim_users::negative_member_query_replacement", view_ids)
        self.assertIn("youtube_add_top_level_comment::positive_version_migration", view_ids)
        self.assertIn("youtube_list_upload_videos::positive_version_migration", view_ids)
        self.assertIn("youtube_search_related_videos::negative_related_parameter_removed", view_ids)
        self.assertIn("youtube_mark_comment_spam::negative_deprecate", view_ids)
        self.assertIn("youtube_channels_get_profile::positive_version_migration", view_ids)
        self.assertIn("youtube_channels_get_uploads_playlist::positive_version_migration", view_ids)
        self.assertIn("youtube_channels_list_uploaded_videos::negative_playlist_lookup_split", view_ids)
        self.assertIn("youtube_activities_list_recommended_videos::negative_home_feed_broader_surface", view_ids)
        self.assertIn("github_list_custom_repository_roles::positive_version_migration", view_ids)
        self.assertIn("github_get_custom_repository_role::positive_version_migration", view_ids)
        self.assertIn("github_delete_generic_reaction::negative_resource_context_split", view_ids)
        self.assertIn("github_import_external_repository::negative_out_of_band_replacement", view_ids)
        self.assertIn("gitlab_get_merge_request_merge_actor::positive_version_migration", view_ids)
        self.assertIn("gitlab_get_merge_request_detailed_status::positive_version_migration", view_ids)
        self.assertIn("gitlab_get_merge_request_with_changes::negative_changes_endpoint_split", view_ids)
        self.assertIn("gitlab_import_project_archive_ambiguous_namespace::negative_namespace_disambiguation", view_ids)
        self.assertIn("slack_exchange_install_code::positive_version_migration", view_ids)
        self.assertIn("slack_get_user_email::positive_scope_migration", view_ids)
        self.assertIn("slack_get_conversation_history::positive_scope_migration", view_ids)
        self.assertIn("slack_get_granted_permissions::negative_permissions_inventory_split", view_ids)

    def test_blind_suite_is_all_core(self) -> None:
        _, summary = evaluate_agent(OracleAgent(), self.suite)
        self.assertEqual(summary["counts"]["core"], 48)
        self.assertEqual(summary["counts"]["ambiguous"], 0)
        self.assertEqual(summary["counts"]["impossible"], 0)

    def test_blind_family_groups_use_vendor_family_tags(self) -> None:
        groups = _primary_family_groups(self.suite)
        self.assertEqual(set(groups), {"trello", "youtube", "youtube_channels", "github_rest", "gitlab_rest", "slack_auth"})
        self.assertEqual({len(case_ids) for case_ids in groups.values()}, {4})

    def test_positive_migration_uses_plugin_identifier(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "trello_poll_member_privacy_since::positive_version_migration"
        )
        rendered_arguments = [argument.rendered_name for argument in example.schema_view.tools[0].arguments]
        self.assertEqual(rendered_arguments, ["id", "since", "limit"])

    def test_negative_current_schema_uses_enterprise_member_query(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "trello_list_scim_users::negative_member_query_replacement"
        )
        rendered_arguments = [argument.rendered_name for argument in example.schema_view.tools[0].arguments]
        self.assertEqual(rendered_arguments, ["id", "query"])
        self.assertEqual([action.control.value for action in example.admissible_actions], ["ask_clarification", "abstain"])

    def test_youtube_positive_migration_uses_playlistitems_list_arguments(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "youtube_list_upload_videos::positive_version_migration"
        )
        rendered_arguments = [argument.rendered_name for argument in example.schema_view.tools[0].arguments]
        self.assertEqual(rendered_arguments, ["playlistId", "maxResults"])

    def test_youtube_negative_related_search_removes_seed_parameter(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "youtube_search_related_videos::negative_related_parameter_removed"
        )
        rendered_arguments = [argument.rendered_name for argument in example.schema_view.tools[0].arguments]
        self.assertEqual(rendered_arguments, ["maxResults"])
        self.assertEqual([action.control.value for action in example.admissible_actions], ["ask_clarification", "abstain"])

    def test_youtube_negative_deprecate_is_abstain_only(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "youtube_mark_comment_spam::negative_deprecate"
        )
        self.assertEqual([action.control.value for action in example.admissible_actions], ["abstain"])

    def test_youtube_channels_positive_profile_migration_uses_channels_list(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "youtube_channels_get_profile::positive_version_migration"
        )
        rendered_arguments = [argument.rendered_name for argument in example.schema_view.tools[0].arguments]
        self.assertEqual(rendered_arguments, ["id"])

    def test_youtube_channels_negative_playlist_lookup_split_requires_lookup(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "youtube_channels_list_uploaded_videos::negative_playlist_lookup_split"
        )
        rendered_arguments = [argument.rendered_name for argument in example.schema_view.tools[0].arguments]
        self.assertEqual(rendered_arguments, ["playlistId", "maxResults"])
        self.assertEqual([action.control.value for action in example.admissible_actions], ["ask_clarification", "abstain"])

    def test_youtube_channels_negative_home_feed_is_not_drop_in(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "youtube_activities_list_recommended_videos::negative_home_feed_broader_surface"
        )
        rendered_arguments = [argument.rendered_name for argument in example.schema_view.tools[0].arguments]
        self.assertEqual(rendered_arguments, ["home", "maxResults"])
        self.assertEqual([action.control.value for action in example.admissible_actions], ["ask_clarification", "abstain"])

    def test_github_positive_custom_role_migration_uses_ga_path(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "github_list_custom_repository_roles::positive_version_migration"
        )
        self.assertEqual(example.schema_view.tools[0].rendered_name, "orgs.custom-repository-roles.list")
        rendered_arguments = [argument.rendered_name for argument in example.schema_view.tools[0].arguments]
        self.assertEqual(rendered_arguments, ["org", "per_page"])

    def test_github_negative_reaction_delete_requires_resource_context(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "github_delete_generic_reaction::negative_resource_context_split"
        )
        rendered_arguments = [argument.rendered_name for argument in example.schema_view.tools[0].arguments]
        self.assertEqual(rendered_arguments, ["owner", "repo", "issue_number", "reaction_id"])
        self.assertEqual([action.control.value for action in example.admissible_actions], ["ask_clarification", "abstain"])

    def test_github_negative_source_import_is_not_drop_in(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "github_import_external_repository::negative_out_of_band_replacement"
        )
        rendered_names = [tool.rendered_name for tool in example.schema_view.tools]
        self.assertEqual(rendered_names, ["repos.create_in_org", "repos.create_using_template", "repos.create_fork"])
        self.assertEqual([action.control.value for action in example.admissible_actions], ["ask_clarification", "abstain"])

    def test_gitlab_positive_merge_actor_migration_uses_same_endpoint_new_field(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "gitlab_get_merge_request_merge_actor::positive_version_migration"
        )
        self.assertEqual(example.schema_view.tools[0].rendered_name, "merge_requests.get")
        rendered_arguments = [argument.rendered_name for argument in example.schema_view.tools[0].arguments]
        self.assertEqual(rendered_arguments, ["id", "merge_request_iid"])

    def test_gitlab_negative_changes_endpoint_split_is_not_drop_in(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "gitlab_get_merge_request_with_changes::negative_changes_endpoint_split"
        )
        self.assertEqual(example.schema_view.tools[0].rendered_name, "merge_requests.diffs.list")
        self.assertEqual([action.control.value for action in example.admissible_actions], ["ask_clarification", "abstain"])

    def test_gitlab_negative_namespace_disambiguation_requires_id_or_path(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "gitlab_import_project_archive_ambiguous_namespace::negative_namespace_disambiguation"
        )
        rendered_names = [tool.rendered_name for tool in example.schema_view.tools[:2]]
        self.assertEqual(rendered_names, ["projects.import", "projects.import"])
        rendered_arguments = [argument.rendered_name for argument in example.schema_view.tools[0].arguments]
        self.assertEqual(rendered_arguments, ["file", "path", "namespace_id"])
        self.assertEqual([action.control.value for action in example.admissible_actions], ["ask_clarification", "abstain"])

    def test_slack_positive_oauth_migration_uses_oauth_v2(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "slack_exchange_install_code::positive_version_migration"
        )
        self.assertEqual(example.schema_view.tools[0].rendered_name, "oauth.v2.access")
        rendered_arguments = [argument.rendered_name for argument in example.schema_view.tools[0].arguments]
        self.assertEqual(rendered_arguments, ["code", "redirect_uri"])

    def test_slack_positive_user_email_migration_keeps_users_info(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "slack_get_user_email::positive_scope_migration"
        )
        self.assertEqual(example.schema_view.tools[0].rendered_name, "users.info")
        rendered_arguments = [argument.rendered_name for argument in example.schema_view.tools[0].arguments]
        self.assertEqual(rendered_arguments, ["user"])

    def test_slack_negative_permissions_inventory_is_split(self) -> None:
        example = next(
            item
            for item in self.suite.examples
            if item.schema_view.view_id == "slack_get_granted_permissions::negative_permissions_inventory_split"
        )
        rendered_names = [tool.rendered_name for tool in example.schema_view.tools[:2]]
        self.assertEqual(rendered_names, ["apps.permissions.scopes.list", "apps.permissions.resources.list"])
        self.assertEqual([action.control.value for action in example.admissible_actions], ["ask_clarification", "abstain"])


if __name__ == "__main__":
    unittest.main()
