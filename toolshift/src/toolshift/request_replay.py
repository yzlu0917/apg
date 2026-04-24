from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .benchmark import BenchmarkSuite, ViewExample
from .embedding_policy import _tool_contract_compatible, _tool_has_description_capability_gap
from .schema import CanonicalAction, ControlTag, RenderedTool, ShiftKind


@dataclass(frozen=True)
class AbstractRequest:
    provider: str
    operation: str
    method: str
    path: str
    query: dict[str, Any]
    body: dict[str, Any]
    effect_signature: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "operation": self.operation,
            "method": self.method,
            "path": self.path,
            "query": self.query,
            "body": self.body,
            "effect_signature": self.effect_signature,
        }

    def fingerprint(self) -> str:
        return json.dumps(self.effect_signature, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class ReplayOutcome:
    emitted: bool
    reason: str
    request: AbstractRequest | None = None


@dataclass(frozen=True)
class ReplayRecord:
    case_id: str
    view_id: str
    transform_name: str
    shift_kind: str
    expected_execute: bool
    passed: bool
    emitted: bool
    reason: str
    request: dict[str, Any] | None
    primary_action: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "view_id": self.view_id,
            "transform_name": self.transform_name,
            "shift_kind": self.shift_kind,
            "expected_execute": self.expected_execute,
            "passed": self.passed,
            "emitted": self.emitted,
            "reason": self.reason,
            "request": self.request,
            "primary_action": self.primary_action,
        }


def replay_primary_action(example: ViewExample) -> ReplayOutcome:
    return replay_action(example, example.case.primary_action)


def replay_action(example: ViewExample, action: CanonicalAction) -> ReplayOutcome:
    if action.control != ControlTag.EXECUTE or action.tool_id is None:
        return ReplayOutcome(emitted=False, reason="non-execute actions do not emit requests")
    rendered_tool = next(
        (tool for tool in example.schema_view.tools if tool.canonical_tool_id == action.tool_id),
        None,
    )
    if rendered_tool is None:
        return ReplayOutcome(emitted=False, reason=f"tool {action.tool_id} is not visible in this schema view")
    if rendered_tool.status == "deprecated":
        return ReplayOutcome(emitted=False, reason="tool is deprecated in this schema view")
    if not _tool_contract_compatible(rendered_tool, action.arguments):
        return ReplayOutcome(emitted=False, reason="tool contract is incompatible with the canonical action arguments")
    if _tool_has_description_capability_gap(rendered_tool, example.case.request):
        return ReplayOutcome(emitted=False, reason="tool description exposes a capability gap for the original request")
    return ReplayOutcome(emitted=True, reason="request rendered", request=_render_request(rendered_tool, action))


def run_request_replay_sanity(suite: BenchmarkSuite) -> tuple[list[ReplayRecord], dict[str, Any]]:
    records: list[ReplayRecord] = []
    clean_fingerprints: dict[str, str] = {}
    positive_fingerprints: dict[str, list[str]] = {}
    for example in suite.examples:
        outcome = replay_primary_action(example)
        expected_execute = any(action.control == ControlTag.EXECUTE for action in example.admissible_actions)
        passed = outcome.emitted if expected_execute else not outcome.emitted
        if outcome.request is not None:
            fingerprint = outcome.request.fingerprint()
            if example.schema_view.shift_kind == ShiftKind.CLEAN:
                clean_fingerprints[example.case.case_id] = fingerprint
            if example.schema_view.shift_kind == ShiftKind.POSITIVE_ORBIT:
                positive_fingerprints.setdefault(example.case.case_id, []).append(fingerprint)
        records.append(
            ReplayRecord(
                case_id=example.case.case_id,
                view_id=example.schema_view.view_id,
                transform_name=example.schema_view.transform_name,
                shift_kind=example.schema_view.shift_kind.value,
                expected_execute=expected_execute,
                passed=passed,
                emitted=outcome.emitted,
                reason=outcome.reason,
                request=outcome.request.to_dict() if outcome.request is not None else None,
                primary_action=example.case.primary_action.to_dict(),
            )
        )

    positive_equivalence_total = 0
    positive_equivalence_correct = 0
    for case_id, fingerprints in positive_fingerprints.items():
        clean_fingerprint = clean_fingerprints.get(case_id)
        if clean_fingerprint is None:
            continue
        for fingerprint in fingerprints:
            positive_equivalence_total += 1
            positive_equivalence_correct += int(fingerprint == clean_fingerprint)

    return records, summarize_replay_records(records, positive_equivalence_correct, positive_equivalence_total)


