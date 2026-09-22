#!/usr/bin/env python3
"""
Analizador léxico para un subconjunto educativo de Prolog.

Convenciones:
- Los signos + y - son operadores, no forman parte del token NUMERO.
- Enteros: [0-9]+
- Reales: dígitos "." dígitos, opcionalmente con exponente, o dígitos con exponente.
- Átomos no entrecomillados: minúscula seguida de letras/dígitos/_.
- Variables: mayúscula o _ seguida de letras/dígitos/_.
- Átomo entre comillas simples y cadena entre comillas dobles permiten escapes
  \\n, \\t, \\r, \\\\, \\\', \\".
- Comentarios: % hasta fin de línea y /* ... */.
- Máxima coincidencia: se consume el lexema más largo posible.
- Prioridad: comentarios > literales/identificadores/números > operadores
  de varios caracteres > operadores de un carácter > delimitadores.
"""

from dataclasses import dataclass
import re
import sys

@dataclass
class Token:
    tipo: str
    lexema: str
    linea: int
    columna: int
    atributo: object = None

    def __str__(self):
        attr = "" if self.atributo is None else f", atributo={self.atributo!r}"
        return f"<{self.tipo}, {self.lexema!r}, {self.linea}, {self.columna}{attr}>"

@dataclass
class ErrorLexico:
    mensaje: str
    lexema: str
    linea: int
    columna: int

    def __str__(self):
        return f"[LÉXICO {self.linea}:{self.columna}] {self.mensaje}: {self.lexema!r}"

# Identificadores del subconjunto.
ATOM_RE = re.compile(r"[a-z][A-Za-z0-9_]*")
VAR_RE = re.compile(r"(?:[A-Z]|_)[A-Za-z0-9_]*")
INT_RE = re.compile(r"[0-9]+")
REAL_RE = re.compile(r"(?:[0-9]+\.[0-9]+(?:[eE][+-]?[0-9]+)?|[0-9]+[eE][+-]?[0-9]+)")

MULTI_OPS = [
    ":-", "?-", "-->",
    "\\==", "\\=", "=..", "==", "=<", ">=", "//", "**"
]
SINGLE_OPS = {
    "=": "IGUAL",
    "<": "MENOR",
    ">": "MAYOR",
    "+": "MAS",
    "-": "MENOS",
    "*": "POR",
    "/": "DIVISION",
    "!": "CORTE",
    ";": "PUNTO_Y_COMA",
    ",": "COMA",
}
DELIMS = {
    "(": "PARENTESIS_IZQ",
    ")": "PARENTESIS_DER",
    "[": "CORCHETE_IZQ",
    "]": "CORCHETE_DER",
    "{": "LLAVE_IZQ",
    "}": "LLAVE_DER",
    "|": "BARRA_VERTICAL",
    ".": "PUNTO",
}

OP_NAMES = {
    ":-": "DOS_PUNTOS_GUION",
    "?-": "CONSULTA",
    "-->": "DCG",
    "\\==": "DISTINTO_ESTRICTO",
    "\\=": "DISTINTO",
    "=..": "DESCOMPONE",
    "==": "IGUAL_ESTRICTO",
    "=<": "MENOR_IGUAL",
    ">=": "MAYOR_IGUAL",
    "//": "DIV_ENTERA",
    "**": "POTENCIA",
}

WORD_OPS = {"is": "IS", "mod": "MOD"}

