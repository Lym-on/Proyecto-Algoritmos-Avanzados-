"""Generación reproducible (por semilla) de instancias y patrones de consulta."""
import itertools
import random

from cadena import Cadena, ErrorValidacion

ETAPAS = ["Cosecha", "Secado", "Seleccion", "Lavado", "Empacado", "Transporte", "Venta"]
PATRONES = ("uniforme", "80_20", "zipf", "rafaga")
ORDENES = ("aleatorio", "ordenado")
ZIPF_S = 1.1          # exponente de la distribución Zipf
FRACCION_CALIENTE = 0.2
PROB_CALIENTE = 0.8
TAM_RAFAGA = 10
PROB_REPETIR = 0.9


def nombres_lotes(n):
    if not isinstance(n, int) or n < 1:
        raise ErrorValidacion("n_lotes debe ser un entero >= 1.")
    return [f"LOTE-{i:06d}" for i in range(n)]


def generar_cadena(n_lotes, etapas_por_lote=3, semilla=0, orden="aleatorio",
                   tipo_arbol="splay"):
    """Devuelve (cadena, lotes, referencia).

    referencia: dict lote -> lista de posiciones de sus bloques (verdad de referencia
    construida sin usar ningún árbol).
    """
    if orden not in ORDENES:
        raise ErrorValidacion(f"orden inválido: {orden!r}. Opciones: {ORDENES}")
    if not 1 <= etapas_por_lote <= len(ETAPAS):
        raise ErrorValidacion(f"etapas_por_lote debe estar entre 1 y {len(ETAPAS)}.")
    rng = random.Random(f"cadena-{semilla}")
    lotes = nombres_lotes(n_lotes)
    orden_insercion = lotes[:]
    if orden == "aleatorio":
        rng.shuffle(orden_insercion)
    cadena = Cadena(dificultad=0, tipo_arbol=tipo_arbol)
    for k in range(etapas_por_lote):
        for lote in orden_insercion:
            cadena.registrar(lote, ETAPAS[k], {"paso": k, "peso_kg": round(rng.uniform(1, 100), 2)})
    referencia = {}
    for b in cadena.bloques:
        referencia.setdefault(b.lote, []).append(b.index)
    return cadena, lotes, referencia


def generar_consultas(lotes, patron, n_consultas, semilla=0):
    """Lista de códigos de lote a consultar según el patrón de acceso."""
    if patron not in PATRONES:
        raise ErrorValidacion(f"patrón inválido: {patron!r}. Opciones: {PATRONES}")
    if n_consultas < 0:
        raise ErrorValidacion("n_consultas debe ser >= 0.")
    rng = random.Random(f"consultas-{patron}-{semilla}")
    if patron == "uniforme":
        return [rng.choice(lotes) for _ in range(n_consultas)]
    perm = lotes[:]
    rng.shuffle(perm)             # qué lotes son "populares" no depende del orden de inserción
    if patron == "80_20":
        k = max(1, int(len(perm) * FRACCION_CALIENTE))
        calientes, frios = perm[:k], (perm[k:] or perm[:k])
        return [rng.choice(calientes) if rng.random() < PROB_CALIENTE else rng.choice(frios)
                for _ in range(n_consultas)]
    if patron == "zipf":
        acumulado = list(itertools.accumulate(1 / (r + 1) ** ZIPF_S for r in range(len(perm))))
        return rng.choices(perm, cum_weights=acumulado, k=n_consultas)
    # rafaga: localidad temporal (se repiten los accesos recientes)
    reciente = [rng.choice(lotes) for _ in range(min(TAM_RAFAGA, len(lotes)))]
    salida = []
    for _ in range(n_consultas):
        if rng.random() < PROB_REPETIR:
            lote = rng.choice(reciente)
        else:
            lote = rng.choice(lotes)
            reciente[rng.randrange(len(reciente))] = lote
        salida.append(lote)
    return salida
