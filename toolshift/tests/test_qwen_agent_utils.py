from __future__ import annotations

import unittest

from toolshift import load_seed_suite
from toolshift.qwen_agent import build_qwen_tool_spec, parse_qwen_response
from toolshift.schema import ControlTag


class QwenAgentUtilsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.suite = load_seed_suite("data/seed_benchmark.json")

    def test_build_qwen_tool_spec_uses_rendered_names(self) -> None:
        example = next(item for item in self.suite.examples if item.schema_view.transform_name == "positive_rename")
        tool = example.schema_view.tools[0]
        spec = build_qwen_tool_spec(tool)
        self.assertEqual(spec["type"], "function")
        self.assertEqual(spec["function"]["name"], tool.rendered_name)
        self.assertIn("properties", spec["function"]["parameters"])

    def test_parse_tool_call_response(self) -> None:
        payload = (
            "<think>\nreasoning\n</think>\n"
            "<tool_call>\n"
            "{\"name\": \"get_current\", \"arguments\": {\"city\": \"Shanghai\", \"temperature_unit\": \"celsius\"}}\n"
            "</tool_call>"
        )
        call = parse_qwen_response(payload)
        self.assertEqual(call.control, ControlTag.EXECUTE)
        self.assertEqual(call.rendered_tool_name, "get_current")
        self.assertEqual(call.arguments["city"], "Shanghai")

    def test_parse_final_decision_response(self) -> None:
        payload = "<final_decision>{\"control\":\"ask_clarification\"}</final_decision>"
        call = parse_qwen_response(payload)
        self.assertEqual(call.control, ControlTag.ASK_CLARIFICATION)

    def test_parse_tool_call_response_with_parameters_field(self) -> None:
        payload = "{\"name\": \"get_current\", \"parameters\": {\"city\": \"Shanghai\", \"temperature_unit\": \"celsius\"}}"
        call = parse_qwen_response(payload)
        self.assertEqual(call.control, ControlTag.EXECUTE)
        self.assertEqual(call.rendered_tool_name, "get_current")
        self.assertEqual(call.arguments["temperature_unit"], "celsius")
