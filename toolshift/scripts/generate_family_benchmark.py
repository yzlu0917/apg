#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path


ABSTAIN_ONLY = {
    "admissible_actions": [
        {
            "control": "abstain",
        }
    ],
    "note": "Deprecated primary tool with no visible substitute should be abstain-only in the richer family suite.",
}


def _action(tool_id: str, **arguments):
    return {
        "control": "execute",
        "tool_id": tool_id,
        "arguments": arguments,
    }


def _case(
    case_id: str,
    request: str,
    tool_ids: list[str],
    slot_values: dict[str, object],
    action: dict[str, object],
    notes: str,
):
    return {
        "case_id": case_id,
        "request": request,
        "tool_ids": tool_ids,
        "slot_values": slot_values,
        "admissible_actions": [action],
        "notes": notes,
    }


def _weather(case_id: str, request: str, city: str, unit: str) -> dict[str, object]:
    return _case(
        case_id,
        request,
        ["weather.get_current", "finance.convert_currency", "email.send"],
        {"city": city, "temperature_unit": unit},
        _action("weather.get_current", city=city, temperature_unit=unit),
        notes="family=weather",
    )


def _finance(case_id: str, request: str, amount: float, source_currency: str, target_currency: str) -> dict[str, object]:
    return _case(
        case_id,
        request,
        ["finance.convert_currency", "weather.get_current", "documents.search"],
        {
            "amount": amount,
            "source_currency": source_currency,
            "target_currency": target_currency,
        },
        _action(
            "finance.convert_currency",
            amount=amount,
            source_currency=source_currency,
            target_currency=target_currency,
        ),
        notes="family=finance",
    )


def _documents(case_id: str, request: str, search_query: str, directory_path: str, recursive: bool) -> dict[str, object]:
    recursive_text = "recursive" if recursive else "non_recursive"
    return _case(
        case_id,
        request,
        ["documents.search", "reminders.create", "notes.summarize"],
        {
            "search_query": search_query,
            "directory_path": directory_path,
            "recursive": recursive,
        },
        _action(
            "documents.search",
            search_query=search_query,
            directory_path=directory_path,
            recursive=recursive,
        ),
        notes=f"family=documents;search_mode={recursive_text}",
    )


def _email(case_id: str, request: str, recipient_email: str, email_subject: str, email_body: str) -> dict[str, object]:
    return _case(
        case_id,
        request,
        ["email.send", "calendar.schedule", "notes.summarize"],
        {
            "recipient_email": recipient_email,
            "email_subject": email_subject,
            "email_body": email_body,
        },
        _action(
            "email.send",
            recipient_email=recipient_email,
            email_subject=email_subject,
            email_body=email_body,
        ),
        notes="family=email",
    )


def _reminder(case_id: str, request: str, reminder_text: str, due_datetime: str, timezone: str) -> dict[str, object]:
    return _case(
        case_id,
        request,
        ["reminders.create", "calendar.schedule", "email.send"],
        {
            "reminder_text": reminder_text,
            "due_datetime": due_datetime,
            "timezone": timezone,
        },
        _action(
            "reminders.create",
            reminder_text=reminder_text,
            due_datetime=due_datetime,
            timezone=timezone,
        ),
        notes="family=reminders_absolute",
    )


def _calendar(case_id: str, request: str, event_title: str, start_datetime: str, attendees: str, timezone: str) -> dict[str, object]:
    return _case(
        case_id,
        request,
        ["calendar.schedule", "email.send", "documents.search"],
        {
            "event_title": event_title,
            "start_datetime": start_datetime,
            "attendees": attendees,
            "timezone": timezone,
        },
        _action(
            "calendar.schedule",
            event_title=event_title,
            start_datetime=start_datetime,
            attendees=attendees,
            timezone=timezone,
        ),
        notes="family=calendar_absolute",
    )


