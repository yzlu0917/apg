from __future__ import annotations

import itertools
import json
import re
import urllib.request
from dataclasses import dataclass
from typing import Any


BFCL_RAW_ROOT = (
    "https://raw.githubusercontent.com/ShishirPatil/gorilla/main/"
    "berkeley-function-call-leaderboard/bfcl_eval/data"
)


@dataclass(frozen=True)
class BFCLCategorySpec:
    category: str
    question_path: str
    answer_path: str | None
    limit: int
    label: str


DEFAULT_CATEGORY_SPECS: tuple[BFCLCategorySpec, ...] = (
    BFCLCategorySpec(
        category="simple_python",
        question_path="BFCL_v4_simple_python.json",
        answer_path="possible_answer/BFCL_v4_simple_python.json",
        limit=10,
        label="execute",
    ),
    BFCLCategorySpec(
        category="multiple",
        question_path="BFCL_v4_multiple.json",
        answer_path="possible_answer/BFCL_v4_multiple.json",
        limit=10,
        label="execute",
    ),
    BFCLCategorySpec(
        category="live_simple",
        question_path="BFCL_v4_live_simple.json",
        answer_path="possible_answer/BFCL_v4_live_simple.json",
        limit=10,
        label="execute",
    ),
    BFCLCategorySpec(
        category="irrelevance",
        question_path="BFCL_v4_irrelevance.json",
        answer_path=None,
        limit=10,
        label="abstain",
    ),
    BFCLCategorySpec(
        category="live_irrelevance",
        question_path="BFCL_v4_live_irrelevance.json",
        answer_path=None,
        limit=10,
        label="abstain",
    ),
)


