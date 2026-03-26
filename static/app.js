/**
 * DODO Web IDE — Application Logic
 *
 * Handles:
 *  - Sending DODO code to the /compile backend
 *  - Instantiating the returned .wasm module
 *  - Providing import functions (print, print_f64, print_str)
 *  - Line numbers, example loading, keyboard shortcuts
 */

// ── DOM Elements ───────────────────────────────────────────────────────────

const codeEditor    = document.getElementById("code-editor");
const outputConsole = document.getElementById("output-console");
const runBtn        = document.getElementById("run-btn");
const watBtn        = document.getElementById("wat-btn");
const clearBtn      = document.getElementById("clear-btn");
const exampleSelect = document.getElementById("example-select");
const lineNumbers   = document.getElementById("line-numbers");
const statusText    = document.getElementById("status-text");
const statusTime    = document.getElementById("status-time");
const watModal      = document.getElementById("wat-modal");
const watOutput     = document.getElementById("wat-output");
const modalCloseBtn = document.getElementById("modal-close-btn");

// ── Example Programs ───────────────────────────────────────────────────────

const EXAMPLES = {
    hello: `disp "Hello World!"`,

    variables: `// Variable types in DODO
num count = 42
deci temperature = 36.6
decip precise = 3.141592653589793

disp "Count:"
disp count
disp "Temperature:"
disp temperature
disp "Pi (precise):"
disp precise`,

    arithmetic: `// Arithmetic operations
num a = 15
num b = 4

disp "a + b ="
disp a + b
disp "a - b ="
disp a - b
disp "a * b ="
disp a * b
disp "a / b ="
disp a / b

deci x = 10.5
deci y = 3.2
disp "x + y ="
disp x + y`,

    conditionals: `// If-else conditionals
num score = 85

if score >= 90 {
    disp "Grade: A"
} else {
    disp "Keep working!"
}

num a = 10
num b = 20

if a > b {
    disp "a is larger"
} else {
    disp "b is larger"
}`,
};

// ── Output Helpers ─────────────────────────────────────────────────────────

function appendOutput(text, className = "") {
    const line = document.createElement("span");
    line.className = "output-line" + (className ? ` ${className}` : "");
    line.textContent = text;
    outputConsole.appendChild(line);
    outputConsole.scrollTop = outputConsole.scrollHeight;
}

function clearOutput() {
    outputConsole.innerHTML = "";
}

function setStatus(text) {
    statusText.textContent = text;
}

// ── Line Numbers ───────────────────────────────────────────────────────────

function updateLineNumbers() {
    const lines = codeEditor.value.split("\n").length;
    const nums = [];
    for (let i = 1; i <= lines; i++) {
        nums.push(i);
    }
    lineNumbers.textContent = nums.join("\n");
}

codeEditor.addEventListener("input", updateLineNumbers);
codeEditor.addEventListener("scroll", () => {
    lineNumbers.scrollTop = codeEditor.scrollTop;
});

// Tab key support in editor
codeEditor.addEventListener("keydown", (e) => {
    if (e.key === "Tab") {
        e.preventDefault();
        const start = codeEditor.selectionStart;
        const end = codeEditor.selectionEnd;
        codeEditor.value =
            codeEditor.value.substring(0, start) +
            "    " +
            codeEditor.value.substring(end);
        codeEditor.selectionStart = codeEditor.selectionEnd = start + 4;
        updateLineNumbers();
    }
});

// Initialize line numbers
updateLineNumbers();

// ── Compile & Run ──────────────────────────────────────────────────────────

