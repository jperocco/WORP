import unittest
import numpy as np
import pandas as pd
from worp_manual_composition_comparison import prefix_tables,score,select_past,test_choice
from worp_manual_capture_test import lineup_outcomes
from worp_optionality_capacity_audit import compositions


class ManualCompositionTests(unittest.TestCase):
    def test_fast_calculation_matches_direct_lineup(self):
        holdings=[np.array([['q']]),np.array([['r1','r2']]),np.array([['w']]),np.array([['t']])]
        prediction={'q':20,'r1':15,'r2':3,'w':14,'t':5};actual={'q':.3,'r1':-.2,'r2':.5,'w':.1,'t':.2}
        legal=compositions(['QB','FLEX']);positions=['QB','RB','WR','TE']
        tables=[prefix_tables(h,prediction,actual,-.1,int(legal[:,j].max())) for j,h in enumerate(holdings)]
        expected=lineup_outcomes(holdings,prediction,actual,dict.fromkeys(positions,-.1),legal)[0]
        np.testing.assert_allclose(score((1,2,1,1),tables,legal),expected)

    def frame(self):
        return pd.DataFrame([dict(week=w,seed=s,QB=q,RB=7-q,WR=5,TE=3,capture=2 if q==3 else 1)
                             for w in (4,8) for s in (7000,17000,27000) for q in (3,4)])

    def test_future_cannot_choose_composition(self):
        d=self.frame();d.loc[d.week.eq(8),'capture']=[-100,100]*3
        self.assertEqual(select_past(d,8)['QB'],3)

    def test_infeasible_future_is_not_reselected(self):
        d=self.frame();d=d[~(d.week.eq(8)&d.QB.eq(3))]
        self.assertEqual(test_choice(d,8)['status'],'chosen_unavailable')


if __name__=='__main__':unittest.main()