def summarize_replay_records(
    records: list[ReplayRecord],
    positive_equivalence_correct: int,
    positive_equivalence_total: int,
) -> dict[str, Any]:
    total = len(records)
    execute_expected = [record for record in records if record.expected_execute]
    negative_expected = [record for record in records if not record.expected_execute]
    by_transform: dict[str, dict[str, Any]] = {}
    for transform_name in sorted({record.transform_name for record in records}):
        transform_records = [record for record in records if record.transform_name == transform_name]
        by_transform[transform_name] = {
            "count": len(transform_records),
            "pass_rate": _safe_rate(sum(int(record.passed) for record in transform_records), len(transform_records)),
            "emit_rate": _safe_rate(sum(int(record.emitted) for record in transform_records), len(transform_records)),
        }
    return {
        "count": total,
        "pass_rate": _safe_rate(sum(int(record.passed) for record in records), total),
        "execute_render_pass_rate": _safe_rate(sum(int(record.passed) for record in execute_expected), len(execute_expected)),
        "negative_block_pass_rate": _safe_rate(sum(int(record.passed) for record in negative_expected), len(negative_expected)),
        "emit_rate": _safe_rate(sum(int(record.emitted) for record in records), total),
        "positive_equivalence_rate": _safe_rate(positive_equivalence_correct, positive_equivalence_total),
        "positive_equivalence_count": positive_equivalence_total,
        "by_transform": by_transform,
    }


