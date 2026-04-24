#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from generate_real_evolution_benchmark import (
    _abstain,
    _action,
    _ask,
    _canonical_arg,
    _canonical_tool,
    _case,
    _rendered_arg,
    _rendered_tool,
    _view,
)


def build_sources() -> dict[str, dict[str, str]]:
    return {
        "trello_2025_08_member_privacy_deprecation": {
            "vendor": "trello",
            "kind": "changelog",
            "url": "https://developer.atlassian.com/cloud/trello/changelog/",
            "summary": "Trello changelog entry for the 2025-08-06 deprecation of the legacy /application/:id/compliance/memberPrivacy route in favor of the plugin compliance route.",
        },
        "trello_gdpr_guide": {
            "vendor": "trello",
            "kind": "guide",
            "url": "https://developer.atlassian.com/cloud/trello/guides/compliance/personal-data-storage-gdpr/",
            "summary": "Trello privacy and compliance guide describing the supported plugin member privacy workflow.",
        },
        "trello_applications_ref": {
            "vendor": "trello",
            "kind": "reference",
            "url": "https://developer.atlassian.com/cloud/trello/rest/api-group-applications/",
            "summary": "Legacy Trello application reference group used as the old compliance-route anchor.",
        },
        "trello_plugins_ref": {
            "vendor": "trello",
            "kind": "reference",
            "url": "https://developer.atlassian.com/cloud/trello/rest/api-group-plugins/",
            "summary": "Current Trello plugin reference group containing plugin-scoped compliance endpoints.",
        },
        "trello_2025_09_scim_deprecation": {
            "vendor": "trello",
            "kind": "changelog",
            "url": "https://developer.atlassian.com/cloud/trello/changelog/",
            "summary": "Trello changelog entry for the 2025-09-15 deprecation of /scim/v2/users and /scim/v2/groups in favor of related REST endpoints.",
        },
        "trello_scim_routes_ref": {
            "vendor": "trello",
            "kind": "reference",
            "url": "https://developer.atlassian.com/cloud/trello/scim/routes/",
            "summary": "Current Trello SCIM routes reference describing legacy Users and Groups listing endpoints.",
        },
        "trello_scim_resources_ref": {
            "vendor": "trello",
            "kind": "reference",
            "url": "https://developer.atlassian.com/cloud/trello/scim/resources/",
            "summary": "Current Trello SCIM resources reference describing SCIM user and group resource semantics.",
        },
        "trello_organizations_ref": {
            "vendor": "trello",
            "kind": "reference",
            "url": "https://developer.atlassian.com/cloud/trello/rest/api-group-organizations/",
            "summary": "Trello REST reference group for organization and enterprise workspace listing endpoints.",
        },
        "trello_members_ref": {
            "vendor": "trello",
            "kind": "reference",
            "url": "https://developer.atlassian.com/cloud/trello/rest/api-group-members/",
            "summary": "Trello REST reference group for member lookup and enterprise member query endpoints.",
        },
        "youtube_channel_ids_guide": {
            "vendor": "youtube",
            "kind": "guide",
            "url": "https://developers.google.com/youtube/v3/guides/working_with_channel_ids",
            "summary": "YouTube guide describing legacy Data API v2 uploads feeds and the move toward stable channel identifiers and v3 resources.",
        },
        "youtube_channels_guide": {
            "vendor": "youtube",
            "kind": "guide",
            "url": "https://developers.google.com/youtube/v3/guides/implementation/channels",
            "summary": "YouTube v3 channel guide showing how to resolve a channel's uploads playlist through contentDetails.relatedPlaylists.uploads.",
        },
        "youtube_playlistitems_list_ref": {
            "vendor": "youtube",
            "kind": "reference",
            "url": "https://developers.google.com/youtube/v3/docs/playlistItems/list",
            "summary": "YouTube v3 playlistItems.list reference for enumerating items from an uploads playlist.",
        },
        "youtube_comment_changes_v2": {
            "vendor": "youtube",
            "kind": "guide",
            "url": "https://developers.google.com/youtube/articles/changes_to_comments",
            "summary": "Legacy YouTube Data API v2 comment-system article documenting old comment feed behavior and write support caveats.",
        },
        "youtube_comments_guide": {
            "vendor": "youtube",
            "kind": "guide",
            "url": "https://developers.google.com/youtube/v3/guides/implementation/comments",
            "summary": "YouTube v3 comments guide describing top-level comment creation with commentThreads.insert and the lack of comments.markAsSpam support.",
        },
        "youtube_search_ref": {
            "vendor": "youtube",
            "kind": "reference",
            "url": "https://developers.google.com/youtube/v3/docs/search",
            "summary": "YouTube v3 search.list reference for generic video, channel, and playlist search.",
        },
        "youtube_revision_history_2023_related": {
            "vendor": "youtube",
            "kind": "changelog",
            "url": "https://developers.google.com/youtube/v3/revision_history",
            "summary": "YouTube revision history entry announcing and completing removal of search.list relatedToVideoId support in 2023.",
        },
        "youtube_revision_history_2023_mark_spam": {
            "vendor": "youtube",
            "kind": "changelog",
            "url": "https://developers.google.com/youtube/v3/revision_history",
            "summary": "YouTube revision history entry announcing that comments.markAsSpam is unsupported and removed from current API use.",
        },
        "youtube_channels_list_ref": {
            "vendor": "youtube",
            "kind": "reference",
            "url": "https://developers.google.com/youtube/v3/docs/channels/list",
            "summary": "YouTube v3 channels.list reference for channel metadata retrieval and relatedPlaylists access.",
        },
        "youtube_activities_list_ref": {
            "vendor": "youtube",
            "kind": "reference",
            "url": "https://developers.google.com/youtube/v3/docs/activities/list",
            "summary": "YouTube v3 activities.list reference for home activities retrieval.",
        },
        "youtube_revision_history_home_feed": {
            "vendor": "youtube",
            "kind": "changelog",
            "url": "https://developers.google.com/youtube/v3/revision_history",
            "summary": "YouTube revision history entry documenting that home activity retrieval can mix uploads, likes, and recommendations rather than providing a pure recommendations feed.",
        },
        "github_custom_roles_beta": {
            "vendor": "github",
            "kind": "changelog",
            "url": "https://github.blog/changelog/2022-09-07-create-a-custom-organization-role-rest-api-is-now-available-in-public-beta/",
            "summary": "GitHub changelog entry announcing the public beta custom organization role REST APIs under the legacy custom_roles path.",
        },
        "github_custom_roles_ga_breaking": {
            "vendor": "github",
            "kind": "changelog",
            "url": "https://github.blog/changelog/2023-03-07-custom-repository-roles-apis-are-now-generally-available/",
            "summary": "GitHub changelog entry describing the GA path migration from custom_roles to custom-repository-roles.",
        },
        "github_custom_roles_ref": {
            "vendor": "github",
            "kind": "reference",
            "url": "https://docs.github.com/en/rest/orgs/custom-repository-roles",
            "summary": "GitHub REST reference for current custom repository role endpoints.",
        },
        "github_reactions_breaking": {
            "vendor": "github",
            "kind": "changelog",
            "url": "https://github.blog/changelog/2024-05-30-deprecation-of-the-delete-reactions-rest-api-endpoint/",
            "summary": "GitHub changelog entry deprecating the generic delete reaction endpoint in favor of resource-specific delete endpoints.",
        },
        "github_reactions_ref": {
            "vendor": "github",
            "kind": "reference",
            "url": "https://docs.github.com/en/rest/reactions",
            "summary": "GitHub REST reference for current resource-specific reactions endpoints.",
        },
        "github_source_imports_closing_down": {
            "vendor": "github",
            "kind": "changelog",
            "url": "https://github.blog/changelog/2024-03-22-source-imports-api-is-closing-down/",
            "summary": "GitHub changelog entry announcing the closure of the Source Imports REST API.",
        },
        "github_source_imports_ref": {
            "vendor": "github",
            "kind": "reference",
            "url": "https://docs.github.com/en/rest/migrations/source-imports",
            "summary": "GitHub REST reference for the legacy Source Imports endpoints.",
        },
        "github_programmatic_imports_guide": {
            "vendor": "github",
            "kind": "guide",
            "url": "https://docs.github.com/en/migrations/overview/programmatically-importing-repositories",
            "summary": "GitHub guide for programmatically importing repositories after Source Imports API deprecation.",
        },
        "github_repos_ref": {
            "vendor": "github",
            "kind": "reference",
            "url": "https://docs.github.com/en/rest/repos/repos",
            "summary": "GitHub REST reference for repository creation and template-based repository endpoints.",
        },
        "gitlab_rest_deprecations": {
            "vendor": "gitlab",
            "kind": "changelog",
            "url": "https://docs.gitlab.com/api/rest/deprecations/",
            "summary": "GitLab REST API deprecations page covering merge request field deprecations, merge request changes endpoint deprecation, and namespace parameter deprecation in project import APIs.",
        },
        "gitlab_merge_requests_ref": {
            "vendor": "gitlab",
            "kind": "reference",
            "url": "https://docs.gitlab.com/api/merge_requests/",
            "summary": "GitLab Merge Requests API reference including merged_by, merge_user, merge_status, detailed_merge_status, and the deprecated changes endpoint.",
        },
        "gitlab_project_import_export_ref": {
            "vendor": "gitlab",
            "kind": "reference",
            "url": "https://docs.gitlab.com/api/project_import_export/",
            "summary": "GitLab project import and export API reference documenting deprecated namespace and the replacement namespace_id or namespace_path parameters.",
        },
        "slack_oauth_flow_changes": {
            "vendor": "slack",
            "kind": "changelog",
            "url": "https://api.slack.com/changelog/2018-04-oauth-flow-changes-for-workspace-token-preview-apps",
            "summary": "Slack changelog entry announcing oauth.token retirement, oauth.access migration for workspace apps, and the split replacement for apps.permissions.info.",
        },
        "slack_oauth_access_ref": {
            "vendor": "slack",
            "kind": "reference",
            "url": "https://api.slack.com/methods/oauth.access",
            "summary": "Legacy Slack OAuth access exchange method for classic apps.",
        },
        "slack_oauth_v2_access_ref": {
            "vendor": "slack",
            "kind": "reference",
            "url": "https://api.slack.com/methods/oauth.v2.access",
            "summary": "Current Slack OAuth v2 access exchange method for new Slack apps.",
        },
        "slack_users_email_changelog": {
            "vendor": "slack",
            "kind": "changelog",
            "url": "https://api.slack.com/changelog/2016-11-10-addressing-email-addresses",
            "summary": "Slack changelog entry announcing that users:read.email is required for email addresses in users.list and users.info.",
        },
        "slack_users_read_email_scope": {
            "vendor": "slack",
            "kind": "scope",
            "url": "https://api.slack.com/scopes/users%3Aread.email",
            "summary": "Slack scope reference describing users:read.email and its requirement alongside users:read for user email access.",
        },
        "slack_users_list_ref": {
            "vendor": "slack",
            "kind": "reference",
            "url": "https://api.slack.com/methods/users.list",
            "summary": "Slack users.list reference documenting that users:read.email is required for email fields in users.list and users.info.",
        },
        "slack_conversations_scopes_changelog": {
            "vendor": "slack",
            "kind": "changelog",
            "url": "https://api.slack.com/changelog/2018-06-conversations-apis-and-scopes-for-workspace-apps",
            "summary": "Slack changelog entry announcing Conversations API scopes for workspace apps and the simplified conversations:history scope model.",
        },
        "slack_conversations_history_ref": {
            "vendor": "slack",
            "kind": "reference",
            "url": "https://api.slack.com/methods/conversations.history",
            "summary": "Slack conversations.history reference documenting current history retrieval and its required scopes.",
        },
        "slack_conversations_api_guide": {
            "vendor": "slack",
            "kind": "guide",
            "url": "https://api.slack.com/conversations-api",
            "summary": "Slack Conversations API guide describing the unified interface and scope model for channel-like objects.",
        },
        "slack_permissions_methods_index": {
            "vendor": "slack",
            "kind": "reference",
            "url": "https://api.slack.com/methods",
            "summary": "Slack Web API methods index containing the current methods, including apps.permissions.scopes.list and apps.permissions.resources.list.",
        },
    }


