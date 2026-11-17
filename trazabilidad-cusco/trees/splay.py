from .node import Node


class SplayTree:
    """Splay tree (top-down, Sleator & Tarjan).

    Cada acceso (búsqueda o inserción) lleva la clave accedida a la raíz,
    así los elementos consultados con frecuencia quedan cerca de ella.
    Costo amortizado O(log n) por operación.
    """

    def __init__(self):
        self.root = None
        self.comparisons = 0

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
                if key < t.left.key:  # zig-zig
                    y = t.left
                    t.left, y.right = y.right, t
                    t = y
                    if t.left is None:
                        break
                r.left = t  # enlazar a la derecha
                r = t
                t = t.left
            elif key > t.key:
                if t.right is None:
                    break
                self.comparisons += 1
                if key > t.right.key:  # zag-zag
                    y = t.right
                    t.right, y.left = y.left, t
                    t = y
                    if t.right is None:
                        break
                l.right = t  # enlazar a la izquierda
                l = t
                t = t.right
            else:
                break
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
