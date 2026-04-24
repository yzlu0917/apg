# Real Evolution Blind Audit

This file records the official source anchors and audit intent for the frozen ToolShift blind real-evolution panel.

## Scope

- This benchmark is a frozen blind test asset, not the current method-selection panel.
- Current method search remains on `data/real_evolution_benchmark.json`, which is now treated as the real-evolution dev panel.
- The blind panel should not be used for method selection, threshold tuning, or loss sweeps.
- New families should be added only through an explicit governance decision that also updates the blind audit and freeze summary.

## Sources

| Source ID | Vendor | Kind | URL | Summary |
| --- | --- | --- | --- | --- |
| `github_custom_roles_beta` | github | changelog | https://github.blog/changelog/2022-09-07-create-a-custom-organization-role-rest-api-is-now-available-in-public-beta/ | GitHub changelog entry announcing the public beta custom organization role REST APIs under the legacy custom_roles path. |
| `github_custom_roles_ga_breaking` | github | changelog | https://github.blog/changelog/2023-03-07-custom-repository-roles-apis-are-now-generally-available/ | GitHub changelog entry describing the GA path migration from custom_roles to custom-repository-roles. |
| `github_custom_roles_ref` | github | reference | https://docs.github.com/en/rest/orgs/custom-repository-roles | GitHub REST reference for current custom repository role endpoints. |
| `github_programmatic_imports_guide` | github | guide | https://docs.github.com/en/migrations/overview/programmatically-importing-repositories | GitHub guide for programmatically importing repositories after Source Imports API deprecation. |
| `github_reactions_breaking` | github | changelog | https://github.blog/changelog/2024-05-30-deprecation-of-the-delete-reactions-rest-api-endpoint/ | GitHub changelog entry deprecating the generic delete reaction endpoint in favor of resource-specific delete endpoints. |
| `github_reactions_ref` | github | reference | https://docs.github.com/en/rest/reactions | GitHub REST reference for current resource-specific reactions endpoints. |
| `github_repos_ref` | github | reference | https://docs.github.com/en/rest/repos/repos | GitHub REST reference for repository creation and template-based repository endpoints. |
| `github_source_imports_closing_down` | github | changelog | https://github.blog/changelog/2024-03-22-source-imports-api-is-closing-down/ | GitHub changelog entry announcing the closure of the Source Imports REST API. |
| `github_source_imports_ref` | github | reference | https://docs.github.com/en/rest/migrations/source-imports | GitHub REST reference for the legacy Source Imports endpoints. |
| `gitlab_merge_requests_ref` | gitlab | reference | https://docs.gitlab.com/api/merge_requests/ | GitLab Merge Requests API reference including merged_by, merge_user, merge_status, detailed_merge_status, and the deprecated changes endpoint. |
| `gitlab_project_import_export_ref` | gitlab | reference | https://docs.gitlab.com/api/project_import_export/ | GitLab project import and export API reference documenting deprecated namespace and the replacement namespace_id or namespace_path parameters. |
| `gitlab_rest_deprecations` | gitlab | changelog | https://docs.gitlab.com/api/rest/deprecations/ | GitLab REST API deprecations page covering merge request field deprecations, merge request changes endpoint deprecation, and namespace parameter deprecation in project import APIs. |
| `slack_conversations_api_guide` | slack | guide | https://api.slack.com/conversations-api | Slack Conversations API guide describing the unified interface and scope model for channel-like objects. |
| `slack_conversations_history_ref` | slack | reference | https://api.slack.com/methods/conversations.history | Slack conversations.history reference documenting current history retrieval and its required scopes. |
| `slack_conversations_scopes_changelog` | slack | changelog | https://api.slack.com/changelog/2018-06-conversations-apis-and-scopes-for-workspace-apps | Slack changelog entry announcing Conversations API scopes for workspace apps and the simplified conversations:history scope model. |
| `slack_oauth_access_ref` | slack | reference | https://api.slack.com/methods/oauth.access | Legacy Slack OAuth access exchange method for classic apps. |
| `slack_oauth_flow_changes` | slack | changelog | https://api.slack.com/changelog/2018-04-oauth-flow-changes-for-workspace-token-preview-apps | Slack changelog entry announcing oauth.token retirement, oauth.access migration for workspace apps, and the split replacement for apps.permissions.info. |
| `slack_oauth_v2_access_ref` | slack | reference | https://api.slack.com/methods/oauth.v2.access | Current Slack OAuth v2 access exchange method for new Slack apps. |
| `slack_permissions_methods_index` | slack | reference | https://api.slack.com/methods | Slack Web API methods index containing the current methods, including apps.permissions.scopes.list and apps.permissions.resources.list. |
| `slack_users_email_changelog` | slack | changelog | https://api.slack.com/changelog/2016-11-10-addressing-email-addresses | Slack changelog entry announcing that users:read.email is required for email addresses in users.list and users.info. |
| `slack_users_list_ref` | slack | reference | https://api.slack.com/methods/users.list | Slack users.list reference documenting that users:read.email is required for email fields in users.list and users.info. |
| `slack_users_read_email_scope` | slack | scope | https://api.slack.com/scopes/users%3Aread.email | Slack scope reference describing users:read.email and its requirement alongside users:read for user email access. |
| `trello_2025_08_member_privacy_deprecation` | trello | changelog | https://developer.atlassian.com/cloud/trello/changelog/ | Trello changelog entry for the 2025-08-06 deprecation of the legacy /application/:id/compliance/memberPrivacy route in favor of the plugin compliance route. |
| `trello_2025_09_scim_deprecation` | trello | changelog | https://developer.atlassian.com/cloud/trello/changelog/ | Trello changelog entry for the 2025-09-15 deprecation of /scim/v2/users and /scim/v2/groups in favor of related REST endpoints. |
| `trello_applications_ref` | trello | reference | https://developer.atlassian.com/cloud/trello/rest/api-group-applications/ | Legacy Trello application reference group used as the old compliance-route anchor. |
| `trello_gdpr_guide` | trello | guide | https://developer.atlassian.com/cloud/trello/guides/compliance/personal-data-storage-gdpr/ | Trello privacy and compliance guide describing the supported plugin member privacy workflow. |
| `trello_members_ref` | trello | reference | https://developer.atlassian.com/cloud/trello/rest/api-group-members/ | Trello REST reference group for member lookup and enterprise member query endpoints. |
| `trello_organizations_ref` | trello | reference | https://developer.atlassian.com/cloud/trello/rest/api-group-organizations/ | Trello REST reference group for organization and enterprise workspace listing endpoints. |
| `trello_plugins_ref` | trello | reference | https://developer.atlassian.com/cloud/trello/rest/api-group-plugins/ | Current Trello plugin reference group containing plugin-scoped compliance endpoints. |
| `trello_scim_resources_ref` | trello | reference | https://developer.atlassian.com/cloud/trello/scim/resources/ | Current Trello SCIM resources reference describing SCIM user and group resource semantics. |
| `trello_scim_routes_ref` | trello | reference | https://developer.atlassian.com/cloud/trello/scim/routes/ | Current Trello SCIM routes reference describing legacy Users and Groups listing endpoints. |
| `youtube_activities_list_ref` | youtube | reference | https://developers.google.com/youtube/v3/docs/activities/list | YouTube v3 activities.list reference for home activities retrieval. |
| `youtube_channel_ids_guide` | youtube | guide | https://developers.google.com/youtube/v3/guides/working_with_channel_ids | YouTube guide describing legacy Data API v2 uploads feeds and the move toward stable channel identifiers and v3 resources. |
| `youtube_channels_guide` | youtube | guide | https://developers.google.com/youtube/v3/guides/implementation/channels | YouTube v3 channel guide showing how to resolve a channel's uploads playlist through contentDetails.relatedPlaylists.uploads. |
| `youtube_channels_list_ref` | youtube | reference | https://developers.google.com/youtube/v3/docs/channels/list | YouTube v3 channels.list reference for channel metadata retrieval and relatedPlaylists access. |
| `youtube_comment_changes_v2` | youtube | guide | https://developers.google.com/youtube/articles/changes_to_comments | Legacy YouTube Data API v2 comment-system article documenting old comment feed behavior and write support caveats. |
| `youtube_comments_guide` | youtube | guide | https://developers.google.com/youtube/v3/guides/implementation/comments | YouTube v3 comments guide describing top-level comment creation with commentThreads.insert and the lack of comments.markAsSpam support. |
| `youtube_playlistitems_list_ref` | youtube | reference | https://developers.google.com/youtube/v3/docs/playlistItems/list | YouTube v3 playlistItems.list reference for enumerating items from an uploads playlist. |
| `youtube_revision_history_2023_mark_spam` | youtube | changelog | https://developers.google.com/youtube/v3/revision_history | YouTube revision history entry announcing that comments.markAsSpam is unsupported and removed from current API use. |
| `youtube_revision_history_2023_related` | youtube | changelog | https://developers.google.com/youtube/v3/revision_history | YouTube revision history entry announcing and completing removal of search.list relatedToVideoId support in 2023. |
| `youtube_revision_history_home_feed` | youtube | changelog | https://developers.google.com/youtube/v3/revision_history | YouTube revision history entry documenting that home activity retrieval can mix uploads, likes, and recommendations rather than providing a pure recommendations feed. |
| `youtube_search_ref` | youtube | reference | https://developers.google.com/youtube/v3/docs/search | YouTube v3 search.list reference for generic video, channel, and playlist search. |

