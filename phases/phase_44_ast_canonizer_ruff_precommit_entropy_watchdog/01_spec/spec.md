# Phase 44 Specification: 60% Infrastructure Compiler Gates (AST Canonizer, Ruff Pre-Commit & Entropy Watchdog)

* **ICM Layer**: Infrastructure (60% Allocation Tier)
* **Context Budget**: < 3,500 tokens (Sub-8K Compliant)
* **Input State**: Empirical HumanEval failures exhibiting 61.3% syntactic and signature drift (35.5% NameError, 16.1% SyntaxError, 9.7% TypeError), and problem 130 runaway token looping.
* **Process**:
  1. Deploy `scripts/hermes_ast_canonizer.py` implementing `CanonicalSignatureTransformer` to execute deterministic AST transformations:
     - Strip markdown fences and deduplicate nested/repeated `def` headers.
     - Strip orphan OOP `self` on standalone functions and rewrite recursive calls.
     - Align positional parameter names to match target docstring stubs.
  2. Deploy `scripts/hermes_ruff_precommit.py` to enforce static analysis linting (`ruff check --select F821,E999,F841`) before executing test assertions.
  3. Deploy `scripts/hermes_entropy_watchdog.py` implementing a sliding-window monitor (4-gram repetition ratio > 0.85, Shannon entropy < 1.5) that triggers slot erase via `POST http://127.0.0.1:8138/slots/0?action=erase` to abort infinite loops.
* **Output Artifacts**:
  - `scripts/hermes_ast_canonizer.py`
  - `scripts/hermes_ruff_precommit.py`
  - `scripts/hermes_entropy_watchdog.py`