def build_cases() -> list[dict[str, object]]:
    return [
        _weather(
            "weather_tokyo_fahrenheit",
            "Check the current weather in Tokyo and return it in Fahrenheit.",
            city="Tokyo",
            unit="fahrenheit",
        ),
        _weather(
            "weather_berlin_celsius",
            "Give me Berlin's current weather in Celsius.",
            city="Berlin",
            unit="celsius",
        ),
        _weather(
            "weather_seattle_celsius",
            "Pull the live weather for Seattle in Celsius.",
            city="Seattle",
            unit="celsius",
        ),
        _finance(
            "fx_eur_to_gbp",
            "Convert 120 euros into British pounds.",
            amount=120,
            source_currency="EUR",
            target_currency="GBP",
        ),
        _finance(
            "fx_jpy_to_usd",
            "How much is 5000 JPY in USD?",
            amount=5000,
            source_currency="JPY",
            target_currency="USD",
        ),
        _finance(
            "fx_cad_to_aud",
            "Translate 88 Canadian dollars into Australian dollars.",
            amount=88,
            source_currency="CAD",
            target_currency="AUD",
        ),
        _documents(
            "documents_alignment_archive_recursive",
            "Search the archive directory recursively for mentions of schema alignment.",
            search_query="schema alignment",
            directory_path="archive",
            recursive=True,
        ),
        _documents(
            "documents_reviewer_feedback_nonrecursive",
            "Look in the reviews folder for files about reviewer feedback without scanning subfolders.",
            search_query="reviewer feedback",
            directory_path="reviews",
            recursive=False,
        ),
        _documents(
            "documents_latency_notes_recursive",
            "Find documents about latency regressions inside the notes directory and its children.",
            search_query="latency regressions",
            directory_path="notes",
            recursive=True,
        ),
        _email(
            "email_weekly_status",
            "Send an email to mei@example.com with subject Weekly status and body Experiment finished on schedule.",
            recipient_email="mei@example.com",
            email_subject="Weekly status",
            email_body="Experiment finished on schedule.",
        ),
        _email(
            "email_budget_followup",
            "Email lee@example.com with subject Budget follow-up and body Revised spreadsheet is attached.",
            recipient_email="lee@example.com",
            email_subject="Budget follow-up",
            email_body="Revised spreadsheet is attached.",
        ),
        _email(
            "email_demo_confirmation",
            "Send a confirmation email to noa@example.com titled Demo confirmation with body Thursday still works for us.",
            recipient_email="noa@example.com",
            email_subject="Demo confirmation",
            email_body="Thursday still works for us.",
        ),
        _reminder(
            "reminder_boarding_pass_absolute",
            "Create a reminder for 2026-04-02T06:30:00 Asia/Tokyo to download the boarding pass.",
            reminder_text="download the boarding pass",
            due_datetime="2026-04-02T06:30:00",
            timezone="Asia/Tokyo",
        ),
        _reminder(
            "reminder_invoice_absolute",
            "Set a reminder for 2026-05-18T14:00:00 Europe/Berlin to send the invoice.",
            reminder_text="send the invoice",
            due_datetime="2026-05-18T14:00:00",
            timezone="Europe/Berlin",
        ),
        _reminder(
            "reminder_backup_absolute",
            "Make a reminder for 2026-06-01T21:15:00 America/Los_Angeles to run the backup.",
            reminder_text="run the backup",
            due_datetime="2026-06-01T21:15:00",
            timezone="America/Los_Angeles",
        ),
        _calendar(
            "calendar_ablation_review_absolute",
            "Schedule a meeting called Ablation review on 2026-04-08T10:00:00 Europe/London with ava@example.com.",
            event_title="Ablation review",
            start_datetime="2026-04-08T10:00:00",
            attendees="ava@example.com",
            timezone="Europe/London",
        ),
        _calendar(
            "calendar_budget_sync_absolute",
            "Schedule a meeting named Budget sync on 2026-05-03T16:30:00 America/New_York with max@example.com.",
            event_title="Budget sync",
            start_datetime="2026-05-03T16:30:00",
            attendees="max@example.com",
            timezone="America/New_York",
        ),
        _calendar(
            "calendar_demo_debrief_absolute",
            "Create a calendar event called Demo debrief on 2026-06-12T09:45:00 Asia/Singapore with iris@example.com.",
            event_title="Demo debrief",
            start_datetime="2026-06-12T09:45:00",
            attendees="iris@example.com",
            timezone="Asia/Singapore",
        ),
    ]


def build_audit_payload(cases: list[dict[str, object]]) -> dict[str, object]:
    view_overrides = {}
    for case in cases:
        view_overrides[f"{case['case_id']}::negative_deprecate"] = ABSTAIN_ONLY
    return {
        "case_overrides": {},
        "view_overrides": view_overrides,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a richer same-family ToolShift benchmark.")
    parser.add_argument("--source-benchmark", default="data/seed_benchmark.json")
    parser.add_argument("--output-benchmark", default="data/family_benchmark.json")
    parser.add_argument("--output-audit", default="data/family_audit.json")
    args = parser.parse_args()

    source_payload = json.loads(Path(args.source_benchmark).read_text(encoding="utf-8"))
    cases = build_cases()
    case_ids = [case["case_id"] for case in cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("duplicate case ids in family benchmark generation")

    benchmark_payload = {
        "tools": source_payload["tools"],
        "cases": cases,
    }
    audit_payload = build_audit_payload(cases)

    output_benchmark = Path(args.output_benchmark)
    output_audit = Path(args.output_audit)
    output_benchmark.write_text(json.dumps(benchmark_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    output_audit.write_text(json.dumps(audit_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(cases)} cases to {output_benchmark}")
    print(f"Wrote audit overrides to {output_audit}")


if __name__ == "__main__":
    main()
