import unittest
from worp_active_roster_bounds import active_bounds


class BoundsTests(unittest.TestCase):
    def test_full_roster_plus_reserve_does_not_get_discarded(self):
        x = active_bounds({'a','b','c'}, {'a'}, {'a':'QB','b':'RB','c':'RB'}, 2, 1)
        self.assertEqual((x['active_min'], x['active_max']), (2,2))
        self.assertEqual((x['RB_min'], x['RB_max']), (1,1))

    def test_small_roster_does_not_prove_no_reserve(self):
        x = active_bounds({'a','b'}, {'a'}, {'a':'QB','b':'RB'}, 3, 1)
        self.assertEqual((x['active_min'], x['active_max']), (1,2))

    def test_impossible_capacity_is_flagged(self):
        with self.assertRaises(ValueError):
            active_bounds({'a','b','c'}, {'a'}, {}, 1, 1)

    def test_missing_starter_is_flagged(self):
        with self.assertRaises(ValueError):
            active_bounds({'a'}, {'b'}, {}, 1, 1)


if __name__ == '__main__':
    unittest.main()
