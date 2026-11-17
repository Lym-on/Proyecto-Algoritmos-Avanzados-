import unittest

import app as web


class TestWeb(unittest.TestCase):
    def setUp(self):
        self.c = web.app.test_client()

    def tearDown(self):
        self.c.get("/demo/restaurar")

    def html(self, url, **kw):
        r = self.c.get(url, **kw)
        return r, r.get_data(as_text=True)

    def test_paginas_principales(self):
        for url in ["/", "/cadena", "/bloque/0", "/bloque/5", "/lote/CAFE-2026-0001"]:
            with self.subTest(url=url):
                r, _ = self.html(url)
                self.assertEqual(r.status_code, 200)

    def test_cadena_integra_muestra_sello_verde(self):
        _, t = self.html("/lote/CAFE-2026-0001")
        self.assertIn("Historial verificado", t)
        self.assertNotIn("Alterado", t)

    def test_no_encontrados(self):
        for url in ["/bloque/999", "/lote/NOEXISTE-9"]:
            with self.subTest(url=url):
                r, t = self.html(url)
                self.assertEqual(r.status_code, 404)
                self.assertIn("No existe", t)

    def test_busqueda_por_lote_bloque_y_hash(self):
        r, _ = self.html("/buscar?q=cafe-2026-0001")
        self.assertEqual(r.headers["Location"], "/lote/CAFE-2026-0001")
        r, _ = self.html("/buscar?q=4")
        self.assertEqual(r.headers["Location"], "/bloque/4")
        h = web.cadena.bloques[2].hash
        r, _ = self.html(f"/buscar?q={h[:12]}")
        self.assertEqual(r.headers["Location"], "/bloque/2")

    def test_busqueda_basura_no_rompe(self):
        for q in ["<script>", "' OR 1=1 --", "   ", "9" * 40]:
            with self.subTest(q=q):
                r, _ = self.html("/buscar", query_string={"q": q}, follow_redirects=True)
                self.assertIn(r.status_code, (200, 404))

    def test_alteracion_se_ve_en_la_web_y_se_restaura(self):
        self.c.get("/demo/alterar")
        _, t = self.html("/bloque/1")
        self.assertIn("Cadena alterada", t)
        self.assertIn("Hash recalculado", t)
        _, t = self.html("/lote/CAFE-2026-0001")
        self.assertIn("La cadena fue alterada", t)
        self.c.get("/demo/restaurar")
        _, t = self.html("/lote/CAFE-2026-0001")
        self.assertIn("Historial verificado", t)

    def test_paginacion_fuera_de_rango(self):
        r, _ = self.html("/cadena?pagina=999")
        self.assertEqual(r.status_code, 200)
        r, _ = self.html("/cadena?pagina=-3")
        self.assertEqual(r.status_code, 200)

    def test_datos_se_escapan_contra_html(self):
        c = web.cadena
        b = c.registrar("XSS-1", "Cosecha", {"nota": "<script>alert(1)</script>"})
        try:
            _, t = self.html(f"/bloque/{b.index}")
            self.assertNotIn("<script>alert(1)</script>", t)
            self.assertIn("&lt;script&gt;", t)
        finally:
            c.bloques.pop()
            c.reconstruir_indice()


if __name__ == "__main__":
    unittest.main()
