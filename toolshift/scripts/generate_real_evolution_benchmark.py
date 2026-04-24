#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _canonical_arg(
    canonical_name: str,
    description: str,
    arg_type: str,
    *,
    required: bool = True,
    enum_values: list[str] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "canonical_name": canonical_name,
        "description": description,
        "arg_type": arg_type,
        "required": required,
    }
    if enum_values:
        payload["enum_values"] = enum_values
    return payload


def _canonical_tool(
    tool_id: str,
    description: str,
    arguments: list[dict[str, object]],
    *,
    semantic_tags: list[str],
) -> dict[str, object]:
    return {
        "tool_id": tool_id,
        "description": description,
        "arguments": arguments,
        "semantic_tags": semantic_tags,
    }


def _rendered_arg(
    rendered_name: str,
    canonical_name: str,
    description: str,
    arg_type: str,
    *,
    required: bool = True,
    enum_values: list[str] | None = None,
    position: int = 0,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "rendered_name": rendered_name,
        "canonical_name": canonical_name,
        "description": description,
        "arg_type": arg_type,
        "required": required,
        "position": position,
    }
    if enum_values:
        payload["enum_values"] = enum_values
    return payload


def _rendered_tool(
    canonical_tool_id: str,
    rendered_name: str,
    description: str,
    arguments: list[dict[str, object]],
    *,
    status: str = "active",
) -> dict[str, object]:
    return {
        "canonical_tool_id": canonical_tool_id,
        "rendered_name": rendered_name,
        "description": description,
        "status": status,
        "arguments": arguments,
    }


def _action(tool_id: str | None = None, **arguments) -> dict[str, object]:
    if tool_id is None:
        return {"control": "abstain"}
    return {
        "control": "execute",
        "tool_id": tool_id,
        "arguments": arguments,
    }


def _ask() -> dict[str, object]:
    return {"control": "ask_clarification"}


def _abstain() -> dict[str, object]:
    return {"control": "abstain"}


def _case(
    *,
    case_id: str,
    request: str,
    tool_ids: list[str],
    slot_values: dict[str, object],
    action: dict[str, object],
    family_tag: str,
    notes: str,
) -> dict[str, object]:
    return {
        "case_id": case_id,
        "request": request,
        "tool_ids": tool_ids,
        "slot_values": slot_values,
        "admissible_actions": [action],
        "family_tag": family_tag,
        "notes": notes,
    }


def _view(
    *,
    case_id: str,
    view_id: str,
    transform_name: str,
    shift_kind: str,
    tools: list[dict[str, object]],
    notes: str,
    admissible_actions: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "case_id": case_id,
        "schema_view": {
            "view_id": view_id,
            "transform_name": transform_name,
            "shift_kind": shift_kind,
            "tools": tools,
            "notes": notes,
        },
        "notes": notes,
    }
    if admissible_actions is not None:
        payload["admissible_actions"] = admissible_actions
    return payload


def build_sources() -> dict[str, dict[str, str]]:
    return {
        "notion_2022_02_22": {
            "vendor": "notion",
            "kind": "changelog",
            "url": "https://developers.notion.com/changelog/releasing-notion-version-2022-02-22",
            "summary": "Historical Notion version note that moved rich text handling from legacy text fields to rich_text.",
        },
        "notion_append_blocks_ref": {
            "vendor": "notion",
            "kind": "reference",
            "url": "https://developers.notion.com/reference/patch-block-children",
            "summary": "Current Append block children reference using paragraph.rich_text arrays.",
        },
        "notion_2025_09_03": {
            "vendor": "notion",
            "kind": "changelog",
            "url": "https://developers.notion.com/changelog/unversioned-requests-no-longer-accepted",
            "summary": "Notion 2025-09-03 version note that deprecates /databases endpoints in favor of data sources and search-based discovery.",
        },
        "notion_get_databases_ref": {
            "vendor": "notion",
            "kind": "reference",
            "url": "https://developers.notion.com/reference/get-databases",
            "summary": "Deprecated Get databases reference, retained here as the legacy clean view anchor.",
        },
        "notion_search_ref": {
            "vendor": "notion",
            "kind": "reference",
            "url": "https://developers.notion.com/reference/post-search",
            "summary": "Current Search reference returning pages and data sources, not a direct drop-in replacement for the old shared-database listing semantics.",
        },
        "notion_database_query_ref": {
            "vendor": "notion",
            "kind": "reference",
            "url": "https://developers.notion.com/reference/post-database-query",
            "summary": "Legacy Query a database reference, kept here as the pre-2025-09-03 clean view anchor.",
        },
        "notion_data_source_query_ref": {
            "vendor": "notion",
            "kind": "reference",
            "url": "https://developers.notion.com/reference/query-a-data-source",
            "summary": "Current Query a data source reference for the 2025-09-03 split.",
        },
        "notion_post_page_ref": {
            "vendor": "notion",
            "kind": "reference",
            "url": "https://developers.notion.com/reference/post-page",
            "summary": "Current Create a page reference after the database/data-source split.",
        },
        "notion_upgrade_2025_09_03": {
            "vendor": "notion",
            "kind": "guide",
            "url": "https://developers.notion.com/guides/get-started/upgrade-guide-2025-09-03",
            "summary": "Official upgrade guide describing the 2025-09-03 database to data-source transition and parent changes.",
        },
        "slack_conversations_2018": {
            "vendor": "slack",
            "kind": "changelog",
            "url": "https://docs.slack.dev/changelog/2018/06/01/conversations-apis-and-more/",
            "summary": "Slack changelog introducing Conversations APIs as the unified replacement surface for legacy channel, group, im, and mpim methods.",
        },
        "slack_mpim_open_ref": {
            "vendor": "slack",
            "kind": "reference",
            "url": "https://docs.slack.dev/reference/methods/mpim.open/",
            "summary": "Legacy mpim.open reference for opening or resuming a multi-person DM.",
        },
        "slack_conversations_open_ref": {
            "vendor": "slack",
            "kind": "reference",
            "url": "https://docs.slack.dev/reference/methods/conversations.open/",
            "summary": "Current conversations.open reference for opening or resuming direct or multi-person direct messages.",
        },
        "slack_files_upload_ref": {
            "vendor": "slack",
            "kind": "reference",
            "url": "https://docs.slack.dev/reference/methods/files.upload/",
            "summary": "Current files.upload reference marking the method deprecated and redirecting developers to the external upload flow.",
        },
        "slack_channels_create_ref": {
            "vendor": "slack",
            "kind": "reference",
            "url": "https://docs.slack.dev/reference/methods/channels.create/",
            "summary": "Legacy channels.create reference for creating a public channel.",
        },
        "slack_conversations_create_ref": {
            "vendor": "slack",
            "kind": "reference",
            "url": "https://docs.slack.dev/reference/methods/conversations.create/",
            "summary": "Current conversations.create reference for creating public or private channels.",
        },
        "slack_channels_list_ref": {
            "vendor": "slack",
            "kind": "reference",
            "url": "https://docs.slack.dev/reference/methods/channels.list/",
            "summary": "Legacy channels.list reference for listing channels in a workspace.",
        },
        "slack_conversations_list_ref": {
            "vendor": "slack",
            "kind": "reference",
            "url": "https://docs.slack.dev/reference/methods/conversations.list/",
            "summary": "Current conversations.list reference that supersedes legacy listing methods.",
        },
        "stripe_2018_tax_info": {
            "vendor": "stripe",
            "kind": "changelog",
            "url": "https://docs.stripe.com/changelog/2018-08-23",
            "summary": "Stripe changelog entry introducing tax_info on customer creation.",
        },
        "stripe_2019_tax_id_data": {
            "vendor": "stripe",
            "kind": "changelog",
            "url": "https://docs.stripe.com/changelog/2019-12-03/removes-deprecated-tax-information-fields",
            "summary": "Stripe changelog removing deprecated tax_info fields and moving callers to tax_id_data.",
        },
        "stripe_customers_create_ref": {
            "vendor": "stripe",
            "kind": "reference",
            "url": "https://docs.stripe.com/api/customers/create",
            "summary": "Current Create customer reference that documents tax_id_data.",
        },
        "stripe_2025_total_count": {
            "vendor": "stripe",
            "kind": "changelog",
            "url": "https://docs.stripe.com/changelog/basil/2025-03-31/deprecate-total-count-expansion",
            "summary": "Stripe changelog deprecating expansion of total_count on list APIs.",
        },
        "stripe_2022_checkout_discounts": {
            "vendor": "stripe",
            "kind": "changelog",
            "url": "https://docs.stripe.com/changelog/2022-08-01/removes-subscription-data-create-checkout-session",
            "summary": "Stripe changelog replacing subscription_data[coupon] with discounts on Checkout Session creation.",
        },
        "stripe_checkout_session_create_ref": {
            "vendor": "stripe",
            "kind": "reference",
            "url": "https://docs.stripe.com/api/checkout/sessions/create",
            "summary": "Current Create Checkout Session reference documenting discounts.",
        },
        "stripe_2018_subscription_source_removed": {
            "vendor": "stripe",
            "kind": "changelog",
            "url": "https://docs.stripe.com/changelog/2018-07-27/subscriptions-no-longer-support-modifying-source",
            "summary": "Stripe changelog removing direct subscription source updates and redirecting callers to customer source management.",
        },
        "stripe_subscriptions_update_ref": {
            "vendor": "stripe",
            "kind": "reference",
            "url": "https://docs.stripe.com/api/subscriptions/update",
            "summary": "Current Update subscription reference after removal of the legacy source parameter.",
        },
        "drive_v2_files_list_ref": {
            "vendor": "drive",
            "kind": "reference",
            "url": "https://developers.google.com/workspace/drive/api/reference/rest/v2/files/list",
            "summary": "Drive v2 files.list reference containing legacy Team Drive parameters such as teamDriveId and includeTeamDriveItems.",
        },
        "drive_v3_files_list_ref": {
            "vendor": "drive",
            "kind": "reference",
            "url": "https://developers.google.com/workspace/drive/api/reference/rest/v3/files/list",
            "summary": "Drive v3 files.list reference containing shared drive parameters such as driveId and includeItemsFromAllDrives.",
        },
        "drive_enable_shared_drives_guide": {
            "vendor": "drive",
            "kind": "guide",
            "url": "https://developers.google.com/workspace/drive/api/guides/enable-shareddrives",
            "summary": "Drive guide for shared drive support and the all-drives parameter surface.",
        },
        "drive_v2_to_v3_ref": {
            "vendor": "drive",
            "kind": "guide",
            "url": "https://developers.google.com/workspace/drive/api/guides/v2-to-v3-reference",
            "summary": "Drive v2-to-v3 reference mapping parents.insert/delete onto files.update addParents/removeParents.",
        },
        "drive_v2_parents_insert_ref": {
            "vendor": "drive",
            "kind": "reference",
            "url": "https://developers.google.com/workspace/drive/api/reference/rest/v2/parents/insert",
            "summary": "Drive v2 parents.insert reference describing the legacy add-parent operation.",
        },
        "drive_v2_parents_delete_ref": {
            "vendor": "drive",
            "kind": "reference",
            "url": "https://developers.google.com/workspace/drive/api/reference/rest/v2/parents/delete",
            "summary": "Drive v2 parents.delete reference describing the legacy remove-parent operation.",
        },
        "drive_v3_files_update_ref": {
            "vendor": "drive",
            "kind": "reference",
            "url": "https://developers.google.com/workspace/drive/api/reference/rest/v3/files/update",
            "summary": "Drive v3 files.update reference containing addParents, removeParents, and the single-parent deprecation notice.",
        },
        "drive_folder_guide": {
            "vendor": "drive",
            "kind": "guide",
            "url": "https://developers.google.com/workspace/drive/api/guides/folder",
            "summary": "Drive folder guide stating that a file can only have one parent folder.",
        },
        "drive_shortcuts_guide": {
            "vendor": "drive",
            "kind": "guide",
            "url": "https://developers.google.com/workspace/drive/api/guides/shortcuts",
            "summary": "Drive shortcuts guide describing shortcuts as separate files linking to targets rather than extra parents.",
        },
        "jira_privacy_migration_guide": {
            "vendor": "jira",
            "kind": "guide",
            "url": "https://developer.atlassian.com/cloud/jira/platform/deprecation-notice-user-privacy-api-migration-guide/",
            "summary": "Jira Cloud privacy migration guide replacing username and userKey with accountId and query-based user lookup.",
        },
        "jira_v2_issue_assignees_ref": {
            "vendor": "jira",
            "kind": "reference",
            "url": "https://developer.atlassian.com/cloud/jira/platform/rest/v2/api-group-issue-assignees/",
            "summary": "Jira v2 issue assignee reference used as the legacy anchor for username-style assignment.",
        },
        "jira_v3_issue_assignees_ref": {
            "vendor": "jira",
            "kind": "reference",
            "url": "https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-assignees/",
            "summary": "Jira v3 issue assignee reference using accountId-based assignment.",
        },
        "jira_v2_issue_watchers_ref": {
            "vendor": "jira",
            "kind": "reference",
            "url": "https://developer.atlassian.com/cloud/jira/platform/rest/v2/api-group-issue-watchers/",
            "summary": "Jira v2 issue watchers reference used as the legacy anchor for username-style watcher changes.",
        },
        "jira_v3_issue_watchers_ref": {
            "vendor": "jira",
            "kind": "reference",
            "url": "https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-watchers/",
            "summary": "Jira v3 issue watchers reference using accountId-based watcher changes.",
        },
        "jira_v2_user_search_ref": {
            "vendor": "jira",
            "kind": "reference",
            "url": "https://developer.atlassian.com/cloud/jira/platform/rest/v2/api-group-user-search/",
            "summary": "Jira v2 user-search reference used as the legacy username-search anchor.",
        },
        "jira_v3_user_search_ref": {
            "vendor": "jira",
            "kind": "reference",
            "url": "https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-user-search/",
            "summary": "Jira v3 user-search reference using query and accountId-oriented lookup.",
        },
        "sheets_v3_v4_migration_guide": {
            "vendor": "sheets",
            "kind": "guide",
            "url": "https://developers.google.com/workspace/sheets/api/guides/migration",
            "summary": "Google Sheets v3-to-v4 migration guide covering worksheets feed, list feed, cells feed, and removed spreadsheet-list operations.",
        },
        "sheets_v4_spreadsheets_get_ref": {
            "vendor": "sheets",
            "kind": "reference",
            "url": "https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets/get",
            "summary": "Sheets v4 spreadsheets.get reference documenting field masks such as sheets.properties.title.",
        },
        "sheets_v4_values_append_ref": {
            "vendor": "sheets",
            "kind": "reference",
            "url": "https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets.values/append",
            "summary": "Sheets v4 spreadsheets.values.append reference for appending rows.",
        },
        "sheets_v4_values_update_ref": {
            "vendor": "sheets",
            "kind": "reference",
            "url": "https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets.values/update",
            "summary": "Sheets v4 spreadsheets.values.update reference for overwriting cells or ranges with RAW or USER_ENTERED interpretation.",
        },
        "people_contacts_migration_guide": {
            "vendor": "people",
            "kind": "guide",
            "url": "https://developers.google.com/people/contacts-api-migration",
            "summary": "Google Contacts API to People API migration guide covering contacts feed replacement, contact group migration, and read-only Other Contacts.",
        },
        "people_connections_list_ref": {
            "vendor": "people",
            "kind": "reference",
            "url": "https://developers.google.com/people/api/rest/v1/people.connections/list",
            "summary": "People API people.connections.list reference for listing My Contacts with personFields.",
        },
        "people_create_contact_ref": {
            "vendor": "people",
            "kind": "reference",
            "url": "https://developers.google.com/people/api/rest/v1/people/createContact",
            "summary": "People API people.createContact reference for creating a new contact.",
        },
        "people_contact_groups_list_ref": {
            "vendor": "people",
            "kind": "reference",
            "url": "https://developers.google.com/people/api/rest/v1/contactGroups/list",
            "summary": "People API contactGroups.list reference for listing contact groups with groupFields.",
        },
        "people_update_contact_ref": {
            "vendor": "people",
            "kind": "reference",
            "url": "https://developers.google.com/people/api/rest/v1/people/updateContact",
            "summary": "People API people.updateContact reference for modifying contact-based people with updatePersonFields.",
        },
        "people_other_contacts_copy_ref": {
            "vendor": "people",
            "kind": "reference",
            "url": "https://developers.google.com/people/api/rest/v1/otherContacts/copyOtherContactToMyContactsGroup",
            "summary": "People API otherContacts.copyOtherContactToMyContactsGroup reference used when an Other Contact must first become a My Contact before mutation.",
        },
        "confluence_v1_v2_notice": {
            "vendor": "confluence",
            "kind": "guide",
            "url": "https://community.developer.atlassian.com/t/deprecating-many-confluence-v1-apis-that-have-v2-equivalents/66883",
            "summary": "Confluence Cloud advance notice describing the migration from v1 content endpoints to v2 page and space endpoints, including cursor pagination and multi-step replacements.",
        },
        "confluence_v1_content_ref": {
            "vendor": "confluence",
            "kind": "reference",
            "url": "https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-content/",
            "summary": "Confluence v1 content reference covering content get, update, search, and child-page style endpoints.",
        },
        "confluence_v1_space_ref": {
            "vendor": "confluence",
            "kind": "reference",
            "url": "https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-space/",
            "summary": "Confluence v1 space reference used for legacy spaceKey-centric lookups.",
        },
        "confluence_v2_page_ref": {
            "vendor": "confluence",
            "kind": "reference",
            "url": "https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-page/",
            "summary": "Confluence v2 page reference covering page get, create, title update, and body-format query parameters.",
        },
        "confluence_v2_children_ref": {
            "vendor": "confluence",
            "kind": "reference",
            "url": "https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-children/",
            "summary": "Confluence v2 children reference covering /pages/{id}/children and cursor pagination.",
        },
        "confluence_v2_space_ref": {
            "vendor": "confluence",
            "kind": "reference",
            "url": "https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-space/",
            "summary": "Confluence v2 space reference covering /spaces and key-based space lookup separate from page listing by spaceId.",
        },
        "bitbucket_teams_workspaces_notice": {
            "vendor": "bitbucket",
            "kind": "guide",
            "url": "https://developer.atlassian.com/cloud/bitbucket/bitbucket-api-teams-deprecation/",
            "summary": "Bitbucket Cloud change notice deprecating /2.0/teams and related account endpoints in favor of /2.0/workspaces and workspace-based payloads.",
        },
        "bitbucket_v1_deprecation_notice": {
            "vendor": "bitbucket",
            "kind": "guide",
            "url": "https://developer.atlassian.com/cloud/bitbucket/deprecation-notice-v1-apis/",
            "summary": "Bitbucket v1 API deprecation notice covering the removal of /1.0/users/{accountname} and other legacy account resources.",
        },
        "bitbucket_workspaces_ref": {
            "vendor": "bitbucket",
            "kind": "reference",
            "url": "https://developer.atlassian.com/cloud/bitbucket/rest/api-group-workspaces/",
            "summary": "Bitbucket workspaces reference covering workspace retrieval and workspace member listing endpoints.",
        },
        "bitbucket_repositories_ref": {
            "vendor": "bitbucket",
            "kind": "reference",
            "url": "https://developer.atlassian.com/cloud/bitbucket/rest/api-group-repositories/",
            "summary": "Bitbucket repositories reference covering repository listing under a workspace.",
        },
        "bitbucket_projects_ref": {
            "vendor": "bitbucket",
            "kind": "reference",
            "url": "https://developer.atlassian.com/cloud/bitbucket/rest/api-group-projects/",
            "summary": "Bitbucket projects reference covering project listing under a workspace.",
        },
        "bitbucket_users_ref": {
            "vendor": "bitbucket",
            "kind": "reference",
            "url": "https://developer.atlassian.com/cloud/bitbucket/rest/api-group-users/",
            "summary": "Bitbucket users reference covering the current read-only user lookup endpoint.",
        },
    }