## Cases

### `github_delete_generic_reaction`

- Family: `github_rest`
- Request: Delete GitHub reaction 4242 from repository octo-sec/toolshift.
- Notes: sources=github_reactions_breaking,github_reactions_ref;pair=generic_reaction_delete_to_resource_context_split

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `github_delete_generic_reaction::clean` | `clean` | `clean` | `execute` | Legacy GitHub generic delete-reaction schema. |
| `github_delete_generic_reaction::negative_resource_context_split` | `negative_near_orbit` | `negative_resource_context_split` | `ask_clarification, abstain` | Real negative near-orbit: GitHub removed the generic delete reaction route and replaced it with resource-specific delete endpoints that require extra context not present in the old reaction-id-only contract. |

### `github_get_custom_repository_role`

- Family: `github_rest`
- Request: Get GitHub custom repository role 42 for organization octo-sec.
- Notes: sources=github_custom_roles_beta,github_custom_roles_ga_breaking,github_custom_roles_ref;pair=custom_role_item_path_migration

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `github_get_custom_repository_role::clean` | `clean` | `clean` | `execute` | Legacy GitHub custom repository role beta path for fetching a single role. |
| `github_get_custom_repository_role::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: GitHub custom repository role item retrieval moved from the beta custom_roles path to the GA custom-repository-roles path. |

### `github_import_external_repository`

- Family: `github_rest`
- Request: Import the external Git repository https://git.example.com/roadmap.git into GitHub repository octo-sec/roadmap-mirror.
- Notes: sources=github_source_imports_closing_down,github_source_imports_ref,github_programmatic_imports_guide,github_repos_ref;pair=source_import_api_to_out_of_band_replacement

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `github_import_external_repository::clean` | `clean` | `clean` | `execute` | Legacy GitHub Source Imports REST API schema. |
| `github_import_external_repository::negative_out_of_band_replacement` | `negative_near_orbit` | `negative_out_of_band_replacement` | `ask_clarification, abstain` | Real negative near-orbit: GitHub Source Imports is closing down, and current repository bootstrap endpoints or migration guides are related but do not provide a drop-in import-from-URL REST contract. |

### `github_list_custom_repository_roles`

- Family: `github_rest`
- Request: List custom repository roles for GitHub organization octo-sec with page size 50.
- Notes: sources=github_custom_roles_beta,github_custom_roles_ga_breaking,github_custom_roles_ref;pair=custom_roles_path_migration

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `github_list_custom_repository_roles::clean` | `clean` | `clean` | `execute` | Legacy GitHub custom repository roles beta path. |
| `github_list_custom_repository_roles::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: GitHub custom repository role listing moved from the beta custom_roles path to the GA custom-repository-roles path. |

