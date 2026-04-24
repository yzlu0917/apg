from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from .benchmark import BenchmarkSuite, ViewExample
from .embedding_policy import _tool_contract_compatible, _tool_has_description_capability_gap
from .schema import CanonicalAction, ControlTag, ShiftKind


@dataclass
class MockToolState:
    notion_blocks: dict[str, list[str]]
    notion_shared_databases: list[str]
    notion_entries: dict[str, list[dict[str, Any]]]
    notion_pages: dict[str, list[str]]
    slack_channels: list[str]
    slack_uploaded_files: dict[str, list[str]]
    slack_group_dms: set[str]
    stripe_customers: list[str]
    stripe_customer_tax_ids: dict[str, tuple[str, str]]
    stripe_checkout_sessions: list[dict[str, Any]]
    stripe_subscriptions: dict[str, dict[str, Any]]
    drive_shared_drive_items: dict[str, list[str]]
    drive_file_parents: dict[str, list[str]]
    jira_issue_assignees: dict[str, str | None]
    jira_issue_watchers: dict[str, set[str]]
    jira_assignable_users: dict[str, dict[str, str]]
    sheets_sheet_titles: dict[str, list[str]]
    sheets_rows: dict[str, list[list[str]]]
    sheets_cells: dict[str, dict[str, str]]
    sheets_accessible_spreadsheets: list[str]
    people_contacts: dict[str, dict[str, str]]
    people_contact_groups: list[str]
    people_other_contacts: dict[str, dict[str, str]]
    confluence_pages: dict[str, dict[str, Any]]
    bitbucket_workspaces: dict[str, dict[str, Any]]
    bitbucket_legacy_accounts: dict[str, dict[str, str]]


@dataclass(frozen=True)
class ExecutionOutcome:
    executed: bool
    request_satisfied: bool
    reason: str
    effect: dict[str, Any]


@dataclass(frozen=True)
class ExecutionRecord:
    case_id: str
    view_id: str
    transform_name: str
    shift_kind: str
    expected_execute: bool
    passed: bool
    executed: bool
    request_satisfied: bool
    reason: str
    effect: dict[str, Any]
    primary_action: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "view_id": self.view_id,
            "transform_name": self.transform_name,
            "shift_kind": self.shift_kind,
            "expected_execute": self.expected_execute,
            "passed": self.passed,
            "executed": self.executed,
            "request_satisfied": self.request_satisfied,
            "reason": self.reason,
            "effect": self.effect,
            "primary_action": self.primary_action,
        }


