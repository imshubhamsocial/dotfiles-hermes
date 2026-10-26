# Phase 01: Canonical Upstream Parity & Zero-Bespoke Core — Implementation Checklist

> **Phase Directory**: `phase_01_canonical_upstream_parity_zero_bespoke_core`  
> **Status**: Stage `02_impl` in progress  

---

## 1. Targeted Symbols & Code Modules
- Target File(s):
  - `~/.hermes/SOUL.md`: token-0 RoPE precedence override string
  - `~/.hermes/mcp_openjev.py`: `canonicalize_bpe_path` subword sanitization regex
- Module Stems:
  - `canonicalize_bpe_path` in `mcp_openjev.py`
  - `SafePathModel` in `mcp_openjev.py`
- Required Skills:
  - `karpathy-surgical-diff`

---

## 2. Causal Hypotheses
1. `test_soul_md_kernel_integrity` fails because `SOUL.md` begins with an escaped backslash `\[PRECEDENCE OVERRIDE:` from markdown linting rather than the raw `[PRECEDENCE OVERRIDE:`. Stripping the leading backslash restores invariant compliance.
2. `test_pydantic_v2_path_sanitization` and `test_cpu_isolation_and_surgical_mutation` fail because `canonicalize_bpe_path` in `mcp_openjev.py` contains `r"[^\\x00-\\x7F]+"`. In Python raw strings, `\\x00` treats the backslash as a literal character, converting the range into character-set subtraction that strips valid ASCII characters (`d`, `a`, `g`, `_`, `e`, etc.) leaving only `x`. Correcting the regex to `r"[^\x00-\x7F]+"` resolves proper BPE path sanitization.

---

## 3. Surgical Implementation Plan
- [x] Step 1: Formulate single-cause causal hypothesis.
- [ ] Step 2: Ensure non-git backup exists (`<target>.hermes.bak`) for mutating Domain B files (`~/.hermes/SOUL.md` and `~/.hermes/mcp_openjev.py`).
- [ ] Step 3: Apply mutation via `jev_mutate_module` adhering to Karpathy U12 15-line diff limit.
- [ ] Step 4: Verify pre-commit `ast.parse` and post-write `ruff check` pass with code 0.
- [ ] Step 5: Advance stage to `03_verify` in `03_verify/status.json`.
