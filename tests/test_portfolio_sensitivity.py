import unittest
import pandas as pd
from worp_portfolio_sensitivity import summarize


class SensitivityTests(unittest.TestCase):
    def test_identical_windows_deduplicate_and_missing_support_excludes(self):
        base=dict(capacity=15,QB=3,RB=3,WR=6,TE=3,seed=7,mean_opportunity=1.)
        rows=[dict(base,week=4,effective_lookback=3,gap_to_window_best=.1)]*3
        rows.append(dict(base,week=8,effective_lookback=5,gap_to_window_best=.2))
        rows.append(dict(base,QB=4,RB=2,week=4,effective_lookback=3,gap_to_window_best=0.))
        surface,shortlist=summarize(pd.DataFrame(rows))
        self.assertEqual(shortlist.QB.tolist(),[3])
        self.assertEqual(shortlist.cases.tolist(),[2])
        self.assertAlmostEqual(shortlist.iloc[0].worst_gap,.2)


if __name__=='__main__':
    unittest.main()
