# Análisis de complejidad

Notación: **n** = número de lotes distintos en el índice, **B** = número de bloques en la cadena,
**e** = etapas por lote (en promedio B = n·e), **Q** = número de consultas.

## 1. Índice `lote -> posiciones de bloques`

| Operación | BST | AVL | Splay |
|---|---|---|---|
| Búsqueda, peor caso (una operación) | O(n) | O(log n) | O(n) |
| Búsqueda, caso promedio / aleatorio | O(log n) | O(log n) | O(log n) |
| Búsqueda, **costo amortizado** | no aplica | no aplica | **O(log n)** |
| Inserción, peor caso | O(n) | O(log n) | O(n) |
| Inserción, amortizado | no aplica | no aplica | O(log n) |
| Espacio | O(n) | O(n) (+1 entero de altura por nodo) | O(n) (sin campos extra) |
| Operación dominante | comparaciones de claves al descender | comparaciones + rotaciones | comparaciones + rotaciones (splay) en **cada** acceso |

Puntos clave:
- **BST:** no se reequilibra. Con claves insertadas en orden creciente degenera en una lista (altura n) y cada búsqueda cuesta ~n/2 comparaciones.
- **AVL:** garantiza altura ≤ 1,4405·log₂(n+2) en todo momento. Cada inserción paga rotaciones, pero las búsquedas nunca modifican el árbol.
- **Splay:** una operación individual puede costar O(n), pero cualquier secuencia de m operaciones cuesta O(m log n) (análisis amortizado de Sleator y Tarjan). Además cumple la propiedad de **optimalidad estática** y la de **conjunto de trabajo**: si los accesos se concentran en pocos elementos o en elementos recientes, el costo por consulta baja a ~O(log k), con k el tamaño de ese conjunto. Pero **toda búsqueda reestructura el árbol**, lo que tiene un costo constante mayor.
- **Constante oculta:** en el recorrido top-down con zig-zig se hacen hasta dos comparaciones por nivel descendido; por eso, con accesos uniformes, el Splay cuesta aproximadamente 1,5 a 2 veces más comparaciones que el AVL, aunque ambos sean O(log n).

## 2. Cadena de bloques

| Operación | Tiempo | Espacio | Operación dominante |
|---|---|---|---|
| `registrar` | O(log n) (índice) + minado | O(1) por bloque | cálculo de hashes SHA-256 (minado: ~16^d intentos esperados con dificultad d) |
| `historial(lote)` | O(log n + e) | O(e) | búsqueda en el índice |
| `es_valida` | **Θ(B)** | O(1) | recalcular un SHA-256 por bloque |
| `reconstruir_indice` | O(B log n) amortizado/promedio | O(n) | B inserciones/búsquedas |
| Espacio total de la cadena | — | Θ(B) | — |

La validación de la cadena es lineal en el número de bloques e independiente del tipo de índice.

## 3. Costo de consultar, de punta a punta
`historial` = búsqueda en el índice (log n en promedio) + armar la lista de e bloques; la verificación de integridad (Θ(B)) se hace aparte. En la web se verifica en cada consulta por simplicidad; una versión de producción podría cachear el resultado hasta el siguiente registro.

## 4. Predicciones que se contrastan con los experimentos
1. BST con inserción aleatoria: ≈ 1,39·log₂ n comparaciones; con inserción ordenada: ≈ n/2.
2. AVL: ≈ log₂ n comparaciones por consulta, sin importar el patrón ni el orden de inserción.
3. Splay con accesos uniformes: O(log n), con constante mayor que AVL.
4. Splay con accesos concentrados o con repetición reciente: debería bajar claramente por debajo de AVL.
5. Verificar la cadena: tiempo lineal en B.
