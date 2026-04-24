from __future__ import annotations

from dataclasses import replace

from .benchmark import ViewExample
from .schema import RenderedArgument, RenderedTool, SchemaView


MASK_VARIANTS: tuple[str, ...] = ("unmasked", "name_mask", "description_mask", "contract_mask")


def mask_example(example: ViewExample, mask_name: str) -> ViewExample:
    if mask_name not in MASK_VARIANTS:
        raise ValueError(f"unsupported mask_name: {mask_name}")
    if mask_name == "unmasked":
        return example
    masked_tools = tuple(_mask_tool(tool, tool_index=index, mask_name=mask_name) for index, tool in enumerate(example.schema_view.tools))
    masked_view = SchemaView(
        view_id=f"{example.schema_view.view_id}|{mask_name}",
        transform_name=f"{example.schema_view.transform_name}|{mask_name}",
        shift_kind=example.schema_view.shift_kind,
        tools=masked_tools,
        notes=f"{example.schema_view.notes} [{mask_name}]".strip(),
    )
    return replace(example, schema_view=masked_view, notes=f"{example.notes} [{mask_name}]".strip())


def mask_examples(examples: tuple[ViewExample, ...] | list[ViewExample], mask_name: str) -> tuple[ViewExample, ...]:
    return tuple(mask_example(example, mask_name) for example in examples)


def _mask_tool(tool: RenderedTool, *, tool_index: int, mask_name: str) -> RenderedTool:
    masked_arguments = tuple(
        _mask_argument(argument, argument_index=index, mask_name=mask_name)
        for index, argument in enumerate(tool.arguments)
    )
    if mask_name == "name_mask":
        return replace(
            tool,
            rendered_name=f"tool_{tool_index + 1}",
            arguments=masked_arguments,
        )
    if mask_name == "description_mask":
        return replace(
            tool,
            description="",
            arguments=masked_arguments,
        )
    if mask_name == "contract_mask":
        return replace(
            tool,
            description="",
            status="active",
            arguments=masked_arguments,
        )
    raise ValueError(f"unsupported mask_name: {mask_name}")


def _mask_argument(argument: RenderedArgument, *, argument_index: int, mask_name: str) -> RenderedArgument:
    if mask_name == "name_mask":
        return replace(argument, rendered_name=f"arg_{argument_index + 1}")
    if mask_name in {"description_mask", "contract_mask"}:
        return replace(argument, description="")
    raise ValueError(f"unsupported mask_name: {mask_name}")
