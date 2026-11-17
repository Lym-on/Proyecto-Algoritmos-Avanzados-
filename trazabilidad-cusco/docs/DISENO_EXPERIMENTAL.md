# Diseño experimental

## Pregunta
¿Qué estructura de índice conviene para consultar lotes de una cadena de trazabilidad: BST, AVL o Splay Tree, y bajo qué condiciones?

## Variables
| Tipo | Variable | Valores |
|---|---|---|
| Factor | Estructura | BST, AVL, Splay |
| Factor | Tamaño N (lotes) | 100, 1 000, 5 000 (con 3 etapas cada uno: 300, 3 000 y 15 000 bloques) |
| Factor | Orden de inserción de lotes | `aleatorio`, `ordenado` (creciente, caso adverso para BST) |
| Factor | Patrón de consulta | `uniforme`, `80_20`, `zipf`, `rafaga` |
| Controlada | Consultas por ejecución | 10 000 (2 000 en el piloto) |
| Controlada | Etapas por lote | 3 |
| Controlada | Dificultad de minado | 0 (no afecta al índice; acelera la generación) |
| Controlada | Mismas consultas y misma cadena para los 3 árboles | comparación pareada |
| Repetición | Semillas | 2026 … 2030 (5 repeticiones; 2 en el piloto) |

## Patrones de consulta
- **uniforme:** todos los lotes con igual probabilidad (caso sin sesgo).
- **80_20:** el 80 % de las consultas va al 20 % de los lotes (elegidos al azar, independientes del orden de inserción).
- **zipf:** probabilidad ∝ 1/rango^1,1 (popularidad muy sesgada y estática).
- **rafaga:** localidad temporal: con probabilidad 0,9 se repite un lote de los 10 consultados más recientemente (ej. varios compradores escaneando el mismo lote en un mercado).

## Métricas
`comps_por_consulta` (métrica principal, independiente de la máquina), `comps_construccion`,
`altura_inicial` y `altura_final`, `t_construccion_ms`, `t_consultas_ms`,
`t_verificacion_cadena_ms`, `errores`.

## Procedimiento de medición
1. Se genera la cadena con la semilla (`generar_cadena`) y se construye la referencia `lote -> posiciones` sin usar árboles.
2. Se mide el tiempo de `es_valida()`.
3. Para cada patrón se generan las consultas con la semilla (`generar_consultas`).
4. Para cada árbol: se construye el índice (`reconstruir_indice`), se pone a cero el contador, se ejecutan las consultas midiendo tiempo con `time.perf_counter`.
5. **Verificación:** una segunda pasada compara cada resultado con la referencia (`errores` debe ser 0). Va fuera del tiempo medido.
6. BST y AVL no cambian al buscar, así que se construyen una vez por instancia; el Splay se reconstruye por cada patrón porque cada búsqueda lo modifica.
7. Total completo: 3 N × 2 órdenes × 5 repeticiones × 4 patrones × 3 árboles = **360 mediciones**.

## Almacenamiento
CSV en `resultados/crudo_<modo>.csv` y entorno en `resultados/entorno_<modo>.txt` (Python, sistema, configuración, semilla base).

## Experimento piloto (`python benchmark.py --modo piloto`)
Misma tubería con N ∈ {100, 500}, 2 repeticiones y 2 000 consultas. Comprueba automáticamente:
1. **Corrección:** `errores == 0` en todas las filas.
2. **Coherencia:** bloques = 3·N; altura AVL ≤ 1,4405·log₂(N+2); BST con inserción ordenada tiene altura N; comparaciones > 0.
3. **Reproducibilidad:** se ejecuta dos veces y las métricas deterministas (comparaciones y alturas) deben coincidir exactamente.

## Amenazas a la validez
- Se cuentan comparaciones de claves; el Splay top-down compara además el nieto en cada zig-zig, lo que infla su contador frente a "niveles recorridos".
- Los tiempos incluyen el overhead del intérprete de Python y varían entre máquinas; por eso la métrica principal son las comparaciones.
- Los patrones son modelos sintéticos de uso; no hay datos reales de escaneos.
- Tamaños hasta 5 000 lotes: las tendencias para tamaños mucho mayores se extrapolan.
