from .node import Node


def _h(n):
    return n.height if n else 0


def _update(n):
    n.height = 1 + max(_h(n.left), _h(n.right))


def _rot_right(y):
    x = y.left
    y.left, x.right = x.right, y
    _update(y)
    _update(x)
    return x


def _rot_left(x):
    y = x.right
    x.right, y.left = y.left, x
    _update(x)
    _update(y)
    return y


class AVL:
    """Árbol AVL: balanceo estricto en cada inserción (línea de comparación)."""

    def __init__(self):
        self.root = None
        self.comparisons = 0

    def insert(self, key, value=None):
        self.root = self._insert(self.root, key, value)

    def _insert(self, n, key, value):
        if n is None:
            return Node(key, value)
        self.comparisons += 1
        if key == n.key:
            n.value = value
            return n
        if key < n.key:
            n.left = self._insert(n.left, key, value)
        else:
            n.right = self._insert(n.right, key, value)
        _update(n)
        bal = _h(n.left) - _h(n.right)
        if bal > 1:
            if _h(n.left.left) < _h(n.left.right):
                n.left = _rot_left(n.left)
            return _rot_right(n)
        if bal < -1:
            if _h(n.right.right) < _h(n.right.left):
                n.right = _rot_right(n.right)
            return _rot_left(n)
        return n

    def search(self, key):
        cur = self.root
        while cur is not None:
            self.comparisons += 1
            if key == cur.key:
                return cur.value
            cur = cur.left if key < cur.key else cur.right
        return None

    def height(self):
        return _h(self.root)
