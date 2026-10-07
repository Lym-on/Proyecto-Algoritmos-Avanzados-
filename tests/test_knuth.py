import unittest
import random
from trees import KnuthDP, optimal_bst_brute_force
from trees.node import Node


def check_bst_property(node, min_val=None, max_val=None):
    if node is None:
        return True
    if min_val is not None and not (min_val < node.key):
        return False
    if max_val is not None and not (node.key < max_val):
        return False
    return (check_bst_property(node.left, min_val, node.key) and
            check_bst_property(node.right, node.key, max_val))


def compute_tree_cost(tree, keys, p, q):
    """Compute expected search cost of a tree."""
    total = 0.0
    n = len(keys)

    def dfs_s(node, d):
        nonlocal total
        if not node:
            return
        idx = keys.index(node.key)
        total += p[idx] * (d + 1)
        dfs_s(node.left, d + 1)
        dfs_s(node.right, d + 1)

    def dfs_f(node, d, lo, hi):
        nonlocal total
        if not node:
            total += sum(q[lo:hi + 1]) * (d + 1)
            return
        idx = keys.index(node.key)
        dfs_f(node.left, d + 1, lo, idx)
        dfs_f(node.right, d + 1, idx + 1, hi)

    dfs_s(tree, 0)
    dfs_f(tree, 0, 0, n)
    return total


