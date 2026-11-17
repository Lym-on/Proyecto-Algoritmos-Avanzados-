import math
import random
import unittest

from trees import BST, AVL, SplayTree

ARBOLES = [BST, AVL, SplayTree]
SEMILLAS = [1, 2, 3, 42, 2026]


def inorden(raiz):
    salida, pila, actual = [], [], raiz
    while pila or actual:
        while actual:
            pila.append(actual)
            actual = actual.left
        actual = pila.pop()
        salida.append(actual.key)
        actual = actual.right
    return salida


class TestArboles(unittest.TestCase):
    def test_arbol_vacio(self):
        for clase in ARBOLES:
            with self.subTest(arbol=clase.__name__):
                t = clase()
                self.assertIsNone(t.search("x"))
                self.assertEqual(t.height(), 0)

    def test_un_elemento(self):
        for clase in ARBOLES:
            with self.subTest(arbol=clase.__name__):
                t = clase()
                t.insert("a", 1)
                self.assertEqual(t.search("a"), 1)
                self.assertIsNone(t.search("b"))
                self.assertEqual(t.height(), 1)

    def test_clave_duplicada_actualiza_valor(self):
        for clase in ARBOLES:
            with self.subTest(arbol=clase.__name__):
                t = clase()
                t.insert("a", 1)
                t.insert("a", 2)
                self.assertEqual(t.search("a"), 2)
                self.assertEqual(inorden(t.root), ["a"])

    def test_aleatorio_contra_diccionario_de_referencia(self):
        for clase in ARBOLES:
            for semilla in SEMILLAS:
                with self.subTest(arbol=clase.__name__, semilla=semilla):
                    rng = random.Random(semilla)
                    t, ref = clase(), {}
                    for _ in range(400):
                        k = f"K{rng.randrange(150):04d}"      # fuerza claves repetidas
                        t.insert(k, k + "!")
                        ref[k] = k + "!"
                    for k in list(ref) + ["K9999", "ZZZ", ""]:
                        self.assertEqual(t.search(k), ref.get(k))
                    self.assertEqual(inorden(t.root), sorted(ref))

    def test_busquedas_intercaladas_con_inserciones(self):
        for clase in ARBOLES:
            with self.subTest(arbol=clase.__name__):
                rng = random.Random(7)
                t, ref = clase(), {}
                for _ in range(600):
                    k = rng.randrange(80)
                    if rng.random() < 0.5:
                        t.insert(k, -k)
                        ref[k] = -k
                    else:
                        self.assertEqual(t.search(k), ref.get(k))

    def test_insercion_ordenada_grande(self):
        for clase in ARBOLES:
            with self.subTest(arbol=clase.__name__):
                t = clase()
                for i in range(2000):
                    t.insert(i, i)
                self.assertEqual(t.search(1999), 1999)
                self.assertEqual(inorden(t.root), list(range(2000)))

    def test_bst_degenera_con_orden_creciente(self):
        t = BST()
        for i in range(500):
            t.insert(i)
        self.assertEqual(t.height(), 500)

    def test_avl_respeta_cota_de_altura(self):
        for semilla in SEMILLAS:
            rng = random.Random(semilla)
            t = AVL()
            claves = list(range(1000))
            rng.shuffle(claves)
            for k in claves:
                t.insert(k)
            self.assertLessEqual(t.height(), 1.4405 * math.log2(1000 + 2))
        t = AVL()
        for i in range(1000):
            t.insert(i)                       # peor caso para un BST
        self.assertLessEqual(t.height(), 1.4405 * math.log2(1002))

    def test_splay_lleva_lo_accedido_a_la_raiz(self):
        rng = random.Random(5)
        t = SplayTree()
        claves = list(range(200))
        rng.shuffle(claves)
        for k in claves:
            t.insert(k, k)
            self.assertEqual(t.root.key, k)   # lo insertado queda en la raíz
        for k in rng.sample(claves, 50):
            t.search(k)
            self.assertEqual(t.root.key, k)   # lo buscado queda en la raíz

    def test_splay_acceso_repetido_cuesta_una_comparacion(self):
        t = SplayTree()
        for i in range(1000):
            t.insert(i)
        t.search(500)
        t.comparisons = 0
        t.search(500)
        self.assertEqual(t.comparisons, 1)

    def test_contador_de_comparaciones(self):
        for clase in ARBOLES:
            with self.subTest(arbol=clase.__name__):
                t = clase()
                for i in range(10):
                    t.insert(i)
                t.comparisons = 0
                t.search(5)
                self.assertGreater(t.comparisons, 0)


if __name__ == "__main__":
    unittest.main()
