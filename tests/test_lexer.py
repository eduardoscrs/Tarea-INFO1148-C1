#!/usr/bin/env python3
"""
Suite de pruebas automatizadas para el analizador léxico de Prolog.
Cubre:
1. Pruebas válidas individuales por categoría.
2. Pruebas inválidas individuales (errores léxicos solicitados).
3. Automatización sobre el corpus de archivos (tests/corpus_valid y tests/corpus_invalid).
4. Verificación de archivos completos (valid.pl e invalid.pl).
5. Máxima coincidencia (longest match) y resolución de prioridades.
6. Deduplicación en la tabla de símbolos/lexemas.
"""

import sys
import unittest
from pathlib import Path

# Agregar directorio raíz para importar lexer
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from lexer import Lexer

VALID_IN_MEMORY = [
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

INVALID_IN_MEMORY = [
    "'sin cerrar", '"sin cerrar', "/* sin cerrar", "123abc", "1.2.3",
    "7e+", "@", "9foo_bar",
]


class TestPrologLexer(unittest.TestCase):

    def test_valid_in_memory(self):
        """Verifica cada categoría léxica válida en memoria."""
        for text, expected in VALID_IN_MEMORY:
            tokens, errors = Lexer(text).run()
            self.assertEqual(len(errors), 0, f"Error inesperado en {text!r}: {errors}")
            self.assertTrue(len(tokens) > 0, f"No se generó token para {text!r}")
            self.assertEqual(tokens[0].tipo, expected, f"Tipo incorrecto para {text!r}")

    def test_invalid_in_memory(self):
        """Verifica detección de errores léxicos representativos en memoria."""
        for text in INVALID_IN_MEMORY:
            tokens, errors = Lexer(text).run()
            self.assertTrue(len(errors) > 0, f"Se esperaba error léxico para {text!r}")

    def test_corpus_valid_files(self):
        """Lee y ejecuta automáticamente cada archivo .pl de tests/corpus_valid/."""
        corpus_dir = ROOT_DIR / "tests" / "corpus_valid"
        self.assertTrue(corpus_dir.exists(), f"Directorio no encontrado: {corpus_dir}")
        valid_files = sorted(corpus_dir.glob("*.pl"))
        self.assertGreaterEqual(len(valid_files), 20, "El corpus debe contener al menos 20 pruebas válidas")

        for fpath in valid_files:
            with self.subTest(file=fpath.name):
                content = fpath.read_text(encoding="utf-8")
                tokens, errors = Lexer(content).run()
                self.assertEqual(len(errors), 0, f"Archivo {fpath.name} produjo errores: {errors}")
                self.assertTrue(len(tokens) > 0, f"Archivo {fpath.name} no produjo tokens")

    def test_corpus_invalid_files(self):
        """Lee y ejecuta automáticamente cada archivo .pl de tests/corpus_invalid/."""
        corpus_dir = ROOT_DIR / "tests" / "corpus_invalid"
        self.assertTrue(corpus_dir.exists(), f"Directorio no encontrado: {corpus_dir}")
        invalid_files = sorted(corpus_dir.glob("*.pl"))
        self.assertGreaterEqual(len(invalid_files), 8, "El corpus debe contener al menos 8 pruebas inválidas")

        for fpath in invalid_files:
            with self.subTest(file=fpath.name):
                content = fpath.read_text(encoding="utf-8")
                tokens, errors = Lexer(content).run()
                self.assertTrue(len(errors) > 0, f"Archivo {fpath.name} debería reportar errores léxicos")

    def test_full_programs(self):
        """Verifica la ejecución de los 2 archivos completos (valid.pl e invalid.pl)."""
        # valid.pl: sin errores
        valid_file = ROOT_DIR / "tests" / "valid.pl"
        toks_v, errs_v = Lexer(valid_file.read_text(encoding="utf-8")).run()
        self.assertEqual(len(errs_v), 0, f"valid.pl no debe tener errores: {errs_v}")
        self.assertGreater(len(toks_v), 20, "valid.pl debe generar tokens representativos")

        # invalid.pl: múltiples errores recuperables
        invalid_file = ROOT_DIR / "tests" / "invalid.pl"
        toks_i, errs_i = Lexer(invalid_file.read_text(encoding="utf-8")).run()
        self.assertGreater(len(errs_i), 0, "invalid.pl debe contener errores léxicos")
        self.assertGreater(len(toks_i), 0, "invalid.pl debe recuperarse y generar tokens válidos")

    def test_longest_match_and_priorities(self):
        """Verifica la máxima coincidencia entre operadores compuestos y simples."""
        toks, errs = Lexer("=.. == =< >= // ** :- ?- \\== \\=").run()
        self.assertEqual(len(errs), 0)
        expected_types = [
            "DESCOMPONE", "IGUAL_ESTRICTO", "MENOR_IGUAL", "MAYOR_IGUAL",
            "DIV_ENTERA", "POTENCIA", "DOS_PUNTOS_GUION", "CONSULTA",
            "DISTINTO_ESTRICTO", "DISTINTO"
        ]
        self.assertEqual([t.tipo for t in toks], expected_types)

    def test_word_operators_vs_identifiers(self):
        """Verifica que palabras clave como prefijos de identificadores sigan siendo ATOMO."""
        # is_valido debe ser ATOMO, no IS + VARIABLE
        toks, errs = Lexer("is is_valido mod mod_func").run()
        self.assertEqual(len(errs), 0)
        self.assertEqual([t.tipo for t in toks], ["IS", "ATOMO", "MOD", "ATOMO"])

    def test_variable_priorities(self):
        """Verifica distinción entre variable anónima, variables nombradas y átomos."""
        toks, errs = Lexer("_ _X X x").run()
        self.assertEqual(len(errs), 0)
        self.assertEqual([t.tipo for t in toks], ["VARIABLE", "VARIABLE", "VARIABLE", "ATOMO"])

    def test_symbol_table_deduplication(self):
        """Verifica que las tablas de símbolos no dupliquen átomos ni variables."""
        lexer = Lexer("padre padre X X padre")
        toks, errs = lexer.run()
        self.assertEqual(len(errs), 0)
        self.assertEqual([t.atributo for t in toks], [1, 1, 1, 1, 1])
        self.assertEqual(len(lexer.symbols["ATOMO"]), 1)
        self.assertEqual(len(lexer.symbols["VARIABLE"]), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