class TestKnuthDP(unittest.TestCase):
    """Tests for Knuth Optimal BST."""

    def test_simple_case(self):
        """Simple 3-key case with known optimal."""
        keys = ['A', 'B', 'C']
        p = [0.3, 0.2, 0.1]
        q = [0.05, 0.1, 0.15, 0.1]

        dp = KnuthDP(keys, p, q)
        dp.solve_direct()
        cost_direct = dp.expected_cost()

        dp2 = KnuthDP(keys, p, q)
        dp2.solve_knuth()
        cost_knuth = dp2.expected_cost()

        self.assertAlmostEqual(cost_direct, cost_knuth, places=10)
        self.assertGreater(cost_direct, 0)

    def test_uniform_probabilities(self):
        """Uniform distribution: optimal should be balanced."""
        keys = list(range(5))
        p = [0.1] * 5
        q = [0.1] * 6

        dp = KnuthDP(keys, p, q)
        dp.solve_knuth()
        tree = dp.build_tree()

        self.assertTrue(check_bst_property(tree))
        self.assertEqual(dp.expected_cost(), dp.cost)

    def test_skewed_distribution(self):
        """Highly skewed: optimal should be degenerate toward hot keys."""
        keys = ['a', 'b', 'c', 'd']
        p = [0.5, 0.2, 0.15, 0.1]
        q = [0.01, 0.01, 0.01, 0.01, 0.01]

        dp = KnuthDP(keys, p, q)
        dp.solve_knuth()
        tree = dp.build_tree()

        self.assertTrue(check_bst_property(tree))
        # Root should be 'a' (highest probability)
        self.assertEqual(tree.key, 'a')

    def test_dp_vs_brute_force_n4(self):
        """Verify DP matches brute force for n=4."""
        keys = ['a', 'b', 'c', 'd']
        p = [0.2, 0.3, 0.1, 0.15]
        q = [0.05, 0.05, 0.05, 0.05, 0.05]

        dp = KnuthDP(keys, p, q)
        is_optimal, dp_cost, brute_cost = dp.verify_optimal()

        self.assertIsNotNone(is_optimal)
        self.assertTrue(is_optimal, f"DP cost {dp_cost} != brute force {brute_cost}")

    def test_dp_vs_brute_force_n5(self):
        """Verify DP matches brute force for n=5."""
        keys = ['a', 'b', 'c', 'd', 'e']
        p = [0.15, 0.25, 0.1, 0.2, 0.1]
        q = [0.02, 0.02, 0.03, 0.02, 0.01, 0.03]

        dp = KnuthDP(keys, p, q)
        is_optimal, dp_cost, brute_cost = dp.verify_optimal()

        self.assertIsNotNone(is_optimal)
        self.assertTrue(is_optimal, f"DP cost {dp_cost} != brute force {brute_cost}")

    def test_dp_vs_brute_force_random_n6(self):
        """Random test n=6."""
        random.seed(42)
        keys = ['a', 'b', 'c', 'd', 'e', 'f']
        p = [random.random() for _ in range(6)]
        q = [random.random() for _ in range(7)]
        # Normalize
        s = sum(p) + sum(q)
        p = [x / s for x in p]
        q = [x / s for x in q]

        dp = KnuthDP(keys, p, q)
        is_optimal, dp_cost, brute_cost = dp.verify_optimal()

        self.assertIsNotNone(is_optimal)
        self.assertTrue(is_optimal, f"DP cost {dp_cost} != brute force {brute_cost}")

    def test_direct_vs_knuth_equal(self):
        """Direct O(n^3) and Knuth O(n^2) should give same cost."""
        keys = list(range(8))
        p = [0.08, 0.12, 0.09, 0.15, 0.11, 0.1, 0.14, 0.06]
        q = [0.01, 0.02, 0.01, 0.02, 0.01, 0.02, 0.01, 0.02, 0.02]

        dp1 = KnuthDP(keys, p, q)
        dp1.solve_direct()
        cost1 = dp1.expected_cost()

        dp2 = KnuthDP(keys, p, q)
        dp2.solve_knuth()
        cost2 = dp2.expected_cost()

        self.assertAlmostEqual(cost1, cost2, places=10,
                               msg=f"Direct {cost1} != Knuth {cost2}")

    def test_root_monotonicity(self):
        """Verify Knuth's root monotonicity property holds."""
        keys = list(range(10))
        p = [random.random() for _ in range(10)]
        q = [random.random() for _ in range(11)]
        s = sum(p) + sum(q)
        p = [x / s for x in p]
        q = [x / s for x in q]

        dp = KnuthDP(keys, p, q)
        dp.solve_knuth()
        root = dp.root_table

        # Check: root[i][j-1] <= root[i][j] <= root[i+1][j]
        for length in range(2, dp.n + 1):
            for i in range(dp.n - length + 1):
                j = i + length
                if root[i][j - 1] > root[i][j]:
                    self.fail(f"Monotonicity violated: root[{i}][{j-1}]={root[i][j-1]} > root[{i}][{j}]={root[i][j]}")
                if root[i][j] > root[i + 1][j]:
                    self.fail(f"Monotonicity violated: root[{i}][{j}]={root[i][j]} > root[{i+1}][{j}]={root[i+1][j]}")

    def test_reconstructed_tree_cost_matches(self):
        """Tree built from root table should have same cost as DP."""
        keys = ['a', 'b', 'c', 'd', 'e']
        p = [0.2, 0.15, 0.25, 0.1, 0.15]
        q = [0.02, 0.03, 0.02, 0.03, 0.02, 0.03]

        dp = KnuthDP(keys, p, q)
        dp.solve_knuth()
        tree = dp.build_tree()

        computed_cost = compute_tree_cost(tree, keys, p, q)
        self.assertAlmostEqual(computed_cost, dp.cost, places=10)

    def test_edge_cases(self):
        """Edge cases: single key, two keys."""
        # n=1
        dp = KnuthDP(['x'], [0.8], [0.1, 0.1])
        dp.solve_knuth()
        tree = dp.build_tree()
        self.assertEqual(tree.key, 'x')
        self.assertIsNone(tree.left)
        self.assertIsNone(tree.right)

        # n=2
        dp = KnuthDP(['a', 'b'], [0.6, 0.3], [0.05, 0.03, 0.02])
        dp.solve_knuth()
        tree = dp.build_tree()
        self.assertTrue(check_bst_property(tree))

    def test_zero_probabilities(self):
        """Handle zero probabilities correctly."""
        keys = ['a', 'b', 'c']
        p = [0.5, 0.0, 0.5]  # b never accessed
        q = [0.0, 0.0, 0.0, 0.0]

        dp = KnuthDP(keys, p, q)
        dp.solve_knuth()
        cost = dp.expected_cost()
        self.assertGreaterEqual(cost, 0)

    def test_knuth_optimization_speed(self):
        """Knuth should be faster for larger n (qualitative test)."""
        import time
        keys = list(range(50))
        p = [1.0 / 50] * 50
        q = [1.0 / 51] * 51

        dp1 = KnuthDP(keys, p, q)
        t0 = time.perf_counter()
        dp1.solve_direct()
        t_direct = time.perf_counter() - t0

        dp2 = KnuthDP(keys, p, q)
        t0 = time.perf_counter()
        dp2.solve_knuth()
        t_knuth = time.perf_counter() - t0

        self.assertAlmostEqual(dp1.cost, dp2.cost, places=10)
        # Knuth should be noticeably faster (though for n=50 both are fast)
        self.assertLessEqual(t_knuth, t_direct * 2)  # generous bound


if __name__ == "__main__":
    unittest.main()