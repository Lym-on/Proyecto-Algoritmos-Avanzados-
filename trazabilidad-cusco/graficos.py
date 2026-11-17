"""Genera tablas (Markdown) y gráficos (PNG) a partir de resultados/crudo_<modo>.csv.

Uso:  python graficos.py --modo completo
"""
import argparse
import csv
import os
import statistics
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CARPETA = "resultados"
ARBOLES = ["bst", "avl", "splay"]
PATRONES = ["uniforme", "80_20", "zipf", "rafaga"]
COLORES = {"bst": "#c0392b", "avl": "#2471a3", "splay": "#1e8449"}


def leer(modo):
    with open(os.path.join(CARPETA, f"crudo_{modo}.csv"), encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    for f in filas:
        for c in ("n_lotes", "n_bloques", "consultas", "comps_construccion", "comps_totales",
                  "altura_inicial", "altura_final", "errores", "repeticion"):
            f[c] = int(f[c])
        for c in ("comps_por_consulta", "t_construccion_ms", "t_consultas_ms",
                  "t_verificacion_cadena_ms"):
            f[c] = float(f[c])
    return filas


def agrupar(filas, metrica):
    g = defaultdict(list)
    for f in filas:
        g[(f["orden"], f["patron"], f["n_lotes"], f["arbol"])].append(f[metrica])
    return {k: (statistics.mean(v), statistics.pstdev(v)) for k, v in g.items()}


def tabla_md(filas, metrica, titulo, decimales=2):
    datos = agrupar(filas, metrica)
    tamanos = sorted({f["n_lotes"] for f in filas})
    ordenes = sorted({f["orden"] for f in filas})
    out = [f"### {titulo}\n"]
    for orden in ordenes:
        out.append(f"**Inserción {orden}** (media ± desv. estándar de las repeticiones)\n")
        out.append("| Patrón | N lotes | BST | AVL | Splay |")
        out.append("|---|---:|---:|---:|---:|")
        for patron in PATRONES:
            for n in tamanos:
                celdas = []
                for a in ARBOLES:
                    m, s = datos[(orden, patron, n, a)]
                    celdas.append(f"{m:.{decimales}f} ± {s:.{decimales}f}")
                out.append(f"| {patron} | {n} | " + " | ".join(celdas) + " |")
        out.append("")
    return "\n".join(out)


def figura(filas, metrica, ylabel, nombre, modo):
    datos = agrupar(filas, metrica)
    tamanos = sorted({f["n_lotes"] for f in filas})
    for orden in sorted({f["orden"] for f in filas}):
        fig, ejes = plt.subplots(1, 4, figsize=(16, 3.8), sharey=True)
        for ax, patron in zip(ejes, PATRONES):
            for a in ARBOLES:
                ys = [datos[(orden, patron, n, a)][0] for n in tamanos]
                err = [datos[(orden, patron, n, a)][1] for n in tamanos]
                ax.errorbar(tamanos, ys, yerr=err, marker="o", label=a.upper() if a != "splay" else "Splay",
                            color=COLORES[a], capsize=3)
            ax.set_xscale("log")
            ax.set_yscale("log")
            ax.set_title(f"Patrón {patron}")
            ax.set_xlabel("N (lotes)")
            ax.grid(alpha=.3, which="both")
        ejes[0].set_ylabel(ylabel)
        ejes[0].legend()
        fig.suptitle(f"{ylabel} — inserción {orden}")
        fig.tight_layout()
        ruta = os.path.join(CARPETA, f"{nombre}_{orden}_{modo}.png")
        fig.savefig(ruta, dpi=130)
        plt.close(fig)
        print("figura:", ruta)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modo", choices=["piloto", "completo"], default="completo")
    modo = ap.parse_args().modo
    filas = leer(modo)
    partes = [f"# Resultados ({modo})\n",
              tabla_md(filas, "comps_por_consulta", "Comparaciones por consulta"),
              tabla_md(filas, "altura_inicial", "Altura del árbol tras construirlo", 1),
              tabla_md(filas, "t_consultas_ms", "Tiempo total de las consultas (ms)", 1),
              tabla_md(filas, "comps_construccion", "Comparaciones para construir el índice", 0)]
    verif = defaultdict(list)
    for f in filas:
        verif[f["n_lotes"]].append(f["t_verificacion_cadena_ms"])
    partes.append("### Tiempo de verificar la cadena completa (ms)\n")
    partes.append("| N lotes | Bloques | Tiempo medio (ms) |\n|---:|---:|---:|")
    for n in sorted(verif):
        partes.append(f"| {n} | {n * 3} | {statistics.mean(verif[n]):.2f} |")
    ruta = os.path.join(CARPETA, f"tablas_{modo}.md")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("\n".join(partes) + "\n")
    print("tablas:", ruta)
    figura(filas, "comps_por_consulta", "Comparaciones por consulta", "comparaciones", modo)
    figura(filas, "t_consultas_ms", "Tiempo de consultas (ms)", "tiempo", modo)


if __name__ == "__main__":
    main()
