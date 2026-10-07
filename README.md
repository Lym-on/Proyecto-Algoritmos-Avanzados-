# Evaluación de Árboles de Búsqueda Autoajustables aplicada a un Índice Autenticado de Estado

Proyecto de Algoritmos Avanzados: evaluación experimental de estructuras de búsqueda para indexar transacciones de blockchain (tx_id → bloque).

## Objetivo

Comparar empíricamente el costo de búsqueda y reorganización de:
1. **BST** — árbol binario de búsqueda simple (sin balanceo)
2. **AVL** — árbol balanceado estrictamente (O(log n) garantizado)
3. **Splay Tree** — autoajustable, amortizado O(log n)
4. **BaselineTree** — árbol estático balanceado por punto medio (construcción óptima en altura)
5. **OptimalBST (Knuth DP)** — óptimo offline via programación dinámica O(n²)

El modelo de costo considera:
- **Costo de búsqueda**: comparaciones/profundidad del nodo
- **Costo de reorganización**: rotaciones (Splay) o recomputación de hashes (Merkle)
- **Modelo dinámico**: Σ access_cost + λ · Σ reorg_cost

## Estructura del Proyecto

```
├── blockchain.py          # Mini blockchain con PoW (SHA-256) y transacciones reproducibles
├── benchmark.py           # Motor de experimentos con métricas completas
├── main.py               # Entrada simple
├── workloads.py          # Generadores de consultas parametrizados
├── experiments/
│   └── run.py            # Pipeline reproducible (CSV/JSON/manifest)
├── analysis/
│   └── plot.py           # Visualización desde resultados CSV
├── trees/
│   ├── __init__.py
│   ├── node.py           # Nodo base con contadores
│   ├── bst.py            # BST simple
│   ├── avl.py            # AVL con rotaciones contadas
│   ├── splay.py          # Splay top-down (zig/zig-zig/zig-zag corregidos)
│   ├── baseline.py       # Árbol estático balanceado por mediana
│   └── knuth_dp.py       # Optimal BST: O(n³) directo + O(n²) Knuth
├── tests/
│   ├── test_trees.py     # BST/AVL/Splay/Blockchain básicos
│   ├── test_splay.py     # 14 tests exhaustivos Splay (zig-zig, amortizado, etc.)
│   ├── test_knuth.py     # 12 tests Knuth DP vs fuerza bruta (n≤10)
│   └── test_workloads.py # 14 tests generadores de consultas
├── results/              # CSV/JSON/manifest de experimentos
├── plots/                # Gráficas generadas
└── README.md
```

## Complejidades

| Estructura | Búsqueda | Inserción | Eliminación | Espacio | Nota |
|------------|----------|-----------|-------------|---------|------|
| BST | O(n) peor / O(log n) prom | O(n) | O(n) | O(n) | Degrada a lista |
| AVL | O(log n) | O(log n) | O(log n) | O(n) | Balanceo estricto |
| Splay | O(n) peor / O(log n) **amortizado** | O(log n) amort | O(log n) amort | O(n) | Autoajustable |
| Baseline | O(log n) | N/A (estático) | N/A | O(n) | Óptimo en altura |
| OptimalBST | O(log n) esperado | N/A (offline) | N/A | O(n) | Óptimo para frecuencias dadas |

## Workloads (Patrones de Acceso)

| Tipo | Parámetros | Descripción |
|------|------------|-------------|
| `uniform` | — | Todas las claves igual probabilidad |
| `locality` | `hot_fraction=0.2`, `query_hot_fraction=0.8` | 20% claves reciben 80% consultas |
| `zipf` | `alpha ∈ {0.5, 1.0, 1.5, 2.0}` | Zipf 1/rank^α |
| `sequential_asc` | — | 0,1,2... adversarial para BST |
| `sequential_desc` | — | n-1,n-2... |
| `sequential_zigzag` | — | 0,n-1,1,n-2... |
| `hot_switch` | `switch_every=1000`, `hot_fraction=0.1` | Conjunto caliente rotativo |

## Métricas Registradas

Por experimento (mismo seed, misma secuencia de consultas para todos los algoritmos):
- `comparisons_total`, `comparisons_avg`
- `time_total`, `time_per_query`
- `height`, `avg_depth`, `max_depth`, `p95_depth`, `p99_depth`
- `rotations`, `rotations_per_access` (Splay)
- `rehashes`, `rehashes_per_access` (para Merkle futuro)
- `cost_access` = comparaciones
- `cost_reorg` = λ × rotaciones
- `cost_total` = cost_access + cost_reorg
- `normalized_cost` = cost_total / cost_optimal

## Cómo Ejecutar

### Benchmark rápido (main.py)
```bash
python main.py
```

### Tests unitarios
```bash
python -m unittest discover -s tests -t . -v
```

### Experimentos reproducibles (recomendado)
```bash
# Quick test (2 tamaños, 1 seed, 3 workloads)
python -m experiments.run --quick

# Experimento completo
python -m experiments.run \
  --sizes 100 500 1000 2000 \
  --seeds 42 123 456 \
  --lambdas 0.0 0.1 1.0 10.0 \
  --queries 5000 \
  --output results
```

### Generar gráficas
```bash
python -m analysis.plot results/experiment_results_YYYYMMDD_HHMMSS.csv -o plots
```

## Reproducibilidad

Cada experimento genera en `results/`:
- `experiment_results_TIMESTAMP.csv` — tabla completa
- `experiment_results_TIMESTAMP.json` — con metadatos
- `manifest_TIMESTAMP.json` — configuración exacta (tamaños, seeds, lambdas, workloads, git commit)

La misma semilla produce **exactamente la misma secuencia de consultas** para todos los algoritmos.

## Resultados Experimentales (Resumen)

Ejecutando `python -m experiments.run --quick` (n=100,500; seed=42; λ=1.0):

| Workload | BST | AVL | Splay | Baseline | OptimalBST |
|----------|-----|-----|-------|----------|------------|
| uniform | 1.20 | 1.01 | 2.21 | 1.20 | **1.00** |
| zipf (α=1.0) | 1.08 | 0.97 | 2.23 | 1.08 | **1.00** |
| locality | 1.55 | 1.28 | 2.08 | 1.55 | **1.00** |

**Observaciones clave**:
- **OptimalBST** es la baseline teórica (ratio=1.0)
- **AVL** supera a BST y Baseline en casi todos los casos
- **Splay** incurre costo de reorganización alto (rotaciones); beneficioso solo con alta localidad y λ bajo
- **BST** degrada en secuencial (no mostrado en quick test)

## Interpretación

El proyecto permite responder experimentalmente:
1. **¿Cuándo Splay supera a estático?** Cuando localidad es alta y λ es bajo (reorganización barata)
2. **¿Cuándo AVL es mejor?** En distribuciones uniformes/moderadas con λ medio/alto
3. **¿Cuánto cuesta reorganización?** Controlado por λ; visible en `cost_reorg` vs `cost_access`
4. **¿Cómo afecta Zipf?** α alto → más skew → Splay mejora relativo, OptimalBST aprovecha frecuencias
5. **Ratio vs óptimo** — `normalized_cost` cuantifica la brecha

## Próximos Pasos / Extensiones

- [ ] Integración completa Merkle (hashes recomputados por rotación)
- [ ] Hibridación: estimación de frecuencias online + DP periódico
- [ ] Treap por pesos / layout Huffman
- [ ] Benchmarks con n > 5000 (requiere optimizar Knuth DP)

## Autor

Álvaro Ayte — Algoritmos Avanzados 2026