import unittest

import pandas as pd

from worp_league_reading_v0_9_5 import build_league_reading


def curve(rb_start=3.8, wr_start=2.8, te_start=2.6):
    rows = []
    starts = {"QB": 4.2, "RB": rb_start, "WR": wr_start, "TE": te_start}
    slopes = {"QB": .10, "RB": .09, "WR": .045, "TE": .075}
    for position in starts:
        for rank in range(1, 61):
            rows.append({
                "position": position,
                "position_rank": rank,
                "three_year_worp_avg": starts[position] - slopes[position] * (rank - 1),
            })
    return pd.DataFrame(rows)


class LeagueReadingTests(unittest.TestCase):
    def test_rb_led_structure_requires_elite_and_depth_evidence(self):
        result = build_league_reading(
            curve(), 12, 1, 2, 2, 1, 4, 1, {"bonus_rec_te": 1.0}
        )
        self.assertTrue(result["rb_led"])
        self.assertEqual(result["headline"], "RB-led shared-FLEX economy")
        self.assertGreaterEqual(result["median_rb_wr_rank_gap"], 5)
        self.assertIn("Comparable WR", result["equivalences"].columns)
        self.assertEqual(len(result["blueprint"]), 4)

    def test_balanced_curve_does_not_force_rb_build(self):
        result = build_league_reading(
            curve(rb_start=2.8, wr_start=2.9), 12, 1, 2, 2, 1, 4, 1, {}
        )
        self.assertFalse(result["rb_led"])
        self.assertIn("without a proven RB override", result["headline"])

    def test_missing_curve_columns_stop_cleanly(self):
        with self.assertRaisesRegex(ValueError, "missing columns"):
            build_league_reading(pd.DataFrame({"position": ["RB"]}), 12, 1, 2, 2, 1, 4, 1, {})


if __name__ == "__main__":
    unittest.main()
