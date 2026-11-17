# Bitácora (borrador: complétala y corrígela con tus datos)

| Fecha | Qué se hizo | Problema / corrección |
|---|---|---|
| 2026-11-06 | Se definió la aplicación: trazabilidad de productos de Cusco con blockchain e índice Splay. | Se descartó la idea inicial (autocompletado, tienda) por alejarse del blockchain. |
| 2026-11-06 | Se creó el proyecto `blockchain_aplicacion`, el entorno virtual y se copió el código de los árboles. | `python` no se encontraba en PowerShell (alias de la Microsoft Store): se usó `py -m venv venv`. Se había generado un `requirements.txt` global por error y se rehízo dentro del entorno. |
| 2026-11-06 | Se implementó `cadena.py` (bloques, prueba de trabajo, índice, verificación) y `main.py`. | Faltaba la carpeta `trees/` al ejecutar: se agregaron los 5 archivos. |
| 2026-11-06 | Se creó la web con Flask, plantillas y generación de QR. | El celular no abrió la página: se revisaron firewall, red WiFi y uso de hotspot (**pendiente de confirmar**). |
| 2026-11-06 | Se agregó validación de entradas, `ErrorValidacion`, reconstrucción del índice y verificación reforzada (índice de bloque y prueba de trabajo). | Antes se aceptaban códigos vacíos, etapas repetidas y datos no serializables. |
| 2026-11-06 | Se escribieron 47 pruebas automatizadas, el generador con semillas, el benchmark y los gráficos. | Se usan semillas por texto para que el conjunto de lotes "populares" no coincida con el orden de inserción (evita un sesgo en el experimento). |
| 2026-11-06 | Se ejecutó el piloto (correcto y reproducible) y el experimento completo (360 mediciones). | Resultado inesperado: el Splay **no** supera al AVL con accesos uniformes ni 80/20; solo gana con ráfagas. Se documentó en el informe. |
| 2026-11-17 | El docente pidió que la interfaz se vea como una blockchain. Se rediseñó la web como explorador de bloques (inicio, cadena, detalle de bloque, lote, búsqueda). | Se agregó `estado_bloques()` para marcar cada bloque como íntegro, alterado o afectado, y pruebas de la web (`tests/test_web.py`). |

## Dificultades pendientes
- Confirmar el escaneo del QR desde un celular real.
- Conseguir (si es posible) datos reales de consultas o de productores.
- Decidir con el docente si la web es una demostración adicional del proyecto del Grupo 2.
