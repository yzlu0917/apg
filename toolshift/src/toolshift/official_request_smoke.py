from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

from .benchmark import BenchmarkSuite, ViewExample
from .request_replay import ReplayOutcome, replay_primary_action


@dataclass(frozen=True)
class OfficialRequestSmokeSpec:
    view_id: str
    expected_emitted: bool
    source_ids: tuple[str, ...]
    doc_needles: tuple[str, ...]
    expected_method: str | None = None
    expected_path: str | None = None
    expected_query_keys: tuple[str, ...] = ()
    expected_body_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class OfficialRequestSmokeRecord:
    view_id: str
    expected_emitted: bool
    passed: bool
    emitted: bool
    reason: str
    source_urls: tuple[str, ...]
    doc_needles: tuple[str, ...]
    doc_hits: dict[str, bool]
    request: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "view_id": self.view_id,
            "expected_emitted": self.expected_emitted,
            "passed": self.passed,
            "emitted": self.emitted,
            "reason": self.reason,
            "source_urls": list(self.source_urls),
            "doc_needles": list(self.doc_needles),
            "doc_hits": self.doc_hits,
            "request": self.request,
        }


OFFICIAL_REQUEST_SMOKE_SPECS: tuple[OfficialRequestSmokeSpec, ...] = (
    OfficialRequestSmokeSpec(
        view_id="drive_add_parent_to_file::clean",
        expected_emitted=True,
        source_ids=("drive_v2_parents_insert_ref",),
        doc_needles=("adds a parent folder for a file", "post https://www.googleapis.com/drive/v2/files/{fileId}/parents"),
        expected_method="POST",
        expected_path="/drive/v2/files/file_brief/parents",
        expected_body_keys=("id",),
    ),
    OfficialRequestSmokeSpec(
        view_id="drive_add_parent_to_file::positive_version_migration",
        expected_emitted=True,
        source_ids=("drive_v2_to_v3_ref", "drive_v3_files_update_ref"),
        doc_needles=("parents.insert", "files.update", "addParents"),
        expected_method="PATCH",
        expected_path="/drive/v3/files/file_brief",
        expected_query_keys=("addParents",),
    ),
    OfficialRequestSmokeSpec(
        view_id="drive_add_file_to_second_folder::negative_shortcut_replacement",
        expected_emitted=False,
        source_ids=("drive_v3_files_update_ref", "drive_folder_guide", "drive_shortcuts_guide"),
        doc_needles=(
            "adding files to multiple folders is no longer supported. use shortcuts instead",
            "a file can only have one parent folder",
            "link to other files or folders on google drive",
        ),
    ),
    OfficialRequestSmokeSpec(
        view_id="jira_assign_issue_user_ref::clean",
        expected_emitted=True,
        source_ids=("jira_v2_issue_assignees_ref",),
        doc_needles=("/rest/api/2/issue/{issueIdOrKey}/assignee", "if `name` or `accountId` is set to"),
        expected_method="PUT",
        expected_path="/rest/api/2/issue/ENG-7/assignee",
        expected_body_keys=("name",),
    ),
    OfficialRequestSmokeSpec(
        view_id="jira_assign_issue_user_ref::positive_version_migration",
        expected_emitted=True,
        source_ids=("jira_v3_issue_assignees_ref", "jira_privacy_migration_guide"),
        doc_needles=("/rest/api/3/issue/{issueIdOrKey}/assignee", "accountid"),
        expected_method="PUT",
        expected_path="/rest/api/3/issue/ENG-7/assignee",
        expected_body_keys=("accountId",),
    ),
    OfficialRequestSmokeSpec(
        view_id="jira_search_assignable_user_query::positive_version_migration",
        expected_emitted=True,
        source_ids=("jira_privacy_migration_guide", "jira_v3_user_search_ref"),
        doc_needles=("supports the `query` request parameter", "accountid"),
        expected_method="GET",
        expected_path="/rest/api/3/user/assignable/search",
        expected_query_keys=("project", "query"),
    ),
    OfficialRequestSmokeSpec(
        view_id="jira_search_assignable_user_legacy_username::negative_legacy_identifier_removed",
        expected_emitted=False,
        source_ids=("jira_privacy_migration_guide",),
        doc_needles=("remove personal data from the api that is used to identify users", "`username` and `userKey`", "accountid"),
    ),
    OfficialRequestSmokeSpec(
        view_id="sheets_get_sheet_titles::positive_version_migration",
        expected_emitted=True,
        source_ids=("sheets_v3_v4_migration_guide", "sheets_v4_spreadsheets_get_ref"),
        doc_needles=("fields=sheets.properties.title", "spreadsheets.get"),
        expected_method="GET",
        expected_path="/v4/spreadsheets/sh_budget",
        expected_query_keys=("fields",),
    ),
    OfficialRequestSmokeSpec(
        view_id="sheets_append_row::positive_version_migration",
        expected_emitted=True,
        source_ids=("sheets_v3_v4_migration_guide", "sheets_v4_values_append_ref"),
        doc_needles=("spreadsheets.values.append", "append rows", "valueinputoption"),
        expected_method="POST",
        expected_path="/v4/spreadsheets/sh_budget/values/ws_hours:append",
        expected_query_keys=("valueInputOption",),
        expected_body_keys=("values",),
    ),
    OfficialRequestSmokeSpec(
        view_id="sheets_update_formula::positive_version_migration",
        expected_emitted=True,
        source_ids=("sheets_v3_v4_migration_guide", "sheets_v4_values_update_ref"),
        doc_needles=("spreadsheets.values.update", "valueinputoption", "user_entered"),
        expected_method="PUT",
        expected_path="/v4/spreadsheets/sh_budget/values/ws_summary!A1",
        expected_query_keys=("valueInputOption",),
        expected_body_keys=("values",),
    ),
    OfficialRequestSmokeSpec(
        view_id="sheets_list_accessible_spreadsheets::negative_drive_scope_replacement",
        expected_emitted=False,
        source_ids=("sheets_v3_v4_migration_guide", "drive_v3_files_list_ref"),
        doc_needles=("does not provide this specific operation", "drive api files.list", "mimetype"),
    ),
    OfficialRequestSmokeSpec(
        view_id="people_list_my_contacts::positive_version_migration",
        expected_emitted=True,
        source_ids=("people_contacts_migration_guide", "people_connections_list_ref"),
        doc_needles=("people.connections.list", "personfields", "connections"),
        expected_method="GET",
        expected_path="/v1/people/me/connections",
        expected_query_keys=("pageSize", "personFields"),
    ),
    OfficialRequestSmokeSpec(
        view_id="people_create_contact::positive_version_migration",
        expected_emitted=True,
        source_ids=("people_contacts_migration_guide", "people_create_contact_ref"),
        doc_needles=("people.createcontact", "personfields", "emailaddresses"),
        expected_method="POST",
        expected_path="/v1/people:createContact",
        expected_query_keys=("personFields",),
        expected_body_keys=("names", "emailAddresses"),
    ),
    OfficialRequestSmokeSpec(
        view_id="people_list_contact_groups::positive_version_migration",
        expected_emitted=True,
        source_ids=("people_contacts_migration_guide", "people_contact_groups_list_ref"),
        doc_needles=("contactgroups.list", "groupfields"),
        expected_method="GET",
        expected_path="/v1/contactGroups",
        expected_query_keys=("groupFields",),
    ),
    OfficialRequestSmokeSpec(
        view_id="people_update_other_contact_email::negative_other_contacts_read_only",
        expected_emitted=False,
        source_ids=("people_contacts_migration_guide", "people_other_contacts_copy_ref"),
        doc_needles=(
            "add the other contact as a my contact",
            "only basic contact information for",
            "copyothercontacttomycontactsgroup",
        ),
    ),
    OfficialRequestSmokeSpec(
        view_id="confluence_get_page_storage::positive_version_migration",
        expected_emitted=True,
        source_ids=("confluence_v1_v2_notice", "confluence_v2_page_ref"),
        doc_needles=("/wiki/api/v2/pages/{id}", "body-format", "get page by id"),
        expected_method="GET",
        expected_path="/wiki/api/v2/pages/2001",
        expected_query_keys=("body-format",),
    ),
    OfficialRequestSmokeSpec(
        view_id="confluence_update_page_title::positive_version_migration",
        expected_emitted=True,
        source_ids=("confluence_v1_v2_notice", "confluence_v2_page_ref"),
        doc_needles=("/wiki/api/v2/pages/{id}/title", "update page title", "title"),
        expected_method="PUT",
        expected_path="/wiki/api/v2/pages/2001/title",
        expected_body_keys=("status", "title"),
    ),
    OfficialRequestSmokeSpec(
        view_id="confluence_list_page_children::positive_version_migration",
        expected_emitted=True,
        source_ids=("confluence_v1_v2_notice", "confluence_v2_children_ref"),
        doc_needles=("/wiki/api/v2/pages/{id}/children", "cursor"),
        expected_method="GET",
        expected_path="/wiki/api/v2/pages/2001/children",
    ),
    OfficialRequestSmokeSpec(
        view_id="confluence_list_pages_by_space_key::negative_space_key_lookup_split",
        expected_emitted=False,
        source_ids=("confluence_v1_v2_notice", "confluence_v2_space_ref", "confluence_v2_page_ref"),
        doc_needles=("/rest/api/space/&lt;spacekey&gt;", "/api/v2/spaces?keys=&lt;spacekey&gt;", "spaceid"),
    ),
    OfficialRequestSmokeSpec(
        view_id="bitbucket_get_workspace::positive_version_migration",
        expected_emitted=True,
        source_ids=("bitbucket_teams_workspaces_notice", "bitbucket_workspaces_ref"),
        doc_needles=("/2.0/teams/{username}", "/2.0/workspaces/{workspace}", "get a workspace"),
        expected_method="GET",
        expected_path="/2.0/workspaces/eng-team",
    ),
    OfficialRequestSmokeSpec(
        view_id="bitbucket_list_workspace_repositories::positive_version_migration",
        expected_emitted=True,
        source_ids=("bitbucket_teams_workspaces_notice", "bitbucket_repositories_ref"),
        doc_needles=("/2.0/workspaces/{workspace}", "/2.0/repositories/{workspace}", "list repositories in a workspace"),
        expected_method="GET",
        expected_path="/2.0/repositories/eng-team",
    ),
    OfficialRequestSmokeSpec(
        view_id="bitbucket_list_workspace_members::positive_version_migration",
        expected_emitted=True,
        source_ids=("bitbucket_teams_workspaces_notice", "bitbucket_workspaces_ref"),
        doc_needles=("/2.0/workspaces/{workspace}/members", "members", "workspace"),
        expected_method="GET",
        expected_path="/2.0/workspaces/eng-team/members",
    ),
    OfficialRequestSmokeSpec(
        view_id="bitbucket_get_legacy_account::negative_account_object_removed",
        expected_emitted=False,
        source_ids=("bitbucket_v1_deprecation_notice", "bitbucket_teams_workspaces_notice", "bitbucket_workspaces_ref"),
        doc_needles=("/1.0/users/{accountname}", "not available in 2.0", "/2.0/workspaces/{workspace}"),
    ),
)


def run_official_request_smoke(
    *,
    suite: BenchmarkSuite,
    benchmark_payload: dict[str, Any],
    fetch_text: Callable[[str], str] | None = None,
) -> tuple[list[OfficialRequestSmokeRecord], dict[str, Any]]:
    fetcher = fetch_text or _fetch_text
    sources = benchmark_payload["sources"]
    example_lookup = {example.schema_view.view_id: example for example in suite.examples}
    url_cache: dict[str, str] = {}
    records: list[OfficialRequestSmokeRecord] = []
    for spec in OFFICIAL_REQUEST_SMOKE_SPECS:
        example = example_lookup[spec.view_id]
        outcome = replay_primary_action(example)
        source_urls = tuple(sources[source_id]["url"] for source_id in spec.source_ids)
        combined_text = []
        for url in source_urls:
            text = url_cache.get(url)
            if text is None:
                text = fetcher(url)
                url_cache[url] = text
            combined_text.append(text.lower())
        doc_text = "\n".join(combined_text)
        doc_hits = {needle: needle.lower() in doc_text for needle in spec.doc_needles}
        passed = _record_passes(spec, outcome, doc_hits)
        records.append(
            OfficialRequestSmokeRecord(
                view_id=spec.view_id,
                expected_emitted=spec.expected_emitted,
                passed=passed,
                emitted=outcome.emitted,
                reason=_record_reason(spec, outcome, doc_hits),
                source_urls=source_urls,
                doc_needles=spec.doc_needles,
                doc_hits=doc_hits,
                request=outcome.request.to_dict() if outcome.request is not None else None,
            )
        )
    return records, summarize_official_request_smoke(records)


