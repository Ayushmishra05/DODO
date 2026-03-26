# 🦤 DODO Programming Language

A simple, expressive programming language built in Python — now with **WebAssembly compilation** and a browser-based IDE.

```
disp "Hello from DODO!"

num x = 42
deci pi = 3.14

if x > 10 {
    disp "Big number!"
}
```

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Language Reference](#language-reference)
  - [Data Types](#data-types)
  - [Variable Declaration](#variable-declaration)
  - [Variable Reassignment](#variable-reassignment)
  - [Arithmetic Operations](#arithmetic-operations)
  - [Comparison Operators](#comparison-operators)
  - [Print Output (`disp`)](#print-output-disp)
  - [Conditional Statements (`if` / `else`)](#conditional-statements-if--else)
  - [Comments](#comments)
  - [Parenthesized Expressions](#parenthesized-expressions)
  - [Unary Negation](#unary-negation)
  - [String Literals](#string-literals)
- [Execution Modes](#execution-modes)
  - [CLI File Execution](#cli-file-execution)
  - [Interactive REPL](#interactive-repl)
  - [Web IDE (WASM)](#web-ide-wasm)
- [Architecture](#architecture)
  - [Interpreter Pipeline](#interpreter-pipeline)
  - [WASM Pipeline](#wasm-pipeline)
- [Project Structure](#project-structure)
- [Examples](#examples)

---

## Features

| Feature | Description |
|---------|-------------|
| **3 numeric types** | `num` (integer), `deci` (float), `decip` (high-precision decimal) |
| **String support** | Double-quoted strings with escape sequences |
| **Arithmetic** | `+`, `-`, `*`, `/` with automatic type promotion |
| **Comparisons** | `==`, `!=`, `<`, `>`, `<=`, `>=` |
| **Conditionals** | `if` / `else` with block syntax |
| **Comments** | Single-line `//` comments |
| **Two execution modes** | Tree-walking interpreter (CLI) + WebAssembly compiler (browser) |
| **Web IDE** | Browser-based editor with WASM execution at `localhost:5000` |

---

## Installation

**Requirements:** Python 3.10+

```bash
# Clone the repository
git clone <repo-url>
cd Dodo

# Install dependencies (only needed for Web IDE)
pip install flask wabt
```

No installation needed for the CLI — just run with Python directly.

---

## Quick Start

```bash
# Run a DODO file
python dodo.py examples/hello.dodo

# Launch the interactive REPL
python dodo.py

# Start the Web IDE
python server.py
# → Open http://127.0.0.1:5000
```

---

## Language Reference

### Data Types

DODO supports three numeric types and strings:

| Type | Keyword | Description | Example |
|------|---------|-------------|---------|
| **Integer** | `num` | Whole numbers (mapped to Python `int`) | `42`, `-7`, `0` |
| **Float** | `deci` | Decimal numbers (mapped to Python `float`) | `3.14`, `-0.5` |
| **Precision Decimal** | `decip` | High-precision decimals (mapped to Python `Decimal`, 50-digit precision) | `3.141592653589793` |
| **String** | *(literal)* | Text enclosed in double quotes | `"Hello World"` |

**Type promotion:** When mixing types in expressions, values are automatically promoted:
- `num` + `deci` → result is `deci`
- `num` + `decip` → result is `decip`
- `deci` + `decip` → result is `decip`

---

### Variable Declaration

Variables must be declared with a type keyword before first use:

```
num count = 10
deci temperature = 36.6
decip precise_pi = 3.14159265358979323846
```

**Syntax:** `<type> <name> = <expression>`

- `<type>` — one of `num`, `deci`, or `decip`
- `<name>` — identifier starting with a letter or underscore, followed by letters, digits, or underscores
- `<expression>` — any valid expression (literal, variable, arithmetic, etc.)

---

### Variable Reassignment

After declaration, variables can be reassigned. The value is automatically coerced to the declared type:

```
num x = 10
x = 25          // x is now 25

deci temp = 20.0
temp = 36.6     // temp is now 36.6
```

Assigning a float to a `num` variable truncates to integer:
```
num x = 10
x = 7           // x is 7 (if assigned 7.9, it would become 7)
```

---

### Arithmetic Operations

| Operator | Operation | Example | Result |
|----------|-----------|---------|--------|
| `+` | Addition | `5 + 3` | `8` |
| `-` | Subtraction | `10 - 4` | `6` |
| `*` | Multiplication | `6 * 7` | `42` |
| `/` | Division | `15 / 4` | `3` (integer) or `3.75` (float) |

**Operator precedence** (highest to lowest):
1. Parentheses `( )`
2. Unary negation `-`
3. Multiplication `*`, Division `/`
4. Addition `+`, Subtraction `-`
5. Comparisons `==`, `!=`, `<`, `>`, `<=`, `>=`

```
num result = 2 + 3 * 4      // result = 14 (not 20)
num grouped = (2 + 3) * 4   // grouped = 20
```

**Division behavior:**
- Integer / Integer → Integer (truncating): `15 / 4` → `3`
- Float / anything → Float: `15.0 / 4` → `3.75`
- Division by zero raises a runtime error.

---

### Comparison Operators

Comparisons return boolean values (`true` / `false`), used primarily in `if` conditions:

| Operator | Meaning | Example |
|----------|---------|---------|
| `==` | Equal to | `x == 10` |
| `!=` | Not equal to | `x != 0` |
| `<` | Less than | `a < b` |
| `>` | Greater than | `a > b` |
| `<=` | Less than or equal | `a <= 100` |
| `>=` | Greater than or equal | `age >= 18` |

---

### Print Output (`disp`)

The `disp` keyword prints a value to the console:

```
disp "Hello World"        // prints: Hello World
disp 42                   // prints: 42
disp 3.14                 // prints: 3.14

num x = 10
disp x                    // prints: 10
disp x + 5                // prints: 15
disp x * 2 + 1            // prints: 21
```

`disp` accepts any expression — literals, variables, or complex expressions.

---

### Conditional Statements (`if` / `else`)

Execute code blocks based on conditions:

```
// Basic if
if x > 10 {
    disp "x is large"
}

// If-else
if score >= 90 {
    disp "Grade: A"
} else {
    disp "Keep trying!"
}
```

**Syntax:**
```
if <condition> {
    <statements>
}

if <condition> {
    <statements>
} else {
    <statements>
}
```

**Truthiness rules:**
- Numbers: `0` is false, everything else is true
- Strings: empty string `""` is false, non-empty is true
- Booleans: standard `true` / `false`

---

### Comments

Single-line comments start with `//`:

```
// This is a comment
num x = 10    // inline comment
```

Everything after `//` until the end of the line is ignored.

---

### Parenthesized Expressions

Use parentheses to control evaluation order:

```
num a = (2 + 3) * 4        // 20, not 14
num b = 10 / (2 + 3)       // 2
disp (a + b) * 2            // 44
```

---

### Unary Negation

Negate numeric values with the `-` prefix:

```
num x = 10
num y = -x          // y = -10
disp -5              // prints: -5
disp -(3 + 4)        // prints: -7
```

---

### String Literals

Strings are enclosed in double quotes and support escape sequences:

```
disp "Hello World"
disp "Line one\nLine two"    // newline
disp "Tab\there"              // tab
disp "She said \"hi\""        // escaped quote
disp "Back\\slash"            // literal backslash
```

| Escape | Character |
|--------|-----------|
| `\n` | Newline |
| `\t` | Tab |
| `\\` | Backslash |
| `\"` | Double quote |

---

## Execution Modes

### CLI File Execution

Run `.dodo` files directly:

```bash
python dodo.py examples/hello.dodo
```

Uses the **tree-walking interpreter** — parses the AST and evaluates it directly in Python.

### Interactive REPL

Launch without arguments for an interactive session:

```bash
python dodo.py
```

```
  ____   ___  ____   ___
 |  _ \ / _ \|  _ \ / _ \
 | | | | | | | | | | | | |
 | |_| | |_| | |_| | |_| |
 |____/ \___/|____/ \___/

 DODO Programming Language v1.0
 Type 'exit' to quit.

dodo> disp "Hello!"
Hello!
dodo> num x = 10
dodo> disp x * 2
20
dodo> exit
Bye!
```

Variables persist across lines in the REPL session.

### Web IDE (WASM)

Compile DODO to WebAssembly and run in the browser:

```bash
pip install flask wabt
python server.py
```

Open `http://127.0.0.1:5000` — a full-featured IDE with:

- **Code editor** with line numbers and tab support
- **Run button** (or `Ctrl+Enter`) to compile & execute
- **Output console** showing program results
- **WAT viewer** to inspect generated WebAssembly text
- **Example loader** with built-in sample programs

**WASM pipeline:** `DODO source → Lexer → Parser → AST → WAT Code Generator → .wat → .wasm → Browser execution`

---

## Architecture

### Interpreter Pipeline

```
Source Code (.dodo)
    │
    ▼
┌─────────┐    tokens    ┌────────┐     AST     ┌─────────────┐
│  Lexer  │ ──────────▶  │ Parser │ ──────────▶  │ Interpreter │ ──▶ Output
└─────────┘              └────────┘              └─────────────┘
```

### WASM Pipeline

```
Source Code (.dodo)
    │
    ▼
┌─────────┐    tokens    ┌────────┐     AST     ┌──────────────┐
│  Lexer  │ ──────────▶  │ Parser │ ──────────▶  │ WasmCodeGen  │
└─────────┘              └────────┘              └──────┬───────┘
                                                        │ .wat
                                                        ▼
                                                 ┌────────────┐
                                                 │  wat2wasm   │
                                                 └──────┬─────┘
                                                        │ .wasm
                                                        ▼
                                                 ┌────────────────┐
                                                 │ Browser / WASM │ ──▶ Output
                                                 │    Runtime     │
                                                 └────────────────┘
```

---

## Project Structure

```
Dodo/
├── dodo.py                 # CLI entry point (file runner + REPL)
├── server.py               # Flask web server for the Web IDE
├── requirements.txt        # Python dependencies (flask, wabt)
├── test_wasm.py            # WASM pipeline test script
├── dodo/
│   ├── __init__.py
│   ├── lexer.py            # Tokenizer — source text → tokens
│   ├── parser.py           # Parser — tokens → AST
│   ├── interpreter.py      # Tree-walking interpreter (CLI mode)
│   ├── wasm_codegen.py     # WASM code generator — AST → WAT
│   └── wat2wasm.py         # WAT → WASM binary converter
├── static/
│   ├── index.html          # Web IDE frontend
│   ├── style.css           # Dark theme styling
│   └── app.js              # WASM execution logic
└── examples/
    ├── hello.dodo           # Hello World
    ├── variables.dodo       # Variable declaration examples
    ├── conditionals.dodo    # If-else examples
    ├── ex1.dodo             # Mixed features demo
    ├── ex2.dodo             # Advanced demo
    ├── sample_output.wat    # Generated WAT example
    └── sample_output.wasm   # Compiled WASM binary
```

---

## Examples

### Hello World
```
disp "Hello World"
```

### Variables & Arithmetic
```
num x = 10
deci pi = 3.14
decip precise = 3.141592653589793

disp x
disp pi
disp precise
disp x + 5
```

### Conditionals
```
num age = 18

if age >= 18 {
    disp "Adult"
} else {
    disp "Minor"
}
```

### Complex Program
```
num a = 15
num b = 4

disp "Sum:"
disp a + b

disp "Product:"
disp a * b

if a > b {
    disp "a is greater"
} else {
    disp "b is greater"
}

deci ratio = 10.5
deci divisor = 3.2
disp "Float division:"
disp ratio / divisor
```

---

## License

MIT