def build_tools() -> list[dict[str, object]]:
    return [
        _canonical_tool(
            "trello.integrations.poll_member_privacy",
            "Poll Trello member privacy compliance events for an integration or Power-Up.",
            [
                _canonical_arg("integration_ref", "Opaque Trello integration or Power-Up identifier.", "string"),
                _canonical_arg("since", "Optional RFC3339 lower-bound timestamp for incremental polling.", "string", required=False),
                _canonical_arg("limit", "Optional maximum number of events to return.", "integer", required=False),
            ],
            semantic_tags=["trello", "privacy", "compliance", "poll", "read"],
        ),
        _canonical_tool(
            "trello.enterprises.list_scim_groups",
            "List SCIM groups exposed for a Trello enterprise.",
            [
                _canonical_arg("enterprise_ref", "Trello enterprise identifier.", "string"),
                _canonical_arg("page_size", "Optional page size for the SCIM listing.", "integer", required=False),
            ],
            semantic_tags=["trello", "enterprise", "scim", "groups", "read"],
        ),
        _canonical_tool(
            "trello.enterprises.list_scim_users",
            "List SCIM users exposed for a Trello enterprise.",
            [
                _canonical_arg("enterprise_ref", "Trello enterprise identifier.", "string"),
                _canonical_arg("query", "Optional SCIM filter or user search token.", "string", required=False),
            ],
            semantic_tags=["trello", "enterprise", "scim", "users", "read"],
        ),
        _canonical_tool(
            "trello.enterprises.list_workspaces",
            "List Trello workspaces that belong to an enterprise.",
            [
                _canonical_arg("enterprise_ref", "Trello enterprise identifier.", "string"),
            ],
            semantic_tags=["trello", "enterprise", "workspaces", "list", "read"],
        ),
        _canonical_tool(
            "trello.enterprises.query_members",
            "Query Trello enterprise members by a generic search token.",
            [
                _canonical_arg("enterprise_ref", "Trello enterprise identifier.", "string"),
                _canonical_arg("query", "Search token used to match enterprise members.", "string", required=False),
            ],
            semantic_tags=["trello", "enterprise", "members", "search", "read"],
        ),
        _canonical_tool(
            "youtube.comment_threads.add_top_level_comment",
            "Add a top-level comment to a YouTube video.",
            [
                _canonical_arg("channel_ref", "YouTube channel identifier for the video's channel.", "string"),
                _canonical_arg("video_id", "YouTube video identifier.", "string"),
                _canonical_arg("comment_text", "Top-level comment text to publish.", "string"),
            ],
            semantic_tags=["youtube", "comments", "threads", "create", "write"],
        ),
        _canonical_tool(
            "youtube.playlists.list_upload_videos",
            "List the videos inside a YouTube uploads collection.",
            [
                _canonical_arg("uploads_ref", "Opaque uploads collection identifier.", "string"),
                _canonical_arg("page_size", "Optional maximum number of videos to return.", "integer", required=False),
            ],
            semantic_tags=["youtube", "playlist_items", "uploads", "list", "read"],
        ),
        _canonical_tool(
            "youtube.search.list_related_videos",
            "List videos related to a given YouTube seed video.",
            [
                _canonical_arg("video_id", "YouTube video identifier used as the related-videos seed.", "string"),
                _canonical_arg("page_size", "Optional maximum number of related videos to return.", "integer", required=False),
            ],
            semantic_tags=["youtube", "search", "related", "videos", "read"],
        ),
        _canonical_tool(
            "youtube.comments.mark_spam",
            "Mark a YouTube comment as spam.",
            [
                _canonical_arg("comment_id", "YouTube comment identifier.", "string"),
            ],
            semantic_tags=["youtube", "comments", "moderation", "spam", "write"],
        ),
        _canonical_tool(
            "youtube.channels.get_profile",
            "Get a YouTube channel profile by channel identifier.",
            [
                _canonical_arg("channel_ref", "YouTube channel identifier.", "string"),
            ],
            semantic_tags=["youtube_channels", "channels", "profile", "read"],
        ),
        _canonical_tool(
            "youtube.channels.get_uploads_playlist",
            "Get the uploads playlist identifier for a YouTube channel.",
            [
                _canonical_arg("channel_ref", "YouTube channel identifier.", "string"),
            ],
            semantic_tags=["youtube_channels", "channels", "uploads_playlist", "read"],
        ),
        _canonical_tool(
            "youtube.channels.list_uploaded_videos",
            "List videos uploaded by a YouTube channel.",
            [
                _canonical_arg("channel_ref", "YouTube channel identifier.", "string"),
                _canonical_arg("page_size", "Optional maximum number of uploaded videos to return.", "integer", required=False),
            ],
            semantic_tags=["youtube_channels", "channels", "uploads", "list", "read"],
        ),
        _canonical_tool(
            "youtube.activities.list_recommended_videos",
            "List recommended videos for a YouTube viewer.",
            [
                _canonical_arg("viewer_ref", "Opaque viewer identifier.", "string"),
                _canonical_arg("page_size", "Optional maximum number of recommendations to return.", "integer", required=False),
            ],
            semantic_tags=["youtube_channels", "activities", "recommendations", "read"],
        ),
        _canonical_tool(
            "github.custom_repository_roles.list_roles",
            "List custom repository roles for a GitHub organization.",
            [
                _canonical_arg("org_ref", "GitHub organization login.", "string"),
                _canonical_arg("page_size", "Optional maximum number of roles to return.", "integer", required=False),
            ],
            semantic_tags=["github_rest", "organization_roles", "custom_roles", "list", "read"],
        ),
        _canonical_tool(
            "github.custom_repository_roles.get_role",
            "Get a custom repository role for a GitHub organization by role identifier.",
            [
                _canonical_arg("org_ref", "GitHub organization login.", "string"),
                _canonical_arg("role_id", "GitHub custom repository role identifier.", "integer"),
            ],
            semantic_tags=["github_rest", "organization_roles", "custom_roles", "get", "read"],
        ),
        _canonical_tool(
            "github.reactions.delete_generic_reaction",
            "Delete a GitHub reaction by its generic reaction identifier.",
            [
                _canonical_arg("reaction_id", "GitHub reaction identifier.", "integer"),
            ],
            semantic_tags=["github_rest", "reactions", "delete", "write"],
        ),
        _canonical_tool(
            "github.reactions.delete_issue_reaction",
            "Delete a GitHub issue reaction when issue context is already known.",
            [
                _canonical_arg("owner_ref", "GitHub repository owner.", "string"),
                _canonical_arg("repo_ref", "GitHub repository name.", "string"),
                _canonical_arg("issue_number", "GitHub issue number.", "integer"),
                _canonical_arg("reaction_id", "GitHub reaction identifier.", "integer"),
            ],
            semantic_tags=["github_rest", "reactions", "issues", "delete", "write"],
        ),
        _canonical_tool(
            "github.reactions.delete_issue_comment_reaction",
            "Delete a GitHub issue comment reaction when comment context is already known.",
            [
                _canonical_arg("owner_ref", "GitHub repository owner.", "string"),
                _canonical_arg("repo_ref", "GitHub repository name.", "string"),
                _canonical_arg("comment_id", "GitHub issue comment identifier.", "integer"),
                _canonical_arg("reaction_id", "GitHub reaction identifier.", "integer"),
            ],
            semantic_tags=["github_rest", "reactions", "issue_comments", "delete", "write"],
        ),
        _canonical_tool(
            "github.reactions.delete_commit_comment_reaction",
            "Delete a GitHub commit comment reaction when comment context is already known.",
            [
                _canonical_arg("owner_ref", "GitHub repository owner.", "string"),
                _canonical_arg("repo_ref", "GitHub repository name.", "string"),
                _canonical_arg("comment_id", "GitHub commit comment identifier.", "integer"),
                _canonical_arg("reaction_id", "GitHub reaction identifier.", "integer"),
            ],
            semantic_tags=["github_rest", "reactions", "commit_comments", "delete", "write"],
        ),
        _canonical_tool(
            "github.source_imports.start_import",
            "Import an external Git repository into GitHub.",
            [
                _canonical_arg("owner_ref", "GitHub organization or user that will own the destination repository.", "string"),
                _canonical_arg("repo_ref", "Destination GitHub repository name.", "string"),
                _canonical_arg("source_git_url", "External Git URL to import from.", "string"),
            ],
            semantic_tags=["github_rest", "imports", "repositories", "migrate", "write"],
        ),
        _canonical_tool(
            "github.repositories.create_repository",
            "Create an empty GitHub repository.",
            [
                _canonical_arg("owner_ref", "GitHub organization or user that will own the repository.", "string"),
                _canonical_arg("repo_ref", "Repository name to create.", "string"),
            ],
            semantic_tags=["github_rest", "repositories", "create", "write"],
        ),
        _canonical_tool(
            "github.repositories.create_from_template",
            "Create a GitHub repository from a template repository.",
            [
                _canonical_arg("owner_ref", "GitHub organization or user that will own the repository.", "string"),
                _canonical_arg("repo_ref", "Repository name to create.", "string"),
                _canonical_arg("template_repo_ref", "Template repository reference.", "string"),
            ],
            semantic_tags=["github_rest", "repositories", "template", "create", "write"],
        ),
        _canonical_tool(
            "github.repositories.create_fork",
            "Create a GitHub fork from an existing GitHub repository.",
            [
                _canonical_arg("owner_ref", "GitHub organization or user that will own the fork.", "string"),
                _canonical_arg("source_repo_ref", "Source GitHub repository reference.", "string"),
            ],
            semantic_tags=["github_rest", "repositories", "fork", "create", "write"],
        ),
        _canonical_tool(
            "gitlab.merge_requests.get_merge_actor",
            "Get the merge actor for a GitLab merge request.",
            [
                _canonical_arg("project_ref", "GitLab project path or numeric identifier.", "string"),
                _canonical_arg("merge_request_iid", "GitLab merge request IID.", "integer"),
            ],
            semantic_tags=["gitlab_rest", "merge_requests", "merge_actor", "read"],
        ),
        _canonical_tool(
            "gitlab.merge_requests.get_detailed_merge_status",
            "Get the detailed merge status for a GitLab merge request.",
            [
                _canonical_arg("project_ref", "GitLab project path or numeric identifier.", "string"),
                _canonical_arg("merge_request_iid", "GitLab merge request IID.", "integer"),
            ],
            semantic_tags=["gitlab_rest", "merge_requests", "merge_status", "read"],
        ),
        _canonical_tool(
            "gitlab.merge_requests.get_with_changes",
            "Get a GitLab merge request together with its file changes snapshot.",
            [
                _canonical_arg("project_ref", "GitLab project path or numeric identifier.", "string"),
                _canonical_arg("merge_request_iid", "GitLab merge request IID.", "integer"),
                _canonical_arg("page", "Optional diff page to return.", "integer", required=False),
                _canonical_arg("page_size", "Optional number of diff records to return.", "integer", required=False),
            ],
            semantic_tags=["gitlab_rest", "merge_requests", "changes", "read"],
        ),
        _canonical_tool(
            "gitlab.projects.import_archive",
            "Import a GitLab project archive into a target namespace.",
            [
                _canonical_arg("archive_ref", "Project archive file identifier.", "string"),
                _canonical_arg("project_path", "Path of the new GitLab project.", "string"),
                _canonical_arg("target_namespace_ref", "GitLab namespace identifier or path.", "string"),
            ],
            semantic_tags=["gitlab_rest", "projects", "import", "write"],
        ),
        _canonical_tool(
            "slack.oauth.exchange_install_code",
            "Exchange a Slack installation authorization code for an access token.",
            [
                _canonical_arg("auth_code", "Temporary Slack OAuth authorization code.", "string"),
                _canonical_arg("redirect_uri", "Optional redirect URI that must match the original authorization step.", "string", required=False),
            ],
            semantic_tags=["slack_auth", "oauth", "exchange_code", "write"],
        ),
        _canonical_tool(
            "slack.users.get_user_email",
            "Get the email address for a Slack user.",
            [
                _canonical_arg("user_ref", "Slack user identifier.", "string"),
            ],
            semantic_tags=["slack_auth", "users", "email", "read"],
        ),
        _canonical_tool(
            "slack.conversations.get_history",
            "Get message history for a Slack conversation.",
            [
                _canonical_arg("conversation_ref", "Slack conversation identifier.", "string"),
                _canonical_arg("page_size", "Optional maximum number of messages to return.", "integer", required=False),
            ],
            semantic_tags=["slack_auth", "conversations", "history", "read"],
        ),
        _canonical_tool(
            "slack.apps.get_granted_permissions",
            "Get the currently granted scopes and resources for the installed Slack app.",
            [],
            semantic_tags=["slack_auth", "permissions", "inventory", "read"],
        ),
    ]


