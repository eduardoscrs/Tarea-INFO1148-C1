# Analizador léxico de un subconjunto de Prolog

## Requisitos
- Python 3.10 o superior.
- No requiere dependencias externas.

## Ejecución
```bash
python3 lexer.py tests/valid.pl
python3 lexer.py tests/invalid.pl
```

El segundo comando termina con código 1 porque contiene errores léxicos recuperables.

## Convenciones
1. `+` y `-` son tokens de operador. El signo no pertenece al número.
2. Se reconocen enteros y reales con decimal y/o exponente.
3. Los operadores de varios caracteres tienen prioridad sobre los de un carácter.
4. `%` inicia comentario de línea; `/* ... */` inicia comentario de bloque.
5. Átomos simples empiezan con minúscula; variables con mayúscula o `_`.
6. `'...'` es átomo entre comillas; `"..."` es cadena.
7. Solo se aceptan escapes `\n`, `\t`, `\r`, `\\`, `\'`, `\"`.
8. `is` y `mod` se entregan como tokens propios.
9. No se realiza análisis sintáctico ni semántico.

## Tabla de lexemas
El lexer conserva índices para ATOMO, VARIABLE, CADENA y ATOMO_COMILLAS, evitando duplicados.
