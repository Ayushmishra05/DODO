"""Quick test of the WASM pipeline."""
import sys
sys.path.insert(0, ".")

from dodo.lexer import Lexer
from dodo.parser import Parser
from dodo.wasm_codegen import WasmCodeGen
from dodo.wat2wasm import compile_wat_to_wasm, save_wat_file, save_wasm_file

code = '''disp "Hello from DODO!"
num x = 42
num y = 8
num result = x + y
disp "The answer is:"
disp result
if result > 40 {
    disp "That is a big number!"
} else {
    disp "That is a small number."
}'''

print("=" * 50)
print("DODO -> WASM Pipeline Test")
print("=" * 50)

# Step 1: Lex & Parse
tokens = Lexer(code).tokenize()
ast = Parser(tokens).parse()
print(f"[OK] Lexed & Parsed: {len(ast.statements)} statements")

# Step 2: Generate WAT
wat = WasmCodeGen(ast).generate()
print(f"[OK] WAT generated: {len(wat)} chars")

# Save sample .wat
save_wat_file(wat, "examples/sample_output.wat")
print("[OK] Saved examples/sample_output.wat")

# Step 3: Compile to WASM
wasm = compile_wat_to_wasm(wat)
print(f"[OK] WASM compiled: {len(wasm)} bytes")

# Save sample .wasm
save_wasm_file(wasm, "examples/sample_output.wasm")
print("[OK] Saved examples/sample_output.wasm")

print()
print("--- Generated WAT ---")
print(wat)
print("ALL TESTS PASSED!")