def build_default_mock_state() -> MockToolState:
    return MockToolState(
        notion_blocks={"blk_123": []},
        notion_shared_databases=["db_notes", "db_tasks"],
        notion_entries={
            "db_tasks": [
                {"id": "task_1", "status": "overdue"},
                {"id": "task_2", "status": "done"},
                {"id": "task_3", "status": "overdue"},
            ]
        },
        notion_pages={"db_tasks": []},
        slack_channels=["eng", "general", "ops"],
        slack_uploaded_files={"C123": []},
        slack_group_dms=set(),
        stripe_customers=[f"cus_{index:03d}" for index in range(40)],
        stripe_customer_tax_ids={},
        stripe_checkout_sessions=[],
        stripe_subscriptions={"sub_123": {"source_id": "src_old"}},
        drive_shared_drive_items={
            "drv_eng": ["file_plan", "file_brief", "file_specs"],
            "drv_fin": ["file_invoice"],
        },
        drive_file_parents={
            "file_brief": [],
            "file_archive": ["fld_archive"],
            "file_plan": ["fld_eng"],
        },
        jira_issue_assignees={"ENG-7": None},
        jira_issue_watchers={"ENG-7": set()},
        jira_assignable_users={
            "ENG": {
                "acct_alice": "acct_alice",
                "acct_bob": "acct_bob",
                "alice": "acct_alice",
            }
        },
        sheets_sheet_titles={
            "sh_budget": ["ws_summary", "ws_hours"],
            "sh_ops": ["ws_backlog"],
        },
        sheets_rows={
            "sh_budget:ws_hours": [["Alice", "8"], ["Bob", "6"]],
        },
        sheets_cells={
            "sh_budget": {
                "ws_summary!A1": "=SUM(B1:B2)",
            }
        },
        sheets_accessible_spreadsheets=["sh_budget", "sh_ops"],
        people_contacts={
            "people/c_alice": {"name": "Alice Example", "email": "alice@example.com"},
            "people/c_bob": {"name": "Bob Example", "email": "bob@example.com"},
            "people/c_carla": {"name": "Carla Example", "email": "carla@example.com"},
        },
        people_contact_groups=["Friends", "Project Team", "Vendors"],
        people_other_contacts={
            "oc_alice": {"name": "Alice Other", "email": "alice.old@example.com"},
            "oc_bob": {"name": "Bob Other", "email": "bob.old@example.com"},
        },
        confluence_pages={
            "2001": {
                "title": "Project Overview",
                "body_html": "<p>Kickoff notes</p>",
                "parent_id": None,
                "space_key": "ENG",
            },
            "2002": {
                "title": "Retro",
                "body_html": "<p>Retro notes</p>",
                "parent_id": "2001",
                "space_key": "ENG",
            },
            "2003": {
                "title": "Demo",
                "body_html": "<p>Demo notes</p>",
                "parent_id": "2001",
                "space_key": "ENG",
            },
            "3001": {
                "title": "Ops Runbook",
                "body_html": "<p>Runbook</p>",
                "parent_id": None,
                "space_key": "OPS",
            },
        },
        bitbucket_workspaces={
            "eng-team": {
                "display_name": "Eng Team",
                "repo_slugs": ["eng-api", "eng-web", "eng-ops"],
                "member_ids": ["acct_alice", "acct_bob"],
            },
            "ops-team": {
                "display_name": "Ops Team",
                "repo_slugs": ["ops-runbook"],
                "member_ids": ["acct_carla"],
            },
        },
        bitbucket_legacy_accounts={
            "eng-team": {"kind": "team", "display_name": "Eng Team"},
            "alice": {"kind": "user", "display_name": "Alice Example"},
        },
    )


def simulate_primary_action(example: ViewExample) -> ExecutionOutcome:
    return simulate_action(example, example.case.primary_action)


def simulate_action(example: ViewExample, action: CanonicalAction) -> ExecutionOutcome:
    if action.control != ControlTag.EXECUTE or action.tool_id is None:
        return ExecutionOutcome(
            executed=False,
            request_satisfied=False,
            reason="non-execute actions are not simulated in execution sanity",
            effect={},
        )
    rendered_tool = next(
        (tool for tool in example.schema_view.tools if tool.canonical_tool_id == action.tool_id),
        None,
    )
    if rendered_tool is None:
        return ExecutionOutcome(
            executed=False,
            request_satisfied=False,
            reason=f"tool {action.tool_id} is not visible in this schema view",
            effect={},
        )
    if rendered_tool.status == "deprecated":
        return ExecutionOutcome(
            executed=False,
            request_satisfied=False,
            reason="tool is deprecated in this schema view",
            effect={},
        )
    if not _tool_contract_compatible(rendered_tool, action.arguments):
        return ExecutionOutcome(
            executed=False,
            request_satisfied=False,
            reason="tool contract is incompatible with the canonical action arguments",
            effect={},
        )
    if _tool_has_description_capability_gap(rendered_tool, example.case.request):
        return ExecutionOutcome(
            executed=False,
            request_satisfied=False,
            reason="tool description exposes a capability gap for the original request",
            effect={},
        )
    state = build_default_mock_state()
    return _apply_action(state, action)


