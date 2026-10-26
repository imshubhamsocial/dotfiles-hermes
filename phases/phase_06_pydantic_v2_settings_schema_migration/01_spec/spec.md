# Phase 06: Pydantic v2 Settings & Schema Migration — Specification Manifest

> **Phase ID**: `phase_06_pydantic_v2_settings_schema_migration`  
> **Canonical Enterprise Tool / Framework**: `pydantic \>= 2.9.0 \+ pydantic-settings \>= 2.5.0 (extra="forbid")1`  
> **ICM Architectural Layer**: `**30% Orchestration** (SafePathModel in mcp\_openjev.py)5`  
> **Hardware Boundary Assertion**: `0.0 MiB CUDA (CPU schema validation)6`  

---

## 1. Master Matrix Realignment Summary
| Field | Specification |
| :--- | :--- |
| **Capability Title** | Pydantic v2 Settings & Schema Migration |
| **Enterprise Toolkit** | pydantic \>= 2.9.0 \+ pydantic-settings \>= 2.5.0 (extra="forbid")1 |
| **ICM Layer / Stage** | **30% Orchestration** (SafePathModel in mcp\_openjev.py)5 |
| **Primary Verification Gate** | `pytest tests/phase01\_canonical\_parity/ \-k pydantic \-q6` |
| **Hardware Assertion** | 0.0 MiB CUDA (CPU schema validation)6 |

---

## 2. Exhaustive Phase Specification
Phase 06 enforces pydantic \>= 2.9.0 and pydantic-settings \>= 2.5.0 with ConfigDict(extra="forbid") and @field\_validator regex path sanitizers across all tool models1. Within the **30% Deterministic Orchestration Layer**, SafePathModel protects position-addressed file targets by snapping malformed BPE path emissions (.py\_py, \_py, .p, dagpy) to canonical stage paths before disk I/O occurs2. Schema validation executes in sub-millisecond CPU time inside the FastMCP stdio worker with 0.0 MiB CUDA delta5. The exact verification contract (![][image73]) is:

---

## 3. Operational Invariants for Active Stage
1. **Sub-8K Context Discipline**: Read ONLY this file during Stage `01_spec`. Do not load other phases.
2. **Turn 1 Reconnaissance**: Emit `<deliberation><global>...</global></deliberation>`, call `jev_compile_intent` and `extract_workspace_ast`.
3. **Task Formulation**: Populate `02_impl/task.md` with target files and symbols before advancing to Stage `02_impl`.


<!-- Embedded Formula References -->
[image73]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEEAAAAVCAYAAAAZ6IOkAAACnElEQVR4Xu2XW4hOURTH/24R5VJueZA7eZOS5OFLLgmRwhNNCY1mXB/cGbkToUSiBiGXEnKJRimUS7yIIk+SZ4+88P+31nb2bIOvmTMvp/OvX9/ea+2zzz7rrL3O/oBSpUqVKvWHOpDb5Bv56bwnE+NB1Fn3ic9kUXN3MTQX9oBnUoerI3lD5qSOImkcLAj3UoernuxKjUVTT2RbIdVA8oh0Th1F1FfyHVYnYp0noxNbYfUMlg0DIttssi7qF16XYEGY4P1ebkszI09NSQ05qdXz7oUFYb73j5Ahv735S7XmaGrMSVdSQ7VaAQvCKjKJLG3uzlU9yEXkHwRl7XryOnVUq+mwIBwn+xJf0AzSRDbCDlCdYDc+5H1du8nHKpBvSSNsPj3wbvcpXR+SJ2QbGUumkQ/kFqwYaz5Jdemkj9tDurtd0jruwuZdS4bBzjpfYONnZkOr01BYELSQvolPGk4+kT6kH+whBpFacjoad50s9/Ya2Hxdva/rx3hbi0wzYSt5SkaQOrctIyu9vYMc9LZOrVqDNBVWv6QK2pAJOhX+gL3tlqSo30+NsEXXRH2l4x1v65AVFie9Q3YkbykIyqJjiU3ZNs99N8hlt+sem8OgSBW0IQj/kxat1Ev1Eva2gnSy1OFK0hu8EPkUBG0TKQ5CqOZ60MPeDrpJDnhbGXbV28qCsPViVZAFodVfib9pJOxA1dv7k93WgOxhupDnsC0iqcimQdB1kvbwKdKNbHGbfuMgaD5tUd1H2kCukZ1kCSwQ4RNeA8ua8bD7SO1y1J9FXsAm19dEUqFSmjbCCl2w67zxALagBbA9rn+r58hg0t/bCsQo2Bt8TD7CtlHQflg2NJDV5BVZ7L7tyAq16oKkoJyAFeuFbiv1L/0CauSEJ1Lri1UAAAAASUVORK5CYII=>

