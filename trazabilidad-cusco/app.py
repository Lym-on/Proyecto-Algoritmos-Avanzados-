"""Explorador web de la cadena de trazabilidad (estilo explorador de Bitcoin)."""
import json
import re
from datetime import datetime

from flask import Flask, abort, redirect, render_template, request, url_for
from markupsafe import Markup, escape

from cadena import Cadena
from datos import LOTES, cargar_demo

app = Flask(__name__)
cadena = Cadena()
cargar_demo(cadena)
_original = {}
POR_PAGINA = 15


# ---------- filtros de plantilla ----------
@app.template_filter("hash_corto")
def hash_corto(h):
    return h if len(h) <= 16 else f"{h[:10]}…{h[-6:]}"


@app.template_filter("hash_html")
def hash_html(h):
    """Hash completo con los ceros iniciales (prueba de trabajo) resaltados."""
    ceros = len(h) - len(h.lstrip("0"))
    return Markup(f'<span class="zeros">{"0" * ceros}</span>{escape(h[ceros:])}')


@app.template_filter("fecha")
def fecha(ts):
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


@app.template_filter("json_bonito")
def json_bonito(d):
    return json.dumps(d, indent=2, ensure_ascii=False)


# ---------- utilidades ----------
def estados():
    """Estado visual de cada bloque: ok, malo (alterado) o afectado (posterior a uno alterado)."""
    base = cadena.estado_bloques()
    primero = next((i for i, (ok, _) in enumerate(base) if not ok), None)
    salida = []
    for i, (ok, motivo) in enumerate(base):
        if not ok:
            nivel = "malo"
        elif primero is not None and i > primero:
            nivel, motivo = "afectado", f"Posterior al bloque #{primero}, que fue alterado."
        else:
            nivel = "ok"
        salida.append({"nivel": nivel, "motivo": motivo})
    return salida, primero


def producto(codigo):
    info = LOTES.get(codigo)
    return info["producto"] if info else codigo


def resumen():
    lotes = {b.lote for b in cadena.bloques}
    est, primero = estados()
    return {
        "bloques": len(cadena.bloques),
        "lotes": len(lotes),
        "dificultad": cadena.dificultad,
        "valida": primero is None,
        "primero_malo": primero,
        "arbol": cadena.tipo_arbol,
        "comparaciones": cadena.indice.comparisons,
    }


app.jinja_env.globals.update(producto=producto)


# ---------- rutas ----------
@app.route("/")
def inicio():
    est, _ = estados()
    ultimos = [(b, est[b.index]) for b in reversed(cadena.bloques[-10:])]
    return render_template("inicio.html", r=resumen(), ultimos=ultimos, lotes=LOTES)


@app.route("/cadena")
def ver_cadena():
    pagina = max(1, request.args.get("pagina", 1, type=int))
    est, _ = estados()
    todos = [(b, est[b.index]) for b in reversed(cadena.bloques)]
    total_pag = max(1, -(-len(todos) // POR_PAGINA))
    pagina = min(pagina, total_pag)
    corte = todos[(pagina - 1) * POR_PAGINA: pagina * POR_PAGINA]
    return render_template("cadena.html", r=resumen(), filas=corte, pagina=pagina, total_pag=total_pag)


@app.route("/buscar")
def buscar():
    q = request.args.get("q", "").strip()
    if q.isdigit():
        return redirect(url_for("ver_bloque", n=int(q)))
    if re.fullmatch(r"[0-9a-fA-F]{8,64}", q):
        for b in cadena.bloques:
            if b.hash.startswith(q.lower()):
                return redirect(url_for("ver_bloque", n=b.index))
    return redirect(url_for("ver_lote", codigo=q.upper()))


@app.route("/bloque/<int:n>")
def ver_bloque(n):
    if not 0 <= n < len(cadena.bloques):
        return render_template("no_encontrado.html", r=resumen(), que=f"bloque #{n}"), 404
    est, _ = estados()
    b = cadena.bloques[n]
    return render_template(
        "bloque.html", r=resumen(), b=b, e=est[n],
        recalculado=b.calcular_hash(),
        hay_siguiente=n + 1 < len(cadena.bloques),
    )


@app.route("/lote/<codigo>")
def ver_lote(codigo):
    etapas = cadena.historial(codigo)
    if not etapas:
        return render_template("no_encontrado.html", r=resumen(), que=f"lote «{codigo}»"), 404
    est, _ = estados()
    filas = [(b, est[b.index]) for b in etapas]
    ok = all(e["nivel"] == "ok" for _, e in filas) and resumen()["valida"]
    return render_template("lote.html", r=resumen(), codigo=codigo, nombre=producto(codigo),
                           filas=filas, ok=ok)


# ---------- solo para la demostración en clase ----------
@app.route("/demo/alterar")
def alterar():
    bloque = cadena.bloques[1]
    _original["datos"] = dict(bloque.datos)
    bloque.datos["fecha"] = "1999-01-01"      # trampa
    return redirect(url_for("ver_bloque", n=1))


@app.route("/demo/restaurar")
def restaurar():
    if "datos" in _original:
        cadena.bloques[1].datos.clear()
        cadena.bloques[1].datos.update(_original.pop("datos"))
    return redirect(url_for("inicio"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
