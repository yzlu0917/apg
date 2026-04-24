# Real Evolution Audit

This file records the official source anchors and audit intent for the first ToolShift real-evolution split.

## Sources

| Source ID | Vendor | Kind | URL | Summary |
| --- | --- | --- | --- | --- |
| `bitbucket_projects_ref` | bitbucket | reference | https://developer.atlassian.com/cloud/bitbucket/rest/api-group-projects/ | Bitbucket projects reference covering project listing under a workspace. |
| `bitbucket_repositories_ref` | bitbucket | reference | https://developer.atlassian.com/cloud/bitbucket/rest/api-group-repositories/ | Bitbucket repositories reference covering repository listing under a workspace. |
| `bitbucket_teams_workspaces_notice` | bitbucket | guide | https://developer.atlassian.com/cloud/bitbucket/bitbucket-api-teams-deprecation/ | Bitbucket Cloud change notice deprecating /2.0/teams and related account endpoints in favor of /2.0/workspaces and workspace-based payloads. |
| `bitbucket_users_ref` | bitbucket | reference | https://developer.atlassian.com/cloud/bitbucket/rest/api-group-users/ | Bitbucket users reference covering the current read-only user lookup endpoint. |
| `bitbucket_v1_deprecation_notice` | bitbucket | guide | https://developer.atlassian.com/cloud/bitbucket/deprecation-notice-v1-apis/ | Bitbucket v1 API deprecation notice covering the removal of /1.0/users/{accountname} and other legacy account resources. |
| `bitbucket_workspaces_ref` | bitbucket | reference | https://developer.atlassian.com/cloud/bitbucket/rest/api-group-workspaces/ | Bitbucket workspaces reference covering workspace retrieval and workspace member listing endpoints. |
| `confluence_v1_content_ref` | confluence | reference | https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-content/ | Confluence v1 content reference covering content get, update, search, and child-page style endpoints. |
| `confluence_v1_space_ref` | confluence | reference | https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-space/ | Confluence v1 space reference used for legacy spaceKey-centric lookups. |
| `confluence_v1_v2_notice` | confluence | guide | https://community.developer.atlassian.com/t/deprecating-many-confluence-v1-apis-that-have-v2-equivalents/66883 | Confluence Cloud advance notice describing the migration from v1 content endpoints to v2 page and space endpoints, including cursor pagination and multi-step replacements. |
| `confluence_v2_children_ref` | confluence | reference | https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-children/ | Confluence v2 children reference covering /pages/{id}/children and cursor pagination. |
| `confluence_v2_page_ref` | confluence | reference | https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-page/ | Confluence v2 page reference covering page get, create, title update, and body-format query parameters. |
| `confluence_v2_space_ref` | confluence | reference | https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-space/ | Confluence v2 space reference covering /spaces and key-based space lookup separate from page listing by spaceId. |
| `drive_enable_shared_drives_guide` | drive | guide | https://developers.google.com/workspace/drive/api/guides/enable-shareddrives | Drive guide for shared drive support and the all-drives parameter surface. |
| `drive_folder_guide` | drive | guide | https://developers.google.com/workspace/drive/api/guides/folder | Drive folder guide stating that a file can only have one parent folder. |
| `drive_shortcuts_guide` | drive | guide | https://developers.google.com/workspace/drive/api/guides/shortcuts | Drive shortcuts guide describing shortcuts as separate files linking to targets rather than extra parents. |
| `drive_v2_files_list_ref` | drive | reference | https://developers.google.com/workspace/drive/api/reference/rest/v2/files/list | Drive v2 files.list reference containing legacy Team Drive parameters such as teamDriveId and includeTeamDriveItems. |
| `drive_v2_parents_delete_ref` | drive | reference | https://developers.google.com/workspace/drive/api/reference/rest/v2/parents/delete | Drive v2 parents.delete reference describing the legacy remove-parent operation. |
| `drive_v2_parents_insert_ref` | drive | reference | https://developers.google.com/workspace/drive/api/reference/rest/v2/parents/insert | Drive v2 parents.insert reference describing the legacy add-parent operation. |
| `drive_v2_to_v3_ref` | drive | guide | https://developers.google.com/workspace/drive/api/guides/v2-to-v3-reference | Drive v2-to-v3 reference mapping parents.insert/delete onto files.update addParents/removeParents. |
| `drive_v3_files_list_ref` | drive | reference | https://developers.google.com/workspace/drive/api/reference/rest/v3/files/list | Drive v3 files.list reference containing shared drive parameters such as driveId and includeItemsFromAllDrives. |
| `drive_v3_files_update_ref` | drive | reference | https://developers.google.com/workspace/drive/api/reference/rest/v3/files/update | Drive v3 files.update reference containing addParents, removeParents, and the single-parent deprecation notice. |
| `jira_privacy_migration_guide` | jira | guide | https://developer.atlassian.com/cloud/jira/platform/deprecation-notice-user-privacy-api-migration-guide/ | Jira Cloud privacy migration guide replacing username and userKey with accountId and query-based user lookup. |
| `jira_v2_issue_assignees_ref` | jira | reference | https://developer.atlassian.com/cloud/jira/platform/rest/v2/api-group-issue-assignees/ | Jira v2 issue assignee reference used as the legacy anchor for username-style assignment. |
| `jira_v2_issue_watchers_ref` | jira | reference | https://developer.atlassian.com/cloud/jira/platform/rest/v2/api-group-issue-watchers/ | Jira v2 issue watchers reference used as the legacy anchor for username-style watcher changes. |
| `jira_v2_user_search_ref` | jira | reference | https://developer.atlassian.com/cloud/jira/platform/rest/v2/api-group-user-search/ | Jira v2 user-search reference used as the legacy username-search anchor. |
| `jira_v3_issue_assignees_ref` | jira | reference | https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-assignees/ | Jira v3 issue assignee reference using accountId-based assignment. |
| `jira_v3_issue_watchers_ref` | jira | reference | https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-watchers/ | Jira v3 issue watchers reference using accountId-based watcher changes. |
| `jira_v3_user_search_ref` | jira | reference | https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-user-search/ | Jira v3 user-search reference using query and accountId-oriented lookup. |
| `notion_2022_02_22` | notion | changelog | https://developers.notion.com/changelog/releasing-notion-version-2022-02-22 | Historical Notion version note that moved rich text handling from legacy text fields to rich_text. |
| `notion_2025_09_03` | notion | changelog | https://developers.notion.com/changelog/unversioned-requests-no-longer-accepted | Notion 2025-09-03 version note that deprecates /databases endpoints in favor of data sources and search-based discovery. |
| `notion_append_blocks_ref` | notion | reference | https://developers.notion.com/reference/patch-block-children | Current Append block children reference using paragraph.rich_text arrays. |
| `notion_data_source_query_ref` | notion | reference | https://developers.notion.com/reference/query-a-data-source | Current Query a data source reference for the 2025-09-03 split. |
| `notion_database_query_ref` | notion | reference | https://developers.notion.com/reference/post-database-query | Legacy Query a database reference, kept here as the pre-2025-09-03 clean view anchor. |
| `notion_get_databases_ref` | notion | reference | https://developers.notion.com/reference/get-databases | Deprecated Get databases reference, retained here as the legacy clean view anchor. |
| `notion_post_page_ref` | notion | reference | https://developers.notion.com/reference/post-page | Current Create a page reference after the database/data-source split. |
| `notion_search_ref` | notion | reference | https://developers.notion.com/reference/post-search | Current Search reference returning pages and data sources, not a direct drop-in replacement for the old shared-database listing semantics. |
| `notion_upgrade_2025_09_03` | notion | guide | https://developers.notion.com/guides/get-started/upgrade-guide-2025-09-03 | Official upgrade guide describing the 2025-09-03 database to data-source transition and parent changes. |
| `people_connections_list_ref` | people | reference | https://developers.google.com/people/api/rest/v1/people.connections/list | People API people.connections.list reference for listing My Contacts with personFields. |
| `people_contact_groups_list_ref` | people | reference | https://developers.google.com/people/api/rest/v1/contactGroups/list | People API contactGroups.list reference for listing contact groups with groupFields. |
| `people_contacts_migration_guide` | people | guide | https://developers.google.com/people/contacts-api-migration | Google Contacts API to People API migration guide covering contacts feed replacement, contact group migration, and read-only Other Contacts. |
| `people_create_contact_ref` | people | reference | https://developers.google.com/people/api/rest/v1/people/createContact | People API people.createContact reference for creating a new contact. |
| `people_other_contacts_copy_ref` | people | reference | https://developers.google.com/people/api/rest/v1/otherContacts/copyOtherContactToMyContactsGroup | People API otherContacts.copyOtherContactToMyContactsGroup reference used when an Other Contact must first become a My Contact before mutation. |
| `people_update_contact_ref` | people | reference | https://developers.google.com/people/api/rest/v1/people/updateContact | People API people.updateContact reference for modifying contact-based people with updatePersonFields. |
| `sheets_v3_v4_migration_guide` | sheets | guide | https://developers.google.com/workspace/sheets/api/guides/migration | Google Sheets v3-to-v4 migration guide covering worksheets feed, list feed, cells feed, and removed spreadsheet-list operations. |
| `sheets_v4_spreadsheets_get_ref` | sheets | reference | https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets/get | Sheets v4 spreadsheets.get reference documenting field masks such as sheets.properties.title. |
| `sheets_v4_values_append_ref` | sheets | reference | https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets.values/append | Sheets v4 spreadsheets.values.append reference for appending rows. |
| `sheets_v4_values_update_ref` | sheets | reference | https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets.values/update | Sheets v4 spreadsheets.values.update reference for overwriting cells or ranges with RAW or USER_ENTERED interpretation. |
| `slack_channels_create_ref` | slack | reference | https://docs.slack.dev/reference/methods/channels.create/ | Legacy channels.create reference for creating a public channel. |
| `slack_channels_list_ref` | slack | reference | https://docs.slack.dev/reference/methods/channels.list/ | Legacy channels.list reference for listing channels in a workspace. |
| `slack_conversations_2018` | slack | changelog | https://docs.slack.dev/changelog/2018/06/01/conversations-apis-and-more/ | Slack changelog introducing Conversations APIs as the unified replacement surface for legacy channel, group, im, and mpim methods. |
| `slack_conversations_create_ref` | slack | reference | https://docs.slack.dev/reference/methods/conversations.create/ | Current conversations.create reference for creating public or private channels. |
| `slack_conversations_list_ref` | slack | reference | https://docs.slack.dev/reference/methods/conversations.list/ | Current conversations.list reference that supersedes legacy listing methods. |
| `slack_conversations_open_ref` | slack | reference | https://docs.slack.dev/reference/methods/conversations.open/ | Current conversations.open reference for opening or resuming direct or multi-person direct messages. |
| `slack_files_upload_ref` | slack | reference | https://docs.slack.dev/reference/methods/files.upload/ | Current files.upload reference marking the method deprecated and redirecting developers to the external upload flow. |
| `slack_mpim_open_ref` | slack | reference | https://docs.slack.dev/reference/methods/mpim.open/ | Legacy mpim.open reference for opening or resuming a multi-person DM. |
| `stripe_2018_subscription_source_removed` | stripe | changelog | https://docs.stripe.com/changelog/2018-07-27/subscriptions-no-longer-support-modifying-source | Stripe changelog removing direct subscription source updates and redirecting callers to customer source management. |
| `stripe_2018_tax_info` | stripe | changelog | https://docs.stripe.com/changelog/2018-08-23 | Stripe changelog entry introducing tax_info on customer creation. |
| `stripe_2019_tax_id_data` | stripe | changelog | https://docs.stripe.com/changelog/2019-12-03/removes-deprecated-tax-information-fields | Stripe changelog removing deprecated tax_info fields and moving callers to tax_id_data. |
| `stripe_2022_checkout_discounts` | stripe | changelog | https://docs.stripe.com/changelog/2022-08-01/removes-subscription-data-create-checkout-session | Stripe changelog replacing subscription_data[coupon] with discounts on Checkout Session creation. |
| `stripe_2025_total_count` | stripe | changelog | https://docs.stripe.com/changelog/basil/2025-03-31/deprecate-total-count-expansion | Stripe changelog deprecating expansion of total_count on list APIs. |
| `stripe_checkout_session_create_ref` | stripe | reference | https://docs.stripe.com/api/checkout/sessions/create | Current Create Checkout Session reference documenting discounts. |
| `stripe_customers_create_ref` | stripe | reference | https://docs.stripe.com/api/customers/create | Current Create customer reference that documents tax_id_data. |
| `stripe_subscriptions_update_ref` | stripe | reference | https://docs.stripe.com/api/subscriptions/update | Current Update subscription reference after removal of the legacy source parameter. |

