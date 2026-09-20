import json
import unittest
import numpy as np
import pandas as pd
from worp_optionality_capacity_audit import compositions
from worp_optionality_multileague import joint_values, select_leagues


class JointOptionalityTests(unittest.TestCase):
    def test_joint_slots_prevent_double_counting_qbs(self):
        outcomes={"q1":("QB",2.),"q2":("QB",1.),"r1":("RB",2.),"r2":("RB",1.)}
        result=joint_values(set(),{"q1","q2"},{"r1","r2"},[outcomes],
            compositions(["QB","RB"]),[2],64,np.random.default_rng(7))
        np.testing.assert_array_equal(result[2,2,0],2.)
        np.testing.assert_array_equal(result[2,0,2],2.)
        self.assertTrue(np.all(result[2,1,1]>=2.))

    def test_strong_core_blocks_future_option_points(self):
        future={"baseq":("QB",10.),"baser":("RB",10.),"q":("QB",2.),"r":("RB",2.)}
        result=joint_values({"baseq","baser"},{"q"},{"r"},[future],
            compositions(["QB","RB"]),[1],8,np.random.default_rng(7))
        np.testing.assert_array_equal(result[1,1,0],0.)
        np.testing.assert_array_equal(result[1,0,1],0.)

    def test_superflex_allows_second_qb(self):
        future={"baseq":("QB",10.),"q":("QB",2.),"r":("RB",1.)}
        result=joint_values({"baseq"},{"q"},{"r"},[future],
            compositions(["QB","SUPER_FLEX"]),[1],8,np.random.default_rng(7))
        np.testing.assert_array_equal(result[1,1,0],2.)
        np.testing.assert_array_equal(result[1,0,1],1.)

    def test_sampling_is_reproducible(self):
        future={"q1":("QB",2.),"q2":("QB",1.),"r1":("RB",2.),"r2":("RB",0.)}
        args=(set(),{"q1","q2"},{"r1","r2"},[future],compositions(["QB","RB"]),[2],64)
        a=joint_values(*args,np.random.default_rng(7))
        b=joint_values(*args,np.random.default_rng(7))
        for key in a:
            np.testing.assert_array_equal(a[key],b[key])

    def test_strata_do_not_mislabel_two_qb_or_include_bestball(self):
        rows=[]
        for lid,qb,bestball in (("1",1,0),("2",2,0),("3",1,1)):
            rows.append({"league_id":lid,"season":2025,"total_rosters":12,
                "roster_positions":json.dumps(["QB"]*qb+["RB","WR","TE","BN"]),
                "settings":json.dumps({"best_ball":bestball})})
        selected=select_leagues(pd.DataFrame(rows))
        self.assertEqual(selected.league_id.tolist(),["1"])


if __name__=="__main__":
    unittest.main()
