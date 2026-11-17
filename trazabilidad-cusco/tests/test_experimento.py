import unittest

import benchmark
from cadena import ARBOLES
from generador import (PATRONES, ORDENES, generar_cadena, generar_consultas, nombres_lotes)


class TestGenerador(unittest.TestCase):
    def test_misma_semilla_mismo_resultado(self):
        for orden in ORDENES:
            a, _, ref_a = generar_cadena(50, 3, semilla=9, orden=orden)
            b, _, ref_b = generar_cadena(50, 3, semilla=9, orden=orden)
            self.assertEqual(ref_a, ref_b)
            self.assertEqual([x.datos for x in a.bloques], [x.datos for x in b.bloques])

    def test_semillas_distintas_ordenes_distintos(self):
        _, _, r1 = generar_cadena(50, 3, semilla=1)
        _, _, r2 = generar_cadena(50, 3, semilla=2)
        self.assertNotEqual(r1, r2)

    def test_consultas_reproducibles_y_validas(self):
        lotes = nombres_lotes(200)
        for patron in PATRONES:
            with self.subTest(patron=patron):
                a = generar_consultas(lotes, patron, 500, semilla=4)
                b = generar_consultas(lotes, patron, 500, semilla=4)
                self.assertEqual(a, b)
                self.assertEqual(len(a), 500)
                self.assertTrue(set(a) <= set(lotes))

    def test_patrones_son_sesgados(self):
        lotes = nombres_lotes(500)
        distintos = {p: len(set(generar_consultas(lotes, p, 5000, 1))) for p in PATRONES}
        self.assertGreater(distintos["uniforme"], distintos["80_20"])
        self.assertGreater(distintos["uniforme"], distintos["zipf"])
        self.assertLess(distintos["rafaga"], 700)

    def test_cadena_generada_es_valida_y_completa(self):
        c, lotes, ref = generar_cadena(30, 3, semilla=0)
        self.assertTrue(c.es_valida())
        self.assertEqual(len(c.bloques), 90)
        self.assertEqual(set(ref), set(lotes))

    def test_todos_los_arboles_coinciden_con_la_referencia(self):
        c, lotes, ref = generar_cadena(80, 3, semilla=3, orden="ordenado")
        for tipo in ARBOLES:
            idx = c.reconstruir_indice(tipo)
            for l in lotes:
                self.assertEqual(idx.search(l), ref[l])


class TestBenchmark(unittest.TestCase):
    def test_piloto_pequeno_correcto_y_reproducible(self):
        original = benchmark.CONFIG["piloto"]
        benchmark.CONFIG["piloto"] = {"tamanos": [30], "repeticiones": 2, "consultas": 300}
        try:
            filas = benchmark.ejecutar("piloto", verbose=False)
            self.assertEqual(benchmark.verificar(filas), [])
            self.assertEqual(len(filas), 1 * len(ORDENES) * 2 * len(PATRONES) * len(ARBOLES))
            repetido = benchmark.ejecutar("piloto", verbose=False)
            self.assertEqual(benchmark.huella(filas), benchmark.huella(repetido))
        finally:
            benchmark.CONFIG["piloto"] = original


if __name__ == "__main__":
    unittest.main()
