from __future__ import annotations

import unittest
from dataclasses import replace

from toolshift import OracleAgent, evaluate_agent, load_seed_suite
from toolshift.eval import canonicalize_prediction
from toolshift.schema import ControlTag, RenderedArgument, ToolCall


class AuditOverrideTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.suite = load_seed_suite("data/seed_benchmark.json")

    def test_audit_marks_calendar_clean_as_ambiguous(self) -> None:
        example = next(item for item in self.suite.examples if item.schema_view.view_id == "calendar_toolshift_sync::clean")
        self.assertEqual(example.split_tag.value, "ambiguous_split")

    def test_audit_overrides_negative_deprecate_to_abstain_only(self) -> None:
        example = next(item for item in self.suite.examples if item.schema_view.view_id == "email_follow_up::negative_deprecate")
        self.assertEqual([action.control.value for action in example.admissible_actions], ["abstain"])

    def test_absolute_time_cases_stay_in_core(self) -> None:
        reminder = next(item for item in self.suite.examples if item.schema_view.view_id == "reminder_tax_form_absolute::clean")
        calendar = next(item for item in self.suite.examples if item.schema_view.view_id == "calendar_toolshift_sync_absolute::clean")
        self.assertEqual(reminder.split_tag.value, "unambiguous_core")
        self.assertEqual(calendar.split_tag.value, "unambiguous_core")

    def test_main_metrics_only_use_unambiguous_core(self) -> None:
        _, summary = evaluate_agent(OracleAgent(), self.suite)
        self.assertEqual(summary["counts"]["core"], 38)
        self.assertEqual(summary["counts"]["ambiguous"], 10)
        self.assertEqual(summary["counts"]["impossible"], 8)
        self.assertEqual(summary["metrics"]["CAA_overall"], 1.0)

    def test_temporal_bundle_is_split_into_datetime_and_timezone(self) -> None:
        example = next(item for item in self.suite.examples if item.schema_view.view_id == "calendar_toolshift_sync_absolute::clean")
        call = ToolCall(
            control=ControlTag.EXECUTE,
            rendered_tool_name="schedule",
            arguments={
                "event_title": "ToolShift sync",
                "start_datetime": "2026-03-12T15:00:00 Asia/Shanghai",
                "attendees": "lin@example.com",
            },
        )
        canonicalized = canonicalize_prediction(example, self.suite.tool_lookup, call)
        self.assertTrue(canonicalized.contract_ok)
        self.assertEqual(canonicalized.action.arguments["start_datetime"], "2026-03-12T15:00:00")
        self.assertEqual(canonicalized.action.arguments["timezone"], "Asia/Shanghai")

    def test_execute_path_ignores_noncanonical_helper_arguments(self) -> None:
        example = next(item for item in self.suite.examples if item.schema_view.view_id == "weather_shanghai_celsius::clean")
        tool = example.schema_view.tools[0]
        helper_argument = RenderedArgument(
            rendered_name="helper_flag",
            canonical_name="helper_flag",
            description="Temporary helper flag not part of canonical action space.",
            arg_type="string",
            required=False,
            position=len(tool.arguments),
        )
        mutated_tool = replace(tool, arguments=tool.arguments + (helper_argument,))
        mutated_example = replace(example, schema_view=replace(example.schema_view, tools=(mutated_tool,)))
        call = ToolCall(
            control=ControlTag.EXECUTE,
            rendered_tool_name=mutated_tool.rendered_name,
            arguments={
                "city": "Shanghai",
                "temperature_unit": "celsius",
                "helper_flag": "debug",
            },
        )
        canonicalized = canonicalize_prediction(mutated_example, self.suite.tool_lookup, call)
        self.assertEqual(canonicalized.action.tool_id, "weather.get_current")
        self.assertEqual(
            canonicalized.action.arguments,
            {
                "city": "Shanghai",
                "temperature_unit": "celsius",
            },
        )