## Cases

### `bitbucket_get_legacy_account`

- Family: `bitbucket`
- Request: Get the Bitbucket legacy account object for account name eng-team, even if it could refer to either a user or a team.
- Notes: sources=bitbucket_v1_deprecation_notice,bitbucket_teams_workspaces_notice,bitbucket_workspaces_ref,bitbucket_users_ref;pair=legacy_account_union_removed

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `bitbucket_get_legacy_account::clean` | `clean` | `clean` | `execute` | Legacy Bitbucket account lookup schema using /1.0/users/{accountname}. |
| `bitbucket_get_legacy_account::negative_account_object_removed` | `negative_near_orbit` | `negative_account_object_removed` | `ask_clarification, abstain` | Real negative near-orbit: Bitbucket no longer exposes a single account endpoint that can return either a user or a team for a legacy account name. |

### `bitbucket_get_workspace`

- Family: `bitbucket`
- Request: Get the Bitbucket workspace profile for eng-team.
- Notes: sources=bitbucket_teams_workspaces_notice,bitbucket_workspaces_ref;pair=team_get_to_workspace_get

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `bitbucket_get_workspace::clean` | `clean` | `clean` | `execute` | Legacy Bitbucket team profile schema using /2.0/teams/{username}. |
| `bitbucket_get_workspace::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: Bitbucket team profile lookup moved from /2.0/teams/{username} to /2.0/workspaces/{workspace}. |

### `bitbucket_list_workspace_members`

- Family: `bitbucket`
- Request: List the members of Bitbucket workspace eng-team.
- Notes: sources=bitbucket_teams_workspaces_notice,bitbucket_workspaces_ref;pair=team_members_to_workspace_members

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `bitbucket_list_workspace_members::clean` | `clean` | `clean` | `execute` | Legacy Bitbucket team member listing schema. |
| `bitbucket_list_workspace_members::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: Bitbucket member listing moved from team-centric to workspace-centric endpoints. |

