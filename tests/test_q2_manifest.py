import unittest

from scripts.q2_manifest import Q2_METHODS, Q2_SEEDS, q2_conditions, q2_key, q2_workloads


class FrozenQ2ManifestTests(unittest.TestCase):
    def test_frozen_matrix_has_7680_unique_keys(self):
        workloads = q2_workloads()
        keys = [q2_key(workload) for workload in workloads]
        self.assertEqual(len(Q2_SEEDS), 3)
        self.assertEqual(len(q2_conditions()), 16)
        self.assertEqual(len(Q2_METHODS), 8)
        self.assertEqual(len(workloads), 7680)
        self.assertEqual(len(set(keys)), 7680)

    def test_location_sensitivity_adds_four_unique_conditions(self):
        conditions = q2_conditions()
        extra = [condition for condition in conditions if condition[2] != "both"]
        self.assertEqual(len(extra), 4)
        self.assertEqual(len(set(conditions)), 16)


if __name__ == "__main__":
    unittest.main(verbosity=2)
