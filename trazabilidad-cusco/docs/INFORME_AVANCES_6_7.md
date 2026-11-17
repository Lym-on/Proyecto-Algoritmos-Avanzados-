# Informe: Avance 6 (pruebas, complejidad, diseño) y Avance 7 (experimentos preliminares)

> Las cifras de comparaciones y alturas son deterministas (dependen solo de las semillas).
> Los tiempos son de la máquina donde se corrió; **vuelve a ejecutar y reemplaza los tiempos por los tuyos.**

## 1. Sistema integrado (flujo completo)
`generar_cadena` (instancias con semilla) → validación de entradas (`ErrorValidacion`) → registro en blockchain con índice intercambiable → consultas según patrón → verificación contra una referencia independiente (`errores = 0`) → métricas a CSV → tablas y gráficos (`graficos.py`). La misma cadena alimenta la web con QR (`app.py`).

## 2. Pruebas automatizadas (Avance 6)
`python -m unittest discover -s tests -t . -v` → **58 pruebas**.

| Archivo | Cobertura |
|---|---|
| `test_validacion.py` | códigos, etapas y datos inválidos; etapa repetida; registros rechazados sin efectos; parámetros inválidos |
| `test_cadena.py` | casos normales (historial, enlaces, prueba de trabajo, 3 árboles, reconstrucción de índice); límite (cadena vacía, un bloque, lote inexistente, unicode, dificultad 0); adversas (alterar datos/hash/enlace/lote/etapa, intercambiar o eliminar bloques, alterar y re-minar un bloque, hash sin prueba de trabajo) y una limitación documentada |
| `test_arboles.py` | árbol vacío, un elemento, claves duplicadas; **aleatorias con 5 semillas contra un `dict` de referencia**; recorrido inorden ordenado; inserción ordenada de 2 000 claves; degeneración del BST; cota de altura del AVL; propiedades del Splay (la clave accedida queda en la raíz; reacceso = 1 comparación) |
| `test_web.py` | páginas principales, no encontrados (404), búsqueda por lote/bloque/hash, entradas basura, alteración visible en la web y restauración, paginación fuera de rango, escape de HTML en los datos |
| `test_experimento.py` | reproducibilidad por semilla; patrones sesgados; coherencia de la cadena generada; los 3 árboles coinciden con la referencia; piloto pequeño correcto y reproducible |

Referencias usadas: diccionario de Python, recorrido inorden y cotas teóricas.

## 3. Complejidad
Ver `docs/ANALISIS_COMPLEJIDAD.md` (peor caso, promedio y amortizado, operaciones dominantes y espacio).

## 4. Diseño experimental y piloto
Ver `docs/DISENO_EXPERIMENTAL.md`. El piloto (`--modo piloto`) verifica corrección, coherencia y reproducibilidad antes del experimento completo (360 mediciones).

## 5. Resultados preliminares (N = 5 000 lotes, 15 000 bloques, 10 000 consultas, 5 repeticiones)
Comparaciones por consulta, inserción aleatoria:

| Patrón | BST | AVL | Splay | Splay vs AVL |
|---|---:|---:|---:|---:|
| uniforme | 15,27 | 11,53 | 21,06 | +83 % |
| 80_20 | 15,34 | 11,53 | 18,57 | +61 % |
| zipf | 14,71 | 11,07 | 12,28 | +11 % |
| rafaga | 15,24 | 11,53 | **6,37** | **−45 %** |

Inserción ordenada (caso adverso): BST **2 498,5** comparaciones/consulta (uniforme) frente a 11,4 del AVL; el Splay se mantiene en 7,1 – 21,8 según el patrón.

Otros datos: construir el índice cuesta ≈ 400 000 comparaciones con Splay frente a ≈ 226 000 con AVL (N = 5 000, aleatorio). Verificar toda la cadena tomó 1,4 ms (300 bloques), 13,5 ms (3 000) y 67,2 ms (15 000): crece de forma lineal.

Tablas y gráficos completos: `resultados/tablas_completo.md` y los PNG de `resultados/`.

## 6. Comparación con la teoría y tendencias
- **Coincide con la teoría:** el BST con inserción aleatoria queda cerca de 1,39·log₂ n (15,3 frente a ≈ 17 de la fórmula asintótica) y con inserción ordenada degenera a ≈ n/2 (2 498 ≈ 5 000/2). El AVL se mantiene en ≈ log₂ n sin importar patrón ni orden (11,4–11,5 para log₂ 5 000 = 12,3) y respeta su cota de altura. La verificación de la cadena es lineal.
- **El Splay no es siempre el mejor.** Con accesos uniformes o poco sesgados cuesta más que el AVL (constante mayor: reestructura en cada consulta y compara dos niveles por paso). Con Zipf casi empata (+11 %). Solo gana cuando hay **localidad temporal** (ráfagas): −45 % comparaciones y ≈ −17 % de tiempo frente a AVL (9,9 → 8,2 ms en N = 5 000), una mejora menor en tiempo porque las rotaciones tienen costo.
- **Inserción ordenada:** el Splay queda en una lista de altura N tras construirse, pero la primera consulta profunda la reestructura y el costo amortizado vuelve a ser logarítmico (21,8 frente a 21,1 con inserción aleatoria). Es el comportamiento amortizado previsto.
- **80_20 no ayudó al Splay:** el 20 % "caliente" de 5 000 lotes son 1 000 lotes, demasiados para que quepan cerca de la raíz; el beneficio aparece con conjuntos de trabajo pequeños.

## 7. Cuándo conviene cada alternativa
| Condición | Recomendación |
|---|---|
| Datos que se insertan en orden o sin control | Evitar BST |
| Consultas sin sesgo, o necesidad de peor caso garantizado | AVL |
| Consultas con ráfagas sobre pocos lotes (ej. varios escaneos del mismo lote) | Splay |
| Muchas inserciones y pocas consultas | AVL o BST aleatorio; el Splay construye con más comparaciones |

Implicación para la aplicación: si los escaneos reales son ráfagas, el Splay se justifica; si no, un AVL es la opción segura. Faltan datos reales de escaneos para decidirlo.

## 8. Limitaciones y dificultades pendientes
- Patrones de consulta sintéticos; no hay datos reales de uso.
- Tamaños hasta 5 000 lotes; no se probó con cientos de miles.
- Los tiempos incluyen el overhead de Python.
- El blockchain no valida la veracidad del dato inicial y no detecta que se quite el último bloque.
- Pendiente: lectura del QR desde el celular depende de la red local (firewall o WiFi que aísla dispositivos).

## 9. Evidencias para la segunda entrega
- [x] Implementación funcional (`cadena.py`, `trees/`, `app.py`)
- [x] Integración (cadena + índice + web + QR + generador + benchmark)
- [x] Pruebas automatizadas (`tests/`, 58 pruebas)
- [x] Análisis de complejidad (`docs/ANALISIS_COMPLEJIDAD.md`)
- [x] Experimentos preliminares (`resultados/`)
- [x] Documentación técnica (`README.md`, `docs/`)
- [ ] Capturas de pantalla de la web y de la ejecución de pruebas/benchmark (hazlas tú)
- [ ] Prueba del QR en un celular real (pendiente)
- [ ] Actualizar la bitácora con tus propias fechas y correcciones
