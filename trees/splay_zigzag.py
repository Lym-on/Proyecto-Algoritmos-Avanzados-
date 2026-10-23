from .splay import SplayTree


class SplaySigZag(SplayTree):
    """Splay bottom-up clásico con los tres casos de rotación: zig, zig-zig y zig-zag.

    Primero desciende guardando el camino y luego sube el nodo accedido hasta la
    raíz con rotaciones explícitas (Sleator y Tarjan, 1985). Cuenta 1 comparación
    por nivel descendido y 1 rotación por cada rotación realizada.
    Hereda insert, search y height de SplayTree.
    """

    def __init__(self):
        super().__init__()
        self.rotations = 0
    def _lift(self, p, x):
        """Rota x (hijo de p) por encima de p. Devuelve x."""
        self.rotations += 1
        if p.left is x:
            p.left, x.right = x.right, p
        else:
            p.right, x.left = x.left, p
        return x

    def _splay(self, key):
        if self.root is None:
            return
        # 1) descenso: camino desde la raíz hasta la clave (o el último nodo visitado)
        path = []
        t = self.root
        while True:
            path.append(t)
            self.comparisons += 1
            if key == t.key:
                break
            nxt = t.left if key < t.key else t.right
            if nxt is None:
                break
            t = nxt
        # 2) ascenso con rotaciones
        x = path.pop()
        while path:
            p = path.pop()
            if not path:                                  # zig
                self._lift(p, x)
                break
            g = path.pop()
            if (g.left is p) == (p.left is x):            # zig-zig
                self._lift(g, p)
                self._lift(p, x)
            else:                                         # zig-zag
                self._lift(p, x)
                if g.left is p:
                    g.left = x
                else:
                    g.right = x
                self._lift(g, x)
            if path:                                      # reconectar con el bisabuelo
                gg = path[-1]
                if gg.left is g:
                    gg.left = x
                else:
                    gg.right = x
        self.root = x