def build_cases() -> list[dict[str, object]]:
    return [
        _case(
            case_id="trello_poll_member_privacy_since",
            request="Poll Trello member privacy events for integration integ_powerup since 2026-02-01T00:00:00Z.",
            tool_ids=[
                "trello.integrations.poll_member_privacy",
                "trello.enterprises.list_workspaces",
                "trello.enterprises.query_members",
            ],
            slot_values={
                "integration_ref": "integ_powerup",
                "since": "2026-02-01T00:00:00Z",
            },
            action=_action(
                "trello.integrations.poll_member_privacy",
                integration_ref="integ_powerup",
                since="2026-02-01T00:00:00Z",
            ),
            family_tag="trello",
            notes="sources=trello_2025_08_member_privacy_deprecation,trello_gdpr_guide,trello_applications_ref,trello_plugins_ref;pair=application_compliance_to_plugin_compliance",
        ),
        _case(
            case_id="trello_poll_member_privacy_window",
            request="Fetch the latest 50 Trello member privacy events for integration integ_powerup.",
            tool_ids=[
                "trello.integrations.poll_member_privacy",
                "trello.enterprises.list_workspaces",
                "trello.enterprises.query_members",
            ],
            slot_values={
                "integration_ref": "integ_powerup",
                "limit": 50,
            },
            action=_action(
                "trello.integrations.poll_member_privacy",
                integration_ref="integ_powerup",
                limit=50,
            ),
            family_tag="trello",
            notes="sources=trello_2025_08_member_privacy_deprecation,trello_gdpr_guide,trello_applications_ref,trello_plugins_ref;pair=application_compliance_to_plugin_compliance",
        ),
        _case(
            case_id="trello_list_scim_groups",
            request="List SCIM groups for Trello enterprise ent_roadmap.",
            tool_ids=[
                "trello.enterprises.list_scim_groups",
                "trello.enterprises.list_workspaces",
                "trello.enterprises.query_members",
            ],
            slot_values={"enterprise_ref": "ent_roadmap"},
            action=_action("trello.enterprises.list_scim_groups", enterprise_ref="ent_roadmap"),
            family_tag="trello",
            notes="sources=trello_2025_09_scim_deprecation,trello_scim_routes_ref,trello_scim_resources_ref,trello_organizations_ref;pair=scim_groups_to_workspace_listing",
        ),
        _case(
            case_id="trello_list_scim_users",
            request="List SCIM users for Trello enterprise ent_roadmap matching alice@example.com.",
            tool_ids=[
                "trello.enterprises.list_scim_users",
                "trello.enterprises.query_members",
                "trello.enterprises.list_workspaces",
            ],
            slot_values={
                "enterprise_ref": "ent_roadmap",
                "query": "alice@example.com",
            },
            action=_action(
                "trello.enterprises.list_scim_users",
                enterprise_ref="ent_roadmap",
                query="alice@example.com",
            ),
            family_tag="trello",
            notes="sources=trello_2025_09_scim_deprecation,trello_scim_routes_ref,trello_scim_resources_ref,trello_members_ref;pair=scim_users_to_member_query",
        ),
        _case(
            case_id="youtube_add_top_level_comment",
            request="Add the top-level comment 'Ship the draft today.' to YouTube video vid_launch on channel chan_devrel.",
            tool_ids=[
                "youtube.comment_threads.add_top_level_comment",
                "youtube.playlists.list_upload_videos",
                "youtube.comments.mark_spam",
            ],
            slot_values={
                "channel_ref": "chan_devrel",
                "video_id": "vid_launch",
                "comment_text": "Ship the draft today.",
            },
            action=_action(
                "youtube.comment_threads.add_top_level_comment",
                channel_ref="chan_devrel",
                video_id="vid_launch",
                comment_text="Ship the draft today.",
            ),
            family_tag="youtube",
            notes="sources=youtube_comment_changes_v2,youtube_comments_guide;pair=legacy_comment_feed_to_commentThreads_insert",
        ),
        _case(
            case_id="youtube_list_upload_videos",
            request="List the latest uploaded videos from uploads collection UPL_devrel with page size 25.",
            tool_ids=[
                "youtube.playlists.list_upload_videos",
                "youtube.comment_threads.add_top_level_comment",
                "youtube.search.list_related_videos",
            ],
            slot_values={
                "uploads_ref": "UPL_devrel",
                "page_size": 25,
            },
            action=_action(
                "youtube.playlists.list_upload_videos",
                uploads_ref="UPL_devrel",
                page_size=25,
            ),
            family_tag="youtube",
            notes="sources=youtube_channel_ids_guide,youtube_channels_guide,youtube_playlistitems_list_ref;pair=uploads_feed_to_playlistitems_list",
        ),
        _case(
            case_id="youtube_search_related_videos",
            request="List videos related to YouTube video vid_launch.",
            tool_ids=[
                "youtube.search.list_related_videos",
                "youtube.playlists.list_upload_videos",
                "youtube.comment_threads.add_top_level_comment",
            ],
            slot_values={
                "video_id": "vid_launch",
            },
            action=_action(
                "youtube.search.list_related_videos",
                video_id="vid_launch",
            ),
            family_tag="youtube",
            notes="sources=youtube_revision_history_2023_related,youtube_search_ref;pair=relatedToVideoId_removed",
        ),
        _case(
            case_id="youtube_mark_comment_spam",
            request="Mark YouTube comment cmt_spam_42 as spam.",
            tool_ids=[
                "youtube.comments.mark_spam",
                "youtube.comment_threads.add_top_level_comment",
                "youtube.search.list_related_videos",
            ],
            slot_values={
                "comment_id": "cmt_spam_42",
            },
            action=_action(
                "youtube.comments.mark_spam",
                comment_id="cmt_spam_42",
            ),
            family_tag="youtube",
            notes="sources=youtube_revision_history_2023_mark_spam,youtube_comments_guide;pair=comments_markAsSpam_removed",
        ),
        _case(
            case_id="youtube_channels_get_profile",
            request="Get the YouTube channel profile for channel chan_devrel.",
            tool_ids=[
                "youtube.channels.get_profile",
                "youtube.channels.get_uploads_playlist",
                "youtube.channels.list_uploaded_videos",
            ],
            slot_values={"channel_ref": "chan_devrel"},
            action=_action("youtube.channels.get_profile", channel_ref="chan_devrel"),
            family_tag="youtube_channels",
            notes="sources=youtube_channel_ids_guide,youtube_channels_list_ref;pair=legacy_channel_profile_to_channels_list",
        ),
        _case(
            case_id="youtube_channels_get_uploads_playlist",
            request="Get the uploads playlist for YouTube channel chan_devrel.",
            tool_ids=[
                "youtube.channels.get_uploads_playlist",
                "youtube.channels.get_profile",
                "youtube.channels.list_uploaded_videos",
            ],
            slot_values={"channel_ref": "chan_devrel"},
            action=_action("youtube.channels.get_uploads_playlist", channel_ref="chan_devrel"),
            family_tag="youtube_channels",
            notes="sources=youtube_channel_ids_guide,youtube_channels_guide,youtube_channels_list_ref;pair=legacy_uploads_feed_link_to_related_playlists",
        ),
        _case(
            case_id="youtube_channels_list_uploaded_videos",
            request="List the latest uploaded videos for YouTube channel chan_devrel with page size 25.",
            tool_ids=[
                "youtube.channels.list_uploaded_videos",
                "youtube.channels.get_uploads_playlist",
                "youtube.channels.get_profile",
            ],
            slot_values={
                "channel_ref": "chan_devrel",
                "page_size": 25,
            },
            action=_action(
                "youtube.channels.list_uploaded_videos",
                channel_ref="chan_devrel",
                page_size=25,
            ),
            family_tag="youtube_channels",
            notes="sources=youtube_channel_ids_guide,youtube_channels_guide,youtube_playlistitems_list_ref;pair=uploads_feed_to_playlist_lookup_split",
        ),
        _case(
            case_id="youtube_activities_list_recommended_videos",
            request="List 10 recommended YouTube videos for viewer viewer_self.",
            tool_ids=[
                "youtube.activities.list_recommended_videos",
                "youtube.channels.list_uploaded_videos",
                "youtube.channels.get_profile",
            ],
            slot_values={
                "viewer_ref": "viewer_self",
                "page_size": 10,
            },
            action=_action(
                "youtube.activities.list_recommended_videos",
                viewer_ref="viewer_self",
                page_size=10,
            ),
            family_tag="youtube_channels",
            notes="sources=youtube_revision_history_home_feed,youtube_activities_list_ref;pair=home_feed_is_broader_than_recommendations",
        ),
        _case(
            case_id="github_list_custom_repository_roles",
            request="List custom repository roles for GitHub organization octo-sec with page size 50.",
            tool_ids=[
                "github.custom_repository_roles.list_roles",
                "github.custom_repository_roles.get_role",
                "github.repositories.create_repository",
            ],
            slot_values={
                "org_ref": "octo-sec",
                "page_size": 50,
            },
            action=_action(
                "github.custom_repository_roles.list_roles",
                org_ref="octo-sec",
                page_size=50,
            ),
            family_tag="github_rest",
            notes="sources=github_custom_roles_beta,github_custom_roles_ga_breaking,github_custom_roles_ref;pair=custom_roles_path_migration",
        ),
        _case(
            case_id="github_get_custom_repository_role",
            request="Get GitHub custom repository role 42 for organization octo-sec.",
            tool_ids=[
                "github.custom_repository_roles.get_role",
                "github.custom_repository_roles.list_roles",
                "github.repositories.create_repository",
            ],
            slot_values={
                "org_ref": "octo-sec",
                "role_id": 42,
            },
            action=_action(
                "github.custom_repository_roles.get_role",
                org_ref="octo-sec",
                role_id=42,
            ),
            family_tag="github_rest",
            notes="sources=github_custom_roles_beta,github_custom_roles_ga_breaking,github_custom_roles_ref;pair=custom_role_item_path_migration",
        ),
        _case(
            case_id="github_delete_generic_reaction",
            request="Delete GitHub reaction 4242 from repository octo-sec/toolshift.",
            tool_ids=[
                "github.reactions.delete_generic_reaction",
                "github.reactions.delete_issue_reaction",
                "github.reactions.delete_issue_comment_reaction",
                "github.reactions.delete_commit_comment_reaction",
            ],
            slot_values={
                "owner_ref": "octo-sec",
                "repo_ref": "toolshift",
                "reaction_id": 4242,
            },
            action=_action(
                "github.reactions.delete_generic_reaction",
                reaction_id=4242,
            ),
            family_tag="github_rest",
            notes="sources=github_reactions_breaking,github_reactions_ref;pair=generic_reaction_delete_to_resource_context_split",
        ),
        _case(
            case_id="github_import_external_repository",
            request="Import the external Git repository https://git.example.com/roadmap.git into GitHub repository octo-sec/roadmap-mirror.",
            tool_ids=[
                "github.source_imports.start_import",
                "github.repositories.create_repository",
                "github.repositories.create_from_template",
                "github.repositories.create_fork",
            ],
            slot_values={
                "owner_ref": "octo-sec",
                "repo_ref": "roadmap-mirror",
                "source_git_url": "https://git.example.com/roadmap.git",
            },
            action=_action(
                "github.source_imports.start_import",
                owner_ref="octo-sec",
                repo_ref="roadmap-mirror",
                source_git_url="https://git.example.com/roadmap.git",
            ),
            family_tag="github_rest",
            notes="sources=github_source_imports_closing_down,github_source_imports_ref,github_programmatic_imports_guide,github_repos_ref;pair=source_import_api_to_out_of_band_replacement",
        ),
        _case(
            case_id="gitlab_get_merge_request_merge_actor",
            request="Get the merge actor for GitLab merge request 42 in project platform/toolshift.",
            tool_ids=[
                "gitlab.merge_requests.get_merge_actor",
                "gitlab.merge_requests.get_detailed_merge_status",
                "gitlab.merge_requests.get_with_changes",
            ],
            slot_values={
                "project_ref": "platform/toolshift",
                "merge_request_iid": 42,
            },
            action=_action(
                "gitlab.merge_requests.get_merge_actor",
                project_ref="platform/toolshift",
                merge_request_iid=42,
            ),
            family_tag="gitlab_rest",
            notes="sources=gitlab_rest_deprecations,gitlab_merge_requests_ref;pair=merged_by_to_merge_user",
        ),
        _case(
            case_id="gitlab_get_merge_request_detailed_status",
            request="Get the detailed merge status for GitLab merge request 42 in project platform/toolshift.",
            tool_ids=[
                "gitlab.merge_requests.get_detailed_merge_status",
                "gitlab.merge_requests.get_merge_actor",
                "gitlab.merge_requests.get_with_changes",
            ],
            slot_values={
                "project_ref": "platform/toolshift",
                "merge_request_iid": 42,
            },
            action=_action(
                "gitlab.merge_requests.get_detailed_merge_status",
                project_ref="platform/toolshift",
                merge_request_iid=42,
            ),
            family_tag="gitlab_rest",
            notes="sources=gitlab_rest_deprecations,gitlab_merge_requests_ref;pair=merge_status_to_detailed_merge_status",
        ),
        _case(
            case_id="gitlab_get_merge_request_with_changes",
            request="Get GitLab merge request 42 in project platform/toolshift together with its file changes.",
            tool_ids=[
                "gitlab.merge_requests.get_with_changes",
                "gitlab.merge_requests.get_merge_actor",
                "gitlab.merge_requests.get_detailed_merge_status",
            ],
            slot_values={
                "project_ref": "platform/toolshift",
                "merge_request_iid": 42,
            },
            action=_action(
                "gitlab.merge_requests.get_with_changes",
                project_ref="platform/toolshift",
                merge_request_iid=42,
            ),
            family_tag="gitlab_rest",
            notes="sources=gitlab_rest_deprecations,gitlab_merge_requests_ref;pair=single_merge_request_changes_to_diff_listing",
        ),
        _case(
            case_id="gitlab_import_project_archive_ambiguous_namespace",
            request="Import GitLab project archive roadmap-export.tar.gz into namespace 1234 as project roadmap-archive.",
            tool_ids=[
                "gitlab.projects.import_archive",
                "gitlab.merge_requests.get_merge_actor",
                "gitlab.merge_requests.get_with_changes",
            ],
            slot_values={
                "archive_ref": "roadmap-export.tar.gz",
                "project_path": "roadmap-archive",
                "target_namespace_ref": "1234",
            },
            action=_action(
                "gitlab.projects.import_archive",
                archive_ref="roadmap-export.tar.gz",
                project_path="roadmap-archive",
                target_namespace_ref="1234",
            ),
            family_tag="gitlab_rest",
            notes="sources=gitlab_rest_deprecations,gitlab_project_import_export_ref;pair=namespace_to_namespace_id_or_path",
        ),
        _case(
            case_id="slack_exchange_install_code",
            request="Exchange Slack installation code code-123 for an access token using redirect URI https://toolshift.example.com/slack/callback.",
            tool_ids=[
                "slack.oauth.exchange_install_code",
                "slack.users.get_user_email",
                "slack.conversations.get_history",
            ],
            slot_values={
                "auth_code": "code-123",
                "redirect_uri": "https://toolshift.example.com/slack/callback",
            },
            action=_action(
                "slack.oauth.exchange_install_code",
                auth_code="code-123",
                redirect_uri="https://toolshift.example.com/slack/callback",
            ),
            family_tag="slack_auth",
            notes="sources=slack_oauth_flow_changes,slack_oauth_access_ref,slack_oauth_v2_access_ref;pair=oauth_access_to_oauth_v2_access",
        ),
        _case(
            case_id="slack_get_user_email",
            request="Get the email address for Slack user U123.",
            tool_ids=[
                "slack.users.get_user_email",
                "slack.conversations.get_history",
                "slack.oauth.exchange_install_code",
            ],
            slot_values={"user_ref": "U123"},
            action=_action(
                "slack.users.get_user_email",
                user_ref="U123",
            ),
            family_tag="slack_auth",
            notes="sources=slack_users_email_changelog,slack_users_read_email_scope,slack_users_list_ref;pair=users_read_to_users_read_email",
        ),
        _case(
            case_id="slack_get_conversation_history",
            request="Get the latest 50 messages from Slack conversation C123.",
            tool_ids=[
                "slack.conversations.get_history",
                "slack.users.get_user_email",
                "slack.apps.get_granted_permissions",
            ],
            slot_values={
                "conversation_ref": "C123",
                "page_size": 50,
            },
            action=_action(
                "slack.conversations.get_history",
                conversation_ref="C123",
                page_size=50,
            ),
            family_tag="slack_auth",
            notes="sources=slack_conversations_scopes_changelog,slack_conversations_history_ref,slack_conversations_api_guide;pair=channels_history_to_conversations_history",
        ),
        _case(
            case_id="slack_get_granted_permissions",
            request="Get the granted scopes and resources for the current Slack app installation.",
            tool_ids=[
                "slack.apps.get_granted_permissions",
                "slack.oauth.exchange_install_code",
                "slack.users.get_user_email",
            ],
            slot_values={},
            action=_action("slack.apps.get_granted_permissions"),
            family_tag="slack_auth",
            notes="sources=slack_oauth_flow_changes,slack_permissions_methods_index;pair=apps_permissions_info_to_scope_and_resource_lists",
        ),
    ]


