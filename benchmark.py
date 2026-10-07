"""Compara BST, AVL, Splay Tree, Baseline y Optimal BST indexando transacciones de blockchain.

Índice: tx_id (hash) -> número de bloque.

Workloads:
  - uniform: todas las transacciones con la misma probabilidad
  - locality: fracción configurable de claves calientes reciben fracción configurable de consultas
  - zipf: distribución Zipf con alpha configurable (0.5, 1.0, 1.5, 2.0)
  - sequential_asc: acceso secuencial ascendente (adversarial para BST)
  - sequential_desc: acceso secuencial descendente
  - sequential_zigzag: patrón zig-zag
  - hot_switch: conjunto caliente que cambia periódicamente
"""
import random
import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Any

from blockchain import build_chain
from trees import AVL, BST, SplayTree, BaselineTree, KnuthDP
from trees.auth_tree import create_authenticated_tree
from trees.node import Node
from workloads import generate_workload, get_workload_config


@dataclass
class ExperimentResult:
    """Result of a single algorithm run on a workload."""
    workload: str
    n: int
    queries: int
    seed: int
    algorithm: str
    comparisons_total: int
    comparisons_avg: float
    time_total: float
    time_per_query: float
    height: int
    avg_depth: float
    max_depth: int
    p95_depth: int
    p99_depth: int
    rotations: int
    rotations_per_access: float
    rehashes: int
    rehashes_per_access: float
    cost_access: float
    cost_reorg: float
    cost_total: float
    lambda_val: float
    normalized_cost: float = 0.0  # vs optimal


class OptimalBSTWrapper:
    """Wrapper to make optimal BST compatible with tree interface."""
    
    def __init__(self, root: Node, keys: List, dp_cost: float):
        self.root = root
        self.keys = keys
        self.dp_cost = dp_cost
        self.comparisons = 0
        self.rotations = 0
        self.rehashes = 0
    
    def reset_counters(self):
        self.comparisons = 0
        self.rotations = 0
        self.rehashes = 0
    
    def search(self, key):
        cur = self.root
        while cur is not None:
            self.comparisons += 1
            if key == cur.key:
                return cur.value
            cur = cur.left if key < cur.key else cur.right
        return None
    
    def height(self):
        if self.root is None:
            return 0
        best, stack = 0, [(self.root, 1)]
        while stack:
            n, d = stack.pop()
            best = max(best, d)
            if n.left:
                stack.append((n.left, d + 1))
            if n.right:
                stack.append((n.right, d + 1))
        return best
    
    def avg_depth(self):
        if self.root is None:
            return 0.0
        total_depth = 0
        count = 0
        stack = [(self.root, 1)]
        while stack:
            n, d = stack.pop()
            total_depth += d
            count += 1
            if n.left:
                stack.append((n.left, d + 1))
            if n.right:
                stack.append((n.right, d + 1))
        return total_depth / count if count else 0.0
    
    def max_depth(self):
        return self.height()
    
    def depth_percentiles(self, p95=True, p99=True):
        if self.root is None:
            return {}
        depths = []
        stack = [(self.root, 1)]
        while stack:
            n, d = stack.pop()
            depths.append(d)
            if n.left:
                stack.append((n.left, d + 1))
            if n.right:
                stack.append((n.right, d + 1))
        depths.sort()
        n = len(depths)
        res = {}
        if p95:
            res["p95"] = depths[int(0.95 * n)] if n > 0 else 0
        if p99:
            res["p99"] = depths[int(0.99 * n)] if n > 0 else 0
        return res


def build_index(tree_cls, txs):
    t = tree_cls()
    for tx_id, block_idx in txs:
        t.insert(tx_id, block_idx)
    return t


def build_optimal_bst(txs, queries):
    """Build optimal static BST using Knuth DP for given query frequencies."""
    ids = [tx for tx, _ in txs]
    # Count query frequencies
    freq = {id_: 0 for id_ in ids}
    for q in queries:
        freq[q] = freq.get(q, 0) + 1
    
    # Sort keys and build probability arrays
    sorted_items = sorted(freq.items())
    keys = [k for k, _ in sorted_items]
    n = len(keys)
    
    # p: success probabilities, q: failure probabilities
    total = len(queries) + n + 1  # add 1 for each gap
    p = [freq[k] / total for k in keys]
    q = [1.0 / total] * (n + 1)  # uniform failure for simplicity
    
    dp = KnuthDP(keys, p, q)
    dp.solve_knuth()
    return dp, dp.build_tree(), keys


