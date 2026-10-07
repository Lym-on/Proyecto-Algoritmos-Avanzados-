from .node import Node


def _rotate_right(t):
    """Rotación simple a la derecha: t se convierte en hijo derecho de su izquierdo."""
    y = t.left
    t.left, y.right = y.right, t
    return y


def _rotate_left(t):
    """Rotación simple a la izquierda: t se convierte en hijo izquierdo de su derecho."""
    y = t.right
    t.right, y.left = y.left, t
    return y


class SplayTree:
    """Splay tree (top-down con nodo cabecera, Sleator & Tarjan).

    Cada acceso (búsqueda o inserción) lleva la clave accedida a la raíz.
    Costo amortizado O(log n) por operación.
    """

    def __init__(self):
        self.root = None
        self.comparisons = 0
        self.rotations = 0
        self.rehashes = 0

    def reset_counters(self):
        self.comparisons = 0
        self.rotations = 0
        self.rehashes = 0

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
                self.comparisons += 1
                if key < t.left.key:  # zig-zig: rotar en t (abuelo)
                    t = _rotate_right(t)
                    self.rotations += 1
                    if t.left is None:
                        break
                # zig: mover t a árbol derecho
                r.left = t
                r = t
                t = t.left
            elif key > t.key:
                if t.right is None:
                    break
                self.comparisons += 1
                if key > t.right.key:  # zag-zag: rotar en t (abuelo)
                    t = _rotate_left(t)
                    self.rotations += 1
                    if t.right is None:
                        break
                # zag: mover t a árbol izquierdo
                l.right = t
                l = t
                t = t.right
            else:
                break
        # Reensamblar
        l.right, r.left = t.left, t.right
        t.left, t.right = header.right, header.left
        self.root = t

    def insert(self, key, value=None):
        if self.root is None:
            self.root = Node(key, value)
            return
        self._splay(key)
        if key == self.root.key:
            self.root.value = value
            return
        n = Node(key, value)
        if key < self.root.key:
            n.left, n.right = self.root.left, self.root
            self.root.left = None
        else:
            n.right, n.left = self.root.right, self.root
            self.root.right = None
        self.root = n

    def search(self, key):
        if self.root is None:
            return None
        self._splay(key)
        return self.root.value if self.root.key == key else None

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
