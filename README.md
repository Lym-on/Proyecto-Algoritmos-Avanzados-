# Evaluación de árboles de búsqueda autoajustables aplicados a Blockchain

Mini blockchain en Python (SHA-256 + Proof of Work) y un índice `tx_id -> bloque`
implementado con tres árboles: **BST** (línea base), **AVL** y **Splay Tree**.
El benchmark mide comparaciones por consulta, altura y tiempo bajo distintos
patrones de acceso (uniforme, localidad 80/20 y Zipf).

## Estructura
- `blockchain.py`: bloques, minado, validación y generador reproducible de transacciones
- `trees/`: `bst.py`, `avl.py`, `splay.py`
- `benchmark.py`: comparación de árboles
- `tests/`: pruebas unitarias

## Uso
```
python main.py
python -m unittest discover -s tests -t .
```