### `bitbucket_list_workspace_repositories`

- Family: `bitbucket`
- Request: List the repositories in Bitbucket workspace eng-team.
- Notes: sources=bitbucket_teams_workspaces_notice,bitbucket_repositories_ref;pair=team_repositories_to_workspace_repositories

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `bitbucket_list_workspace_repositories::clean` | `clean` | `clean` | `execute` | Legacy Bitbucket team repository listing schema. |
| `bitbucket_list_workspace_repositories::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: Bitbucket repository listing moved from /2.0/teams/{username}/repositories to /2.0/repositories/{workspace}. |

### `confluence_get_page_storage`

- Family: `confluence`
- Request: Get Confluence page 2001 including its storage body.
- Notes: sources=confluence_v1_content_ref,confluence_v2_page_ref,confluence_v1_v2_notice;pair=content_get_expand_to_pages_body_format

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `confluence_get_page_storage::clean` | `clean` | `clean` | `execute` | Legacy Confluence v1 content get schema using expand=body.storage. |
| `confluence_get_page_storage::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: Confluence page retrieval moved from v1 expand=body.storage to v2 body-format=storage. |

### `confluence_list_page_children`

- Family: `confluence`
- Request: List the child pages under Confluence page 2001.
- Notes: sources=confluence_v1_content_ref,confluence_v2_children_ref,confluence_v1_v2_notice;pair=content_child_page_to_pages_children

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `confluence_list_page_children::clean` | `clean` | `clean` | `execute` | Legacy Confluence v1 child page listing schema. |
| `confluence_list_page_children::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: Confluence child page listing moved to /wiki/api/v2/pages/{id}/children. |

### `confluence_list_pages_by_space_key`

- Family: `confluence`
- Request: List the Confluence pages in space key ENG.
- Notes: sources=confluence_v1_space_ref,confluence_v2_space_ref,confluence_v2_page_ref,confluence_v1_v2_notice;pair=space_key_lookup_split

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `confluence_list_pages_by_space_key::clean` | `clean` | `clean` | `execute` | Legacy Confluence v1 page listing schema using a spaceKey filter. |
| `confluence_list_pages_by_space_key::negative_space_key_lookup_split` | `negative_near_orbit` | `negative_space_key_lookup_split` | `ask_clarification, abstain` | Real negative near-orbit: Confluence v2 page listing expects a numeric spaceId, so a raw space key now requires a separate space lookup step. |

### `confluence_update_page_title`

- Family: `confluence`
- Request: Rename Confluence page 2001 to 'Sprint Plan'.
- Notes: sources=confluence_v1_content_ref,confluence_v2_page_ref,confluence_v1_v2_notice;pair=content_update_to_page_title_endpoint

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `confluence_update_page_title::clean` | `clean` | `clean` | `execute` | Legacy Confluence v1 content update schema for title changes. |
| `confluence_update_page_title::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: Confluence title updates moved from generic content update to the dedicated v2 page title endpoint. |