def run_execution_sanity(suite: BenchmarkSuite) -> tuple[list[ExecutionRecord], dict[str, Any]]:
    records: list[ExecutionRecord] = []
    clean_effects: dict[str, str] = {}
    positive_effects: dict[str, list[str]] = {}
    for example in suite.examples:
        outcome = simulate_primary_action(example)
        expected_execute = any(action.control == ControlTag.EXECUTE for action in example.admissible_actions)
        passed = outcome.request_satisfied if expected_execute else not outcome.request_satisfied
        effect_fingerprint = json.dumps(outcome.effect, sort_keys=True, separators=(",", ":"))
        if example.schema_view.shift_kind == ShiftKind.CLEAN and outcome.request_satisfied:
            clean_effects[example.case.case_id] = effect_fingerprint
        if example.schema_view.shift_kind == ShiftKind.POSITIVE_ORBIT and outcome.request_satisfied:
            positive_effects.setdefault(example.case.case_id, []).append(effect_fingerprint)
        records.append(
            ExecutionRecord(
                case_id=example.case.case_id,
                view_id=example.schema_view.view_id,
                transform_name=example.schema_view.transform_name,
                shift_kind=example.schema_view.shift_kind.value,
                expected_execute=expected_execute,
                passed=passed,
                executed=outcome.executed,
                request_satisfied=outcome.request_satisfied,
                reason=outcome.reason,
                effect=outcome.effect,
                primary_action=example.case.primary_action.to_dict(),
            )
        )

    positive_equivalence_total = 0
    positive_equivalence_correct = 0
    for case_id, fingerprints in positive_effects.items():
        clean_fingerprint = clean_effects.get(case_id)
        if clean_fingerprint is None:
            continue
        for fingerprint in fingerprints:
            positive_equivalence_total += 1
            positive_equivalence_correct += int(fingerprint == clean_fingerprint)

    return records, summarize_execution_records(records, positive_equivalence_correct, positive_equivalence_total)


def summarize_execution_records(
    records: list[ExecutionRecord],
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
            "execute_rate": _safe_rate(sum(int(record.executed) for record in transform_records), len(transform_records)),
            "satisfied_rate": _safe_rate(sum(int(record.request_satisfied) for record in transform_records), len(transform_records)),
        }
    return {
        "count": total,
        "pass_rate": _safe_rate(sum(int(record.passed) for record in records), total),
        "execute_expected_pass_rate": _safe_rate(sum(int(record.passed) for record in execute_expected), len(execute_expected)),
        "negative_guard_pass_rate": _safe_rate(sum(int(record.passed) for record in negative_expected), len(negative_expected)),
        "execute_rate": _safe_rate(sum(int(record.executed) for record in records), total),
        "satisfied_rate": _safe_rate(sum(int(record.request_satisfied) for record in records), total),
        "positive_equivalence_rate": _safe_rate(positive_equivalence_correct, positive_equivalence_total),
        "positive_equivalence_count": positive_equivalence_total,
        "by_transform": by_transform,
    }


