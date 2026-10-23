"""Link-cut tree (Sleator & Tarjan) con raíz fija, sin evert.

Representa un bosque de árboles con raíz. Cada camino "preferido" se guarda en
un splay tree; los enlaces entre caminos son punteros al padre que no son hijos.

Operaciones (amortizado O(log n)):
  add(id, peso), link(hijo, padre), cut(hijo), connected(u, v),
  find_root(u), lca(u, v), path_sum(u), depth(u)
"""


class LNode:
    __slots__ = ("id", "left", "right", "parent", "val", "sum", "size")

    def __init__(self, id_, val=1):
        self.id = id_
        self.left = self.right = self.parent = None
        self.val = self.sum = val
        self.size = 1


def _is_root(x):
    """x es raíz de su splay tree auxiliar (su padre es solo un path-parent)."""
    p = x.parent
    return p is None or (p.left is not x and p.right is not x)


def _update(x):
    x.sum = x.val
    x.size = 1
    if x.left:
        x.sum += x.left.sum
        x.size += x.left.size
    if x.right:
        x.sum += x.right.sum
        x.size += x.right.size


class LinkCutTree:
    def __init__(self):
        self.nodes = {}
        self.rotations = 0

    def reset_counters(self):
        self.rotations = 0

    # ---------- splay interno ----------
    def _rotate(self, x):
        self.rotations += 1
        p = x.parent
        g = p.parent
        if not _is_root(p):
            if g.left is p:
                g.left = x
            else:
                g.right = x
        x.parent = g
        if p.left is x:
            p.left = x.right
            if x.right:
                x.right.parent = p
            x.right = p
        else:
            p.right = x.left
            if x.left:
                x.left.parent = p
            x.left = p
        p.parent = x
        _update(p)
        _update(x)

    def _splay(self, x):
        while not _is_root(x):
            p = x.parent
            if not _is_root(p):
                g = p.parent
                # zig-zig si x y p son hijos del mismo lado; si no, zig-zag
                self._rotate(p if (g.left is p) == (p.left is x) else x)
            self._rotate(x)

    def _access(self, x):
        """Deja el camino raíz->x como un solo camino preferido, con x en la
        raíz de su splay. Devuelve el último nodo de unión (sirve para LCA)."""
        last, y = None, x
        while y:
            self._splay(y)
            y.right = last
            _update(y)
            last, y = y, y.parent
        self._splay(x)
        return last

    # ---------- API ----------
    def add(self, id_, weight=1):
        if id_ in self.nodes:
            raise ValueError(f"nodo duplicado: {id_!r}")
        self.nodes[id_] = LNode(id_, weight)

    def _get(self, id_):
        try:
            return self.nodes[id_]
        except KeyError:
            raise KeyError(f"nodo inexistente: {id_!r}") from None

    def find_root(self, u):
        x = self._get(u)
        self._access(x)
        while x.left:
            x = x.left
        self._splay(x)
        return x.id

    def connected(self, u, v):
        return self.find_root(u) == self.find_root(v)

    def link(self, child, parent):
        """Hace de `parent` el padre de `child`. child debe ser raíz de su árbol."""
        c, p = self._get(child), self._get(parent)
        self._access(c)
        if c.left is not None:
            raise ValueError(f"{child!r} no es raíz de su árbol; haga cut primero")
        if self.find_root(parent) == child:
            raise ValueError("link crearía un ciclo")
        c.parent = p

    def cut(self, child):
        """Separa `child` de su padre (si es raíz, no hace nada)."""
        c = self._get(child)
        self._access(c)
        if c.left:
            c.left.parent = None
            c.left = None
            _update(c)

    def lca(self, u, v):
        """Ancestro común más bajo; None si están en árboles distintos."""
        a, b = self._get(u), self._get(v)
        if self.find_root(u) != self.find_root(v):
            return None
        self._access(a)
        return self._access(b).id

    def path_sum(self, u):
        """Suma de pesos del camino raíz -> u (inclusive)."""
        x = self._get(u)
        self._access(x)
        return x.sum

    def depth(self, u):
        """Número de aristas de la raíz a u."""
        x = self._get(u)
        self._access(x)
        return x.size - 1