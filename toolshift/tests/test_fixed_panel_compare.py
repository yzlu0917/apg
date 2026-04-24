from __future__ import annotations

import unittest

from toolshift.fixed_panel_compare import compare_methods, flatten_method_records, summarize_method_records


class FixedPanelCompareTest(unittest.TestCase):
    def test_compare_uses_real_family_tag_and_tracks_improvements(self) -> None:
        payload = {
            "family_holdout_cv": {
                "contract_gate": {
                    "seed_0": [
                        _record(
                            case_id="case_alpha",
                            view_id="case_alpha::clean",
                            transform_name="clean",
                            shift_kind="clean",
                            admissible=True,
                            predicted_control="execute",
                            predicted_tool_id="tool.alpha",
                            expected_actions=[{"control": "execute", "tool_id": "tool.alpha", "arguments": {}}],
                        ),
                        _record(
                            case_id="case_alpha",
                            view_id="case_alpha::negative_contract",
                            transform_name="negative_contract",
                            shift_kind="negative_near_orbit",
                            admissible=False,
                            predicted_control="execute",
                            predicted_tool_id="legacy.alpha",
                            expected_actions=[{"control": "abstain", "tool_id": None, "arguments": {}}],
                        ),
                    ]
                },
                "capability_gate": {
                    "seed_0": [
                        _record(
                            case_id="case_alpha",
                            view_id="case_alpha::clean",
                            transform_name="clean",
                            shift_kind="clean",
                            admissible=True,
                            predicted_control="execute",
                            predicted_tool_id="tool.alpha",
                            expected_actions=[{"control": "execute", "tool_id": "tool.alpha", "arguments": {}}],
                        ),
                        _record(
                            case_id="case_alpha",
                            view_id="case_alpha::negative_contract",
                            transform_name="negative_contract",
                            shift_kind="negative_near_orbit",
                            admissible=True,
                            predicted_control="abstain",
                            predicted_tool_id=None,
                            expected_actions=[{"control": "abstain", "tool_id": None, "arguments": {}}],
                        ),
                    ]
                },
            }
        }
        view_metadata = {
            "case_alpha::clean": {
                "case_id": "case_alpha",
                "family_tag": "vendor_alpha",
                "primary_tool_id": "tool.alpha",
                "transform_name": "clean",
                "shift_kind": "clean",
                "split_tag": "unambiguous_core",
            },
            "case_alpha::negative_contract": {
                "case_id": "case_alpha",
                "family_tag": "vendor_alpha",
                "primary_tool_id": "tool.alpha",
                "transform_name": "negative_contract",
                "shift_kind": "negative_near_orbit",
                "split_tag": "unambiguous_core",
            },
        }

        baseline_records = flatten_method_records(
            payload,
            regime="family_holdout_cv",
            method="contract_gate",
            view_metadata=view_metadata,
        )
        candidate_records = flatten_method_records(
            payload,
            regime="family_holdout_cv",
            method="capability_gate",
            view_metadata=view_metadata,
        )

        baseline_summary = summarize_method_records(baseline_records)
        self.assertIn("vendor_alpha", baseline_summary["by_family_tag"])
        self.assertNotIn("tool.alpha", baseline_summary["by_family_tag"])

        comparison = compare_methods(baseline_records, candidate_records)
        self.assertEqual(comparison["improved_pair_count"], 1)
        self.assertEqual(comparison["regressed_pair_count"], 0)
        self.assertEqual(comparison["strictly_fixed_views"], ["case_alpha::negative_contract"])
        self.assertEqual(comparison["improvements"]["by_family_tag"], {"vendor_alpha": 1})
        self.assertEqual(comparison["improvements"]["from_bucket"], {"wrong_tool_choice": 1})


def _record(
    *,
    case_id: str,
    view_id: str,
    transform_name: str,
    shift_kind: str,
    admissible: bool,
    predicted_control: str,
    predicted_tool_id: str | None,
    expected_actions: list[dict],
) -> dict:
    return {
        "agent_name": "test",
        "case_id": case_id,
        "view_id": view_id,
        "transform_name": transform_name,
        "shift_kind": shift_kind,
        "split_tag": "unambiguous_core",
        "admissible": admissible,
        "contract_ok": True,
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


if __name__ == "__main__":
    unittest.main()