### `gitlab_get_merge_request_detailed_status`

- Family: `gitlab_rest`
- Request: Get the detailed merge status for GitLab merge request 42 in project platform/toolshift.
- Notes: sources=gitlab_rest_deprecations,gitlab_merge_requests_ref;pair=merge_status_to_detailed_merge_status

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `gitlab_get_merge_request_detailed_status::clean` | `clean` | `clean` | `execute` | Legacy GitLab merge request field schema exposing merge_status. |
| `gitlab_get_merge_request_detailed_status::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: GitLab merge request mergeability moved from merge_status to detailed_merge_status. |

### `gitlab_get_merge_request_merge_actor`

- Family: `gitlab_rest`
- Request: Get the merge actor for GitLab merge request 42 in project platform/toolshift.
- Notes: sources=gitlab_rest_deprecations,gitlab_merge_requests_ref;pair=merged_by_to_merge_user

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `gitlab_get_merge_request_merge_actor::clean` | `clean` | `clean` | `execute` | Legacy GitLab merge request field schema exposing merged_by. |
| `gitlab_get_merge_request_merge_actor::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: GitLab merge request merge actor moved from merged_by to merge_user. |

### `gitlab_get_merge_request_with_changes`

- Family: `gitlab_rest`
- Request: Get GitLab merge request 42 in project platform/toolshift together with its file changes.
- Notes: sources=gitlab_rest_deprecations,gitlab_merge_requests_ref;pair=single_merge_request_changes_to_diff_listing

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `gitlab_get_merge_request_with_changes::clean` | `clean` | `clean` | `execute` | Legacy GitLab single merge-request changes endpoint schema. |
| `gitlab_get_merge_request_with_changes::negative_changes_endpoint_split` | `negative_near_orbit` | `negative_changes_endpoint_split` | `ask_clarification, abstain` | Real negative near-orbit: GitLab deprecated the single changes endpoint in favor of the diffs listing endpoint, which is related but not a drop-in replacement for retrieving one merge request together with its changes snapshot. |

