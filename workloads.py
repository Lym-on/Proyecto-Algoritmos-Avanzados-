"""
Workload generators for benchmarking search trees.

All generators produce the same query sequence for a given seed,
allowing fair comparison between algorithms.
"""
import random
from typing import List, Callable


def generate_uniform(ids: List, n_queries: int, rng: random.Random) -> List:
    """Uniform distribution: all keys equally likely."""
    return [rng.choice(ids) for _ in range(n_queries)]


def generate_locality(ids: List, n_queries: int, rng: random.Random,
                      hot_fraction: float = 0.2, query_hot_fraction: float = 0.8) -> List:
    """
    Temporal locality: hot_fraction of keys receive query_hot_fraction of queries.
    
    By default, 20% of keys (most recent) get 80% of queries.
    """
    cut = int(len(ids) * (1 - hot_fraction))
    old, recent = ids[:cut], ids[cut:]
    return [rng.choice(recent if rng.random() < query_hot_fraction else old)
            for _ in range(n_queries)]


def generate_zipf(ids: List, n_queries: int, rng: random.Random, alpha: float = 1.0) -> List:
    """
    Zipf distribution: popularity follows 1/rank^alpha.
    
    Keys are ranked by their position in the list (first = most popular).
    alpha=1.0: classic Zipf
    alpha=0.5: flatter distribution
    alpha=1.5: more skewed
    alpha=2.0: very skewed
    """
    n = len(ids)
    weights = [1.0 / ((i + 1) ** alpha) for i in range(n)]
    total = sum(weights)
    weights = [w / total for w in weights]
    return rng.choices(ids, weights=weights, k=n_queries)


def generate_sequential_asc(ids: List, n_queries: int, rng: random.Random) -> List:
    """Sequential ascending access pattern (adversarial for BST)."""
    n = len(ids)
    return [ids[i % n] for i in range(n_queries)]


def generate_sequential_desc(ids: List, n_queries: int, rng: random.Random) -> List:
    """Sequential descending access pattern."""
    n = len(ids)
    return [ids[-(i % n) - 1] for i in range(n_queries)]


def generate_sequential_zigzag(ids: List, n_queries: int, rng: random.Random) -> List:
    """Zig-zag pattern: 0, n-1, 1, n-2, 2, n-3, ..."""
    n = len(ids)
    queries = []
    left, right = 0, n - 1
    toggle = True
    while len(queries) < n_queries:
        if toggle and left <= right:
            queries.append(ids[left])
            left += 1
        elif not toggle and left <= right:
            queries.append(ids[right])
            right -= 1
        else:
            left, right = 0, n - 1
            toggle = True
        toggle = not toggle
    return queries[:n_queries]


def generate_hot_switch(ids: List, n_queries: int, rng: random.Random,
                        switch_every: int = 1000, hot_fraction: float = 0.1) -> List:
    """
    Hot-set switches periodically.
    
    Every switch_every queries, a new random hot set is chosen.
    """
    n = len(ids)
    hot_size = max(1, int(n * hot_fraction))
    queries = []
    current_hot = rng.sample(ids, hot_size)
    remaining_in_phase = switch_every
    
    for _ in range(n_queries):
        if remaining_in_phase == 0:
            current_hot = rng.sample(ids, hot_size)
            remaining_in_phase = switch_every
        
        # 80% hot, 20% cold
        if rng.random() < 0.8:
            queries.append(rng.choice(current_hot))
        else:
            cold = [x for x in ids if x not in current_hot]
            queries.append(rng.choice(cold) if cold else rng.choice(ids))
        remaining_in_phase -= 1
    
    return queries


def generate_workload(workload_type: str, ids: List, n_queries: int, seed: int,
                      **kwargs) -> List:
    """
    Factory function to generate workload by name.
    
    Supported types:
    - 'uniform'
    - 'locality' (hot_fraction, query_hot_fraction)
    - 'zipf' (alpha)
    - 'sequential_asc'
    - 'sequential_desc'
    - 'sequential_zigzag'
    - 'hot_switch' (switch_every, hot_fraction)
    """
    rng = random.Random(seed)
    
    generators = {
        'uniform': generate_uniform,
        'locality': generate_locality,
        'zipf': generate_zipf,
        'sequential_asc': generate_sequential_asc,
        'sequential_desc': generate_sequential_desc,
        'sequential_zigzag': generate_sequential_zigzag,
        'hot_switch': generate_hot_switch,
    }
    
    if workload_type not in generators:
        raise ValueError(f"Unknown workload: {workload_type}. Available: {list(generators.keys())}")
    
    return generators[workload_type](ids, n_queries, rng, **kwargs)


# Default workload configurations for experiments
DEFAULT_WORKLOADS = {
    'uniform': {},
    'locality': {'hot_fraction': 0.2, 'query_hot_fraction': 0.8},
    'zipf_0.5': {'workload_type': 'zipf', 'alpha': 0.5},
    'zipf_1.0': {'workload_type': 'zipf', 'alpha': 1.0},
    'zipf_1.5': {'workload_type': 'zipf', 'alpha': 1.5},
    'zipf_2.0': {'workload_type': 'zipf', 'alpha': 2.0},
    'sequential_asc': {'workload_type': 'sequential_asc'},
    'sequential_desc': {'workload_type': 'sequential_desc'},
    'sequential_zigzag': {'workload_type': 'sequential_zigzag'},
    'hot_switch': {'workload_type': 'hot_switch', 'switch_every': 1000, 'hot_fraction': 0.1},
}


def get_workload_config(name: str) -> dict:
    """Get workload configuration by name."""
    if name in DEFAULT_WORKLOADS:
        return DEFAULT_WORKLOADS[name].copy()
    # Try parsing zipf_X.Y
    if name.startswith('zipf_'):
        try:
            alpha = float(name[5:])
            return {'workload_type': 'zipf', 'alpha': alpha}
        except ValueError:
            pass
    raise ValueError(f"Unknown workload config: {name}")