def build_tools() -> list[dict[str, object]]:
    return [
        _canonical_tool(
            "notion.blocks.append_paragraph",
            "Append a paragraph block under an existing Notion block.",
            [
                _canonical_arg("block_id", "Identifier of the parent block.", "string"),
                _canonical_arg("content", "Paragraph text content to append.", "string"),
            ],
            semantic_tags=["notion", "blocks", "write", "content"],
        ),
        _canonical_tool(
            "notion.databases.list_shared",
            "List databases that are directly shared with the integration.",
            [
                _canonical_arg("query", "Optional query string used by search-based fallbacks.", "string", required=False),
                _canonical_arg(
                    "result_type",
                    "Optional search filter for result object type.",
                    "enum",
                    required=False,
                    enum_values=["page", "data_source"],
                ),
            ],
            semantic_tags=["notion", "databases", "search", "read"],
        ),
        _canonical_tool(
            "notion.data_sources.query_entries",
            "Query entries from a Notion database or data source.",
            [
                _canonical_arg("container_id", "Database or data source identifier.", "string"),
                _canonical_arg("status_filter", "Optional status filter for the query.", "string", required=False),
            ],
            semantic_tags=["notion", "data_sources", "query", "read"],
        ),
        _canonical_tool(
            "notion.pages.create_in_container",
            "Create a page under a Notion database-style container.",
            [
                _canonical_arg("parent_id", "Database or data source identifier that should parent the new page.", "string"),
                _canonical_arg("title", "Title of the page to create.", "string"),
            ],
            semantic_tags=["notion", "pages", "create", "write"],
        ),
        _canonical_tool(
            "slack.conversations.open_group_dm",
            "Open or resume a multi-person direct message in Slack.",
            [
                _canonical_arg("users_csv", "Comma-separated Slack user IDs to include in the MPIM.", "string"),
            ],
            semantic_tags=["slack", "messaging", "conversation", "open"],
        ),
        _canonical_tool(
            "slack.files.upload_to_channel",
            "Upload a file to a Slack channel in one API call.",
            [
                _canonical_arg("channel_id", "Slack channel ID.", "string"),
                _canonical_arg("file_path", "Path to the file to upload.", "string"),
                _canonical_arg("title", "Optional display title for the uploaded file.", "string", required=False),
            ],
            semantic_tags=["slack", "files", "write", "upload"],
        ),
        _canonical_tool(
            "slack.conversations.create_channel",
            "Create a Slack channel.",
            [
                _canonical_arg("channel_name", "Name of the channel to create.", "string"),
            ],
            semantic_tags=["slack", "conversations", "create", "write"],
        ),
        _canonical_tool(
            "slack.conversations.list_channels",
            "List channels visible to the caller in Slack.",
            [],
            semantic_tags=["slack", "conversations", "list", "read"],
        ),
        _canonical_tool(
            "stripe.customers.create_with_tax_id",
            "Create a Stripe customer together with a tax identifier.",
            [
                _canonical_arg("email", "Customer email address.", "string"),
                _canonical_arg(
                    "tax_id_type",
                    "Type of tax identifier to attach.",
                    "enum",
                    enum_values=["eu_vat", "us_ein"],
                ),
                _canonical_arg("tax_id_value", "Tax identifier value.", "string"),
            ],
            semantic_tags=["stripe", "customers", "write", "tax"],
        ),
        _canonical_tool(
            "stripe.customers.list_with_total_count",
            "List Stripe customers and include the legacy total_count field.",
            [
                _canonical_arg("limit", "Number of customers to return.", "integer"),
                _canonical_arg("include_total_count", "Whether to request total_count in the response.", "boolean"),
            ],
            semantic_tags=["stripe", "customers", "list", "count"],
        ),
        _canonical_tool(
            "stripe.checkout.create_session_with_discount",
            "Create a Stripe Checkout Session with a subscription discount.",
            [
                _canonical_arg("price_id", "Price identifier for the subscription line item.", "string"),
                _canonical_arg("coupon_id", "Coupon identifier to apply.", "string"),
            ],
            semantic_tags=["stripe", "checkout", "session", "discount"],
        ),
        _canonical_tool(
            "stripe.subscriptions.update_default_source",
            "Update a subscription's payment source in the legacy Stripe API.",
            [
                _canonical_arg("subscription_id", "Subscription identifier.", "string"),
                _canonical_arg("source_id", "Payment source identifier.", "string"),
            ],
            semantic_tags=["stripe", "subscriptions", "update", "billing"],
        ),
        _canonical_tool(
            "drive.files.list_shared_drive_items",
            "List items inside a specific Google Drive shared drive.",
            [
                _canonical_arg("shared_drive_id", "Shared drive identifier.", "string"),
                _canonical_arg(
                    "include_all_drive_items",
                    "Whether to include shared drive items in the listing.",
                    "boolean",
                ),
                _canonical_arg(
                    "supports_shared_drives",
                    "Whether the caller supports shared drive semantics.",
                    "boolean",
                ),
            ],
            semantic_tags=["drive", "files", "list", "shared_drive"],
        ),
        _canonical_tool(
            "drive.files.add_parent",
            "Add a Google Drive file to a folder.",
            [
                _canonical_arg("file_id", "Drive file identifier.", "string"),
                _canonical_arg("parent_id", "Drive folder identifier to add.", "string"),
            ],
            semantic_tags=["drive", "files", "folders", "write"],
        ),
        _canonical_tool(
            "drive.files.remove_parent",
            "Remove a Google Drive file from a folder.",
            [
                _canonical_arg("file_id", "Drive file identifier.", "string"),
                _canonical_arg("parent_id", "Drive folder identifier to remove.", "string"),
            ],
            semantic_tags=["drive", "files", "folders", "write"],
        ),
        _canonical_tool(
            "drive.files.add_secondary_parent",
            "Place a Google Drive file in an additional folder while keeping its current folder.",
            [
                _canonical_arg("file_id", "Drive file identifier.", "string"),
                _canonical_arg("parent_id", "Additional folder identifier to add.", "string"),
            ],
            semantic_tags=["drive", "files", "folders", "multi_parent"],
        ),
        _canonical_tool(
            "jira.issues.assign_user",
            "Assign a Jira issue to a user identity.",
            [
                _canonical_arg("issue_key", "Jira issue key.", "string"),
                _canonical_arg("user_ref", "Opaque user identity token.", "string"),
            ],
            semantic_tags=["jira", "issues", "assign", "write"],
        ),
        _canonical_tool(
            "jira.issues.add_watcher",
            "Add a watcher to a Jira issue.",
            [
                _canonical_arg("issue_key", "Jira issue key.", "string"),
                _canonical_arg("user_ref", "Opaque user identity token.", "string"),
            ],
            semantic_tags=["jira", "issues", "watchers", "write"],
        ),
        _canonical_tool(
            "jira.users.search_assignable",
            "Find an assignable Jira user by a generic search attribute.",
            [
                _canonical_arg("project_key", "Jira project key.", "string"),
                _canonical_arg("user_query", "Search token used to find the user.", "string"),
            ],
            semantic_tags=["jira", "users", "search", "assignable"],
        ),
        _canonical_tool(
            "jira.users.search_by_legacy_username",
            "Find an assignable Jira user by a legacy username identifier.",
            [
                _canonical_arg("project_key", "Jira project key.", "string"),
                _canonical_arg("legacy_username", "Legacy Jira username.", "string"),
            ],
            semantic_tags=["jira", "users", "search", "legacy_username"],
        ),
        _canonical_tool(
            "sheets.spreadsheets.get_sheet_titles",
            "List the sheet titles inside a Google spreadsheet.",
            [
                _canonical_arg("spreadsheet_id", "Google Sheets spreadsheet identifier.", "string"),
            ],
            semantic_tags=["sheets", "spreadsheets", "metadata", "titles", "read"],
        ),
        _canonical_tool(
            "sheets.values.append_row",
            "Append a new row of values to a Google Sheets worksheet.",
            [
                _canonical_arg("spreadsheet_id", "Google Sheets spreadsheet identifier.", "string"),
                _canonical_arg("worksheet_name", "Worksheet name used as the append target range.", "string"),
                _canonical_arg("row_values_csv", "Comma-separated cell values for the appended row.", "string"),
            ],
            semantic_tags=["sheets", "values", "append", "write"],
        ),
        _canonical_tool(
            "sheets.values.update_formula",
            "Update a Google Sheets cell or range with a formula or user-entered value.",
            [
                _canonical_arg("spreadsheet_id", "Google Sheets spreadsheet identifier.", "string"),
                _canonical_arg("range_a1", "A1 notation range to update.", "string"),
                _canonical_arg("formula", "Formula or value to write into the target range.", "string"),
            ],
            semantic_tags=["sheets", "values", "update", "formula", "write"],
        ),
        _canonical_tool(
            "sheets.spreadsheets.list_accessible",
            "List the spreadsheets accessible by the authenticated user.",
            [],
            semantic_tags=["sheets", "spreadsheets", "list", "read"],
        ),
        _canonical_tool(
            "people.contacts.list_my_contacts",
            "List the caller's personal contacts with names and email addresses.",
            [
                _canonical_arg("page_size", "Maximum number of contacts to return.", "integer"),
            ],
            semantic_tags=["people", "contacts", "list", "read"],
        ),
        _canonical_tool(
            "people.contacts.create_contact",
            "Create a personal contact with a name and email address.",
            [
                _canonical_arg("given_name", "Display name for the contact.", "string"),
                _canonical_arg("email", "Primary email address for the contact.", "string"),
            ],
            semantic_tags=["people", "contacts", "create", "write"],
        ),
        _canonical_tool(
            "people.contact_groups.list",
            "List the caller's Google contact groups.",
            [],
            semantic_tags=["people", "contact_groups", "list", "read"],
        ),
        _canonical_tool(
            "people.other_contacts.update_email",
            "Update the email address stored on an Other Contact entry.",
            [
                _canonical_arg("other_contact_id", "Legacy Other Contact identifier.", "string"),
                _canonical_arg("email", "Updated email address to store on the Other Contact.", "string"),
            ],
            semantic_tags=["people", "other_contacts", "update", "write"],
        ),
        _canonical_tool(
            "confluence.pages.get_storage",
            "Get a Confluence page by ID together with its storage body.",
            [
                _canonical_arg("page_id", "Confluence page identifier.", "string"),
            ],
            semantic_tags=["confluence", "pages", "read", "storage"],
        ),
        _canonical_tool(
            "confluence.pages.update_title",
            "Update the title of a Confluence page.",
            [
                _canonical_arg("page_id", "Confluence page identifier.", "string"),
                _canonical_arg("title", "New title for the page.", "string"),
            ],
            semantic_tags=["confluence", "pages", "update", "title"],
        ),
        _canonical_tool(
            "confluence.pages.list_children",
            "List the child pages directly under a Confluence page.",
            [
                _canonical_arg("page_id", "Parent Confluence page identifier.", "string"),
            ],
            semantic_tags=["confluence", "pages", "children", "read"],
        ),
        _canonical_tool(
            "confluence.pages.list_by_space_key",
            "List Confluence pages by a legacy space key.",
            [
                _canonical_arg("space_key", "Legacy Confluence space key.", "string"),
            ],
            semantic_tags=["confluence", "pages", "space_key", "read"],
        ),
        _canonical_tool(
            "bitbucket.workspaces.get",
            "Get a Bitbucket workspace profile by workspace slug.",
            [
                _canonical_arg("workspace_slug", "Bitbucket workspace slug.", "string"),
            ],
            semantic_tags=["bitbucket", "workspaces", "read", "profile"],
        ),
        _canonical_tool(
            "bitbucket.repositories.list_workspace",
            "List repositories that belong to a Bitbucket workspace.",
            [
                _canonical_arg("workspace_slug", "Bitbucket workspace slug.", "string"),
            ],
            semantic_tags=["bitbucket", "repositories", "list", "workspace"],
        ),
        _canonical_tool(
            "bitbucket.workspaces.list_members",
            "List members that belong to a Bitbucket workspace.",
            [
                _canonical_arg("workspace_slug", "Bitbucket workspace slug.", "string"),
            ],
            semantic_tags=["bitbucket", "workspaces", "members", "read"],
        ),
        _canonical_tool(
            "bitbucket.accounts.get_legacy_account",
            "Get a Bitbucket legacy account object by account name, where the account may be either a user or a team.",
            [
                _canonical_arg("account_name", "Legacy Bitbucket account name.", "string"),
            ],
            semantic_tags=["bitbucket", "accounts", "legacy", "read"],
        ),
    ]


