from __future__ import annotations

import json
import re
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import urlparse

from .benchmark import BenchmarkSuite
from .request_replay import ReplayOutcome, replay_primary_action


@dataclass(frozen=True)
class ApiSurfaceSmokeSpec:
    view_id: str
    expected_emitted: bool
    validation_kind: str
    spec_url: str | None = None
    doc_source_ids: tuple[str, ...] = ()
    doc_needles: tuple[str, ...] = ()


@dataclass(frozen=True)
class ApiSurfaceSmokeRecord:
    view_id: str
    validation_kind: str
    expected_emitted: bool
    passed: bool
    emitted: bool
    reason: str
    spec_url: str | None
    doc_source_urls: tuple[str, ...]
    spec_hits: dict[str, bool]
    doc_hits: dict[str, bool]
    request: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "view_id": self.view_id,
            "validation_kind": self.validation_kind,
            "expected_emitted": self.expected_emitted,
            "passed": self.passed,
            "emitted": self.emitted,
            "reason": self.reason,
            "spec_url": self.spec_url,
            "doc_source_urls": list(self.doc_source_urls),
            "spec_hits": self.spec_hits,
            "doc_hits": self.doc_hits,
            "request": self.request,
        }


API_SURFACE_SMOKE_SPECS: tuple[ApiSurfaceSmokeSpec, ...] = (
    ApiSurfaceSmokeSpec(
        view_id="drive_add_parent_to_file::clean",
        expected_emitted=True,
        validation_kind="drive_discovery",
        spec_url="https://www.googleapis.com/discovery/v1/apis/drive/v2/rest",
    ),
    ApiSurfaceSmokeSpec(
        view_id="drive_add_parent_to_file::positive_version_migration",
        expected_emitted=True,
        validation_kind="drive_discovery",
        spec_url="https://www.googleapis.com/discovery/v1/apis/drive/v3/rest",
    ),
    ApiSurfaceSmokeSpec(
        view_id="jira_assign_issue_user_ref::clean",
        expected_emitted=True,
        validation_kind="jira_openapi",
        spec_url="https://developer.atlassian.com/cloud/jira/platform/swagger.v3.json",
    ),
    ApiSurfaceSmokeSpec(
        view_id="jira_assign_issue_user_ref::positive_version_migration",
        expected_emitted=True,
        validation_kind="jira_openapi",
        spec_url="https://developer.atlassian.com/cloud/jira/platform/swagger-v3.v3.json",
    ),
    ApiSurfaceSmokeSpec(
        view_id="jira_search_assignable_user_query::positive_version_migration",
        expected_emitted=True,
        validation_kind="jira_openapi",
        spec_url="https://developer.atlassian.com/cloud/jira/platform/swagger-v3.v3.json",
    ),
    ApiSurfaceSmokeSpec(
        view_id="sheets_get_sheet_titles::positive_version_migration",
        expected_emitted=True,
        validation_kind="sheets_discovery",
        spec_url="https://www.googleapis.com/discovery/v1/apis/sheets/v4/rest",
    ),
    ApiSurfaceSmokeSpec(
        view_id="sheets_append_row::positive_version_migration",
        expected_emitted=True,
        validation_kind="sheets_discovery",
        spec_url="https://www.googleapis.com/discovery/v1/apis/sheets/v4/rest",
    ),
    ApiSurfaceSmokeSpec(
        view_id="sheets_update_formula::positive_version_migration",
        expected_emitted=True,
        validation_kind="sheets_discovery",
        spec_url="https://www.googleapis.com/discovery/v1/apis/sheets/v4/rest",
    ),
    ApiSurfaceSmokeSpec(
        view_id="drive_add_file_to_second_folder::negative_shortcut_replacement",
        expected_emitted=False,
        validation_kind="negative_docs",
        doc_source_ids=("drive_v3_files_update_ref", "drive_folder_guide", "drive_shortcuts_guide"),
        doc_needles=(
            "adding files to multiple folders is no longer supported. use shortcuts instead",
            "a file can only have one parent folder",
            "link to other files or folders on google drive",
        ),
    ),
    ApiSurfaceSmokeSpec(
        view_id="jira_search_assignable_user_legacy_username::negative_legacy_identifier_removed",
        expected_emitted=False,
        validation_kind="negative_docs",
        doc_source_ids=("jira_privacy_migration_guide",),
        doc_needles=(
            "remove personal data from the api that is used to identify users",
            "`username` and `userKey`",
            "accountid",
        ),
    ),
    ApiSurfaceSmokeSpec(
        view_id="sheets_list_accessible_spreadsheets::negative_drive_scope_replacement",
        expected_emitted=False,
        validation_kind="negative_docs",
        doc_source_ids=("sheets_v3_v4_migration_guide", "drive_v3_files_list_ref"),
        doc_needles=("does not provide this specific operation", "drive api files.list", "mimetype"),
    ),
    ApiSurfaceSmokeSpec(
        view_id="people_list_my_contacts::positive_version_migration",
        expected_emitted=True,
        validation_kind="people_discovery",
        spec_url="https://www.googleapis.com/discovery/v1/apis/people/v1/rest",
    ),
    ApiSurfaceSmokeSpec(
        view_id="people_create_contact::positive_version_migration",
        expected_emitted=True,
        validation_kind="people_discovery",
        spec_url="https://www.googleapis.com/discovery/v1/apis/people/v1/rest",
    ),
    ApiSurfaceSmokeSpec(
        view_id="people_list_contact_groups::positive_version_migration",
        expected_emitted=True,
        validation_kind="people_discovery",
        spec_url="https://www.googleapis.com/discovery/v1/apis/people/v1/rest",
    ),
    ApiSurfaceSmokeSpec(
        view_id="people_update_other_contact_email::negative_other_contacts_read_only",
        expected_emitted=False,
        validation_kind="negative_docs",
        doc_source_ids=("people_contacts_migration_guide", "people_other_contacts_copy_ref"),
        doc_needles=(
            "add the other contact as a my contact",
            "only basic contact information for",
            "copyothercontacttomycontactsgroup",
        ),
    ),
    ApiSurfaceSmokeSpec(
        view_id="confluence_get_page_storage::positive_version_migration",
        expected_emitted=True,
        validation_kind="confluence_openapi",
        spec_url="https://dac-static.atlassian.com/cloud/confluence/openapi-v2.v3.json",
    ),
    ApiSurfaceSmokeSpec(
        view_id="confluence_update_page_title::positive_version_migration",
        expected_emitted=True,
        validation_kind="confluence_openapi",
        spec_url="https://dac-static.atlassian.com/cloud/confluence/openapi-v2.v3.json",
    ),
    ApiSurfaceSmokeSpec(
        view_id="confluence_list_page_children::positive_version_migration",
        expected_emitted=True,
        validation_kind="confluence_openapi",
        spec_url="https://dac-static.atlassian.com/cloud/confluence/openapi-v2.v3.json",
    ),
    ApiSurfaceSmokeSpec(
        view_id="confluence_list_pages_by_space_key::negative_space_key_lookup_split",
        expected_emitted=False,
        validation_kind="negative_docs",
        doc_source_ids=("confluence_v1_v2_notice", "confluence_v2_space_ref", "confluence_v2_page_ref"),
        doc_needles=(
            "/rest/api/space/&lt;spacekey&gt;",
            "/api/v2/spaces?keys=&lt;spacekey&gt;",
            "spaceid",
        ),
    ),
    ApiSurfaceSmokeSpec(
        view_id="bitbucket_get_workspace::positive_version_migration",
        expected_emitted=True,
        validation_kind="bitbucket_swagger",
        spec_url="https://api.bitbucket.org/swagger.json",
    ),
    ApiSurfaceSmokeSpec(
        view_id="bitbucket_list_workspace_repositories::positive_version_migration",
        expected_emitted=True,
        validation_kind="bitbucket_swagger",
        spec_url="https://api.bitbucket.org/swagger.json",
    ),
    ApiSurfaceSmokeSpec(
        view_id="bitbucket_list_workspace_members::positive_version_migration",
        expected_emitted=True,
        validation_kind="bitbucket_swagger",
        spec_url="https://api.bitbucket.org/swagger.json",
    ),
    ApiSurfaceSmokeSpec(
        view_id="bitbucket_get_legacy_account::negative_account_object_removed",
        expected_emitted=False,
        validation_kind="negative_docs",
        doc_source_ids=("bitbucket_v1_deprecation_notice", "bitbucket_teams_workspaces_notice", "bitbucket_workspaces_ref"),
        doc_needles=(
            "/1.0/users/{accountname}",
            "not available in 2.0",
            "/2.0/workspaces/{workspace}",
        ),
    ),
)


