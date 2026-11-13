import unittest
import numpy as np
from worp_positional_portfolio_simulation import portfolio_counts, profile_orders, contribution, evaluate
from worp_optionality_capacity_audit import compositions


class PortfolioTests(unittest.TestCase):
    def test_counts_fill_capacity_and_respect_supply(self):
        rows=portfolio_counts(5,['QB','RB','FLEX'],[2,3,2,1])
        self.assertTrue(rows)
        self.assertTrue(all(sum(x)==5 and x[0]>=1 and x[1]>=1 and x[3]<=1 for x in rows))

    def test_nested_profiles_are_distinct_and_ranked_on_prior_data(self):
        prior=[{'a':4,'b':3,'c':2,'d':1}]
        x=profile_orders(set('abcd'),prior,2,2,20,np.random.default_rng(7))
        self.assertTrue(all(row[0] in 'ab' and row[1] in 'cd' for row in x))

    def test_joint_flex_has_only_one_winner(self):
        selected=[np.array([['q']]),np.array([['r']]),np.array([['w']]),np.array([['t']])]
        scores={'q':.4,'r':.3,'w':.2,'t':.1}
        legal=compositions(['QB','FLEX'])
        tables=[contribution(selected[j],scores,int(legal[:,j].max())) for j in range(4)]
        np.testing.assert_allclose(evaluate((1,1,1,1),tables,legal),[.7])

    def test_bench_addition_cannot_reduce_opportunity(self):
        table=contribution(np.array([['a','b']]),{'a':.1,'b':.3},1)
        self.assertGreaterEqual(table[2,0,1],table[1,0,1])


if __name__ == '__main__':
    unittest.main()