### `drive_add_file_to_second_folder`

- Family: `drive`
- Request: Also place file file_plan in folder fld_reports while keeping it in folder fld_eng.
- Notes: sources=drive_v2_parents_insert_ref,drive_v3_files_update_ref,drive_folder_guide,drive_shortcuts_guide;pair=single_parent_shortcut_replacement

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `drive_add_file_to_second_folder::clean` | `clean` | `clean` | `execute` | Legacy Drive parent insertion schema before the single-parent restriction mattered for this request. |
| `drive_add_file_to_second_folder::negative_shortcut_replacement` | `negative_near_orbit` | `negative_shortcut_replacement` | `ask_clarification, abstain` | Real negative near-orbit: Drive no longer supports adding the same file to multiple folders; shortcuts are a related but not exact replacement. |

### `drive_add_parent_to_file`

- Family: `drive`
- Request: Place file file_brief in folder fld_reports.
- Notes: sources=drive_v2_parents_insert_ref,drive_v2_to_v3_ref,drive_v3_files_update_ref;pair=parents_insert_to_files_update_add_parents

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `drive_add_parent_to_file::clean` | `clean` | `clean` | `execute` | Legacy Drive parent insertion schema via parents.insert. |
| `drive_add_parent_to_file::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: Drive parent insertion moved from parents.insert to files.update addParents. |

### `drive_list_shared_drive_items`

- Family: `drive`
- Request: List the files in shared drive drv_eng.
- Notes: sources=drive_v2_files_list_ref,drive_v3_files_list_ref,drive_enable_shared_drives_guide;pair=team_drives_to_shared_drives_list

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `drive_list_shared_drive_items::clean` | `clean` | `clean` | `execute` | Legacy Drive list schema using Team Drive parameters. |
| `drive_list_shared_drive_items::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: Drive list parameters moved from Team Drive names to shared drive names. |

