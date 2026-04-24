from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen


API_BANK_ROOT = "https://raw.githubusercontent.com/AlibabaResearch/DAMO-ConvAI/main/api-bank"
SAMPLE_ROOT = f"{API_BANK_ROOT}/lv1-lv2-samples/level-1-given-desc"
API_ROOT = f"{API_BANK_ROOT}/apis"


@dataclass(frozen=True)
class ApiBankSelection:
    case_id: str
    sample_file: str
    target_api: str
    family_tag: str
    tool_bundle: tuple[str, ...]
    rationale: str


IMPORT_PLAN: tuple[ApiBankSelection, ...] = (
    ApiBankSelection(
        case_id="api_bank_add_agenda_level_1_1",
        sample_file="AddAgenda-level-1-1.jsonl",
        target_api="AddAgenda",
        family_tag="api_bank_organizer",
        tool_bundle=("AddAgenda", "AddAlarm", "AddMeeting", "AddReminder", "GetUserToken"),
        rationale="Organizer case with explicit content, time, location, and auth context.",
    ),
    ApiBankSelection(
        case_id="api_bank_add_alarm_level_1_1",
        sample_file="AddAlarm-level-1-1.jsonl",
        target_api="AddAlarm",
        family_tag="api_bank_organizer",
        tool_bundle=("AddAgenda", "AddAlarm", "AddMeeting", "AddReminder", "GetUserToken"),
        rationale="Organizer case with explicit alarm time and auth context.",
    ),
    ApiBankSelection(
        case_id="api_bank_add_meeting_level_1_1",
        sample_file="AddMeeting-level-1-1.jsonl",
        target_api="AddMeeting",
        family_tag="api_bank_organizer",
        tool_bundle=("AddAgenda", "AddAlarm", "AddMeeting", "AddReminder", "GetUserToken"),
        rationale="Organizer case with explicit meeting topic, time range, location, attendees, and auth context.",
    ),
    ApiBankSelection(
        case_id="api_bank_add_reminder_level_1_1",
        sample_file="AddReminder-level-1-1.jsonl",
        target_api="AddReminder",
        family_tag="api_bank_organizer",
        tool_bundle=("AddAgenda", "AddAlarm", "AddMeeting", "AddReminder", "GetUserToken"),
        rationale="Organizer case with explicit reminder content, time, and auth context.",
    ),
    ApiBankSelection(
        case_id="api_bank_book_hotel_level_1_1",
        sample_file="BookHotel-level-1-1.jsonl",
        target_api="BookHotel",
        family_tag="api_bank_service",
        tool_bundle=("BookHotel", "AppointmentRegistration", "CancelRegistration", "ModifyRegistration", "QueryRegistration"),
        rationale="Service case with directly grounded booking arguments and no hidden room-count inference.",
    ),
    ApiBankSelection(
        case_id="api_bank_appointment_registration_level_1_1",
        sample_file="AppointmentRegistration-level-1-1.jsonl",
        target_api="AppointmentRegistration",
        family_tag="api_bank_service",
        tool_bundle=("BookHotel", "AppointmentRegistration", "CancelRegistration", "ModifyRegistration", "QueryRegistration"),
        rationale="Service case with explicit patient, doctor, and date fields.",
    ),
    ApiBankSelection(
        case_id="api_bank_query_balance_level_1_1",
        sample_file="QueryBalance-level-1-1.jsonl",
        target_api="QueryBalance",
        family_tag="api_bank_service",
        tool_bundle=("QueryBalance", "OpenBankAccount", "QueryStock", "GetUserToken"),
        rationale="Finance case with auth context and single target API call.",
    ),
    ApiBankSelection(
        case_id="api_bank_calculator_level_1_1",
        sample_file="Calculator-level-1-1.jsonl",
        target_api="Calculator",
        family_tag="api_bank_utility",
        tool_bundle=("Calculator", "Dictionary", "ImageCaption", "PlayMusic", "Translate", "Wiki"),
        rationale="Utility case with exact formula argument.",
    ),
    ApiBankSelection(
        case_id="api_bank_dictionary_level_1_1",
        sample_file="Dictionary-level-1-1.jsonl",
        target_api="Dictionary",
        family_tag="api_bank_utility",
        tool_bundle=("Calculator", "Dictionary", "ImageCaption", "PlayMusic", "Translate", "Wiki"),
        rationale="Utility case with exact lexical lookup argument.",
    ),
    ApiBankSelection(
        case_id="api_bank_image_caption_level_1_1",
        sample_file="ImageCaption-level-1-1.jsonl",
        target_api="ImageCaption",
        family_tag="api_bank_utility",
        tool_bundle=("Calculator", "Dictionary", "ImageCaption", "PlayMusic", "Translate", "Wiki"),
        rationale="Utility case with explicit image URL argument.",
    ),
    ApiBankSelection(
        case_id="api_bank_play_music_level_1_1",
        sample_file="PlayMusic-level-1-1.jsonl",
        target_api="PlayMusic",
        family_tag="api_bank_utility",
        tool_bundle=("Calculator", "Dictionary", "ImageCaption", "PlayMusic", "Translate", "Wiki"),
        rationale="Utility case with explicit music title argument.",
    ),
    ApiBankSelection(
        case_id="api_bank_translate_level_1_1",
        sample_file="Translate-level-1-1.jsonl",
        target_api="Translate",
        family_tag="api_bank_utility",
        tool_bundle=("Calculator", "Dictionary", "ImageCaption", "PlayMusic", "Translate", "Wiki"),
        rationale="Utility case with explicit source text and target language.",
    ),
)


