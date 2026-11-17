import unittest

from cadena import Cadena, ErrorValidacion
from generador import generar_cadena, generar_consultas


class TestValidacion(unittest.TestCase):
    def setUp(self):
        self.c = Cadena(dificultad=0)

    def test_lotes_invalidos(self):
        for malo in ["", "abc", "lote 1", "A--", "-A", "A_1", None, 123, "A" * 61]:
            with self.subTest(lote=malo):
                with self.assertRaises(ErrorValidacion):
                    self.c.registrar(malo, "Cosecha", {})

    def test_lote_valido(self):
        self.c.registrar("CAFE-2026-0001", "Cosecha", {})
        self.c.registrar("A", "Cosecha", {})

    def test_etapas_invalidas(self):
        for mala in ["", "   ", None, 5, "x" * 61]:
            with self.subTest(etapa=mala):
                with self.assertRaises(ErrorValidacion):
                    self.c.registrar("A-1", mala, {})

    def test_datos_invalidos(self):
        for malo in [None, [], "texto", 5, {1: "a"}, {"a": {1, 2}}, {"a": object()}]:
            with self.subTest(datos=malo):
                with self.assertRaises(ErrorValidacion):
                    self.c.registrar("A-1", "Cosecha", malo)

    def test_etapa_repetida_en_mismo_lote(self):
        self.c.registrar("A-1", "Cosecha", {})
        with self.assertRaises(ErrorValidacion):
            self.c.registrar("A-1", "Cosecha", {})
        self.c.registrar("A-2", "Cosecha", {})   # otro lote sí puede

    def test_registro_rechazado_no_deja_rastro(self):
        with self.assertRaises(ErrorValidacion):
            self.c.registrar("mal", "Cosecha", {})
        self.assertEqual(len(self.c.bloques), 0)
        self.assertFalse(self.c.existe("mal"))

    def test_parametros_de_cadena(self):
        for dif in [-1, 6, 1.5, "2", True]:
            with self.subTest(dificultad=dif):
                with self.assertRaises(ErrorValidacion):
                    Cadena(dificultad=dif)
        with self.assertRaises(ErrorValidacion):
            Cadena(tipo_arbol="rojo-negro")

    def test_parametros_del_generador(self):
        with self.assertRaises(ErrorValidacion):
            generar_cadena(0)
        with self.assertRaises(ErrorValidacion):
            generar_cadena(10, etapas_por_lote=0)
        with self.assertRaises(ErrorValidacion):
            generar_cadena(10, orden="raro")
        with self.assertRaises(ErrorValidacion):
            generar_consultas(["A"], "inexistente", 5)


if __name__ == "__main__":
    unittest.main()
