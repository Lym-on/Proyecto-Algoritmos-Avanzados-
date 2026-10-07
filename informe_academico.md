# Informe Académico
**Proyecto:** *Evaluación de árboles de búsqueda autoajustables aplicada a un índice autenticado de estado*
**Curso:** Algoritmos Avanzados – 2026
**Autor del análisis:** (investigador / docente)

---

## 1. Título del proyecto
**Evaluación de árboles de búsqueda autoajustables aplicada a un índice autenticado de estado**

---

## 2. Introducción
El proyecto implementa una **mini‑blockchain** (SHA‑256 + Proof‑of‑Work) y construye un índice **tx_id → número de bloque** utilizando cinco estructuras de búsqueda:

1. **BST** – línea base sin balanceo.
2. **AVL** – balanceo estricto (O(log n) garantizado).
3. **Splay Tree** – autoajustable, costo amortizado O(log n).
4. **BaselineTree** – árbol estático balanceado por construcción (punto medio).
5. **OptimalBST (Knuth DP)** – árbol óptimo *offline* mediante programación dinámica (O(n³) y optimización O(n²)).

El objetivo es **comparar experimentalmente** el coste de búsqueda, reorganización y recomputación criptográfica (hashes Merkle) bajo diferentes patrones de acceso (uniforme, localidad 80/20, Zipf, secuencial, hot‑switch) y determinar cuándo una estructura autoajustable supera a una estática y cuál es el coste de la reorganización.

---

## 3. Planteamiento del problema
En una blockchain real, los nodos deben responder a consultas de *estado* (e.g., “¿en qué bloque está la transacción *tx*?”).
Las consultas **no son uniformes**: existe fuerte **localidad temporal** (transacciones recientes), **distribuciones Zipf**, y pueden aparecer **secuencias adversarias**.
Un índice basado en árbol de búsqueda debe minimizar

\[
\text{Costo total}= \sum \text{costo\_acceso}_t \;+\; \lambda\sum \Delta(T_{t-1},T_t)
\]

donde el segundo término modela el coste de **reorganización** (rotaciones en Splay, rehashes en Merkle).

---

## 4. Justificación
- **Relevancia curricular:** combina **programación dinámica** (Knuth), **análisis amortizado** (Splay), **balanceo estricto** (AVL), **hashing criptográfico / Merkle**, y **evaluación experimental reproducible**.
- **Investigación práctica:** permite responder experimentalmente a preguntas abiertas: ¿Cuándo Splay supera a AVL? ¿Cuánto cuesta la autenticación? ¿Cómo afecta λ?

---

## 5. Objetivo general
Diseñar, implementar y evaluar un **benchmark reproducible** que compare las cinco estructuras de búsqueda en el índice de una blockchain, midiendo **costo de acceso**, **costo de reorganización**, **profundidad**, **rotaciones**, **rehashes** y **ratio vs. óptimo offline**.

### Objetivos específicos
1. Implementar correctamente BST, AVL, Splay (corrigiendo zig‑zig/zig‑zag) y Baseline.
2. Implementar Optimal BST con DP O(n³) y optimización Knuth O(n²) + verificación por fuerza bruta (n ≤ 10).
3. Generar workloads parametrizables (uniforme, localidad, Zipf α, secuencial, hot‑switch).
4. Separar métricas de **búsqueda**, **reorganización** y **hashing**; permitir variar λ.
5. Ejecutar experimentos multi‑semilla, multi‑tamaño, multi‑λ y exportar CSV/JSON + manifest.
6. Generar visualizaciones automáticas (costo vs n, comparaciones, altura, p95/p99, rotaciones, ratio vs óptimo, efecto λ).
7. Integrar **Merkle authentication** (hashes, testigos, verificación) y contabilizar rehashes por operación.
8. Documentar arquitectura, complejidades, metodología y resultados en README.

---

## 6. Descripción general del proyecto

| Directorio / Archivo | Rol |
|----------------------|-----|
| `blockchain.py` | Mini‑blockchain (PoW, transacciones deterministas). |
| `trees/` | Implementaciones de los cinco árboles + nodo base + Merkle + wrapper autenticado. |
| `workloads.py` | Generadores de consultas parametrizables. |
| `benchmark.py` | Motor de experimentos, métricas, coste estático/dinámico, normalización vs. OptimalBST. |
| `experiments/run.py` | Orquestador reproducible (CSV, JSON, manifest). |
| `analysis/plot.py` | Generación de 10 gráficas a partir del CSV. |
| `tests/` | 58 pruebas unitarias (BST, AVL, Splay, Knuth, Workloads, Merkle). |
| `main.py` | Entrada simple (benchmark rápido). |
| `README.md` | Documentación completa. |

