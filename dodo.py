#!/usr/bin/env python3
"""
DODO Language — CLI Entry Point

Usage:
    python dodo.py <file.dodo>    Run a DODO program
    python dodo.py                Launch interactive REPL
"""

import sys
import os

# Ensure the project root is on the path so `dodo` package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dodo.lexer import Lexer, LexerError
from dodo.parser import Parser, ParserError
from dodo.interpreter import Interpreter, RuntimeError_


BANNER = r"""
  ____   ___  ____   ___
 |  _ \ / _ \|  _ \ / _ \
 | | | | | | | | | | | | |
 | |_| | |_| | |_| | |_| |
 |____/ \___/|____/ \___/

 DODO Programming Language v1.0
 Type 'exit' to quit.
"""


def run_source(source: str, interpreter: Interpreter):
    """Lex → Parse → Interpret a block of DODO source code."""
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    interpreter.run(ast)


def run_file(filepath: str):
    """Execute a .dodo file."""
    if not os.path.isfile(filepath):
        print(f"Error: File not found — {filepath}")
        sys.exit(1)
    if not filepath.endswith(".dodo"):
        print("Warning: File does not have a .dodo extension.")
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()
    interpreter = Interpreter()
    try:
        run_source(source, interpreter)
    except (LexerError, ParserError, RuntimeError_) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def repl():
    """Interactive REPL for the DODO language."""
    print(BANNER)
    interpreter = Interpreter()
    while True:
        try:
            line = input("dodo> ")
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        if line.strip().lower() in ("exit", "quit"):
            print("Bye!")
            break
        if not line.strip():
            continue
        try:
            run_source(line, interpreter)
        except (LexerError, ParserError, RuntimeError_) as e:
            print(f"Error: {e}")


def main():
    if len(sys.argv) > 1:
        run_file(sys.argv[1])
    else:
        repl()


if __name__ == "__main__":
    main()
