import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))
from lexer import Lexer

VALID = [
    ("padre", "ATOMO"), ("persona_1", "ATOMO"), ("X", "VARIABLE"),
    ("_Temporal", "VARIABLE"), ("_", "VARIABLE"), ("123", "ENTERO"),
    ("3.14", "REAL"), ("1.2e-3", "REAL"), ("'Juan Pérez'", "ATOMO_COMILLAS"),
    ('"Hola mundo"', "CADENA"), (":-", "DOS_PUNTOS_GUION"), ("?-", "CONSULTA"),
    ("-->", "DCG"), ("=..", "DESCOMPONE"), ("\\=", "DISTINTO"),
    ("==", "IGUAL_ESTRICTO"), ("=<", "MENOR_IGUAL"), (">=", "MAYOR_IGUAL"),
    ("//", "DIV_ENTERA"), ("**", "POTENCIA"), ("is", "IS"), ("mod", "MOD"),
    ("\\+", "NO"), ("!", "CORTE"), (";", "PUNTO_Y_COMA"), ("|", "BARRA_VERTICAL"),
    (".", "PUNTO"), ("[a]", "CORCHETE_IZQ"), ("{a}", "LLAVE_IZQ"),
]

INVALID = [
    "'sin cerrar", '"sin cerrar', "/* sin cerrar", "123abc", "1.2.3",
    "7e+", "@", "9foo_bar",
]

def test_valid_cases():
    for text, expected in VALID:
        tokens, errors = Lexer(text).run()
        assert not errors, (text, errors)
        assert tokens and tokens[0].tipo == expected, (text, tokens)

def test_invalid_cases():
    for text in INVALID:
        tokens, errors = Lexer(text).run()
        assert errors, text

def test_longest_match():
    toks, errs = Lexer("=.. == =< >= // ** :- ?-").run()
    assert not errs
    assert [t.tipo for t in toks] == [
        "DESCOMPONE", "IGUAL_ESTRICTO", "MENOR_IGUAL", "MAYOR_IGUAL",
        "DIV_ENTERA", "POTENCIA", "DOS_PUNTOS_GUION", "CONSULTA"
    ]

def test_symbol_table_deduplication():
    toks, errs = Lexer("padre padre X X padre").run()
    assert not errs
    assert [t.atributo for t in toks] == [1,1,1,1,1]

if __name__ == '__main__':
    test_valid_cases(); test_invalid_cases(); test_longest_match(); test_symbol_table_deduplication()
    print('OK: pruebas léxicas')
