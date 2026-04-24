from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ControlTag(str, Enum):
    EXECUTE = "execute"
    ABSTAIN = "abstain"
    ASK_CLARIFICATION = "ask_clarification"


class SplitTag(str, Enum):
    UNAMBIGUOUS_CORE = "unambiguous_core"
    AMBIGUOUS = "ambiguous_split"


class ShiftKind(str, Enum):
    CLEAN = "clean"
    POSITIVE_ORBIT = "positive_orbit"
    NEGATIVE_NEAR_ORBIT = "negative_near_orbit"
    IMPOSSIBLE = "impossible"


@dataclass(frozen=True)
class CanonicalArgument:
    canonical_name: str
    description: str
    arg_type: str
    required: bool = True
    enum_values: tuple[str, ...] = ()
    minimum: float | None = None
    maximum: float | None = None
    aliases: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CanonicalArgument":
        return cls(
            canonical_name=payload["canonical_name"],
            description=payload["description"],
            arg_type=payload["arg_type"],
            required=payload.get("required", True),
            enum_values=tuple(payload.get("enum_values", ())),
            minimum=payload.get("minimum"),
            maximum=payload.get("maximum"),
            aliases=tuple(payload.get("aliases", ())),
        )

    def normalize(self, value: Any) -> Any:
        if value is None:
            return None
        if self.arg_type == "string":
            return str(value).strip()
        if self.arg_type == "enum":
            return str(value).strip().lower()
        if self.arg_type == "integer":
            return int(value)
        if self.arg_type == "number":
            return float(value)
        if self.arg_type == "boolean":
            if isinstance(value, bool):
                return value
            return str(value).strip().lower() in {"1", "true", "yes", "y"}
        return value

    def validate(self, value: Any) -> tuple[bool, str | None]:
        if value is None:
            if self.required:
                return False, f"missing required argument: {self.canonical_name}"
            return True, None
        try:
            normalized = self.normalize(value)
        except (TypeError, ValueError) as exc:
            return False, f"{self.canonical_name} normalization failed: {exc}"
        if self.arg_type == "enum" and self.enum_values:
            allowed = {entry.lower() for entry in self.enum_values}
            if normalized not in allowed:
                return False, f"{self.canonical_name}={normalized} outside enum set"
        if self.arg_type in {"integer", "number"}:
            if self.minimum is not None and normalized < self.minimum:
                return False, f"{self.canonical_name}={normalized} below minimum {self.minimum}"
            if self.maximum is not None and normalized > self.maximum:
                return False, f"{self.canonical_name}={normalized} above maximum {self.maximum}"
        return True, None

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_name": self.canonical_name,
            "description": self.description,
            "arg_type": self.arg_type,
            "required": self.required,
            "enum_values": list(self.enum_values),
            "minimum": self.minimum,
            "maximum": self.maximum,
            "aliases": list(self.aliases),
        }


@dataclass(frozen=True)
class CanonicalTool:
    tool_id: str
    description: str
    arguments: tuple[CanonicalArgument, ...]
    semantic_tags: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CanonicalTool":
        return cls(
            tool_id=payload["tool_id"],
            description=payload["description"],
            arguments=tuple(CanonicalArgument.from_dict(arg) for arg in payload["arguments"]),
            semantic_tags=tuple(payload.get("semantic_tags", ())),
        )

    def argument(self, canonical_name: str) -> CanonicalArgument:
        for argument in self.arguments:
            if argument.canonical_name == canonical_name:
                return argument
        raise KeyError(f"unknown argument {canonical_name} for {self.tool_id}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "description": self.description,
            "arguments": [argument.to_dict() for argument in self.arguments],
            "semantic_tags": list(self.semantic_tags),
        }