def summarize_official_request_smoke(records: list[OfficialRequestSmokeRecord]) -> dict[str, Any]:
    total = len(records)
    expected_emit = [record for record in records if record.expected_emitted]
    expected_block = [record for record in records if not record.expected_emitted]
    by_provider: dict[str, dict[str, Any]] = {}
    for record in records:
        provider = record.request["provider"] if record.request is not None else _provider_from_view_id(record.view_id)
        bucket = by_provider.setdefault(provider, {"count": 0, "pass": 0, "emit": 0})
        bucket["count"] += 1
        bucket["pass"] += int(record.passed)
        bucket["emit"] += int(record.emitted)
    provider_summary = {
        provider: {
            "count": payload["count"],
            "pass_rate": _safe_rate(payload["pass"], payload["count"]),
            "emit_rate": _safe_rate(payload["emit"], payload["count"]),
        }
        for provider, payload in sorted(by_provider.items())
    }
    return {
        "count": total,
        "pass_rate": _safe_rate(sum(int(record.passed) for record in records), total),
        "emit_expected_pass_rate": _safe_rate(sum(int(record.passed) for record in expected_emit), len(expected_emit)),
        "block_expected_pass_rate": _safe_rate(sum(int(record.passed) for record in expected_block), len(expected_block)),
        "emit_rate": _safe_rate(sum(int(record.emitted) for record in records), total),
        "provider_summary": provider_summary,
    }


