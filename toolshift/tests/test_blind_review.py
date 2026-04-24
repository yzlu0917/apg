from __future__ import annotations

import unittest

from toolshift import load_seed_suite
from toolshift.blind_review import core_training_examples, primary_family_groups, summarize_records_by_family
from toolshift.eval import EvalRecord
from toolshift.schema import CanonicalAction, ControlTag, ShiftKind, SplitTag, ToolCall


class BlindReviewHelpersTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dev_suite = load_seed_suite("data/real_evolution_benchmark.json")
        cls.blind_suite = load_seed_suite("data/real_evolution_blind_benchmark.json")

    def test_core_training_examples_omit_impossible(self) -> None:
        examples = core_training_examples(self.dev_suite)
        self.assertTrue(examples)
        self.assertTrue(all(example.split_tag == SplitTag.UNAMBIGUOUS_CORE for example in examples))
        self.assertTrue(all(example.schema_view.shift_kind != ShiftKind.IMPOSSIBLE for example in examples))

    def test_primary_family_groups_match_blind_freeze_metadata(self) -> None:
        groups = primary_family_groups(self.blind_suite)
        self.assertEqual(
            tuple(sorted(groups)),
            ("github_rest", "gitlab_rest", "slack_auth", "trello", "youtube", "youtube_channels"),
        )

    def test_summarize_records_by_family_groups_case_records(self) -> None:
        example = next(example for example in self.blind_suite.examples if example.case.family_tag == "trello")
        record = EvalRecord(
            agent_name="dummy",
            case_id=example.case.case_id,
            view_id=example.schema_view.view_id,
            transform_name=example.schema_view.transform_name,
            shift_kind=example.schema_view.shift_kind,
            split_tag=example.split_tag.value,
            admissible=True,
            contract_ok=True,
            confidence=1.0,
            predicted_action=CanonicalAction(control=ControlTag.ABSTAIN),
            expected_actions=(CanonicalAction(control=ControlTag.ABSTAIN),),
            errors=(),
            raw_call=ToolCall(control=ControlTag.ABSTAIN, confidence=1.0),
        )
        family_summary = summarize_records_by_family(self.blind_suite, [record])
        self.assertEqual(family_summary["trello"]["view_count"], 1)
        self.assertEqual(family_summary["trello"]["CAA"], 1.0)
        self.assertEqual(family_summary["youtube"]["view_count"], 0)


if __name__ == "__main__":
    unittest.main()
