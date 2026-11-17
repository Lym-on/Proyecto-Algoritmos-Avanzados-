# Origen Cusco: trazabilidad con blockchain e índice autoajustable

Sistema de trazabilidad de productos (café, papa nativa, quinua) sobre una mini blockchain
en Python (SHA-256 + prueba de trabajo). Cada etapa de un lote (cosecha, secado, empaque...)
es un bloque. Un índice `código de lote -> bloques` permite consultar rápido; el índice es
intercambiable (BST, AVL o Splay Tree) y se evalúa experimentalmente. Una web con QR permite
al comprador verificar el historial desde el celular.

## Instalación (Windows, PowerShell)
```powershell
py -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
Linux/macOS: `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`

## Ejecución
| Qué | Comando |
|---|---|
| Prueba por consola | `python main.py` |
| Servidor web (explorador de bloques) | `python app.py` → http://localhost:5000 |
| Casos límite con valores | `python demo_casos_limite.py` |
| Generar QR (con el servidor en otra terminal) | `python generar_qr.py` |
| Pruebas automatizadas | `python -m unittest discover -s tests -t . -v` |
| Experimento piloto (segundos) | `python benchmark.py --modo piloto` |
| Experimento completo (~2-5 min) | `python benchmark.py --modo completo` |
| Tablas y gráficos | `python graficos.py --modo completo` |

## Módulos
| Archivo | Función |
|---|---|
| `trees/` | `BST`, `AVL`, `SplayTree` con `insert`, `search`, `height` y contador `comparisons` |
| `cadena.py` | `Bloque`, `Cadena` (registrar, historial, existe, es_valida, reconstruir_indice), validación de entradas (`ErrorValidacion`) |
| `generador.py` | Instancias sintéticas y patrones de consulta reproducibles por semilla |
| `benchmark.py` | Diseño experimental, medición, verificación y guardado de resultados |
| `graficos.py` | Tablas Markdown y gráficos PNG desde el CSV |
| `datos.py`, `app.py`, `templates/`, `generar_qr.py` | Explorador web de la cadena (estilo explorador de Bitcoin, tema oscuro) y QR |
| `demo_casos_limite.py` | Imprime con números los casos límite |
| `tests/` | Pruebas automatizadas (`unittest`) |
| `docs/` | Análisis de complejidad, diseño experimental, bitácora, informe de avances |

## Páginas del explorador
| Ruta | Muestra |
|---|---|
| `/` | Resumen (altura, lotes, prueba de trabajo, estado de la cadena), últimos bloques y lotes |
| `/cadena` | Todos los bloques, paginados |
| `/bloque/<n>` | Detalle: hash, hash previo, nonce, datos, estado y hash recalculado si fue alterado |
| `/lote/<codigo>` | Historial de un producto (destino del QR) |
| `/buscar?q=` | Busca por código de lote, número de bloque o prefijo de hash |
| `/demo/alterar`, `/demo/restaurar` | Simula y revierte una alteración (solo demostración) |

## Parámetros
**`Cadena(dificultad=2, tipo_arbol="splay")`**: `dificultad` entero 0-5 (ceros iniciales del hash);
`tipo_arbol` ∈ `bst`, `avl`, `splay`.

**`registrar(lote, etapa, datos)`**
- `lote`: texto, MAYÚSCULAS/dígitos/guiones, máx. 60 (ej. `CAFE-2026-0001`).
- `etapa`: texto no vacío, máx. 60; no puede repetirse dentro del mismo lote.
- `datos`: diccionario con claves de texto y valores serializables a JSON.
- Si algo es inválido lanza `ErrorValidacion` y no modifica la cadena.

**`generar_cadena(n_lotes, etapas_por_lote=3, semilla=0, orden="aleatorio")`**
`orden` ∈ `aleatorio`, `ordenado` (orden de inserción de los lotes). Máx. 7 etapas por lote.

**`generar_consultas(lotes, patron, n_consultas, semilla)`**
`patron` ∈ `uniforme`, `80_20`, `zipf`, `rafaga` (ver `docs/DISENO_EXPERIMENTAL.md`).

## Formatos de entrada y salida
- **Entrada:** código de lote (URL `/lote/<codigo>` o campo de texto en `/`).
- **Salida web:** línea de tiempo del lote con sello ✅ (cadena íntegra) o ❌ (alterada).
- **Salida de experimentos:** `resultados/crudo_<modo>.csv`, una fila por (N, orden, patrón, árbol, repetición), columnas:
  `modo, n_lotes, n_bloques, orden, patron, arbol, repeticion, semilla, consultas, comps_construccion, comps_totales, comps_por_consulta, altura_inicial, altura_final, t_construccion_ms, t_consultas_ms, t_verificacion_cadena_ms, errores`.

## Cómo reproducir las pruebas
1. Instalar dependencias y activar el entorno (arriba).
2. `python -m unittest discover -s tests -t . -v` (todas deben pasar).
3. `python benchmark.py --modo piloto` debe terminar con `Verificación ... OK` y `Reproducibilidad ... OK`.
4. `python benchmark.py --modo completo` y luego `python graficos.py --modo completo`.
Las métricas de comparaciones y alturas dependen solo de las semillas (deterministas); los tiempos varían según la máquina.

## Organización de resultados
```
resultados/
  crudo_piloto.csv / crudo_completo.csv     datos de cada medición
  entorno_<modo>.txt                        Python, sistema, configuración y semilla
  tablas_<modo>.md                          tablas resumen (media ± desviación)
  comparaciones_<orden>_<modo>.png          gráficos de comparaciones por consulta
  tiempo_<orden>_<modo>.png                 gráficos de tiempo de consultas
```

## Limitaciones
- El blockchain garantiza que un dato no cambia después de registrado, no que el dato inicial sea verdadero.
- Quitar el último bloque no se detecta con una sola copia de la cadena (no hay bloque siguiente que lo delate).
- Es una sola máquina; no hay red de nodos ni consenso.