### `drive_remove_parent_from_file`

- Family: `drive`
- Request: Remove file file_archive from folder fld_archive.
- Notes: sources=drive_v2_parents_delete_ref,drive_v2_to_v3_ref,drive_v3_files_update_ref;pair=parents_delete_to_files_update_remove_parents

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `drive_remove_parent_from_file::clean` | `clean` | `clean` | `execute` | Legacy Drive parent removal schema via parents.delete. |
| `drive_remove_parent_from_file::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: Drive parent removal moved from parents.delete to files.update removeParents. |

### `jira_add_issue_watcher_user_ref`

- Family: `jira`
- Request: Add Jira user token acct_alice as a watcher on issue ENG-7.
- Notes: sources=jira_privacy_migration_guide,jira_v2_issue_watchers_ref,jira_v3_issue_watchers_ref;pair=username_to_accountid_watcher

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `jira_add_issue_watcher_user_ref::clean` | `clean` | `clean` | `execute` | Legacy Jira watcher schema using username-style identifiers. |
| `jira_add_issue_watcher_user_ref::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: Jira issue watcher changes moved from username-style identifiers to accountId. |

### `jira_assign_issue_user_ref`

- Family: `jira`
- Request: Assign issue ENG-7 to Jira user token acct_alice.
- Notes: sources=jira_privacy_migration_guide,jira_v2_issue_assignees_ref,jira_v3_issue_assignees_ref;pair=username_to_accountid_assignment

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `jira_assign_issue_user_ref::clean` | `clean` | `clean` | `execute` | Legacy Jira assignment schema using username-style identifiers. |
| `jira_assign_issue_user_ref::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: Jira issue assignment moved from username-style identifiers to accountId. |

### `jira_search_assignable_user_legacy_username`

- Family: `jira`
- Request: Find the assignable Jira user in project ENG with legacy username alice.
- Notes: sources=jira_privacy_migration_guide,jira_v2_user_search_ref,jira_v3_user_search_ref;pair=legacy_username_search_removed

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `jira_search_assignable_user_legacy_username::clean` | `clean` | `clean` | `execute` | Legacy Jira assignable-user search schema where username lookup was still supported. |
| `jira_search_assignable_user_legacy_username::negative_legacy_identifier_removed` | `negative_near_orbit` | `negative_legacy_identifier_removed` | `ask_clarification, abstain` | Real negative near-orbit: Jira no longer supports username or userKey as stable user identifiers in query-based lookup. |

### `jira_search_assignable_user_query`

- Family: `jira`
- Request: Find the assignable Jira user in project ENG matching user token acct_alice.
- Notes: sources=jira_privacy_migration_guide,jira_v2_user_search_ref,jira_v3_user_search_ref;pair=username_to_query_search

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `jira_search_assignable_user_query::clean` | `clean` | `clean` | `execute` | Legacy Jira assignable-user search schema using username. |
| `jira_search_assignable_user_query::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: Jira assignable-user search moved from username to query-based lookup. |

