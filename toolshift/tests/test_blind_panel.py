from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from toolshift.blind_panel import summarize_blind_panel, validate_blind_panel


class BlindPanelValidationTest(unittest.TestCase):
    def test_blind_panel_summary_matches_frozen_metadata(self) -> None:
        summary = summarize_blind_panel("data/real_evolution_blind_benchmark.json")
        self.assertEqual(summary.panel_role, "blind_test")
        self.assertEqual(summary.panel_state, "frozen")
        self.assertFalse(summary.method_selection_allowed)
        self.assertEqual(summary.case_count, 24)
        self.assertEqual(summary.view_count, 48)
        self.assertEqual(summary.source_count, 42)
        self.assertEqual(
            summary.family_tags,
            ("github_rest", "gitlab_rest", "slack_auth", "trello", "youtube", "youtube_channels"),
        )
        self.assertEqual(summary.vendor_tags, ("github", "gitlab", "slack", "trello", "youtube"))
        self.assertEqual(summary.dev_family_overlap, ())

    def test_validate_blind_panel_passes_for_frozen_asset(self) -> None:
        summary = validate_blind_panel("data/real_evolution_blind_benchmark.json")
        self.assertEqual(summary.split_tags, ("unambiguous_core",))

    def test_validate_blind_panel_rejects_method_selection_flag(self) -> None:
        payload = json.loads(Path("data/real_evolution_blind_benchmark.json").read_text(encoding="utf-8"))
        payload["metadata"]["method_selection_allowed"] = True
        with tempfile.TemporaryDirectory() as tmpdir:
            benchmark_path = Path(tmpdir) / "blind.json"
            audit_path = Path(tmpdir) / "blind_audit.json"
            audit_markdown_path = Path(tmpdir) / "blind_audit.md"
            payload["metadata"]["audit_path"] = str(audit_path)
            payload["metadata"]["audit_markdown_path"] = str(audit_markdown_path)
            benchmark_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            audit_path.write_text('{"case_overrides": {}, "view_overrides": {}}\n', encoding="utf-8")
            audit_markdown_path.write_text("# tmp\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "method_selection_allowed"):
                validate_blind_panel(benchmark_path)


if __name__ == "__main__":
    unittest.main()
