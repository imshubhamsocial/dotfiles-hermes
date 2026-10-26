# Phase 16: Dream-RSI Replay Simulator & MASS Loop — Specification Manifest

> **Phase ID**: `phase_16_dream_rsi_replay_simulator_mass_loop`  
> **Canonical Enterprise Tool / Framework**: `diskcache.Cache(persist=True) \+ Doubly Robust (DR) Estimator1`  
> **ICM Architectural Layer**: `**Layer 2** Position-Addressed Replay Trees (.hermes/cache/dream\_worlds/)1`  
> **Hardware Boundary Assertion**: `0.0 MiB CUDA; single-slot \-np 1 reuse1`  

---

## 1. Master Matrix Realignment Summary
| Field | Specification |
| :--- | :--- |
| **Capability Title** | Dream-RSI Replay Simulator & MASS Loop |
| **Enterprise Toolkit** | diskcache.Cache(persist=True) \+ Doubly Robust (DR) Estimator1 |
| **ICM Layer / Stage** | **Layer 2** Position-Addressed Replay Trees (.hermes/cache/dream\_worlds/)1 |
| **Primary Verification Gate** | `pytest tests/phase16\_dream\_rsi\_eval/ \-q1` |
| **Hardware Assertion** | 0.0 MiB CUDA; single-slot \-np 1 reuse1 |

---

## 2. Exhaustive Phase Specification
Phase 16 integrates Google DeepMind Dream-RSI (DreamReplayEngine), diskcache.Cache(".hermes/cache/dream\_worlds", persist=True), and 3-Pass MASS role-switched self-improvement1. Serving as the **Layer 2 Position-Addressed Replay Cache**, it persists counterfactual trajectory trees as content-addressed JSON files (.hermes/cache/dream\_worlds/\<sha256\>.json), decoupling offline policy evaluation from live session context while reusing the single GPU slot (-np 1\) with 0.0 MiB extra VRAM (6/6 tests pass in 0.02s)1. The exact verification contract (![][image73]) is:

---

## 3. Operational Invariants for Active Stage
1. **Sub-8K Context Discipline**: Read ONLY this file during Stage `01_spec`. Do not load other phases.
2. **Turn 1 Reconnaissance**: Emit `<deliberation><global>...</global></deliberation>`, call `jev_compile_intent` and `extract_workspace_ast`.
3. **Task Formulation**: Populate `02_impl/task.md` with target files and symbols before advancing to Stage `02_impl`.


<!-- Embedded Formula References -->
[image73]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEEAAAAVCAYAAAAZ6IOkAAACnElEQVR4Xu2XW4hOURTH/24R5VJueZA7eZOS5OFLLgmRwhNNCY1mXB/cGbkToUSiBiGXEnKJRimUS7yIIk+SZ4+88P+31nb2bIOvmTMvp/OvX9/ea+2zzz7rrL3O/oBSpUqVKvWHOpDb5Bv56bwnE+NB1Fn3ic9kUXN3MTQX9oBnUoerI3lD5qSOImkcLAj3UoernuxKjUVTT2RbIdVA8oh0Th1F1FfyHVYnYp0noxNbYfUMlg0DIttssi7qF16XYEGY4P1ebkszI09NSQ05qdXz7oUFYb73j5Ahv735S7XmaGrMSVdSQ7VaAQvCKjKJLG3uzlU9yEXkHwRl7XryOnVUq+mwIBwn+xJf0AzSRDbCDlCdYDc+5H1du8nHKpBvSSNsPj3wbvcpXR+SJ2QbGUumkQ/kFqwYaz5Jdemkj9tDurtd0jruwuZdS4bBzjpfYONnZkOr01BYELSQvolPGk4+kT6kH+whBpFacjoad50s9/Ya2Hxdva/rx3hbi0wzYSt5SkaQOrctIyu9vYMc9LZOrVqDNBVWv6QK2pAJOhX+gL3tlqSo30+NsEXXRH2l4x1v65AVFie9Q3YkbykIyqJjiU3ZNs99N8hlt+sem8OgSBW0IQj/kxat1Ev1Eva2gnSy1OFK0hu8EPkUBG0TKQ5CqOZ60MPeDrpJDnhbGXbV28qCsPViVZAFodVfib9pJOxA1dv7k93WgOxhupDnsC0iqcimQdB1kvbwKdKNbHGbfuMgaD5tUd1H2kCukZ1kCSwQ4RNeA8ua8bD7SO1y1J9FXsAm19dEUqFSmjbCCl2w67zxALagBbA9rn+r58hg0t/bCsQo2Bt8TD7CtlHQflg2NJDV5BVZ7L7tyAq16oKkoJyAFeuFbiv1L/0CauSEJ1Lri1UAAAAASUVORK5CYII=>