def run_algorithm(tree_cls, txs, queries, lambda_val=1.0):
    """Run a single algorithm on the workload and collect metrics."""
    tree = build_index(tree_cls, txs)
    tree.reset_counters()
    
    t0 = time.perf_counter()
    for q in queries:
        tree.search(q)
    t1 = time.perf_counter()
    
    # Collect metrics
    result = ExperimentResult(
        workload="",  # filled by caller
        n=len(txs),
        queries=len(queries),
        seed=0,  # filled by caller
        algorithm=tree_cls.__name__,
        comparisons_total=tree.comparisons,
        comparisons_avg=tree.comparisons / len(queries),
        time_total=t1 - t0,
        time_per_query=(t1 - t0) / len(queries),
        height=tree.height(),
        avg_depth=tree.avg_depth(),
        max_depth=tree.max_depth(),
        p95_depth=tree.depth_percentiles().get("p95", 0),
        p99_depth=tree.depth_percentiles().get("p99", 0),
        rotations=getattr(tree, 'rotations', 0),
        rotations_per_access=getattr(tree, 'rotations', 0) / len(queries),
        rehashes=getattr(tree, 'rehashes', 0),
        rehashes_per_access=getattr(tree, 'rehashes', 0) / len(queries),
        cost_access=tree.comparisons,
        cost_reorg=getattr(tree, 'rotations', 0) * lambda_val,
        cost_total=tree.comparisons + getattr(tree, 'rotations', 0) * lambda_val,
        lambda_val=lambda_val,
    )
    return result, tree


def run_optimal_bst(txs, queries, lambda_val=1.0):
    """Run optimal BST (Knuth DP) on the workload."""
    dp, root, keys = build_optimal_bst(txs, queries)
    tree = OptimalBSTWrapper(root, keys, dp.expected_cost())
    
    # Compute cost using the tree
    tree.reset_counters()
    for q in queries:
        tree.search(q)
    
    optimal_cost = dp.expected_cost()
    
    result = ExperimentResult(
        workload="",
        n=len(txs),
        queries=len(queries),
        seed=0,
        algorithm="OptimalBST",
        comparisons_total=tree.comparisons,
        comparisons_avg=tree.comparisons / len(queries),
        time_total=0.0,  # offline, no search time
        time_per_query=0.0,
        height=tree.height(),
        avg_depth=tree.avg_depth(),
        max_depth=tree.max_depth(),
        p95_depth=tree.depth_percentiles().get("p95", 0),
        p99_depth=tree.depth_percentiles().get("p99", 0),
        rotations=0,
        rotations_per_access=0.0,
        rehashes=0,
        rehashes_per_access=0.0,
        cost_access=tree.comparisons,  # use actual comparisons like other algorithms
        cost_reorg=0.0,
        cost_total=tree.comparisons,
        lambda_val=lambda_val,
        normalized_cost=1.0,  # baseline
    )
    return result, optimal_cost


def run_authenticated_algorithm(tree_type: str, txs, queries, lambda_val=1.0):
    """Run an authenticated algorithm and collect metrics including rehashes."""
    auth_tree = create_authenticated_tree(tree_type)
    
    # Build initial index
    for tx_id, block_idx in txs:
        auth_tree.base_tree.insert(tx_id, block_idx)
    auth_tree.build_from_base()
    auth_tree.reset_counters()
    
    t0 = time.perf_counter()
    for q in queries:
        auth_tree.search(q)
    t1 = time.perf_counter()
    
    result = ExperimentResult(
        workload="",
        n=len(txs),
        queries=len(queries),
        seed=0,
        algorithm=f"{tree_type}_Auth",
        comparisons_total=auth_tree.base_tree.comparisons,
        comparisons_avg=auth_tree.base_tree.comparisons / len(queries),
        time_total=t1 - t0,
        time_per_query=(t1 - t0) / len(queries),
        height=auth_tree.height(),
        avg_depth=auth_tree.avg_depth(),
        max_depth=auth_tree.max_depth(),
        p95_depth=auth_tree.depth_percentiles().get("p95", 0),
        p99_depth=auth_tree.depth_percentiles().get("p99", 0),
        rotations=getattr(auth_tree.base_tree, 'rotations', 0),
        rotations_per_access=getattr(auth_tree.base_tree, 'rotations', 0) / len(queries),
        rehashes=auth_tree.rehashes,
        rehashes_per_access=auth_tree.rehashes / len(queries),
        cost_access=auth_tree.base_tree.comparisons,
        cost_reorg=(getattr(auth_tree.base_tree, 'rotations', 0) + auth_tree.rehashes) * lambda_val,
        cost_total=auth_tree.base_tree.comparisons + (getattr(auth_tree.base_tree, 'rotations', 0) + auth_tree.rehashes) * lambda_val,
        lambda_val=lambda_val,
    )
    return result, auth_tree