def build_cases() -> list[dict[str, object]]:
    return [
        _case(
            case_id="notion_append_paragraph_block",
            request="Append a paragraph saying 'Ship the proposal draft today.' under block blk_123.",
            tool_ids=[
                "notion.blocks.append_paragraph",
                "notion.databases.list_shared",
                "slack.files.upload_to_channel",
            ],
            slot_values={
                "block_id": "blk_123",
                "content": "Ship the proposal draft today.",
            },
            action=_action(
                "notion.blocks.append_paragraph",
                block_id="blk_123",
                content="Ship the proposal draft today.",
            ),
            family_tag="notion",
            notes="sources=notion_2022_02_22,notion_append_blocks_ref;pair=legacy_text_to_rich_text",
        ),
        _case(
            case_id="notion_list_shared_databases",
            request="List the databases shared directly with this integration.",
            tool_ids=[
                "notion.databases.list_shared",
                "notion.blocks.append_paragraph",
                "stripe.customers.list_with_total_count",
            ],
            slot_values={},
            action=_action("notion.databases.list_shared"),
            family_tag="notion",
            notes="sources=notion_get_databases_ref,notion_2025_09_03,notion_search_ref;pair=list_databases_to_search",
        ),
        _case(
            case_id="notion_query_overdue_entries",
            request="Query entries in container db_tasks where status is overdue.",
            tool_ids=[
                "notion.data_sources.query_entries",
                "notion.pages.create_in_container",
                "slack.files.upload_to_channel",
            ],
            slot_values={
                "container_id": "db_tasks",
                "status_filter": "overdue",
            },
            action=_action(
                "notion.data_sources.query_entries",
                container_id="db_tasks",
                status_filter="overdue",
            ),
            family_tag="notion",
            notes="sources=notion_database_query_ref,notion_data_source_query_ref,notion_upgrade_2025_09_03;pair=database_query_to_data_source_query",
        ),
        _case(
            case_id="notion_create_page_in_database",
            request="Create a page titled 'Review backlog' in database db_tasks.",
            tool_ids=[
                "notion.pages.create_in_container",
                "notion.data_sources.query_entries",
                "stripe.customers.create_with_tax_id",
            ],
            slot_values={
                "parent_id": "db_tasks",
                "title": "Review backlog",
            },
            action=_action(
                "notion.pages.create_in_container",
                parent_id="db_tasks",
                title="Review backlog",
            ),
            family_tag="notion",
            notes="sources=notion_post_page_ref,notion_upgrade_2025_09_03;pair=database_parent_to_data_source_parent",
        ),
        _case(
            case_id="slack_open_group_dm",
            request="Open or resume a group DM for users U123,U456.",
            tool_ids=[
                "slack.conversations.open_group_dm",
                "slack.files.upload_to_channel",
                "notion.blocks.append_paragraph",
            ],
            slot_values={"users_csv": "U123,U456"},
            action=_action("slack.conversations.open_group_dm", users_csv="U123,U456"),
            family_tag="slack",
            notes="sources=slack_conversations_2018,slack_mpim_open_ref,slack_conversations_open_ref;pair=mpim_open_to_conversations_open",
        ),
        _case(
            case_id="slack_create_public_channel",
            request="Create a public channel named release-updates.",
            tool_ids=[
                "slack.conversations.create_channel",
                "slack.conversations.list_channels",
                "notion.blocks.append_paragraph",
            ],
            slot_values={"channel_name": "release-updates"},
            action=_action("slack.conversations.create_channel", channel_name="release-updates"),
            family_tag="slack",
            notes="sources=slack_conversations_2018,slack_channels_create_ref,slack_conversations_create_ref;pair=channels_create_to_conversations_create",
        ),
        _case(
            case_id="slack_list_channels",
            request="List the workspace channels.",
            tool_ids=[
                "slack.conversations.list_channels",
                "slack.conversations.create_channel",
                "stripe.customers.list_with_total_count",
            ],
            slot_values={},
            action=_action("slack.conversations.list_channels"),
            family_tag="slack",
            notes="sources=slack_conversations_2018,slack_channels_list_ref,slack_conversations_list_ref;pair=channels_list_to_conversations_list",
        ),
        _case(
            case_id="slack_upload_file_to_channel",
            request="Upload /tmp/spec.pdf to channel C123 with title 'Spec Draft'.",
            tool_ids=[
                "slack.files.upload_to_channel",
                "slack.conversations.open_group_dm",
                "stripe.customers.create_with_tax_id",
            ],
            slot_values={
                "channel_id": "C123",
                "file_path": "/tmp/spec.pdf",
                "title": "Spec Draft",
            },
            action=_action(
                "slack.files.upload_to_channel",
                channel_id="C123",
                file_path="/tmp/spec.pdf",
                title="Spec Draft",
            ),
            family_tag="slack",
            notes="sources=slack_files_upload_ref;pair=files_upload_to_external_upload_flow",
        ),
        _case(
            case_id="stripe_create_customer_with_tax_id",
            request="Create a customer for finance@example.com with EU VAT ID DE123456789.",
            tool_ids=[
                "stripe.customers.create_with_tax_id",
                "stripe.customers.list_with_total_count",
                "slack.conversations.open_group_dm",
            ],
            slot_values={
                "email": "finance@example.com",
                "tax_id_type": "eu_vat",
                "tax_id_value": "DE123456789",
            },
            action=_action(
                "stripe.customers.create_with_tax_id",
                email="finance@example.com",
                tax_id_type="eu_vat",
                tax_id_value="DE123456789",
            ),
            family_tag="stripe",
            notes="sources=stripe_2018_tax_info,stripe_2019_tax_id_data,stripe_customers_create_ref;pair=tax_info_to_tax_id_data",
        ),
        _case(
            case_id="stripe_create_checkout_session_with_coupon",
            request="Create a subscription Checkout Session for price price_premium using coupon coupon_20off.",
            tool_ids=[
                "stripe.checkout.create_session_with_discount",
                "stripe.subscriptions.update_default_source",
                "slack.conversations.open_group_dm",
            ],
            slot_values={
                "price_id": "price_premium",
                "coupon_id": "coupon_20off",
            },
            action=_action(
                "stripe.checkout.create_session_with_discount",
                price_id="price_premium",
                coupon_id="coupon_20off",
            ),
            family_tag="stripe",
            notes="sources=stripe_2022_checkout_discounts,stripe_checkout_session_create_ref;pair=subscription_data_coupon_to_discounts",
        ),
        _case(
            case_id="stripe_list_customers_total_count",
            request="List 25 customers and include the total count.",
            tool_ids=[
                "stripe.customers.list_with_total_count",
                "stripe.customers.create_with_tax_id",
                "notion.databases.list_shared",
            ],
            slot_values={
                "limit": 25,
                "include_total_count": True,
            },
            action=_action(
                "stripe.customers.list_with_total_count",
                limit=25,
                include_total_count=True,
            ),
            family_tag="stripe",
            notes="sources=stripe_2025_total_count;pair=legacy_total_count_expansion_removed",
        ),
        _case(
            case_id="stripe_update_subscription_source",
            request="Update subscription sub_123 to use source src_456.",
            tool_ids=[
                "stripe.subscriptions.update_default_source",
                "stripe.checkout.create_session_with_discount",
                "notion.databases.list_shared",
            ],
            slot_values={
                "subscription_id": "sub_123",
                "source_id": "src_456",
            },
            action=_action(
                "stripe.subscriptions.update_default_source",
                subscription_id="sub_123",
                source_id="src_456",
            ),
            family_tag="stripe",
            notes="sources=stripe_2018_subscription_source_removed,stripe_subscriptions_update_ref;pair=subscription_source_removed",
        ),
        _case(
            case_id="drive_list_shared_drive_items",
            request="List the files in shared drive drv_eng.",
            tool_ids=[
                "drive.files.list_shared_drive_items",
                "drive.files.add_parent",
                "notion.databases.list_shared",
            ],
            slot_values={
                "shared_drive_id": "drv_eng",
                "include_all_drive_items": True,
                "supports_shared_drives": True,
            },
            action=_action(
                "drive.files.list_shared_drive_items",
                shared_drive_id="drv_eng",
                include_all_drive_items=True,
                supports_shared_drives=True,
            ),
            family_tag="drive",
            notes="sources=drive_v2_files_list_ref,drive_v3_files_list_ref,drive_enable_shared_drives_guide;pair=team_drives_to_shared_drives_list",
        ),
        _case(
            case_id="drive_add_parent_to_file",
            request="Place file file_brief in folder fld_reports.",
            tool_ids=[
                "drive.files.add_parent",
                "drive.files.remove_parent",
                "slack.conversations.list_channels",
            ],
            slot_values={
                "file_id": "file_brief",
                "parent_id": "fld_reports",
            },
            action=_action(
                "drive.files.add_parent",
                file_id="file_brief",
                parent_id="fld_reports",
            ),
            family_tag="drive",
            notes="sources=drive_v2_parents_insert_ref,drive_v2_to_v3_ref,drive_v3_files_update_ref;pair=parents_insert_to_files_update_add_parents",
        ),
        _case(
            case_id="drive_remove_parent_from_file",
            request="Remove file file_archive from folder fld_archive.",
            tool_ids=[
                "drive.files.remove_parent",
                "drive.files.add_parent",
                "stripe.customers.list_with_total_count",
            ],
            slot_values={
                "file_id": "file_archive",
                "parent_id": "fld_archive",
            },
            action=_action(
                "drive.files.remove_parent",
                file_id="file_archive",
                parent_id="fld_archive",
            ),
            family_tag="drive",
            notes="sources=drive_v2_parents_delete_ref,drive_v2_to_v3_ref,drive_v3_files_update_ref;pair=parents_delete_to_files_update_remove_parents",
        ),
        _case(
            case_id="drive_add_file_to_second_folder",
            request="Also place file file_plan in folder fld_reports while keeping it in folder fld_eng.",
            tool_ids=[
                "drive.files.add_secondary_parent",
                "drive.files.add_parent",
                "slack.files.upload_to_channel",
            ],
            slot_values={
                "file_id": "file_plan",
                "parent_id": "fld_reports",
            },
            action=_action(
                "drive.files.add_secondary_parent",
                file_id="file_plan",
                parent_id="fld_reports",
            ),
            family_tag="drive",
            notes="sources=drive_v2_parents_insert_ref,drive_v3_files_update_ref,drive_folder_guide,drive_shortcuts_guide;pair=single_parent_shortcut_replacement",
        ),
        _case(
            case_id="jira_assign_issue_user_ref",
            request="Assign issue ENG-7 to Jira user token acct_alice.",
            tool_ids=[
                "jira.issues.assign_user",
                "jira.issues.add_watcher",
                "slack.conversations.create_channel",
            ],
            slot_values={
                "issue_key": "ENG-7",
                "user_ref": "acct_alice",
            },
            action=_action(
                "jira.issues.assign_user",
                issue_key="ENG-7",
                user_ref="acct_alice",
            ),
            family_tag="jira",
            notes="sources=jira_privacy_migration_guide,jira_v2_issue_assignees_ref,jira_v3_issue_assignees_ref;pair=username_to_accountid_assignment",
        ),
        _case(
            case_id="jira_add_issue_watcher_user_ref",
            request="Add Jira user token acct_alice as a watcher on issue ENG-7.",
            tool_ids=[
                "jira.issues.add_watcher",
                "jira.issues.assign_user",
                "notion.blocks.append_paragraph",
            ],
            slot_values={
                "issue_key": "ENG-7",
                "user_ref": "acct_alice",
            },
            action=_action(
                "jira.issues.add_watcher",
                issue_key="ENG-7",
                user_ref="acct_alice",
            ),
            family_tag="jira",
            notes="sources=jira_privacy_migration_guide,jira_v2_issue_watchers_ref,jira_v3_issue_watchers_ref;pair=username_to_accountid_watcher",
        ),
        _case(
            case_id="jira_search_assignable_user_query",
            request="Find the assignable Jira user in project ENG matching user token acct_alice.",
            tool_ids=[
                "jira.users.search_assignable",
                "jira.issues.assign_user",
                "stripe.customers.list_with_total_count",
            ],
            slot_values={
                "project_key": "ENG",
                "user_query": "acct_alice",
            },
            action=_action(
                "jira.users.search_assignable",
                project_key="ENG",
                user_query="acct_alice",
            ),
            family_tag="jira",
            notes="sources=jira_privacy_migration_guide,jira_v2_user_search_ref,jira_v3_user_search_ref;pair=username_to_query_search",
        ),
        _case(
            case_id="jira_search_assignable_user_legacy_username",
            request="Find the assignable Jira user in project ENG with legacy username alice.",
            tool_ids=[
                "jira.users.search_by_legacy_username",
                "jira.issues.assign_user",
                "slack.conversations.list_channels",
            ],
            slot_values={
                "project_key": "ENG",
                "legacy_username": "alice",
            },
            action=_action(
                "jira.users.search_by_legacy_username",
                project_key="ENG",
                legacy_username="alice",
            ),
            family_tag="jira",
            notes="sources=jira_privacy_migration_guide,jira_v2_user_search_ref,jira_v3_user_search_ref;pair=legacy_username_search_removed",
        ),
        _case(
            case_id="sheets_get_sheet_titles",
            request="List the sheet titles in spreadsheet sh_budget.",
            tool_ids=[
                "sheets.spreadsheets.get_sheet_titles",
                "sheets.values.append_row",
                "drive.files.list_shared_drive_items",
            ],
            slot_values={
                "spreadsheet_id": "sh_budget",
            },
            action=_action(
                "sheets.spreadsheets.get_sheet_titles",
                spreadsheet_id="sh_budget",
            ),
            family_tag="sheets",
            notes="sources=sheets_v3_v4_migration_guide,sheets_v4_spreadsheets_get_ref;pair=worksheets_feed_to_spreadsheets_get_fields",
        ),
        _case(
            case_id="sheets_append_row",
            request="Append row 'Elizabeth,42' to worksheet ws_hours in spreadsheet sh_budget.",
            tool_ids=[
                "sheets.values.append_row",
                "sheets.values.update_formula",
                "drive.files.add_parent",
            ],
            slot_values={
                "spreadsheet_id": "sh_budget",
                "worksheet_name": "ws_hours",
                "row_values_csv": "Elizabeth,42",
            },
            action=_action(
                "sheets.values.append_row",
                spreadsheet_id="sh_budget",
                worksheet_name="ws_hours",
                row_values_csv="Elizabeth,42",
            ),
            family_tag="sheets",
            notes="sources=sheets_v3_v4_migration_guide,sheets_v4_values_append_ref;pair=list_feed_post_to_values_append",
        ),
        _case(
            case_id="sheets_update_formula",
            request="Set cell ws_summary!A1 in spreadsheet sh_budget to =SUM(B1:B3).",
            tool_ids=[
                "sheets.values.update_formula",
                "sheets.values.append_row",
                "drive.files.remove_parent",
            ],
            slot_values={
                "spreadsheet_id": "sh_budget",
                "range_a1": "ws_summary!A1",
                "formula": "=SUM(B1:B3)",
            },
            action=_action(
                "sheets.values.update_formula",
                spreadsheet_id="sh_budget",
                range_a1="ws_summary!A1",
                formula="=SUM(B1:B3)",
            ),
            family_tag="sheets",
            notes="sources=sheets_v3_v4_migration_guide,sheets_v4_values_update_ref;pair=cells_feed_put_to_values_update",
        ),
        _case(
            case_id="sheets_list_accessible_spreadsheets",
            request="List the spreadsheets accessible by the authenticated user.",
            tool_ids=[
                "sheets.spreadsheets.list_accessible",
                "sheets.spreadsheets.get_sheet_titles",
                "drive.files.list_shared_drive_items",
            ],
            slot_values={},
            action=_action("sheets.spreadsheets.list_accessible"),
            family_tag="sheets",
            notes="sources=sheets_v3_v4_migration_guide,drive_v3_files_list_ref;pair=spreadsheets_feed_removed_in_v4",
        ),
        _case(
            case_id="people_list_my_contacts",
            request="List my first 10 personal Google contacts with names and email addresses.",
            tool_ids=[
                "people.contacts.list_my_contacts",
                "people.contacts.create_contact",
                "sheets.spreadsheets.get_sheet_titles",
            ],
            slot_values={
                "page_size": 10,
            },
            action=_action(
                "people.contacts.list_my_contacts",
                page_size=10,
            ),
            family_tag="people",
            notes="sources=people_contacts_migration_guide,people_connections_list_ref;pair=contacts_feed_to_people_connections_list",
        ),
        _case(
            case_id="people_create_contact",
            request="Create a Google contact named Alice Example with email alice@example.com.",
            tool_ids=[
                "people.contacts.create_contact",
                "people.contacts.list_my_contacts",
                "slack.conversations.open_group_dm",
            ],
            slot_values={
                "given_name": "Alice Example",
                "email": "alice@example.com",
            },
            action=_action(
                "people.contacts.create_contact",
                given_name="Alice Example",
                email="alice@example.com",
            ),
            family_tag="people",
            notes="sources=people_contacts_migration_guide,people_create_contact_ref;pair=contacts_feed_insert_to_people_create_contact",
        ),
        _case(
            case_id="people_list_contact_groups",
            request="List my Google contact groups.",
            tool_ids=[
                "people.contact_groups.list",
                "people.contacts.list_my_contacts",
                "notion.databases.list_shared",
            ],
            slot_values={},
            action=_action("people.contact_groups.list"),
            family_tag="people",
            notes="sources=people_contacts_migration_guide,people_contact_groups_list_ref;pair=groups_feed_to_contactgroups_list",
        ),
        _case(
            case_id="people_update_other_contact_email",
            request="Update Other Contact oc_alice to email alice.new@example.com.",
            tool_ids=[
                "people.other_contacts.update_email",
                "people.contacts.create_contact",
                "jira.users.search_assignable",
            ],
            slot_values={
                "other_contact_id": "oc_alice",
                "email": "alice.new@example.com",
            },
            action=_action(
                "people.other_contacts.update_email",
                other_contact_id="oc_alice",
                email="alice.new@example.com",
            ),
            family_tag="people",
            notes="sources=people_contacts_migration_guide,people_update_contact_ref,people_other_contacts_copy_ref;pair=other_contacts_read_only_capability_gap",
        ),
        _case(
            case_id="confluence_get_page_storage",
            request="Get Confluence page 2001 including its storage body.",
            tool_ids=[
                "confluence.pages.get_storage",
                "confluence.pages.update_title",
                "people.contacts.list_my_contacts",
            ],
            slot_values={
                "page_id": "2001",
            },
            action=_action(
                "confluence.pages.get_storage",
                page_id="2001",
            ),
            family_tag="confluence",
            notes="sources=confluence_v1_content_ref,confluence_v2_page_ref,confluence_v1_v2_notice;pair=content_get_expand_to_pages_body_format",
        ),
        _case(
            case_id="confluence_update_page_title",
            request="Rename Confluence page 2001 to 'Sprint Plan'.",
            tool_ids=[
                "confluence.pages.update_title",
                "confluence.pages.get_storage",
                "notion.blocks.append_paragraph",
            ],
            slot_values={
                "page_id": "2001",
                "title": "Sprint Plan",
            },
            action=_action(
                "confluence.pages.update_title",
                page_id="2001",
                title="Sprint Plan",
            ),
            family_tag="confluence",
            notes="sources=confluence_v1_content_ref,confluence_v2_page_ref,confluence_v1_v2_notice;pair=content_update_to_page_title_endpoint",
        ),
        _case(
            case_id="confluence_list_page_children",
            request="List the child pages under Confluence page 2001.",
            tool_ids=[
                "confluence.pages.list_children",
                "confluence.pages.get_storage",
                "drive.files.list_shared_drive_items",
            ],
            slot_values={
                "page_id": "2001",
            },
            action=_action(
                "confluence.pages.list_children",
                page_id="2001",
            ),
            family_tag="confluence",
            notes="sources=confluence_v1_content_ref,confluence_v2_children_ref,confluence_v1_v2_notice;pair=content_child_page_to_pages_children",
        ),
        _case(
            case_id="confluence_list_pages_by_space_key",
            request="List the Confluence pages in space key ENG.",
            tool_ids=[
                "confluence.pages.list_by_space_key",
                "confluence.pages.get_storage",
                "sheets.spreadsheets.get_sheet_titles",
            ],
            slot_values={
                "space_key": "ENG",
            },
            action=_action(
                "confluence.pages.list_by_space_key",
                space_key="ENG",
            ),
            family_tag="confluence",
            notes="sources=confluence_v1_space_ref,confluence_v2_space_ref,confluence_v2_page_ref,confluence_v1_v2_notice;pair=space_key_lookup_split",
        ),
        _case(
            case_id="bitbucket_get_workspace",
            request="Get the Bitbucket workspace profile for eng-team.",
            tool_ids=[
                "bitbucket.workspaces.get",
                "bitbucket.repositories.list_workspace",
                "confluence.pages.get_storage",
            ],
            slot_values={
                "workspace_slug": "eng-team",
            },
            action=_action(
                "bitbucket.workspaces.get",
                workspace_slug="eng-team",
            ),
            family_tag="bitbucket",
            notes="sources=bitbucket_teams_workspaces_notice,bitbucket_workspaces_ref;pair=team_get_to_workspace_get",
        ),
        _case(
            case_id="bitbucket_list_workspace_repositories",
            request="List the repositories in Bitbucket workspace eng-team.",
            tool_ids=[
                "bitbucket.repositories.list_workspace",
                "bitbucket.workspaces.get",
                "drive.files.list_shared_drive_items",
            ],
            slot_values={
                "workspace_slug": "eng-team",
            },
            action=_action(
                "bitbucket.repositories.list_workspace",
                workspace_slug="eng-team",
            ),
            family_tag="bitbucket",
            notes="sources=bitbucket_teams_workspaces_notice,bitbucket_repositories_ref;pair=team_repositories_to_workspace_repositories",
        ),
        _case(
            case_id="bitbucket_list_workspace_members",
            request="List the members of Bitbucket workspace eng-team.",
            tool_ids=[
                "bitbucket.workspaces.list_members",
                "bitbucket.workspaces.get",
                "jira.users.search_assignable",
            ],
            slot_values={
                "workspace_slug": "eng-team",
            },
            action=_action(
                "bitbucket.workspaces.list_members",
                workspace_slug="eng-team",
            ),
            family_tag="bitbucket",
            notes="sources=bitbucket_teams_workspaces_notice,bitbucket_workspaces_ref;pair=team_members_to_workspace_members",
        ),
        _case(
            case_id="bitbucket_get_legacy_account",
            request="Get the Bitbucket legacy account object for account name eng-team, even if it could refer to either a user or a team.",
            tool_ids=[
                "bitbucket.accounts.get_legacy_account",
                "bitbucket.workspaces.get",
                "bitbucket.workspaces.list_members",
            ],
            slot_values={
                "account_name": "eng-team",
            },
            action=_action(
                "bitbucket.accounts.get_legacy_account",
                account_name="eng-team",
            ),
            family_tag="bitbucket",
            notes="sources=bitbucket_v1_deprecation_notice,bitbucket_teams_workspaces_notice,bitbucket_workspaces_ref,bitbucket_users_ref;pair=legacy_account_union_removed",
        ),
    ]


