import unittest
import pandas as pd
from worp_engine import LeagueSettings, select_aggregate_starters
from worp_lineup_economics_v0_9_4 import build_lineup_scoring_share
from worp_league_reading_v0_9_5 import build_league_reading
from worp_roster_scenarios import evaluate_scenario


def sample_curve():
    rows = []
    starts = {"QB": 4.2, "RB": 3.8, "WR": 2.8, "TE": 2.6}
    slopes = {"QB": .10, "RB": .09, "WR": .045, "TE": .075}
    for pos, start in starts.items():
        for rank in range(1, 61):
            rows.append({"position": pos, "position_rank": rank,
                         "three_year_worp_avg": start - slopes[pos] * (rank - 1)})
    return pd.DataFrame(rows)


class RestrictedFlexEligibilityTests(unittest.TestCase):
    def test_engine_restricts_slot_to_rb_wr(self):
        week = pd.DataFrame([
            {"player_id": "TE1", "position": "TE", "fantasy_points": 100.0},
            {"player_id": "RB1", "position": "RB", "fantasy_points": 10.0},
            {"player_id": "WR1", "position": "WR", "fantasy_points": 9.0},
        ])
        settings = LeagueSettings(teams=1, qb=0, rb=0, wr=0, te=0,
                                  flex=0, superflex=0, rbwr_flex=1)
        starters = select_aggregate_starters(week, settings)
        self.assertEqual(starters["player_id"].tolist(), ["RB1"])

    def test_lineup_economics_restricts_occupancy(self):
        weeks = pd.DataFrame([
            {"season": 2025, "week": 1, "player_id": "TE1", "position": "TE", "fantasy_points": 100.0},
            {"season": 2025, "week": 1, "player_id": "RB1", "position": "RB", "fantasy_points": 20.0},
            {"season": 2025, "week": 1, "player_id": "WR1", "position": "WR", "fantasy_points": 10.0},
        ])
        rows = build_lineup_scoring_share(weeks, 1, 0, 0, 0, 0, 0, 0, 1)
        self.assertEqual(rows[0]["slot"], "WRRB_FLEX 1")
        self.assertEqual(rows[0]["occupancy"], {"RB": 1.0})

    def test_scenario_does_not_allow_te_in_restricted_slot(self):
        env = {"scoring_core_low": 1, "scoring_core_high": 3,
               "QB_low": 0, "QB_high": 2, "RB_low": 0, "RB_high": 3,
               "WR_low": 0, "WR_high": 3, "TE_low": 0, "TE_high": 3}
        result = evaluate_scenario(
            {"QB": 1, "RB": 0, "WR": 0, "TE": 1},
            {"QB": 0, "RB": 0, "WR": 0, "TE": 0},
            2, ["QB", "WRRB_FLEX"], env)
        self.assertFalse(result["can_start"])

    def test_scenario_allows_rb_in_restricted_slot(self):
        env = {"scoring_core_low": 1, "scoring_core_high": 3,
               "QB_low": 0, "QB_high": 2, "RB_low": 0, "RB_high": 3,
               "WR_low": 0, "WR_high": 3, "TE_low": 0, "TE_high": 3}
        result = evaluate_scenario(
            {"QB": 1, "RB": 1, "WR": 0, "TE": 1},
            {"QB": 0, "RB": 0, "WR": 0, "TE": 0},
            3, ["QB", "WRRB_FLEX", "BN"], env)
        self.assertTrue(result["saveable"])

    def test_league_reading_counts_restricted_slots(self):
        result = build_league_reading(sample_curve(), 12, 1, 2, 2, 1, 1, 1, {},
                                      rbwr_flex=4)
        self.assertEqual(result["start_n"], 12)
        self.assertIn("RB/WR", result["headline"])


if __name__ == "__main__":
    unittest.main()
