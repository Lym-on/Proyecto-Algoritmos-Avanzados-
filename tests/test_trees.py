import random
import unittest

from blockchain import build_chain
from trees import AVL, BST, SplayTree


class TestTrees(unittest.TestCase):
    def check(self, cls):
        rng = random.Random(1)
        keys = rng.sample(range(10_000), 500)
        t = cls()
        for k in keys:
            t.insert(k, k * 2)
        for k in keys:
            self.assertEqual(t.search(k), k * 2)
        self.assertIsNone(t.search(-1))

    def test_bst(self):
        self.check(BST)

    def test_avl(self):
        self.check(AVL)

    def test_splay(self):
        self.check(SplayTree)

    def test_avl_balanced_on_sorted_input(self):
        t = AVL()
        for k in range(1024):
            t.insert(k)
        self.assertLessEqual(t.height(), 12)

    def test_splay_moves_key_to_root(self):
        t = SplayTree()
        for k in range(100):
            t.insert(k)
        t.search(42)
        self.assertEqual(t.root.key, 42)


class TestBlockchain(unittest.TestCase):
    def test_valid_and_tamper(self):
        bc = build_chain(n_blocks=5, tx_per_block=3, seed=1)
        self.assertTrue(bc.is_valid())
        bc.chain[2].transactions[0]["amount"] += 1
        self.assertFalse(bc.is_valid())

    def test_reproducible_transactions(self):
        a = build_chain(3, 3, seed=7)
        b = build_chain(3, 3, seed=7)
        self.assertEqual(
            [t["id"] for blk in a.chain for t in blk.transactions],
            [t["id"] for blk in b.chain for t in blk.transactions],
        )


if __name__ == "__main__":
    unittest.main()