def run_experiment(n_blocks=200, tx_per_block=10, n_queries=5000, seed=42,
                   workload="uniform", workload_params=None, lambda_val=1.0,
                   include_authenticated=False):
    """Run a single experiment configuration."""
    if workload_params is None:
        workload_params = {}
    
    bc = build_chain(n_blocks, tx_per_block, difficulty=2, seed=seed)
    txs = [(tx["id"], b.index) for b in bc.chain for tx in b.transactions]
    ids = [tx for tx, _ in txs]
    
    # Generate queries
    queries = generate_workload(workload, ids, n_queries, seed, **workload_params)
    
    print(f"Blockchain válida: {bc.is_valid()} | bloques: {len(bc.chain)} | transacciones: {len(txs)}")
    print(f"Workload: {workload} | Consultas: {n_queries} | Semilla: {seed} | λ: {lambda_val}\n")
    
    # Run all algorithms
    algorithms = [BST, AVL, SplayTree, BaselineTree]
    results = []
    
    # First run online algorithms
    for cls in algorithms:
        result, _ = run_algorithm(cls, txs, queries, lambda_val)
        result.workload = workload
        result.seed = seed
        results.append(result)
    
    # Run authenticated versions if requested
    if include_authenticated:
        auth_types = ["BST", "AVL", "Splay", "Baseline"]
        for tree_type in auth_types:
            result, _ = run_authenticated_algorithm(tree_type, txs, queries, lambda_val)
            result.workload = workload
            result.seed = seed
            results.append(result)
    
    # Run optimal BST (offline)
    opt_result, opt_cost = run_optimal_bst(txs, queries, lambda_val)
    opt_result.workload = workload
    opt_result.seed = seed
    results.append(opt_result)
    
    # Normalize costs against optimal
    opt_total_cost = opt_cost * len(queries)
    for r in results:
        if opt_total_cost > 0:
            r.normalized_cost = r.cost_total / opt_total_cost
    
    return results


def print_results(results: List[ExperimentResult]):
    """Print formatted results table."""
    header = (f"{'Workload':<15}{'Algoritmo':<14}{'Comp/cons':>10}{'Altura':>7}"
              f"{'Prof.Prom':>9}{'p99':>5}{'Rot/acc':>9}{'Rehash/acc':>11}"
              f"{'CostoAcc':>10}{'CostoReorg':>11}{'CostoTot':>10}{'Norm.Cost':>10}")
    print(header)
    print("-" * len(header))
    
    for r in results:
        print(f"{r.workload:<15}{r.algorithm:<14}{r.comparisons_avg:>10.2f}"
              f"{r.height:>7}{r.avg_depth:>9.2f}{r.p99_depth:>5}"
              f"{r.rotations_per_access:>9.3f}{r.rehashes_per_access:>11.3f}"
              f"{r.cost_access:>10.1f}{r.cost_reorg:>11.1f}{r.cost_total:>10.1f}{r.normalized_cost:>10.3f}")


def run_all_workloads(n_blocks=200, tx_per_block=10, n_queries=5000, seed=42, lambda_val=1.0):
    """Run experiment across all standard workloads."""
    workload_configs = [
        ("uniform", {}),
        ("locality", {"hot_fraction": 0.2, "query_hot_fraction": 0.8}),
        ("zipf", {"alpha": 0.5}),
        ("zipf", {"alpha": 1.0}),
        ("zipf", {"alpha": 1.5}),
        ("zipf", {"alpha": 2.0}),
        ("sequential_asc", {}),
        ("sequential_desc", {}),
        ("sequential_zigzag", {}),
        ("hot_switch", {"switch_every": 1000, "hot_fraction": 0.1}),
    ]
    
    all_results = []
    for workload, params in workload_configs:
        try:
            results = run_experiment(n_blocks, tx_per_block, n_queries, seed,
                                     workload, params, lambda_val)
            print_results(results)
            print()
            all_results.extend(results)
        except Exception as e:
            print(f"Error in {workload}: {e}\n")
    
    return all_results


def run(n_blocks=50, tx_per_block=10, n_queries=2000, seed=42, lambda_val=1.0):
    """Entry point used by `main.py` and by the script itself."""
    return run_all_workloads(
        n_blocks=n_blocks,
        tx_per_block=tx_per_block,
        n_queries=n_queries,
        seed=seed,
        lambda_val=lambda_val,
    )


if __name__ == "__main__":
    # Quick test run
    run(n_blocks=50, tx_per_block=10, n_queries=2000, seed=42)