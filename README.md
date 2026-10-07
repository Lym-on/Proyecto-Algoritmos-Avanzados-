# Evaluación de árboles de búsqueda aplicados a una blockchain

Proyecto académico de **Algoritmos Avanzados** que compara tres estructuras de
datos para buscar transacciones dentro de una blockchain:

- **BST (Binary Search Tree):** árbol binario de búsqueda sin balanceo.
- **AVL:** árbol que mantiene una altura equilibrada mediante rotaciones.
- **Splay Tree:** árbol autoajustable que mueve a la raíz la clave consultada.

El proyecto genera una blockchain pequeña en Python, construye un índice con la
relación:

```text
ID de transacción (tx_id) -> número de bloque
```

Después ejecuta muchas búsquedas sobre cada árbol y compara su rendimiento bajo
distintos patrones de acceso. La finalidad es observar cómo cambia la eficiencia
de cada estructura según la distribución de las consultas.

## ¿Qué incluye la simulación?

### Blockchain

La blockchain implementada utiliza:

- Hashes **SHA-256**.
- **Proof of Work**: cada bloque se mina hasta obtener un hash con un número
  determinado de ceros iniciales.
- Encadenamiento mediante el hash del bloque anterior.
- Transacciones generadas aleatoriamente de forma reproducible mediante una
  semilla.
- Validación para detectar modificaciones en la cadena.

Esta implementación es educativa; no pretende ser una blockchain lista para
producción.

### Árboles de búsqueda

Cada árbol almacena el identificador de una transacción como clave y el índice
del bloque como valor.

| Estructura | Característica principal | Uso en el experimento |
| --- | --- | --- |
| BST | No realiza balanceo | Línea base de comparación |
| AVL | Mantiene la altura equilibrada | Búsquedas con altura controlada |
| Splay Tree | Reorganiza el árbol después de cada acceso | Consultas con claves frecuentes |

## Patrones de consulta

El benchmark utiliza tres escenarios:

1. **Uniforme:** todas las transacciones tienen la misma probabilidad de ser
   consultadas.
2. **Localidad 80/20:** el 80 % de las consultas se concentra en el 20 % más
   reciente de las transacciones.
3. **Zipf:** unas pocas transacciones reciben muchas consultas y el resto recibe
   pocas, simulando una distribución de popularidad.

Para cada escenario se registran:

- Comparaciones promedio por consulta.
- Altura final del árbol.
- Tiempo total de búsqueda.

## Estructura del proyecto

```text
.
├── blockchain.py          # Bloques, minado, validación y transacciones
├── benchmark.py           # Construcción del índice y comparación
├── main.py                # Punto de entrada del programa
├── trees/
│   ├── __init__.py        # Exporta BST, AVL y SplayTree
│   ├── node.py           # Nodo binario genérico
│   ├── bst.py             # Árbol binario de búsqueda
│   ├── avl.py             # Árbol AVL
│   └── splay.py           # Árbol Splay
└── tests/
    └── test_trees.py      # Pruebas unitarias
```

## Requisitos

- Python 3.8 o superior.
- No se requieren paquetes externos; el proyecto utiliza únicamente la
  biblioteca estándar de Python.

## Instalación y ejecución

Clona o descarga el repositorio y entra en su carpeta raíz:

```bash
cd Proyecto-Algoritmos-Avanzados-
```

Ejecuta el benchmark:

```bash
python main.py
```

La ejecución crea una blockchain de 200 bloques, con 10 transacciones por
bloque, y realiza 50,000 consultas por escenario.

## Ejecutar las pruebas

```bash
python -m unittest discover -s tests -t .
```

Las pruebas verifican las operaciones de los árboles, el balance del AVL, el
comportamiento de autoajuste del Splay y la validación de la blockchain.

## Personalizar el experimento

El benchmark puede ejecutarse desde Python con otros parámetros:

```python
from benchmark import run

run(
    n_blocks=100,
    tx_per_block=20,
    n_queries=10000,
    seed=7,
)
```

La semilla (`seed`) permite repetir el experimento con los mismos datos y
comparar los resultados de forma consistente.

## Interpretación esperada

- El **AVL** normalmente conserva una altura baja y estable.
- El **BST** puede volverse alto y menos eficiente si los datos se insertan en
  un orden desfavorable.
- El **Splay Tree** puede beneficiarse de los patrones de localidad, porque las
  claves consultadas con frecuencia se acercan a la raíz.

Los resultados dependen del tamaño de la blockchain, la semilla y el patrón de
consultas. Por eso deben analizarse comparando las tres estructuras bajo las
mismas condiciones.
