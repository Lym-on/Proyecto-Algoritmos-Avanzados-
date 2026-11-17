"""Experimentos: Splay vs AVL vs BST como índice de la cadena de trazabilidad.

Uso:
    python benchmark.py --modo piloto      # rápido (segundos), verifica el procedimiento
    python benchmark.py --modo completo    # experimento definitivo (varios minutos)
"""
import argparse
import csv
import math
import os
import platform
import sys
import time
from datetime import datetime

from cadena import ARBOLES
from generador import PATRONES, ORDENES, generar_cadena, generar_consultas

CONFIG = {
    "piloto":   {"tamanos": [100, 500],         "repeticiones": 2, "consultas": 2000},
    "completo": {"tamanos": [100, 1000, 5000],  "repeticiones": 5, "consultas": 10000},
}
ETAPAS_POR_LOTE = 3
SEMILLA_BASE = 2026
CAMPOS = ["modo", "n_lotes", "n_bloques", "orden", "patron", "arbol", "repeticion", "semilla",
          "consultas", "comps_construccion", "comps_totales", "comps_por_consulta",
          "altura_inicial", "altura_final", "t_construccion_ms", "t_consultas_ms",
          "t_verificacion_cadena_ms", "errores"]
CARPETA = "resultados"


def medir(indice, consultas, referencia):
    """Mide solo las consultas; la verificación contra la referencia va aparte."""
    indice.comparisons = 0
    t0 = time.perf_counter()
    for lote in consultas:
        indice.search(lote)
    t = (time.perf_counter() - t0) * 1000
    comps = indice.comparisons
    altura_final = indice.height()
    errores = sum(1 for lote in consultas if indice.search(lote) != referencia[lote])
    return comps, altura_final, t, errores


def ejecutar(modo, verbose=True):
    cfg = CONFIG[modo]
    filas = []
    for n in cfg["tamanos"]:
        for orden in ORDENES:
            for rep in range(cfg["repeticiones"]):
                semilla = SEMILLA_BASE + rep
                cadena, lotes, referencia = generar_cadena(n, ETAPAS_POR_LOTE, semilla, orden)
                t0 = time.perf_counter()
                cadena_valida = cadena.es_valida()
                t_verif = (time.perf_counter() - t0) * 1000
                assert cadena_valida, "la cadena generada debe ser válida"
                estaticos = {}      # BST y AVL no cambian al buscar: se construyen una vez
                for patron in PATRONES:
                    consultas = generar_consultas(lotes, patron, cfg["consultas"], semilla)
                    for tipo in ARBOLES:
                        if tipo in estaticos:
                            indice, comps_b, t_b, h0 = estaticos[tipo]
                        else:
                            t0 = time.perf_counter()
                            indice = cadena.reconstruir_indice(tipo)
                            t_b = (time.perf_counter() - t0) * 1000
                            comps_b, h0 = indice.comparisons, indice.height()
                            if tipo != "splay":
                                estaticos[tipo] = (indice, comps_b, t_b, h0)
                        comps, h1, t_q, errores = medir(indice, consultas, referencia)
                        filas.append({
                            "modo": modo, "n_lotes": n, "n_bloques": len(cadena.bloques),
                            "orden": orden, "patron": patron, "arbol": tipo,
                            "repeticion": rep, "semilla": semilla, "consultas": len(consultas),
                            "comps_construccion": comps_b, "comps_totales": comps,
                            "comps_por_consulta": round(comps / len(consultas), 4),
                            "altura_inicial": h0, "altura_final": h1,
                            "t_construccion_ms": round(t_b, 3), "t_consultas_ms": round(t_q, 3),
                            "t_verificacion_cadena_ms": round(t_verif, 3), "errores": errores,
                        })
                if verbose:
                    print(f"  n={n:<5} orden={orden:<9} rep={rep} listo", flush=True)
    return filas


def guardar(filas, modo):
    os.makedirs(CARPETA, exist_ok=True)
    ruta = os.path.join(CARPETA, f"crudo_{modo}.csv")
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(filas)
    with open(os.path.join(CARPETA, f"entorno_{modo}.txt"), "w", encoding="utf-8") as f:
        f.write(f"fecha: {datetime.now().isoformat(timespec='seconds')}\n")
        f.write(f"python: {sys.version.split()[0]}\nsistema: {platform.platform()}\n")
        f.write(f"procesador: {platform.processor() or 'desconocido'}\n")
        f.write(f"configuracion: {CONFIG[modo]}\netapas_por_lote: {ETAPAS_POR_LOTE}\n")
        f.write(f"semilla_base: {SEMILLA_BASE}\n")
    return ruta


def verificar(filas):
    """Comprobaciones de corrección y coherencia. Devuelve lista de fallos."""
    fallos = []
    if any(f["errores"] != 0 for f in filas):
        fallos.append("hay consultas cuyo resultado no coincide con la referencia")
    if any(f["comps_por_consulta"] <= 0 for f in filas):
        fallos.append("comparaciones por consulta <= 0")
    for f in filas:
        if f["n_bloques"] != f["n_lotes"] * ETAPAS_POR_LOTE:
            fallos.append("número de bloques incoherente")
            break
    for f in filas:
        if f["arbol"] == "avl":
            cota = 1.4405 * math.log2(f["n_lotes"] + 2)
            if f["altura_inicial"] > cota + 1e-9:
                fallos.append(f"AVL supera la cota teórica de altura ({f['altura_inicial']} > {cota:.2f})")
                break
    for f in filas:
        if f["arbol"] == "bst" and f["orden"] == "ordenado" and f["altura_inicial"] != f["n_lotes"]:
            fallos.append("BST con inserción ordenada debería degenerar en lista (altura = n)")
            break
    return fallos


def huella(filas):
    """Columnas deterministas (no dependen del reloj) para comprobar reproducibilidad."""
    return [(f["n_lotes"], f["orden"], f["patron"], f["arbol"], f["repeticion"],
             f["comps_construccion"], f["comps_totales"], f["altura_inicial"], f["altura_final"])
            for f in filas]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--modo", choices=list(CONFIG), default="piloto")
    args = ap.parse_args()
    print(f"Modo {args.modo}: {CONFIG[args.modo]}")
    t0 = time.perf_counter()
    filas = ejecutar(args.modo)
    ruta = guardar(filas, args.modo)
    print(f"{len(filas)} mediciones guardadas en {ruta} ({time.perf_counter() - t0:.1f} s)")
    fallos = verificar(filas)
    print("Verificación de corrección y coherencia:", "OK" if not fallos else "FALLÓ")
    for f in fallos:
        print("  -", f)
    if args.modo == "piloto":
        print("Repitiendo el piloto para comprobar reproducibilidad...")
        repetido = ejecutar("piloto", verbose=False)
        igual = huella(filas) == huella(repetido)
        print("Reproducibilidad (mismas semillas -> mismas métricas):", "OK" if igual else "FALLÓ")
        if not igual:
            fallos.append("no reproducible")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
