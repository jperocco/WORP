import unittest
import pandas as pd
from worp_portfolio_temporal_validation import choose_training,evaluate_fold


class TemporalTests(unittest.TestCase):
    def frame(self):
        rows=[]
        for week in (4,8):
            for seed in (7000,17000,27000):
                for qb,rb in ((3,4),(4,3)):
                    rows.append(dict(week=week,seed=seed,QB=qb,RB=rb,WR=5,TE=3,
                                     mean_opportunity=1.,gap_to_window_best=0 if qb==3 else .2))
        return pd.DataFrame(rows)

    def test_future_scores_cannot_change_selection(self):
        d=self.frame();a=choose_training(d,8)
        d.loc[d.week.eq(8),'gap_to_window_best']=[10,0]*3
        b=choose_training(d,8)
        self.assertEqual(int(a.QB),int(b.QB))
        self.assertEqual(int(b.QB),3)

    def test_missing_future_supply_does_not_reselect(self):
        d=self.frame();d=d[~(d.week.eq(8)&d.QB.eq(3))]
        r=evaluate_fold(d,8)
        self.assertEqual(r['status'],'selected_composition_unavailable')
        self.assertEqual(r['QB'],3)

    def test_empty_training_is_not_prediction(self):
        self.assertIsNone(choose_training(self.frame(),4))


if __name__=='__main__':
    unittest.main()