def build_api_bank_benchmark() -> tuple[dict[str, object], str]:
    tool_specs: dict[str, dict[str, object]] = {}
    cases: list[dict[str, object]] = []
    sources: dict[str, dict[str, str]] = {
        "api_bank_paper": {
            "vendor": "api_bank",
            "kind": "paper",
            "url": "https://arxiv.org/abs/2304.08244",
            "summary": "API-Bank benchmark paper introducing runnable tool-use dialogues over a public API set.",
        },
        "api_bank_repo": {
            "vendor": "api_bank",
            "kind": "repository",
            "url": "https://github.com/AlibabaResearch/DAMO-ConvAI/tree/main/api-bank",
            "summary": "Official API-Bank code and data release inside DAMO-ConvAI.",
        },
    }
    audit_lines = [
        "# API-Bank Bridge Audit",
        "",
        "This file records the imported API-Bank subset that is bridged into a TOOLSHIFT-compatible benchmark.",
        "",
        "| case_id | source sample | target api | family_tag | rationale |",
        "| --- | --- | --- | --- | --- |",
    ]

    for selection in IMPORT_PLAN:
        transcript = _load_jsonl(f"{SAMPLE_ROOT}/{selection.sample_file}")
        api_turn = _target_api_turn(transcript, selection.target_api)
        source_id = f"{selection.case_id}_source"
        sources[source_id] = {
            "vendor": "api_bank",
            "kind": "sample",
            "url": f"{SAMPLE_ROOT}/{selection.sample_file}",
            "summary": f"API-Bank sample dialogue bridged into TOOLSHIFT case {selection.case_id}.",
        }

        for api_name in selection.tool_bundle:
            tool_id, tool_payload = _build_tool(api_name)
            tool_specs[tool_id] = tool_payload

        target_tool_id = _tool_id(selection.target_api)
        slot_values = _normalize_slot_values(api_turn["param_dict"], tool_specs[target_tool_id])
        cases.append(
            {
                "case_id": selection.case_id,
                "request": _serialize_context(transcript, selection.target_api),
                "tool_ids": [_tool_id(api_name) for api_name in selection.tool_bundle],
                "slot_values": slot_values,
                "admissible_actions": [
                    {
                        "control": "execute",
                        "tool_id": target_tool_id,
                        "arguments": slot_values,
                    }
                ],
                "family_tag": selection.family_tag,
                "notes": (
                    f"Imported from API-Bank sample {selection.sample_file}. "
                    f"Target API is {selection.target_api}; TOOLSHIFT transforms are applied automatically."
                ),
            }
        )
        audit_lines.append(
            f"| {selection.case_id} | `{selection.sample_file}` | `{selection.target_api}` | `{selection.family_tag}` | {selection.rationale} |"
        )

    payload: dict[str, object] = {
        "tools": [tool_specs[tool_id] for tool_id in sorted(tool_specs)],
        "cases": cases,
        "sources": sources,
        "metadata": {
            "external_source": "API-Bank",
            "bridge_kind": "external_static_tool_benchmark",
            "case_count": len(cases),
            "tool_count": len(tool_specs),
            "family_tags": sorted({selection.family_tag for selection in IMPORT_PLAN}),
        },
    }
    return payload, "\n".join(audit_lines) + "\n"


