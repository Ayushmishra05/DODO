"""
DODO Language — Lexer / Tokenizer
Scans source text and produces a list of Token objects.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import List


# ── Token types ──────────────────────────────────────────────────────────────

class TokenType(Enum):
    # Literals
    NUMBER = auto()
    STRING = auto()
    IDENT = auto()

    # Keywords
    DISP = auto()
    NUM = auto()
    DECI = auto()
    DECIP = auto()
    IF = auto()
    ELSE = auto()

    # Operators
    PLUS = auto()      # +
    MINUS = auto()     # -
    MUL = auto()       # *
    DIV = auto()       # /
    ASSIGN = auto()    # =
    EQ = auto()        # ==
    NEQ = auto()       # !=
    LT = auto()        # <
    GT = auto()        # >
    LTE = auto()       # <=
    GTE = auto()       # >=

    # Delimiters
    LBRACE = auto()    # {
    RBRACE = auto()    # }
    LPAREN = auto()    # (
    RPAREN = auto()    # )

    # Special
    NEWLINE = auto()
    EOF = auto()


KEYWORDS = {
    "disp": TokenType.DISP,
    "num": TokenType.NUM,
    "deci": TokenType.DECI,
    "decip": TokenType.DECIP,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
}


# ── Token data class ────────────────────────────────────────────────────────

@dataclass
class Token:
    type: TokenType
    value: object
    line: int
    col: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:{self.col})"


# ── Lexer ────────────────────────────────────────────────────────────────────

class LexerError(Exception):
    """Raised when the lexer encounters an unexpected character."""
    def __init__(self, message: str, line: int, col: int):
        super().__init__(f"[Line {line}, Col {col}] {message}")
        self.line = line
        self.col = col


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1

    # ── helpers ──────────────────────────────────────────────────────────

    def _peek(self) -> str | None:
        if self.pos < len(self.source):
            return self.source[self.pos]
        return None

    def _advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _match(self, expected: str) -> bool:
        if self.pos < len(self.source) and self.source[self.pos] == expected:
            self._advance()
            return True
        return False

    # ── main tokenise method ─────────────────────────────────────────────

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []

        while self.pos < len(self.source):
            ch = self._peek()

            # Skip spaces / tabs (but NOT newlines)
            if ch in (" ", "\t", "\r"):
                self._advance()
                continue

            # Newlines — emit a NEWLINE token (statement delimiter)
            if ch == "\n":
                tokens.append(Token(TokenType.NEWLINE, "\\n", self.line, self.col))
                self._advance()
                continue

            # Single-line comments: // …
            if ch == "/" and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == "/":
                while self.pos < len(self.source) and self._peek() != "\n":
                    self._advance()
                continue

            # Strings
            if ch == '"':
                tokens.append(self._read_string())
                continue

            # Numbers
            if ch.isdigit():
                tokens.append(self._read_number())
                continue

            # Identifiers / keywords
            if ch.isalpha() or ch == "_":
                tokens.append(self._read_identifier())
                continue

            # Two-char operators
            start_line, start_col = self.line, self.col
            if ch == "=" and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == "=":
                self._advance(); self._advance()
                tokens.append(Token(TokenType.EQ, "==", start_line, start_col))
                continue
            if ch == "!" and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == "=":
                self._advance(); self._advance()
                tokens.append(Token(TokenType.NEQ, "!=", start_line, start_col))
                continue
            if ch == "<" and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == "=":
                self._advance(); self._advance()
                tokens.append(Token(TokenType.LTE, "<=", start_line, start_col))
                continue
            if ch == ">" and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == "=":
                self._advance(); self._advance()
                tokens.append(Token(TokenType.GTE, ">=", start_line, start_col))
                continue

            # Single-char tokens
            single = {
                "+": TokenType.PLUS,
                "-": TokenType.MINUS,
                "*": TokenType.MUL,
                "/": TokenType.DIV,
                "=": TokenType.ASSIGN,
                "<": TokenType.LT,
                ">": TokenType.GT,
                "{": TokenType.LBRACE,
                "}": TokenType.RBRACE,
                "(": TokenType.LPAREN,
                ")": TokenType.RPAREN,
            }
            if ch in single:
                self._advance()
                tokens.append(Token(single[ch], ch, start_line, start_col))
                continue

            raise LexerError(f"Unexpected character: {ch!r}", self.line, self.col)

        tokens.append(Token(TokenType.EOF, None, self.line, self.col))
        return tokens

    # ── sub-scanners ─────────────────────────────────────────────────────

    def _read_string(self) -> Token:
        start_line, start_col = self.line, self.col
        self._advance()  # consume opening "
        chars: list[str] = []
        while self._peek() is not None and self._peek() != '"':
            if self._peek() == "\\":
                self._advance()
                esc = self._advance()
                escape_map = {"n": "\n", "t": "\t", "\\": "\\", '"': '"'}
                chars.append(escape_map.get(esc, esc))
            else:
                chars.append(self._advance())
        if self._peek() is None:
            raise LexerError("Unterminated string literal", start_line, start_col)
        self._advance()  # consume closing "
        return Token(TokenType.STRING, "".join(chars), start_line, start_col)

    def _read_number(self) -> Token:
        start_line, start_col = self.line, self.col
        chars: list[str] = []
        has_dot = False
        while self._peek() is not None and (self._peek().isdigit() or self._peek() == "."):
            if self._peek() == ".":
                if has_dot:
                    break
                has_dot = True
            chars.append(self._advance())
        text = "".join(chars)
        value = float(text) if has_dot else int(text)
        return Token(TokenType.NUMBER, value, start_line, start_col)

    def _read_identifier(self) -> Token:
        start_line, start_col = self.line, self.col
        chars: list[str] = []
        while self._peek() is not None and (self._peek().isalnum() or self._peek() == "_"):
            chars.append(self._advance())
        word = "".join(chars)
        ttype = KEYWORDS.get(word, TokenType.IDENT)
        return Token(ttype, word, start_line, start_col)
