from __future__ import annotations

import json
from dataclasses import replace
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .schema import CanonicalAction, CanonicalTool, ControlTag, SchemaView, ShiftKind, SplitTag
from .transforms import make_distractor_tool, render_tool, with_status


@dataclass(frozen=True)
class TaskCase:
    case_id: str
    request: str
    tool_ids: tuple[str, ...]
    slot_values: dict[str, Any]
    admissible_actions: tuple[CanonicalAction, ...]
    split_tag: SplitTag
    family_tag: str | None = None
    notes: str = ""

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TaskCase":
        return cls(
            case_id=payload["case_id"],
            request=payload["request"],
            tool_ids=tuple(payload["tool_ids"]),
            slot_values=dict(payload["slot_values"]),
            admissible_actions=tuple(CanonicalAction.from_dict(action) for action in payload["admissible_actions"]),
            split_tag=SplitTag(payload.get("split_tag", SplitTag.UNAMBIGUOUS_CORE.value)),
            family_tag=payload.get("family_tag"),
            notes=payload.get("notes", ""),
        )

    @property
    def primary_action(self) -> CanonicalAction:
        return self.admissible_actions[0]


@dataclass(frozen=True)
class ViewExample:
    case: TaskCase
    schema_view: SchemaView
    admissible_actions: tuple[CanonicalAction, ...]
    split_tag: SplitTag
    notes: str = ""


@dataclass(frozen=True)
class BenchmarkSuite:
    tool_lookup: dict[str, CanonicalTool]
    cases: tuple[TaskCase, ...]
    examples: tuple[ViewExample, ...]

    def examples_for_case(self, case_id: str) -> list[ViewExample]:
        return [example for example in self.examples if example.case.case_id == case_id]


def load_seed_suite(path: str | Path, audit_path: str | Path | None = None) -> BenchmarkSuite:
    benchmark_path = Path(path)
    payload = json.loads(benchmark_path.read_text(encoding="utf-8"))
    tool_lookup = {tool["tool_id"]: CanonicalTool.from_dict(tool) for tool in payload["tools"]}
    cases = tuple(TaskCase.from_dict(case_payload) for case_payload in payload["cases"])
    if payload.get("views"):
        examples = _build_explicit_examples(cases, payload["views"])
    else:
        examples = []
        for case in cases:
            examples.extend(_build_examples_for_case(case, tool_lookup))
    audit_payload = _load_audit_payload(benchmark_path, audit_path)
    if audit_payload is not None:
        examples = _apply_audit_overrides(examples, audit_payload)
    return BenchmarkSuite(tool_lookup=tool_lookup, cases=cases, examples=tuple(examples))


def _load_audit_payload(benchmark_path: Path, audit_path: str | Path | None) -> dict[str, Any] | None:
    if audit_path is not None:
        resolved_paths = [Path(audit_path)]
    else:
        benchmark_name = benchmark_path.name
        candidates = []
        if benchmark_name.endswith("_benchmark.json"):
            candidates.append(benchmark_name.replace("_benchmark.json", "_audit.json"))
        candidates.append(f"{benchmark_path.stem}_audit.json")
        candidates.append("seed_audit.json")
        resolved_paths = [benchmark_path.with_name(candidate) for candidate in candidates]
    for resolved_path in resolved_paths:
        if resolved_path.exists():
            return json.loads(resolved_path.read_text(encoding="utf-8"))
    return None


def _apply_audit_overrides(examples: list[ViewExample], audit_payload: dict[str, Any]) -> list[ViewExample]:
    case_overrides = audit_payload.get("case_overrides", {})
    view_overrides = audit_payload.get("view_overrides", {})
    updated: list[ViewExample] = []
    for example in examples:
        merged_override = {}
        if example.case.case_id in case_overrides:
            merged_override.update(case_overrides[example.case.case_id])
        if example.schema_view.view_id in view_overrides:
            merged_override.update(view_overrides[example.schema_view.view_id])
        updated.append(_apply_override(example, merged_override))
    return updated


