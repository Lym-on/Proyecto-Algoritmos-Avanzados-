# Datos de ejemplo (productores ficticios)
LOTES = {
    "CAFE-2026-0001": {
        "producto": "Café de altura",
        "etapas": [
            ("Cosecha", {"fecha": "2026-05-10", "productor": "Don Mario Quispe", "lugar": "Quillabamba, La Convención"}),
            ("Secado", {"fecha": "2026-05-12", "dias": 3, "metodo": "Al sol, en tendales"}),
            ("Empacado", {"fecha": "2026-05-20", "lugar": "Cusco", "peso": "250 g"}),
            ("Transporte", {"fecha": "2026-05-22", "destino": "Tienda Plaza Regocijo"}),
        ],
    },
    "PAPA-2026-0002": {
        "producto": "Papa nativa",
        "etapas": [
            ("Cosecha", {"fecha": "2026-04-15", "productor": "Comunidad Chinchero", "lugar": "Chinchero, Urubamba"}),
            ("Selección", {"fecha": "2026-04-16", "variedades": "Peruanita, Huayro, Ccompis"}),
            ("Empacado", {"fecha": "2026-04-18", "lugar": "Cusco", "peso": "1 kg"}),
            ("Venta", {"fecha": "2026-04-20", "lugar": "Mercado San Pedro"}),
        ],
    },
    "QUINUA-2026-0003": {
        "producto": "Quinua orgánica",
        "etapas": [
            ("Cosecha", {"fecha": "2026-06-02", "productor": "Doña Rosa Huamán", "lugar": "Anta, Cusco"}),
            ("Lavado", {"fecha": "2026-06-05", "detalle": "Eliminación de saponina"}),
            ("Empacado", {"fecha": "2026-06-08", "lugar": "Cusco", "peso": "500 g"}),
        ],
    },
}


def cargar_demo(cadena):
    # Se registran intercalados para que los bloques de un lote queden separados
    maximo = max(len(v["etapas"]) for v in LOTES.values())
    for i in range(maximo):
        for codigo, info in LOTES.items():
            if i < len(info["etapas"]):
                etapa, datos = info["etapas"][i]
                cadena.registrar(codigo, etapa, datos)
