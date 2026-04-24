from __future__ import annotations

import unittest

from toolshift.diagnostics import classify_serialized_record, summarize_serialized_records


def _record(
    *,
    admissible: bool,
    predicted_control: str,
    expected_actions: list[dict],
    predicted_tool_id: str | None = None,
    contract_ok: bool = True,
) -> dict:
    return {
        "agent_name": "test",
        "case_id": "case_1",
        "view_id": "case_1::clean",
        "transform_name": "clean",
        "shift_kind": "clean",
        "split_tag": "unambiguous_core",
        "admissible": admissible,
        "contract_ok": contract_ok,
        "confidence": 1.0,
        "predicted_action": {
            "control": predicted_control,
            "tool_id": predicted_tool_id,
            "arguments": {},
        },
        "expected_actions": expected_actions,
        "errors": [],
        "raw_call": {
            "control": predicted_control,
            "rendered_tool_name": None,
            "arguments": {},
            "confidence": 1.0,
            "metadata": {},
        },
    }


class DiagnosticsTest(unittest.TestCase):
    def test_classify_missed_execute(self) -> None:
        record = _record(
            admissible=False,
            predicted_control="ask_clarification",
            expected_actions=[{"control": "execute", "tool_id": "calendar.schedule", "arguments": {}}],
        )
        diagnosis = classify_serialized_record(record)
        self.assertEqual(diagnosis["bucket"], "missed_execute_ask_clarification")
        self.assertEqual(diagnosis["group"], "control_policy_error")

    def test_classify_wrong_non_execute_policy(self) -> None:
        record = _record(
            admissible=False,
            predicted_control="ask_clarification",
            expected_actions=[{"control": "abstain", "tool_id": None, "arguments": {}}],
        )
        diagnosis = classify_serialized_record(record)
        self.assertEqual(diagnosis["bucket"], "wrong_non_execute_policy")
        self.assertEqual(diagnosis["group"], "control_policy_error")

    def test_classify_wrong_tool_choice(self) -> None:
        record = _record(
            admissible=False,
            predicted_control="execute",
            predicted_tool_id="finance.convert_currency",
            expected_actions=[{"control": "execute", "tool_id": "weather.get_current", "arguments": {}}],
        )
        diagnosis = classify_serialized_record(record)
        self.assertEqual(diagnosis["bucket"], "wrong_tool_choice")
        self.assertEqual(diagnosis["group"], "tool_choice_error")

    def test_classify_argument_grounding_error(self) -> None:
        record = _record(
            admissible=False,
            predicted_control="execute",
            predicted_tool_id="weather.get_current",
            expected_actions=[{"control": "execute", "tool_id": "weather.get_current", "arguments": {"city": "Tokyo"}}],
        )
        diagnosis = classify_serialized_record(record)
        self.assertEqual(diagnosis["bucket"], "argument_grounding_error")
        self.assertEqual(diagnosis["group"], "argument_or_contract_error")

    def test_classify_invalid_execute_contract(self) -> None:
        record = _record(
            admissible=False,
            predicted_control="execute",
            predicted_tool_id="weather.get_current",
            expected_actions=[{"control": "execute", "tool_id": "weather.get_current", "arguments": {"city": "Tokyo"}}],
            contract_ok=False,
        )
        diagnosis = classify_serialized_record(record)
        self.assertEqual(diagnosis["bucket"], "invalid_execute_contract")
        self.assertEqual(diagnosis["group"], "argument_or_contract_error")

    def test_summarize_serialized_records_tracks_execute_rate(self) -> None:
        records = [
            _record(
                admissible=False,
                predicted_control="ask_clarification",
                expected_actions=[{"control": "execute", "tool_id": "calendar.schedule", "arguments": {}}],
            ),
            _record(
                admissible=True,
                predicted_control="abstain",
                expected_actions=[{"control": "abstain", "tool_id": None, "arguments": {}}],
            ),
        ]
        summary = summarize_serialized_records(records, case_to_family={"case_1": "calendar.schedule"})
        self.assertEqual(summary["count"], 2)
        self.assertEqual(summary["execute_rate"], 0.0)
        self.assertEqual(summary["expected_execute_count"], 1)
        self.assertEqual(summary["group_counts"]["control_policy_error"], 1)
        self.assertEqual(summary["group_counts"]["correct"], 1)
        self.assertIn("calendar.schedule", summary["by_family"])


if __name__ == "__main__":
    unittest.main()