### `notion_append_paragraph_block`

- Family: `notion`
- Request: Append a paragraph saying 'Ship the proposal draft today.' under block blk_123.
- Notes: sources=notion_2022_02_22,notion_append_blocks_ref;pair=legacy_text_to_rich_text

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `notion_append_paragraph_block::clean` | `clean` | `clean` | `execute` | Legacy Notion block append schema before the rich_text migration. |
| `notion_append_paragraph_block::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: append block children moved paragraph content from text to rich_text. |

### `notion_create_page_in_database`

- Family: `notion`
- Request: Create a page titled 'Review backlog' in database db_tasks.
- Notes: sources=notion_post_page_ref,notion_upgrade_2025_09_03;pair=database_parent_to_data_source_parent

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `notion_create_page_in_database::clean` | `clean` | `clean` | `execute` | Legacy Notion page creation schema using a database parent. |
| `notion_create_page_in_database::negative_parent_scope_change` | `negative_near_orbit` | `negative_parent_scope_change` | `ask_clarification, abstain` | Real negative near-orbit: a database identifier alone no longer resolves the exact parent after the database to data-source split. |

### `notion_list_shared_databases`

- Family: `notion`
- Request: List the databases shared directly with this integration.
- Notes: sources=notion_get_databases_ref,notion_2025_09_03,notion_search_ref;pair=list_databases_to_search

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `notion_list_shared_databases::clean` | `clean` | `clean` | `execute` | Legacy Notion databases listing endpoint before the 2025-09-03 split. |
| `notion_list_shared_databases::negative_search_replacement` | `negative_near_orbit` | `negative_search_replacement` | `ask_clarification, abstain` | Real negative near-orbit: search remains visible but does not exactly preserve the old shared-database listing contract. |

### `notion_query_overdue_entries`

- Family: `notion`
- Request: Query entries in container db_tasks where status is overdue.
- Notes: sources=notion_database_query_ref,notion_data_source_query_ref,notion_upgrade_2025_09_03;pair=database_query_to_data_source_query

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `notion_query_overdue_entries::clean` | `clean` | `clean` | `execute` | Legacy Notion database query schema. |
| `notion_query_overdue_entries::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: database query moved to data source query in the 2025-09-03 split. |

### `people_create_contact`

- Family: `people`
- Request: Create a Google contact named Alice Example with email alice@example.com.
- Notes: sources=people_contacts_migration_guide,people_create_contact_ref;pair=contacts_feed_insert_to_people_create_contact

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `people_create_contact::clean` | `clean` | `clean` | `execute` | Legacy Google Contacts feed contact creation schema. |
| `people_create_contact::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: contact creation moved from contacts feed insert to people.createContact. |

### `people_list_contact_groups`

- Family: `people`
- Request: List my Google contact groups.
- Notes: sources=people_contacts_migration_guide,people_contact_groups_list_ref;pair=groups_feed_to_contactgroups_list

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `people_list_contact_groups::clean` | `clean` | `clean` | `execute` | Legacy Google Contacts groups feed schema. |
| `people_list_contact_groups::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: groups feed listing moved to contactGroups.list. |

