"""Compara BST, AVL y Splay Tree indexando las transacciones de un blockchain.

Índice: tx_id (hash) -> número de bloque.
Escenarios de consulta:
  - uniforme: todas las transacciones con la misma probabilidad
  - localidad: 80% de las consultas van al 20% de las transacciones
               (las más recientes), como pasa en una blockchain real
  - zipf: pocas transacciones muy consultadas, cola larga
"""
import random
import time

from blockchain import build_chain
from trees import AVL, BST, SplayTree


def build_index(tree_cls, txs):
    t = tree_cls()
    for tx_id, block_idx in txs:
        t.insert(tx_id, block_idx)
    return t


def make_queries(txs, kind, n_queries, rng):
    ids = [tx for tx, _ in txs]  # ya están en orden cronológico
    if kind == "uniforme":
        return [rng.choice(ids) for _ in range(n_queries)]
    if kind == "localidad":
        cut = int(len(ids) * 0.8)
        old, recent = ids[:cut], ids[cut:]
        return [rng.choice(recent if rng.random() < 0.8 else old) for _ in range(n_queries)]
    if kind == "zipf":
        weights = [1 / (i + 1) for i in range(len(ids))]
        hot = ids[:]
        rng.shuffle(hot)
        return rng.choices(hot, weights=weights, k=n_queries)
    raise ValueError(kind)


def run(n_blocks=200, tx_per_block=10, n_queries=50_000, seed=42):
    bc = build_chain(n_blocks, tx_per_block, difficulty=2, seed=seed)
    txs = [(tx["id"], b.index) for b in bc.chain for tx in b.transactions]
    print(f"Blockchain válida: {bc.is_valid()} | bloques: {len(bc.chain)} | transacciones: {len(txs)}")
    print(f"Consultas por escenario: {n_queries} | semilla: {seed}\n")

    header = f"{'Escenario':<11}{'Árbol':<8}{'Comp/consulta':>15}{'Altura':>8}{'Tiempo (s)':>12}"
    print(header)
    print("-" * len(header))
    for kind in ("uniforme", "localidad", "zipf"):
        queries = make_queries(txs, kind, n_queries, random.Random(seed))
        for cls in (BST, AVL, SplayTree):
            tree = build_index(cls, txs)
            tree.comparisons = 0  # medir solo las búsquedas
            t0 = time.perf_counter()
            for q in queries:
                tree.search(q)
            dt = time.perf_counter() - t0
            print(f"{kind:<11}{cls.__name__:<8}{tree.comparisons / n_queries:>15.2f}{tree.height():>8}{dt:>12.3f}")
        print()


if __name__ == "__main__":
    run()