def _render_request(rendered_tool: RenderedTool, action: CanonicalAction) -> AbstractRequest:
    tool_id = action.tool_id
    assert tool_id is not None
    arguments = dict(action.arguments)

    if tool_id == "notion.blocks.append_paragraph":
        content_field = "paragraph.rich_text" if any(arg.rendered_name == "paragraph.rich_text" for arg in rendered_tool.arguments) else "paragraph.text"
        return AbstractRequest(
            provider="notion",
            operation="blocks.append_paragraph",
            method="PATCH",
            path=f"/v1/blocks/{arguments['block_id']}/children",
            query={},
            body={"children": [{"paragraph": {content_field: arguments["content"]}}]},
            effect_signature={"op": "notion.append_paragraph", "block_id": arguments["block_id"], "content": arguments["content"]},
        )
    if tool_id == "notion.databases.list_shared":
        if rendered_tool.rendered_name == "notion.search":
            body: dict[str, Any] = {}
            if arguments.get("query") is not None:
                body["query"] = arguments["query"]
            if arguments.get("result_type") is not None:
                body["filter.type"] = arguments["result_type"]
            return AbstractRequest(
                provider="notion",
                operation="search",
                method="POST",
                path="/v1/search",
                query={},
                body=body,
                effect_signature={"op": "notion.list_shared_databases"},
            )
        return AbstractRequest(
            provider="notion",
            operation="databases.list",
            method="GET",
            path="/v1/databases",
            query={},
            body={},
            effect_signature={"op": "notion.list_shared_databases"},
        )
    if tool_id == "notion.data_sources.query_entries":
        if any(arg.rendered_name == "data_source_id" for arg in rendered_tool.arguments):
            path = f"/v1/data-sources/{arguments['container_id']}/query"
        else:
            path = f"/v1/databases/{arguments['container_id']}/query"
        body = {}
        if arguments.get("status_filter") is not None:
            body["filter.status"] = arguments["status_filter"]
        return AbstractRequest(
            provider="notion",
            operation="query_entries",
            method="POST",
            path=path,
            query={},
            body=body,
            effect_signature={
                "op": "notion.query_entries",
                "container_id": arguments["container_id"],
                "status_filter": arguments.get("status_filter"),
            },
        )
    if tool_id == "notion.pages.create_in_container":
        parent_field = "parent.data_source_id" if any(arg.rendered_name == "parent.data_source_id" for arg in rendered_tool.arguments) else "parent.database_id"
        return AbstractRequest(
            provider="notion",
            operation="pages.create",
            method="POST",
            path="/v1/pages",
            query={},
            body={parent_field: arguments["parent_id"], "properties.title": arguments["title"]},
            effect_signature={"op": "notion.create_page", "parent_id": arguments["parent_id"], "title": arguments["title"]},
        )
    if tool_id == "slack.conversations.open_group_dm":
        return AbstractRequest(
            provider="slack",
            operation=rendered_tool.rendered_name,
            method="POST",
            path=f"/api/{rendered_tool.rendered_name}",
            query={},
            body={"users": arguments["users_csv"]},
            effect_signature={"op": "slack.open_group_dm", "users_csv": arguments["users_csv"]},
        )
    if tool_id == "slack.files.upload_to_channel":
        body = {"channels": arguments["channel_id"], "file": arguments["file_path"]}
        if arguments.get("title") is not None:
            body["title"] = arguments["title"]
        return AbstractRequest(
            provider="slack",
            operation="files.upload",
            method="POST",
            path="/api/files.upload",
            query={},
            body=body,
            effect_signature={
                "op": "slack.upload_file",
                "channel_id": arguments["channel_id"],
                "file_path": arguments["file_path"],
                "title": arguments.get("title"),
            },
        )
    if tool_id == "slack.conversations.create_channel":
        return AbstractRequest(
            provider="slack",
            operation=rendered_tool.rendered_name,
            method="POST",
            path=f"/api/{rendered_tool.rendered_name}",
            query={},
            body={"name": arguments["channel_name"]},
            effect_signature={"op": "slack.create_channel", "channel_name": arguments["channel_name"]},
        )
    if tool_id == "slack.conversations.list_channels":
        return AbstractRequest(
            provider="slack",
            operation=rendered_tool.rendered_name,
            method="GET",
            path=f"/api/{rendered_tool.rendered_name}",
            query={},
            body={},
            effect_signature={"op": "slack.list_channels"},
        )
    if tool_id == "stripe.customers.create_with_tax_id":
        tax_prefix = "tax_id_data" if any(arg.rendered_name.startswith("tax_id_data") for arg in rendered_tool.arguments) else "tax_info"
        return AbstractRequest(
            provider="stripe",
            operation="customers.create",
            method="POST",
            path="/v1/customers",
            query={},
            body={
                "email": arguments["email"],
                f"{tax_prefix}[type]": arguments["tax_id_type"],
                f"{tax_prefix}[value]": arguments["tax_id_value"],
            },
            effect_signature={
                "op": "stripe.create_customer_with_tax_id",
                "email": arguments["email"],
                "tax_id_type": arguments["tax_id_type"],
                "tax_id_value": arguments["tax_id_value"],
            },
        )
    if tool_id == "stripe.customers.list_with_total_count":
        query = {"limit": arguments["limit"]}
        if any(arg.rendered_name == "expand_total_count" for arg in rendered_tool.arguments) and arguments.get("include_total_count"):
            query["expand[]"] = "total_count"
        return AbstractRequest(
            provider="stripe",
            operation="customers.list",
            method="GET",
            path="/v1/customers",
            query=query,
            body={},
            effect_signature={
                "op": "stripe.list_customers",
                "limit": arguments["limit"],
                "include_total_count": bool(arguments.get("include_total_count")),
            },
        )
    if tool_id == "stripe.checkout.create_session_with_discount":
        coupon_field = "discounts[0][coupon]" if any(arg.rendered_name == "discounts[0][coupon]" for arg in rendered_tool.arguments) else "subscription_data[coupon]"
        return AbstractRequest(
            provider="stripe",
            operation="checkout.sessions.create",
            method="POST",
            path="/v1/checkout/sessions",
            query={},
            body={"line_items[0][price]": arguments["price_id"], coupon_field: arguments["coupon_id"]},
            effect_signature={"op": "stripe.create_checkout_session", "price_id": arguments["price_id"], "coupon_id": arguments["coupon_id"]},
        )
    if tool_id == "stripe.subscriptions.update_default_source":
        body = {}
        if any(arg.rendered_name == "source" for arg in rendered_tool.arguments):
            body["source"] = arguments["source_id"]
        return AbstractRequest(
            provider="stripe",
            operation="subscriptions.update",
            method="POST",
            path=f"/v1/subscriptions/{arguments['subscription_id']}",
            query={},
            body=body,
            effect_signature={"op": "stripe.update_subscription_source", "subscription_id": arguments["subscription_id"], "source_id": arguments["source_id"]},
        )
    if tool_id == "drive.files.list_shared_drive_items":
        query = {}
        path = "/drive/v3/files"
        if any(arg.rendered_name == "teamDriveId" for arg in rendered_tool.arguments):
            query = {
                "teamDriveId": arguments["shared_drive_id"],
                "includeTeamDriveItems": arguments["include_all_drive_items"],
                "supportsTeamDrives": arguments["supports_shared_drives"],
            }
            path = "/drive/v2/files"
        else:
            query = {
                "driveId": arguments["shared_drive_id"],
                "includeItemsFromAllDrives": arguments["include_all_drive_items"],
                "supportsAllDrives": arguments["supports_shared_drives"],
            }
        return AbstractRequest(
            provider="drive",
            operation="files.list",
            method="GET",
            path=path,
            query=query,
            body={},
            effect_signature={
                "op": "drive.list_shared_drive_items",
                "shared_drive_id": arguments["shared_drive_id"],
                "include_all_drive_items": arguments["include_all_drive_items"],
                "supports_shared_drives": arguments["supports_shared_drives"],
            },
        )
    if tool_id == "drive.files.add_parent":
        if rendered_tool.rendered_name == "parents.insert":
            return AbstractRequest(
                provider="drive",
                operation="parents.insert",
                method="POST",
                path=f"/drive/v2/files/{arguments['file_id']}/parents",
                query={},
                body={"id": arguments["parent_id"]},
                effect_signature={"op": "drive.add_parent", "file_id": arguments["file_id"], "parent_id": arguments["parent_id"]},
            )
        return AbstractRequest(
            provider="drive",
            operation="files.update",
            method="PATCH",
            path=f"/drive/v3/files/{arguments['file_id']}",
            query={"addParents": arguments["parent_id"]},
            body={},
            effect_signature={"op": "drive.add_parent", "file_id": arguments["file_id"], "parent_id": arguments["parent_id"]},
        )
    if tool_id == "drive.files.remove_parent":
        if rendered_tool.rendered_name == "parents.delete":
            return AbstractRequest(
                provider="drive",
                operation="parents.delete",
                method="DELETE",
                path=f"/drive/v2/files/{arguments['file_id']}/parents/{arguments['parent_id']}",
                query={},
                body={},
                effect_signature={"op": "drive.remove_parent", "file_id": arguments["file_id"], "parent_id": arguments["parent_id"]},
            )
        return AbstractRequest(
            provider="drive",
            operation="files.update",
            method="PATCH",
            path=f"/drive/v3/files/{arguments['file_id']}",
            query={"removeParents": arguments["parent_id"]},
            body={},
            effect_signature={"op": "drive.remove_parent", "file_id": arguments["file_id"], "parent_id": arguments["parent_id"]},
        )
    if tool_id == "drive.files.add_secondary_parent":
        return AbstractRequest(
            provider="drive",
            operation="parents.insert",
            method="POST",
            path=f"/drive/v2/files/{arguments['file_id']}/parents",
            query={},
            body={"id": arguments["parent_id"]},
            effect_signature={"op": "drive.add_secondary_parent", "file_id": arguments["file_id"], "parent_id": arguments["parent_id"]},
        )
    if tool_id == "jira.issues.assign_user":
        user_field = "accountId" if any(arg.rendered_name == "accountId" for arg in rendered_tool.arguments) else "name"
        version = "3" if user_field == "accountId" else "2"
        return AbstractRequest(
            provider="jira",
            operation="issue.assignee",
            method="PUT",
            path=f"/rest/api/{version}/issue/{arguments['issue_key']}/assignee",
            query={},
            body={user_field: arguments["user_ref"]},
            effect_signature={"op": "jira.assign_user", "issue_key": arguments["issue_key"], "user_ref": arguments["user_ref"]},
        )
    if tool_id == "jira.issues.add_watcher":
        user_field = "accountId" if any(arg.rendered_name == "accountId" for arg in rendered_tool.arguments) else "username"
        version = "3" if user_field == "accountId" else "2"
        return AbstractRequest(
            provider="jira",
            operation="issue.watchers",
            method="POST",
            path=f"/rest/api/{version}/issue/{arguments['issue_key']}/watchers",
            query={},
            body={user_field: arguments["user_ref"]},
            effect_signature={"op": "jira.add_watcher", "issue_key": arguments["issue_key"], "user_ref": arguments["user_ref"]},
        )
    if tool_id == "jira.users.search_assignable":
        query_field = "query" if any(arg.rendered_name == "query" for arg in rendered_tool.arguments) else "username"
        version = "3" if query_field == "query" else "2"
        return AbstractRequest(
            provider="jira",
            operation="user.assignable.search",
            method="GET",
            path=f"/rest/api/{version}/user/assignable/search",
            query={"project": arguments["project_key"], query_field: arguments["user_query"]},
            body={},
            effect_signature={"op": "jira.search_assignable_user", "project_key": arguments["project_key"], "user_query": arguments["user_query"]},
        )
    if tool_id == "jira.users.search_by_legacy_username":
        query_field = "query" if any(arg.rendered_name == "query" for arg in rendered_tool.arguments) else "username"
        version = "3" if query_field == "query" else "2"
        return AbstractRequest(
            provider="jira",
            operation="user.assignable.search",
            method="GET",
            path=f"/rest/api/{version}/user/assignable/search",
            query={"project": arguments["project_key"], query_field: arguments["legacy_username"]},
            body={},
            effect_signature={"op": "jira.search_legacy_username", "project_key": arguments["project_key"], "legacy_username": arguments["legacy_username"]},
        )
    if tool_id == "sheets.spreadsheets.get_sheet_titles":
        if rendered_tool.rendered_name == "worksheets.feed":
            return AbstractRequest(
                provider="sheets",
                operation="worksheets.feed",
                method="GET",
                path=f"/feeds/worksheets/{arguments['spreadsheet_id']}/private/full",
                query={},
                body={},
                effect_signature={"op": "sheets.get_sheet_titles", "spreadsheet_id": arguments["spreadsheet_id"]},
            )
        return AbstractRequest(
            provider="sheets",
            operation="spreadsheets.get",
            method="GET",
            path=f"/v4/spreadsheets/{arguments['spreadsheet_id']}",
            query={"fields": "sheets.properties.title"},
            body={},
            effect_signature={"op": "sheets.get_sheet_titles", "spreadsheet_id": arguments["spreadsheet_id"]},
        )
    if tool_id == "sheets.values.append_row":
        row_values = _csv_cells(arguments["row_values_csv"])
        if rendered_tool.rendered_name == "list.feed.insert":
            return AbstractRequest(
                provider="sheets",
                operation="list.feed.insert",
                method="POST",
                path=f"/feeds/list/{arguments['spreadsheet_id']}/{arguments['worksheet_name']}/private/full",
                query={},
                body={"gsx$row": arguments["row_values_csv"]},
                effect_signature={
                    "op": "sheets.append_row",
                    "spreadsheet_id": arguments["spreadsheet_id"],
                    "worksheet_name": arguments["worksheet_name"],
                    "row_values": row_values,
                },
            )
        return AbstractRequest(
            provider="sheets",
            operation="spreadsheets.values.append",
            method="POST",
            path=f"/v4/spreadsheets/{arguments['spreadsheet_id']}/values/{arguments['worksheet_name']}:append",
            query={"valueInputOption": "RAW"},
            body={"values": [row_values]},
            effect_signature={
                "op": "sheets.append_row",
                "spreadsheet_id": arguments["spreadsheet_id"],
                "worksheet_name": arguments["worksheet_name"],
                "row_values": row_values,
            },
        )
    if tool_id == "sheets.values.update_formula":
        if rendered_tool.rendered_name == "cells.feed.update":
            return AbstractRequest(
                provider="sheets",
                operation="cells.feed.update",
                method="PUT",
                path=f"/feeds/cells/{arguments['spreadsheet_id']}/private/full/{arguments['range_a1']}",
                query={},
                body={"inputValue": arguments["formula"]},
                effect_signature={
                    "op": "sheets.update_formula",
                    "spreadsheet_id": arguments["spreadsheet_id"],
                    "range_a1": arguments["range_a1"],
                    "formula": arguments["formula"],
                },
            )
        return AbstractRequest(
            provider="sheets",
            operation="spreadsheets.values.update",
            method="PUT",
            path=f"/v4/spreadsheets/{arguments['spreadsheet_id']}/values/{arguments['range_a1']}",
            query={"valueInputOption": "USER_ENTERED"},
            body={"values": [[arguments["formula"]]]},
            effect_signature={
                "op": "sheets.update_formula",
                "spreadsheet_id": arguments["spreadsheet_id"],
                "range_a1": arguments["range_a1"],
                "formula": arguments["formula"],
            },
        )
    if tool_id == "sheets.spreadsheets.list_accessible":
        if rendered_tool.rendered_name == "spreadsheets.feed":
            return AbstractRequest(
                provider="sheets",
                operation="spreadsheets.feed",
                method="GET",
                path="/feeds/spreadsheets/private/full",
                query={},
                body={},
                effect_signature={"op": "sheets.list_accessible_spreadsheets"},
            )
        return AbstractRequest(
            provider="sheets",
            operation="drive.files.list",
            method="GET",
            path="/drive/v3/files",
            query={"q": "mimeType='application/vnd.google-apps.spreadsheet'"},
            body={},
            effect_signature={"op": "sheets.list_accessible_spreadsheets"},
        )
    if tool_id == "people.contacts.list_my_contacts":
        if rendered_tool.rendered_name == "contacts.feed":
            return AbstractRequest(
                provider="people",
                operation="contacts.feed",
                method="GET",
                path="/m8/feeds/contacts/default/full",
                query={"max-results": arguments["page_size"]},
                body={},
                effect_signature={"op": "people.list_my_contacts", "page_size": arguments["page_size"]},
            )
        return AbstractRequest(
            provider="people",
            operation="people.connections.list",
            method="GET",
            path="/v1/people/me/connections",
            query={"pageSize": arguments["page_size"], "personFields": "names,emailAddresses"},
            body={},
            effect_signature={"op": "people.list_my_contacts", "page_size": arguments["page_size"]},
        )
    if tool_id == "people.contacts.create_contact":
        if rendered_tool.rendered_name == "contacts.feed.insert":
            return AbstractRequest(
                provider="people",
                operation="contacts.feed.insert",
                method="POST",
                path="/m8/feeds/contacts/default/full",
                query={},
                body={"gd$name": arguments["given_name"], "gd$email": arguments["email"]},
                effect_signature={
                    "op": "people.create_contact",
                    "given_name": arguments["given_name"],
                    "email": arguments["email"],
                },
            )
        return AbstractRequest(
            provider="people",
            operation="people.createContact",
            method="POST",
            path="/v1/people:createContact",
            query={"personFields": "names,emailAddresses"},
            body={"names": [arguments["given_name"]], "emailAddresses": [arguments["email"]]},
            effect_signature={
                "op": "people.create_contact",
                "given_name": arguments["given_name"],
                "email": arguments["email"],
            },
        )
    if tool_id == "people.contact_groups.list":
        if rendered_tool.rendered_name == "groups.feed":
            return AbstractRequest(
                provider="people",
                operation="groups.feed",
                method="GET",
                path="/m8/feeds/groups/default/full",
                query={},
                body={},
                effect_signature={"op": "people.list_contact_groups"},
            )
        return AbstractRequest(
            provider="people",
            operation="contactGroups.list",
            method="GET",
            path="/v1/contactGroups",
            query={"groupFields": "name"},
            body={},
            effect_signature={"op": "people.list_contact_groups"},
        )
    if tool_id == "people.other_contacts.update_email":
        if rendered_tool.rendered_name == "contacts.feed.update":
            return AbstractRequest(
                provider="people",
                operation="contacts.feed.update",
                method="PUT",
                path=f"/m8/feeds/contacts/default/full/{arguments['other_contact_id']}",
                query={},
                body={"gd$email": arguments["email"]},
                effect_signature={
                    "op": "people.update_other_contact_email",
                    "other_contact_id": arguments["other_contact_id"],
                    "email": arguments["email"],
                },
            )
        return AbstractRequest(
            provider="people",
            operation="people.updateContact",
            method="PATCH",
            path=f"/v1/people/{arguments['other_contact_id']}:updateContact",
            query={
                "updatePersonFields": "emailAddresses",
                "personFields": "emailAddresses",
            },
            body={"emailAddresses": [arguments["email"]]},
            effect_signature={
                "op": "people.update_other_contact_email",
                "other_contact_id": arguments["other_contact_id"],
                "email": arguments["email"],
            },
        )
    if tool_id == "confluence.pages.get_storage":
        if rendered_tool.rendered_name == "content.get":
            return AbstractRequest(
                provider="confluence",
                operation="content.get",
                method="GET",
                path=f"/wiki/rest/api/content/{arguments['page_id']}",
                query={"expand": "body.storage"},
                body={},
                effect_signature={"op": "confluence.get_page_storage", "page_id": arguments["page_id"]},
            )
        return AbstractRequest(
            provider="confluence",
            operation="pages.get",
            method="GET",
            path=f"/wiki/api/v2/pages/{arguments['page_id']}",
            query={"body-format": "storage"},
            body={},
            effect_signature={"op": "confluence.get_page_storage", "page_id": arguments["page_id"]},
        )
    if tool_id == "confluence.pages.update_title":
        if rendered_tool.rendered_name == "content.update":
            return AbstractRequest(
                provider="confluence",
                operation="content.update",
                method="PUT",
                path=f"/wiki/rest/api/content/{arguments['page_id']}",
                query={},
                body={"title": arguments["title"]},
                effect_signature={
                    "op": "confluence.update_page_title",
                    "page_id": arguments["page_id"],
                    "title": arguments["title"],
                },
            )
        return AbstractRequest(
            provider="confluence",
            operation="pages.updateTitle",
            method="PUT",
            path=f"/wiki/api/v2/pages/{arguments['page_id']}/title",
            query={},
            body={"status": "current", "title": arguments["title"]},
            effect_signature={
                "op": "confluence.update_page_title",
                "page_id": arguments["page_id"],
                "title": arguments["title"],
            },
        )
    if tool_id == "confluence.pages.list_children":
        if rendered_tool.rendered_name == "content.child.page":
            return AbstractRequest(
                provider="confluence",
                operation="content.child.page",
                method="GET",
                path=f"/wiki/rest/api/content/{arguments['page_id']}/child/page",
                query={},
                body={},
                effect_signature={"op": "confluence.list_page_children", "page_id": arguments["page_id"]},
            )
        return AbstractRequest(
            provider="confluence",
            operation="pages.children.list",
            method="GET",
            path=f"/wiki/api/v2/pages/{arguments['page_id']}/children",
            query={},
            body={},
            effect_signature={"op": "confluence.list_page_children", "page_id": arguments["page_id"]},
        )
    if tool_id == "confluence.pages.list_by_space_key":
        if rendered_tool.rendered_name == "content.list":
            return AbstractRequest(
                provider="confluence",
                operation="content.list",
                method="GET",
                path="/wiki/rest/api/content",
                query={"spaceKey": arguments["space_key"], "type": "page"},
                body={},
                effect_signature={"op": "confluence.list_pages_by_space_key", "space_key": arguments["space_key"]},
            )
        return AbstractRequest(
            provider="confluence",
            operation="pages.in.space",
            method="GET",
            path=f"/wiki/api/v2/spaces/{arguments['space_key']}/pages",
            query={},
            body={},
            effect_signature={"op": "confluence.list_pages_by_space_key", "space_key": arguments["space_key"]},
        )
    if tool_id == "bitbucket.workspaces.get":
        if rendered_tool.rendered_name == "teams.get":
            return AbstractRequest(
                provider="bitbucket",
                operation="teams.get",
                method="GET",
                path=f"/2.0/teams/{arguments['workspace_slug']}",
                query={},
                body={},
                effect_signature={"op": "bitbucket.get_workspace", "workspace_slug": arguments["workspace_slug"]},
            )
        return AbstractRequest(
            provider="bitbucket",
            operation="workspaces.get",
            method="GET",
            path=f"/2.0/workspaces/{arguments['workspace_slug']}",
            query={},
            body={},
            effect_signature={"op": "bitbucket.get_workspace", "workspace_slug": arguments["workspace_slug"]},
        )
    if tool_id == "bitbucket.repositories.list_workspace":
        if rendered_tool.rendered_name == "teams.repositories.list":
            return AbstractRequest(
                provider="bitbucket",
                operation="teams.repositories.list",
                method="GET",
                path=f"/2.0/teams/{arguments['workspace_slug']}/repositories",
                query={},
                body={},
                effect_signature={
                    "op": "bitbucket.list_workspace_repositories",
                    "workspace_slug": arguments["workspace_slug"],
                },
            )
        return AbstractRequest(
            provider="bitbucket",
            operation="repositories.listByWorkspace",
            method="GET",
            path=f"/2.0/repositories/{arguments['workspace_slug']}",
            query={},
            body={},
            effect_signature={
                "op": "bitbucket.list_workspace_repositories",
                "workspace_slug": arguments["workspace_slug"],
            },
        )
    if tool_id == "bitbucket.workspaces.list_members":
        if rendered_tool.rendered_name == "teams.members.list":
            return AbstractRequest(
                provider="bitbucket",
                operation="teams.members.list",
                method="GET",
                path=f"/2.0/teams/{arguments['workspace_slug']}/members",
                query={},
                body={},
                effect_signature={
                    "op": "bitbucket.list_workspace_members",
                    "workspace_slug": arguments["workspace_slug"],
                },
            )
        return AbstractRequest(
            provider="bitbucket",
            operation="workspaces.members.list",
            method="GET",
            path=f"/2.0/workspaces/{arguments['workspace_slug']}/members",
            query={},
            body={},
            effect_signature={
                "op": "bitbucket.list_workspace_members",
                "workspace_slug": arguments["workspace_slug"],
            },
        )
    if tool_id == "bitbucket.accounts.get_legacy_account":
        if rendered_tool.rendered_name == "users.getLegacyAccount":
            return AbstractRequest(
                provider="bitbucket",
                operation="users.getLegacyAccount",
                method="GET",
                path=f"/1.0/users/{arguments['account_name']}",
                query={},
                body={},
                effect_signature={
                    "op": "bitbucket.get_legacy_account",
                    "account_name": arguments["account_name"],
                },
            )
        return AbstractRequest(
            provider="bitbucket",
            operation="workspaces.get",
            method="GET",
            path=f"/2.0/workspaces/{arguments['account_name']}",
            query={},
            body={},
            effect_signature={
                "op": "bitbucket.get_legacy_account",
                "account_name": arguments["account_name"],
            },
        )

    raise ValueError(f"unsupported request rendering for {tool_id}")


def _safe_rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def _csv_cells(raw_value: Any) -> list[str]:
    return [part.strip() for part in str(raw_value).split(",")]