def build_bfcl_bridge_payload(
    *,
    raw_root: str = BFCL_RAW_ROOT,
    category_specs: tuple[BFCLCategorySpec, ...] = DEFAULT_CATEGORY_SPECS,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    tool_payloads: list[dict[str, Any]] = []
    case_payloads: list[dict[str, Any]] = []
    view_payloads: list[dict[str, Any]] = []
    selected_counts: dict[str, int] = {}

    for spec in category_specs:
        questions = _load_jsonl(f"{raw_root}/{spec.question_path}")
        answers = _load_answer_lookup(f"{raw_root}/{spec.answer_path}") if spec.answer_path else {}
        selected = 0
        for item in questions:
            if selected >= spec.limit:
                break
            if not _case_is_supported(item):
                continue
            case_tools, case_payload, view_payload = _convert_case(item, spec, answers)
            tool_payloads.extend(case_tools)
            case_payloads.append(case_payload)
            view_payloads.append(view_payload)
            selected += 1
        selected_counts[spec.category] = selected

    benchmark_payload = {
        "metadata": {
            "panel_role": "external_bridge",
            "source_benchmark": "BFCL_v4",
            "source_root": raw_root,
            "selection_policy": "first_scalar_supported_cases_by_category_id",
            "category_limits": {spec.category: spec.limit for spec in category_specs},
            "selected_counts": selected_counts,
            "audit_path": "data/bfcl_bridge_audit.json",
            "audit_markdown_path": "history/bfcl_bridge_audit.md",
        },
        "tools": tool_payloads,
        "cases": case_payloads,
        "views": view_payloads,
    }
    audit_payload = {"case_overrides": {}, "view_overrides": {}}
    audit_markdown = build_bfcl_bridge_audit_markdown(benchmark_payload)
    return benchmark_payload, audit_payload, audit_markdown


def build_bfcl_bridge_audit_markdown(benchmark_payload: dict[str, Any]) -> str:
    metadata = benchmark_payload["metadata"]
    lines = [
        "# BFCL Bridge Audit",
        "",
        "This file records the source anchors and deterministic import policy for the ToolShift BFCL bridge benchmark.",
        "",
        "## Source Benchmark",
        "",
        "- Benchmark: BFCL v4",
        f"- Raw root: `{metadata['source_root']}`",
        "- Source repository: `https://github.com/ShishirPatil/gorilla/tree/main/berkeley-function-call-leaderboard`",
        "",
        "## Import Policy",
        "",
        "- Categories imported: `simple_python`, `multiple`, `live_simple`, `irrelevance`, `live_irrelevance`",
        "- Per-category sampling: first scalar-compatible cases in source order",
        "- Scalar-compatible means every visible top-level parameter is one of `string/integer/float/boolean`",
        "- Execute categories keep BFCL possible answers as set-valued admissible actions",
        "- Irrelevance categories map to `abstain`-only admissible actions",
        "",
        "## Selected Counts",
        "",
    ]
    for category, count in metadata["selected_counts"].items():
        lines.append(f"- `{category}`: {count}")
    return "\n".join(lines)


def _load_jsonl(url: str) -> list[dict[str, Any]]:
    with urllib.request.urlopen(url) as response:
        text = response.read().decode("utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def _load_answer_lookup(url: str) -> dict[str, list[dict[str, Any]]]:
    lookup: dict[str, list[dict[str, Any]]] = {}
    for row in _load_jsonl(url):
        lookup[row["id"]] = row["ground_truth"]
    return lookup


def _case_is_supported(item: dict[str, Any]) -> bool:
    for function in item["function"]:
        properties = function["parameters"].get("properties", {})
        for payload in properties.values():
            if _map_type(payload.get("type")) is None:
                return False
    return True


def _convert_case(
    item: dict[str, Any],
    spec: BFCLCategorySpec,
    answer_lookup: dict[str, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    case_id = f"bfcl_{spec.category}_{item['id']}"
    case_tools: list[dict[str, Any]] = []
    tool_ids: list[str] = []
    name_to_tool_id: dict[str, str] = {}
    for index, function in enumerate(item["function"]):
        tool_id = f"{case_id}.tool_{index}.{_slug(function['name'])}"
        tool_ids.append(tool_id)
        name_to_tool_id[function["name"]] = tool_id
        case_tools.append(_build_tool_payload(tool_id, function))

    admissible_actions = (
        [{"control": "abstain"}]
        if spec.label == "abstain"
        else _expand_ground_truth_actions(answer_lookup[item["id"]], name_to_tool_id, case_tools)
    )
    slot_values = dict(admissible_actions[0].get("arguments", {})) if admissible_actions else {}
    case_payload = {
        "case_id": case_id,
        "request": _render_question(item["question"]),
        "tool_ids": tool_ids,
        "slot_values": slot_values,
        "admissible_actions": admissible_actions,
        "family_tag": spec.category,
        "notes": f"Imported from BFCL v4 {spec.category} ({item['id']}).",
        "metadata": {
            "source_benchmark": "BFCL_v4",
            "source_category": spec.category,
            "source_id": item["id"],
        },
    }
    view_payload = {
        "case_id": case_id,
        "split_tag": "unambiguous_core",
        "admissible_actions": admissible_actions,
        "schema_view": {
            "view_id": f"{case_id}::clean",
            "transform_name": "clean",
            "shift_kind": "clean",
            "notes": f"BFCL {spec.category} bridge clean view.",
            "tools": [
                {
                    "canonical_tool_id": tool_id,
                    "rendered_name": function["name"],
                    "description": function.get("description", ""),
                    "status": "active",
                    "arguments": [
                        {
                            "rendered_name": name,
                            "canonical_name": name,
                            "description": payload.get("description", ""),
                            "arg_type": _map_type(payload.get("type")),
                            "required": name in set(function["parameters"].get("required", ())),
                            "position": position,
                        }
                        for position, (name, payload) in enumerate(function["parameters"].get("properties", {}).items())
                    ],
                }
                for tool_id, function in zip(tool_ids, item["function"])
            ],
        },
        "notes": f"Imported from BFCL v4 {spec.category} ({item['id']}).",
    }
    return case_tools, case_payload, view_payload


def _build_tool_payload(tool_id: str, function: dict[str, Any]) -> dict[str, Any]:
    required = set(function["parameters"].get("required", ()))
    arguments = []
    for position, (name, payload) in enumerate(function["parameters"].get("properties", {}).items()):
        arg_type = _map_type(payload.get("type"))
        if arg_type is None:
            raise ValueError(f"unsupported BFCL parameter type: {payload.get('type')}")
        arguments.append(
            {
                "canonical_name": name,
                "description": payload.get("description", ""),
                "arg_type": arg_type,
                "required": name in required,
                "aliases": [],
            }
        )
    return {
        "tool_id": tool_id,
        "description": function.get("description", ""),
        "semantic_tags": [],
        "arguments": arguments,
    }


def _expand_ground_truth_actions(
    ground_truth: list[dict[str, Any]],
    name_to_tool_id: dict[str, str],
    case_tools: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    tool_lookup = {tool["tool_id"]: tool for tool in case_tools}
    actions: list[dict[str, Any]] = []
    seen: set[str] = set()
    for candidate in ground_truth:
        if len(candidate) != 1:
            continue
        function_name, argument_options = next(iter(candidate.items()))
        tool_id = name_to_tool_id.get(function_name)
        if tool_id is None:
            continue
        tool_payload = tool_lookup[tool_id]
        expanded = _expand_argument_combinations(tool_payload, argument_options)
        for arguments in expanded:
            action = {
                "control": "execute",
                "tool_id": tool_id,
                "arguments": arguments,
            }
            key = json.dumps(action, sort_keys=True, ensure_ascii=False)
            if key in seen:
                continue
            seen.add(key)
            actions.append(action)
    return actions


def _expand_argument_combinations(tool_payload: dict[str, Any], argument_options: dict[str, Any]) -> list[dict[str, Any]]:
    choice_space: list[tuple[str, list[Any], bool]] = []
    for argument in tool_payload["arguments"]:
        canonical_name = argument["canonical_name"]
        required = argument.get("required", True)
        if canonical_name not in argument_options:
            if required:
                raise ValueError(f"missing ground-truth argument {canonical_name}")
            choice_space.append((canonical_name, [None], False))
            continue
        values = argument_options[canonical_name]
        if not isinstance(values, list):
            values = [values]
        normalized_values = []
        for value in values:
            if value == "" and not required:
                normalized_values.append(None)
            else:
                normalized_values.append(value)
        choice_space.append((canonical_name, normalized_values, required))

    expanded: list[dict[str, Any]] = []
    for combination in itertools.product(*(choices for _, choices, _ in choice_space)):
        arguments: dict[str, Any] = {}
        for (canonical_name, _, required), value in zip(choice_space, combination):
            if value is None and not required:
                continue
            arguments[canonical_name] = value
        expanded.append(arguments)
    return expanded


def _render_question(question_payload: list[Any]) -> str:
    if not question_payload:
        return ""
    turns = question_payload[0]
    parts = []
    for turn in turns:
        role = turn.get("role", "user").capitalize()
        content = turn.get("content", "")
        parts.append(f"{role}: {content}")
    return "\n".join(parts)


def _map_type(raw_type: Any) -> str | None:
    if raw_type == "integer":
        return "integer"
    if raw_type in {"float", "number"}:
        return "number"
    if raw_type == "boolean":
        return "boolean"
    if raw_type == "string":
        return "string"
    return None


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
