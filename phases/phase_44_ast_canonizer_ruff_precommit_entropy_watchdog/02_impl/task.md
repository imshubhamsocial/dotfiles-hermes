# Implementation Task Checklist: Phase 44

## 1. Concrete Symbol Targets
- `CanonicalSignatureTransformer` in `scripts/hermes_ast_canonizer.py`
- `sanitize_and_canonize_edit_surface` in `scripts/hermes_ast_canonizer.py`
- `execute_ruff_precommit_gate` in `scripts/hermes_ruff_precommit.py`
- `SlidingWindowShannonEntropyWatchdog` in `scripts/hermes_entropy_watchdog.py`
- `03_verify/contract.sh` in `phases/phase_44_ast_canonizer_ruff_precommit_entropy_watchdog/03_verify/contract.sh`

## 2. Causal Hypotheses
- **H1 (AST Signature Canonization)**: Transforming raw completions via `ast.NodeTransformer` to strip markdown fences, deduplicate outer `def` headers, remove hallucinated OOP `self`, and align positional parameter names with the canonical prompt stub eliminates 100% of signature mismatch errors (NameError 35.5%, SyntaxError 16.1%, TypeError 9.7%) in < 2ms at 0.0 MiB VRAM.
- **H2 (Ruff Pre-Commit Gate)**: Catching static analysis errors (`F821` undefined names, `E999` syntax errors, `F841` unused variables) before test execution prevents broken code from polluting test runner state.
- **H3 (Shannon Entropy Watchdog)**: Calculating 4-gram repetition ratio ($> 0.85$) and Shannon token entropy ($< 1.5$) over sliding windows halts infinite generation loops within 64 tokens via slot erase (`POST /slots/0?action=erase`).

## 3. Implementation Steps
- [x] Implement `scripts/hermes_ast_canonizer.py` with `CanonicalSignatureTransformer` and `sanitize_and_canonize_edit_surface`.
- [x] Implement `scripts/hermes_ruff_precommit.py` wrapping `ruff check`.
- [x] Implement `scripts/hermes_entropy_watchdog.py` for token loop detection and slot erase triggering.
- [ ] Implement and execute `03_verify/contract.sh` with empirical unit tests.
