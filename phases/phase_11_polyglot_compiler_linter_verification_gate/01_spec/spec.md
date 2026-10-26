# Phase 11: Polyglot Compiler & Linter Verification Gate — Specification Manifest

> **Phase ID**: `phase_11_polyglot_compiler_linter_verification_gate`  
> **Canonical Enterprise Tool / Framework**: `ruff \>= 0.7.0 \+ pyright \+ Python ast.parse1`  
> **ICM Architectural Layer**: `**Stage 02\_impl/ ![][image25] 03\_verify/** Pre-Commit Gate2`  
> **Hardware Boundary Assertion**: `0.0 MiB CUDA (CPU AST & linter)5`  

---

## 1. Master Matrix Realignment Summary
| Field | Specification |
| :--- | :--- |
| **Capability Title** | Polyglot Compiler & Linter Verification Gate |
| **Enterprise Toolkit** | ruff \>= 0.7.0 \+ pyright \+ Python ast.parse1 |
| **ICM Layer / Stage** | **Stage 02\_impl/ ![][image25] 03\_verify/** Pre-Commit Gate2 |
| **Primary Verification Gate** | `ruff check .hermes/mcp\_openjev.py conftest.py1` |
| **Hardware Assertion** | 0.0 MiB CUDA (CPU AST & linter)5 |

---

## 2. Exhaustive Phase Specification
Phase 11 binds ruff \>= 0.7.0, pyright \>= 1.1.414, @biomejs/biome \>= 2.5.13, and Python ast.parse directly into the jev\_mutate\_module post-write hooks1. Functioning as the **Stage 02\_impl/ ![][image25] 03\_verify/ Transition Gate**, it enforces the Cursor/Claude Code Linter-Fix Invariant: malformed syntax is rejected in memory before touching the Stage 02\_impl/ disk inode, and ruff check executes immediately post-write on CPU (0.0 MiB CUDA delta)3. The exact verification contract (![][image73]) is:

---

## 3. Operational Invariants for Active Stage
1. **Sub-8K Context Discipline**: Read ONLY this file during Stage `01_spec`. Do not load other phases.
2. **Turn 1 Reconnaissance**: Emit `<deliberation><global>...</global></deliberation>`, call `jev_compile_intent` and `extract_workspace_ast`.
3. **Task Formulation**: Populate `02_impl/task.md` with target files and symbols before advancing to Stage `02_impl`.


<!-- Embedded Formula References -->
[image25]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABUAAAAVCAYAAACpF6WWAAAAbklEQVR4XmNgGAWjYFCAAHQBaoANQCyILkgpcAHiCnRBaoAeILZCF6QUMAPxSiCuBGJWNDkwWAjEu8nAF4D4HRAnMlAJiALxeiAWQ5cgFzAB8VYglkSXoAQEA3E0uiClAORtrJFDCdBDFxgFcAAAUUUTNyPN6gQAAAAASUVORK5CYII=>

[image73]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEEAAAAVCAYAAAAZ6IOkAAACnElEQVR4Xu2XW4hOURTH/24R5VJueZA7eZOS5OFLLgmRwhNNCY1mXB/cGbkToUSiBiGXEnKJRimUS7yIIk+SZ4+88P+31nb2bIOvmTMvp/OvX9/ea+2zzz7rrL3O/oBSpUqVKvWHOpDb5Bv56bwnE+NB1Fn3ic9kUXN3MTQX9oBnUoerI3lD5qSOImkcLAj3UoernuxKjUVTT2RbIdVA8oh0Th1F1FfyHVYnYp0noxNbYfUMlg0DIttssi7qF16XYEGY4P1ebkszI09NSQ05qdXz7oUFYb73j5Ahv735S7XmaGrMSVdSQ7VaAQvCKjKJLG3uzlU9yEXkHwRl7XryOnVUq+mwIBwn+xJf0AzSRDbCDlCdYDc+5H1du8nHKpBvSSNsPj3wbvcpXR+SJ2QbGUumkQ/kFqwYaz5Jdemkj9tDurtd0jruwuZdS4bBzjpfYONnZkOr01BYELSQvolPGk4+kT6kH+whBpFacjoad50s9/Ya2Hxdva/rx3hbi0wzYSt5SkaQOrctIyu9vYMc9LZOrVqDNBVWv6QK2pAJOhX+gL3tlqSo30+NsEXXRH2l4x1v65AVFie9Q3YkbykIyqJjiU3ZNs99N8hlt+sem8OgSBW0IQj/kxat1Ev1Eva2gnSy1OFK0hu8EPkUBG0TKQ5CqOZ60MPeDrpJDnhbGXbV28qCsPViVZAFodVfib9pJOxA1dv7k93WgOxhupDnsC0iqcimQdB1kvbwKdKNbHGbfuMgaD5tUd1H2kCukZ1kCSwQ4RNeA8ua8bD7SO1y1J9FXsAm19dEUqFSmjbCCl2w67zxALagBbA9rn+r58hg0t/bCsQo2Bt8TD7CtlHQflg2NJDV5BVZ7L7tyAq16oKkoJyAFeuFbiv1L/0CauSEJ1Lri1UAAAAASUVORK5CYII=>

