import unittest
import numpy as np
from worp_manual_capture_test import lineup_outcomes


class CaptureTests(unittest.TestCase):
    def holdings(self):
        return [np.array([['q']]),np.array([['r1','r2']]),np.array([['w']]),np.array([['t']])]

    def test_future_spike_does_not_change_manual_selection(self):
        a,b,c=lineup_outcomes(self.holdings(),{'r1':20,'r2':5},{'r1':-.2,'r2':.4},dict.fromkeys(['QB','RB','WR','TE'],-.1),np.array([[0,1,0,0]]))
        np.testing.assert_allclose(a,[-.2]);np.testing.assert_allclose(b,[0]);np.testing.assert_allclose(c,[.4])

    def test_missing_stats_are_not_replacement_zero(self):
        a,_,_=lineup_outcomes(self.holdings(),{'r1':20},{'r2':.4},dict.fromkeys(['QB','RB','WR','TE'],-.3),np.array([[0,1,0,0]]))
        np.testing.assert_allclose(a,[-.3])

    def test_bench_negative_is_not_captured(self):
        a,b,c=lineup_outcomes(self.holdings(),{'r1':20},{'r1':.2,'r2':-.5},dict.fromkeys(['QB','RB','WR','TE'],-.1),np.array([[0,1,0,0]]))
        np.testing.assert_allclose(a,[.2]);np.testing.assert_allclose(b,[.2]);np.testing.assert_allclose(c,[.2])


if __name__=='__main__':
    unittest.main()
