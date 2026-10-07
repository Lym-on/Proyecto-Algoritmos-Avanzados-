import unittest
import random
from workloads import (
    generate_uniform,
    generate_locality,
    generate_zipf,
    generate_sequential_asc,
    generate_sequential_desc,
    generate_sequential_zigzag,
    generate_hot_switch,
    generate_workload,
    get_workload_config,
)


class TestWorkloads(unittest.TestCase):
    """Tests for workload generators."""

    def setUp(self):
        self.ids = list(range(100))
        self.n_queries = 1000
        self.seed = 42

    def test_uniform_distribution(self):
        """Uniform: all keys should appear roughly equally."""
        queries = generate_uniform(self.ids, self.n_queries, random.Random(self.seed))
        self.assertEqual(len(queries), self.n_queries)
        # Each key should appear ~10 times (1000/100)
        from collections import Counter
        counts = Counter(queries)
        for count in counts.values():
            self.assertGreater(count, 0)
            self.assertLess(count, 30)  # generous bound

    def test_uniform_deterministic(self):
        """Same seed should produce same sequence."""
        q1 = generate_uniform(self.ids, self.n_queries, random.Random(self.seed))
        q2 = generate_uniform(self.ids, self.n_queries, random.Random(self.seed))
        self.assertEqual(q1, q2)

    def test_locality_distribution(self):
        """Locality: hot keys should appear much more often."""
        queries = generate_locality(self.ids, self.n_queries, random.Random(self.seed),
                                    hot_fraction=0.2, query_hot_fraction=0.8)
        self.assertEqual(len(queries), self.n_queries)
        
        from collections import Counter
        counts = Counter(queries)
        hot_keys = set(self.ids[80:])  # last 20%
        cold_keys = set(self.ids[:80])
        
        hot_count = sum(counts[k] for k in hot_keys)
        cold_count = sum(counts[k] for k in cold_keys)
        
        # Hot should get ~80% of queries
        self.assertGreater(hot_count, 0.6 * self.n_queries)
        self.assertLess(hot_count, 0.95 * self.n_queries)

    def test_locality_parameters(self):
        """Test custom locality parameters."""
        # 10% hot, 90% queries to hot
        queries = generate_locality(self.ids, self.n_queries, random.Random(self.seed),
                                    hot_fraction=0.1, query_hot_fraction=0.9)
        from collections import Counter
        counts = Counter(queries)
        hot_keys = set(self.ids[90:])
        hot_count = sum(counts[k] for k in hot_keys)
        self.assertGreater(hot_count, 0.8 * self.n_queries)

    def test_zipf_distribution(self):
        """Zipf: first key should be most frequent."""
        queries = generate_zipf(self.ids, self.n_queries, random.Random(self.seed), alpha=1.0)
        self.assertEqual(len(queries), self.n_queries)
        
        from collections import Counter
        counts = Counter(queries)
        # Key 0 should be most frequent (or close to it)
        max_key = max(counts, key=counts.get)
        # With Zipf, rank 1 should be most popular
        self.assertLess(max_key, 10)  # should be among top 10

    def test_zipf_alpha_variations(self):
        """Different alpha values should produce different skew."""
        q_flat = generate_zipf(self.ids, self.n_queries, random.Random(self.seed), alpha=0.5)
        q_steep = generate_zipf(self.ids, self.n_queries, random.Random(self.seed), alpha=2.0)
        
        from collections import Counter
        counts_flat = Counter(q_flat)
        counts_steep = Counter(q_steep)
        
        # Steeper alpha should concentrate more on top keys
        top5_flat = sum(counts_flat[i] for i in range(5))
        top5_steep = sum(counts_steep[i] for i in range(5))
        self.assertGreater(top5_steep, top5_flat)

    def test_sequential_asc(self):
        """Sequential ascending should cycle through keys in order."""
        queries = generate_sequential_asc(self.ids, 150, random.Random(self.seed))
        self.assertEqual(len(queries), 150)
        # Should be 0,1,2,...,99,0,1,2,...,49
        for i in range(150):
            self.assertEqual(queries[i], i % 100)

    def test_sequential_desc(self):
        """Sequential descending should cycle in reverse."""
        queries = generate_sequential_desc(self.ids, 150, random.Random(self.seed))
        self.assertEqual(len(queries), 150)
        for i in range(150):
            self.assertEqual(queries[i], 99 - (i % 100))

    def test_sequential_zigzag(self):
        """Zig-zag should alternate ends."""
        queries = generate_sequential_zigzag(self.ids, 20, random.Random(self.seed))
        # Pattern: 0, 99, 1, 98, 2, 97, ...
        expected = [0, 99, 1, 98, 2, 97, 3, 96, 4, 95, 5, 94, 6, 93, 7, 92, 8, 91, 9, 90]
        self.assertEqual(queries, expected)

    def test_hot_switch(self):
        """Hot switch should change hot set periodically."""
        queries = generate_hot_switch(self.ids, 5000, random.Random(self.seed),
                                      switch_every=1000, hot_fraction=0.1)
        self.assertEqual(len(queries), 5000)
        # Should have some variation - not all same key
        from collections import Counter
        counts = Counter(queries)
        self.assertGreater(len(counts), 1)

    def test_generate_workload_factory(self):
        """Factory function should work for all types."""
        for wtype in ['uniform', 'locality', 'zipf', 'sequential_asc', 
                      'sequential_desc', 'sequential_zigzag', 'hot_switch']:
            queries = generate_workload(wtype, self.ids, 100, self.seed)
            self.assertEqual(len(queries), 100)

    def test_generate_workload_passes_kwargs(self):
        """Factory should pass kwargs to generator."""
        q1 = generate_workload('zipf', self.ids, 100, self.seed, alpha=0.5)
        q2 = generate_workload('zipf', self.ids, 100, self.seed, alpha=2.0)
        # Different alphas should produce different distributions
        from collections import Counter
        c1 = Counter(q1)
        c2 = Counter(q2)
        top5_1 = sum(c1[i] for i in range(5))
        top5_2 = sum(c2[i] for i in range(5))
        self.assertNotEqual(top5_1, top5_2)

    def test_get_workload_config(self):
        """Config lookup should work."""
        cfg = get_workload_config('uniform')
        self.assertEqual(cfg, {})
        
        cfg = get_workload_config('zipf_1.5')
        self.assertEqual(cfg, {'workload_type': 'zipf', 'alpha': 1.5})
        
        cfg = get_workload_config('locality')
        self.assertIn('hot_fraction', cfg)

    def test_same_seed_same_sequence_all_generators(self):
        """All generators should be deterministic with same seed."""
        for gen_func in [generate_uniform, generate_locality, generate_zipf,
                         generate_sequential_asc, generate_sequential_desc,
                         generate_sequential_zigzag, generate_hot_switch]:
            q1 = gen_func(self.ids, self.n_queries, random.Random(self.seed))
            q2 = gen_func(self.ids, self.n_queries, random.Random(self.seed))
            self.assertEqual(q1, q2, f"{gen_func.__name__} not deterministic")


if __name__ == "__main__":
    unittest.main()