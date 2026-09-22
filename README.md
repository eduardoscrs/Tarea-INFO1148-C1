# Analizador Léxico para un Subconjunto de Prolog

Implementación de un analizador léxico (*lexer*) para un subconjunto formal del lenguaje **Prolog**, desarrollado para el curso **Teoría de la Computación (INFO1148)**.

El analizador integra fundamentos formales de la Teoría de la Computación: alfabetos, lenguajes regulares, expresiones regulares, autómatas finitos (AFN/AFD), construcción de subconjuntos, minimización y resolución de máxima coincidencia (*longest match*).

---

## Requisitos y Dependencias

- **Python 3.10 o superior**.
- **Sin dependencias externas**: desarrollado utilizando exclusivamente la biblioteca estándar de Python (`re`, `dataclasses`, `sys`, `unittest`, `pathlib`).

---

## Estructura del Repositorio

```text
├── lexer.py                 # Código fuente del analizador léxico
├── README.md                # Instrucciones de ejecución y documentación
├── docs/
│   ├── informe.md           # Informe técnico en formato Markdown
│   └── Formato Informe Tarea.pdf  # Plantilla oficial del informe
└── tests/
    ├── test_lexer.py        # Suite de pruebas unitarias automatizadas (unittest)
    ├── valid.pl             # Programa Prolog completo sin errores léxicos
    ├── invalid.pl           # Archivo Prolog con múltiples errores recuperables
    ├── corpus_valid/        # 20 archivos de prueba independientes (casos válidos)
    │   ├── valid_01.pl ... valid_20.pl
    └── corpus_invalid/      # 8 archivos de prueba independientes (casos inválidos)
        ├── invalid_01.pl ... invalid_08.pl
```

---

## Instrucciones de Ejecución

### 1. Analizar un archivo Prolog
Para analizar cualquier archivo fuente Prolog e imprimir los tokens reconocidos, la tabla de lexemas y los posibles errores:

```bash
python lexer.py ruta/al/archivo.pl
```

#### Ejemplos incluidos:
```bash
# Archivo completo válido (código de salida 0):
python lexer.py tests/valid.pl

# Archivo con errores recuperables (código de salida 1):
python lexer.py tests/invalid.pl

# Archivo individual del corpus:
python lexer.py tests/corpus_valid/valid_09.pl
python lexer.py tests/corpus_invalid/invalid_03.pl
```

### 2. Ejecutar la suite de pruebas automatizadas
Para ejecutar automáticamente todas las pruebas unitarias, validando la totalidad del corpus (`tests/corpus_valid/` y `tests/corpus_invalid/`), máxima coincidencia y deduplicación:

```bash
python tests/test_lexer.py
```
*(O de forma equivalente: `python -m unittest tests/test_lexer.py`)*

---

## Formato de Salida

Cada token generado posee la estructura:
```text
<TIPO_TOKEN, 'lexema', línea, columna, atributo>
```
*(El campo `atributo` representa el índice asignado en la tabla de símbolos deduplicada para identificadores y literales).*

Al finalizar el recorrido, el analizador muestra la sección:
- **`--- TABLA DE LEXEMAS ---`**: Catálogo deduplicado de átomos, variables y literales con su identificador numérico único.
- **`--- ERRORES LÉXICOS ---`**: Reporte detallado de anomalías con ubicación (`línea:columna`), mensaje descriptivo y fragmento exacto no reconocido, continuando el análisis (*recuperación local*).

---

## Decisiones de Diseño y Convenciones

1. **Máxima coincidencia (*Longest Match*):** Se consume siempre el lexema admisible más largo. Por ejemplo, `:-` produce `DOS_PUNTOS_GUION` y no `:` seguido de `-`; `==` produce `IGUAL_ESTRICTO` y no dos tokens `=`.
2. **Signos aritméticos y números:** `+` y `-` se tratan consistentemente como operadores aritméticos separados para evitar ambigüedades con operaciones binarias (`10 - 2` vs `10` `-2`). Los reales requieren dígitos tras el punto (`3.14` es `REAL`; `3.` se tokeniza como `ENTERO` y `PUNTO`).
3. **Identificadores:** Átomos comienzan con minúscula (`[a-z]`); variables comienzan con mayúscula (`[A-Z]`) o guion bajo (`_`). La variable anónima `_` es tratada como `VARIABLE`.
4. **Operadores de palabra:** `is` y `mod` son reconocidos como tokens operadores independientes cuando coinciden exactamente con la palabra clave; prefijos como `is_valido` continúan reconociéndose como átomos.
5. **Comentarios y layout:** Se ignoran espacios y tabulaciones conservando la posición de línea y columna. `%` define comentarios de una línea y `/* ... */` comentarios de bloque.
