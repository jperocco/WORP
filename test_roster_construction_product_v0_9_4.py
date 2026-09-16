import unittest

import pandas as pd

from worp_roster_construction_product_v0_9_4 import (
    recover_v0_32_ranges,
    roster_construction_envelope,
    whole_roster_layers,
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


def sloped_curve():
    rows = []
    # Deliberately different marginal economics: QB and TE retain value deeper
    # than RB, while WR has a broad middle. This lets the test verify that the
    # V0.24 gate excludes legal but economically poor allocations.
    slopes = {"QB": 0.018, "RB": 0.045, "WR": 0.025, "TE": 0.020}
    starts = {"QB": 1.30, "RB": 1.55, "WR": 1.45, "TE": 1.20}
    for position in ("QB", "RB", "WR", "TE"):
        for rank in range(1, 121):
            value = starts[position] - slopes[position] * (rank - 1)
            rows.append({
                "position": position,
                "position_rank": rank,
                "three_year_worp_avg": value,
            })
    return pd.DataFrame(rows)


class RosterConstructionProductTests(unittest.TestCase):
    def test_header_only_v0_32_recovers_from_local_v0_24(self):
        header_only = pd.DataFrame(columns=["format_key", "scoring_core_low"])
        v24 = pd.DataFrame([
            {
                "format_key": "12T SF Start10 QB1 RB2 WR3 TE1 FLEX2 SFLEX1 TEP",
                "scoring_total": 14,
                "QB_low_050": 2, "QB_high_050": 3,
                "RB_low_050": 3, "RB_high_050": 5,
                "WR_low_050": 4, "WR_high_050": 6,
                "TE_low_050": 2, "TE_high_050": 3,
            },
            {
                "format_key": "12T SF Start10 QB1 RB2 WR3 TE1 FLEX2 SFLEX1 TEP",
                "scoring_total": 15,
                "QB_low_050": 2, "QB_high_050": 4,
                "RB_low_050": 3, "RB_high_050": 5,
                "WR_low_050": 5, "WR_high_050": 7,
                "TE_low_050": 2, "TE_high_050": 3,
            },
        ])
        recovered = recover_v0_32_ranges(header_only, v24)
        self.assertEqual(len(recovered), 1)
        row = recovered.iloc[0]
        self.assertEqual((row.scoring_core_low, row.scoring_core_high), (14, 15))
        self.assertEqual((row.WR_low, row.WR_high), (4, 7))

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

    def test_superflex_and_two_te_change_the_envelope(self):
        league_curve = curve({"QB": 42, "RB": 66, "WR": 90, "TE": 48})
        one_qb = roster_construction_envelope(
            league_curve, None, 12, 1, 2, 3, 1, 3, 0, 26
        )
        superflex = roster_construction_envelope(
            league_curve, None, 12, 1, 2, 3, 1, 2, 1, 26
        )
        two_te = roster_construction_envelope(
            league_curve, None, 12, 1, 2, 3, 2, 1, 1, 26
        )
        self.assertGreaterEqual(superflex["QB_high"], one_qb["QB_high"])
        self.assertGreaterEqual(two_te["TE_low"], superflex["TE_low"])
        self.assertNotEqual(
            (one_qb["QB_low"], one_qb["QB_high"], one_qb["TE_low"]),
            (two_te["QB_low"], two_te["QB_high"], two_te["TE_low"]),
        )

    def test_v0_24_gate_excludes_economically_bad_legal_extremes(self):
        result = roster_construction_envelope(
            sloped_curve(), None, 12, 1, 2, 2, 2, 3, 1, 28, tep=True
        )
        # The ungated legal surface is QB1–4 / RB2–6 / WR2–6 / TE2–6.
        # A decision-equivalent result must remove at least one legal extreme.
        gated = (
            result["QB_low"], result["QB_high"], result["RB_low"], result["RB_high"],
            result["WR_low"], result["WR_high"], result["TE_low"], result["TE_high"],
        )
        self.assertNotEqual(gated, (1, 4, 2, 6, 2, 6, 2, 6))
        self.assertEqual(
            result["decision_equivalence"], "V0.24_ABS_050_PROTECTION_090"
        )

    def test_bench_size_changes_optionality_not_scoring_core(self):
        envelope = {"scoring_core_low": 14, "scoring_core_high": 16}
        five_bench = whole_roster_layers(envelope, active_roster_size=16, superflex=1)
        twelve_bench = whole_roster_layers(envelope, active_roster_size=23, superflex=1)
        self.assertEqual((five_bench["optionality_low"], five_bench["optionality_high"]), (0, 2))
        self.assertEqual((twelve_bench["optionality_low"], twelve_bench["optionality_high"]), (7, 9))
        self.assertEqual(five_bench["primary_optionality"], ("QB", "RB"))

    def test_one_qb_moves_qb_to_secondary_optionality(self):
        envelope = {"scoring_core_low": 11, "scoring_core_high": 13}
        layers = whole_roster_layers(envelope, active_roster_size=20, superflex=0)
        self.assertEqual(layers["primary_optionality"], ("RB",))
        self.assertEqual(layers["secondary_optionality"], ("QB",))
        self.assertEqual(layers["deprioritized_optionality"], ("WR",))
        self.assertEqual(layers["unresolved_optionality"], ("TE",))


if __name__ == "__main__":
    unittest.main()
