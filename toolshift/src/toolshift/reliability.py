from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .eval import EvalRecord
from .schema import CanonicalAction, ControlTag, ShiftKind, ToolCall


def eval_record_from_dict(payload: dict[str, Any]) -> EvalRecord:
    raw_call_payload = payload.get("raw_call", {})
    return EvalRecord(
        agent_name=payload["agent_name"],
        case_id=payload["case_id"],
        view_id=payload["view_id"],
        transform_name=payload["transform_name"],
        shift_kind=ShiftKind(payload["shift_kind"]),
        split_tag=payload["split_tag"],
        admissible=bool(payload["admissible"]),
        contract_ok=bool(payload["contract_ok"]),
        confidence=float(payload.get("confidence", 0.0)),
        predicted_action=CanonicalAction.from_dict(payload["predicted_action"]),
        expected_actions=tuple(CanonicalAction.from_dict(action) for action in payload["expected_actions"]),
        errors=tuple(payload.get("errors", ())),
        raw_call=ToolCall(
            control=ControlTag(raw_call_payload.get("control", payload["predicted_action"]["control"])),
            rendered_tool_name=raw_call_payload.get("rendered_tool_name"),
            arguments=dict(raw_call_payload.get("arguments", {})),
            confidence=float(raw_call_payload.get("confidence", payload.get("confidence", 0.0))),
            metadata=dict(raw_call_payload.get("metadata", {})),
        ),
    )


def load_flat_eval_records(path: str | Path) -> list[EvalRecord]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise TypeError(f"expected flat record list in {path}, got {type(payload).__name__}")
    return [eval_record_from_dict(item) for item in payload]


def load_nested_eval_records(path: str | Path, method: str) -> dict[str, list[EvalRecord]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if method not in payload:
        raise KeyError(f"method {method} not found in {path}")
    seed_payload = payload[method]
    if not isinstance(seed_payload, dict):
        raise TypeError(f"expected nested seed payload for {method} in {path}")
    return {
        seed_name: [eval_record_from_dict(item) for item in records]
        for seed_name, records in seed_payload.items()
    }


def extract_case_sources(notes: str) -> tuple[str, ...]:
    if "sources=" not in notes:
        return ()
    source_blob = notes.split("sources=", 1)[1].split(";", 1)[0]
    return tuple(source_id.strip() for source_id in source_blob.split(",") if source_id.strip())


def case_source_summary(payload: dict[str, Any]) -> dict[str, Any]:
    sources = payload["sources"]
    per_case_source_counts: list[int] = []
    per_case_kind_counts: list[int] = []
    per_case_vendor_counts: list[int] = []
    mixed_kind_cases = 0
    mixed_vendor_cases = 0
    for case in payload["cases"]:
        source_ids = extract_case_sources(case.get("notes", ""))
        source_entries = [sources[source_id] for source_id in source_ids if source_id in sources]
        kinds = {entry["kind"] for entry in source_entries}
        vendors = {entry["vendor"] for entry in source_entries}
        per_case_source_counts.append(len(source_entries))
        per_case_kind_counts.append(len(kinds))
        per_case_vendor_counts.append(len(vendors))
        if len(kinds) >= 2:
            mixed_kind_cases += 1
        if len(vendors) >= 2:
            mixed_vendor_cases += 1
    return {
        "mean_source_count": sum(per_case_source_counts) / len(per_case_source_counts),
        "min_source_count": min(per_case_source_counts),
        "max_source_count": max(per_case_source_counts),
        "mixed_kind_cases": mixed_kind_cases,
        "mixed_vendor_cases": mixed_vendor_cases,
        "source_count_histogram": dict(Counter(per_case_source_counts)),
        "kind_count_histogram": dict(Counter(per_case_kind_counts)),
        "vendor_count_histogram": dict(Counter(per_case_vendor_counts)),
    }


def build_case_vendor_map(payload: dict[str, Any]) -> dict[str, str]:
    sources = payload["sources"]
    vendor_map: dict[str, str] = {}
    for case in payload["cases"]:
        source_ids = extract_case_sources(case.get("notes", ""))
        vendors = sorted({sources[source_id]["vendor"] for source_id in source_ids if source_id in sources})
        if not vendors:
            vendor_map[case["case_id"]] = case.get("family_tag") or "unknown"
        elif len(vendors) == 1:
            vendor_map[case["case_id"]] = vendors[0]
        else:
            vendor_map[case["case_id"]] = "+".join(vendors)
    return vendor_map


def summarize_benchmark_structure(payload: dict[str, Any]) -> dict[str, Any]:
    case_lookup = {case["case_id"]: case for case in payload["cases"]}
    action_size_histogram: Counter[int] = Counter()
    control_signature_histogram: Counter[str] = Counter()
    shift_action_histogram: Counter[str] = Counter()
    multi_action_negative = 0
    for view in payload["views"]:
        actions = view.get("admissible_actions", case_lookup[view["case_id"]]["admissible_actions"])
        action_size = len(actions)
        controls = sorted({action["control"] for action in actions})
        signature = "+".join(controls)
        shift_kind = view["schema_view"]["shift_kind"]
        action_size_histogram[action_size] += 1
        control_signature_histogram[signature] += 1
        shift_action_histogram[f"{shift_kind}:{signature}"] += 1
        if shift_kind == ShiftKind.NEGATIVE_NEAR_ORBIT.value and action_size > 1:
            multi_action_negative += 1
    family_counts = Counter(case.get("family_tag", "none") for case in payload["cases"])
    vendor_counts = Counter(build_case_vendor_map(payload).values())
    return {
        "counts": {
            "cases": len(payload["cases"]),
            "views": len(payload["views"]),
            "sources": len(payload["sources"]),
            "families": len(family_counts),
            "vendors": len(vendor_counts),
        },
        "family_counts": dict(sorted(family_counts.items())),
        "vendor_counts": dict(sorted(vendor_counts.items())),
        "action_size_histogram": dict(sorted(action_size_histogram.items())),
        "control_signature_histogram": dict(sorted(control_signature_histogram.items())),
        "shift_action_histogram": dict(sorted(shift_action_histogram.items())),
        "multi_action_negative": multi_action_negative,
        "case_source_summary": case_source_summary(payload),
    }