def run_api_surface_smoke(
    *,
    suite: BenchmarkSuite,
    benchmark_payload: dict[str, Any],
    fetch_json: Callable[[str], dict[str, Any]] | None = None,
    fetch_text: Callable[[str], str] | None = None,
) -> tuple[list[ApiSurfaceSmokeRecord], dict[str, Any]]:
    json_fetcher = fetch_json or _fetch_json
    text_fetcher = fetch_text or _fetch_text
    sources = benchmark_payload["sources"]
    example_lookup = {example.schema_view.view_id: example for example in suite.examples}
    json_cache: dict[str, dict[str, Any]] = {}
    text_cache: dict[str, str] = {}
    records: list[ApiSurfaceSmokeRecord] = []
    for spec in API_SURFACE_SMOKE_SPECS:
        example = example_lookup[spec.view_id]
        outcome = replay_primary_action(example)
        spec_hits: dict[str, bool] = {}
        if spec.spec_url is not None:
            spec_doc = json_cache.get(spec.spec_url)
            if spec_doc is None:
                spec_doc = json_fetcher(spec.spec_url)
                json_cache[spec.spec_url] = spec_doc
            if spec.validation_kind in {"drive_discovery", "sheets_discovery", "people_discovery"}:
                spec_hits = _validate_google_discovery(outcome, spec_doc)
            elif spec.validation_kind in {"jira_openapi", "confluence_openapi", "bitbucket_swagger"}:
                spec_hits = _validate_openapi(outcome, spec_doc)
            else:
                raise ValueError(f"unsupported validation kind {spec.validation_kind}")

        doc_source_urls = tuple(sources[source_id]["url"] for source_id in spec.doc_source_ids)
        doc_hits: dict[str, bool] = {}
        if doc_source_urls:
            combined_text: list[str] = []
            for url in doc_source_urls:
                text = text_cache.get(url)
                if text is None:
                    text = text_fetcher(url)
                    text_cache[url] = text
                combined_text.append(text.lower())
            doc_text = "\n".join(combined_text)
            doc_hits = {needle: needle.lower() in doc_text for needle in spec.doc_needles}

        records.append(
            ApiSurfaceSmokeRecord(
                view_id=spec.view_id,
                validation_kind=spec.validation_kind,
                expected_emitted=spec.expected_emitted,
                passed=_record_passes(spec, outcome, spec_hits, doc_hits),
                emitted=outcome.emitted,
                reason=_record_reason(spec, outcome, spec_hits, doc_hits),
                spec_url=spec.spec_url,
                doc_source_urls=doc_source_urls,
                spec_hits=spec_hits,
                doc_hits=doc_hits,
                request=outcome.request.to_dict() if outcome.request is not None else None,
            )
        )
    return records, summarize_api_surface_smoke(records)


