import unittest
from trees.merkle import (
    MerkleNode, compute_merkle_root, generate_witness, 
    verify_witness, build_merkle_from_sorted, MerkleTree
)
from trees.auth_tree import AuthenticatedTree, create_authenticated_tree
from trees.avl import AVL
from trees.splay import SplayTree
from trees.bst import BST


class TestMerkle(unittest.TestCase):
    """Tests for Merkle tree authentication."""

    def test_merkle_node_hash(self):
        """Test hash computation."""
        node = MerkleNode("key1", "value1")
        self.assertEqual(len(node.hash), 64)  # SHA-256 hex
        self.assertEqual(node.height, 1)

    def test_merkle_tree_insert_search(self):
        """Test basic insert and search."""
        tree = MerkleTree()
        for k, v in [("b", 2), ("a", 1), ("c", 3)]:
            tree.insert(k, v)
        
        self.assertEqual(tree.search("a"), 1)
        self.assertEqual(tree.search("b"), 2)
        self.assertEqual(tree.search("c"), 3)
        self.assertIsNone(tree.search("d"))
        self.assertEqual(tree.height(), 2)

    def test_merkle_witness_verification(self):
        """Test witness generation and verification."""
        tree = MerkleTree()
        for k, v in [("b", 2), ("a", 1), ("c", 3), ("d", 4)]:
            tree.insert(k, v)
        
        root_hash = tree.get_root_hash()
        witness = tree.get_witness("a")
        
        # Valid witness should verify
        self.assertTrue(tree.verify("a", 1, witness))
        # Invalid value should fail
        self.assertFalse(tree.verify("a", 999, witness))
        # Invalid key should fail
        self.assertFalse(tree.verify("x", 1, witness))

    def test_merkle_rehashes_on_insert(self):
        """Test that rehashes are counted on insert."""
        tree = MerkleTree()
        tree.reset_counters()
        tree.insert("a", 1)
        initial_rehashes = tree.rehashes
        tree.insert("b", 2)
        self.assertGreater(tree.rehashes, initial_rehashes)

    def test_merkle_balanced_build(self):
        """Test building balanced tree from sorted items."""
        items = [(f"key{i}", i) for i in range(7)]
        root = build_merkle_from_sorted(items)
        
        self.assertIsNotNone(root)
        self.assertEqual(root.height, 3)  # balanced
        
        # Verify all keys present
        def check_keys(node, expected):
            if node is None:
                return
            self.assertIn(node.key, expected)
            check_keys(node.left, expected)
            check_keys(node.right, expected)
        
        check_keys(root, set(f"key{i}" for i in range(7)))

    def test_verify_witness_external(self):
        """Test verify_witness function directly."""
        tree = MerkleTree()
        for k, v in [("b", 2), ("a", 1), ("c", 3)]:
            tree.insert(k, v)
        
        root_hash = tree.get_root_hash()
        witness = tree.get_witness("a")
        
        self.assertTrue(verify_witness("a", 1, witness, root_hash))
        self.assertFalse(verify_witness("a", 2, witness, root_hash))


class TestAuthenticatedTree(unittest.TestCase):
    """Tests for AuthenticatedTree wrapper."""

    def test_avl_authenticated_build(self):
        """Test building authenticated AVL from base."""
        base = AVL()
        for k in [5, 3, 7, 1, 4, 6, 8]:
            base.insert(k, k * 10)
        
        auth = create_authenticated_tree("AVL")
        for k in [5, 3, 7, 1, 4, 6, 8]:
            auth.base_tree.insert(k, k * 10)
        auth.build_from_base()
        
        self.assertEqual(auth.height(), base.height())
        self.assertEqual(auth.search(4), 40)
        self.assertIsNotNone(auth.get_root_hash())

    def test_splay_authenticated_build(self):
        """Test building authenticated Splay from base."""
        base = SplayTree()
        for k in [5, 3, 7, 1, 4, 6, 8]:
            base.insert(k, k * 10)
        
        auth = create_authenticated_tree("Splay")
        for k in [5, 3, 7, 1, 4, 6, 8]:
            auth.base_tree.insert(k, k * 10)
        auth.build_from_base()
        
        self.assertEqual(auth.height(), base.height())
        # Splay on search
        auth.search(1)
        self.assertEqual(auth.base_tree.root.key, 1)

    def test_bst_authenticated(self):
        """Test authenticated BST."""
        auth = create_authenticated_tree("BST")
        for k in [5, 3, 7, 1, 4, 6, 8]:
            auth.base_tree.insert(k, k * 10)
        auth.build_from_base()
        
        self.assertEqual(auth.search(4), 40)
        witness = auth.get_witness(4)
        self.assertTrue(auth.verify(4, 40, witness))

    def test_rehashes_counted(self):
        """Test that rehashes are tracked."""
        auth = create_authenticated_tree("AVL")
        auth.reset_counters()
        
        for k in [5, 3, 7]:
            auth.insert(k, k * 10)
        
        # Should have rehashes from insertions
        self.assertGreater(auth.rehashes, 0)

    def test_witness_verification_after_search(self):
        """Test witness still valid after Splay search restructures."""
        auth = create_authenticated_tree("Splay")
        for k in [10, 5, 15, 2, 7, 12, 20]:
            auth.base_tree.insert(k, k * 10)
        auth.build_from_base()
        
        root_before = auth.get_root_hash()
        witness_before = auth.get_witness(2)
        
        # Search triggers splay
        auth.search(2)
        
        root_after = auth.get_root_hash()
        # Root hash should change after splay
        self.assertNotEqual(root_before, root_after)
        
        # New witness should verify against new root
        witness_after = auth.get_witness(2)
        self.assertTrue(auth.verify(2, 20, witness_after))


if __name__ == "__main__":
    unittest.main()