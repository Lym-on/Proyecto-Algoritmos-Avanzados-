import unittest

from cadena import Cadena, Bloque
from trees import BST, AVL, SplayTree


def crear(tipo="splay", dificultad=1):
    c = Cadena(dificultad=dificultad, tipo_arbol=tipo)
    c.registrar("CAFE-1", "Cosecha", {"lugar": "Quillabamba"})
    c.registrar("PAPA-1", "Cosecha", {"lugar": "Chinchero"})
    c.registrar("CAFE-1", "Secado", {"dias": 3})
    c.registrar("CAFE-1", "Empacado", {"peso": "250 g"})
    c.registrar("PAPA-1", "Empacado", {"peso": "1 kg"})
    return c


class TestCasosNormales(unittest.TestCase):
    def test_historial_por_lote(self):
        c = crear()
        self.assertEqual([b.etapa for b in c.historial("CAFE-1")], ["Cosecha", "Secado", "Empacado"])
        self.assertEqual([b.etapa for b in c.historial("PAPA-1")], ["Cosecha", "Empacado"])

    def test_cadena_valida(self):
        self.assertTrue(crear().es_valida())

    def test_enlace_entre_bloques(self):
        c = crear()
        self.assertEqual(c.bloques[0].hash_previo, "0")
        for i in range(1, len(c.bloques)):
            self.assertEqual(c.bloques[i].hash_previo, c.bloques[i - 1].hash)

    def test_prueba_de_trabajo(self):
        c = crear(dificultad=2)
        self.assertTrue(all(b.hash.startswith("00") for b in c.bloques))

    def test_funciona_con_cada_arbol(self):
        for tipo, clase in [("bst", BST), ("avl", AVL), ("splay", SplayTree)]:
            with self.subTest(arbol=tipo):
                c = crear(tipo)
                self.assertIsInstance(c.indice, clase)
                self.assertEqual(len(c.historial("CAFE-1")), 3)

    def test_reconstruir_indice_da_mismos_resultados(self):
        c = crear("bst")
        esperado = {l: [b.index for b in c.historial(l)] for l in ("CAFE-1", "PAPA-1")}
        for tipo in ("avl", "splay", "bst"):
            c.reconstruir_indice(tipo)
            self.assertEqual(c.tipo_arbol, tipo)
            for l, pos in esperado.items():
                self.assertEqual([b.index for b in c.historial(l)], pos)

    def test_datos_se_copian_al_registrar(self):
        datos = {"a": 1}
        c = Cadena(dificultad=0)
        c.registrar("A-1", "Cosecha", datos)
        datos["a"] = 999                      # el llamador no puede alterar la cadena
        self.assertTrue(c.es_valida())


class TestEstadoPorBloque(unittest.TestCase):
    def test_todos_ok_en_cadena_integra(self):
        estados = crear().estado_bloques()
        self.assertEqual(len(estados), 5)
        self.assertTrue(all(ok for ok, _ in estados))

    def test_solo_el_bloque_alterado_falla(self):
        c = crear()
        c.bloques[2].datos["dias"] = 1
        self.assertEqual([ok for ok, _ in c.estado_bloques()], [True, True, False, True, True])
        self.assertFalse(c.es_valida())

    def test_motivo_de_enlace_roto(self):
        c = crear()
        b = c.bloques[3]
        b.hash_previo = "0" * 64              # enlace roto, pero el bloque se re-mina
        b.nonce = 0
        b.hash = b.calcular_hash()
        b.minar(c.dificultad)
        ok, motivo = c.estado_bloques()[3]
        self.assertFalse(ok)
        self.assertIn("enlaza", motivo)


class TestCasosLimite(unittest.TestCase):
    def test_cadena_vacia(self):
        c = Cadena(dificultad=0)
        self.assertTrue(c.es_valida())
        self.assertEqual(c.historial("A-1"), [])
        self.assertFalse(c.existe("A-1"))

    def test_un_solo_bloque(self):
        c = Cadena(dificultad=0)
        c.registrar("A-1", "Cosecha", {})
        self.assertTrue(c.es_valida())
        self.assertEqual(len(c.historial("A-1")), 1)

    def test_lote_inexistente(self):
        c = crear()
        self.assertEqual(c.historial("NOEXISTE-9"), [])
        self.assertFalse(c.existe("NOEXISTE-9"))

    def test_datos_vacios_y_unicode(self):
        c = Cadena(dificultad=0)
        c.registrar("A-1", "Cosecha", {})
        c.registrar("A-1", "Secado", {"nota": "Año 2026, ñandú, café ☕"})
        self.assertTrue(c.es_valida())

    def test_dificultad_cero(self):
        c = Cadena(dificultad=0)
        c.registrar("A-1", "Cosecha", {})
        self.assertEqual(c.bloques[0].nonce, 0)


class TestEntradasAdversas(unittest.TestCase):
    def test_alterar_datos(self):
        c = crear()
        c.bloques[2].datos["dias"] = 1
        self.assertFalse(c.es_valida())

    def test_alterar_primer_bloque(self):
        c = crear()
        c.bloques[0].datos["lugar"] = "Otro"
        self.assertFalse(c.es_valida())

    def test_alterar_hash_previo(self):
        c = crear()
        c.bloques[3].hash_previo = "0" * 64
        self.assertFalse(c.es_valida())

    def test_alterar_lote_o_etapa(self):
        c = crear()
        c.bloques[1].lote = "FALSO-1"
        self.assertFalse(c.es_valida())
        c = crear()
        c.bloques[1].etapa = "Venta"
        self.assertFalse(c.es_valida())

    def test_alterar_y_recalcular_hash_se_detecta_por_el_enlace(self):
        c = crear()
        b = c.bloques[1]
        b.datos["lugar"] = "Otro"
        b.nonce = 0
        b.hash = b.calcular_hash()
        b.minar(c.dificultad)                 # el atacante re-mina su bloque
        self.assertFalse(c.es_valida())       # pero el siguiente bloque ya no enlaza

    def test_intercambiar_bloques(self):
        c = crear()
        c.bloques[1], c.bloques[2] = c.bloques[2], c.bloques[1]
        self.assertFalse(c.es_valida())

    def test_eliminar_bloque_intermedio(self):
        c = crear()
        del c.bloques[2]
        self.assertFalse(c.es_valida())

    def test_hash_sin_prueba_de_trabajo(self):
        c = crear(dificultad=2)
        b = c.bloques[-1]
        b.hash = "f" * 64
        self.assertFalse(c.es_valida())

    def test_limitacion_conocida_ultimo_bloque_eliminado(self):
        """Limitación documentada: quitar el último bloque no rompe ningún enlace."""
        c = crear()
        c.bloques.pop()
        self.assertTrue(c.es_valida())        # una cadena sola no puede detectarlo


if __name__ == "__main__":
    unittest.main()
