from .node import Node
from .splay import SplayTree


class SplaySimple(SplayTree):
    """Splay simple (top-down) SIN rotación zig-zig: baja un nivel por paso.

    Solo enlaza nodos en los árboles auxiliares, sin rotar. Cuenta 1 comparación
    por nivel (SplayTree cuenta hasta 2). Hereda insert, search y height.
    Sin zig-zig se pierde la garantía amortizada O(log n).
    """

    def _splay(self, key):
        if self.root is None:
            return
        header = Node(None)
        l = r = header
        t = self.root
        while True:
            self.comparisons += 1
            if key < t.key:
                if t.left is None:
                    break
                r.left = t
                r = t
                t = t.left
            elif key > t.key:
                if t.right is None:
                    break
                l.right = t
                l = t
                t = t.right
            else:
                break
        l.right, r.left = t.left, t.right
        t.left, t.right = header.right, header.left
        self.root = t