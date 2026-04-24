#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from toolshift.benchmark import load_seed_suite
from toolshift.eval import EvalRecord, canonicalize_prediction, summarize_records
from toolshift.schema import CanonicalAction, ControlTag, ShiftKind, ToolCall


def main() -> None:
    parser = argparse.ArgumentParser(description="Rejudge saved ToolShift records against the current benchmark and audit policy.")
    parser.add_argument("--benchmark", default="data/seed_benchmark.json")
    parser.add_argument("--records", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    suite = load_seed_suite(args.benchmark)
    examples = {example.schema_view.view_id: example for example in suite.examples}
    payload = json.loads(Path(args.records).read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        raise ValueError("Expected a flat list of records, not a dict keyed by agent.")

    records = []
    for item in payload:
        example = examples[item["view_id"]]
        raw_call = item["raw_call"]
        tool_call = ToolCall(
            control=ControlTag(raw_call["control"]),
            rendered_tool_name=raw_call.get("rendered_tool_name"),
            arguments=raw_call.get("arguments", {}),
            confidence=raw_call.get("confidence", item["confidence"]),
            metadata=raw_call.get("metadata", {}),
        )
        canonicalized = canonicalize_prediction(example, suite.tool_lookup, tool_call)
        admissible = any(
            canonicalized.action.fingerprint(suite.tool_lookup) == action.fingerprint(suite.tool_lookup)
            for action in example.admissible_actions
        )
        records.append(
            EvalRecord(
                agent_name=item["agent_name"],
                case_id=item["case_id"],
                view_id=item["view_id"],
                transform_name=item["transform_name"],
                shift_kind=ShiftKind(item["shift_kind"]),
                split_tag=example.split_tag.value,
                admissible=admissible,
                contract_ok=canonicalized.contract_ok,
                confidence=item["confidence"],
                predicted_action=canonicalized.action,
                expected_actions=example.admissible_actions,
                errors=canonicalized.errors,
                raw_call=tool_call,
            )
        )

    summary = summarize_records(records, suite.tool_lookup)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