def _apply_action(state: MockToolState, action: CanonicalAction) -> ExecutionOutcome:
    tool_id = action.tool_id
    arguments = deepcopy(action.arguments)
    if tool_id == "notion.blocks.append_paragraph":
        children = state.notion_blocks.setdefault(str(arguments["block_id"]), [])
        children.append(str(arguments["content"]))
        return ExecutionOutcome(
            executed=True,
            request_satisfied=children[-1] == str(arguments["content"]),
            reason="paragraph appended",
            effect={"block_id": arguments["block_id"], "appended_content": children[-1]},
        )
    if tool_id == "notion.databases.list_shared":
        databases = sorted(state.notion_shared_databases)
        return ExecutionOutcome(
            executed=True,
            request_satisfied=True,
            reason="shared databases listed",
            effect={"shared_database_ids": databases},
        )
    if tool_id == "notion.data_sources.query_entries":
        entries = deepcopy(state.notion_entries.get(str(arguments["container_id"]), []))
        status_filter = arguments.get("status_filter")
        if status_filter is not None:
            entries = [entry for entry in entries if entry["status"] == status_filter]
        return ExecutionOutcome(
            executed=True,
            request_satisfied=all(entry["status"] == status_filter for entry in entries) if status_filter is not None else True,
            reason="container entries queried",
            effect={"container_id": arguments["container_id"], "entry_ids": [entry["id"] for entry in entries]},
        )
    if tool_id == "notion.pages.create_in_container":
        parent_id = str(arguments["parent_id"])
        title = str(arguments["title"])
        state.notion_pages.setdefault(parent_id, []).append(title)
        return ExecutionOutcome(
            executed=True,
            request_satisfied=title in state.notion_pages[parent_id],
            reason="page created",
            effect={"parent_id": parent_id, "title": title},
        )
    if tool_id == "slack.conversations.open_group_dm":
        participants = ",".join(sorted(str(arguments["users_csv"]).split(",")))
        state.slack_group_dms.add(participants)
        return ExecutionOutcome(
            executed=True,
            request_satisfied=participants in state.slack_group_dms,
            reason="group dm opened",
            effect={"participants": participants},
        )
    if tool_id == "slack.files.upload_to_channel":
        channel_id = str(arguments["channel_id"])
        title = str(arguments.get("title") or arguments["file_path"])
        state.slack_uploaded_files.setdefault(channel_id, []).append(title)
        return ExecutionOutcome(
            executed=True,
            request_satisfied=title in state.slack_uploaded_files[channel_id],
            reason="file uploaded",
            effect={"channel_id": channel_id, "uploaded_title": title},
        )
    if tool_id == "slack.conversations.create_channel":
        channel_name = str(arguments["channel_name"])
        if channel_name not in state.slack_channels:
            state.slack_channels.append(channel_name)
            state.slack_channels.sort()
        return ExecutionOutcome(
            executed=True,
            request_satisfied=channel_name in state.slack_channels,
            reason="channel created",
            effect={"channel_name": channel_name},
        )
    if tool_id == "slack.conversations.list_channels":
        channels = sorted(state.slack_channels)
        return ExecutionOutcome(
            executed=True,
            request_satisfied=True,
            reason="channels listed",
            effect={"channel_names": channels},
        )
    if tool_id == "stripe.customers.create_with_tax_id":
        customer_id = f"cus_{len(state.stripe_customers):03d}"
        state.stripe_customers.append(customer_id)
        state.stripe_customer_tax_ids[customer_id] = (str(arguments["tax_id_type"]), str(arguments["tax_id_value"]))
        return ExecutionOutcome(
            executed=True,
            request_satisfied=state.stripe_customer_tax_ids[customer_id] == (
                str(arguments["tax_id_type"]),
                str(arguments["tax_id_value"]),
            ),
            reason="customer created with tax id",
            effect={"customer_id": customer_id, "email": str(arguments["email"])},
        )
    if tool_id == "stripe.customers.list_with_total_count":
        limit = int(arguments["limit"])
        customer_ids = state.stripe_customers[:limit]
        effect = {"customer_ids": customer_ids}
        if bool(arguments.get("include_total_count")):
            effect["total_count"] = len(state.stripe_customers)
        return ExecutionOutcome(
            executed=True,
            request_satisfied=not bool(arguments.get("include_total_count")) or "total_count" in effect,
            reason="customers listed",
            effect=effect,
        )
    if tool_id == "stripe.checkout.create_session_with_discount":
        session_id = f"cs_{len(state.stripe_checkout_sessions):03d}"
        session = {
            "session_id": session_id,
            "price_id": str(arguments["price_id"]),
            "coupon_id": str(arguments["coupon_id"]),
        }
        state.stripe_checkout_sessions.append(session)
        return ExecutionOutcome(
            executed=True,
            request_satisfied=session in state.stripe_checkout_sessions,
            reason="checkout session created",
            effect=session,
        )
    if tool_id == "stripe.subscriptions.update_default_source":
        subscription_id = str(arguments["subscription_id"])
        source_id = str(arguments["source_id"])
        subscription = state.stripe_subscriptions.setdefault(subscription_id, {})
        subscription["source_id"] = source_id
        return ExecutionOutcome(
            executed=True,
            request_satisfied=state.stripe_subscriptions[subscription_id].get("source_id") == source_id,
            reason="subscription source updated",
            effect={"subscription_id": subscription_id, "source_id": source_id},
        )
    if tool_id == "drive.files.list_shared_drive_items":
        shared_drive_id = str(arguments["shared_drive_id"])
        items = deepcopy(state.drive_shared_drive_items.get(shared_drive_id, []))
        return ExecutionOutcome(
            executed=True,
            request_satisfied=True,
            reason="shared drive items listed",
            effect={"shared_drive_id": shared_drive_id, "item_ids": items},
        )
    if tool_id == "drive.files.add_parent":
        file_id = str(arguments["file_id"])
        parent_id = str(arguments["parent_id"])
        parents = state.drive_file_parents.setdefault(file_id, [])
        if parent_id not in parents:
            parents.append(parent_id)
            parents.sort()
        return ExecutionOutcome(
            executed=True,
            request_satisfied=parent_id in state.drive_file_parents[file_id],
            reason="drive parent added",
            effect={"file_id": file_id, "parent_ids": deepcopy(state.drive_file_parents[file_id])},
        )
    if tool_id == "drive.files.remove_parent":
        file_id = str(arguments["file_id"])
        parent_id = str(arguments["parent_id"])
        parents = state.drive_file_parents.setdefault(file_id, [])
        if parent_id in parents:
            parents.remove(parent_id)
        return ExecutionOutcome(
            executed=True,
            request_satisfied=parent_id not in state.drive_file_parents[file_id],
            reason="drive parent removed",
            effect={"file_id": file_id, "parent_ids": deepcopy(state.drive_file_parents[file_id])},
        )
    if tool_id == "drive.files.add_secondary_parent":
        file_id = str(arguments["file_id"])
        parent_id = str(arguments["parent_id"])
        parents = state.drive_file_parents.setdefault(file_id, [])
        if parent_id not in parents:
            parents.append(parent_id)
            parents.sort()
        return ExecutionOutcome(
            executed=True,
            request_satisfied=parent_id in state.drive_file_parents[file_id] and len(state.drive_file_parents[file_id]) >= 2,
            reason="drive secondary parent added",
            effect={"file_id": file_id, "parent_ids": deepcopy(state.drive_file_parents[file_id])},
        )
    if tool_id == "jira.issues.assign_user":
        issue_key = str(arguments["issue_key"])
        user_ref = str(arguments["user_ref"])
        state.jira_issue_assignees[issue_key] = user_ref
        return ExecutionOutcome(
            executed=True,
            request_satisfied=state.jira_issue_assignees[issue_key] == user_ref,
            reason="jira issue assigned",
            effect={"issue_key": issue_key, "assignee": user_ref},
        )
    if tool_id == "jira.issues.add_watcher":
        issue_key = str(arguments["issue_key"])
        user_ref = str(arguments["user_ref"])
        watchers = state.jira_issue_watchers.setdefault(issue_key, set())
        watchers.add(user_ref)
        return ExecutionOutcome(
            executed=True,
            request_satisfied=user_ref in state.jira_issue_watchers[issue_key],
            reason="jira watcher added",
            effect={"issue_key": issue_key, "watchers": sorted(state.jira_issue_watchers[issue_key])},
        )
    if tool_id == "jira.users.search_assignable":
        project_key = str(arguments["project_key"])
        user_query = str(arguments["user_query"])
        match = state.jira_assignable_users.get(project_key, {}).get(user_query)
        return ExecutionOutcome(
            executed=True,
            request_satisfied=match is not None,
            reason="jira assignable user searched",
            effect={"project_key": project_key, "matched_user_ref": match},
        )
    if tool_id == "jira.users.search_by_legacy_username":
        project_key = str(arguments["project_key"])
        legacy_username = str(arguments["legacy_username"])
        match = state.jira_assignable_users.get(project_key, {}).get(legacy_username)
        return ExecutionOutcome(
            executed=True,
            request_satisfied=match is not None,
            reason="jira legacy username searched",
            effect={"project_key": project_key, "matched_user_ref": match},
        )
    if tool_id == "sheets.spreadsheets.get_sheet_titles":
        spreadsheet_id = str(arguments["spreadsheet_id"])
        titles = deepcopy(state.sheets_sheet_titles.get(spreadsheet_id, []))
        return ExecutionOutcome(
            executed=True,
            request_satisfied=bool(titles),
            reason="sheet titles listed",
            effect={"spreadsheet_id": spreadsheet_id, "sheet_titles": titles},
        )
    if tool_id == "sheets.values.append_row":
        spreadsheet_id = str(arguments["spreadsheet_id"])
        worksheet_name = str(arguments["worksheet_name"])
        row_values = _csv_cells(arguments["row_values_csv"])
        row_key = f"{spreadsheet_id}:{worksheet_name}"
        state.sheets_rows.setdefault(row_key, []).append(row_values)
        return ExecutionOutcome(
            executed=True,
            request_satisfied=row_values in state.sheets_rows[row_key],
            reason="sheet row appended",
            effect={
                "spreadsheet_id": spreadsheet_id,
                "worksheet_name": worksheet_name,
                "row_values": row_values,
            },
        )
    if tool_id == "sheets.values.update_formula":
        spreadsheet_id = str(arguments["spreadsheet_id"])
        range_a1 = str(arguments["range_a1"])
        formula = str(arguments["formula"])
        sheet_cells = state.sheets_cells.setdefault(spreadsheet_id, {})
        sheet_cells[range_a1] = formula
        return ExecutionOutcome(
            executed=True,
            request_satisfied=sheet_cells[range_a1] == formula,
            reason="sheet cell updated",
            effect={
                "spreadsheet_id": spreadsheet_id,
                "range_a1": range_a1,
                "formula": formula,
            },
        )
    if tool_id == "sheets.spreadsheets.list_accessible":
        spreadsheets = sorted(state.sheets_accessible_spreadsheets)
        return ExecutionOutcome(
            executed=True,
            request_satisfied=True,
            reason="accessible spreadsheets listed",
            effect={"spreadsheet_ids": spreadsheets},
        )
    if tool_id == "people.contacts.list_my_contacts":
        page_size = int(arguments["page_size"])
        contact_ids = list(state.people_contacts.keys())[:page_size]
        return ExecutionOutcome(
            executed=True,
            request_satisfied=len(contact_ids) <= page_size,
            reason="people contacts listed",
            effect={"contact_ids": contact_ids},
        )
    if tool_id == "people.contacts.create_contact":
        resource_name = f"people/c_{len(state.people_contacts) + 1:03d}"
        state.people_contacts[resource_name] = {
            "name": str(arguments["given_name"]),
            "email": str(arguments["email"]),
        }
        return ExecutionOutcome(
            executed=True,
            request_satisfied=state.people_contacts[resource_name]["email"] == str(arguments["email"]),
            reason="people contact created",
            effect={
                "resource_name": resource_name,
                "given_name": str(arguments["given_name"]),
                "email": str(arguments["email"]),
            },
        )
    if tool_id == "people.contact_groups.list":
        group_names = sorted(state.people_contact_groups)
        return ExecutionOutcome(
            executed=True,
            request_satisfied=True,
            reason="people contact groups listed",
            effect={"group_names": group_names},
        )
    if tool_id == "people.other_contacts.update_email":
        other_contact_id = str(arguments["other_contact_id"])
        email = str(arguments["email"])
        record = state.people_other_contacts.setdefault(other_contact_id, {"name": other_contact_id, "email": ""})
        record["email"] = email
        return ExecutionOutcome(
            executed=True,
            request_satisfied=state.people_other_contacts[other_contact_id]["email"] == email,
            reason="people other contact updated",
            effect={"other_contact_id": other_contact_id, "email": email},
        )
    if tool_id == "confluence.pages.get_storage":
        page_id = str(arguments["page_id"])
        page = deepcopy(state.confluence_pages.get(page_id, {}))
        return ExecutionOutcome(
            executed=True,
            request_satisfied=bool(page),
            reason="confluence page loaded",
            effect={"page_id": page_id, "title": page.get("title"), "body_html": page.get("body_html")},
        )
    if tool_id == "confluence.pages.update_title":
        page_id = str(arguments["page_id"])
        title = str(arguments["title"])
        page = state.confluence_pages.setdefault(page_id, {"body_html": "", "parent_id": None, "space_key": "ENG"})
        page["title"] = title
        return ExecutionOutcome(
            executed=True,
            request_satisfied=state.confluence_pages[page_id]["title"] == title,
            reason="confluence page title updated",
            effect={"page_id": page_id, "title": title},
        )
    if tool_id == "confluence.pages.list_children":
        page_id = str(arguments["page_id"])
        child_ids = sorted(
            child_id for child_id, page in state.confluence_pages.items() if page.get("parent_id") == page_id
        )
        return ExecutionOutcome(
            executed=True,
            request_satisfied=True,
            reason="confluence child pages listed",
            effect={"page_id": page_id, "child_ids": child_ids},
        )
    if tool_id == "confluence.pages.list_by_space_key":
        space_key = str(arguments["space_key"])
        page_ids = sorted(
            page_id for page_id, page in state.confluence_pages.items() if page.get("space_key") == space_key
        )
        return ExecutionOutcome(
            executed=True,
            request_satisfied=True,
            reason="confluence pages listed by space key",
            effect={"space_key": space_key, "page_ids": page_ids},
        )
    if tool_id == "bitbucket.workspaces.get":
        workspace_slug = str(arguments["workspace_slug"])
        workspace = deepcopy(state.bitbucket_workspaces.get(workspace_slug, {}))
        return ExecutionOutcome(
            executed=True,
            request_satisfied=bool(workspace),
            reason="bitbucket workspace loaded",
            effect={
                "workspace_slug": workspace_slug,
                "display_name": workspace.get("display_name"),
            },
        )
    if tool_id == "bitbucket.repositories.list_workspace":
        workspace_slug = str(arguments["workspace_slug"])
        repo_slugs = sorted(state.bitbucket_workspaces.get(workspace_slug, {}).get("repo_slugs", []))
        return ExecutionOutcome(
            executed=True,
            request_satisfied=True,
            reason="bitbucket workspace repositories listed",
            effect={"workspace_slug": workspace_slug, "repo_slugs": repo_slugs},
        )
    if tool_id == "bitbucket.workspaces.list_members":
        workspace_slug = str(arguments["workspace_slug"])
        member_ids = sorted(state.bitbucket_workspaces.get(workspace_slug, {}).get("member_ids", []))
        return ExecutionOutcome(
            executed=True,
            request_satisfied=True,
            reason="bitbucket workspace members listed",
            effect={"workspace_slug": workspace_slug, "member_ids": member_ids},
        )
    if tool_id == "bitbucket.accounts.get_legacy_account":
        account_name = str(arguments["account_name"])
        account = deepcopy(state.bitbucket_legacy_accounts.get(account_name, {}))
        return ExecutionOutcome(
            executed=True,
            request_satisfied=bool(account),
            reason="bitbucket legacy account loaded",
            effect={
                "account_name": account_name,
                "kind": account.get("kind"),
                "display_name": account.get("display_name"),
            },
        )
    return ExecutionOutcome(
        executed=False,
        request_satisfied=False,
        reason=f"unsupported tool semantics for {tool_id}",
        effect={},
    )


def _safe_rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def _csv_cells(raw_value: Any) -> list[str]:
    return [part.strip() for part in str(raw_value).split(",")]