### `people_list_my_contacts`

- Family: `people`
- Request: List my first 10 personal Google contacts with names and email addresses.
- Notes: sources=people_contacts_migration_guide,people_connections_list_ref;pair=contacts_feed_to_people_connections_list

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `people_list_my_contacts::clean` | `clean` | `clean` | `execute` | Legacy Google Contacts feed listing schema. |
| `people_list_my_contacts::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: contacts feed listing moved to people.connections.list with personFields. |

### `people_update_other_contact_email`

- Family: `people`
- Request: Update Other Contact oc_alice to email alice.new@example.com.
- Notes: sources=people_contacts_migration_guide,people_update_contact_ref,people_other_contacts_copy_ref;pair=other_contacts_read_only_capability_gap

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `people_update_other_contact_email::clean` | `clean` | `clean` | `execute` | Legacy contacts-feed style schema for updating a stored contact email. |
| `people_update_other_contact_email::negative_other_contacts_read_only` | `negative_near_orbit` | `negative_other_contacts_read_only` | `ask_clarification, abstain` | Real negative near-orbit: People API treats Other Contacts as read-only, so direct mutation is no longer available as a one-step update. |

### `sheets_append_row`

- Family: `sheets`
- Request: Append row 'Elizabeth,42' to worksheet ws_hours in spreadsheet sh_budget.
- Notes: sources=sheets_v3_v4_migration_guide,sheets_v4_values_append_ref;pair=list_feed_post_to_values_append

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `sheets_append_row::clean` | `clean` | `clean` | `execute` | Legacy Sheets list feed for appending a new row. |
| `sheets_append_row::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: list feed row insertion moved to spreadsheets.values.append. |

### `sheets_get_sheet_titles`

- Family: `sheets`
- Request: List the sheet titles in spreadsheet sh_budget.
- Notes: sources=sheets_v3_v4_migration_guide,sheets_v4_spreadsheets_get_ref;pair=worksheets_feed_to_spreadsheets_get_fields

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `sheets_get_sheet_titles::clean` | `clean` | `clean` | `execute` | Legacy Sheets worksheets feed for retrieving sheet titles. |
| `sheets_get_sheet_titles::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: worksheets feed retrieval moved to spreadsheets.get with a fields mask. |

### `sheets_list_accessible_spreadsheets`

- Family: `sheets`
- Request: List the spreadsheets accessible by the authenticated user.
- Notes: sources=sheets_v3_v4_migration_guide,drive_v3_files_list_ref;pair=spreadsheets_feed_removed_in_v4

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `sheets_list_accessible_spreadsheets::clean` | `clean` | `clean` | `execute` | Legacy Sheets spreadsheets feed for listing accessible spreadsheets. |
| `sheets_list_accessible_spreadsheets::negative_drive_scope_replacement` | `negative_near_orbit` | `negative_drive_scope_replacement` | `ask_clarification, abstain` | Real negative near-orbit: Sheets API v4 does not provide the old spreadsheets-feed listing operation; Drive files.list is related but not a drop-in replacement. |

### `sheets_update_formula`

- Family: `sheets`
- Request: Set cell ws_summary!A1 in spreadsheet sh_budget to =SUM(B1:B3).
- Notes: sources=sheets_v3_v4_migration_guide,sheets_v4_values_update_ref;pair=cells_feed_put_to_values_update

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `sheets_update_formula::clean` | `clean` | `clean` | `execute` | Legacy Sheets cells feed update schema. |
| `sheets_update_formula::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: cells feed updates moved to spreadsheets.values.update with USER_ENTERED formulas. |

### `slack_create_public_channel`

