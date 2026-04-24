from __future__ import annotations

import json
import unittest

from toolshift import load_seed_suite
from toolshift.panel_stability import (
    aggregate_seed_metrics,
    build_case_group_maps,
    cluster_bootstrap_metrics,
    leave_one_group_out_metrics,
)
from toolshift.reliability import eval_record_from_dict


class PanelStabilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.suite = load_seed_suite("data/real_evolution_blind_benchmark.json")
        with open("data/real_evolution_blind_benchmark.json", encoding="utf-8") as handle:
            cls.payload = json.load(handle)
        with open("artifacts/real_evolution_blind_qwen3_8b_v1/records.json", encoding="utf-8") as handle:
            record_payload = json.load(handle)
        cls.seed_records = {"seed_0": [eval_record_from_dict(record) for record in record_payload]}
        cls.group_maps = build_case_group_maps(cls.payload)

    def test_group_maps_cover_all_cases(self) -> None:
        case_ids = {case.case_id for case in self.suite.cases}
        self.assertEqual(set(self.group_maps["family"]), case_ids)
        self.assertEqual(set(self.group_maps["vendor"]), case_ids)

    def test_family_bootstrap_returns_ci_for_core_metrics(self) -> None:
        summary = cluster_bootstrap_metrics(
            self.seed_records,
            self.suite,
            case_to_group=self.group_maps["family"],
            replicates=100,
            seed=0,
        )
        self.assertIn("NOS", summary)
        self.assertIn("CAA_overall", summary)
        self.assertLessEqual(summary["NOS"]["lo"], summary["NOS"]["hi"])

    def test_leave_one_family_out_returns_each_family(self) -> None:
        summary = leave_one_group_out_metrics(
            self.seed_records,
            self.suite,
            case_to_group=self.group_maps["family"],
        )
        self.assertEqual(set(summary), {"github_rest", "gitlab_rest", "slack_auth", "trello", "youtube", "youtube_channels"})
        aggregate = aggregate_seed_metrics(self.seed_records, self.suite)
        self.assertIsNotNone(aggregate["CAA_overall"])
        self.assertTrue(all(metrics["CAA_overall"] is not None for metrics in summary.values()))


if __name__ == "__main__":
    unittest.main()