def summarize_api_surface_smoke(records: list[ApiSurfaceSmokeRecord]) -> dict[str, Any]:
    total = len(records)
    emit_expected = [record for record in records if record.expected_emitted]
    block_expected = [record for record in records if not record.expected_emitted]
    by_kind: dict[str, dict[str, int]] = {}
    by_provider: dict[str, dict[str, int]] = {}
    for record in records:
        kind_bucket = by_kind.setdefault(record.validation_kind, {"count": 0, "pass": 0, "emit": 0})
        kind_bucket["count"] += 1
        kind_bucket["pass"] += int(record.passed)
        kind_bucket["emit"] += int(record.emitted)

        provider = record.request["provider"] if record.request is not None else record.view_id.split("_", 1)[0]
        provider_bucket = by_provider.setdefault(provider, {"count": 0, "pass": 0, "emit": 0})
        provider_bucket["count"] += 1
        provider_bucket["pass"] += int(record.passed)
        provider_bucket["emit"] += int(record.emitted)

    return {
        "count": total,
        "pass_rate": _safe_rate(sum(int(record.passed) for record in records), total),
        "emit_expected_pass_rate": _safe_rate(sum(int(record.passed) for record in emit_expected), len(emit_expected)),
        "block_expected_pass_rate": _safe_rate(sum(int(record.passed) for record in block_expected), len(block_expected)),
        "emit_rate": _safe_rate(sum(int(record.emitted) for record in records), total),
        "by_kind": {
            key: {
                "count": payload["count"],
                "pass_rate": _safe_rate(payload["pass"], payload["count"]),
                "emit_rate": _safe_rate(payload["emit"], payload["count"]),
            }
            for key, payload in sorted(by_kind.items())
        },
        "by_provider": {
            key: {
                "count": payload["count"],
                "pass_rate": _safe_rate(payload["pass"], payload["count"]),
                "emit_rate": _safe_rate(payload["emit"], payload["count"]),
            }
            for key, payload in sorted(by_provider.items())
        },
    }


