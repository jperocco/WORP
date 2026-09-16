import unittest

import pandas as pd

from worp_roster_construction_product_v0_9_4 import (
    roster_construction_envelope,
)


def curve(frontiers):
    rows = []
    for position, end in frontiers.items():
        for rank in range(1, end + 6):
            rows.append(
                {
                    "position": position,
                    "position_rank": rank,
                    "three_year_worp_avg": 1.0 if rank <= end else -0.1,
                }
            )
    return pd.DataFrame(rows)


class RosterConstructionProductTests(unittest.TestCase):
    def test_exact_historical_support_wins(self):
        historical = pd.DataFrame(
            [{
                "format_key": "12T SF Start10 QB1 RB2 WR3 TE1 FLEX2 SFLEX1 TEP",
                "scoring_core_low": 14, "scoring_core_high": 15,
                "QB_low": 2, "QB_high": 4, "RB_low": 3, "RB_high": 5,
                "WR_low": 4, "WR_high": 7, "TE_low": 2, "TE_high": 3,
            }]
        )
        result = roster_construction_envelope(
            curve({"QB": 36, "RB": 60, "WR": 72, "TE": 30}), historical,
            12, 1, 2, 3, 1, 2, 1, 26, tep=True,
        )
        self.assertEqual(result["source"], "EXACT_HISTORICAL_SUPPORT")
        self.assertEqual((result["scoring_core_low"], result["scoring_core_high"]), (14, 15))

    def test_unseen_format_gets_league_native_envelope(self):
        result = roster_construction_envelope(
            curve({"QB": 24, "RB": 60, "WR": 84, "TE": 36}), pd.DataFrame(),
            12, 1, 2, 3, 1, 3, 0, 26,
        )
        self.assertEqual(result["source"], "LEAGUE_NATIVE_DERIVED")
        self.assertEqual(result["confidence"], "LOWER_VALIDATION")
        self.assertEqual((result["scoring_core_low"], result["scoring_core_high"]), (13, 15))
        self.assertLessEqual(result["QB_low"], result["QB_high"])
        self.assertLessEqual(result["RB_low"], result["RB_high"])
        self.assertLessEqual(result["WR_low"], result["WR_high"])
        self.assertLessEqual(result["TE_low"], result["TE_high"])

    def test_active_roster_capacity_caps_core(self):
        result = roster_construction_envelope(
            curve({"QB": 40, "RB": 80, "WR": 100, "TE": 50}), None,
            10, 1, 2, 2, 1, 2, 0, 10,
        )
        self.assertEqual(result["scoring_core_high"], 10)
        self.assertGreaterEqual(result["scoring_core_low"], 8)


if __name__ == "__main__":
    unittest.main()

