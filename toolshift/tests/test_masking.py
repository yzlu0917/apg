from __future__ import annotations

import unittest

from toolshift import load_seed_suite
from toolshift.masking import mask_example


class MaskingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        suite = load_seed_suite("data/real_evolution_benchmark.json")
        cls.example = next(example for example in suite.examples if example.schema_view.shift_kind.value == "negative_near_orbit")

    def test_name_mask_replaces_rendered_names_only(self) -> None:
        masked = mask_example(self.example, "name_mask")
        self.assertTrue(masked.schema_view.view_id.endswith("|name_mask"))
        self.assertEqual(masked.schema_view.tools[0].rendered_name, "tool_1")
        self.assertEqual(masked.schema_view.tools[0].description, self.example.schema_view.tools[0].description)
        self.assertEqual(masked.schema_view.tools[0].arguments[0].rendered_name, "arg_1")
        self.assertEqual(masked.schema_view.tools[0].arguments[0].description, self.example.schema_view.tools[0].arguments[0].description)

    def test_description_mask_blanks_only_descriptions(self) -> None:
        masked = mask_example(self.example, "description_mask")
        self.assertEqual(masked.schema_view.tools[0].rendered_name, self.example.schema_view.tools[0].rendered_name)
        self.assertEqual(masked.schema_view.tools[0].description, "")
        self.assertEqual(masked.schema_view.tools[0].status, self.example.schema_view.tools[0].status)
        self.assertEqual(masked.schema_view.tools[0].arguments[0].description, "")

    def test_contract_mask_blanks_descriptions_and_status_cues(self) -> None:
        masked = mask_example(self.example, "contract_mask")
        self.assertEqual(masked.schema_view.tools[0].rendered_name, self.example.schema_view.tools[0].rendered_name)
        self.assertEqual(masked.schema_view.tools[0].description, "")
        self.assertEqual(masked.schema_view.tools[0].status, "active")
        self.assertEqual(masked.schema_view.tools[0].arguments[0].description, "")


if __name__ == "__main__":
    unittest.main()
