from cadena import Cadena

c = Cadena()
c.registrar("CAFE-2026-0001", "Cosecha", {"productor": "Don Mario", "lugar": "Quillabamba"})
c.registrar("CAFE-2026-0001", "Secado", {"dias": 3})
c.registrar("CAFE-2026-0001", "Empacado", {"lugar": "Cusco"})

for b in c.historial("CAFE-2026-0001"):
    print(b.index, b.etapa, b.datos, b.hash[:10])

print("Cadena válida:", c.es_valida())
c.bloques[1].datos["dias"] = 1          # intento de trampa
print("Después de alterar:", c.es_valida())