def _record_passes(
    spec: OfficialRequestSmokeSpec,
    outcome: ReplayOutcome,
    doc_hits: dict[str, bool],
) -> bool:
    if not all(doc_hits.values()):
        return False
    if outcome.emitted != spec.expected_emitted:
        return False
    if not outcome.emitted or outcome.request is None:
        return True
    if spec.expected_method is not None and outcome.request.method != spec.expected_method:
        return False
    if spec.expected_path is not None and outcome.request.path != spec.expected_path:
        return False
    if any(key not in outcome.request.query for key in spec.expected_query_keys):
        return False
    if any(key not in outcome.request.body for key in spec.expected_body_keys):
        return False
    return True


def _record_reason(
    spec: OfficialRequestSmokeSpec,
    outcome: ReplayOutcome,
    doc_hits: dict[str, bool],
) -> str:
    missing = [needle for needle, hit in doc_hits.items() if not hit]
    if missing:
        return f"missing official doc evidence: {missing}"
    if outcome.emitted != spec.expected_emitted:
        return f"unexpected replay emission state: emitted={outcome.emitted}"
    if not outcome.emitted:
        return outcome.reason
    if outcome.request is None:
        return "missing request payload"
    if spec.expected_method is not None and outcome.request.method != spec.expected_method:
        return f"unexpected method: {outcome.request.method}"
    if spec.expected_path is not None and outcome.request.path != spec.expected_path:
        return f"unexpected path: {outcome.request.path}"
    for key in spec.expected_query_keys:
        if key not in outcome.request.query:
            return f"missing query key: {key}"
    for key in spec.expected_body_keys:
        if key not in outcome.request.body:
            return f"missing body key: {key}"
    return "ok"


def _fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "ToolShift/0.1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", "ignore")


def _provider_from_view_id(view_id: str) -> str:
    return view_id.split("_", 1)[0]


def load_benchmark_payload(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _safe_rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator
