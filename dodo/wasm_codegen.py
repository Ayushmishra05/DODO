"""
DODO Language — WASM Code Generator
Traverses the AST and emits WebAssembly Text Format (.wat).

Supports:
  - Integer (num) → i32
  - Float (deci, decip) → f64
  - String literals → linear memory data segments
  - Arithmetic, comparisons, if/else, print
"""

from dodo.parser import (
    Program, DispStatement, VarDeclaration, Assignment,
    IfStatement, NumberLiteral, StringLiteral, Identifier,
    BinaryOp, UnaryOp,
)


class WasmCodeGenError(Exception):
    """Raised when code generation encounters an unsupported construct."""
    pass


class WasmCodeGen:
    """
    Generates WebAssembly Text Format (.wat) from a DODO AST.

    The generated module:
      - Imports env.print (param i32) for integer printing
      - Imports env.print_str (param i32 i32) for string printing (offset, len)
      - Imports env.print_f64 (param f64) for float printing
      - Exports a "main" function as the entry point
      - Exports "memory" for JS to read string data
    """

    def __init__(self, program: Program):
        self.program = program
        # Variable tracking: name → {"type": "i32"|"f64", "index": int}
        self.locals: dict[str, dict] = {}
        self.local_counter = 0
        # String data segments: list of (offset, text)
        self.string_data: list[tuple[int, str]] = []
        self.string_offset = 0  # current write offset in linear memory
        # Collect a unique label counter for if/else blocks
        self.label_counter = 0

    def generate(self) -> str:
        """Generate complete .wat module text."""
        # First pass: collect all variable declarations
        self._collect_variables(self.program.statements)

        # Second pass: collect all string literals
        self._collect_strings(self.program.statements)

        # Third pass: generate instruction body
        body_lines = []
        for stmt in self.program.statements:
            body_lines.extend(self._emit_statement(stmt))

        # Build the full module
        return self._build_module(body_lines)

    # ── First Pass: Collect Variables ────────────────────────────────────

    def _collect_variables(self, stmts):
        """Walk statements to discover all variable declarations."""
        for stmt in stmts:
            if isinstance(stmt, VarDeclaration):
                wasm_type = self._dodo_type_to_wasm(stmt.var_type)
                if stmt.name not in self.locals:
                    self.locals[stmt.name] = {
                        "type": wasm_type,
                        "index": self.local_counter,
                    }
                    self.local_counter += 1
            elif isinstance(stmt, IfStatement):
                self._collect_variables(stmt.body)
                if stmt.else_body:
                    self._collect_variables(stmt.else_body)

    def _dodo_type_to_wasm(self, var_type: str) -> str:
        """Map DODO type keywords to WASM types."""
        if var_type == "num":
            return "i32"
        elif var_type in ("deci", "decip"):
            return "f64"
        return "i32"

    # ── Second Pass: Collect String Literals ─────────────────────────────

    def _collect_strings(self, stmts):
        """Walk all nodes to find string literals and assign memory offsets."""
        for stmt in stmts:
            self._collect_strings_in_node(stmt)

    def _collect_strings_in_node(self, node):
        """Recursively find StringLiteral nodes."""
        if isinstance(node, StringLiteral):
            # Only add if not already added (by value)
            for _, existing_text in self.string_data:
                if existing_text == node.value:
                    return
            encoded = node.value.encode("utf-8")
            self.string_data.append((self.string_offset, node.value))
            self.string_offset += len(encoded)
        elif isinstance(node, DispStatement):
            self._collect_strings_in_node(node.expression)
        elif isinstance(node, VarDeclaration):
            self._collect_strings_in_node(node.value)
        elif isinstance(node, Assignment):
            self._collect_strings_in_node(node.value)
        elif isinstance(node, BinaryOp):
            self._collect_strings_in_node(node.left)
            self._collect_strings_in_node(node.right)
        elif isinstance(node, UnaryOp):
            self._collect_strings_in_node(node.operand)
        elif isinstance(node, IfStatement):
            self._collect_strings_in_node(node.condition)
            for s in node.body:
                self._collect_strings_in_node(s)
            if node.else_body:
                for s in node.else_body:
                    self._collect_strings_in_node(s)

    def _get_string_info(self, text: str) -> tuple[int, int]:
        """Return (offset, length) for a string literal."""
        for offset, stored_text in self.string_data:
            if stored_text == text:
                return offset, len(text.encode("utf-8"))
        raise WasmCodeGenError(f"String not found in data: {text!r}")

    # ── Module Assembly ─────────────────────────────────────────────────

    def _build_module(self, body_lines: list[str]) -> str:
        """Assemble the complete .wat module."""
        parts = []
        parts.append("(module")

        # ── Imports
        parts.append('  (import "env" "print" (func $print (param i32)))')
        parts.append('  (import "env" "print_f64" (func $print_f64 (param f64)))')
        parts.append('  (import "env" "print_str" (func $print_str (param i32) (param i32)))')

        # ── Memory (1 page = 64KB, enough for string data)
        parts.append("  (memory (export \"memory\") 1)")

        # ── Data segments for string literals
        for offset, text in self.string_data:
            escaped = self._escape_wat_string(text)
            parts.append(f'  (data (i32.const {offset}) "{escaped}")')

        # ── Main function
        parts.append('  (func (export "main")')

        # Local variable declarations
        for name, info in self.locals.items():
            parts.append(f"    (local ${name} {info['type']})")

        # Function body
        for line in body_lines:
            parts.append(f"    {line}")

        parts.append("  )")  # end func
        parts.append(")")    # end module

        return "\n".join(parts) + "\n"

    def _escape_wat_string(self, text: str) -> str:
        """Escape a string for WAT data segment format."""
        result = []
        for ch in text:
            code = ord(ch)
            if 32 <= code < 127 and ch not in ('"', '\\'):
                result.append(ch)
            else:
                result.append(f"\\{code:02x}")
        return "".join(result)

    # ── Statement Emission ──────────────────────────────────────────────

    def _emit_statement(self, node) -> list[str]:
        """Emit WAT instructions for a statement. Returns list of lines."""
        if isinstance(node, DispStatement):
            return self._emit_disp(node)
        if isinstance(node, VarDeclaration):
            return self._emit_var_decl(node)
        if isinstance(node, Assignment):
            return self._emit_assign(node)
        if isinstance(node, IfStatement):
            return self._emit_if(node)
        # Expression statement — evaluate and drop result
        lines = self._emit_expr(node)
        lines.append("drop")
        return lines

    def _emit_disp(self, node: DispStatement) -> list[str]:
        """Emit print call."""
        expr = node.expression
        if isinstance(expr, StringLiteral):
            # String print: push offset and length, call $print_str
            offset, length = self._get_string_info(expr.value)
            return [
                f"i32.const {offset}",
                f"i32.const {length}",
                "call $print_str",
            ]
        else:
            # Numeric print
            lines = self._emit_expr(expr)
            expr_type = self._infer_type(expr)
            if expr_type == "f64":
                lines.append("call $print_f64")
            else:
                lines.append("call $print")
            return lines

    def _emit_var_decl(self, node: VarDeclaration) -> list[str]:
        """Emit variable declaration with initial value."""
        lines = self._emit_expr(node.value)
        var_info = self.locals[node.name]
        # Type conversion if needed
        expr_type = self._infer_type(node.value)
        lines.extend(self._emit_type_convert(expr_type, var_info["type"]))
        lines.append(f"local.set ${node.name}")
        return lines

    def _emit_assign(self, node: Assignment) -> list[str]:
        """Emit variable assignment."""
        if node.name not in self.locals:
            raise WasmCodeGenError(f"Undefined variable: '{node.name}'")
        lines = self._emit_expr(node.value)
        var_info = self.locals[node.name]
        expr_type = self._infer_type(node.value)
        lines.extend(self._emit_type_convert(expr_type, var_info["type"]))
        lines.append(f"local.set ${node.name}")
        return lines

    def _emit_if(self, node: IfStatement) -> list[str]:
        """Emit if/else block."""
        lines = []
        # Evaluate condition (must be i32 for WASM if)
        cond_lines = self._emit_expr(node.condition)
        cond_type = self._infer_type(node.condition)
        lines.extend(cond_lines)
        # If condition is f64 comparison, result is already i32
        # But if it's a raw f64 value used as truthy, convert
        if cond_type == "f64":
            # f64 != 0.0 → i32 (truthy check)
            lines.append("f64.const 0")
            lines.append("f64.ne")

        lines.append("if")
        for stmt in node.body:
            lines.extend(self._emit_statement(stmt))
        if node.else_body:
            lines.append("else")
            for stmt in node.else_body:
                lines.extend(self._emit_statement(stmt))
        lines.append("end")
        return lines

    # ── Expression Emission ─────────────────────────────────────────────

    def _emit_expr(self, node) -> list[str]:
        """Emit WAT instructions for an expression. Pushes result onto stack."""
        if isinstance(node, NumberLiteral):
            return self._emit_number(node)
        if isinstance(node, StringLiteral):
            # For string in expression context, push offset
            offset, _ = self._get_string_info(node.value)
            return [f"i32.const {offset}"]
        if isinstance(node, Identifier):
            return self._emit_identifier(node)
        if isinstance(node, BinaryOp):
            return self._emit_binary(node)
        if isinstance(node, UnaryOp):
            return self._emit_unary(node)
        raise WasmCodeGenError(f"Unsupported expression node: {type(node).__name__}")

    def _emit_number(self, node: NumberLiteral) -> list[str]:
        """Emit a numeric literal."""
        if isinstance(node.value, float):
            return [f"f64.const {node.value}"]
        else:
            return [f"i32.const {node.value}"]

    def _emit_identifier(self, node: Identifier) -> list[str]:
        """Emit a variable read."""
        if node.name not in self.locals:
            raise WasmCodeGenError(f"Undefined variable: '{node.name}'")
        return [f"local.get ${node.name}"]

    def _emit_binary(self, node: BinaryOp) -> list[str]:
        """Emit a binary operation."""
        lines = []
        left_type = self._infer_type(node.left)
        right_type = self._infer_type(node.right)

        # Determine operation type
        op_type = "f64" if left_type == "f64" or right_type == "f64" else "i32"

        # Emit left operand
        left_lines = self._emit_expr(node.left)
        lines.extend(left_lines)
        if op_type == "f64" and left_type == "i32":
            lines.append("f64.convert_i32_s")

        # Emit right operand
        right_lines = self._emit_expr(node.right)
        lines.extend(right_lines)
        if op_type == "f64" and right_type == "i32":
            lines.append("f64.convert_i32_s")

        # Emit the operation
        op = node.op
        if op_type == "i32":
            op_map = {
                "+": "i32.add",
                "-": "i32.sub",
                "*": "i32.mul",
                "/": "i32.div_s",
                "==": "i32.eq",
                "!=": "i32.ne",
                "<": "i32.lt_s",
                ">": "i32.gt_s",
                "<=": "i32.le_s",
                ">=": "i32.ge_s",
            }
        else:
            op_map = {
                "+": "f64.add",
                "-": "f64.sub",
                "*": "f64.mul",
                "/": "f64.div",
                "==": "f64.eq",
                "!=": "f64.ne",
                "<": "f64.lt",
                ">": "f64.gt",
                "<=": "f64.le",
                ">=": "f64.ge",
            }

        if op not in op_map:
            raise WasmCodeGenError(f"Unsupported operator: {op}")
        lines.append(op_map[op])
        return lines

    def _emit_unary(self, node: UnaryOp) -> list[str]:
        """Emit a unary operation (negation)."""
        lines = []
        operand_type = self._infer_type(node.operand)
        if node.op == "-":
            if operand_type == "f64":
                lines.extend(self._emit_expr(node.operand))
                lines.append("f64.neg")
            else:
                lines.append("i32.const 0")
                lines.extend(self._emit_expr(node.operand))
                lines.append("i32.sub")
        else:
            raise WasmCodeGenError(f"Unsupported unary operator: {node.op}")
        return lines

    # ── Type Inference ──────────────────────────────────────────────────

    def _infer_type(self, node) -> str:
        """Infer the WASM type of an expression node."""
        if isinstance(node, NumberLiteral):
            return "f64" if isinstance(node.value, float) else "i32"
        if isinstance(node, StringLiteral):
            return "i32"  # string offset is i32
        if isinstance(node, Identifier):
            if node.name in self.locals:
                return self.locals[node.name]["type"]
            return "i32"
        if isinstance(node, BinaryOp):
            left_t = self._infer_type(node.left)
            right_t = self._infer_type(node.right)
            # Comparisons always return i32
            if node.op in ("==", "!=", "<", ">", "<=", ">="):
                return "i32"
            return "f64" if left_t == "f64" or right_t == "f64" else "i32"
        if isinstance(node, UnaryOp):
            return self._infer_type(node.operand)
        return "i32"

    def _emit_type_convert(self, from_type: str, to_type: str) -> list[str]:
        """Emit conversion instruction if types differ."""
        if from_type == to_type:
            return []
        if from_type == "i32" and to_type == "f64":
            return ["f64.convert_i32_s"]
        if from_type == "f64" and to_type == "i32":
            return ["i32.trunc_f64_s"]
        return []
