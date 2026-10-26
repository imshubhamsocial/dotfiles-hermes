# Phase 31: Gemma CPU Sidecars & Neuro-Symbolic ARC-AGI — Specification Manifest

> **Phase ID**: `phase_31_gemma_cpu_sidecars_neuro_symbolic_arc_agi`  
> **Canonical Enterprise Tool / Framework**: `jev\_gemma\_sidecar\_embed\_and\_refine \+ jev\_arc\_agi\_neurosymbolic\_solve1`  
> **ICM Architectural Layer**: `**Layer 3** In-Process CPU Sidecars & DSL Synthesis1`  
> **Hardware Boundary Assertion**: `0.0 MiB CUDA (![][image71] host DDR5 RAM)1`  

---

## 1. Master Matrix Realignment Summary
| Field | Specification |
| :--- | :--- |
| **Capability Title** | Gemma CPU Sidecars & Neuro-Symbolic ARC-AGI |
| **Enterprise Toolkit** | jev\_gemma\_sidecar\_embed\_and\_refine \+ jev\_arc\_agi\_neurosymbolic\_solve1 |
| **ICM Layer / Stage** | **Layer 3** In-Process CPU Sidecars & DSL Synthesis1 |
| **Primary Verification Gate** | `python3 \-c "import mcp\_openjev as m; assert m.jev\_arc\_agi\_neurosymbolic\_solve(\[\], \[\[7,1\],\[2,6\]\])\['rhae\_score'\]==1.0"1` |
| **Hardware Assertion** | 0.0 MiB CUDA (![][image71] host DDR5 RAM)1 |

---

## 2. Exhaustive Phase Specification
Phase 31 pins \_GemmaCPUSidecarPool (EmbeddingGemma 2 256d MRL L2-norm \+ T5Gemma 2 270M-270M) and jev\_arc\_agi\_neurosymbolic\_solve inside .hermes/mcp\_openjev.py1. Operating as **Layer 3 In-Process CPU Sidecars**, it ranks code chunks above prose docstrings (0.7842 vs. 0.5968, margin \+0.1874) in 1.46 ms for Stage 01\_spec/ retrieval and synthesizes executable Python grid transformations (def transform(grid): ...) for Stage 02\_impl/ with Relative Human-Action Efficiency ![][image93], consuming \~1.16 GB host DDR5 RAM (540 MiB T5Gemma 2 \+ 620 MiB EmbeddingGemma 2\) and 0.0 MiB CUDA VRAM delta1. The exact verification contract (![][image73]) is:

---

## 3. Operational Invariants for Active Stage
1. **Sub-8K Context Discipline**: Read ONLY this file during Stage `01_spec`. Do not load other phases.
2. **Turn 1 Reconnaissance**: Emit `<deliberation><global>...</global></deliberation>`, call `jev_compile_intent` and `extract_workspace_ast`.
3. **Task Formulation**: Populate `02_impl/task.md` with target files and symbols before advancing to Stage `02_impl`.


<!-- Embedded Formula References -->
[image71]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFMAAAASCAYAAAAntuLJAAAAkUlEQVR4Xu3SoQ0CQRBA0XU0gDpCQgW4Ezg8JZAgEScJBoOmBVpAUQMeS4KhACQ0wN/kyLFLcg3sf8k3M6s2E4IkSZIklWhNT7rRnsbpOtHkA3VqOtOKFrSjB81/3nxNaJsP1TnSIJtN6U4bGrazii6h/2qLd8gHrfiJJ3rRld60TF7oT7y4PvFqZzTKF5JUkA8/mA7TdiXVWQAAAABJRU5ErkJggg==>

[image73]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEEAAAAVCAYAAAAZ6IOkAAACnElEQVR4Xu2XW4hOURTH/24R5VJueZA7eZOS5OFLLgmRwhNNCY1mXB/cGbkToUSiBiGXEnKJRimUS7yIIk+SZ4+88P+31nb2bIOvmTMvp/OvX9/ea+2zzz7rrL3O/oBSpUqVKvWHOpDb5Bv56bwnE+NB1Fn3ic9kUXN3MTQX9oBnUoerI3lD5qSOImkcLAj3UoernuxKjUVTT2RbIdVA8oh0Th1F1FfyHVYnYp0noxNbYfUMlg0DIttssi7qF16XYEGY4P1ebkszI09NSQ05qdXz7oUFYb73j5Ahv735S7XmaGrMSVdSQ7VaAQvCKjKJLG3uzlU9yEXkHwRl7XryOnVUq+mwIBwn+xJf0AzSRDbCDlCdYDc+5H1du8nHKpBvSSNsPj3wbvcpXR+SJ2QbGUumkQ/kFqwYaz5Jdemkj9tDurtd0jruwuZdS4bBzjpfYONnZkOr01BYELSQvolPGk4+kT6kH+whBpFacjoad50s9/Ya2Hxdva/rx3hbi0wzYSt5SkaQOrctIyu9vYMc9LZOrVqDNBVWv6QK2pAJOhX+gL3tlqSo30+NsEXXRH2l4x1v65AVFie9Q3YkbykIyqJjiU3ZNs99N8hlt+sem8OgSBW0IQj/kxat1Ev1Eva2gnSy1OFK0hu8EPkUBG0TKQ5CqOZ60MPeDrpJDnhbGXbV28qCsPViVZAFodVfib9pJOxA1dv7k93WgOxhupDnsC0iqcimQdB1kvbwKdKNbHGbfuMgaD5tUd1H2kCukZ1kCSwQ4RNeA8ua8bD7SO1y1J9FXsAm19dEUqFSmjbCCl2w67zxALagBbA9rn+r58hg0t/bCsQo2Bt8TD7CtlHQflg2NJDV5BVZ7L7tyAq16oKkoJyAFeuFbiv1L/0CauSEJ1Lri1UAAAAASUVORK5CYII=>

[image93]: <data:image/png;base64,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>