def _validate_google_discovery(outcome: ReplayOutcome, spec_doc: dict[str, Any]) -> dict[str, bool]:
    request = outcome.request
    if request is None:
        return {"spec_found": False, "method": False, "path_template": False, "query_keys": False, "body_keys": False}
    method = _lookup_discovery_method(spec_doc, request.operation)
    if method is None:
        return {"spec_found": False, "method": False, "path_template": False, "query_keys": False, "body_keys": False}
    parameters = dict(spec_doc.get("parameters", {}))
    parameters.update(method.get("parameters", {}))
    body_properties = _discovery_body_properties(spec_doc, method)
    path_template = _discovery_path_template(method["path"], request.path)
    return {
        "spec_found": True,
        "method": method.get("httpMethod") == request.method,
        "path_template": _path_template_matches(path_template, request.path),
        "query_keys": all(key in parameters for key in request.query),
        "body_keys": all(key in body_properties for key in request.body) if request.body else True,
    }


def _validate_openapi(outcome: ReplayOutcome, spec_doc: dict[str, Any]) -> dict[str, bool]:
    request = outcome.request
    if request is None:
        return {"spec_found": False, "method": False, "path_template": False, "query_keys": False, "body_keys": False}
    method_name = request.method.lower()
    matched_template = None
    matched_operation = None
    matched_path_item = None
    for candidate_template, path_item, operation in _iter_openapi_operations(spec_doc, method_name):
        if _path_template_matches(candidate_template, request.path):
            matched_template = candidate_template
            matched_path_item = path_item
            matched_operation = operation
            break
    if matched_template is None or matched_operation is None or matched_path_item is None:
        return {"spec_found": False, "method": False, "path_template": False, "query_keys": False, "body_keys": False}
    parameter_names = _openapi_parameter_names(matched_path_item, matched_operation)
    body_properties = _openapi_body_properties(spec_doc, matched_operation)
    return {
        "spec_found": True,
        "method": True,
        "path_template": _path_template_matches(matched_template, request.path),
        "query_keys": all(key in parameter_names for key in request.query),
        "body_keys": all(key in body_properties for key in request.body) if request.body else True,
    }


def _iter_openapi_operations(
    spec_doc: dict[str, Any],
    method_name: str,
) -> list[tuple[str, dict[str, Any], dict[str, Any]]]:
    operations: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    for path_template, path_item in spec_doc.get("paths", {}).items():
        operation = path_item.get(method_name)
        if operation is None:
            continue
        for candidate_template in _openapi_candidate_templates(spec_doc, path_template):
            operations.append((candidate_template, path_item, operation))
    return operations


def _openapi_candidate_templates(spec_doc: dict[str, Any], path_template: str) -> list[str]:
    normalized_path = path_template if path_template.startswith("/") else f"/{path_template}"
    candidates: list[str] = []
    seen: set[str] = set()
    for prefix in _openapi_server_path_prefixes(spec_doc):
        candidate = _join_url_paths(prefix, normalized_path)
        if candidate in seen:
            continue
        seen.add(candidate)
        candidates.append(candidate)
    return candidates


def _openapi_server_path_prefixes(spec_doc: dict[str, Any]) -> list[str]:
    prefixes = [""]
    seen = {""}
    base_path = spec_doc.get("basePath")
    if isinstance(base_path, str) and base_path and base_path != "/":
        normalized_base_path = base_path.rstrip("/")
        if normalized_base_path not in seen:
            seen.add(normalized_base_path)
            prefixes.append(normalized_base_path)
    for server in spec_doc.get("servers", []):
        url = server.get("url")
        if not isinstance(url, str) or not url:
            continue
        parsed = urlparse(url)
        path = parsed.path or ""
        if not path or path == "/":
            continue
        normalized = path.rstrip("/")
        if normalized not in seen:
            seen.add(normalized)
            prefixes.append(normalized)
    return prefixes


def _join_url_paths(prefix: str, path: str) -> str:
    if not prefix:
        return path
    return f"{prefix.rstrip('/')}/{path.lstrip('/')}"


