from __future__ import annotations

import unittest

from toolshift.panel_review import compute_metric_deltas, lowest_family_by_metric


class PanelReviewTest(unittest.TestCase):
    def test_compute_metric_deltas_handles_missing_values(self) -> None:
        deltas = compute_metric_deltas(
            {"CAA_overall": 1.0, "NOS": None},
            {"CAA_overall": 0.9, "NOS": 0.7},
            metric_names=("CAA_overall", "NOS"),
        )
        self.assertAlmostEqual(deltas["CAA_overall"], -0.1)
        self.assertIsNone(deltas["NOS"])

    def test_lowest_family_by_metric_returns_minimum(self) -> None:
        result = lowest_family_by_metric(
            {
                "a": {"NOS": 0.5},
                "b": {"NOS": 0.0},
                "c": {"NOS": 1.0},
            },
            "NOS",
        )
        self.assertEqual(result, ("b", 0.0))

    def test_lowest_family_by_metric_supports_family_alias(self) -> None:
        result = lowest_family_by_metric(
            {
                "a": {"CAA": 0.8},
                "b": {"CAA": 0.6},
            },
            "CAA_overall",
        )
        self.assertEqual(result, ("b", 0.6))


if __name__ == "__main__":
    unittest.main()
