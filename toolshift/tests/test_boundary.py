from __future__ import annotations

import unittest

from toolshift import load_seed_suite
from toolshift.boundary import build_impossible_shadow_examples
from toolshift.schema import ShiftKind


class BoundaryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.suite = load_seed_suite("data/real_evolution_benchmark.json")

    def test_impossible_shadows_cover_each_negative_case(self) -> None:
        negatives = [
            example
            for example in self.suite.examples
            if example.schema_view.shift_kind == ShiftKind.NEGATIVE_NEAR_ORBIT
        ]
        shadows = build_impossible_shadow_examples(self.suite)
        self.assertEqual(len(shadows), len(negatives))

    def test_impossible_shadow_uses_clean_surface_and_negative_action(self) -> None:
        target = next(
            example
            for example in self.suite.examples
            if example.schema_view.view_id == "notion_create_page_in_database::negative_parent_scope_change"
        )
        clean = next(
            example
            for example in self.suite.examples
            if example.schema_view.view_id == "notion_create_page_in_database::clean"
        )
        shadow = next(
            example
            for example in build_impossible_shadow_examples(self.suite)
            if example.case.case_id == target.case.case_id and example.schema_view.transform_name.endswith(target.schema_view.transform_name)
        )
        self.assertEqual(shadow.schema_view.shift_kind, ShiftKind.IMPOSSIBLE)
        self.assertEqual(
            [tool.rendered_name for tool in shadow.schema_view.tools],
            [tool.rendered_name for tool in clean.schema_view.tools],
        )
        self.assertEqual(shadow.admissible_actions, target.admissible_actions)
        self.assertIn("Impossible shadow", shadow.notes)


if __name__ == "__main__":
    unittest.main()