def _openapi_parameter_names(path_item: dict[str, Any], operation: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for parameter in path_item.get("parameters", []):
        name = parameter.get("name")
        if isinstance(name, str):
            names.add(name)
    for parameter in operation.get("parameters", []):
        name = parameter.get("name")
        if isinstance(name, str):
            names.add(name)
    return names


def _lookup_discovery_method(spec_doc: dict[str, Any], operation: str) -> dict[str, Any] | None:
    parts = operation.split(".")
    if len(parts) < 2:
        return None
    resources = spec_doc.get("resources", {})
    for resource_name in parts[:-1]:
        resource = resources.get(resource_name)
        if resource is None:
            return None
        resources = resource.get("resources", {})
        methods = resource.get("methods", {})
    return methods.get(parts[-1])


def _discovery_body_properties(spec_doc: dict[str, Any], method: dict[str, Any]) -> set[str]:
    request_schema = method.get("request", {})
    ref = request_schema.get("$ref")
    if ref is None:
        return set()
    return set(spec_doc.get("schemas", {}).get(ref, {}).get("properties", {}).keys())


def _discovery_path_template(method_path: str, actual_path: str) -> str:
    if method_path.startswith("v"):
        return f"/{method_path}"
    parts = [part for part in actual_path.strip("/").split("/") if part]
    if len(parts) < 2:
        raise ValueError(f"cannot infer provider/version from {actual_path}")
    return f"/{parts[0]}/{parts[1]}/{method_path}"


def _openapi_body_properties(spec_doc: dict[str, Any], operation: dict[str, Any]) -> set[str]:
    request_body = _resolve_openapi_request_body(spec_doc, operation.get("requestBody", {}))
    content = request_body.get("content", {})
    properties: set[str] = set()
    for payload in content.values():
        schema = payload.get("schema", {})
        properties.update(_resolve_openapi_properties(spec_doc, schema).keys())
    return properties


def _resolve_openapi_properties(spec_doc: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    if not schema:
        return {}
    if "$ref" in schema:
        resolved = _resolve_openapi_ref(spec_doc, schema["$ref"])
        return _resolve_openapi_properties(spec_doc, resolved)
    properties = dict(schema.get("properties", {}))
    for combiner in ("allOf", "oneOf", "anyOf"):
        for entry in schema.get(combiner, []):
            properties.update(_resolve_openapi_properties(spec_doc, entry))
    return properties


def _resolve_openapi_ref(spec_doc: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        return {}
    cursor: Any = spec_doc
    for part in ref[2:].split("/"):
        cursor = cursor[part]
    assert isinstance(cursor, dict)
    return cursor


def _resolve_openapi_request_body(spec_doc: dict[str, Any], request_body: dict[str, Any]) -> dict[str, Any]:
    if "$ref" in request_body:
        return _resolve_openapi_ref(spec_doc, request_body["$ref"])
    return request_body


def _path_template_matches(path_template: str, actual_path: str) -> bool:
    pattern_parts: list[str] = ["^"]
    cursor = 0
    while cursor < len(path_template):
        if path_template[cursor] != "{":
            pattern_parts.append(re.escape(path_template[cursor]))
            cursor += 1
            continue
        end = path_template.find("}", cursor)
        if end == -1:
            pattern_parts.append(re.escape(path_template[cursor:]))
            break
        token = path_template[cursor + 1 : end]
        pattern_parts.append(".+" if token.startswith("+") else "[^/]+")
        cursor = end + 1
    pattern_parts.append("$")
    return re.fullmatch("".join(pattern_parts), actual_path) is not None


def _record_passes(
    spec: ApiSurfaceSmokeSpec,
    outcome: ReplayOutcome,
    spec_hits: dict[str, bool],
    doc_hits: dict[str, bool],
) -> bool:
    if outcome.emitted != spec.expected_emitted:
        return False
    if spec_hits and not all(spec_hits.values()):
        return False
    if doc_hits and not all(doc_hits.values()):
        return False
    return True


def _record_reason(
    spec: ApiSurfaceSmokeSpec,
    outcome: ReplayOutcome,
    spec_hits: dict[str, bool],
    doc_hits: dict[str, bool],
) -> str:
    if outcome.emitted != spec.expected_emitted:
        return f"unexpected replay emission state: emitted={outcome.emitted}"
    missing_spec = [key for key, hit in spec_hits.items() if not hit]
    if missing_spec:
        return f"machine-readable spec mismatch: {missing_spec}"
    missing_doc = [key for key, hit in doc_hits.items() if not hit]
    if missing_doc:
        return f"missing official doc evidence: {missing_doc}"
    if not outcome.emitted:
        return outcome.reason
    return "ok"


def _fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "ToolShift/0.1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def _fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "ToolShift/0.1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", "ignore")


def _safe_rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator
