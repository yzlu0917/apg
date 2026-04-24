from __future__ import annotations

import unittest

from toolshift import load_seed_suite
from toolshift.official_request_smoke import (
    OFFICIAL_REQUEST_SMOKE_SPECS,
    load_benchmark_payload,
    run_official_request_smoke,
)


class OfficialRequestSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.benchmark_path = "data/real_evolution_benchmark.json"
        cls.suite = load_seed_suite(cls.benchmark_path)
        cls.payload = load_benchmark_payload(cls.benchmark_path)
        cls.doc_map = cls._build_fake_doc_map()

    @classmethod
    def _build_fake_doc_map(cls) -> dict[str, str]:
        doc_fragments: dict[str, list[str]] = {}
        sources = cls.payload["sources"]
        for spec in OFFICIAL_REQUEST_SMOKE_SPECS:
            for source_id in spec.source_ids:
                url = sources[source_id]["url"]
                doc_fragments.setdefault(url, []).extend(spec.doc_needles)
        return {url: "\n".join(fragments) for url, fragments in doc_fragments.items()}

    def _fake_fetch_text(self, url: str) -> str:
        return self.doc_map[url]

    def test_fake_docs_make_all_specs_pass(self) -> None:
        records, summary = run_official_request_smoke(
            suite=self.suite,
            benchmark_payload=self.payload,
            fetch_text=self._fake_fetch_text,
        )
        self.assertEqual(len(records), len(OFFICIAL_REQUEST_SMOKE_SPECS))
        self.assertEqual(summary["pass_rate"], 1.0)
        self.assertEqual(summary["emit_expected_pass_rate"], 1.0)
        self.assertEqual(summary["block_expected_pass_rate"], 1.0)
        self.assertEqual(summary["provider_summary"]["bitbucket"]["count"], 4)
        self.assertEqual(summary["provider_summary"]["drive"]["count"], 3)
        self.assertEqual(summary["provider_summary"]["confluence"]["count"], 4)
        self.assertEqual(summary["provider_summary"]["jira"]["count"], 4)
        self.assertEqual(summary["provider_summary"]["people"]["count"], 4)
        self.assertEqual(summary["provider_summary"]["sheets"]["count"], 4)

    def test_missing_doc_marker_fails_record(self) -> None:
        broken_docs = dict(self.doc_map)
        spec = next(
            item
            for item in OFFICIAL_REQUEST_SMOKE_SPECS
            if item.view_id == "drive_add_file_to_second_folder::negative_shortcut_replacement"
        )
        for source_id in spec.source_ids:
            broken_url = self.payload["sources"][source_id]["url"]
            broken_docs[broken_url] = "a file can only have one parent folder"
        records, summary = run_official_request_smoke(
            suite=self.suite,
            benchmark_payload=self.payload,
            fetch_text=broken_docs.__getitem__,
        )
        failing_record = next(
            record
            for record in records
            if record.view_id == "drive_add_file_to_second_folder::negative_shortcut_replacement"
        )
        self.assertFalse(failing_record.passed)
        self.assertIn("missing official doc evidence", failing_record.reason)
        self.assertLess(summary["pass_rate"], 1.0)

    def test_negative_legacy_identifier_case_stays_blocked(self) -> None:
        records, _ = run_official_request_smoke(
            suite=self.suite,
            benchmark_payload=self.payload,
            fetch_text=self._fake_fetch_text,
        )
        record = next(
            item
            for item in records
            if item.view_id == "jira_search_assignable_user_legacy_username::negative_legacy_identifier_removed"
        )
        self.assertTrue(record.passed)
        self.assertFalse(record.emitted)
        self.assertIsNone(record.request)
        self.assertIn("capability gap", record.reason)


if __name__ == "__main__":
    unittest.main()