- Family: `slack`
- Request: Create a public channel named release-updates.
- Notes: sources=slack_conversations_2018,slack_channels_create_ref,slack_conversations_create_ref;pair=channels_create_to_conversations_create

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `slack_create_public_channel::clean` | `clean` | `clean` | `execute` | Legacy Slack channels.create schema. |
| `slack_create_public_channel::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: legacy channels.create capability now lives under conversations.create. |

### `slack_list_channels`

- Family: `slack`
- Request: List the workspace channels.
- Notes: sources=slack_conversations_2018,slack_channels_list_ref,slack_conversations_list_ref;pair=channels_list_to_conversations_list

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `slack_list_channels::clean` | `clean` | `clean` | `execute` | Legacy Slack channels.list schema. |
| `slack_list_channels::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: legacy channels.list capability now lives under conversations.list. |

### `slack_open_group_dm`

- Family: `slack`
- Request: Open or resume a group DM for users U123,U456.
- Notes: sources=slack_conversations_2018,slack_mpim_open_ref,slack_conversations_open_ref;pair=mpim_open_to_conversations_open

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `slack_open_group_dm::clean` | `clean` | `clean` | `execute` | Legacy Slack mpim.open schema. |
| `slack_open_group_dm::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: legacy mpim.open capability now lives under conversations.open. |

### `slack_upload_file_to_channel`

- Family: `slack`
- Request: Upload /tmp/spec.pdf to channel C123 with title 'Spec Draft'.
- Notes: sources=slack_files_upload_ref;pair=files_upload_to_external_upload_flow

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `slack_upload_file_to_channel::clean` | `clean` | `clean` | `execute` | Legacy Slack one-shot file upload schema. |
| `slack_upload_file_to_channel::negative_deprecate` | `negative_near_orbit` | `negative_deprecate` | `abstain` | Real negative near-orbit: files.upload is explicitly deprecated, with no one-shot substitute exposed in this view. |

### `stripe_create_checkout_session_with_coupon`

- Family: `stripe`
- Request: Create a subscription Checkout Session for price price_premium using coupon coupon_20off.
- Notes: sources=stripe_2022_checkout_discounts,stripe_checkout_session_create_ref;pair=subscription_data_coupon_to_discounts

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `stripe_create_checkout_session_with_coupon::clean` | `clean` | `clean` | `execute` | Legacy Stripe Checkout Session schema using subscription_data[coupon]. |
| `stripe_create_checkout_session_with_coupon::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: Checkout Session coupon input moved from subscription_data[coupon] to discounts. |

### `stripe_create_customer_with_tax_id`

- Family: `stripe`
- Request: Create a customer for finance@example.com with EU VAT ID DE123456789.
- Notes: sources=stripe_2018_tax_info,stripe_2019_tax_id_data,stripe_customers_create_ref;pair=tax_info_to_tax_id_data

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `stripe_create_customer_with_tax_id::clean` | `clean` | `clean` | `execute` | Legacy Stripe customer creation schema using tax_info. |
| `stripe_create_customer_with_tax_id::positive_version_migration` | `positive_orbit` | `positive_version_migration` | `execute` | Real version migration: Stripe customer creation moved from tax_info to tax_id_data. |

### `stripe_list_customers_total_count`

- Family: `stripe`
- Request: List 25 customers and include the total count.
- Notes: sources=stripe_2025_total_count;pair=legacy_total_count_expansion_removed

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `stripe_list_customers_total_count::clean` | `clean` | `clean` | `execute` | Legacy Stripe list API where total_count expansion was still supported. |
| `stripe_list_customers_total_count::negative_removed_capability` | `negative_near_orbit` | `negative_removed_capability` | `ask_clarification, abstain` | Real negative near-orbit: total_count is removed from list responses, so the original request is no longer satisfiable as-is. |

### `stripe_update_subscription_source`

- Family: `stripe`
- Request: Update subscription sub_123 to use source src_456.
- Notes: sources=stripe_2018_subscription_source_removed,stripe_subscriptions_update_ref;pair=subscription_source_removed

| View ID | Shift | Transform | Admissible | Notes |
| --- | --- | --- | --- | --- |
| `stripe_update_subscription_source::clean` | `clean` | `clean` | `execute` | Legacy Stripe subscription update schema with a direct source parameter. |
| `stripe_update_subscription_source::negative_source_removed` | `negative_near_orbit` | `negative_source_removed` | `ask_clarification, abstain` | Real negative near-orbit: Stripe removed the direct subscription source parameter, so the old one-step update is no longer available. |

