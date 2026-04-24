from __future__ import annotations

import json
import unittest

from toolshift import load_seed_suite
from toolshift.protocol_reliability import apply_policy_variant, summarize_benchmark_protocol, summarize_protocol_records
from toolshift.reliability import eval_record_from_dict


class ProtocolReliabilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dev_suite = load_seed_suite("data/real_evolution_benchmark.json")
        cls.blind_suite = load_seed_suite("data/real_evolution_blind_benchmark.json")
        with open("data/real_evolution_benchmark.json", encoding="utf-8") as handle:
            cls.dev_payload = json.load(handle)
        with open("artifacts/real_evolution_blind_qwen3_8b_v1/records.json", encoding="utf-8") as handle:
            blind_records_payload = json.load(handle)
        cls.blind_records = [eval_record_from_dict(record) for record in blind_records_payload]

    def test_benchmark_protocol_summary_counts_multi_action_negatives(self) -> None:
        summary = summarize_benchmark_protocol(self.dev_payload)
        self.assertEqual(summary["counts"]["cases"], 36)
        self.assertEqual(summary["counts"]["views"], 72)
        self.assertEqual(summary["multi_action_negative"], 10)
        self.assertAlmostEqual(summary["multi_action_negative_fraction"], 10 / 11)

    def test_single_action_only_marks_multi_action_negative_as_ambiguous(self) -> None:
        records, details = apply_policy_variant(self.blind_suite, self.blind_records, variant="single_action_only")
        summary = summarize_protocol_records(records, self.blind_suite.tool_lookup)
        self.assertEqual(details["excluded_view_count"], 10)
        self.assertEqual(summary["counts"]["ambiguous"], 10)
        self.assertEqual(summary["counts"]["core"], 38)

    def test_negative_projection_variants_relabel_dual_control_views(self) -> None:
        ask_records, ask_details = apply_policy_variant(self.blind_suite, self.blind_records, variant="ask_only_negative")
        abstain_records, abstain_details = apply_policy_variant(
            self.blind_suite,
            self.blind_records,
            variant="abstain_only_negative",
        )
        ask_summary = summarize_protocol_records(ask_records, self.blind_suite.tool_lookup)
        abstain_summary = summarize_protocol_records(abstain_records, self.blind_suite.tool_lookup)
        self.assertEqual(ask_details["relabeled_negative_view_count"], 10)
        self.assertEqual(abstain_details["relabeled_negative_view_count"], 10)
        self.assertEqual(ask_summary["counts"]["core"], 48)
        self.assertEqual(abstain_summary["counts"]["core"], 48)


if __name__ == "__main__":
    unittest.main()