### `gitlab_import_project_archive_ambiguous_namespace`

- Family: `gitlab_rest`
- Request: Import GitLab project archive roadmap-export.tar.gz into namespace 1234 as project roadmap-archive.
- Notes: sources=gitlab_rest_deprecations,gitlab_project_import_export_ref;pair=namespace_to_namespace_id_or_path

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `gitlab_import_project_archive_ambiguous_namespace::clean` | `clean` | `clean` | `execute` | Legacy GitLab project import schema with the ambiguous namespace parameter. |
| `gitlab_import_project_archive_ambiguous_namespace::negative_namespace_disambiguation` | `negative_near_orbit` | `negative_namespace_disambiguation` | `ask_clarification, abstain` | Real negative near-orbit: GitLab deprecated namespace in project import APIs, requiring namespace_id or namespace_path instead. An old numeric token can no longer be treated as an unambiguous ID-or-path drop-in argument. |

### `slack_exchange_install_code`

- Family: `slack_auth`
- Request: Exchange Slack installation code code-123 for an access token using redirect URI https://toolshift.example.com/slack/callback.
- Notes: sources=slack_oauth_flow_changes,slack_oauth_access_ref,slack_oauth_v2_access_ref;pair=oauth_access_to_oauth_v2_access

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `slack_exchange_install_code::clean` | `clean` | `clean` | `execute` | Legacy Slack OAuth access exchange schema. |
| `slack_exchange_install_code::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: Slack installation code exchange moved from oauth.access to oauth.v2.access for new Slack apps. |

### `slack_get_conversation_history`

- Family: `slack_auth`
- Request: Get the latest 50 messages from Slack conversation C123.
- Notes: sources=slack_conversations_scopes_changelog,slack_conversations_history_ref,slack_conversations_api_guide;pair=channels_history_to_conversations_history

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `slack_get_conversation_history::clean` | `clean` | `clean` | `execute` | Legacy Slack channel history schema with type-specific history scopes. |
| `slack_get_conversation_history::positive_scope_migration` | `positive_orbit` | `positive_scope_migration` | `execute` | Real version migration: Slack history retrieval moved onto conversations.history with the unified Conversations API scope model. |

### `slack_get_granted_permissions`

- Family: `slack_auth`
- Request: Get the granted scopes and resources for the current Slack app installation.
- Notes: sources=slack_oauth_flow_changes,slack_permissions_methods_index;pair=apps_permissions_info_to_scope_and_resource_lists

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `slack_get_granted_permissions::clean` | `clean` | `clean` | `execute` | Legacy Slack permissions inventory schema with apps.permissions.info. |
| `slack_get_granted_permissions::negative_permissions_inventory_split` | `negative_near_orbit` | `negative_permissions_inventory_split` | `ask_clarification, abstain` | Real negative near-orbit: Slack retired apps.permissions.info and split the old one-shot permission inventory into separate scopes.list and resources.list methods, which are related but not a drop-in replacement. |

### `slack_get_user_email`

- Family: `slack_auth`
- Request: Get the email address for Slack user U123.
- Notes: sources=slack_users_email_changelog,slack_users_read_email_scope,slack_users_list_ref;pair=users_read_to_users_read_email

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `slack_get_user_email::clean` | `clean` | `clean` | `execute` | Legacy Slack user email access schema relying on users:read. |
| `slack_get_user_email::positive_scope_migration` | `positive_orbit` | `positive_scope_migration` | `execute` | Real positive orbit: Slack user email retrieval still uses users.info, but now requires users:read.email alongside users:read. |

### `trello_list_scim_groups`

- Family: `trello`
- Request: List SCIM groups for Trello enterprise ent_roadmap.
- Notes: sources=trello_2025_09_scim_deprecation,trello_scim_routes_ref,trello_scim_resources_ref,trello_organizations_ref;pair=scim_groups_to_workspace_listing

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `trello_list_scim_groups::clean` | `clean` | `clean` | `execute` | Legacy Trello SCIM group listing schema. |
| `trello_list_scim_groups::negative_workspace_listing_replacement` | `negative_near_orbit` | `negative_workspace_listing_replacement` | `ask_clarification, abstain` | Real negative near-orbit: Trello deprecated SCIM Groups endpoints in favor of related REST workspace endpoints that are not a drop-in replacement for SCIM group listing. |

### `trello_list_scim_users`

- Family: `trello`
- Request: List SCIM users for Trello enterprise ent_roadmap matching alice@example.com.
- Notes: sources=trello_2025_09_scim_deprecation,trello_scim_routes_ref,trello_scim_resources_ref,trello_members_ref;pair=scim_users_to_member_query

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `trello_list_scim_users::clean` | `clean` | `clean` | `execute` | Legacy Trello SCIM user listing schema. |
| `trello_list_scim_users::negative_member_query_replacement` | `negative_near_orbit` | `negative_member_query_replacement` | `ask_clarification, abstain` | Real negative near-orbit: Trello deprecated SCIM Users endpoints in favor of related member query routes that do not preserve the old SCIM user-list contract as a drop-in replacement. |

### `trello_poll_member_privacy_since`

- Family: `trello`
- Request: Poll Trello member privacy events for integration integ_powerup since 2026-02-01T00:00:00Z.
- Notes: sources=trello_2025_08_member_privacy_deprecation,trello_gdpr_guide,trello_applications_ref,trello_plugins_ref;pair=application_compliance_to_plugin_compliance

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `trello_poll_member_privacy_since::clean` | `clean` | `clean` | `execute` | Legacy Trello application-scoped compliance polling schema. |
| `trello_poll_member_privacy_since::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: Trello member privacy polling moved from the legacy application compliance route to the supported plugin compliance route. |