def _apply_override(example: ViewExample, override: dict[str, Any]) -> ViewExample:
    if not override:
        return example
    split_tag = example.split_tag
    if "split_tag" in override:
        split_tag = SplitTag(override["split_tag"])
    admissible_actions = example.admissible_actions
    if "admissible_actions" in override:
        admissible_actions = tuple(CanonicalAction.from_dict(action) for action in override["admissible_actions"])
    notes = example.notes
    override_note = override.get("note")
    if override_note:
        notes = f"{notes} Audit: {override_note}".strip()
    return replace(
        example,
        split_tag=split_tag,
        admissible_actions=admissible_actions,
        notes=notes,
    )


def _base_tools(case: TaskCase, tool_lookup: dict[str, CanonicalTool]) -> list[CanonicalTool]:
    return [tool_lookup[tool_id] for tool_id in case.tool_ids]


def _keyword(case: TaskCase) -> str:
    primary_tool = case.primary_action.tool_id or "task"
    return primary_tool.split(".")[0]


def _build_explicit_examples(cases: tuple[TaskCase, ...], view_payloads: list[dict[str, Any]]) -> list[ViewExample]:
    case_lookup = {case.case_id: case for case in cases}
    examples: list[ViewExample] = []
    for payload in view_payloads:
        case = case_lookup[payload["case_id"]]
        split_tag = SplitTag(payload.get("split_tag", case.split_tag.value))
        admissible_actions = tuple(
            CanonicalAction.from_dict(action) for action in payload.get("admissible_actions", [action.to_dict() for action in case.admissible_actions])
        )
        example = ViewExample(
            case=case,
            schema_view=SchemaView.from_dict(payload["schema_view"]),
            admissible_actions=admissible_actions,
            split_tag=split_tag,
            notes=payload.get("notes", ""),
        )
        examples.append(example)
    return examples


