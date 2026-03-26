"""
DODO Language — Interpreter
Tree-walking evaluator that executes the AST produced by the parser.
"""

from decimal import Decimal, getcontext
from dodo.parser import (
    Program, DispStatement, VarDeclaration, Assignment,
    IfStatement, NumberLiteral, StringLiteral, Identifier,
    BinaryOp, UnaryOp,
)

# Allow high precision for `decip`
getcontext().prec = 50


class RuntimeError_(Exception):
    """DODO runtime error."""
    pass


class Environment:
    """Variable store that tracks both values and their declared types."""

    def __init__(self):
        self.vars: dict[str, object] = {}
        self.types: dict[str, str] = {}      # name → "num" | "deci" | "decip"

    def declare(self, name: str, var_type: str, value: object):
        self.vars[name] = value
        self.types[name] = var_type

    def get(self, name: str) -> object:
        if name not in self.vars:
            raise RuntimeError_(f"Undefined variable: '{name}'")
        return self.vars[name]

    def set(self, name: str, value: object):
        if name not in self.vars:
            raise RuntimeError_(f"Undefined variable: '{name}'")
        # Coerce to declared type
        var_type = self.types[name]
        self.vars[name] = _coerce(value, var_type)

    def has(self, name: str) -> bool:
        return name in self.vars


def _coerce(value: object, var_type: str) -> object:
    """Coerce *value* to the DODO type *var_type*."""
    try:
        if var_type == "num":
            return int(value)
        elif var_type == "deci":
            return float(value)
        elif var_type == "decip":
            return Decimal(str(value))
    except (ValueError, TypeError):
        raise RuntimeError_(f"Cannot convert {value!r} to {var_type}")
    return value


# ═══════════════════════════════════════════════════════════════════════════
#  Interpreter
# ═══════════════════════════════════════════════════════════════════════════

class Interpreter:
    def __init__(self):
        self.env = Environment()

    def run(self, program: Program):
        for stmt in program.statements:
            self._exec(stmt)

    # ── statement dispatch ───────────────────────────────────────────────

    def _exec(self, node: object):
        if isinstance(node, DispStatement):
            return self._exec_disp(node)
        if isinstance(node, VarDeclaration):
            return self._exec_var_decl(node)
        if isinstance(node, Assignment):
            return self._exec_assign(node)
        if isinstance(node, IfStatement):
            return self._exec_if(node)
        # Expression statement (future-proof)
        return self._eval(node)

    def _exec_disp(self, node: DispStatement):
        value = self._eval(node.expression)
        # Format output nicely
        if isinstance(value, Decimal):
            # Remove trailing zeros for clean display
            print(f"{value:f}".rstrip('0').rstrip('.') if value == value.to_integral_value() is False else f"{value:f}")
        else:
            print(value)

    def _exec_var_decl(self, node: VarDeclaration):
        raw = self._eval(node.value)
        value = _coerce(raw, node.var_type)
        self.env.declare(node.name, node.var_type, value)

    def _exec_assign(self, node: Assignment):
        value = self._eval(node.value)
        self.env.set(node.name, value)

    def _exec_if(self, node: IfStatement):
        condition = self._eval(node.condition)
        if self._is_truthy(condition):
            for stmt in node.body:
                self._exec(stmt)
        elif node.else_body is not None:
            for stmt in node.else_body:
                self._exec(stmt)

    # ── expression evaluation ────────────────────────────────────────────

    def _eval(self, node: object) -> object:
        if isinstance(node, NumberLiteral):
            return node.value
        if isinstance(node, StringLiteral):
            return node.value
        if isinstance(node, Identifier):
            return self.env.get(node.name)
        if isinstance(node, BinaryOp):
            return self._eval_binary(node)
        if isinstance(node, UnaryOp):
            return self._eval_unary(node)
        raise RuntimeError_(f"Unknown AST node: {type(node).__name__}")

    def _eval_binary(self, node: BinaryOp) -> object:
        left = self._eval(node.left)
        right = self._eval(node.right)

        # Promote types if mixing Decimal with int/float
        if isinstance(left, Decimal) or isinstance(right, Decimal):
            left = Decimal(str(left))
            right = Decimal(str(right))

        op = node.op
        if op == "+":
            return left + right
        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if op == "/":
            if right == 0:
                raise RuntimeError_("Division by zero")
            return left / right

        # Comparisons always return bool
        if op == "==":
            return left == right
        if op == "!=":
            return left != right
        if op == "<":
            return left < right
        if op == ">":
            return left > right
        if op == "<=":
            return left <= right
        if op == ">=":
            return left >= right

        raise RuntimeError_(f"Unknown operator: {op}")

    def _eval_unary(self, node: UnaryOp) -> object:
        operand = self._eval(node.operand)
        if node.op == "-":
            return -operand
        raise RuntimeError_(f"Unknown unary operator: {node.op}")

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _is_truthy(value: object) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float, Decimal)):
            return value != 0
        if isinstance(value, str):
            return len(value) > 0
        return value is not None
