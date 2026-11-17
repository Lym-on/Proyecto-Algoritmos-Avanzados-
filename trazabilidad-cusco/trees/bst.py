from .node import Node


class BST:
    """Árbol binario de búsqueda simple (línea base, sin balanceo)."""

    def __init__(self):
        self.root = None
        self.comparisons = 0

    def insert(self, key, value=None):
        if self.root is None:
            self.root = Node(key, value)
            return
        cur = self.root
        while True:
            self.comparisons += 1
            if key == cur.key:
                cur.value = value
                return
            side = "left" if key < cur.key else "right"
            nxt = getattr(cur, side)
            if nxt is None:
                setattr(cur, side, Node(key, value))
                return
            cur = nxt

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