def _build_tool(api_name: str) -> tuple[str, dict[str, object]]:
    source = _fetch_text(f"{API_ROOT}/{_class_to_filename(api_name)}.py")
    description, parameters = _parse_api_source(source)
    arguments = []
    for position, (name, spec) in enumerate(parameters.items()):
        arguments.append(
            {
                "canonical_name": name,
                "description": spec["description"],
                "arg_type": _map_arg_type(spec["type"]),
                "required": True,
                "position": position,
            }
        )
    return _tool_id(api_name), {
        "tool_id": _tool_id(api_name),
        "description": description,
        "arguments": arguments,
        "semantic_tags": ["external", "api_bank", api_name.lower()],
    }


def _parse_api_source(source: str) -> tuple[str, dict[str, dict[str, str]]]:
    module = ast.parse(source)
    class_def = next(node for node in module.body if isinstance(node, ast.ClassDef))
    description = ""
    parameters: dict[str, dict[str, str]] = {}
    for node in class_def.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        name = node.targets[0].id
        if name == "description":
            description = ast.literal_eval(node.value)
        elif name == "input_parameters":
            parameters = ast.literal_eval(node.value)
    if not description or not parameters:
        raise ValueError("Failed to parse API-Bank tool definition")
    return description, parameters


def _serialize_context(transcript: list[dict[str, object]], target_api: str) -> str:
    lines = ["Dialogue context before the final API action:"]
    for turn in transcript:
        role = turn["role"]
        if role == "API" and turn["api_name"] == target_api:
            break
        if role == "User":
            lines.append(f"User: {turn['text']}")
        elif role == "AI":
            lines.append(f"Assistant: {turn['text']}")
        elif role == "API":
            result = turn.get("result", {})
            output = result.get("output") if isinstance(result, dict) else None
            lines.append(f"API[{turn['api_name']}] output: {json.dumps(output, ensure_ascii=False)}")
    lines.append("Choose the best final API action for this context.")
    return "\n".join(lines)


def _target_api_turn(transcript: list[dict[str, object]], target_api: str) -> dict[str, object]:
    for turn in reversed(transcript):
        if turn["role"] == "API" and turn["api_name"] == target_api:
            return turn
    raise KeyError(f"Target API {target_api} not found in transcript")


def _normalize_slot_values(slot_values: dict[str, object], tool_payload: dict[str, object]) -> dict[str, object]:
    typed_values: dict[str, object] = {}
    type_lookup = {argument["canonical_name"]: argument["arg_type"] for argument in tool_payload["arguments"]}
    for name, value in slot_values.items():
        arg_type = type_lookup.get(name, "string")
        if arg_type == "integer":
            typed_values[name] = int(value)
        elif arg_type == "number":
            typed_values[name] = float(value)
        elif arg_type == "boolean":
            typed_values[name] = str(value).strip().lower() in {"1", "true", "yes", "y"}
        else:
            typed_values[name] = value
    return typed_values


def _load_jsonl(url: str) -> list[dict[str, object]]:
    return [json.loads(line) for line in _fetch_text(url).splitlines() if line.strip()]


def _fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": "toolshift-importer"})
    with urlopen(request) as response:
        return response.read().decode("utf-8")


def _tool_id(api_name: str) -> str:
    return f"api_bank.{_class_to_filename(api_name)}"


def _class_to_filename(api_name: str) -> str:
    first_pass = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", api_name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", first_pass).lower()


def _map_arg_type(api_bank_type: str) -> str:
    lowered = api_bank_type.lower()
    if lowered == "int":
        return "integer"
    if lowered == "float":
        return "number"
    if lowered == "bool":
        return "boolean"
    return "string"