### `trello_poll_member_privacy_window`

- Family: `trello`
- Request: Fetch the latest 50 Trello member privacy events for integration integ_powerup.
- Notes: sources=trello_2025_08_member_privacy_deprecation,trello_gdpr_guide,trello_applications_ref,trello_plugins_ref;pair=application_compliance_to_plugin_compliance

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `trello_poll_member_privacy_window::clean` | `clean` | `clean` | `execute` | Legacy Trello application-scoped compliance polling schema with optional limit pagination. |
| `trello_poll_member_privacy_window::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: Trello compliance pagination moved onto the plugin-scoped memberPrivacy route. |

### `youtube_activities_list_recommended_videos`

- Family: `youtube_channels`
- Request: List 10 recommended YouTube videos for viewer viewer_self.
- Notes: sources=youtube_revision_history_home_feed,youtube_activities_list_ref;pair=home_feed_is_broader_than_recommendations

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `youtube_activities_list_recommended_videos::clean` | `clean` | `clean` | `execute` | Legacy YouTube home recommendations feed schema. |
| `youtube_activities_list_recommended_videos::negative_home_feed_broader_surface` | `negative_near_orbit` | `negative_home_feed_broader_surface` | `ask_clarification, abstain` | Real negative near-orbit: the current home activities feed is broader than the old recommendations-only surface and is not a drop-in replacement. |

### `youtube_add_top_level_comment`

- Family: `youtube`
- Request: Add the top-level comment 'Ship the draft today.' to YouTube video vid_launch on channel chan_devrel.
- Notes: sources=youtube_comment_changes_v2,youtube_comments_guide;pair=legacy_comment_feed_to_commentThreads_insert

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `youtube_add_top_level_comment::clean` | `clean` | `clean` | `execute` | Legacy YouTube comment-feed style top-level comment creation schema. |
| `youtube_add_top_level_comment::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: YouTube top-level comment creation moved from legacy comment feed writes to commentThreads.insert. |

