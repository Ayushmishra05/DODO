"""
DODO Language — WAT to WASM Converter

Converts WebAssembly Text Format (.wat) to binary (.wasm).
Tries multiple strategies:
  1. WABT's `wat2wasm` CLI tool
  2. `wabt` Python package
  3. Clear error with installation instructions
"""

import subprocess
import shutil
import tempfile
import os


class Wat2WasmError(Exception):
    """Raised when WAT → WASM conversion fails."""
    pass


def compile_wat_to_wasm(wat_text: str) -> bytes:
    """
    Convert WAT text to WASM binary bytes.

    Attempts to use the WABT `wat2wasm` tool, falling back to
    the `wabt` Python package if available.

    Args:
        wat_text: WebAssembly Text Format source code.

    Returns:
        The compiled .wasm binary as bytes.

    Raises:
        Wat2WasmError: If conversion fails or no tool is available.
    """
    # Strategy 1: Try WABT CLI tool
    wat2wasm_path = shutil.which("wat2wasm")
    if wat2wasm_path:
        return _compile_with_cli(wat_text, wat2wasm_path)

    # Strategy 2: Try wabt Python package
    try:
        import wabt  # type: ignore
        return _compile_with_wabt_package(wat_text)
    except ImportError:
        pass

    # Strategy 3: No tool available
    raise Wat2WasmError(
        "No WAT→WASM compiler found. Please install one of:\n"
        "  1. WABT CLI tools: https://github.com/WebAssembly/wabt/releases\n"
        "     - Download and add `wat2wasm` to your PATH\n"
        "  2. Python wabt package: pip install wabt\n"
    )


def _compile_with_cli(wat_text: str, wat2wasm_path: str) -> bytes:
    """Compile using WABT's wat2wasm CLI tool."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        wat_file = os.path.join(tmp_dir, "output.wat")
        wasm_file = os.path.join(tmp_dir, "output.wasm")

        with open(wat_file, "w", encoding="utf-8") as f:
            f.write(wat_text)

        try:
            result = subprocess.run(
                [wat2wasm_path, wat_file, "-o", wasm_file],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            raise Wat2WasmError("wat2wasm timed out")

        if result.returncode != 0:
            raise Wat2WasmError(
                f"wat2wasm failed:\n{result.stderr.strip()}"
            )

        with open(wasm_file, "rb") as f:
            return f.read()


def _compile_with_wabt_package(wat_text: str) -> bytes:
    """Compile using the wabt Python package."""
    try:
        from wabt import Wabt  # type: ignore
        w = Wabt()

        with tempfile.TemporaryDirectory() as tmp_dir:
            wat_file = os.path.join(tmp_dir, "output.wat")
            wasm_file = os.path.join(tmp_dir, "output.wasm")

            with open(wat_file, "w", encoding="utf-8") as f:
                f.write(wat_text)

            w.wat_to_wasm(wat_file, output=wasm_file)

            with open(wasm_file, "rb") as f:
                return f.read()
    except Wat2WasmError:
        raise
    except Exception as e:
        raise Wat2WasmError(f"wabt Python package error: {e}")


def save_wat_file(wat_text: str, filepath: str):
    """Save WAT text to a file."""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(wat_text)


def save_wasm_file(wasm_bytes: bytes, filepath: str):
    """Save WASM binary to a file."""
    with open(filepath, "wb") as f:
        f.write(wasm_bytes)