@dataclass(frozen=True)
class RenderedArgument:
    rendered_name: str
    canonical_name: str
    description: str
    arg_type: str
    required: bool = True
    enum_values: tuple[str, ...] = ()
    minimum: float | None = None
    maximum: float | None = None
    position: int = 0

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RenderedArgument":
        return cls(
            rendered_name=payload["rendered_name"],
            canonical_name=payload["canonical_name"],
            description=payload["description"],
            arg_type=payload["arg_type"],
            required=payload.get("required", True),
            enum_values=tuple(payload.get("enum_values", ())),
            minimum=payload.get("minimum"),
            maximum=payload.get("maximum"),
            position=payload.get("position", 0),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "rendered_name": self.rendered_name,
            "canonical_name": self.canonical_name,
            "description": self.description,
            "arg_type": self.arg_type,
            "required": self.required,
            "enum_values": list(self.enum_values),
            "minimum": self.minimum,
            "maximum": self.maximum,
            "position": self.position,
        }


@dataclass(frozen=True)
class RenderedTool:
    canonical_tool_id: str
    rendered_name: str
    description: str
    arguments: tuple[RenderedArgument, ...]
    status: str = "active"

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RenderedTool":
        return cls(
            canonical_tool_id=payload["canonical_tool_id"],
            rendered_name=payload["rendered_name"],
            description=payload["description"],
            arguments=tuple(RenderedArgument.from_dict(argument) for argument in payload["arguments"]),
            status=payload.get("status", "active"),
        )

    def argument_by_rendered_name(self, rendered_name: str) -> RenderedArgument:
        lowered = rendered_name.lower()
        for argument in self.arguments:
            if argument.rendered_name.lower() == lowered:
                return argument
        raise KeyError(f"unknown rendered argument {rendered_name} for {self.rendered_name}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_tool_id": self.canonical_tool_id,
            "rendered_name": self.rendered_name,
            "description": self.description,
            "status": self.status,
            "arguments": [argument.to_dict() for argument in self.arguments],
        }


@dataclass(frozen=True)
class SchemaView:
    view_id: str
    transform_name: str
    shift_kind: ShiftKind
    tools: tuple[RenderedTool, ...]
    notes: str = ""

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SchemaView":
        return cls(
            view_id=payload["view_id"],
            transform_name=payload["transform_name"],
            shift_kind=ShiftKind(payload["shift_kind"]),
            tools=tuple(RenderedTool.from_dict(tool) for tool in payload["tools"]),
            notes=payload.get("notes", ""),
        )

    def tool_by_name(self, rendered_name: str) -> RenderedTool | None:
        lowered = rendered_name.lower()
        for tool in self.tools:
            if tool.rendered_name.lower() == lowered:
                return tool
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "view_id": self.view_id,
            "transform_name": self.transform_name,
            "shift_kind": self.shift_kind.value,
            "notes": self.notes,
            "tools": [tool.to_dict() for tool in self.tools],
        }


@dataclass(frozen=True)
class CanonicalAction:
    control: ControlTag
    tool_id: str | None = None
    arguments: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CanonicalAction":
        return cls(
            control=ControlTag(payload["control"]),
            tool_id=payload.get("tool_id"),
            arguments=dict(payload.get("arguments", {})),
        )

    def normalized(self, tool_lookup: dict[str, CanonicalTool]) -> "CanonicalAction":
        if self.control != ControlTag.EXECUTE:
            return CanonicalAction(control=self.control, tool_id=None, arguments={})
        if self.tool_id is None:
            raise ValueError("execute action must include tool_id")
        tool = tool_lookup[self.tool_id]
        normalized_arguments: dict[str, Any] = {}
        for argument in tool.arguments:
            value = self.arguments.get(argument.canonical_name)
            normalized_arguments[argument.canonical_name] = argument.normalize(value)
        return CanonicalAction(control=self.control, tool_id=self.tool_id, arguments=normalized_arguments)

    def fingerprint(self, tool_lookup: dict[str, CanonicalTool]) -> str:
        normalized = self.normalized(tool_lookup)
        payload = {
            "control": normalized.control.value,
            "tool_id": normalized.tool_id,
            "arguments": normalized.arguments,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "control": self.control.value,
            "tool_id": self.tool_id,
            "arguments": self.arguments,
        }


@dataclass(frozen=True)
class ToolCall:
    control: ControlTag
    rendered_tool_name: str | None = None
    arguments: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "control": self.control.value,
            "rendered_tool_name": self.rendered_tool_name,
            "arguments": self.arguments,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }
