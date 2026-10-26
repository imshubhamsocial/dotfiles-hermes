# AGENTS.md — Phase 12 SoL-Pi Runtime Harness & Anti-Thrashing Testbed Orientation

> **Project**: Hermes Agent OS — Phase 12 Evaluation Harness  
> **Literature**: NVIDIA SoL-Pi (arXiv:2609.20519), Claude Code Pattern 6 (Two-Strike Tabu)  
> **Target Scenario**: `scenario/session_store.py` (Session iteration exception)  
> **Verification Gate**: `pytest tests/phase12_sol_pi_eval/ -q && python3 -c "import json; d=json.load(open('tests/phase12_sol_pi_eval/metrics.json')); assert d['token_reduction_pct'] >= 44.0 and d['tabu_halt_triggered'] is True and d['verifier_preserved_tracebacks'] is True"`

---

## 1. Goal Contract Standard

```text
/goal Refactor scenario/session_store.py to safely handle concurrent dictionary mutations during cleanup, strictly applying SoL-Pi coalesced dispatch and Two-Strike Tabu constraints.

outcome:
  1. Inspect scenario/session_store.py and identify the RuntimeError: dictionary changed size during iteration.
  2. Apply a surgical patch wrapping dictionary keys/items in a list snapshot under Karpathy U12 3x diff limit.
  3. Coalesce patch application with pytest execution in a single tool turn.
  4. Verify that failing test tracebacks are captured via the 1KB Head/Tail redirection wrapper without exit-code masking.
  5. All tests in scenario/test_session_store.py pass with exit code 0.

verify: pytest tests/phase12_sol_pi_eval/ -q && python3 -c "import json; d=json.load(open('tests/phase12_sol_pi_eval/metrics.json')); assert d['token_reduction_pct'] >= 44.0 and d['tabu_halt_triggered'] is True and d['verifier_preserved_tracebacks'] is True"

constraints:
  - Karpathy U12: patch must be <= 10 lines in session_store.py.
  - Two-Strike Tabu: if 2 consecutive identical diffs fail, execution must halt.
  - VRAM <= 4,812 MiB throughout.

boundaries: tests/phase12_sol_pi_eval/
```