### `youtube_channels_get_profile`

- Family: `youtube_channels`
- Request: Get the YouTube channel profile for channel chan_devrel.
- Notes: sources=youtube_channel_ids_guide,youtube_channels_list_ref;pair=legacy_channel_profile_to_channels_list

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `youtube_channels_get_profile::clean` | `clean` | `clean` | `execute` | Legacy YouTube channel profile schema. |
| `youtube_channels_get_profile::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: YouTube channel profile retrieval moved onto channels.list resources. |

### `youtube_channels_get_uploads_playlist`

- Family: `youtube_channels`
- Request: Get the uploads playlist for YouTube channel chan_devrel.
- Notes: sources=youtube_channel_ids_guide,youtube_channels_guide,youtube_channels_list_ref;pair=legacy_uploads_feed_link_to_related_playlists

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `youtube_channels_get_uploads_playlist::clean` | `clean` | `clean` | `execute` | Legacy YouTube channel profile schema exposing an uploads feed link. |
| `youtube_channels_get_uploads_playlist::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: uploads playlist lookup moved to channels.list contentDetails.relatedPlaylists.uploads. |

### `youtube_channels_list_uploaded_videos`

- Family: `youtube_channels`
- Request: List the latest uploaded videos for YouTube channel chan_devrel with page size 25.
- Notes: sources=youtube_channel_ids_guide,youtube_channels_guide,youtube_playlistitems_list_ref;pair=uploads_feed_to_playlist_lookup_split

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `youtube_channels_list_uploaded_videos::clean` | `clean` | `clean` | `execute` | Legacy YouTube uploads feed listing schema. |
| `youtube_channels_list_uploaded_videos::negative_playlist_lookup_split` | `negative_near_orbit` | `negative_playlist_lookup_split` | `ask_clarification, abstain` | Real negative near-orbit: listing uploaded videos by channel now requires a separate channels.list lookup to resolve the uploads playlist before calling playlistItems.list. |

### `youtube_list_upload_videos`

- Family: `youtube`
- Request: List the latest uploaded videos from uploads collection UPL_devrel with page size 25.
- Notes: sources=youtube_channel_ids_guide,youtube_channels_guide,youtube_playlistitems_list_ref;pair=uploads_feed_to_playlistitems_list

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `youtube_list_upload_videos::clean` | `clean` | `clean` | `execute` | Legacy YouTube uploads feed listing schema. |
| `youtube_list_upload_videos::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: legacy YouTube uploads feed access moved to playlistItems.list over the uploads playlist representation. |

### `youtube_mark_comment_spam`

- Family: `youtube`
- Request: Mark YouTube comment cmt_spam_42 as spam.
- Notes: sources=youtube_revision_history_2023_mark_spam,youtube_comments_guide;pair=comments_markAsSpam_removed

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `youtube_mark_comment_spam::clean` | `clean` | `clean` | `execute` | Legacy YouTube comment moderation schema with comments.markAsSpam. |
| `youtube_mark_comment_spam::negative_deprecate` | `negative_near_orbit` | `negative_deprecate` | `abstain` | Real negative near-orbit: comments.markAsSpam is no longer supported in the YouTube Data API. |

### `youtube_search_related_videos`

- Family: `youtube`
- Request: List videos related to YouTube video vid_launch.
- Notes: sources=youtube_revision_history_2023_related,youtube_search_ref;pair=relatedToVideoId_removed

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `youtube_search_related_videos::clean` | `clean` | `clean` | `execute` | Legacy YouTube search schema with relatedToVideoId support. |
| `youtube_search_related_videos::negative_related_parameter_removed` | `negative_near_orbit` | `negative_related_parameter_removed` | `ask_clarification, abstain` | Real negative near-orbit: YouTube no longer supports relatedToVideoId on search.list, so generic search is not a drop-in replacement for the old related-videos operation. |