ESCAPES = {"n", "t", "r", "\\", "'", '"'}
WHITESPACE = " \t\r\n\f\v"

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.i = 0
        self.line = 1
        self.col = 1
        self.tokens = []
        self.errors = []
        self.symbols = {
            "ATOMO": {},
            "VARIABLE": {},
            "CADENA": {},
            "ATOMO_COMILLAS": {},
        }

    def current(self):
        return self.source[self.i] if self.i < len(self.source) else ""

    def peek(self, n=1):
        j = self.i + n
        return self.source[j] if j < len(self.source) else ""

    def advance(self):
        c = self.current()
        if not c:
            return
        self.i += 1
        if c == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1

    def consume(self, text):
        for _ in text:
            self.advance()

    def format_symbol_table(self) -> str:
        lines = []
        for cat, table in self.symbols.items():
            if table:
                lines.append(f"  {cat}:")
                for lex, idx in sorted(table.items(), key=lambda x: x[1]):
                    lines.append(f"    [{idx}] {lex!r}")
        if not lines:
            return "  (tabla vacía)"
        return "\n".join(lines)

    def _is_bad_num_char(self):
        c = self.current()
        if not c:
            return False
        if c.isalnum() or c == "_":
            return True
        if c == "." and (self.peek().isalnum() or self.peek() == "_"):
            return True
        return False

    def add(self, tipo, lexema, line, col, attr=None):
        if tipo in self.symbols and attr is None:
            table = self.symbols[tipo]
            if lexema not in table:
                table[lexema] = len(table) + 1
            attr = table[lexema]
        self.tokens.append(Token(tipo, lexema, line, col, attr))

    def error(self, message, fragment, line=None, col=None):
        self.errors.append(ErrorLexico(message, fragment,
                                       self.line if line is None else line,
                                       self.col if col is None else col))

    def skip_layout_and_comments(self):
        while True:
            changed = False
            while self.current() and self.current() in WHITESPACE:
                changed = True
                self.advance()

            if self.current() == "%":
                changed = True
                while self.current() and self.current() != "\n":
                    self.advance()
                continue

            if self.current() == "/" and self.peek() == "*":
                changed = True
                sl, sc = self.line, self.col
                self.consume("/*")
                while self.current():
                    if self.current() == "*" and self.peek() == "/":
                        self.consume("*/")
                        break
                    self.advance()
                else:
                    fragment = self.source[self._index_from(sl, sc):self.i]
                    self.error("comentario de bloque sin cierre", fragment, sl, sc)
                continue

            if not changed:
                return

    def _index_from(self, line, col):
        # Solo se usa para diagnóstico; suficientemente simple para este lexer.
        # Reconstruye desde el principio.
        l, c = 1, 1
        for idx, ch in enumerate(self.source):
            if l == line and c == col:
                return idx
            if ch == "\n":
                l, c = l + 1, 1
            else:
                c += 1
        return len(self.source)

    def read_quoted(self, quote, tipo):
        sl, sc = self.line, self.col
        self.advance()  # quote
        chars = []
        while self.current():
            c = self.current()
            if c == quote:
                self.advance()
                lex = quote + "".join(chars) + quote
                self.add(tipo, lex, sl, sc)
                return

            if c == "\\":
                esc_col = self.col
                self.advance()
                nxt = self.current()
                if not nxt:
                    self.error("secuencia de escape sin terminar", "\\", self.line, esc_col)
                    return
                if nxt not in ESCAPES:
                    # Convención educativa: solo se aceptan los escapes definidos.
                    self.error("secuencia de escape no admitida", "\\" + nxt,
                               self.line, self.col - 1)
                    chars.append(nxt)
                    self.advance()
                    continue
                chars.append("\\" + nxt)
                self.advance()
                continue

            if c == "\n":
                # Permitimos salto de línea solo para simplificar recuperación;
                # sigue siendo error por literal sin cierre.
                self.error("literal sin cierre", quote, sl, sc)
                return

            chars.append(c)
            self.advance()

        self.error("literal sin cierre", quote, sl, sc)

    def read_number(self):
        sl, sc = self.line, self.col
        start = self.i
        m = REAL_RE.match(self.source, self.i)
        if m:
            lex = m.group(0)
            for _ in lex: self.advance()
            # Detectar continuación que no puede pertenecer al número.
            # Un punto solo es fin de cláusula Prolog y se deja como token PUNTO.
            # Solo es continuación inválida si es alfanumérico/_ o punto seguido de dígito (ej. 1.2.3).
            nxt = self.current()
            if nxt and (nxt.isalnum() or nxt == "_" or (nxt == "." and self.peek().isdigit())):
                while self._is_bad_num_char():
                    self.advance()
                bad = self.source[start:self.i]
                self.error("número mal formado", bad, sl, sc)
                return
            self.add("REAL", lex, sl, sc)
            return

        m = INT_RE.match(self.source, self.i)
        assert m is not None
        lex = m.group(0)
        for _ in lex: self.advance()

        # Exponente incompleto, parte decimal inválida o sufijo de identificador.
        if self.current() and self.current() in "eE":
            bad_start = self.i
            self.advance()
            if self.current() and self.current() in "+-":
                self.advance()
            if not self.current().isdigit():
                while self._is_bad_num_char() or (self.current() and self.current() in "+-"):
                    self.advance()
                bad = self.source[start:self.i]
                self.error("número mal formado", bad, sl, sc)
                return

        if self.current() == "." and self.peek().isdigit():
            # Esto debería haber coincidido con REAL_RE; se deja por robustez.
            while self._is_bad_num_char():
                self.advance()
            self.error("número mal formado", self.source[start:self.i], sl, sc)
            return

        if self.current() and (self.current().isalpha() or self.current() == "_"):
            while self._is_bad_num_char():
                self.advance()
            self.error("número mal formado", self.source[start:self.i], sl, sc)
            return

        self.add("ENTERO", lex, sl, sc)

    def read_identifier(self):
        sl, sc = self.line, self.col
        c = self.current()
        if c.islower():
            m = ATOM_RE.match(self.source, self.i)
            assert m is not None
            lex = m.group(0)
            for _ in lex: self.advance()
            if lex in WORD_OPS:
                self.add(WORD_OPS[lex], lex, sl, sc)
            else:
                self.add("ATOMO", lex, sl, sc)
        else:
            m = VAR_RE.match(self.source, self.i)
            assert m is not None
            lex = m.group(0)
            for _ in lex: self.advance()
            self.add("VARIABLE", lex, sl, sc)

    def run(self):
        while self.i < len(self.source):
            self.skip_layout_and_comments()
            if self.i >= len(self.source):
                break

            c = self.current()
            sl, sc = self.line, self.col

            if c == "'":
                self.read_quoted("'", "ATOMO_COMILLAS")
                continue
            if c == '"':
                self.read_quoted('"', "CADENA")
                continue
            if c.isdigit():
                self.read_number()
                continue
            if c.isalpha() or c == "_":
                self.read_identifier()
                continue

            # Operadores de longitud máxima.
            matched = False
            for op in MULTI_OPS:
                if self.source.startswith(op, self.i):
                    self.consume(op)
                    self.add(OP_NAMES[op], op, sl, sc)
                    matched = True
                    break
            if matched:
                continue

            # \+ tiene dos caracteres y debe reconocerse antes que cualquier error.
            if self.source.startswith("\\+", self.i):
                self.consume("\\+")
                self.add("NO", "\\+", sl, sc)
                continue

            if c in SINGLE_OPS:
                self.advance()
                self.add(SINGLE_OPS[c], c, sl, sc)
                continue

            if c in DELIMS:
                self.advance()
                self.add(DELIMS[c], c, sl, sc)
                continue

            # Símbolo no permitido en el subconjunto.
            self.error("carácter no admitido", c, sl, sc)
            self.advance()

        return self.tokens, self.errors

def lex_file(path):
    text = open(path, encoding="utf-8").read()
    return Lexer(text).run()

def main():
    if len(sys.argv) != 2:
        print(f"Uso: {sys.argv[0]} archivo.pl")
        raise SystemExit(2)
    lexer = Lexer(open(sys.argv[1], encoding="utf-8").read())
    tokens, errors = lexer.run()
    for t in tokens:
        print(t)
    print("\n--- TABLA DE LEXEMAS ---")
    print(lexer.format_symbol_table())
    if errors:
        print("\n--- ERRORES LÉXICOS ---")
        for e in errors:
            print(e)
        raise SystemExit(1)

if __name__ == "__main__":
    main()