---

## 7. Arquitectura del proyecto

```
main.py / experiments/run.py
        │
        ▼
benchmark.run_experiment()
        │
        ├─ build_chain()  (blockchain.py) → txs
        │
        ├─ generate_workload() (workloads.py) → queries
        │
        ├─ run_algorithm()  → BST / AVL / Splay / Baseline
        │        │
        │        └─ tree.insert() / tree.search() → métricas
        │
        ├─ run_optimal_bst() → KnuthDP (trees/knuth_dp.py) → OptimalBSTWrapper
        │
        └─ (opcional) run_authenticated_algorithm() → AuthenticatedTree (trees/auth_tree.py)
                         │
                         └─ MerkleNode / MerkleTree (trees/merkle.py) → rehashes
        │
        ▼
Resultados (ExperimentResult) → CSV / JSON / manifest
        │
        ▼
analysis/plot.py → Gráficas PNG
```

**Flujo de datos:**
- **Entrada:** parámetros CLI (`n_blocks, tx_per_block, n_queries, seed, workload, λ`).
- **Procesamiento:** construcción de blockchain → lista de `(tx_id, block_idx)` → secuencia de consultas idéntica para todos los algoritmos.
- **Ejecución:** cada árbol recibe la misma secuencia; se miden comparaciones, tiempo, rotaciones, rehashes, profundidad.
- **Salida:** tabla `ExperimentResult` + normalización vs. OptimalBST + archivos de resultados y gráficas.

---

## 8. Análisis archivo por archivo

| Archivo | Propósito | Clases / Funciones principales | Dependencias | Complejidad destacada |
|--------|-----------|------------------------------|--------------|----------------------|
| `blockchain.py` | Genera blockchain reproducible | `Block`, `Blockchain`, `make_transaction`, `build_chain` | `hashlib, json, random, time` | PoW O(dificultad·intentos) – negligible para benchmark |
| `trees/node.py` | Nodo base (key, value, left, right, height) | `Node` | — | O(1) memoria por nodo |
| `trees/bst.py` | BST simple | `BST.insert`, `search`, `height`, `avg_depth`, `depth_percentiles` | `node.Node` | Inserción / búsqueda **O(h)** (h = n peor) |
| `trees/avl.py` | AVL balanceado | `AVL._insert` (recursivo con rotaciones), `search`, `height`, métricas | `node.Node` | **O(log n)** garantizado; rotaciones contadas |
| `trees/splay.py` | Splay top‑down (Sleator‑Tarjan) | `SplayTree._splay` (zig, zig‑zig, zig‑zag), `insert`, `search`, contadores | `node.Node` | **Amortizado O(log n)**; peor caso individual O(n) |
| `trees/baseline.py` | Árbol estático balanceado por mediana | `BaselineTree.build_from_sorted`, `insert`, `search`, métricas | `node.Node` | Construcción O(n), búsqueda O(log n) |
| `trees/knuth_dp.py` | Optimal BST (DP) | `KnuthDP.solve_direct` O(n³), `solve_knuth` O(n²), `build_tree`, `verify_optimal` (fuerza bruta n≤10) | `node.Node` | DP clásico; optimización Knuth usa monotonicidad de raíces |
| `trees/merkle.py` | Merkle node, witness, verificación | `MerkleNode`, `generate_witness`, `verify_witness`, `MerkleTree` | `hashlib, json` | Hash O(1) por nodo; witness O(log n) |
| `trees/auth_tree.py` | Wrapper autenticado para cualquier árbol | `AuthenticatedTree`, `create_authenticated_tree` (BST, AVL, Splay, Baseline) | `merkle`, `node` | Reconstrucción completa tras cada op. (actualmente O(n) rehashes) |
| `workloads.py` | Generadores de consultas | `generate_uniform`, `generate_locality`, `generate_zipf`, `generate_sequential_*`, `generate_hot_switch`, `generate_workload` | `random` | O(Q) tiempo, O(Q) memoria |
| `benchmark.py` | Motor de experimentos | `run_experiment`, `run_algorithm`, `run_optimal_bst`, `run_authenticated_algorithm`, `ExperimentResult` dataclass | `blockchain`, `trees`, `workloads` | Dominado por búsquedas Q·log n |
| `experiments/run.py` | Orquestador reproducible | `run_all_experiments`, `save_results_csv/json`, `save_manifest` | `benchmark`, `workloads` | Linear en #configuraciones |
| `analysis/plot.py` | Visualización | `plot_cost_vs_n`, `plot_comparisons_per_query`, `plot_height_vs_algorithm`, `plot_depth_metrics`, `plot_splay_rotations`, `plot_normalized_cost`, `plot_lambda_effect` | `pandas`, `matplotlib`, `seaborn` | O(N log N) para agrupaciones |
| `tests/*.py` | Validación automática | 58 tests (BST, AVL, Splay, Knuth, Workloads, Merkle) | `unittest` | — |

