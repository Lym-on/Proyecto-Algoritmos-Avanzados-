from .node import Node
import itertools


class KnuthDP:
    """
    Optimal BST via Knuth's Dynamic Programming.

    Given sorted keys k[0..n-1] with success frequencies p[0..n-1]
    and failure frequencies q[0..n] (q[i] = freq of search between k[i-1] and k[i]),
    computes the BST minimizing expected search cost:
        J(T) = sum(p[i] * (depth(k_i) + 1)) + sum(q[i] * (depth(e_i) + 1))

    Provides:
    - O(n^3) direct DP
    - O(n^2) Knuth optimization (requires quadrangle inequality)
    - Tree reconstruction from root table
    """

    def __init__(self, keys, p, q):
        """
        keys: list of n sorted keys
        p: list of n success probabilities (sum(p) + sum(q) = 1)
        q: list of n+1 failure probabilities
        """
        if len(keys) != len(p):
            raise ValueError("keys and p must have same length")
        if len(q) != len(p) + 1:
            raise ValueError("q must have length len(p) + 1")

        self.keys = keys
        self.p = p
        self.q = q
        self.n = len(keys)

        # Results
        self.cost = None
        self.root_table = None
        self._tree = None

    def _compute_prefix_sums(self):
        """Compute prefix sums for O(1) range sum queries."""
        # w[i][j] = sum(p[i..j]) + sum(q[i..j])
        self.w = [[0.0] * (self.n + 1) for _ in range(self.n + 1)]
        for i in range(self.n + 1):
            self.w[i][i] = self.q[i]
            for j in range(i + 1, self.n + 1):
                self.w[i][j] = self.w[i][j - 1] + self.p[j - 1] + self.q[j]

    def solve_direct(self):
        """
        Direct O(n^3) DP.

        dp[i][j] = minimum cost for keys i..j-1 (subtree with keys i..j-1)
        root[i][j] = optimal root index for keys i..j-1

        Recurrence:
        dp[i][j] = min_{i <= r < j} (dp[i][r] + dp[r+1][j]) + w[i][j]
        """
        self._compute_prefix_sums()

        dp = [[0.0] * (self.n + 1) for _ in range(self.n + 1)]
        root = [[0] * (self.n + 1) for _ in range(self.n + 1)]

        # Base case: empty trees
        for i in range(self.n + 1):
            dp[i][i] = self.q[i]
            root[i][i] = i  # dummy

        # Length 1 to n
        for length in range(1, self.n + 1):
            for i in range(self.n - length + 1):
                j = i + length
                dp[i][j] = float('inf')
                best_r = i
                for r in range(i, j):
                    cost = dp[i][r] + dp[r + 1][j] + self.w[i][j]
                    if cost < dp[i][j]:
                        dp[i][j] = cost
                        best_r = r
                root[i][j] = best_r

        self.cost = dp[0][self.n]
        self.root_table = root
        return self.cost

    def solve_knuth(self):
        """
        Knuth's O(n^2) optimization.

        Requires quadrangle inequality: w satisfies monotonicity of roots.
        For optimal BST, this holds because w is derived from probabilities.

        Optimization: root[i][j-1] <= root[i][j] <= root[i+1][j]
        So we only search r in [root[i][j-1], root[i+1][j]]
        """
        self._compute_prefix_sums()

        dp = [[0.0] * (self.n + 1) for _ in range(self.n + 1)]
        root = [[0] * (self.n + 1) for _ in range(self.n + 1)]

        for i in range(self.n + 1):
            dp[i][i] = self.q[i]
            root[i][i] = i

        for length in range(1, self.n + 1):
            for i in range(self.n - length + 1):
                j = i + length
                dp[i][j] = float('inf')

                # Knuth's optimization: search range
                r_start = root[i][j - 1] if length > 1 else i
                r_end = root[i + 1][j] if length > 1 else j - 1

                best_r = r_start
                for r in range(r_start, r_end + 1):
                    cost = dp[i][r] + dp[r + 1][j] + self.w[i][j]
                    if cost < dp[i][j]:
                        dp[i][j] = cost
                        best_r = r
                root[i][j] = best_r

        self.cost = dp[0][self.n]
        self.root_table = root
        return self.cost

    def build_tree(self):
        """Reconstruct optimal BST from root table."""
        if self.root_table is None:
            raise RuntimeError("Must call solve_direct() or solve_knuth() first")
        self._tree = self._build_recursive(0, self.n)
        return self._tree

    def _build_recursive(self, i, j):
        """Build tree for keys[i..j-1]."""
        if i >= j:
            return None
        r = self.root_table[i][j]
        node = Node(self.keys[r], r)  # value = index in original array
        node.left = self._build_recursive(i, r)
        node.right = self._build_recursive(r + 1, j)
        return node

    def get_tree(self):
        if self._tree is None:
            self.build_tree()
        return self._tree

    def expected_cost(self):
        """Return the optimal expected search cost."""
        if self.cost is None:
            self.solve_knuth()
        return self.cost

    def verify_optimal(self):
        """
        Verify against brute force for n <= 10.
        Returns (is_optimal, dp_cost, brute_cost).
        """
        if self.n > 10:
            return None, None, None

        self.solve_direct()
        dp_cost = self.cost

        # Brute force: try all possible BST shapes (Catalan number of them)
        # For small n, generate all permutations as insertion orders and pick best
        # Actually, we need to check all tree shapes. Use recursive generation.
        brute_cost = self._brute_force_optimal()

        return abs(dp_cost - brute_cost) < 1e-9, dp_cost, brute_cost

    def _brute_force_optimal(self):
        """Brute force all BST shapes for n <= 10."""
        # Generate all possible BST structures recursively
        best = float('inf')

        def build_all_trees(keys_list):
            """Yield all BST roots for given sorted keys."""
            if not keys_list:
                yield None
                return
            for i, key in enumerate(keys_list):
                for left in build_all_trees(keys_list[:i]):
                    for right in build_all_trees(keys_list[i + 1:]):
                        root = Node(key, key)
                        root.left = left
                        root.right = right
                        yield root

        def compute_cost(tree):
            total = 0.0
            # Success costs
            def dfs_success(node, depth):
                nonlocal total
                if node is None:
                    return
                idx = self.keys.index(node.key)
                total += self.p[idx] * (depth + 1)
                dfs_success(node.left, depth + 1)
                dfs_success(node.right, depth + 1)

            # Failure costs (gaps between keys)
            def dfs_failure(node, depth, key_range):
                nonlocal total
                if node is None:
                    # This gap covers key_range[0]..key_range[1] (inclusive of failure indices)
                    lo, hi = key_range
                    if lo <= hi:
                        total += sum(self.q[lo:hi + 1]) * (depth + 1)
                    return
                idx = self.keys.index(node.key)
                dfs_failure(node.left, depth + 1, (key_range[0], idx))
                dfs_failure(node.right, depth + 1, (idx + 1, key_range[1]))

            dfs_success(tree, 0)
            dfs_failure(tree, 0, (0, self.n))
            return total

        for tree in build_all_trees(self.keys):
            cost = compute_cost(tree)
            if cost < best:
                best = cost
        return best

    def print_tables(self):
        """Print DP tables for debugging."""
        if self.root_table is None:
            self.solve_knuth()
        print("Root table:")
        for i in range(self.n + 1):
            row = []
            for j in range(self.n + 1):
                if i <= j:
                    row.append(str(self.root_table[i][j]))
                else:
                    row.append(".")
            print("  ", " ".join(row))
        print(f"Optimal cost: {self.cost}")


def optimal_bst_brute_force(keys, p, q):
    """
    Brute force optimal BST for verification (n <= 8).
    Returns (best_cost, best_tree).
    """
    n = len(keys)
    best_cost = float('inf')
    best_tree = None

    def build_all(keys_list):
        if not keys_list:
            yield None
            return
        for i, key in enumerate(keys_list):
            for left in build_all(keys_list[:i]):
                for right in build_all(keys_list[i + 1:]):
                    root = Node(key, key)
                    root.left = left
                    root.right = right
                    yield root

    def cost_of(tree):
        total = 0.0
        # Success
        def dfs_s(node, d):
            nonlocal total
            if not node:
                return
            idx = keys.index(node.key)
            total += p[idx] * (d + 1)
            dfs_s(node.left, d + 1)
            dfs_s(node.right, d + 1)
        # Failure
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

    for tree in build_all(keys):
        c = cost_of(tree)
        if c < best_cost:
            best_cost = c
            best_tree = tree
    return best_cost, best_tree