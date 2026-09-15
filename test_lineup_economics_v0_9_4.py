import unittest

import pandas as pd

from worp_lineup_economics_v0_9_4 import build_lineup_scoring_share


class LineupEconomicsTests(unittest.TestCase):
    def setUp(self):
        rows = []
        values = {
            "QB": [30, 20, 10, 5],
            "RB": [24, 22, 18, 16, 12, 8, 4, -10],
            "WR": [26, 23, 21, 19, 17, 15, 13, 11, 9, 7],
            "TE": [14, 10, 6, 2],
        }
        for position, points in values.items():
            for rank, score in enumerate(points, start=1):
                rows.append(
                    {
                        "season": 2025,
                        "week": 1,
                        "player_id": f"{position}{rank}",
                        "position": position,
                        "fantasy_points": score,
                    }
                )
        self.weeks = pd.DataFrame(rows)

    def test_slot_points_share_and_flex_mix(self):
        result = build_lineup_scoring_share(
            self.weeks, teams=2, qb=1, rb=1, wr=1, te=1, flex=2, superflex=0
        )
        by_slot = {row["slot"]: row for row in result}

        self.assertEqual(list(by_slot), ["QB", "RB", "WR", "TE", "FLEX 1", "FLEX 2"])
        self.assertAlmostEqual(by_slot["QB"]["points_week"], 25.0)
        self.assertAlmostEqual(by_slot["FLEX 1"]["points_week"], 20.0)
        self.assertEqual(by_slot["FLEX 1"]["occupancy"], {"WR": 1.0})
        self.assertAlmostEqual(by_slot["FLEX 2"]["points_week"], 17.5)
        self.assertEqual(by_slot["FLEX 2"]["occupancy"], {"RB": 0.5, "WR": 0.5})
        self.assertAlmostEqual(sum(row["lineup_share"] for row in result), 1.0)

    def test_negative_deep_score_does_not_break_total_share(self):
        result = build_lineup_scoring_share(
            self.weeks, teams=2, qb=0, rb=4, wr=0, te=0, flex=0, superflex=0
        )
        self.assertLess(result[-1]["points_week"], 0)
        self.assertAlmostEqual(sum(row["lineup_share"] for row in result), 1.0)

    def test_superflex_uses_best_remaining_eligible_position(self):
        result = build_lineup_scoring_share(
            self.weeks, teams=2, qb=1, rb=1, wr=1, te=1, flex=0, superflex=1
        )
        superflex = result[-1]
        self.assertEqual(superflex["slot"], "SUPER_FLEX 1")
        self.assertEqual(superflex["occupancy"], {"WR": 1.0})


if __name__ == "__main__":
    unittest.main()