def build_views() -> list[dict[str, object]]:
    notion_append_legacy = _rendered_tool(
        "notion.blocks.append_paragraph",
        "notion.blocks.children.append",
        "Append child blocks under an existing block. Paragraph content is provided through paragraph.text.",
        [
            _rendered_arg("block_id", "block_id", "Parent block identifier.", "string", position=0),
            _rendered_arg("paragraph.text", "content", "Plain text content for the paragraph block.", "string", position=1),
        ],
    )
    notion_append_current = _rendered_tool(
        "notion.blocks.append_paragraph",
        "notion.blocks.children.append",
        "Append child blocks under an existing block. Paragraph content is provided through paragraph.rich_text.",
        [
            _rendered_arg("block_id", "block_id", "Parent block identifier.", "string", position=0),
            _rendered_arg("paragraph.rich_text", "content", "Rich text array content for the paragraph block.", "string", position=1),
        ],
    )
    notion_list_legacy = _rendered_tool(
        "notion.databases.list_shared",
        "notion.databases.list",
        "List the databases shared directly with the integration.",
        [],
    )
    notion_search_current = _rendered_tool(
        "notion.databases.list_shared",
        "notion.search",
        "Search pages and data sources visible to the integration. Results may include child content and do not exactly recover the old shared-database listing semantics.",
        [
            _rendered_arg("query", "query", "Optional text query.", "string", required=False, position=0),
            _rendered_arg(
                "filter.type",
                "result_type",
                "Optional result type filter for page or data_source.",
                "enum",
                required=False,
                enum_values=["page", "data_source"],
                position=1,
            ),
        ],
    )
    notion_query_database_legacy = _rendered_tool(
        "notion.data_sources.query_entries",
        "notion.databases.query",
        "Query entries from a database.",
        [
            _rendered_arg("database_id", "container_id", "Database identifier.", "string", position=0),
            _rendered_arg("filter.status", "status_filter", "Optional status filter.", "string", required=False, position=1),
        ],
    )
    notion_query_data_source_current = _rendered_tool(
        "notion.data_sources.query_entries",
        "notion.data_sources.query",
        "Query entries from a data source.",
        [
            _rendered_arg("data_source_id", "container_id", "Data source identifier.", "string", position=0),
            _rendered_arg("filter.status", "status_filter", "Optional status filter.", "string", required=False, position=1),
        ],
    )
    notion_create_page_database_legacy = _rendered_tool(
        "notion.pages.create_in_container",
        "notion.pages.create",
        "Create a page under a database parent.",
        [
            _rendered_arg("parent.database_id", "parent_id", "Database parent identifier.", "string", position=0),
            _rendered_arg("properties.title", "title", "Title of the new page.", "string", position=1),
        ],
    )
    notion_create_page_data_source_current = _rendered_tool(
        "notion.pages.create_in_container",
        "notion.pages.create",
        "Create a page under a data source parent. A database identifier alone no longer identifies the exact parent when a database contains multiple data sources.",
        [
            _rendered_arg("parent.data_source_id", "parent_id", "Data source parent identifier.", "string", position=0),
            _rendered_arg("properties.title", "title", "Title of the new page.", "string", position=1),
        ],
    )
    slack_mpim_legacy = _rendered_tool(
        "slack.conversations.open_group_dm",
        "mpim.open",
        "Begins or resumes a multi-person direct message.",
        [
            _rendered_arg("users", "users_csv", "Comma-separated user IDs to include in the MPIM.", "string", position=0),
        ],
    )
    slack_conversations_open = _rendered_tool(
        "slack.conversations.open_group_dm",
        "conversations.open",
        "Opens or resumes a direct message or multi-person direct message conversation.",
        [
            _rendered_arg("users", "users_csv", "Comma-separated user IDs to include in the conversation.", "string", position=0),
        ],
    )
    slack_upload_clean = _rendered_tool(
        "slack.files.upload_to_channel",
        "files.upload",
        "Uploads or creates a file in Slack in a single API call.",
        [
            _rendered_arg("channels", "channel_id", "Channel to share the upload into.", "string", position=0),
            _rendered_arg("file", "file_path", "Path to the file to upload.", "string", position=1),
            _rendered_arg("title", "title", "Optional display title.", "string", required=False, position=2),
        ],
    )
    slack_upload_deprecated = _rendered_tool(
        "slack.files.upload_to_channel",
        "files.upload",
        "Deprecated: use the external upload flow instead. This one-shot method no longer satisfies the supported upload contract.",
        [
            _rendered_arg("channels", "channel_id", "Channel to share the upload into.", "string", position=0),
            _rendered_arg("file", "file_path", "Path to the file to upload.", "string", position=1),
            _rendered_arg("title", "title", "Optional display title.", "string", required=False, position=2),
        ],
        status="deprecated",
    )
    slack_channels_create_legacy = _rendered_tool(
        "slack.conversations.create_channel",
        "channels.create",
        "Creates a public channel.",
        [
            _rendered_arg("name", "channel_name", "Channel name.", "string", position=0),
        ],
    )
    slack_conversations_create = _rendered_tool(
        "slack.conversations.create_channel",
        "conversations.create",
        "Create a public or private channel using the Conversations API.",
        [
            _rendered_arg("name", "channel_name", "Channel name.", "string", position=0),
        ],
    )
    slack_channels_list_legacy = _rendered_tool(
        "slack.conversations.list_channels",
        "channels.list",
        "Lists channels in a Slack team.",
        [],
    )
    slack_conversations_list = _rendered_tool(
        "slack.conversations.list_channels",
        "conversations.list",
        "Lists channels in a Slack team using the Conversations API.",
        [],
    )
    stripe_create_tax_info = _rendered_tool(
        "stripe.customers.create_with_tax_id",
        "customers.create",
        "Create a customer. Tax identifiers are passed via tax_info.",
        [
            _rendered_arg("email", "email", "Customer email address.", "string", position=0),
            _rendered_arg("tax_info.type", "tax_id_type", "Tax identifier type.", "enum", enum_values=["eu_vat", "us_ein"], position=1),
            _rendered_arg("tax_info.value", "tax_id_value", "Tax identifier value.", "string", position=2),
        ],
    )
    stripe_create_tax_id_data = _rendered_tool(
        "stripe.customers.create_with_tax_id",
        "customers.create",
        "Create a customer. Tax identifiers are passed via tax_id_data.",
        [
            _rendered_arg("email", "email", "Customer email address.", "string", position=0),
            _rendered_arg("tax_id_data.type", "tax_id_type", "Tax identifier type.", "enum", enum_values=["eu_vat", "us_ein"], position=1),
            _rendered_arg("tax_id_data.value", "tax_id_value", "Tax identifier value.", "string", position=2),
        ],
    )
    stripe_list_legacy = _rendered_tool(
        "stripe.customers.list_with_total_count",
        "customers.list",
        "List customers and expand total_count in the response.",
        [
            _rendered_arg("limit", "limit", "Number of customers to return.", "integer", position=0),
            _rendered_arg("expand_total_count", "include_total_count", "Whether to include total_count.", "boolean", position=1),
        ],
    )
    stripe_list_current = _rendered_tool(
        "stripe.customers.list_with_total_count",
        "customers.list",
        "List customers. total_count can no longer be expanded on list API responses.",
        [
            _rendered_arg("limit", "limit", "Number of customers to return.", "integer", position=0),
        ],
    )
    stripe_checkout_coupon_legacy = _rendered_tool(
        "stripe.checkout.create_session_with_discount",
        "checkout.sessions.create",
        "Create a Checkout Session. Subscription discounts are passed via subscription_data[coupon].",
        [
            _rendered_arg("line_items[0][price]", "price_id", "Price to subscribe to.", "string", position=0),
            _rendered_arg("subscription_data[coupon]", "coupon_id", "Coupon to apply to the subscription.", "string", position=1),
        ],
    )
    stripe_checkout_discounts_current = _rendered_tool(
        "stripe.checkout.create_session_with_discount",
        "checkout.sessions.create",
        "Create a Checkout Session. Subscription discounts are passed via discounts[].",
        [
            _rendered_arg("line_items[0][price]", "price_id", "Price to subscribe to.", "string", position=0),
            _rendered_arg("discounts[0][coupon]", "coupon_id", "Coupon to apply to the session.", "string", position=1),
        ],
    )
    stripe_subscription_source_legacy = _rendered_tool(
        "stripe.subscriptions.update_default_source",
        "subscriptions.update",
        "Update a subscription and set its source directly.",
        [
            _rendered_arg("subscription", "subscription_id", "Subscription identifier.", "string", position=0),
            _rendered_arg("source", "source_id", "Source identifier.", "string", position=1),
        ],
    )
    stripe_subscription_source_current = _rendered_tool(
        "stripe.subscriptions.update_default_source",
        "subscriptions.update",
        "Update a subscription. The source parameter is no longer supported on subscription endpoints; update the customer instead.",
        [
            _rendered_arg("subscription", "subscription_id", "Subscription identifier.", "string", position=0),
        ],
    )
    drive_list_legacy = _rendered_tool(
        "drive.files.list_shared_drive_items",
        "files.list",
        "List files in a Team Drive.",
        [
            _rendered_arg("teamDriveId", "shared_drive_id", "Team Drive identifier to search.", "string", position=0),
            _rendered_arg(
                "includeTeamDriveItems",
                "include_all_drive_items",
                "Whether Team Drive items should be included in the results.",
                "boolean",
                position=1,
            ),
            _rendered_arg(
                "supportsTeamDrives",
                "supports_shared_drives",
                "Whether the application supports Team Drives.",
                "boolean",
                position=2,
            ),
        ],
    )
    drive_list_current = _rendered_tool(
        "drive.files.list_shared_drive_items",
        "files.list",
        "List files in a shared drive.",
        [
            _rendered_arg("driveId", "shared_drive_id", "Shared drive identifier to search.", "string", position=0),
            _rendered_arg(
                "includeItemsFromAllDrives",
                "include_all_drive_items",
                "Whether both My Drive and shared drive items should be included in results.",
                "boolean",
                position=1,
            ),
            _rendered_arg(
                "supportsAllDrives",
                "supports_shared_drives",
                "Whether the requesting application supports both My Drives and shared drives.",
                "boolean",
                position=2,
            ),
        ],
    )
    drive_add_parent_legacy = _rendered_tool(
        "drive.files.add_parent",
        "parents.insert",
        "Adds a parent folder for a file.",
        [
            _rendered_arg("fileId", "file_id", "Drive file identifier.", "string", position=0),
            _rendered_arg("parent.id", "parent_id", "Folder identifier to add as the parent.", "string", position=1),
        ],
    )
    drive_add_parent_current = _rendered_tool(
        "drive.files.add_parent",
        "files.update",
        "Update a file and add a parent folder for that file via addParents.",
        [
            _rendered_arg("fileId", "file_id", "Drive file identifier.", "string", position=0),
            _rendered_arg("addParents", "parent_id", "Comma-separated list of parent IDs to add.", "string", position=1),
        ],
    )
    drive_remove_parent_legacy = _rendered_tool(
        "drive.files.remove_parent",
        "parents.delete",
        "Removes a parent from a file.",
        [
            _rendered_arg("fileId", "file_id", "Drive file identifier.", "string", position=0),
            _rendered_arg("parentId", "parent_id", "Folder identifier to remove.", "string", position=1),
        ],
    )
    drive_remove_parent_current = _rendered_tool(
        "drive.files.remove_parent",
        "files.update",
        "Update a file and remove a parent folder from that file via removeParents.",
        [
            _rendered_arg("fileId", "file_id", "Drive file identifier.", "string", position=0),
            _rendered_arg("removeParents", "parent_id", "Comma-separated list of parent IDs to remove.", "string", position=1),
        ],
    )
    drive_add_secondary_parent_legacy = _rendered_tool(
        "drive.files.add_secondary_parent",
        "parents.insert",
        "Adds a parent folder for a file while keeping the file itself unchanged.",
        [
            _rendered_arg("fileId", "file_id", "Drive file identifier.", "string", position=0),
            _rendered_arg("parent.id", "parent_id", "Additional folder identifier to add.", "string", position=1),
        ],
    )
    drive_add_secondary_parent_current = _rendered_tool(
        "drive.files.add_secondary_parent",
        "files.update",
        "A file can only have one parent folder. Adding files to multiple folders is not supported. Use shortcuts instead.",
        [
            _rendered_arg("fileId", "file_id", "Drive file identifier.", "string", position=0),
            _rendered_arg("addParents", "parent_id", "Comma-separated list of parent IDs to add.", "string", position=1),
            _rendered_arg(
                "enforceSingleParent",
                "enforce_single_parent",
                "Deprecated legacy control. Adding files to multiple folders is not supported.",
                "boolean",
                required=False,
                position=2,
            ),
        ],
    )
    jira_assign_legacy = _rendered_tool(
        "jira.issues.assign_user",
        "issue.assignee",
        "Assign an issue to a user using the legacy username-style identifier.",
        [
            _rendered_arg("issueIdOrKey", "issue_key", "Jira issue key.", "string", position=0),
            _rendered_arg("name", "user_ref", "Legacy username-style identifier for the assignee.", "string", position=1),
        ],
    )
    jira_assign_current = _rendered_tool(
        "jira.issues.assign_user",
        "issue.assignee",
        "Assign an issue to a user by accountId.",
        [
            _rendered_arg("issueIdOrKey", "issue_key", "Jira issue key.", "string", position=0),
            _rendered_arg("accountId", "user_ref", "Atlassian account ID for the assignee.", "string", position=1),
        ],
    )
    jira_watch_legacy = _rendered_tool(
        "jira.issues.add_watcher",
        "issue.watchers",
        "Add a watcher to an issue using the legacy username-style identifier.",
        [
            _rendered_arg("issueIdOrKey", "issue_key", "Jira issue key.", "string", position=0),
            _rendered_arg("username", "user_ref", "Legacy username-style identifier for the watcher.", "string", position=1),
        ],
    )
    jira_watch_current = _rendered_tool(
        "jira.issues.add_watcher",
        "issue.watchers",
        "Add a watcher to an issue by accountId.",
        [
            _rendered_arg("issueIdOrKey", "issue_key", "Jira issue key.", "string", position=0),
            _rendered_arg("accountId", "user_ref", "Atlassian account ID for the watcher.", "string", position=1),
        ],
    )
    jira_search_legacy = _rendered_tool(
        "jira.users.search_assignable",
        "user.assignable.search",
        "Find an assignable user in a project by username.",
        [
            _rendered_arg("project", "project_key", "Jira project key.", "string", position=0),
            _rendered_arg("username", "user_query", "Legacy username-style search token.", "string", position=1),
        ],
    )
    jira_search_current = _rendered_tool(
        "jira.users.search_assignable",
        "user.assignable.search",
        "Find an assignable user in a project by query. Query can be an email address, display name, or any other user attribute.",
        [
            _rendered_arg("project", "project_key", "Jira project key.", "string", position=0),
            _rendered_arg("query", "user_query", "Generic search token for the user lookup.", "string", position=1),
        ],
    )
    jira_search_legacy_negative = _rendered_tool(
        "jira.users.search_by_legacy_username",
        "user.assignable.search",
        "Find an assignable user in a project by username.",
        [
            _rendered_arg("project", "project_key", "Jira project key.", "string", position=0),
            _rendered_arg("username", "legacy_username", "Legacy username identifier to search for.", "string", position=1),
        ],
    )
    jira_search_current_legacy = _rendered_tool(
        "jira.users.search_by_legacy_username",
        "user.assignable.search",
        "Find an assignable user in a project by query. Username and userKey are no longer supported; use accountId or another query attribute instead.",
        [
            _rendered_arg("project", "project_key", "Jira project key.", "string", position=0),
            _rendered_arg("query", "legacy_username", "Generic user attribute query.", "string", position=1),
        ],
    )
    sheets_titles_legacy = _rendered_tool(
        "sheets.spreadsheets.get_sheet_titles",
        "worksheets.feed",
        "Retrieve the worksheets in a spreadsheet through the worksheets feed.",
        [
            _rendered_arg("spreadsheetId", "spreadsheet_id", "Spreadsheet identifier.", "string", position=0),
        ],
    )
    sheets_titles_current = _rendered_tool(
        "sheets.spreadsheets.get_sheet_titles",
        "spreadsheets.get",
        "Retrieve spreadsheet metadata. Use fields=sheets.properties.title to retrieve the titles of the sheets in a spreadsheet.",
        [
            _rendered_arg("spreadsheetId", "spreadsheet_id", "Spreadsheet identifier.", "string", position=0),
        ],
    )
    sheets_append_legacy = _rendered_tool(
        "sheets.values.append_row",
        "list.feed.insert",
        "Add a new row of data using the list feed.",
        [
            _rendered_arg("spreadsheetId", "spreadsheet_id", "Spreadsheet identifier.", "string", position=0),
            _rendered_arg("worksheetId", "worksheet_name", "Worksheet identifier used by the list feed.", "string", position=1),
            _rendered_arg("gsx$row", "row_values_csv", "Comma-separated row payload for the appended entry.", "string", position=2),
        ],
    )
    sheets_append_current = _rendered_tool(
        "sheets.values.append_row",
        "spreadsheets.values.append",
        "Append rows using spreadsheets.values.append. Provide the worksheet range and the row values to append.",
        [
            _rendered_arg("spreadsheetId", "spreadsheet_id", "Spreadsheet identifier.", "string", position=0),
            _rendered_arg("range", "worksheet_name", "Worksheet range used as the append target.", "string", position=1),
            _rendered_arg("values", "row_values_csv", "Comma-separated row payload encoded into a ValueRange body.", "string", position=2),
        ],
    )
    sheets_update_legacy = _rendered_tool(
        "sheets.values.update_formula",
        "cells.feed.update",
        "Update a cell through the cells feed.",
        [
            _rendered_arg("spreadsheetId", "spreadsheet_id", "Spreadsheet identifier.", "string", position=0),
            _rendered_arg("cell", "range_a1", "A1-like cell reference mapped onto the legacy cell feed path.", "string", position=1),
            _rendered_arg("inputValue", "formula", "Formula or value for the target cell.", "string", position=2),
        ],
    )
    sheets_update_current = _rendered_tool(
        "sheets.values.update_formula",
        "spreadsheets.values.update",
        "Update values using spreadsheets.values.update with valueInputOption=USER_ENTERED so formulas are interpreted as formulas.",
        [
            _rendered_arg("spreadsheetId", "spreadsheet_id", "Spreadsheet identifier.", "string", position=0),
            _rendered_arg("range", "range_a1", "A1 notation range to update.", "string", position=1),
            _rendered_arg("values", "formula", "Formula or user-entered value encoded into a ValueRange body.", "string", position=2),
        ],
    )
    sheets_list_legacy = _rendered_tool(
        "sheets.spreadsheets.list_accessible",
        "spreadsheets.feed",
        "List the spreadsheets accessible by the authenticated user.",
        [],
    )
    sheets_list_current = _rendered_tool(
        "sheets.spreadsheets.list_accessible",
        "drive.files.list",
        "Sheets API v4 does not provide this specific operation for listing accessible spreadsheets. It can be replicated via the Drive API Files.list method using a mimeType query, but it is not a drop-in replacement for this sheets tool.",
        [],
    )
    people_list_legacy = _rendered_tool(
        "people.contacts.list_my_contacts",
        "contacts.feed",
        "List contact entries from the legacy contacts feed.",
        [
            _rendered_arg("max-results", "page_size", "Maximum number of contacts to return.", "integer", position=0),
        ],
    )
    people_list_current = _rendered_tool(
        "people.contacts.list_my_contacts",
        "people.connections.list",
        "List My Contacts via people.connections.list. Use personFields=names,emailAddresses to include names and email addresses.",
        [
            _rendered_arg("pageSize", "page_size", "Maximum number of contacts to return.", "integer", position=0),
        ],
    )
    people_create_legacy = _rendered_tool(
        "people.contacts.create_contact",
        "contacts.feed.insert",
        "Insert a new contact entry through the legacy contacts feed.",
        [
            _rendered_arg("gd$name", "given_name", "Display name for the contact entry.", "string", position=0),
            _rendered_arg("gd$email", "email", "Email address for the contact entry.", "string", position=1),
        ],
    )
    people_create_current = _rendered_tool(
        "people.contacts.create_contact",
        "people.createContact",
        "Create a contact via people.createContact and request names,emailAddresses in personFields.",
        [
            _rendered_arg("names", "given_name", "Name payload for the new contact.", "string", position=0),
            _rendered_arg("emailAddresses", "email", "Email payload for the new contact.", "string", position=1),
        ],
    )
    people_groups_legacy = _rendered_tool(
        "people.contact_groups.list",
        "groups.feed",
        "List contact groups from the legacy groups feed.",
        [],
    )
    people_groups_current = _rendered_tool(
        "people.contact_groups.list",
        "contactGroups.list",
        "List contact groups via contactGroups.list. Use groupFields=name to retrieve group names.",
        [],
    )
    people_other_update_legacy = _rendered_tool(
        "people.other_contacts.update_email",
        "contacts.feed.update",
        "Update a contact entry in the legacy contacts feed.",
        [
            _rendered_arg("contactId", "other_contact_id", "Legacy contact identifier to update.", "string", position=0),
            _rendered_arg("gd$email", "email", "Updated email address for the contact entry.", "string", position=1),
        ],
    )
    people_other_update_current = _rendered_tool(
        "people.other_contacts.update_email",
        "people.updateContact",
        "Only contact based people can be modified directly. Other Contacts are read-only. To update an Other Contact email or other data fields, add the Other Contact as a My Contact first using otherContacts.copyOtherContactToMyContactsGroup. That is not a drop-in replacement for directly updating this Other Contact.",
        [
            _rendered_arg("resourceName", "other_contact_id", "Other Contact identifier to update.", "string", position=0),
            _rendered_arg("emailAddresses", "email", "Updated email payload.", "string", position=1),
        ],
    )
    confluence_get_v1 = _rendered_tool(
        "confluence.pages.get_storage",
        "content.get",
        "Get a Confluence content item by ID. Use expand=body.storage to include the storage body.",
        [
            _rendered_arg("id", "page_id", "Confluence content identifier.", "string", position=0),
        ],
    )
    confluence_get_v2 = _rendered_tool(
        "confluence.pages.get_storage",
        "pages.get",
        "Get a Confluence page by ID. Use body-format=storage to include the storage body in the response.",
        [
            _rendered_arg("id", "page_id", "Confluence page identifier.", "string", position=0),
        ],
    )
    confluence_update_v1 = _rendered_tool(
        "confluence.pages.update_title",
        "content.update",
        "Update a Confluence content item and set its title.",
        [
            _rendered_arg("id", "page_id", "Confluence content identifier.", "string", position=0),
            _rendered_arg("title", "title", "Updated title for the content item.", "string", position=1),
        ],
    )
    confluence_update_v2 = _rendered_tool(
        "confluence.pages.update_title",
        "pages.updateTitle",
        "Update only the title of a Confluence page via /wiki/api/v2/pages/{id}/title.",
        [
            _rendered_arg("id", "page_id", "Confluence page identifier.", "string", position=0),
            _rendered_arg("title", "title", "Updated title for the page.", "string", position=1),
        ],
    )
    confluence_children_v1 = _rendered_tool(
        "confluence.pages.list_children",
        "content.child.page",
        "List the child pages under a Confluence content item using the legacy content child page endpoint.",
        [
            _rendered_arg("id", "page_id", "Parent content identifier.", "string", position=0),
        ],
    )
    confluence_children_v2 = _rendered_tool(
        "confluence.pages.list_children",
        "pages.children.list",
        "List the child pages under a Confluence page via /wiki/api/v2/pages/{id}/children using cursor-based pagination.",
        [
            _rendered_arg("id", "page_id", "Parent page identifier.", "string", position=0),
        ],
    )
    confluence_spacekey_v1 = _rendered_tool(
        "confluence.pages.list_by_space_key",
        "content.list",
        "List Confluence pages in a space using the legacy spaceKey parameter.",
        [
            _rendered_arg("spaceKey", "space_key", "Legacy Confluence space key.", "string", position=0),
        ],
    )
    confluence_spaceid_v2 = _rendered_tool(
        "confluence.pages.list_by_space_key",
        "pages.in.space",
        "List Confluence pages in a space by numeric spaceId. This does not provide this specific operation for a raw space key: resolving a space key requires a separate /wiki/api/v2/spaces?keys=<spacekey> lookup and is not a drop-in replacement.",
        [
            _rendered_arg("spaceId", "space_key", "Numeric Confluence space identifier.", "string", position=0),
        ],
    )
    bitbucket_workspace_legacy = _rendered_tool(
        "bitbucket.workspaces.get",
        "teams.get",
        "Get a Bitbucket team profile by username.",
        [
            _rendered_arg("username", "workspace_slug", "Legacy Bitbucket team username.", "string", position=0),
        ],
    )
    bitbucket_workspace_current = _rendered_tool(
        "bitbucket.workspaces.get",
        "workspaces.get",
        "Get a Bitbucket workspace by workspace slug.",
        [
            _rendered_arg("workspace", "workspace_slug", "Bitbucket workspace slug.", "string", position=0),
        ],
    )
    bitbucket_repositories_legacy = _rendered_tool(
        "bitbucket.repositories.list_workspace",
        "teams.repositories.list",
        "List repositories in a Bitbucket team by team username.",
        [
            _rendered_arg("username", "workspace_slug", "Legacy Bitbucket team username.", "string", position=0),
        ],
    )
    bitbucket_repositories_current = _rendered_tool(
        "bitbucket.repositories.list_workspace",
        "repositories.listByWorkspace",
        "List repositories in a Bitbucket workspace.",
        [
            _rendered_arg("workspace", "workspace_slug", "Bitbucket workspace slug.", "string", position=0),
        ],
    )
    bitbucket_members_legacy = _rendered_tool(
        "bitbucket.workspaces.list_members",
        "teams.members.list",
        "List members of a Bitbucket team by team username.",
        [
            _rendered_arg("username", "workspace_slug", "Legacy Bitbucket team username.", "string", position=0),
        ],
    )
    bitbucket_members_current = _rendered_tool(
        "bitbucket.workspaces.list_members",
        "workspaces.members.list",
        "List members of a Bitbucket workspace by workspace slug.",
        [
            _rendered_arg("workspace", "workspace_slug", "Bitbucket workspace slug.", "string", position=0),
        ],
    )
    bitbucket_account_legacy = _rendered_tool(
        "bitbucket.accounts.get_legacy_account",
        "users.getLegacyAccount",
        "Get a Bitbucket account object by legacy account name. This resource can return either a user or a team.",
        [
            _rendered_arg("accountname", "account_name", "Legacy Bitbucket account name.", "string", position=0),
        ],
    )
    bitbucket_account_current = _rendered_tool(
        "bitbucket.accounts.get_legacy_account",
        "workspaces.get",
        "Get a Bitbucket workspace by workspace slug. This does not provide this specific operation for a legacy account name that could refer to either a user or a team: account resolution is split across separate /2.0/users and /2.0/workspaces APIs and is not a drop-in replacement.",
        [
            _rendered_arg("workspace", "account_name", "Bitbucket workspace slug.", "string", position=0),
        ],
    )

    return [
        _view(
            case_id="notion_append_paragraph_block",
            view_id="notion_append_paragraph_block::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[notion_append_legacy, notion_list_legacy, slack_upload_clean],
            notes="Legacy Notion block append schema before the rich_text migration.",
        ),
        _view(
            case_id="notion_append_paragraph_block",
            view_id="notion_append_paragraph_block::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[notion_append_current, notion_search_current, slack_upload_clean],
            notes="Real version migration: append block children moved paragraph content from text to rich_text.",
        ),
        _view(
            case_id="notion_list_shared_databases",
            view_id="notion_list_shared_databases::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[notion_list_legacy, notion_append_legacy, stripe_list_legacy],
            notes="Legacy Notion databases listing endpoint before the 2025-09-03 split.",
        ),
        _view(
            case_id="notion_list_shared_databases",
            view_id="notion_list_shared_databases::negative_search_replacement",
            transform_name="negative_search_replacement",
            shift_kind="negative_near_orbit",
            tools=[notion_search_current, notion_append_current, stripe_list_current],
            notes="Real negative near-orbit: search remains visible but does not exactly preserve the old shared-database listing contract.",
            admissible_actions=[_ask(), _abstain()],
        ),
        _view(
            case_id="notion_query_overdue_entries",
            view_id="notion_query_overdue_entries::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[notion_query_database_legacy, notion_create_page_database_legacy, slack_upload_clean],
            notes="Legacy Notion database query schema.",
        ),
        _view(
            case_id="notion_query_overdue_entries",
            view_id="notion_query_overdue_entries::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[notion_query_data_source_current, notion_create_page_data_source_current, slack_upload_clean],
            notes="Real version migration: database query moved to data source query in the 2025-09-03 split.",
        ),
        _view(
            case_id="notion_create_page_in_database",
            view_id="notion_create_page_in_database::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[notion_create_page_database_legacy, notion_query_database_legacy, stripe_create_tax_info],
            notes="Legacy Notion page creation schema using a database parent.",
        ),
        _view(
            case_id="notion_create_page_in_database",
            view_id="notion_create_page_in_database::negative_parent_scope_change",
            transform_name="negative_parent_scope_change",
            shift_kind="negative_near_orbit",
            tools=[notion_create_page_data_source_current, notion_query_data_source_current, stripe_create_tax_id_data],
            notes="Real negative near-orbit: a database identifier alone no longer resolves the exact parent after the database to data-source split.",
            admissible_actions=[_ask(), _abstain()],
        ),
        _view(
            case_id="slack_open_group_dm",
            view_id="slack_open_group_dm::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[slack_mpim_legacy, slack_upload_clean, notion_append_current],
            notes="Legacy Slack mpim.open schema.",
        ),
        _view(
            case_id="slack_open_group_dm",
            view_id="slack_open_group_dm::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[slack_conversations_open, slack_upload_clean, notion_append_current],
            notes="Real version migration: legacy mpim.open capability now lives under conversations.open.",
        ),
        _view(
            case_id="slack_create_public_channel",
            view_id="slack_create_public_channel::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[slack_channels_create_legacy, slack_channels_list_legacy, notion_append_current],
            notes="Legacy Slack channels.create schema.",
        ),
        _view(
            case_id="slack_create_public_channel",
            view_id="slack_create_public_channel::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[slack_conversations_create, slack_conversations_list, notion_append_current],
            notes="Real version migration: legacy channels.create capability now lives under conversations.create.",
        ),
        _view(
            case_id="slack_list_channels",
            view_id="slack_list_channels::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[slack_channels_list_legacy, slack_channels_create_legacy, stripe_list_legacy],
            notes="Legacy Slack channels.list schema.",
        ),
        _view(
            case_id="slack_list_channels",
            view_id="slack_list_channels::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[slack_conversations_list, slack_conversations_create, stripe_list_current],
            notes="Real version migration: legacy channels.list capability now lives under conversations.list.",
        ),
        _view(
            case_id="slack_upload_file_to_channel",
            view_id="slack_upload_file_to_channel::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[slack_upload_clean, slack_mpim_legacy, stripe_create_tax_info],
            notes="Legacy Slack one-shot file upload schema.",
        ),
        _view(
            case_id="slack_upload_file_to_channel",
            view_id="slack_upload_file_to_channel::negative_deprecate",
            transform_name="negative_deprecate",
            shift_kind="negative_near_orbit",
            tools=[slack_upload_deprecated, slack_conversations_open, stripe_create_tax_id_data],
            notes="Real negative near-orbit: files.upload is explicitly deprecated, with no one-shot substitute exposed in this view.",
            admissible_actions=[_abstain()],
        ),
        _view(
            case_id="stripe_create_customer_with_tax_id",
            view_id="stripe_create_customer_with_tax_id::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[stripe_create_tax_info, stripe_list_legacy, slack_mpim_legacy],
            notes="Legacy Stripe customer creation schema using tax_info.",
        ),
        _view(
            case_id="stripe_create_customer_with_tax_id",
            view_id="stripe_create_customer_with_tax_id::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[stripe_create_tax_id_data, stripe_list_current, slack_conversations_open],
            notes="Real version migration: Stripe customer creation moved from tax_info to tax_id_data.",
        ),
        _view(
            case_id="stripe_create_checkout_session_with_coupon",
            view_id="stripe_create_checkout_session_with_coupon::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[stripe_checkout_coupon_legacy, stripe_subscription_source_legacy, slack_mpim_legacy],
            notes="Legacy Stripe Checkout Session schema using subscription_data[coupon].",
        ),
        _view(
            case_id="stripe_create_checkout_session_with_coupon",
            view_id="stripe_create_checkout_session_with_coupon::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[stripe_checkout_discounts_current, stripe_subscription_source_current, slack_conversations_open],
            notes="Real version migration: Checkout Session coupon input moved from subscription_data[coupon] to discounts.",
        ),
        _view(
            case_id="stripe_list_customers_total_count",
            view_id="stripe_list_customers_total_count::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[stripe_list_legacy, stripe_create_tax_info, notion_list_legacy],
            notes="Legacy Stripe list API where total_count expansion was still supported.",
        ),
        _view(
            case_id="stripe_list_customers_total_count",
            view_id="stripe_list_customers_total_count::negative_removed_capability",
            transform_name="negative_removed_capability",
            shift_kind="negative_near_orbit",
            tools=[stripe_list_current, stripe_create_tax_id_data, notion_search_current],
            notes="Real negative near-orbit: total_count is removed from list responses, so the original request is no longer satisfiable as-is.",
            admissible_actions=[_ask(), _abstain()],
        ),
        _view(
            case_id="stripe_update_subscription_source",
            view_id="stripe_update_subscription_source::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[stripe_subscription_source_legacy, stripe_checkout_coupon_legacy, notion_list_legacy],
            notes="Legacy Stripe subscription update schema with a direct source parameter.",
        ),
        _view(
            case_id="stripe_update_subscription_source",
            view_id="stripe_update_subscription_source::negative_source_removed",
            transform_name="negative_source_removed",
            shift_kind="negative_near_orbit",
            tools=[stripe_subscription_source_current, stripe_checkout_discounts_current, notion_search_current],
            notes="Real negative near-orbit: Stripe removed the direct subscription source parameter, so the old one-step update is no longer available.",
            admissible_actions=[_ask(), _abstain()],
        ),
        _view(
            case_id="drive_list_shared_drive_items",
            view_id="drive_list_shared_drive_items::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[drive_list_legacy, drive_add_parent_legacy, notion_list_legacy],
            notes="Legacy Drive list schema using Team Drive parameters.",
        ),
        _view(
            case_id="drive_list_shared_drive_items",
            view_id="drive_list_shared_drive_items::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[drive_list_current, drive_add_parent_current, notion_search_current],
            notes="Real version migration: Drive list parameters moved from Team Drive names to shared drive names.",
        ),
        _view(
            case_id="drive_add_parent_to_file",
            view_id="drive_add_parent_to_file::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[drive_add_parent_legacy, drive_remove_parent_legacy, slack_channels_list_legacy],
            notes="Legacy Drive parent insertion schema via parents.insert.",
        ),
        _view(
            case_id="drive_add_parent_to_file",
            view_id="drive_add_parent_to_file::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[drive_add_parent_current, drive_remove_parent_current, slack_conversations_list],
            notes="Real version migration: Drive parent insertion moved from parents.insert to files.update addParents.",
        ),
        _view(
            case_id="drive_remove_parent_from_file",
            view_id="drive_remove_parent_from_file::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[drive_remove_parent_legacy, drive_add_parent_legacy, stripe_list_legacy],
            notes="Legacy Drive parent removal schema via parents.delete.",
        ),
        _view(
            case_id="drive_remove_parent_from_file",
            view_id="drive_remove_parent_from_file::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[drive_remove_parent_current, drive_add_parent_current, stripe_list_current],
            notes="Real version migration: Drive parent removal moved from parents.delete to files.update removeParents.",
        ),
        _view(
            case_id="drive_add_file_to_second_folder",
            view_id="drive_add_file_to_second_folder::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[drive_add_secondary_parent_legacy, drive_add_parent_legacy, slack_upload_clean],
            notes="Legacy Drive parent insertion schema before the single-parent restriction mattered for this request.",
        ),
        _view(
            case_id="drive_add_file_to_second_folder",
            view_id="drive_add_file_to_second_folder::negative_shortcut_replacement",
            transform_name="negative_shortcut_replacement",
            shift_kind="negative_near_orbit",
            tools=[drive_add_secondary_parent_current, drive_add_parent_current, slack_upload_clean],
            notes="Real negative near-orbit: Drive no longer supports adding the same file to multiple folders; shortcuts are a related but not exact replacement.",
            admissible_actions=[_ask(), _abstain()],
        ),
        _view(
            case_id="jira_assign_issue_user_ref",
            view_id="jira_assign_issue_user_ref::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[jira_assign_legacy, jira_watch_legacy, slack_channels_create_legacy],
            notes="Legacy Jira assignment schema using username-style identifiers.",
        ),
        _view(
            case_id="jira_assign_issue_user_ref",
            view_id="jira_assign_issue_user_ref::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[jira_assign_current, jira_watch_current, slack_conversations_create],
            notes="Real version migration: Jira issue assignment moved from username-style identifiers to accountId.",
        ),
        _view(
            case_id="jira_add_issue_watcher_user_ref",
            view_id="jira_add_issue_watcher_user_ref::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[jira_watch_legacy, jira_assign_legacy, notion_append_legacy],
            notes="Legacy Jira watcher schema using username-style identifiers.",
        ),
        _view(
            case_id="jira_add_issue_watcher_user_ref",
            view_id="jira_add_issue_watcher_user_ref::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[jira_watch_current, jira_assign_current, notion_append_current],
            notes="Real version migration: Jira issue watcher changes moved from username-style identifiers to accountId.",
        ),
        _view(
            case_id="jira_search_assignable_user_query",
            view_id="jira_search_assignable_user_query::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[jira_search_legacy, jira_assign_legacy, stripe_list_legacy],
            notes="Legacy Jira assignable-user search schema using username.",
        ),
        _view(
            case_id="jira_search_assignable_user_query",
            view_id="jira_search_assignable_user_query::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[jira_search_current, jira_assign_current, stripe_list_current],
            notes="Real version migration: Jira assignable-user search moved from username to query-based lookup.",
        ),
        _view(
            case_id="jira_search_assignable_user_legacy_username",
            view_id="jira_search_assignable_user_legacy_username::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[jira_search_legacy_negative, jira_assign_legacy, slack_channels_list_legacy],
            notes="Legacy Jira assignable-user search schema where username lookup was still supported.",
        ),
        _view(
            case_id="jira_search_assignable_user_legacy_username",
            view_id="jira_search_assignable_user_legacy_username::negative_legacy_identifier_removed",
            transform_name="negative_legacy_identifier_removed",
            shift_kind="negative_near_orbit",
            tools=[jira_search_current_legacy, jira_assign_current, slack_conversations_list],
            notes="Real negative near-orbit: Jira no longer supports username or userKey as stable user identifiers in query-based lookup.",
            admissible_actions=[_ask(), _abstain()],
        ),
        _view(
            case_id="sheets_get_sheet_titles",
            view_id="sheets_get_sheet_titles::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[sheets_titles_legacy, sheets_append_legacy, drive_list_legacy],
            notes="Legacy Sheets worksheets feed for retrieving sheet titles.",
        ),
        _view(
            case_id="sheets_get_sheet_titles",
            view_id="sheets_get_sheet_titles::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[sheets_titles_current, sheets_append_current, drive_list_current],
            notes="Real version migration: worksheets feed retrieval moved to spreadsheets.get with a fields mask.",
        ),
        _view(
            case_id="sheets_append_row",
            view_id="sheets_append_row::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[sheets_append_legacy, sheets_update_legacy, drive_add_parent_legacy],
            notes="Legacy Sheets list feed for appending a new row.",
        ),
        _view(
            case_id="sheets_append_row",
            view_id="sheets_append_row::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[sheets_append_current, sheets_update_current, drive_add_parent_current],
            notes="Real version migration: list feed row insertion moved to spreadsheets.values.append.",
        ),
        _view(
            case_id="sheets_update_formula",
            view_id="sheets_update_formula::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[sheets_update_legacy, sheets_append_legacy, drive_remove_parent_legacy],
            notes="Legacy Sheets cells feed update schema.",
        ),
        _view(
            case_id="sheets_update_formula",
            view_id="sheets_update_formula::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[sheets_update_current, sheets_append_current, drive_remove_parent_current],
            notes="Real version migration: cells feed updates moved to spreadsheets.values.update with USER_ENTERED formulas.",
        ),
        _view(
            case_id="sheets_list_accessible_spreadsheets",
            view_id="sheets_list_accessible_spreadsheets::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[sheets_list_legacy, sheets_titles_legacy, drive_list_legacy],
            notes="Legacy Sheets spreadsheets feed for listing accessible spreadsheets.",
        ),
        _view(
            case_id="sheets_list_accessible_spreadsheets",
            view_id="sheets_list_accessible_spreadsheets::negative_drive_scope_replacement",
            transform_name="negative_drive_scope_replacement",
            shift_kind="negative_near_orbit",
            tools=[sheets_list_current, sheets_titles_current, drive_list_current],
            notes="Real negative near-orbit: Sheets API v4 does not provide the old spreadsheets-feed listing operation; Drive files.list is related but not a drop-in replacement.",
            admissible_actions=[_ask(), _abstain()],
        ),
        _view(
            case_id="people_list_my_contacts",
            view_id="people_list_my_contacts::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[people_list_legacy, people_create_legacy, sheets_titles_legacy],
            notes="Legacy Google Contacts feed listing schema.",
        ),
        _view(
            case_id="people_list_my_contacts",
            view_id="people_list_my_contacts::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[people_list_current, people_create_current, sheets_titles_current],
            notes="Real version migration: contacts feed listing moved to people.connections.list with personFields.",
        ),
        _view(
            case_id="people_create_contact",
            view_id="people_create_contact::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[people_create_legacy, people_list_legacy, slack_mpim_legacy],
            notes="Legacy Google Contacts feed contact creation schema.",
        ),
        _view(
            case_id="people_create_contact",
            view_id="people_create_contact::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[people_create_current, people_list_current, slack_conversations_open],
            notes="Real version migration: contact creation moved from contacts feed insert to people.createContact.",
        ),
        _view(
            case_id="people_list_contact_groups",
            view_id="people_list_contact_groups::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[people_groups_legacy, people_list_legacy, notion_list_legacy],
            notes="Legacy Google Contacts groups feed schema.",
        ),
        _view(
            case_id="people_list_contact_groups",
            view_id="people_list_contact_groups::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[people_groups_current, people_list_current, notion_search_current],
            notes="Real version migration: groups feed listing moved to contactGroups.list.",
        ),
        _view(
            case_id="people_update_other_contact_email",
            view_id="people_update_other_contact_email::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[people_other_update_legacy, people_create_legacy, jira_search_legacy],
            notes="Legacy contacts-feed style schema for updating a stored contact email.",
        ),
        _view(
            case_id="people_update_other_contact_email",
            view_id="people_update_other_contact_email::negative_other_contacts_read_only",
            transform_name="negative_other_contacts_read_only",
            shift_kind="negative_near_orbit",
            tools=[people_other_update_current, people_create_current, jira_search_current],
            notes="Real negative near-orbit: People API treats Other Contacts as read-only, so direct mutation is no longer available as a one-step update.",
            admissible_actions=[_ask(), _abstain()],
        ),
        _view(
            case_id="confluence_get_page_storage",
            view_id="confluence_get_page_storage::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[confluence_get_v1, confluence_update_v1, people_list_legacy],
            notes="Legacy Confluence v1 content get schema using expand=body.storage.",
        ),
        _view(
            case_id="confluence_get_page_storage",
            view_id="confluence_get_page_storage::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[confluence_get_v2, confluence_update_v2, people_list_current],
            notes="Real version migration: Confluence page retrieval moved from v1 expand=body.storage to v2 body-format=storage.",
        ),
        _view(
            case_id="confluence_update_page_title",
            view_id="confluence_update_page_title::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[confluence_update_v1, confluence_get_v1, notion_append_legacy],
            notes="Legacy Confluence v1 content update schema for title changes.",
        ),
        _view(
            case_id="confluence_update_page_title",
            view_id="confluence_update_page_title::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[confluence_update_v2, confluence_get_v2, notion_append_current],
            notes="Real version migration: Confluence title updates moved from generic content update to the dedicated v2 page title endpoint.",
        ),
        _view(
            case_id="confluence_list_page_children",
            view_id="confluence_list_page_children::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[confluence_children_v1, confluence_get_v1, drive_list_legacy],
            notes="Legacy Confluence v1 child page listing schema.",
        ),
        _view(
            case_id="confluence_list_page_children",
            view_id="confluence_list_page_children::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[confluence_children_v2, confluence_get_v2, drive_list_current],
            notes="Real version migration: Confluence child page listing moved to /wiki/api/v2/pages/{id}/children.",
        ),
        _view(
            case_id="confluence_list_pages_by_space_key",
            view_id="confluence_list_pages_by_space_key::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[confluence_spacekey_v1, confluence_get_v1, sheets_titles_legacy],
            notes="Legacy Confluence v1 page listing schema using a spaceKey filter.",
        ),
        _view(
            case_id="confluence_list_pages_by_space_key",
            view_id="confluence_list_pages_by_space_key::negative_space_key_lookup_split",
            transform_name="negative_space_key_lookup_split",
            shift_kind="negative_near_orbit",
            tools=[confluence_spaceid_v2, confluence_get_v2, sheets_titles_current],
            notes="Real negative near-orbit: Confluence v2 page listing expects a numeric spaceId, so a raw space key now requires a separate space lookup step.",
            admissible_actions=[_ask(), _abstain()],
        ),
        _view(
            case_id="bitbucket_get_workspace",
            view_id="bitbucket_get_workspace::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[bitbucket_workspace_legacy, bitbucket_repositories_legacy, confluence_get_v1],
            notes="Legacy Bitbucket team profile schema using /2.0/teams/{username}.",
        ),
        _view(
            case_id="bitbucket_get_workspace",
            view_id="bitbucket_get_workspace::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[bitbucket_workspace_current, bitbucket_repositories_current, confluence_get_v2],
            notes="Real version migration: Bitbucket team profile lookup moved from /2.0/teams/{username} to /2.0/workspaces/{workspace}.",
        ),
        _view(
            case_id="bitbucket_list_workspace_repositories",
            view_id="bitbucket_list_workspace_repositories::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[bitbucket_repositories_legacy, bitbucket_workspace_legacy, drive_list_legacy],
            notes="Legacy Bitbucket team repository listing schema.",
        ),
        _view(
            case_id="bitbucket_list_workspace_repositories",
            view_id="bitbucket_list_workspace_repositories::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[bitbucket_repositories_current, bitbucket_workspace_current, drive_list_current],
            notes="Real version migration: Bitbucket repository listing moved from /2.0/teams/{username}/repositories to /2.0/repositories/{workspace}.",
        ),
        _view(
            case_id="bitbucket_list_workspace_members",
            view_id="bitbucket_list_workspace_members::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[bitbucket_members_legacy, bitbucket_workspace_legacy, jira_search_legacy],
            notes="Legacy Bitbucket team member listing schema.",
        ),
        _view(
            case_id="bitbucket_list_workspace_members",
            view_id="bitbucket_list_workspace_members::positive_version_migration",
            transform_name="positive_version_migration",
            shift_kind="positive_orbit",
            tools=[bitbucket_members_current, bitbucket_workspace_current, jira_search_current],
            notes="Real version migration: Bitbucket member listing moved from team-centric to workspace-centric endpoints.",
        ),
        _view(
            case_id="bitbucket_get_legacy_account",
            view_id="bitbucket_get_legacy_account::clean",
            transform_name="clean",
            shift_kind="clean",
            tools=[bitbucket_account_legacy, bitbucket_workspace_legacy, people_groups_current],
            notes="Legacy Bitbucket account lookup schema using /1.0/users/{accountname}.",
        ),
        _view(
            case_id="bitbucket_get_legacy_account",
            view_id="bitbucket_get_legacy_account::negative_account_object_removed",
            transform_name="negative_account_object_removed",
            shift_kind="negative_near_orbit",
            tools=[bitbucket_account_current, bitbucket_workspace_current, people_groups_current],
            notes="Real negative near-orbit: Bitbucket no longer exposes a single account endpoint that can return either a user or a team for a legacy account name.",
            admissible_actions=[_ask(), _abstain()],
        ),
    ]


def build_benchmark_payload() -> dict[str, object]:
    return {
        "tools": build_tools(),
        "cases": build_cases(),
        "views": build_views(),
        "sources": build_sources(),
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
        "# Real Evolution Audit",
        "",
        "This file records the official source anchors and audit intent for the first ToolShift real-evolution split.",
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
    lines.extend(
        [
            "",
            "## Cases",
            "",
        ]
    )
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
    parser = argparse.ArgumentParser(description="Generate the first ToolShift real-evolution benchmark and audit files.")
    parser.add_argument("--output-benchmark", default="data/real_evolution_benchmark.json")
    parser.add_argument("--output-audit", default="data/real_evolution_audit.json")
    parser.add_argument("--output-audit-md", default="history/real_evolution_audit.md")
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

    print(f"Wrote {benchmark_path}")
    print(f"Wrote {audit_path}")
    print(f"Wrote {audit_markdown_path}")


if __name__ == "__main__":
    main()
