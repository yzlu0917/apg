from __future__ import annotations

from dataclasses import replace

from .schema import CanonicalTool, RenderedArgument, RenderedTool


TOOL_RENAMES: dict[str, str] = {
    "weather.get_current": "climate_probe",
    "finance.convert_currency": "fx_quote",
    "reminders.create": "memorize_task",
    "documents.search": "doc_locator",
    "calendar.schedule": "agenda_commit",
    "email.send": "dispatch_message",
    "notes.summarize": "brief_note",
}

ARG_RENAMES: dict[str, str] = {
    "city": "locale",
    "temperature_unit": "temp_scale",
    "amount": "quantity",
    "source_currency": "from_ccy",
    "target_currency": "into_ccy",
    "reminder_text": "task_prompt",
    "due_datetime": "trigger_at",
    "timezone": "tz_code",
    "search_query": "needle",
    "directory_path": "root_path",
    "recursive": "walk_tree",
    "event_title": "meeting_label",
    "start_datetime": "starts_at",
    "attendees": "guest_list",
    "recipient_email": "recipient",
    "email_subject": "title_line",
    "email_body": "message_body",
}

PARAPHRASES: dict[str, str] = {
    "weather.get_current": "Return a present-time atmospheric snapshot for a named place.",
    "finance.convert_currency": "Translate an amount from one currency into another at the latest rate.",
    "reminders.create": "Store a personal reminder and schedule when it should alert.",
    "documents.search": "Locate files whose contents or names match the supplied query.",
    "calendar.schedule": "Create a calendar event with a start time and participants.",
    "email.send": "Deliver an email message with recipient, subject, and body content.",
    "notes.summarize": "Condense a note into a shorter digest.",
}

ARG_PARAPHRASES: dict[str, str] = {
    "city": "Named place whose current conditions should be checked.",
    "temperature_unit": "Requested temperature scale, such as celsius or fahrenheit.",
    "amount": "Numeric amount that needs conversion.",
    "source_currency": "Currency the amount currently uses.",
    "target_currency": "Currency the caller wants back.",
    "reminder_text": "Task or reminder content to remember later.",
    "due_datetime": "Exact alert time, expressed as a timestamp string.",
    "timezone": "Time zone that anchors the supplied time.",
    "search_query": "Text or concept that documents should match.",
    "directory_path": "Folder to search inside.",
    "recursive": "Whether subdirectories should be traversed too.",
    "event_title": "Human-facing title of the meeting or event.",
    "start_datetime": "When the event should begin.",
    "attendees": "People who should be invited.",
    "recipient_email": "Email address that should receive the message.",
    "email_subject": "Subject line shown to the recipient.",
    "email_body": "Main body text of the outgoing email.",
}


def render_tool(
    tool: CanonicalTool,
    *,
    rename: bool = False,
    paraphrase: bool = False,
    reorder: bool = False,
    status: str = "active",
    arg_overrides: dict[str, dict[str, object]] | None = None,
) -> RenderedTool:
    rendered_name = TOOL_RENAMES.get(tool.tool_id, tool.tool_id.split(".")[-1]) if rename else tool.tool_id.split(".")[-1]
    description = PARAPHRASES.get(tool.tool_id, tool.description) if paraphrase else tool.description
    arg_overrides = arg_overrides or {}
    rendered_arguments: list[RenderedArgument] = []
    base_arguments = list(tool.arguments)
    if reorder:
        base_arguments = list(reversed(base_arguments))
    for index, argument in enumerate(base_arguments):
        override = dict(arg_overrides.get(argument.canonical_name, {}))
        rendered_argument = RenderedArgument(
            rendered_name=str(
                override.pop(
                    "rendered_name",
                    ARG_RENAMES.get(argument.canonical_name, argument.canonical_name) if rename else argument.canonical_name,
                )
            ),
            canonical_name=argument.canonical_name,
            description=str(
                override.pop(
                    "description",
                    ARG_PARAPHRASES.get(argument.canonical_name, argument.description) if paraphrase else argument.description,
                )
            ),
            arg_type=str(override.pop("arg_type", argument.arg_type)),
            required=bool(override.pop("required", argument.required)),
            enum_values=tuple(override.pop("enum_values", argument.enum_values)),
            minimum=override.pop("minimum", argument.minimum),
            maximum=override.pop("maximum", argument.maximum),
            position=index,
        )
        rendered_arguments.append(rendered_argument)
    return RenderedTool(
        canonical_tool_id=tool.tool_id,
        rendered_name=rendered_name,
        description=description,
        arguments=tuple(rendered_arguments),
        status=status,
    )


def make_distractor_tool(case_keyword: str) -> RenderedTool:
    return RenderedTool(
        canonical_tool_id=f"distractor.{case_keyword}",
        rendered_name=f"{case_keyword}_debug_console",
        description=f"Inspect internal {case_keyword} traces and diagnostics. Not intended for end-user task execution.",
        status="active",
        arguments=(
            RenderedArgument(
                rendered_name="trace_id",
                canonical_name="trace_id",
                description="Internal trace identifier.",
                arg_type="string",
                required=True,
                position=0,
            ),
        ),
    )


def with_status(tool: RenderedTool, status: str, description_prefix: str) -> RenderedTool:
    return replace(tool, status=status, description=f"{description_prefix} {tool.description}".strip())

