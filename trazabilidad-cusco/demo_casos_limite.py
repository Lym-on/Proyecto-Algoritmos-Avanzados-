"""Muestra con números los casos límite (los mismos de tests/test_cadena.py)."""
from cadena import Cadena
from trees import BST, AVL, SplayTree

print("=== CASO 1: cadena vacía ===")
c = Cadena(dificultad=0)
print("bloques:", len(c.bloques))
print("es_valida():", c.es_valida())
print("historial('A-1'):", c.historial("A-1"))
print("existe('A-1'):", c.existe("A-1"))

print("\n=== CASO 2: un solo bloque ===")
c = Cadena(dificultad=0)
b = c.registrar("A-1", "Cosecha", {})
print("bloques:", len(c.bloques))
print("hash_previo:", b.hash_previo)
print("hash:", b.hash[:16], "...")
print("es_valida():", c.es_valida())
print("etapas de A-1:", len(c.historial("A-1")))

print("\n=== CASO 3: lote inexistente ===")
c = Cadena(dificultad=0)
c.registrar("CAFE-1", "Cosecha", {})
print("historial('NOEXISTE-9'):", c.historial("NOEXISTE-9"))
print("existe('NOEXISTE-9'):", c.existe("NOEXISTE-9"))

print("\n=== CASO 4: datos vacíos y unicode ===")
c = Cadena(dificultad=0)
c.registrar("A-1", "Cosecha", {})
c.registrar("A-1", "Secado", {"nota": "Año 2026, ñandú, café ☕"})
print("datos bloque 0:", c.bloques[0].datos)
print("datos bloque 1:", c.bloques[1].datos)
print("es_valida():", c.es_valida())

print("\n=== CASO 5: dificultad 0 vs 2 (prueba de trabajo) ===")
for d in (0, 2, 3):
    c = Cadena(dificultad=d)
    b = c.registrar("A-1", "Cosecha", {})
    print(f"dificultad={d}: nonce={b.nonce:<6} hash={b.hash[:12]}...")

print("\n=== CASO 6: árboles con 0 y 1 elemento ===")
for clase in (BST, AVL, SplayTree):
    t = clase()
    vacio = (t.search("x"), t.height())
    t.insert("a", 1)
    uno = (t.search("a"), t.search("b"), t.height())
    print(f"{clase.__name__:<10} vacío -> search/altura={vacio} | 1 elemento -> a/b/altura={uno}")

print("\n=== CASO 7: BST degenera con orden creciente (n = 500) ===")
for clase in (BST, AVL, SplayTree):
    t = clase()
    for i in range(500):
        t.insert(i)
    print(f"{clase.__name__:<10} altura = {t.height()}")

print("\n=== CASO 8: Splay, reacceso al mismo elemento ===")
t = SplayTree()
for i in range(1000):
    t.insert(i)
t.comparisons = 0; t.search(500); primera = t.comparisons
t.comparisons = 0; t.search(500); segunda = t.comparisons
print(f"1ª búsqueda de 500: {primera} comparaciones | 2ª búsqueda: {segunda} comparación")
