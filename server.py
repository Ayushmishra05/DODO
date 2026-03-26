"""
DODO Language — Flask Web Server

Provides a web interface to write and execute DODO programs
compiled to WebAssembly.

Endpoints:
    GET  /         → Serves the frontend HTML page
    POST /compile  → Compiles DODO code to .wasm binary
"""

import sys
import os
import traceback

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, Response, jsonify, send_from_directory

from dodo.lexer import Lexer, LexerError
from dodo.parser import Parser, ParserError
from dodo.wasm_codegen import WasmCodeGen, WasmCodeGenError
from dodo.wat2wasm import compile_wat_to_wasm, Wat2WasmError

app = Flask(__name__, static_folder="static")


@app.route("/")
def index():
    """Serve the frontend page."""
    return send_from_directory("static", "index.html")


@app.route("/compile", methods=["POST"])
def compile_dodo():
    """
    Compile DODO source code to .wasm binary.

    Expects: Plain text body containing DODO source code.
    Returns: .wasm binary on success, JSON error on failure.
    """
    source = request.get_data(as_text=True)

    if not source or not source.strip():
        return jsonify({"error": "No source code provided"}), 400

    try:
        # Step 1: Lex
        tokens = Lexer(source).tokenize()

        # Step 2: Parse
        ast = Parser(tokens).parse()

        # Step 3: Generate WAT
        codegen = WasmCodeGen(ast)
        wat_text = codegen.generate()

        # Step 4: Compile WAT → WASM
        wasm_bytes = compile_wat_to_wasm(wat_text)

        # Return the .wasm binary
        return Response(
            wasm_bytes,
            mimetype="application/wasm",
            headers={"Content-Disposition": "inline; filename=output.wasm"},
        )

    except LexerError as e:
        return jsonify({"error": f"Lexer Error: {e}"}), 400
    except ParserError as e:
        return jsonify({"error": f"Parser Error: {e}"}), 400
    except WasmCodeGenError as e:
        return jsonify({"error": f"Code Generation Error: {e}"}), 400
    except Wat2WasmError as e:
        return jsonify({"error": f"WASM Compilation Error: {e}"}), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Internal Error: {e}"}), 500


@app.route("/compile_wat", methods=["POST"])
def compile_wat_only():
    """
    Compile DODO source code and return only the WAT text.
    Useful for debugging / inspecting generated code.
    """
    source = request.get_data(as_text=True)

    if not source or not source.strip():
        return jsonify({"error": "No source code provided"}), 400

    try:
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        codegen = WasmCodeGen(ast)
        wat_text = codegen.generate()
        return Response(wat_text, mimetype="text/plain")

    except (LexerError, ParserError, WasmCodeGenError) as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Internal Error: {e}"}), 500


if __name__ == "__main__":
    print("\n  🦤 DODO Web IDE — http://127.0.0.1:5000\n")
    app.run(host="0.0.0.0", port=5000, debug=True)
