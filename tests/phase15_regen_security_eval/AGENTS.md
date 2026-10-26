# AGENTS.md — Phase 15 OpenJEV, FastEmbed CPU & Spec-Driven Security Testbed

> **Project**: Hermes Agent OS — Phase 15 Evaluation Harness  
> **Literature**: Regenerative Software Engineering via Agentic Scaffolding (Google DeepMind / MIT, arXiv:2610.14224), Google Harness²  
> **Target Scenario**: `scenario/` (Sanitization engine command escape & prompt injection defense)  
> **Verification Gate**: `pytest tests/phase15_regen_security_eval/ -q && python3 -c "import json; s=json.load(open('tests/phase15_regen_security_eval/security_regen_report.json')); assert s['sympy_vram_bound_verified'] is True and s['fastembed_cuda_mib'] == 0 and s['open_notebook_mcp_connected'] is True and s['memory_poisoning_blocked'] == 100 and s['regen_roundoff_error'] < 1e-6"`

---

## 1. Goal Contract Standard

```text
/goal Refactor SanitizerEngine in scenario/sanitizer_engine.py to prevent command injection and subshell escape bypasses, verifying SymPy VRAM cost bounds and FastEmbed CPU isolation.

outcome:
  1. Inspect scenario/sanitizer_engine.py.
  2. Frame analysis using Declarative Attention and verify hypotheses with OpenJEV.
  3. Apply surgical patch ensuring subshell $(...) and backtick escapes are strictly neutralized.
  4. All tests in scenario/test_sanitizer.py pass with exit code 0.

verify: pytest scenario/test_sanitizer.py -q
```