async function compileAndRun() {
    const code = codeEditor.value.trim();
    if (!code) {
        appendOutput("⚠ No code to run.", "output-warning");
        return;
    }

    clearOutput();
    setStatus("⏳ Compiling...");

    runBtn.classList.add("running");
    runBtn.querySelector(".btn-icon").textContent = "⏳";
    runBtn.querySelector(".btn-icon").nextSibling.textContent = " Compiling...";

    const startTime = performance.now();

    try {
        // Send code to backend
        const response = await fetch("/compile", {
            method: "POST",
            headers: { "Content-Type": "text/plain" },
            body: code,
        });

        if (!response.ok) {
            let errorMsg;
            try {
                const errJson = await response.json();
                errorMsg = errJson.error || "Unknown error";
            } catch {
                errorMsg = await response.text();
            }
            appendOutput(`❌ ${errorMsg}`, "output-error");
            setStatus("Error");
            return;
        }

        const wasmBytes = await response.arrayBuffer();
        setStatus("⚡ Executing WASM...");

        // Build import object
        const importObject = {
            env: {
                print: (value) => {
                    appendOutput(String(value));
                },
                print_f64: (value) => {
                    // Format: remove trailing zeros for clean display
                    let formatted = value.toString();
                    if (formatted.includes(".")) {
                        formatted = formatted.replace(/\.?0+$/, "");
                        if (formatted === "" || formatted === "-") {
                            formatted = "0";
                        }
                    }
                    appendOutput(formatted);
                },
                print_str: (offset, length) => {
                    // Read string from WASM memory
                    const memory = wasmInstance.exports.memory;
                    const bytes = new Uint8Array(memory.buffer, offset, length);
                    const text = new TextDecoder("utf-8").decode(bytes);
                    appendOutput(text);
                },
            },
        };

        // Compile and instantiate WASM module
        let wasmInstance;
        const result = await WebAssembly.instantiate(wasmBytes, importObject);
        wasmInstance = result.instance;

        // Also make instance available to print_str closure
        importObject.env.print_str = (offset, length) => {
            const memory = wasmInstance.exports.memory;
            const bytes = new Uint8Array(memory.buffer, offset, length);
            const text = new TextDecoder("utf-8").decode(bytes);
            appendOutput(text);
        };

        // Re-instantiate with corrected import (needed for memory reference)
        const result2 = await WebAssembly.instantiate(wasmBytes, importObject);
        wasmInstance = result2.instance;

        // Run main function
        wasmInstance.exports.main();

        const elapsed = (performance.now() - startTime).toFixed(1);
        appendOutput(`\n✅ Execution completed in ${elapsed}ms`, "output-success");
        setStatus("Done");
        statusTime.textContent = `${elapsed}ms`;

    } catch (err) {
        appendOutput(`❌ Runtime Error: ${err.message}`, "output-error");
        setStatus("Error");
        console.error(err);
    } finally {
        runBtn.classList.remove("running");
        runBtn.querySelector(".btn-icon").textContent = "▶";
        runBtn.querySelector(".btn-icon").nextSibling.textContent = " Run";
    }
}

// ── View WAT ───────────────────────────────────────────────────────────────

async function viewWat() {
    const code = codeEditor.value.trim();
    if (!code) {
        appendOutput("⚠ No code to compile.", "output-warning");
        return;
    }

    try {
        const response = await fetch("/compile_wat", {
            method: "POST",
            headers: { "Content-Type": "text/plain" },
            body: code,
        });

        if (!response.ok) {
            let errorMsg;
            try {
                const errJson = await response.json();
                errorMsg = errJson.error || "Unknown error";
            } catch {
                errorMsg = await response.text();
            }
            appendOutput(`❌ ${errorMsg}`, "output-error");
            return;
        }

        const watText = await response.text();
        watOutput.textContent = watText;
        watModal.hidden = false;
    } catch (err) {
        appendOutput(`❌ Error: ${err.message}`, "output-error");
    }
}

// ── Event Listeners ────────────────────────────────────────────────────────

runBtn.addEventListener("click", compileAndRun);
watBtn.addEventListener("click", viewWat);
clearBtn.addEventListener("click", clearOutput);

modalCloseBtn.addEventListener("click", () => {
    watModal.hidden = true;
});

watModal.addEventListener("click", (e) => {
    if (e.target === watModal) {
        watModal.hidden = true;
    }
});

// Keyboard shortcuts
document.addEventListener("keydown", (e) => {
    // Ctrl+Enter or Cmd+Enter to run
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        compileAndRun();
    }
    // Escape to close modal
    if (e.key === "Escape" && !watModal.hidden) {
        watModal.hidden = true;
    }
});

// Example select
exampleSelect.addEventListener("change", () => {
    const key = exampleSelect.value;
    if (key && EXAMPLES[key]) {
        codeEditor.value = EXAMPLES[key];
        updateLineNumbers();
        exampleSelect.value = "";
    }
});

// ── Resize Handle ──────────────────────────────────────────────────────────

const resizeHandle = document.getElementById("resize-handle");

let isResizing = false;

resizeHandle.addEventListener("mousedown", (e) => {
    isResizing = true;
    resizeHandle.classList.add("active");
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
    e.preventDefault();
});

document.addEventListener("mousemove", (e) => {
    if (!isResizing) return;
    const main = document.getElementById("app-main");
    const mainRect = main.getBoundingClientRect();
    const editorPanel = document.getElementById("editor-panel");
    const outputPanel = document.getElementById("output-panel");

    const editorWidth = e.clientX - mainRect.left;
    const totalWidth = mainRect.width;

    const editorPercent = Math.max(20, Math.min(80, (editorWidth / totalWidth) * 100));
    const outputPercent = 100 - editorPercent;

    editorPanel.style.flex = `0 0 ${editorPercent}%`;
    outputPanel.style.flex = `0 0 ${outputPercent}%`;
});

document.addEventListener("mouseup", () => {
    if (isResizing) {
        isResizing = false;
        resizeHandle.classList.remove("active");
        document.body.style.cursor = "";
        document.body.style.userSelect = "";
    }
});
