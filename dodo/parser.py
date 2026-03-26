"""
DODO Language — Parser
Recursive-descent parser that converts a token stream into an AST.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from dodo.lexer import Token, TokenType, LexerError


# ═══════════════════════════════════════════════════════════════════════════
#  AST Node Definitions
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class NumberLiteral:
    value: object  # int or float

@dataclass
class StringLiteral:
    value: str

@dataclass
class Identifier:
    name: str

@dataclass
class BinaryOp:
    left: object
    op: str
    right: object

@dataclass
class UnaryOp:
    op: str
    operand: object

@dataclass
class DispStatement:
    expression: object

@dataclass
class VarDeclaration:
    var_type: str   # "num", "deci", "decip"
    name: str
    value: object   # expression

@dataclass
class Assignment:
    name: str
    value: object

@dataclass
class IfStatement:
    condition: object
    body: List[object]
    else_body: Optional[List[object]] = field(default=None)

@dataclass
class Program:
    statements: List[object]


# ═══════════════════════════════════════════════════════════════════════════
#  Parser
# ═══════════════════════════════════════════════════════════════════════════

class ParserError(Exception):
    def __init__(self, message: str, token: Token):
        super().__init__(f"[Line {token.line}, Col {token.col}] {message}")
        self.token = token


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    # ── helpers ──────────────────────────────────────────────────────────

    def _current(self) -> Token:
        return self.tokens[self.pos]

    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def _check(self, *types: TokenType) -> bool:
        return self._current().type in types

    def _match(self, *types: TokenType) -> Optional[Token]:
        if self._current().type in types:
            return self._advance()
        return None

    def _expect(self, ttype: TokenType, msg: str) -> Token:
        tok = self._match(ttype)
        if tok is None:
            raise ParserError(msg, self._current())
        return tok

    def _skip_newlines(self):
        while self._current().type == TokenType.NEWLINE:
            self._advance()

    # ── entry point ──────────────────────────────────────────────────────

    def parse(self) -> Program:
        self._skip_newlines()
        stmts: List[object] = []
        while not self._check(TokenType.EOF):
            stmts.append(self._statement())
            self._skip_newlines()
        return Program(stmts)

    # ── statements ───────────────────────────────────────────────────────

    def _statement(self) -> object:
        tok = self._current()

        if tok.type == TokenType.DISP:
            return self._disp_statement()

        if tok.type in (TokenType.NUM, TokenType.DECI, TokenType.DECIP):
            return self._var_declaration()

        if tok.type == TokenType.IF:
            return self._if_statement()

        if tok.type == TokenType.IDENT:
            return self._assignment_or_expr()

        raise ParserError(f"Unexpected token: {tok.value!r}", tok)

    # disp <expr>
    def _disp_statement(self) -> DispStatement:
        self._advance()  # consume 'disp'
        expr = self._expression()
        return DispStatement(expr)

    # num|deci|decip IDENT = <expr>
    def _var_declaration(self) -> VarDeclaration:
        type_tok = self._advance()
        name_tok = self._expect(TokenType.IDENT, "Expected variable name after type keyword")
        self._expect(TokenType.ASSIGN, "Expected '=' in variable declaration")
        value = self._expression()
        return VarDeclaration(type_tok.value, name_tok.value, value)

    # IDENT = <expr>
    def _assignment_or_expr(self) -> object:
        # Look ahead: if IDENT followed by '=', it's an assignment
        if self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].type == TokenType.ASSIGN:
            name_tok = self._advance()
            self._advance()  # consume '='
            value = self._expression()
            return Assignment(name_tok.value, value)
        # Otherwise treat as expression statement (future-proof)
        return self._expression()

    # if <expr> { stmts } (else { stmts })?
    def _if_statement(self) -> IfStatement:
        self._advance()  # consume 'if'
        condition = self._expression()
        self._skip_newlines()
        self._expect(TokenType.LBRACE, "Expected '{' after if condition")
        body = self._block()
        self._expect(TokenType.RBRACE, "Expected '}' to close if block")

        else_body = None
        # Check for else (possibly after newlines)
        self._skip_newlines()
        if self._match(TokenType.ELSE):
            self._skip_newlines()
            self._expect(TokenType.LBRACE, "Expected '{' after else")
            else_body = self._block()
            self._expect(TokenType.RBRACE, "Expected '}' to close else block")

        return IfStatement(condition, body, else_body)

    def _block(self) -> List[object]:
        stmts: List[object] = []
        self._skip_newlines()
        while not self._check(TokenType.RBRACE, TokenType.EOF):
            stmts.append(self._statement())
            self._skip_newlines()
        return stmts

    # ── expressions (precedence climbing) ────────────────────────────────

    def _expression(self) -> object:
        return self._comparison()

    def _comparison(self) -> object:
        left = self._addition()
        while self._check(TokenType.EQ, TokenType.NEQ, TokenType.LT, TokenType.GT, TokenType.LTE, TokenType.GTE):
            op_tok = self._advance()
            right = self._addition()
            left = BinaryOp(left, op_tok.value, right)
        return left

    def _addition(self) -> object:
        left = self._multiplication()
        while self._check(TokenType.PLUS, TokenType.MINUS):
            op_tok = self._advance()
            right = self._multiplication()
            left = BinaryOp(left, op_tok.value, right)
        return left

    def _multiplication(self) -> object:
        left = self._unary()
        while self._check(TokenType.MUL, TokenType.DIV):
            op_tok = self._advance()
            right = self._unary()
            left = BinaryOp(left, op_tok.value, right)
        return left

    def _unary(self) -> object:
        if self._check(TokenType.MINUS):
            op_tok = self._advance()
            operand = self._unary()
            return UnaryOp(op_tok.value, operand)
        return self._primary()

    def _primary(self) -> object:
        tok = self._current()

        if tok.type == TokenType.NUMBER:
            self._advance()
            return NumberLiteral(tok.value)

        if tok.type == TokenType.STRING:
            self._advance()
            return StringLiteral(tok.value)

        if tok.type == TokenType.IDENT:
            self._advance()
            return Identifier(tok.name if hasattr(tok, "name") else tok.value)

        if tok.type == TokenType.LPAREN:
            self._advance()
            expr = self._expression()
            self._expect(TokenType.RPAREN, "Expected ')' after expression")
            return expr

        raise ParserError(f"Unexpected token in expression: {tok.value!r}", tok)