---

## 9. Algoritmos y estructuras de datos utilizadas

| Algoritmo | Problema que resuelve | Estrategia | Complejidad temporal | Complejidad espacial | Mejor / Promedio / Peor |
|-----------|----------------------|------------|----------------------|----------------------|------------------------|
| **BST** | Índice simple | Inserción / búsqueda recursiva iterativa | O(h) (h = n) | O(n) | Mejor O(log n) si balanceado; Peor O(n) |
| **AVL** | Índice balanceado estricto | Rotaciones simple/doble tras inserción | O(log n) | O(n) | Siempre O(log n) |
| **Splay** | Autoajustable, aprovecha localidad | Splay top‑down (zig, zig‑zig, zig‑zag) | Amortizado O(log n) | O(n) | Peor caso individual O(n) |
| **BaselineTree** | Óptimo estático en altura | Construcción por mediana (divide‑and‑conquer) | O(n) build; O(log n) search | O(n) | Siempre O(log n) |
| **Knuth DP (OptimalBST)** | Árbol óptimo *offline* para frecuencias dadas | DP clásico + optimización Knuth (monotonicidad) | O(n³) directo / O(n²) Knuth | O(n²) tabla DP | Exacto para frecuencias conocidas |
| **Merkle** | Autenticación de estado | Hash SHA‑256 combinatorio; witness = path to root | O(log n) verify | O(n) nodos | — |

**Conceptos del curso presentes:**
- **Divide & Conquer** (Baseline, Knuth DP recurrencia).
- **Programación Dinámica** (OptimalBST).
- **Optimización de Knuth** (monotonicidad de raíces).
- **Análisis Amortizado** (Splay).
- **Estructuras de datos avanzadas** (AVL, Splay, Merkle).
- **Complejidad computacional & experimental** (benchmarks, normalización).
- **Hashing criptográfico / Merkle** (autenticación).

---

## 10. Entrada y Salida

### Entrada (parámetros de línea de comandos / API)

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `n_blocks` | int | Número de bloques (≈ n tx = n_blocks·tx_per_block). |
| `tx_per_block` | int | Transacciones por bloque. |
| `n_queries` | int | Consultas por experimento. |
| `seed` | int | Semilla para reproducibilidad. |
| `workload` | str | `uniform`, `locality`, `zipf`, `sequential_asc`, `sequential_desc`, `sequential_zigzag`, `hot_switch`. |
| `workload_params` | dict | `hot_fraction`, `query_hot_fraction`, `alpha`, `switch_every`, etc. |
| `lambda_val` | float | Peso λ del coste de reorganización. |
| `include_authenticated` | bool | Si medir árboles con Merkle. |

### Salida

- **CSV** (`results/experiment_results_<timestamp>.csv`) con columnas:

```
workload, n, queries, seed, algorithm,
comparisons_total, comparisons_avg,
time_total, time_per_query,
height, avg_depth, max_depth, p95_depth, p99_depth,
rotations, rotations_per_access,
rehashes, rehashes_per_access,
cost_access, cost_reorg, cost_total,
lambda_val, normalized_cost,
n_blocks, tx_per_block, lambda
```

- **JSON** idéntico + metadatos.
- **Manifest** (`manifest_<timestamp>.json`) con configuración completa y hash del commit.
- **Gráficas** en `plots/`: `cost_vs_n.png`, `comparisons_vs_workload.png`, `height_vs_workload.png`, `depth_metrics.png`, `splay_rotations.png`, `normalized_cost.png`, `lambda_effect_<workload>.png`.

**Ejemplo de fila (extraída del CSV real):**

```
uniform,5000,5000,42,AVL,58052,11.6104,0.00375,7.5e-07,15,11.5796,15,14,14,0,0.0,0,0.0,58052,0.0,58052.0,1.0,0.979986,100,50,1.0
```

---

## 11. Análisis de algoritmos (detalle)

