# Phase 21: Google ADK 2.9+ TaskDAG & A2A Federation — Specification Manifest

> **Phase ID**: `phase_21_google_adk_2_9_taskdag_a2a_federation`  
> **Canonical Enterprise Tool / Framework**: `google-adk \>= 2.9.0 \+ LangGraph \+ jev\_taskdag\_plan1`  
> **ICM Architectural Layer**: `**30% Orchestration** Staged Inode Progression (01\_spec ![][image25] 03\_verify)2`  
> **Hardware Boundary Assertion**: `0.0 MiB CUDA delta (shared Port 8138 slot)1`  

---

## 1. Master Matrix Realignment Summary
| Field | Specification |
| :--- | :--- |
| **Capability Title** | Google ADK 2.9+ TaskDAG & A2A Federation |
| **Enterprise Toolkit** | google-adk \>= 2.9.0 \+ LangGraph \+ jev\_taskdag\_plan1 |
| **ICM Layer / Stage** | **30% Orchestration** Staged Inode Progression (01\_spec ![][image25] 03\_verify)2 |
| **Primary Verification Gate** | `pytest tests/phase21\_adk\_taskdag\_eval/ \-q1` |
| **Hardware Assertion** | 0.0 MiB CUDA delta (shared Port 8138 slot)1 |

---

## 2. Exhaustive Phase Specification
Phase 21 deploys google-adk \>= 2.9.0 (SequentialAgent, LlmAgent, EventActions(transfer\_to\_agent=...)), langgraph \>= 0.2.35, and Kahn’s topological sort (jev\_taskdag\_plan)1. Enforcing **30% Orchestration Staged Inode Progression**, it binds four privilege-isolated ADK personas directly to ICM stage folders: @architect writes 01\_spec/spec.md (read-only AST access), @coder mutates 02\_impl/ (surgical diffs), @tester executes 03\_verify/ (pytest), and @critic records trajectories into 03\_verify/status.json1. Sharing Port 8138 Slot 0 sequentially with identical \--keep 4096 prefixes yields 0.0 MiB CUDA delta, 0 context pollution tokens, and 0 circular deadlocks (7/7 tests pass in 0.02s)1. The exact verification contract (![][image73]) is:

---

## 3. Operational Invariants for Active Stage
1. **Sub-8K Context Discipline**: Read ONLY this file during Stage `01_spec`. Do not load other phases.
2. **Turn 1 Reconnaissance**: Emit `<deliberation><global>...</global></deliberation>`, call `jev_compile_intent` and `extract_workspace_ast`.
3. **Task Formulation**: Populate `02_impl/task.md` with target files and symbols before advancing to Stage `02_impl`.


<!-- Embedded Formula References -->
[image25]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABUAAAAVCAYAAACpF6WWAAAAbklEQVR4XmNgGAWjYFCAAHQBaoANQCyILkgpcAHiCnRBaoAeILZCF6QUMAPxSiCuBGJWNDkwWAjEu8nAF4D4HRAnMlAJiALxeiAWQ5cgFzAB8VYglkSXoAQEA3E0uiClAORtrJFDCdBDFxgFcAAAUUUTNyPN6gQAAAAASUVORK5CYII=>

[image73]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEEAAAAVCAYAAAAZ6IOkAAACnElEQVR4Xu2XW4hOURTH/24R5VJueZA7eZOS5OFLLgmRwhNNCY1mXB/cGbkToUSiBiGXEnKJRimUS7yIIk+SZ4+88P+31nb2bIOvmTMvp/OvX9/ea+2zzz7rrL3O/oBSpUqVKvWHOpDb5Bv56bwnE+NB1Fn3ic9kUXN3MTQX9oBnUoerI3lD5qSOImkcLAj3UoernuxKjUVTT2RbIdVA8oh0Th1F1FfyHVYnYp0noxNbYfUMlg0DIttssi7qF16XYEGY4P1ebkszI09NSQ05qdXz7oUFYb73j5Ahv735S7XmaGrMSVdSQ7VaAQvCKjKJLG3uzlU9yEXkHwRl7XryOnVUq+mwIBwn+xJf0AzSRDbCDlCdYDc+5H1du8nHKpBvSSNsPj3wbvcpXR+SJ2QbGUumkQ/kFqwYaz5Jdemkj9tDurtd0jruwuZdS4bBzjpfYONnZkOr01BYELSQvolPGk4+kT6kH+whBpFacjoad50s9/Ya2Hxdva/rx3hbi0wzYSt5SkaQOrctIyu9vYMc9LZOrVqDNBVWv6QK2pAJOhX+gL3tlqSo30+NsEXXRH2l4x1v65AVFie9Q3YkbykIyqJjiU3ZNs99N8hlt+sem8OgSBW0IQj/kxat1Ev1Eva2gnSy1OFK0hu8EPkUBG0TKQ5CqOZ60MPeDrpJDnhbGXbV28qCsPViVZAFodVfib9pJOxA1dv7k93WgOxhupDnsC0iqcimQdB1kvbwKdKNbHGbfuMgaD5tUd1H2kCukZ1kCSwQ4RNeA8ua8bD7SO1y1J9FXsAm19dEUqFSmjbCCl2w67zxALagBbA9rn+r58hg0t/bCsQo2Bt8TD7CtlHQflg2NJDV5BVZ7L7tyAq16oKkoJyAFeuFbiv1L/0CauSEJ1Lri1UAAAAASUVORK5CYII=>

