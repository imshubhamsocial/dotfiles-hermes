# Phase 11: Polyglot Compiler & Linter Verification Gate — Implementation Checklist

> **Phase Directory**: `phase_11_polyglot_compiler_linter_verification_gate`  
> **Status**: Stage `02_impl` execution complete  

---

## 1. Targeted Symbols & Code Modules
- Target File(s):
  - `.hermes/mcp_openjev.py`: fix ruff linter warnings (`PERF102`, `PLW1510`, `BLE001`, `S112`, `S110`, `SIM222`)
  - `conftest.py`: fix ruff linter warnings (`BLE001`, `S110`)
- Module Stems:
  - `ruff` pre-commit compiler/linter gate
- Required Skills:
  - `karpathy-surgical-diff`

---

## 2. Causal Hypotheses
1. `ruff check` enforces Python AST hygiene. Catching broad `Exception` in try blocks and ignoring explicit `check=False` on subprocess calls triggers linter failures. Replacing blind exception catches with explicit exception tuples and adding explicit subprocess parameters resolves all violations.
2. Running `ruff check .hermes/mcp_openjev.py conftest.py` executes 100% on CPU (0.0 MiB CUDA delta) and validates structural code integrity.

---

## 3. Surgical Implementation Plan
- [x] Step 1: Formulate single-cause causal hypothesis.
- [x] Step 2: Ensure non-git backup exists (`<target>.hermes.bak`) if mutating Domain B files.
- [x] Step 3: Apply mutation via `jev_mutate_module` adhering to Karpathy U12 15-line diff limit.
- [x] Step 4: Verify pre-commit `ast.parse` and post-write `ruff check` pass with code 0.
- [x] Step 5: Advance stage to `03_verify` in `03_verify/status.json`.
