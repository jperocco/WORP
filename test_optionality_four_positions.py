import unittest
import numpy as np
from worp_optionality_capacity_audit import compositions
from worp_optionality_four_positions import marginal_options


class MarginalTests(unittest.TestCase):
    def test_positive_bench_score_can_add_nothing(self):
        week = {"core": ("WR", .2), "bench": ("WR", .1)}
        np.testing.assert_allclose(marginal_options({"core"}, {"bench"}, [week], compositions(["WR"])), [0])

    def test_flex_competes_across_positions(self):
        week = {"core": ("WR", .2), "rb": ("RB", .3), "te": ("TE", .1)}
        result = marginal_options({"core"}, {"rb", "te"}, [week], compositions(["FLEX"]))
        np.testing.assert_allclose(result, [.1, 0])

    def test_holds_same_candidate_across_weeks(self):
        future = [{"a": ("RB", .4), "b": ("RB", 0)}, {"a": ("RB", 0), "b": ("RB", .4)}]
        np.testing.assert_allclose(marginal_options(set(), {"a", "b"}, future, compositions(["RB"])), [.4, .4])

    def test_qb_eligibility_changes_marginal(self):
        week = {"q1": ("QB", .4), "q2": ("QB", .2)}
        for slot, expected in (("FLEX", 0), ("SUPER_FLEX", .2)):
            np.testing.assert_allclose(marginal_options({"q1"}, {"q2"}, [week], compositions(["QB", slot])), [expected])

    def test_rejects_existing_baseline_candidate(self):
        with self.assertRaises(ValueError):
            marginal_options({"a"}, {"a"}, [], compositions(["RB"]))


if __name__ == "__main__":
    unittest.main()
