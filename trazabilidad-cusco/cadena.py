"""Blockchain de trazabilidad con índice de búsqueda intercambiable (BST, AVL, Splay)."""
import copy
import hashlib
import json
import re
import time

from trees import BST, AVL, SplayTree

ARBOLES = {"bst": BST, "avl": AVL, "splay": SplayTree}
PATRON_CODIGO = re.compile(r"^[A-Z0-9]+(-[A-Z0-9]+)*$")
MAX_TEXTO = 60
MAX_DIFICULTAD = 5


class ErrorValidacion(ValueError):
    """Entrada inválida (código, etapa, datos o parámetros)."""


def validar_lote(lote):
    if not isinstance(lote, str) or not lote:
        raise ErrorValidacion("El código de lote debe ser un texto no vacío.")
    if len(lote) > MAX_TEXTO:
        raise ErrorValidacion(f"El código de lote supera {MAX_TEXTO} caracteres.")
    if not PATRON_CODIGO.match(lote):
        raise ErrorValidacion("Código de lote inválido: use MAYÚSCULAS, dígitos y guiones (ej. CAFE-2026-0001).")


def validar_etapa(etapa):
    if not isinstance(etapa, str) or not etapa.strip():
        raise ErrorValidacion("La etapa debe ser un texto no vacío.")
    if len(etapa) > MAX_TEXTO:
        raise ErrorValidacion(f"La etapa supera {MAX_TEXTO} caracteres.")


def validar_datos(datos):
    if not isinstance(datos, dict):
        raise ErrorValidacion("Los datos deben ser un diccionario.")
    if not all(isinstance(k, str) for k in datos):
        raise ErrorValidacion("Todas las claves de los datos deben ser texto.")
    try:
        json.dumps(datos)
    except (TypeError, ValueError):
        raise ErrorValidacion("Los datos deben poder serializarse a JSON.")


class Bloque:
    def __init__(self, index, lote, etapa, datos, hash_previo, dificultad=2):
        self.index = index
        self.timestamp = time.time()
        self.lote = lote
        self.etapa = etapa
        self.datos = datos
        self.hash_previo = hash_previo
        self.nonce = 0
        self.hash = self.calcular_hash()
        self.minar(dificultad)

    def calcular_hash(self):
        contenido = json.dumps(
            [self.index, self.timestamp, self.lote, self.etapa,
             self.datos, self.hash_previo, self.nonce],
            sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(contenido.encode()).hexdigest()

    def minar(self, dificultad):
        """Prueba de trabajo: busca un nonce tal que el hash empiece con ceros."""
        while not self.hash.startswith("0" * dificultad):
            self.nonce += 1
            self.hash = self.calcular_hash()


class Cadena:
    def __init__(self, dificultad=2, tipo_arbol="splay"):
        if not isinstance(dificultad, int) or isinstance(dificultad, bool) \
                or not 0 <= dificultad <= MAX_DIFICULTAD:
            raise ErrorValidacion(f"La dificultad debe ser un entero entre 0 y {MAX_DIFICULTAD}.")
        if tipo_arbol not in ARBOLES:
            raise ErrorValidacion(f"Tipo de árbol desconocido: {tipo_arbol!r}. Opciones: {list(ARBOLES)}")
        self.dificultad = dificultad
        self.tipo_arbol = tipo_arbol
        self.bloques = []
        self.indice = ARBOLES[tipo_arbol]()   # lote -> [posiciones de sus bloques]

    # ---------- índice ----------
    def _indexar(self, bloque, indice):
        posiciones = indice.search(bloque.lote)
        if posiciones is None:
            indice.insert(bloque.lote, [bloque.index])
        else:
            posiciones.append(bloque.index)

    def reconstruir_indice(self, tipo_arbol=None):
        """Crea un índice nuevo recorriendo la cadena en orden. Lo deja activo y lo devuelve."""
        tipo = tipo_arbol or self.tipo_arbol
        if tipo not in ARBOLES:
            raise ErrorValidacion(f"Tipo de árbol desconocido: {tipo!r}.")
        indice = ARBOLES[tipo]()
        for b in self.bloques:
            self._indexar(b, indice)
        self.indice = indice
        self.tipo_arbol = tipo
        return indice

    # ---------- operaciones ----------
    def registrar(self, lote, etapa, datos):
        validar_lote(lote)
        validar_etapa(etapa)
        validar_datos(datos)
        if any(b.etapa == etapa for b in self.historial(lote)):
            raise ErrorValidacion(f"El lote {lote} ya tiene registrada la etapa {etapa!r}.")
        previo = self.bloques[-1].hash if self.bloques else "0"
        b = Bloque(len(self.bloques), lote, etapa, copy.deepcopy(datos), previo, self.dificultad)
        self.bloques.append(b)
        self._indexar(b, self.indice)
        return b

    def historial(self, lote):
        posiciones = self.indice.search(lote) or []
        return [self.bloques[i] for i in posiciones]

    def existe(self, lote):
        return self.indice.search(lote) is not None

    def estado_bloques(self):
        """Lista de (ok, motivo) por bloque. Recorre toda la cadena: O(B)."""
        estados = []
        for i, b in enumerate(self.bloques):
            esperado = self.bloques[i - 1].hash if i > 0 else "0"
            if b.index != i:
                estados.append((False, "El número de bloque no coincide con su posición."))
            elif b.hash != b.calcular_hash():
                estados.append((False, "El contenido no coincide con su hash: fue modificado."))
            elif not b.hash.startswith("0" * self.dificultad):
                estados.append((False, "El hash no cumple la prueba de trabajo."))
            elif b.hash_previo != esperado:
                estados.append((False, "No enlaza con el hash del bloque anterior."))
            else:
                estados.append((True, "Bloque íntegro."))
        return estados

    def es_valida(self):
        """True si todos los bloques son íntegros."""
        return all(ok for ok, _ in self.estado_bloques())