def _build_examples_for_case(case: TaskCase, tool_lookup: dict[str, CanonicalTool]) -> list[ViewExample]:
    tools = _base_tools(case, tool_lookup)
    primary_tool_id = case.primary_action.tool_id
    assert primary_tool_id is not None

    clean_tools = tuple(render_tool(tool) for tool in tools)
    rename_tools = tuple(render_tool(tool, rename=True) for tool in tools)
    paraphrase_tools = tuple(render_tool(tool, paraphrase=True) for tool in tools)
    combo_tools = tuple(render_tool(tool, rename=True, paraphrase=True, reorder=True) for tool in tools) + (
        make_distractor_tool(_keyword(case)),
    )

    contract_tools = []
    mutated = False
    for tool in tools:
        if tool.tool_id != primary_tool_id:
            contract_tools.append(render_tool(tool))
            continue
        contract_tools.append(_contract_mutated_tool(tool, case))
        mutated = True
    if not mutated:
        contract_tools = [render_tool(tool) for tool in tools]

    deprecated_tools = []
    for tool in tools:
        rendered = render_tool(tool, paraphrase=True)
        if tool.tool_id == primary_tool_id:
            rendered = with_status(
                rendered,
                status="deprecated",
                description_prefix="Deprecated: this tool no longer satisfies the original request contract.",
            )
        deprecated_tools.append(rendered)

    impossible_tools = tuple(render_tool(tool) for tool in tools)

    return [
        ViewExample(
            case=case,
            schema_view=SchemaView(
                view_id=f"{case.case_id}::clean",
                transform_name="clean",
                shift_kind=ShiftKind.CLEAN,
                tools=clean_tools,
                notes="Canonical clean schema view.",
            ),
            admissible_actions=case.admissible_actions,
            split_tag=case.split_tag,
            notes="Main clean evaluation sample.",
        ),
        ViewExample(
            case=case,
            schema_view=SchemaView(
                view_id=f"{case.case_id}::positive_rename",
                transform_name="positive_rename",
                shift_kind=ShiftKind.POSITIVE_ORBIT,
                tools=rename_tools,
                notes="Schema-preserving rename and alias view.",
            ),
            admissible_actions=case.admissible_actions,
            split_tag=case.split_tag,
            notes="Positive orbit: rename/alias only.",
        ),
        ViewExample(
            case=case,
            schema_view=SchemaView(
                view_id=f"{case.case_id}::positive_paraphrase",
                transform_name="positive_paraphrase",
                shift_kind=ShiftKind.POSITIVE_ORBIT,
                tools=paraphrase_tools,
                notes="Schema-preserving documentation paraphrase.",
            ),
            admissible_actions=case.admissible_actions,
            split_tag=case.split_tag,
            notes="Positive orbit: doc paraphrase only.",
        ),
        ViewExample(
            case=case,
            schema_view=SchemaView(
                view_id=f"{case.case_id}::positive_combo",
                transform_name="positive_combo",
                shift_kind=ShiftKind.POSITIVE_ORBIT,
                tools=combo_tools,
                notes="Schema-preserving composition of rename, paraphrase, reorder, and distractor insertion.",
            ),
            admissible_actions=case.admissible_actions,
            split_tag=case.split_tag,
            notes="Positive orbit: compositional shift.",
        ),
        ViewExample(
            case=case,
            schema_view=SchemaView(
                view_id=f"{case.case_id}::negative_contract",
                transform_name="negative_contract",
                shift_kind=ShiftKind.NEGATIVE_NEAR_ORBIT,
                tools=tuple(contract_tools),
                notes="Schema-visible contract mutation that invalidates the base action.",
            ),
            admissible_actions=(
                CanonicalAction(control=ControlTag.ASK_CLARIFICATION),
            ),
            split_tag=case.split_tag,
            notes="Negative near-orbit: base action should not be executed as-is.",
        ),
        ViewExample(
            case=case,
            schema_view=SchemaView(
                view_id=f"{case.case_id}::negative_deprecate",
                transform_name="negative_deprecate",
                shift_kind=ShiftKind.NEGATIVE_NEAR_ORBIT,
                tools=tuple(deprecated_tools),
                notes="Schema-visible deprecation with no admissible substitute in the seed suite.",
            ),
            admissible_actions=(
                CanonicalAction(control=ControlTag.ABSTAIN),
                CanonicalAction(control=ControlTag.ASK_CLARIFICATION),
            ),
            split_tag=case.split_tag,
            notes="Negative near-orbit: abstain and ask_clarification are both admissible control responses.",
        ),
        ViewExample(
            case=case,
            schema_view=SchemaView(
                view_id=f"{case.case_id}::impossible_hidden_behavior",
                transform_name="impossible_hidden_behavior",
                shift_kind=ShiftKind.IMPOSSIBLE,
                tools=impossible_tools,
                notes="Hidden backend behavior shift with identical schema. This split should be failed honestly.",
            ),
            admissible_actions=case.admissible_actions,
            split_tag=case.split_tag,
            notes="Boundary split; excluded from main summary.",
        ),
    ]


def _contract_mutated_tool(tool: CanonicalTool, case: TaskCase):
    action = case.primary_action
    overrides: dict[str, dict[str, object]] = {}
    for argument in tool.arguments:
        if argument.canonical_name not in action.arguments:
            continue
        gold_value = action.arguments[argument.canonical_name]
        if argument.arg_type == "enum" and argument.enum_values:
            mutated_choices = tuple(choice for choice in argument.enum_values if str(choice).lower() != str(gold_value).lower())
            if mutated_choices:
                overrides[argument.canonical_name] = {
                    "enum_values": mutated_choices,
                    "description": f"{argument.description} The previous value {gold_value!r} is no longer accepted.",
                }
                return render_tool(tool, arg_overrides=overrides, paraphrase=True)
        if argument.arg_type in {"integer", "number"}:
            try:
                numeric_value = float(gold_value)
            except (TypeError, ValueError):
                numeric_value = None
            if numeric_value is not None:
                overrides[argument.canonical_name] = {
                    "minimum": numeric_value + 1,
                    "description": f"{argument.description} Values at or below {numeric_value} are now rejected.",
                }
                return render_tool(tool, arg_overrides=overrides, paraphrase=True)
        if argument.arg_type == "string":
            overrides[argument.canonical_name] = {
                "arg_type": "integer",
                "description": f"{argument.description} The contract now expects an integer-coded value instead of free text.",
            }
            return render_tool(tool, arg_overrides=overrides, paraphrase=True)
    return render_tool(tool, paraphrase=True)