def build_views() -> list[dict[str, object]]:
    trello_member_privacy_legacy = _rendered_tool(
        "trello.integrations.poll_member_privacy",
        "applications.get_compliance_member_privacy",
        "Poll privacy compliance events for a Trello application key using the legacy application-scoped memberPrivacy route.",
        [
            _rendered_arg("key", "integration_ref", "Legacy Trello application key.", "string", position=0),
            _rendered_arg("since", "since", "Optional lower-bound timestamp for incremental polling.", "string", required=False, position=1),
            _rendered_arg("limit", "limit", "Optional maximum number of events to return.", "integer", required=False, position=2),
        ],
    )
    trello_member_privacy_current = _rendered_tool(
        "trello.integrations.poll_member_privacy",
        "plugins.get_member_privacy_compliance",
        "Poll privacy compliance events for a Trello Power-Up plugin through the supported plugin memberPrivacy route.",
        [
            _rendered_arg("id", "integration_ref", "Opaque Trello plugin identifier.", "string", position=0),
            _rendered_arg("since", "since", "Optional lower-bound timestamp for incremental polling.", "string", required=False, position=1),
            _rendered_arg("limit", "limit", "Optional maximum number of events to return.", "integer", required=False, position=2),
        ],
    )
    trello_scim_groups_legacy = _rendered_tool(
        "trello.enterprises.list_scim_groups",
        "scim.groups.list",
        "List SCIM groups for a Trello enterprise through the legacy /scim/v2/Groups route.",
        [
            _rendered_arg("enterpriseId", "enterprise_ref", "Trello enterprise identifier.", "string", position=0),
            _rendered_arg("count", "page_size", "Optional SCIM page size.", "integer", required=False, position=1),
        ],
    )
    trello_scim_groups_current = _rendered_tool(
        "trello.enterprises.list_scim_groups",
        "enterprises.get_organizations",
        "List Trello workspaces in an enterprise. The legacy SCIM Groups endpoints are deprecated; these organization endpoints are related but are not a drop-in replacement for listing SCIM groups.",
        [
            _rendered_arg("id", "enterprise_ref", "Trello enterprise identifier.", "string", position=0),
        ],
    )
    trello_scim_users_legacy = _rendered_tool(
        "trello.enterprises.list_scim_users",
        "scim.users.list",
        "List SCIM users for a Trello enterprise through the legacy /scim/v2/Users route.",
        [
            _rendered_arg("enterpriseId", "enterprise_ref", "Trello enterprise identifier.", "string", position=0),
            _rendered_arg("filter", "query", "Optional SCIM filter used to narrow the listing.", "string", required=False, position=1),
        ],
    )
    trello_scim_users_current = _rendered_tool(
        "trello.enterprises.list_scim_users",
        "enterprises.query_members",
        "Query enterprise members by a generic search token. The legacy SCIM Users endpoints are deprecated; enterprise member queries are related but do not preserve the old SCIM user-list contract as a drop-in replacement.",
        [
            _rendered_arg("id", "enterprise_ref", "Trello enterprise identifier.", "string", position=0),
            _rendered_arg("query", "query", "Optional search token for matching enterprise members.", "string", required=False, position=1),
        ],
    )
    trello_workspaces_current = _rendered_tool(
        "trello.enterprises.list_workspaces",
        "enterprises.get_organizations",
        "Get the workspaces that belong to a Trello enterprise.",
        [
            _rendered_arg("id", "enterprise_ref", "Trello enterprise identifier.", "string", position=0),
        ],
    )
    trello_members_current = _rendered_tool(
        "trello.enterprises.query_members",
        "enterprises.query_members",
        "Query members that belong to a Trello enterprise.",
        [
            _rendered_arg("id", "enterprise_ref", "Trello enterprise identifier.", "string", position=0),
            _rendered_arg("query", "query", "Optional search token for matching members.", "string", required=False, position=1),
        ],
    )
    youtube_comment_legacy = _rendered_tool(
        "youtube.comment_threads.add_top_level_comment",
        "comments.insert",
        "Insert a new top-level comment into a legacy YouTube video comments feed.",
        [
            _rendered_arg("channelId", "channel_ref", "YouTube channel identifier for the video's channel.", "string", position=0),
            _rendered_arg("videoId", "video_id", "YouTube video identifier.", "string", position=1),
            _rendered_arg("text", "comment_text", "Top-level comment text.", "string", position=2),
        ],
    )
    youtube_comment_current = _rendered_tool(
        "youtube.comment_threads.add_top_level_comment",
        "commentThreads.insert",
        "Add a top-level comment to a video using commentThreads.insert.",
        [
            _rendered_arg("snippet.channelId", "channel_ref", "YouTube channel identifier for the video's channel.", "string", position=0),
            _rendered_arg("snippet.videoId", "video_id", "YouTube video identifier.", "string", position=1),
            _rendered_arg(
                "snippet.topLevelComment.snippet.textOriginal",
                "comment_text",
                "Top-level comment text to publish.",
                "string",
                position=2,
            ),
        ],
    )
    youtube_uploads_legacy = _rendered_tool(
        "youtube.playlists.list_upload_videos",
        "users.uploads.feed.list",
        "List videos from a legacy YouTube uploads feed.",
        [
            _rendered_arg("user", "uploads_ref", "Legacy uploads collection or user feed reference.", "string", position=0),
            _rendered_arg("max-results", "page_size", "Optional maximum number of videos to return.", "integer", required=False, position=1),
        ],
    )
    youtube_uploads_current = _rendered_tool(
        "youtube.playlists.list_upload_videos",
        "playlistItems.list",
        "List videos from a channel's uploads playlist using playlistItems.list.",
        [
            _rendered_arg("playlistId", "uploads_ref", "Uploads playlist identifier.", "string", position=0),
            _rendered_arg("maxResults", "page_size", "Optional maximum number of videos to return.", "integer", required=False, position=1),
        ],
    )
    youtube_related_legacy = _rendered_tool(
        "youtube.search.list_related_videos",
        "search.list",
        "List videos related to a seed video by setting relatedToVideoId.",
        [
            _rendered_arg("relatedToVideoId", "video_id", "Seed video identifier used to retrieve related videos.", "string", position=0),
            _rendered_arg("maxResults", "page_size", "Optional maximum number of related videos to return.", "integer", required=False, position=1),
        ],
    )
    youtube_related_current = _rendered_tool(
        "youtube.search.list_related_videos",
        "search.list",
        "The relatedToVideoId parameter is no longer supported. Generic search results remain available, but the API no longer exposes this old related-videos retrieval contract as a drop-in operation.",
        [
            _rendered_arg("maxResults", "page_size", "Optional maximum number of search results to return.", "integer", required=False, position=0),
        ],
    )
    youtube_mark_spam_legacy = _rendered_tool(
        "youtube.comments.mark_spam",
        "comments.markAsSpam",
        "Mark one or more YouTube comments as spam.",
        [
            _rendered_arg("id", "comment_id", "YouTube comment identifier to mark as spam.", "string", position=0),
        ],
    )
    youtube_mark_spam_current = _rendered_tool(
        "youtube.comments.mark_spam",
        "comments.markAsSpam",
        "The comments.markAsSpam method is no longer supported in the YouTube Data API.",
        [
            _rendered_arg("id", "comment_id", "YouTube comment identifier that would have been marked as spam.", "string", position=0),
        ],
        status="deprecated",
    )
    youtube_channel_profile_legacy = _rendered_tool(
        "youtube.channels.get_profile",
        "channels.profile.get",
        "Get a legacy YouTube channel profile by channel identifier.",
        [
            _rendered_arg("id", "channel_ref", "YouTube channel identifier.", "string", position=0),
        ],
    )
    youtube_channel_profile_current = _rendered_tool(
        "youtube.channels.get_profile",
        "channels.list",
        "Get a YouTube channel resource by identifier using channels.list.",
        [
            _rendered_arg("id", "channel_ref", "YouTube channel identifier.", "string", position=0),
        ],
    )
    youtube_uploads_playlist_legacy = _rendered_tool(
        "youtube.channels.get_uploads_playlist",
        "channels.profile.uploads_feed",
        "Retrieve the uploads feed link for a legacy YouTube channel profile.",
        [
            _rendered_arg("id", "channel_ref", "YouTube channel identifier.", "string", position=0),
        ],
    )
    youtube_uploads_playlist_current = _rendered_tool(
        "youtube.channels.get_uploads_playlist",
        "channels.list",
        "Retrieve a channel's uploads playlist through contentDetails.relatedPlaylists.uploads in channels.list.",
        [
            _rendered_arg("id", "channel_ref", "YouTube channel identifier.", "string", position=0),
        ],
    )
    youtube_channel_uploads_legacy = _rendered_tool(
        "youtube.channels.list_uploaded_videos",
        "channels.uploads.feed.list",
        "List a channel's uploaded videos directly from the legacy uploads feed.",
        [
            _rendered_arg("channelId", "channel_ref", "YouTube channel identifier.", "string", position=0),
            _rendered_arg("max-results", "page_size", "Optional maximum number of uploaded videos to return.", "integer", required=False, position=1),
        ],
    )
    youtube_channel_uploads_current = _rendered_tool(
        "youtube.channels.list_uploaded_videos",
        "playlistItems.list",
        "List uploaded videos from the channel's uploads playlist. This now requires a separate channels.list lookup to resolve relatedPlaylists.uploads, so it is not a drop-in replacement for the old single-step channel uploads feed.",
        [
            _rendered_arg("playlistId", "channel_ref", "Uploads playlist identifier resolved from the channel profile.", "string", position=0),
            _rendered_arg("maxResults", "page_size", "Optional maximum number of uploaded videos to return.", "integer", required=False, position=1),
        ],
    )
    youtube_home_recommendations_legacy = _rendered_tool(
        "youtube.activities.list_recommended_videos",
        "activities.home.recommendations",
        "List recommended videos for the current YouTube viewer through the legacy home recommendations feed.",
        [
            _rendered_arg("viewer", "viewer_ref", "Opaque viewer identifier.", "string", position=0),
            _rendered_arg("max-results", "page_size", "Optional maximum number of recommendations to return.", "integer", required=False, position=1),
        ],
    )
    youtube_home_activities_current = _rendered_tool(
        "youtube.activities.list_recommended_videos",
        "activities.list",
        "List home activities for the current viewer. The home feed can mix uploads, likes, and recommendations, so it no longer recovers the old recommendations-only contract as a drop-in operation.",
        [
            _rendered_arg("home", "viewer_ref", "Boolean-style home feed selector for the authorized viewer.", "string", position=0),
            _rendered_arg("maxResults", "page_size", "Optional maximum number of activities to return.", "integer", required=False, position=1),
        ],
    )
    github_custom_roles_list_legacy = _rendered_tool(
        "github.custom_repository_roles.list_roles",
        "orgs.custom_roles.list",
        "List custom repository roles for a GitHub organization using the legacy public-beta custom_roles path.",
        [
            _rendered_arg("org", "org_ref", "GitHub organization login.", "string", position=0),
            _rendered_arg("per_page", "page_size", "Optional maximum number of roles to return.", "integer", required=False, position=1),
        ],
    )
    github_custom_roles_list_current = _rendered_tool(
        "github.custom_repository_roles.list_roles",
        "orgs.custom-repository-roles.list",
        "List custom repository roles for a GitHub organization using the GA custom-repository-roles path.",
        [
            _rendered_arg("org", "org_ref", "GitHub organization login.", "string", position=0),
            _rendered_arg("per_page", "page_size", "Optional maximum number of roles to return.", "integer", required=False, position=1),
        ],
    )
    github_custom_role_get_legacy = _rendered_tool(
        "github.custom_repository_roles.get_role",
        "orgs.custom_roles.get",
        "Get a GitHub custom repository role using the legacy public-beta custom_roles path.",
        [
            _rendered_arg("org", "org_ref", "GitHub organization login.", "string", position=0),
            _rendered_arg("role_id", "role_id", "GitHub custom repository role identifier.", "integer", position=1),
        ],
    )
    github_custom_role_get_current = _rendered_tool(
        "github.custom_repository_roles.get_role",
        "orgs.custom-repository-roles.get",
        "Get a GitHub custom repository role using the GA custom-repository-roles path.",
        [
            _rendered_arg("org", "org_ref", "GitHub organization login.", "string", position=0),
            _rendered_arg("role_id", "role_id", "GitHub custom repository role identifier.", "integer", position=1),
        ],
    )
    github_generic_reaction_delete_legacy = _rendered_tool(
        "github.reactions.delete_generic_reaction",
        "reactions.delete",
        "Delete a GitHub reaction directly by reaction identifier using the legacy generic delete endpoint.",
        [
            _rendered_arg("reaction_id", "reaction_id", "GitHub reaction identifier.", "integer", position=0),
        ],
    )
    github_issue_reaction_delete_current = _rendered_tool(
        "github.reactions.delete_issue_reaction",
        "issues.reactions.delete",
        "Delete a GitHub issue reaction. The legacy generic delete endpoint is gone; current delete operations require issue context and are not a drop-in replacement when only a reaction identifier is known.",
        [
            _rendered_arg("owner", "owner_ref", "GitHub repository owner.", "string", position=0),
            _rendered_arg("repo", "repo_ref", "GitHub repository name.", "string", position=1),
            _rendered_arg("issue_number", "issue_number", "GitHub issue number.", "integer", position=2),
            _rendered_arg("reaction_id", "reaction_id", "GitHub reaction identifier.", "integer", position=3),
        ],
    )
    github_issue_comment_reaction_delete_current = _rendered_tool(
        "github.reactions.delete_issue_comment_reaction",
        "issue_comments.reactions.delete",
        "Delete a GitHub issue comment reaction. Current reaction delete endpoints require resource-specific comment context and are not a drop-in replacement for the legacy generic reaction delete route.",
        [
            _rendered_arg("owner", "owner_ref", "GitHub repository owner.", "string", position=0),
            _rendered_arg("repo", "repo_ref", "GitHub repository name.", "string", position=1),
            _rendered_arg("comment_id", "comment_id", "GitHub issue comment identifier.", "integer", position=2),
            _rendered_arg("reaction_id", "reaction_id", "GitHub reaction identifier.", "integer", position=3),
        ],
    )
    github_commit_comment_reaction_delete_current = _rendered_tool(
        "github.reactions.delete_commit_comment_reaction",
        "commit_comments.reactions.delete",
        "Delete a GitHub commit comment reaction. Current reaction delete endpoints require commit-comment context and are not a drop-in replacement for deleting by reaction identifier alone.",
        [
            _rendered_arg("owner", "owner_ref", "GitHub repository owner.", "string", position=0),
            _rendered_arg("repo", "repo_ref", "GitHub repository name.", "string", position=1),
            _rendered_arg("comment_id", "comment_id", "GitHub commit comment identifier.", "integer", position=2),
            _rendered_arg("reaction_id", "reaction_id", "GitHub reaction identifier.", "integer", position=3),
        ],
    )
    github_source_import_legacy = _rendered_tool(
        "github.source_imports.start_import",
        "repos.source_import.start",
        "Import an external Git repository into GitHub using the legacy Source Imports REST API.",
        [
            _rendered_arg("owner", "owner_ref", "GitHub organization or user that will own the repository.", "string", position=0),
            _rendered_arg("repo", "repo_ref", "Destination GitHub repository name.", "string", position=1),
            _rendered_arg("vcs_url", "source_git_url", "External Git URL to import from.", "string", position=2),
        ],
    )
    github_create_repo_current = _rendered_tool(
        "github.repositories.create_repository",
        "repos.create_in_org",
        "Create an empty GitHub repository. Source Imports is closing down; generic repository creation is related but does not recover the old import-from-URL contract as a drop-in replacement.",
        [
            _rendered_arg("org", "owner_ref", "GitHub organization login.", "string", position=0),
            _rendered_arg("name", "repo_ref", "Repository name to create.", "string", position=1),
        ],
    )
    github_create_from_template_current = _rendered_tool(
        "github.repositories.create_from_template",
        "repos.create_using_template",
        "Create a repository from a GitHub template. This is a current repository bootstrap route, but it is not a drop-in replacement for importing an arbitrary external Git URL.",
        [
            _rendered_arg("owner", "owner_ref", "GitHub organization login.", "string", position=0),
            _rendered_arg("name", "repo_ref", "Repository name to create.", "string", position=1),
            _rendered_arg("template_repo", "template_repo_ref", "Template repository reference.", "string", position=2),
        ],
    )
    github_create_fork_current = _rendered_tool(
        "github.repositories.create_fork",
        "repos.create_fork",
        "Fork an existing GitHub repository. Forking is related repository bootstrap functionality, but it is not a drop-in replacement for importing from an arbitrary external Git URL.",
        [
            _rendered_arg("org", "owner_ref", "GitHub organization login.", "string", position=0),
            _rendered_arg("source_repo", "source_repo_ref", "Source GitHub repository reference.", "string", position=1),
        ],
    )
    gitlab_merge_actor_legacy = _rendered_tool(
        "gitlab.merge_requests.get_merge_actor",
        "merge_requests.get",
        "Retrieve a GitLab merge request and read the legacy merged_by field to identify the merge actor.",
        [
            _rendered_arg("id", "project_ref", "GitLab project path or numeric identifier.", "string", position=0),
            _rendered_arg("merge_request_iid", "merge_request_iid", "GitLab merge request IID.", "integer", position=1),
        ],
    )
    gitlab_merge_actor_current = _rendered_tool(
        "gitlab.merge_requests.get_merge_actor",
        "merge_requests.get",
        "Retrieve a GitLab merge request and read the current merge_user field to identify the merge actor.",
        [
            _rendered_arg("id", "project_ref", "GitLab project path or numeric identifier.", "string", position=0),
            _rendered_arg("merge_request_iid", "merge_request_iid", "GitLab merge request IID.", "integer", position=1),
        ],
    )
    gitlab_merge_status_legacy = _rendered_tool(
        "gitlab.merge_requests.get_detailed_merge_status",
        "merge_requests.get",
        "Retrieve a GitLab merge request and read the legacy merge_status field for mergeability.",
        [
            _rendered_arg("id", "project_ref", "GitLab project path or numeric identifier.", "string", position=0),
            _rendered_arg("merge_request_iid", "merge_request_iid", "GitLab merge request IID.", "integer", position=1),
        ],
    )
    gitlab_merge_status_current = _rendered_tool(
        "gitlab.merge_requests.get_detailed_merge_status",
        "merge_requests.get",
        "Retrieve a GitLab merge request and read the current detailed_merge_status field for mergeability.",
        [
            _rendered_arg("id", "project_ref", "GitLab project path or numeric identifier.", "string", position=0),
            _rendered_arg("merge_request_iid", "merge_request_iid", "GitLab merge request IID.", "integer", position=1),
        ],
    )
    gitlab_merge_changes_legacy = _rendered_tool(
        "gitlab.merge_requests.get_with_changes",
        "merge_requests.changes.get",
        "Retrieve a GitLab merge request together with its files and changes through the deprecated single changes endpoint.",
        [
            _rendered_arg("id", "project_ref", "GitLab project path or numeric identifier.", "string", position=0),
            _rendered_arg("merge_request_iid", "merge_request_iid", "GitLab merge request IID.", "integer", position=1),
        ],
    )
    gitlab_merge_diffs_current = _rendered_tool(
        "gitlab.merge_requests.get_with_changes",
        "merge_requests.diffs.list",
        "List diff records for a GitLab merge request. The deprecated single changes endpoint is gone; current diffs listing is related but does not recover the old one-shot merge-request-plus-changes contract as a drop-in operation.",
        [
            _rendered_arg("id", "project_ref", "GitLab project path or numeric identifier.", "string", position=0),
            _rendered_arg("merge_request_iid", "merge_request_iid", "GitLab merge request IID.", "integer", position=1),
            _rendered_arg("page", "page", "Optional diff page to return.", "integer", required=False, position=2),
            _rendered_arg("per_page", "page_size", "Optional number of diff records to return.", "integer", required=False, position=3),
        ],
    )
    gitlab_project_import_legacy = _rendered_tool(
        "gitlab.projects.import_archive",
        "projects.import",
        "Import a GitLab project archive using the legacy namespace parameter, which accepted either an ID or a path.",
        [
            _rendered_arg("file", "archive_ref", "Project archive file identifier.", "string", position=0),
            _rendered_arg("path", "project_path", "Path of the new GitLab project.", "string", position=1),
            _rendered_arg("namespace", "target_namespace_ref", "GitLab namespace identifier or path.", "string", position=2),
        ],
    )
    gitlab_project_import_namespace_id_current = _rendered_tool(
        "gitlab.projects.import_archive",
        "projects.import",
        "Import a GitLab project archive by specifying namespace_id explicitly. The old namespace parameter is deprecated because a numeric token can no longer be treated as both ID and path without ambiguity.",
        [
            _rendered_arg("file", "archive_ref", "Project archive file identifier.", "string", position=0),
            _rendered_arg("path", "project_path", "Path of the new GitLab project.", "string", position=1),
            _rendered_arg("namespace_id", "target_namespace_ref", "Numeric namespace identifier.", "string", position=2),
        ],
    )
    gitlab_project_import_namespace_path_current = _rendered_tool(
        "gitlab.projects.import_archive",
        "projects.import",
        "Import a GitLab project archive by specifying namespace_path explicitly. The deprecated namespace parameter cannot be used as an ambiguous ID-or-path token in the current contract.",
        [
            _rendered_arg("file", "archive_ref", "Project archive file identifier.", "string", position=0),
            _rendered_arg("path", "project_path", "Path of the new GitLab project.", "string", position=1),
            _rendered_arg("namespace_path", "target_namespace_ref", "Namespace path.", "string", position=2),
        ],
    )
    slack_oauth_access_legacy = _rendered_tool(
        "slack.oauth.exchange_install_code",
        "oauth.access",
        "Exchange a temporary Slack OAuth code for an access token using the legacy oauth.access method.",
        [
            _rendered_arg("code", "auth_code", "Temporary Slack OAuth authorization code.", "string", position=0),
            _rendered_arg("redirect_uri", "redirect_uri", "Optional redirect URI that must match the original authorization step.", "string", required=False, position=1),
        ],
    )
    slack_oauth_v2_current = _rendered_tool(
        "slack.oauth.exchange_install_code",
        "oauth.v2.access",
        "Exchange a temporary Slack OAuth code for an access token using the current OAuth v2 access method for Slack apps.",
        [
            _rendered_arg("code", "auth_code", "Temporary Slack OAuth authorization code.", "string", position=0),
            _rendered_arg("redirect_uri", "redirect_uri", "Optional redirect URI that must match the original authorization step.", "string", required=False, position=1),
        ],
    )
    slack_users_email_legacy = _rendered_tool(
        "slack.users.get_user_email",
        "users.info",
        "Get a Slack user record and read its email field. Legacy apps could rely on users:read alone for this data.",
        [
            _rendered_arg("user", "user_ref", "Slack user identifier.", "string", position=0),
        ],
    )
    slack_users_email_current = _rendered_tool(
        "slack.users.get_user_email",
        "users.info",
        "Get a Slack user record and read its email field. Current apps must request both users:read and users:read.email to access this field.",
        [
            _rendered_arg("user", "user_ref", "Slack user identifier.", "string", position=0),
        ],
    )
    slack_channels_history_legacy = _rendered_tool(
        "slack.conversations.get_history",
        "channels.history",
        "Fetch message history for a public Slack channel using the legacy channels.history method and type-specific history scope.",
        [
            _rendered_arg("channel", "conversation_ref", "Slack conversation identifier.", "string", position=0),
            _rendered_arg("count", "page_size", "Optional maximum number of messages to return.", "integer", required=False, position=1),
        ],
    )
    slack_conversations_history_current = _rendered_tool(
        "slack.conversations.get_history",
        "conversations.history",
        "Fetch message history for a Slack conversation using the unified Conversations API and current conversations:history scope model.",
        [
            _rendered_arg("channel", "conversation_ref", "Slack conversation identifier.", "string", position=0),
            _rendered_arg("limit", "page_size", "Optional maximum number of messages to return.", "integer", required=False, position=1),
        ],
    )
    slack_permissions_info_legacy = _rendered_tool(
        "slack.apps.get_granted_permissions",
        "apps.permissions.info",
        "Get the granted scopes and resources for the current Slack app installation through the legacy one-shot permissions inventory method.",
        [],
    )
    slack_permissions_scopes_current = _rendered_tool(
        "slack.apps.get_granted_permissions",
        "apps.permissions.scopes.list",
        "List the granted scopes for the current Slack app installation. This is only one half of the replacement for the retired apps.permissions.info method.",
        [],
    )
    slack_permissions_resources_current = _rendered_tool(
        "slack.apps.get_granted_permissions",
        "apps.permissions.resources.list",
        "List the granted resources for the current Slack app installation. This is only one half of the replacement for the retired apps.permissions.info method.",
        [],
    )

    return [
        _view(
            case_id="trello_poll_member_privacy_since",
            view_id="trello_poll_member_privacy_since::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[trello_member_privacy_legacy, trello_workspaces_current, trello_members_current],
            notes="Legacy Trello application-scoped compliance polling schema.",
        ),
        _view(
            case_id="trello_poll_member_privacy_since",
            view_id="trello_poll_member_privacy_since::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[trello_member_privacy_current, trello_workspaces_current, trello_members_current],
            notes="Real version migration: Trello member privacy polling moved from the legacy application compliance route to the supported plugin compliance route.",
        ),
        _view(
            case_id="trello_poll_member_privacy_window",
            view_id="trello_poll_member_privacy_window::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[trello_member_privacy_legacy, trello_members_current, trello_workspaces_current],
            notes="Legacy Trello application-scoped compliance polling schema with optional limit pagination.",
        ),
        _view(
            case_id="trello_poll_member_privacy_window",
            view_id="trello_poll_member_privacy_window::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[trello_member_privacy_current, trello_members_current, trello_workspaces_current],
            notes="Real version migration: Trello compliance pagination moved onto the plugin-scoped memberPrivacy route.",
        ),
        _view(
            case_id="trello_list_scim_groups",
            view_id="trello_list_scim_groups::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[trello_scim_groups_legacy, trello_workspaces_current, trello_members_current],
            notes="Legacy Trello SCIM group listing schema.",
        ),
        _view(
            case_id="trello_list_scim_groups",
            view_id="trello_list_scim_groups::negative_workspace_listing_replacement",
            transform_name="negative_workspace_listing_replacement",
            shift_kind="negative_near_orbit",
            tools=[trello_scim_groups_current, trello_workspaces_current, trello_members_current],
            notes="Real negative near-orbit: Trello deprecated SCIM Groups endpoints in favor of related REST workspace endpoints that are not a drop-in replacement for SCIM group listing.",
            admissible_actions=[_ask(), _abstain()],
        ),
        _view(
            case_id="trello_list_scim_users",
            view_id="trello_list_scim_users::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[trello_scim_users_legacy, trello_members_current, trello_workspaces_current],
            notes="Legacy Trello SCIM user listing schema.",
        ),
        _view(
            case_id="trello_list_scim_users",
            view_id="trello_list_scim_users::negative_member_query_replacement",
            transform_name="negative_member_query_replacement",
            shift_kind="negative_near_orbit",
            tools=[trello_scim_users_current, trello_members_current, trello_workspaces_current],
            notes="Real negative near-orbit: Trello deprecated SCIM Users endpoints in favor of related member query routes that do not preserve the old SCIM user-list contract as a drop-in replacement.",
            admissible_actions=[_ask(), _abstain()],
        ),
        _view(
            case_id="youtube_add_top_level_comment",
            view_id="youtube_add_top_level_comment::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[youtube_comment_legacy, youtube_uploads_legacy, youtube_related_legacy],
            notes="Legacy YouTube comment-feed style top-level comment creation schema.",
        ),
        _view(
            case_id="youtube_add_top_level_comment",
            view_id="youtube_add_top_level_comment::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[youtube_comment_current, youtube_uploads_current, youtube_related_current],
            notes="Real version migration: YouTube top-level comment creation moved from legacy comment feed writes to commentThreads.insert.",
        ),
        _view(
            case_id="youtube_list_upload_videos",
            view_id="youtube_list_upload_videos::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[youtube_uploads_legacy, youtube_comment_legacy, youtube_mark_spam_legacy],
            notes="Legacy YouTube uploads feed listing schema.",
        ),
        _view(
            case_id="youtube_list_upload_videos",
            view_id="youtube_list_upload_videos::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[youtube_uploads_current, youtube_comment_current, youtube_mark_spam_current],
            notes="Real version migration: legacy YouTube uploads feed access moved to playlistItems.list over the uploads playlist representation.",
        ),
        _view(
            case_id="youtube_search_related_videos",
            view_id="youtube_search_related_videos::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[youtube_related_legacy, youtube_uploads_legacy, youtube_comment_legacy],
            notes="Legacy YouTube search schema with relatedToVideoId support.",
        ),
        _view(
            case_id="youtube_search_related_videos",
            view_id="youtube_search_related_videos::negative_related_parameter_removed",
            transform_name="negative_related_parameter_removed",
            shift_kind="negative_near_orbit",
            tools=[youtube_related_current, youtube_uploads_current, youtube_comment_current],
            notes="Real negative near-orbit: YouTube no longer supports relatedToVideoId on search.list, so generic search is not a drop-in replacement for the old related-videos operation.",
            admissible_actions=[_ask(), _abstain()],
        ),
        _view(
            case_id="youtube_mark_comment_spam",
            view_id="youtube_mark_comment_spam::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[youtube_mark_spam_legacy, youtube_comment_legacy, youtube_related_legacy],
            notes="Legacy YouTube comment moderation schema with comments.markAsSpam.",
        ),
        _view(
            case_id="youtube_mark_comment_spam",
            view_id="youtube_mark_comment_spam::negative_deprecate",
            transform_name="negative_deprecate",
            shift_kind="negative_near_orbit",
            tools=[youtube_mark_spam_current, youtube_comment_current, youtube_related_current],
            notes="Real negative near-orbit: comments.markAsSpam is no longer supported in the YouTube Data API.",
            admissible_actions=[_abstain()],
        ),
        _view(
            case_id="youtube_channels_get_profile",
            view_id="youtube_channels_get_profile::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[youtube_channel_profile_legacy, youtube_uploads_playlist_legacy, youtube_channel_uploads_legacy],
            notes="Legacy YouTube channel profile schema.",
        ),
        _view(
            case_id="youtube_channels_get_profile",
            view_id="youtube_channels_get_profile::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[youtube_channel_profile_current, youtube_uploads_playlist_current, youtube_channel_uploads_current],
            notes="Real version migration: YouTube channel profile retrieval moved onto channels.list resources.",
        ),
        _view(
            case_id="youtube_channels_get_uploads_playlist",
            view_id="youtube_channels_get_uploads_playlist::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[youtube_uploads_playlist_legacy, youtube_channel_profile_legacy, youtube_channel_uploads_legacy],
            notes="Legacy YouTube channel profile schema exposing an uploads feed link.",
        ),
        _view(
            case_id="youtube_channels_get_uploads_playlist",
            view_id="youtube_channels_get_uploads_playlist::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[youtube_uploads_playlist_current, youtube_channel_profile_current, youtube_channel_uploads_current],
            notes="Real version migration: uploads playlist lookup moved to channels.list contentDetails.relatedPlaylists.uploads.",
        ),
        _view(
            case_id="youtube_channels_list_uploaded_videos",
            view_id="youtube_channels_list_uploaded_videos::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[youtube_channel_uploads_legacy, youtube_uploads_playlist_legacy, youtube_channel_profile_legacy],
            notes="Legacy YouTube uploads feed listing schema.",
        ),
        _view(
            case_id="youtube_channels_list_uploaded_videos",
            view_id="youtube_channels_list_uploaded_videos::negative_playlist_lookup_split",
            transform_name="negative_playlist_lookup_split",
            shift_kind="negative_near_orbit",
            tools=[youtube_channel_uploads_current, youtube_uploads_playlist_current, youtube_channel_profile_current],
            notes="Real negative near-orbit: listing uploaded videos by channel now requires a separate channels.list lookup to resolve the uploads playlist before calling playlistItems.list.",
            admissible_actions=[_ask(), _abstain()],
        ),
        _view(
            case_id="youtube_activities_list_recommended_videos",
            view_id="youtube_activities_list_recommended_videos::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[youtube_home_recommendations_legacy, youtube_channel_profile_legacy, youtube_channel_uploads_legacy],
            notes="Legacy YouTube home recommendations feed schema.",
        ),
        _view(
            case_id="youtube_activities_list_recommended_videos",
            view_id="youtube_activities_list_recommended_videos::negative_home_feed_broader_surface",
            transform_name="negative_home_feed_broader_surface",
            shift_kind="negative_near_orbit",
            tools=[youtube_home_activities_current, youtube_channel_profile_current, youtube_channel_uploads_current],
            notes="Real negative near-orbit: the current home activities feed is broader than the old recommendations-only surface and is not a drop-in replacement.",
            admissible_actions=[_ask(), _abstain()],
        ),
        _view(
            case_id="github_list_custom_repository_roles",
            view_id="github_list_custom_repository_roles::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[github_custom_roles_list_legacy, github_custom_role_get_current, github_create_repo_current],
            notes="Legacy GitHub custom repository roles beta path.",
        ),
        _view(
            case_id="github_list_custom_repository_roles",
            view_id="github_list_custom_repository_roles::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[github_custom_roles_list_current, github_custom_role_get_current, github_create_repo_current],
            notes="Real version migration: GitHub custom repository role listing moved from the beta custom_roles path to the GA custom-repository-roles path.",
        ),
        _view(
            case_id="github_get_custom_repository_role",
            view_id="github_get_custom_repository_role::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[github_custom_role_get_legacy, github_custom_roles_list_current, github_create_repo_current],
            notes="Legacy GitHub custom repository role beta path for fetching a single role.",
        ),
        _view(
            case_id="github_get_custom_repository_role",
            view_id="github_get_custom_repository_role::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[github_custom_role_get_current, github_custom_roles_list_current, github_create_repo_current],
            notes="Real version migration: GitHub custom repository role item retrieval moved from the beta custom_roles path to the GA custom-repository-roles path.",
        ),
        _view(
            case_id="github_delete_generic_reaction",
            view_id="github_delete_generic_reaction::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[github_generic_reaction_delete_legacy, github_issue_reaction_delete_current, github_issue_comment_reaction_delete_current],
            notes="Legacy GitHub generic delete-reaction schema.",
        ),
        _view(
            case_id="github_delete_generic_reaction",
            view_id="github_delete_generic_reaction::negative_resource_context_split",
            transform_name="negative_resource_context_split",
            shift_kind="negative_near_orbit",
            tools=[github_issue_reaction_delete_current, github_issue_comment_reaction_delete_current, github_commit_comment_reaction_delete_current],
            notes="Real negative near-orbit: GitHub removed the generic delete reaction route and replaced it with resource-specific delete endpoints that require extra context not present in the old reaction-id-only contract.",
            admissible_actions=[_ask(), _abstain()],
        ),
        _view(
            case_id="github_import_external_repository",
            view_id="github_import_external_repository::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[github_source_import_legacy, github_create_repo_current, github_create_from_template_current],
            notes="Legacy GitHub Source Imports REST API schema.",
        ),
        _view(
            case_id="github_import_external_repository",
            view_id="github_import_external_repository::negative_out_of_band_replacement",
            transform_name="negative_out_of_band_replacement",
            shift_kind="negative_near_orbit",
            tools=[github_create_repo_current, github_create_from_template_current, github_create_fork_current],
            notes="Real negative near-orbit: GitHub Source Imports is closing down, and current repository bootstrap endpoints or migration guides are related but do not provide a drop-in import-from-URL REST contract.",
            admissible_actions=[_ask(), _abstain()],
        ),
        _view(
            case_id="gitlab_get_merge_request_merge_actor",
            view_id="gitlab_get_merge_request_merge_actor::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[gitlab_merge_actor_legacy, gitlab_merge_status_current, gitlab_merge_changes_legacy],
            notes="Legacy GitLab merge request field schema exposing merged_by.",
        ),
        _view(
            case_id="gitlab_get_merge_request_merge_actor",
            view_id="gitlab_get_merge_request_merge_actor::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[gitlab_merge_actor_current, gitlab_merge_status_current, gitlab_merge_diffs_current],
            notes="Real version migration: GitLab merge request merge actor moved from merged_by to merge_user.",
        ),
        _view(
            case_id="gitlab_get_merge_request_detailed_status",
            view_id="gitlab_get_merge_request_detailed_status::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[gitlab_merge_status_legacy, gitlab_merge_actor_current, gitlab_merge_changes_legacy],
            notes="Legacy GitLab merge request field schema exposing merge_status.",
        ),
        _view(
            case_id="gitlab_get_merge_request_detailed_status",
            view_id="gitlab_get_merge_request_detailed_status::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[gitlab_merge_status_current, gitlab_merge_actor_current, gitlab_merge_diffs_current],
            notes="Real version migration: GitLab merge request mergeability moved from merge_status to detailed_merge_status.",
        ),
        _view(
            case_id="gitlab_get_merge_request_with_changes",
            view_id="gitlab_get_merge_request_with_changes::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[gitlab_merge_changes_legacy, gitlab_merge_actor_legacy, gitlab_merge_status_legacy],
            notes="Legacy GitLab single merge-request changes endpoint schema.",
        ),
        _view(
            case_id="gitlab_get_merge_request_with_changes",
            view_id="gitlab_get_merge_request_with_changes::negative_changes_endpoint_split",
            transform_name="negative_changes_endpoint_split",
            shift_kind="negative_near_orbit",
            tools=[gitlab_merge_diffs_current, gitlab_merge_actor_current, gitlab_merge_status_current],
            notes="Real negative near-orbit: GitLab deprecated the single changes endpoint in favor of the diffs listing endpoint, which is related but not a drop-in replacement for retrieving one merge request together with its changes snapshot.",
            admissible_actions=[_ask(), _abstain()],
        ),
        _view(
            case_id="gitlab_import_project_archive_ambiguous_namespace",
            view_id="gitlab_import_project_archive_ambiguous_namespace::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[gitlab_project_import_legacy, gitlab_merge_actor_current, gitlab_merge_status_current],
            notes="Legacy GitLab project import schema with the ambiguous namespace parameter.",
        ),
        _view(
            case_id="gitlab_import_project_archive_ambiguous_namespace",
            view_id="gitlab_import_project_archive_ambiguous_namespace::negative_namespace_disambiguation",
            transform_name="negative_namespace_disambiguation",
            shift_kind="negative_near_orbit",
            tools=[gitlab_project_import_namespace_id_current, gitlab_project_import_namespace_path_current, gitlab_merge_status_current],
            notes="Real negative near-orbit: GitLab deprecated namespace in project import APIs, requiring namespace_id or namespace_path instead. An old numeric token can no longer be treated as an unambiguous ID-or-path drop-in argument.",
            admissible_actions=[_ask(), _abstain()],
        ),
        _view(
            case_id="slack_exchange_install_code",
            view_id="slack_exchange_install_code::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[slack_oauth_access_legacy, slack_users_email_legacy, slack_channels_history_legacy],
            notes="Legacy Slack OAuth access exchange schema.",
        ),
        _view(
            case_id="slack_exchange_install_code",
            view_id="slack_exchange_install_code::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[slack_oauth_v2_current, slack_users_email_current, slack_conversations_history_current],
            notes="Real version migration: Slack installation code exchange moved from oauth.access to oauth.v2.access for new Slack apps.",
        ),
        _view(
            case_id="slack_get_user_email",
            view_id="slack_get_user_email::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[slack_users_email_legacy, slack_channels_history_legacy, slack_oauth_access_legacy],
            notes="Legacy Slack user email access schema relying on users:read.",
        ),
        _view(
            case_id="slack_get_user_email",
            view_id="slack_get_user_email::positive_scope_migration",
            transform_name="positive_scope_migration",
            shift_kind="positive_orbit",
            tools=[slack_users_email_current, slack_conversations_history_current, slack_oauth_v2_current],
            notes="Real positive orbit: Slack user email retrieval still uses users.info, but now requires users:read.email alongside users:read.",
        ),
        _view(
            case_id="slack_get_conversation_history",
            view_id="slack_get_conversation_history::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[slack_channels_history_legacy, slack_users_email_legacy, slack_permissions_info_legacy],
            notes="Legacy Slack channel history schema with type-specific history scopes.",
        ),
        _view(
            case_id="slack_get_conversation_history",
            view_id="slack_get_conversation_history::positive_scope_migration",
            transform_name="positive_scope_migration",
            shift_kind="positive_orbit",
            tools=[slack_conversations_history_current, slack_users_email_current, slack_permissions_scopes_current],
            notes="Real version migration: Slack history retrieval moved onto conversations.history with the unified Conversations API scope model.",
        ),
        _view(
            case_id="slack_get_granted_permissions",
            view_id="slack_get_granted_permissions::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[slack_permissions_info_legacy, slack_oauth_access_legacy, slack_users_email_legacy],
            notes="Legacy Slack permissions inventory schema with apps.permissions.info.",
        ),
        _view(
            case_id="slack_get_granted_permissions",
            view_id="slack_get_granted_permissions::negative_permissions_inventory_split",
            transform_name="negative_permissions_inventory_split",
            shift_kind="negative_near_orbit",
            tools=[slack_permissions_scopes_current, slack_permissions_resources_current, slack_oauth_v2_current],
            notes="Real negative near-orbit: Slack retired apps.permissions.info and split the old one-shot permission inventory into separate scopes.list and resources.list methods, which are related but not a drop-in replacement.",
            admissible_actions=[_ask(), _abstain()],
        ),
    ]


