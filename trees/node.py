class Node:
    """Nodo binario genérico (clave, valor, hijos)."""
    __slots__ = ("key", "value", "left", "right", "height")

    def __init__(self, key, value=None):
        self.key = key
        self.value = value
        self.left = None
        self.right = None
        self.height = 1  # solo lo usa el AVL

    def reset_counters(self):
        """Para compatibilidad con árboles que usan contadores en nodos."""
        pass