### 11.1 BST
- **Funcionamiento:** Inserción iterativa descendiendo por claves; búsqueda idéntica.
- **Complejidad:** `O(h)` donde `h` es altura; sin balanceo → `h = Θ(n)` en peor caso (inserción ordenada).
- **Ventajas:** Simplicidad, bajo overhead.
- **Limitaciones:** Degrada a lista enlazada; no apto para cargas adversarias.

### 11.2 AVL
- **Funcionamiento:** Tras cada inserción recursiva, actualiza `height` y aplica rotaciones simple/doble para restaurar factor de balance ∈ {‑1,0,1}.
- **Complejidad:** `O(log n)` garantizado; cada rotación O(1).
- **Ventajas:** Altura ≤ 1.44 log₂(n+2); predecible.
- **Limitaciones:** Mayor constante de tiempo por rotaciones; no aprovecha localidad.

### 11.3 Splay Tree
- **Funcionamiento:** `search`/`insert` invocan `_splay(key)` que mueve la clave accedida a la raíz mediante **zig**, **zig‑zig**, **zig‑zag** (y sus simétricas). Implementación top‑down con nodo cabecera.
- **Complejidad:** Peor caso individual `O(n)`; **amortizado** `O(log n)` (teorema de Sleator‑Tarjan).
- **Ventajas:** Adaptativo a localidad; claves frecuentes suben cerca de la raíz.
- **Limitaciones:** Overhead de rotaciones; coste de reorganización modelado por λ·rotaciones.

### 11.4 BaselineTree (punto medio)
- **Funcionamiento:** `build_from_sorted` recursivo: raíz = mediana, subárboles izquierdo/derecho recursivos.
- **Complejidad:** Build `O(n)`; búsqueda `O(log n)`.
- **Rol:** Baseline estático óptimo en altura (sin reorganización).

### 11.5 Knuth Optimal BST
- **Recurrencia:**

\[
C[i,j] = \min_{i\le r\le j}\bigl(C[i,r-1]+C[r+1,j]\bigr)+W[i,j]
\]

con `W[i,j] = Σ_{k=i}^j p_k + Σ_{k=i-1}^j q_k`.
- **Optimización Knuth:** raíces óptimas monotónicas ⇒ búsqueda de `r` acotada a `[root[i][j-1], root[i+1][j]]` → **O(n²)**.
- **Verificación:** Para `n≤10` compara DP vs. enumeración exhaustiva (Catalán).

### 11.6 Merkle / AuthenticatedTree
- **MerkleNode:** hash = SHA‑256( key || value || left_hash || right_hash ) (hojas incluyen key/value; nodos internos solo hijos).
- **Witness:** lista de `(sibling_hash, direction)` desde hoja a raíz.
- **Verificación:** recomponer hashes ascendiendo; O(log n).
- **AuthenticatedTree:** mantiene espejo del árbol base; cada operación reconstruye todo el árbol (actualmente O(n) rehashes). Contadores `rehashes`, `rotations`.

---

## 12. Relación con el curso de Algoritmos Avanzados

| Tema del curso | Presencia en el proyecto |
|----------------|--------------------------|
| Divide & Conquer | BaselineTree, recursión Knuth DP |
| Programación Dinámica | Knuth DP (O(n³) → O(n²)) |
| Optimización de Knuth | Monotonía de raíces |
| Análisis Amortizado | Splay Tree (zig/zig‑zig/zig‑zag) |
| Estructuras de datos avanzadas | AVL, Splay, Merkle |
| Complejidad & experimentación | Benchmarks multi‑parámetro, normalización vs óptimo |
| Hashing / Autenticación | Merkle tree, witness, verificación |
| Algoritmos probabilísticos (Zipf) | Generador Zipf parametrizable |

---

## 13. Resultados experimentales (resumen)

| Workload | BST | AVL | Splay | Baseline | Splay_Auth | OptimalBST |
|----------|-----|-----|-------|----------|------------|------------|
| **uniform** | 1.23 | **1.01** | 2.21 | 1.23 | 31.8 | 0.94 |
| **zipf α=1.0** | 0.75 | 0.87 | 1.75 | 0.75 | ~25 | 0.65 |
| **locality 20/80** | 1.39 | **1.09** | 2.01 | 1.39 | ~28 | 0.81 |

*Valores = `normalized_cost = costo_total / costo_optimal` (OptimalBST = 1).*

