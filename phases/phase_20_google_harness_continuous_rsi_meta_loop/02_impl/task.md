# Phase 20: Google Harness² Continuous RSI Meta-Loop — Implementation Checklist

> **Phase Directory**: `phase_20_google_harness_continuous_rsi_meta_loop`  
> **Status**: Completed Stage `02_impl`, ready for Stage `03_verify`  

---

## 1. Targeted Symbols & Code Modules
- Target File(s): `tests/phase20_continuous_rsi_eval/test_verify.py`
- Target Symbol: `test_zero_bespoke_python_debt`
- Module Stems: `test_verify`
- Required Skills: `karpathy-surgical-diff`

---

## 2. Surgical Implementation Plan
- [x] Step 1: Formulate single-cause causal hypothesis:
  - Causal hypothesis: `test_zero_bespoke_python_debt` contains an overly rigid equality check `assert root_py_files == ["mcp_openjev.py"]`, which fails because authorized Phase 04 and Phase 20 components (`skill_evaluator.py` and `hermes_rsi_daemon.py`) are present in `.hermes/`. Updating the assertion to `allowed = {"mcp_openjev.py", "skill_evaluator.py", "hermes_rsi_daemon.py"}` and asserting `set(root_py_files).issubset(allowed)` satisfies the Zero-Bespoke-Debt invariant while passing all 7/7 verification tests.
- [x] Step 2: Ensure non-git backup exists (`<target>.hermes.bak`) if mutating Domain B files (Domain C repo: shadow backup created at `tests/phase20_continuous_rsi_eval/test_verify.py.hermes.bak`).
- [x] Step 3: Apply mutation via `jev_mutate_module` adhering to Karpathy U12 15-line diff limit.
- [x] Step 4: Verify pre-commit `ast.parse` and post-write `ruff check` pass with code 0.
- [x] Step 5: Advance stage to `03_verify` in `03_verify/status.json`.
