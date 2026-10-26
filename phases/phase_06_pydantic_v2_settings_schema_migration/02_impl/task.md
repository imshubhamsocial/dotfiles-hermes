# Phase 06: Pydantic v2 Settings & Schema Migration — Implementation Checklist

> **Phase Directory**: `phase_06_pydantic_v2_settings_schema_migration`  
> **Status**: Stage `02_impl` execution complete  

---

## 1. Targeted Symbols & Code Modules
- Target File(s):
  - `.hermes/mcp_openjev.py`: `SafePathModel` class enforcing `ConfigDict(extra="forbid")` and regex BPE path sanitization
  - `tests/phase01_canonical_parity/test_phase01_parity.py`: `test_pydantic_v2_path_sanitization`
- Module Stems:
  - `SafePathModel`, `canonicalize_bpe_path`
- Required Skills:
  - `karpathy-surgical-diff`

---

## 2. Causal Hypotheses
1. Malformed BPE token boundary artifacts (`.py_py`, `_py`, `.p`, `dagpy`) corrupt target module paths during LLM tool invocation. `SafePathModel` with `@field_validator("path", mode="before")` sanitizes paths to canonical extensions deterministically on the CPU (0.0 MiB CUDA delta).
2. Enforcing `ConfigDict(extra="forbid")` on all tool input schemas rejects unexpected attributes, guaranteeing strict schema conformance across the FastMCP orchestration layer.

---

## 3. Surgical Implementation Plan
- [x] Step 1: Formulate single-cause causal hypothesis.
- [x] Step 2: Ensure non-git backup exists (`<target>.hermes.bak`) if mutating Domain B files.
- [x] Step 3: Verify `SafePathModel` and `ConfigDict(extra="forbid")` in `.hermes/mcp_openjev.py`.
- [x] Step 4: Verify `pytest tests/phase01_canonical_parity/test_phase01_parity.py -k test_pydantic_v2_path_sanitization -q` passes with code 0.
- [x] Step 5: Advance stage to `03_verify` in `03_verify/status.json`.