def build_benchmark_payload() -> dict[str, object]:
    cases = build_cases()
    views = build_views()
    sources = build_sources()
    family_tags = sorted({case["family_tag"] for case in cases})
    vendor_tags = sorted({source["vendor"] for source in sources.values()})
    return {
        "tools": build_tools(),
        "cases": cases,
        "views": views,
        "sources": sources,
        "metadata": {
            "panel_role": "blind_test",
            "panel_version": "blind_v6",
            "panel_state": "frozen",
            "method_selection_allowed": False,
            "dev_panel_benchmark": "data/real_evolution_benchmark.json",
            "audit_path": "data/real_evolution_blind_audit.json",
            "audit_markdown_path": "history/real_evolution_blind_audit.md",
            "family_tags": family_tags,
            "vendor_tags": vendor_tags,
            "counts": {
                "cases": len(cases),
                "views": len(views),
                "sources": len(sources),
            },
        },
    }


def build_audit_payload() -> dict[str, object]:
    return {
        "case_overrides": {},
        "view_overrides": {},
    }


def build_audit_markdown(benchmark_payload: dict[str, object]) -> str:
    sources = benchmark_payload["sources"]
    cases = benchmark_payload["cases"]
    views = benchmark_payload["views"]
    lines = [
        "# Real Evolution Blind Audit",
        "",
        "This file records the official source anchors and audit intent for the frozen ToolShift blind real-evolution panel.",
        "",
        "## Scope",
        "",
        "- This benchmark is a frozen blind test asset, not the current method-selection panel.",
        "- Current method search remains on `data/real_evolution_benchmark.json`, which is now treated as the real-evolution dev panel.",
        "- The blind panel should not be used for method selection, threshold tuning, or loss sweeps.",
        "- New families should be added only through an explicit governance decision that also updates the blind audit and freeze summary.",
        "",
        "## Sources",
        "",
        "| Source ID | Vendor | Kind | URL | Summary |",
        "| --- | --- | --- | --- | --- |",
    ]
    for source_id in sorted(sources):
        source = sources[source_id]
        lines.append(
            f"| `{source_id}` | {source['vendor']} | {source['kind']} | {source['url']} | {source['summary']} |"
        )

    case_lookup = {case["case_id"]: case for case in cases}
    lines.extend(["", "## Cases", ""])
    for case_id in sorted(case_lookup):
        case = case_lookup[case_id]
        lines.append(f"### `{case_id}`")
        lines.append("")
        lines.append(f"- Family: `{case['family_tag']}`")
        lines.append(f"- Request: {case['request']}")
        lines.append(f"- Notes: {case['notes']}")
        lines.append("")
        lines.append("| View ID | Shift | Transform | Admissible | Notes |")
        lines.append("| --- | --- | --- | --- | --- |")
        for view in [item for item in views if item["case_id"] == case_id]:
            admissible = view.get("admissible_actions", case["admissible_actions"])
            admissible_str = ", ".join(action["control"] for action in admissible)
            schema_view = view["schema_view"]
            lines.append(
                f"| `{schema_view['view_id']}` | `{schema_view['shift_kind']}` | `{schema_view['transform_name']}` | `{admissible_str}` | {view['notes']} |"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the ToolShift blind real-evolution benchmark and audit files.")
    parser.add_argument("--output-benchmark", default="data/real_evolution_blind_benchmark.json")
    parser.add_argument("--output-audit", default="data/real_evolution_blind_audit.json")
    parser.add_argument("--output-audit-md", default="history/real_evolution_blind_audit.md")
    args = parser.parse_args()

    benchmark_payload = build_benchmark_payload()
    audit_payload = build_audit_payload()
    audit_markdown = build_audit_markdown(benchmark_payload)

    benchmark_path = Path(args.output_benchmark)
    audit_path = Path(args.output_audit)
    audit_markdown_path = Path(args.output_audit_md)

    benchmark_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_markdown_path.parent.mkdir(parents=True, exist_ok=True)

    benchmark_path.write_text(json.dumps(benchmark_payload, indent=2) + "\n", encoding="utf-8")
    audit_path.write_text(json.dumps(audit_payload, indent=2) + "\n", encoding="utf-8")
    audit_markdown_path.write_text(audit_markdown + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