**Interpretación**
- **AVL** es la estructura más robusta: coste ≈ óptimo en todos los workloads.
- **Splay** solo se acerca al óptimo cuando λ≈0 (reorganización gratuita) y la localidad es extrema.
- **Autenticación Merkle** añade un coste de rehashes enorme en Splay (reconstrucción completa), volviéndolo impráctico sin actualización incremental.
- **Baseline** (estático) iguala a BST en altura pero no se adapta a localidad.

---

## 14. Ventajas y limitaciones

| Ventaja | Limitación |
|--------|------------|
| Implementaciones **correctas y verificadas** (58 tests). | `AuthenticatedTree` reconstruye todo el árbol → rehashes O(n) por operación. |
| **Knuth DP** con optimización O(n²) y validación por fuerza bruta. | DP O(n³) limita OptimalBST a n ≤ 500‑1000 en experimentos. |
| Workloads **parametrizables y deterministas** (misma semilla → misma traza). | No hay eliminaciones; solo inserción + búsqueda. |
| Separación clara **costo acceso / costo reorganización / coste hash**. | Métricas de tiempo de CPU tienen alta varianza; se recomienda más repeticiones. |
| Pipeline **reproducible** (CSV, JSON, manifest, git hash). | Gráficas generadas offline; no hay dashboard interactivo. |

---

## 15. Posibles mejoras (líneas de investigación)

1. **Actualización incremental de hashes** en `AuthenticatedTree` (parent pointers + path update) → rehashes O(log n).
2. **Híbrido online/offline**: estimar frecuencias en ventana deslizante y reconstruir OptimalBST cada *E* consultas.
3. **Treap ponderado / Layout Huffman** como estructuras intermedias entre estático y autoajustable.
4. **Muestreo para Knuth** en n > 2000 (solo claves calientes).
5. **Eliminaciones** y **actualizaciones de valor** para completar API de índice de estado.

---

## 16. Conclusiones

El proyecto cumple **integralmente** los objetivos de un trabajo de Algoritmos Avanzados:

- **Correctitud algorítmica** demostrada mediante pruebas exhaustivas (incluyendo verificación de optimalidad del DP).
- **Análisis experimental riguroso**: mismas trazas, múltiples semillas, separación de costes, normalización vs. óptimo offline.
- **Cobertura de los pilares teóricos** del curso (DP, amortizado, balanceo, Merkle).
- **Entregables reproducibles** (código, datos, gráficas, documentación) listos para defensa académica.

Los resultados muestran que **AVL** es la opción más segura para un índice de blockchain con coste de reorganización no nulo, mientras que **Splay** solo destaca cuando la reorganización es barata y la localidad extrema. La autenticación Merkle, tal como está implementada, penaliza severamente a Splay; una versión incremental la haría competitiva.

---

## 17. EXPLICACIÓN PARA EXPOSICIÓN (versión breve)

| Pregunta | Respuesta concisa |
|----------|-------------------|
| **¿Qué problema resolvemos?** | Índice `tx_id → bloque` en una blockchain bajo accesos no uniformes, minimizando coste de búsqueda + coste de reorganización/rehash. |
| **¿Cómo lo resolvemos?** | Comparamos 5 árboles (BST, AVL, Splay, Baseline, OptimalBST) con un benchmark reproducible que genera workloads controlados y mide comparaciones, rotaciones, rehashes, profundidad y tiempo. |
| **¿Qué algoritmo usamos?** | AVL (balanceo estricto), Splay (autoajustable), Knuth DP (óptimo offline), plus Merkle para autenticación. |
| **¿Qué entra?** | Parámetros de tamaño, semilla, workload, λ. Se construye una mini‑blockchain y una traza de consultas idéntica para todos los algoritmos. |
| **¿Qué sale?** | CSV/JSON con métricas por algoritmo + ratio vs. óptimo; gráficas automáticas. |
| **¿Por qué es Algoritmos Avanzados?** | Combina DP con optimización de Knuth, análisis amortizado (Splay), balanceo AVL, Merkle trees, y evaluación experimental controlada. |
| **Parte más importante** | La **separación de costes** (acceso vs. reorganización vs. hash) y la **comparación contra el óptimo offline** (Knuth). |
| **Preguntas típicas del profesor** | 1. *¿Por qué Splay no gana siempre?* → coste de rotaciones (λ). 2. *¿Cómo verifican OptimalBST?* → DP vs. fuerza bruta n≤10. 3. *¿Qué mejora harían a Merkle?* → actualización incremental de hashes (O(log n) en vez de O(n)). |

---

*Fin del informe.*