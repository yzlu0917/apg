from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from .agents import BaseAgent
from .benchmark import ViewExample
from .schema import ControlTag, RenderedTool, ToolCall


SYSTEM_PROMPT = (
    "You are evaluating tool use under schema evolution. "
    "Decide exactly one action for the user request. "
    "If one listed function semantically satisfies the request and all required arguments can be grounded from the request, "
    "emit exactly one <tool_call> JSON block and nothing else after it. "
    "If required information is missing, or the visible contract rejects the grounded values, emit exactly one "
    "<final_decision>{\"control\":\"ask_clarification\"}</final_decision>. "
    "If the schema explicitly marks the relevant tool as deprecated or unavailable for this request, emit exactly one "
    "<final_decision>{\"control\":\"abstain\"}</final_decision>. "
    "Use the rendered function name exactly as listed in the tool schema."
)

THINK_RE = re.compile(r"<think>.*?</think>\s*", re.DOTALL)
TOOL_CALL_RE = re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.DOTALL)
FINAL_DECISION_RE = re.compile(r"<final_decision>\s*(\{.*?\})\s*</final_decision>", re.DOTALL)
JSON_BLOCK_RE = re.compile(r"(\{.*\})", re.DOTALL)


def build_qwen_tool_spec(tool: RenderedTool) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    required: list[str] = []
    for argument in tool.arguments:
        schema: dict[str, Any] = {
            "type": "string",
            "description": argument.description,
        }
        if argument.arg_type == "boolean":
            schema["type"] = "boolean"
        elif argument.arg_type == "integer":
            schema["type"] = "integer"
        elif argument.arg_type == "number":
            schema["type"] = "number"
        elif argument.arg_type == "enum":
            schema["type"] = "string"
            schema["enum"] = list(argument.enum_values)
        if argument.minimum is not None:
            schema["minimum"] = argument.minimum
        if argument.maximum is not None:
            schema["maximum"] = argument.maximum
        properties[argument.rendered_name] = schema
        if argument.required:
            required.append(argument.rendered_name)
    return {
        "type": "function",
        "function": {
            "name": tool.rendered_name,
            "description": tool.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


def parse_qwen_response(response_text: str) -> ToolCall:
    stripped = THINK_RE.sub("", response_text).strip()

    tool_match = TOOL_CALL_RE.search(stripped)
    if tool_match:
        payload = _safe_json_load(tool_match.group(1))
        if isinstance(payload, dict):
            name = payload.get("name")
            arguments = _extract_arguments(payload)
            if isinstance(name, str) and isinstance(arguments, dict):
                return ToolCall(
                    control=ControlTag.EXECUTE,
                    rendered_tool_name=name,
                    arguments=arguments,
                    confidence=1.0,
                    metadata={"raw_response": response_text},
                )

    decision_match = FINAL_DECISION_RE.search(stripped)
    if decision_match:
        payload = _safe_json_load(decision_match.group(1))
        control = _extract_control(payload)
        if control is not None:
            return ToolCall(control=control, confidence=1.0, metadata={"raw_response": response_text})

    fallback_json = _safe_json_load(_extract_first_json_block(stripped))
    control = _extract_control(fallback_json)
    if control is not None:
        return ToolCall(control=control, confidence=0.5, metadata={"raw_response": response_text})
    if isinstance(fallback_json, dict):
        name = fallback_json.get("name")
        arguments = _extract_arguments(fallback_json)
        if isinstance(name, str) and isinstance(arguments, dict):
            return ToolCall(
                control=ControlTag.EXECUTE,
                rendered_tool_name=name,
                arguments=arguments,
                confidence=0.5,
                metadata={"raw_response": response_text},
            )

    lowered = stripped.lower()
    if "ask_clarification" in lowered:
        return ToolCall(control=ControlTag.ASK_CLARIFICATION, confidence=0.2, metadata={"raw_response": response_text})
    if "abstain" in lowered:
        return ToolCall(control=ControlTag.ABSTAIN, confidence=0.2, metadata={"raw_response": response_text})
    return ToolCall(control=ControlTag.ABSTAIN, confidence=0.0, metadata={"raw_response": response_text})


def _extract_first_json_block(text: str) -> str | None:
    match = JSON_BLOCK_RE.search(text)
    if not match:
        return None
    return match.group(1)


def _safe_json_load(payload: str | None) -> dict[str, Any] | None:
    if not payload:
        return None
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return None


def _extract_arguments(payload: dict[str, Any]) -> dict[str, Any]:
    arguments = payload.get("arguments")
    if isinstance(arguments, dict):
        return arguments
    parameters = payload.get("parameters")
    if isinstance(parameters, dict):
        return parameters
    return {}


def _extract_control(payload: dict[str, Any] | None) -> ControlTag | None:
    if not isinstance(payload, dict):
        return None
    control = payload.get("control")
    if not isinstance(control, str):
        return None
    try:
        return ControlTag(control)
    except ValueError:
        return None


@dataclass
class QwenPromptAgent(BaseAgent):
    model_path: str
    device_map: str = "cuda:0"
    max_new_tokens: int = 256
    enable_thinking: bool = True
    seed: int = 0

    def __init__(
        self,
        model_path: str,
        *,
        name: str = "qwen_prompt_0.6b",
        device_map: str = "cuda:0",
        max_new_tokens: int = 256,
        enable_thinking: bool = True,
        seed: int = 0,
    ) -> None:
        super().__init__(name=name)
        self.model_path = model_path
        self.device_map = device_map
        self.max_new_tokens = max_new_tokens
        self.enable_thinking = enable_thinking
        self.seed = seed
        self._model = None
        self._tokenizer = None
        self._torch = None

    def predict(self, example: ViewExample) -> ToolCall:
        model, tokenizer, torch = self._ensure_model()
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"User request:\n{example.case.request}\n\n"
                    f"Schema note:\n{example.schema_view.notes}\n\n"
                    "Return exactly one action tag."
                ),
            },
        ]
        tools = [build_qwen_tool_spec(tool) for tool in example.schema_view.tools]
        prompt = tokenizer.apply_chat_template(
            messages,
            tools=tools,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=self.enable_thinking,
        )
        inputs = tokenizer([prompt], return_tensors="pt").to(model.device)
        with torch.no_grad():
            generated = model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
            )
        new_ids = generated[0][len(inputs.input_ids[0]):]
        response_text = tokenizer.decode(new_ids, skip_special_tokens=True)
        return parse_qwen_response(response_text)

    def _ensure_model(self):
        if self._model is not None and self._tokenizer is not None and self._torch is not None:
            return self._model, self._tokenizer, self._torch
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        torch.manual_seed(self.seed)
        tokenizer = AutoTokenizer.from_pretrained(self.model_path, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            torch_dtype="auto",
            device_map=self.device_map,
            trust_remote_code=True,
        )
        self._model = model
        self._tokenizer = tokenizer
        self._torch = torch
        return model, tokenizer, torch
