"""
Merkle Tree implementation for authenticated data structures.

Each node stores: hash = H(left_hash || right_hash || key || value)
Witness (authentication path) allows verification against root hash.
"""
import hashlib
import json
from typing import List, Tuple, Optional
from .node import Node


class MerkleNode:
    """Merkle tree node with hash authentication."""
    __slots__ = ("key", "value", "left", "right", "hash", "height")
    
    def __init__(self, key, value=None, left=None, right=None):
        self.key = key
        self.value = value
        self.left = left
        self.right = right
        self.hash = None
        self.height = 1
        self._recompute_hash()
    
    def _recompute_hash(self):
        """Recompute hash from children and own data."""
        left_hash = self.left.hash if self.left else "0" * 64
        right_hash = self.right.hash if self.right else "0" * 64
        
        # Only include key/value for leaf nodes
        is_leaf = self.left is None and self.right is None
        if is_leaf:
            payload = json.dumps({
                "key": self.key,
                "value": self.value,
                "left": left_hash,
                "right": right_hash
            }, sort_keys=True)
        else:
            # Internal node: only child hashes
            payload = json.dumps({
                "left": left_hash,
                "right": right_hash
            }, sort_keys=True)
        self.hash = hashlib.sha256(payload.encode()).hexdigest()
        
        # Update height
        lh = self.left.height if self.left else 0
        rh = self.right.height if self.right else 0
        self.height = 1 + max(lh, rh)
    
    def update_hash(self):
        """Public method to recompute hash (call after child changes)."""
        self._recompute_hash()
        return self.hash


def compute_merkle_root(node: Optional[MerkleNode]) -> str:
    """Get root hash of Merkle tree."""
    return node.hash if node else "0" * 64


def generate_witness(root: MerkleNode, key) -> List[Tuple[str, str, str]]:
    """
    Generate authentication path (witness) for a key.
    
    Returns list of (sibling_hash, direction, parent_hash) tuples
    from leaf to root. Direction: 'L' if sibling is left child, 'R' if right.
    """
    if root is None:
        return []
    
    path = []
    node = root
    
    while node is not None:
        if key == node.key:
            # Found the key - path complete
            break
        elif key < node.key:
            # Go left, record right sibling
            if node.right:
                path.append((node.right.hash, 'R', node.hash))
            node = node.left
        else:
            # Go right, record left sibling
            if node.left:
                path.append((node.left.hash, 'L', node.hash))
            node = node.right
    
    return path


def verify_witness(key, value, witness: List[Tuple[str, str, str]], root_hash: str) -> bool:
    """
    Verify a key-value pair against root hash using witness.
    
    Witness: list of (sibling_hash, direction, parent_hash) from ROOT to LEAF.
    Must match MerkleNode hash format exactly.
    """
    import hashlib, json
    
    # Compute leaf hash exactly like MerkleNode (leaf format includes key/value)
    leaf_payload = json.dumps({
        "key": key,
        "value": value,
        "left": "0" * 64,
        "right": "0" * 64
    }, sort_keys=True)
    current_hash = hashlib.sha256(leaf_payload.encode()).hexdigest()
    
    # Walk up the witness - process in REVERSE order (leaf to root)
    for sibling_hash, direction, _ in reversed(witness):
        if direction == 'L':
            # Sibling is left child - we are right child
            payload = json.dumps({
                "left": sibling_hash,
                "right": current_hash
            }, sort_keys=True)
        else:
            # Sibling is right child - we are left child
            payload = json.dumps({
                "left": current_hash,
                "right": sibling_hash
            }, sort_keys=True)
        current_hash = hashlib.sha256(payload.encode()).hexdigest()
    
    return current_hash == root_hash


class MerkleTree:
    """Merkle tree with BST ordering and authentication."""
    
    def __init__(self):
        self.root = None
        self.rehashes = 0
    
    def reset_counters(self):
        self.rehashes = 0
    
    def _insert_recursive(self, node: Optional[MerkleNode], key, value) -> MerkleNode:
        """Insert and update hashes on path."""
        if node is None:
            return MerkleNode(key, value)
        
        if key == node.key:
            node.value = value
        elif key < node.key:
            node.left = self._insert_recursive(node.left, key, value)
        else:
            node.right = self._insert_recursive(node.right, key, value)
        
        # Recompute hash after child change
        node.update_hash()
        self.rehashes += 1
        return node
    
    def insert(self, key, value=None):
        self.root = self._insert_recursive(self.root, key, value)
    
    def search(self, key):
        node = self.root
        while node is not None:
            if key == node.key:
                return node.value
            node = node.left if key < node.key else node.right
        return None
    
    def get_root_hash(self) -> str:
        return compute_merkle_root(self.root)
    
    def get_witness(self, key) -> List[Tuple[str, str, str]]:
        return generate_witness(self.root, key)
    
    def verify(self, key, value, witness: List[Tuple[str, str, str]]) -> bool:
        return verify_witness(key, value, witness, self.get_root_hash())
    
    def height(self) -> int:
        return self.root.height if self.root else 0
    
    def rotate_right(self, y: MerkleNode) -> MerkleNode:
        """Right rotation with hash updates."""
        x = y.left
        y.left = x.right
        x.right = y
        
        # Update hashes bottom-up
        y.update_hash()
        x.update_hash()
        self.rehashes += 2
        return x
    
    def rotate_left(self, x: MerkleNode) -> MerkleNode:
        """Left rotation with hash updates."""
        y = x.right
        x.right = y.left
        y.left = x
        
        x.update_hash()
        y.update_hash()
        self.rehashes += 2
        return y


def build_merkle_from_sorted(items: List[Tuple]) -> MerkleNode:
    """Build balanced Merkle tree from sorted (key, value) pairs."""
    if not items:
        return None
    mid = len(items) // 2
    key, value = items[mid]
    node = MerkleNode(key, value)
    node.left = build_merkle_from_sorted(items[:mid])
    node.right = build_merkle_from_sorted(items[mid+1:])
    node.update_hash()
    return node