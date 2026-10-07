import unittest
from trees import SplayTree


def check_bst_property(node, min_val=float('-inf'), max_val=float('inf')):
    if node is None:
        return True
    if not (min_val < node.key < max_val):
        return False
    return (check_bst_property(node.left, min_val, node.key) and
            check_bst_property(node.right, node.key, max_val))


def get_height(node):
    if node is None:
        return 0
    return 1 + max(get_height(node.left), get_height(node.right))


class TestSplayTree(unittest.TestCase):
    """Tests exhaustivos para SplayTree."""

    def test_bst_property_after_inserts(self):
        t = SplayTree()
        for val in [10, 5, 15, 2, 7, 12, 20, 1, 3]:
            t.insert(val, val * 10)
        self.assertTrue(check_bst_property(t.root))

    def test_bst_property_after_searches(self):
        t = SplayTree()
        for val in [10, 5, 15, 2, 7, 12, 20, 1, 3]:
            t.insert(val, val * 10)
        for key in [1, 3, 7, 10, 12, 15, 20]:
            t.search(key)
            self.assertTrue(check_bst_property(t.root))

    def test_zig_zig_no_height_increase(self):
        """Zig-zig (left-left): buscar nieto izquierdo no debe aumentar altura total."""
        t = SplayTree()
        # Construir:       10
        #                /   \
        #               5     15
        #              / \
        #             2   7
        #            /
        #           1
        for val in [10, 5, 15, 2, 7, 1]:
            t.insert(val, val * 10)
        h_before = t.height()
        t.reset_counters()
        result = t.search(1)  # zig-zig en 10->5->2->1
        h_after = t.height()
        self.assertEqual(result, 10)
        self.assertEqual(t.root.key, 1)  # clave accedida sube a raíz
        self.assertLessEqual(h_after, h_before + 1, 
            f"Altura aumentó de {h_before} a {h_after} en zig-zig")

    def test_zig_zag_correct(self):
        """Zig-zag (left-right): buscar hijo derecho de hijo izquierdo."""
        t = SplayTree()
        #       10
        #      /  \
        #     5    15
        #    / \
        #   2   7
        #        \
        #         3  <- zig-zag
        for val in [10, 5, 15, 2, 7, 3]:
            t.insert(val, val * 10)
        h_before = t.height()
        t.reset_counters()
        result = t.search(3)
        h_after = t.height()
        self.assertEqual(result, 30)
        self.assertEqual(t.root.key, 3)
        self.assertLessEqual(h_after, h_before + 1)

    def test_zag_zig_correct(self):
        """Zag-zig (right-left): buscar hijo izquierdo de hijo derecho."""
        t = SplayTree()
        #       10
        #      /  \
        #     5    15
        #         /  \
        #        12  20
        #         \
        #         13  <- zag-zig
        for val in [10, 5, 15, 12, 20, 13]:
            t.insert(val, val * 10)
        h_before = t.height()
        t.reset_counters()
        result = t.search(13)
        h_after = t.height()
        self.assertEqual(result, 130)
        self.assertEqual(t.root.key, 13)
        self.assertLessEqual(h_after, h_before + 1)

    def test_zag_zag_correct(self):
        """Zag-zag (right-right): buscar nieto derecho."""
        t = SplayTree()
        #       10
        #      /  \
        #     5    15
        #           \
        #           20
        #             \
        #             25  <- zag-zag
        for val in [10, 5, 15, 20, 25]:
            t.insert(val, val * 10)
        h_before = t.height()
        t.reset_counters()
        result = t.search(25)
        h_after = t.height()
        self.assertEqual(result, 250)
        self.assertEqual(t.root.key, 25)
        self.assertLessEqual(h_after, h_before + 1)

    def test_search_moves_to_root(self):
        t = SplayTree()
        for k in range(1, 8):
            t.insert(k, k * 10)
        for k in [4, 2, 6, 1]:
            t.search(k)
            self.assertEqual(t.root.key, k)

    def test_amortized_sequence(self):
        """Secuencia 1,2,3...n: costo amortizado O(n log n), no O(n²)."""
        t = SplayTree()
        n = 100
        for k in range(1, n + 1):
            t.insert(k, k)
        total_comparisons = 0
        for k in range(1, n + 1):
            t.reset_counters()
            t.search(k)
            total_comparisons += t.comparisons
        # Costo amortizado: ~n log n comparaciones totales
        # Límite generoso: < n * 3 * log2(n)
        import math
        self.assertLess(total_comparisons, n * 3 * math.log2(n),
            f"Comparaciones totales {total_comparisons} >> n log n")

    def test_repeated_access_same_key(self):
        """Acceso repetido a la misma clave: O(1) después del primero."""
        t = SplayTree()
        for k in range(1, 11):
            t.insert(k, k * 10)
        t.search(5)
        self.assertEqual(t.root.key, 5)
        for _ in range(5):
            t.reset_counters()
            t.search(5)
            self.assertEqual(t.comparisons, 1, "Acceso repetido debe ser 1 comparación")
            self.assertEqual(t.root.key, 5)

    def test_insert_existing_key_updates_value(self):
        t = SplayTree()
        t.insert(5, 50)
        t.insert(5, 500)
        self.assertEqual(t.search(5), 500)
        self.assertEqual(t.root.key, 5)

    def test_search_nonexistent(self):
        t = SplayTree()
        for k in [10, 5, 15]:
            t.insert(k, k * 10)
        t.reset_counters()
        result = t.search(99)
        self.assertIsNone(result)
        # La clave más cercana debería haber subido a raíz
        self.assertIn(t.root.key, [10, 15])

    def test_rotations_counted(self):
        """Verificar que se cuentan rotaciones en zig-zig."""
        t = SplayTree()
        # Insertar SIN que 1 quede en raíz: insertar en orden que no haga splay de 1
        for val in [10, 5, 15, 2, 7]:
            t.insert(val, val * 10)
        # Ahora insertar 1 - esto hará zig-zig
        t.reset_counters()
        t.insert(1, 10)
        self.assertGreater(t.rotations, 0, "Debe haber al menos 1 rotación en zig-zig durante insert")

    def test_counters_reset(self):
        t = SplayTree()
        t.insert(1, 10)
        t.search(1)
        self.assertGreater(t.comparisons, 0)
        t.reset_counters()
        self.assertEqual(t.comparisons, 0)
        self.assertEqual(t.rotations, 0)
        self.assertEqual(t.rehashes, 0)

    def test_height_and_depth_metrics(self):
        t = SplayTree()
        for k in range(1, 16):
            t.insert(k, k * 10)
        self.assertEqual(t.max_depth(), t.height())
        self.assertGreater(t.avg_depth(), 0)
        pct = t.depth_percentiles()
        self.assertIn("p95", pct)
        self.assertIn("p99", pct)
        self.assertLessEqual(pct["p95"], t.height())
        self.assertLessEqual(pct["p99"], t.height())


if __name__ == "__main__":
    unittest.main()