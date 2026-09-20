import unittest
from worp_roster_scenarios import evaluate_scenario,scenario_key

ENV=dict(scoring_core_low=14,scoring_core_high=16,QB_low=2,QB_high=3,RB_low=3,RB_high=5,WR_low=4,WR_high=6,TE_low=2,TE_high=4)
SLOTS=['QB','RB','RB','WR','WR','WR','TE','FLEX','FLEX','SUPER_FLEX']+['BN']*14
CORE=dict(QB=3,RB=4,WR=5,TE=3)
EXTRA=dict(QB=2,RB=5,WR=1,TE=1)


class ScenarioTests(unittest.TestCase):
    def test_complete_accounting(self):
        r=evaluate_scenario(CORE,EXTRA,24,SLOTS,ENV)
        self.assertTrue(r['saveable']);self.assertEqual(r['core'],15);self.assertEqual(r['extra'],9)
        self.assertEqual(r['total'],dict(QB=5,RB=9,WR=6,TE=4))

    def test_under_and_over_capacity_cannot_save(self):
        for n in (23,25):
            self.assertFalse(evaluate_scenario(CORE,EXTRA,n,SLOTS,ENV)['saveable'])

    def test_flex_cannot_be_filled_by_extra_qbs(self):
        r=evaluate_scenario(dict(QB=4,RB=0,WR=0,TE=0),dict.fromkeys(CORE,0),4,['QB','FLEX','BN','BN'],ENV)
        self.assertFalse(r['can_start'])

    def test_superflex_can_be_filled_by_non_qb(self):
        r=evaluate_scenario(dict(QB=1,RB=1,WR=0,TE=0),dict.fromkeys(CORE,0),2,['QB','SUPER_FLEX'],ENV)
        self.assertTrue(r['saveable'])

    def test_small_roster_does_not_mutate_reference(self):
        before=ENV.copy();r=evaluate_scenario(dict(QB=1,RB=1,WR=1,TE=1),dict.fromkeys(CORE,0),4,['QB','RB','WR','TE'],ENV)
        self.assertTrue(r['saveable']);self.assertFalse(r['reference_fits']);self.assertEqual(before,ENV)

    def test_reference_is_comparison_not_save_approval(self):
        r=evaluate_scenario(dict(QB=4,RB=5,WR=7,TE=4),dict(QB=1,RB=1,WR=1,TE=1),24,SLOTS,ENV)
        self.assertTrue(r['saveable']);self.assertFalse(r['core_in_range'])

    def test_context_does_not_leak_across_leagues_or_settings(self):
        a=scenario_key('a',SLOTS,{},ENV,24)
        self.assertNotEqual(a,scenario_key('b',SLOTS,{},ENV,24))
        self.assertNotEqual(a,scenario_key('a',SLOTS,{'rec':1},ENV,24))

    def test_invalid_counts_and_unknown_slots(self):
        with self.assertRaises(ValueError):evaluate_scenario(dict(QB=1.5,RB=2,WR=3,TE=1),EXTRA,24,SLOTS,ENV)
        self.assertFalse(evaluate_scenario(CORE,EXTRA,24,SLOTS+['K'],ENV)['saveable'])


if __name__=='__main__':unittest.main()
