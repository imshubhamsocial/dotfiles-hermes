# Phase 13: STAIR Structural AST & 5-Layer Memory — Specification Manifest

> **Phase ID**: `phase_13_stair_structural_ast_5_layer_memory`  
> **Canonical Enterprise Tool / Framework**: `@ast-grep/cli \+ Python ast.walk \+ OpenViking Port 19331`  
> **ICM Architectural Layer**: `**Stage 01\_spec/** Structural Outline Discovery1`  
> **Hardware Boundary Assertion**: `0.0 MiB CUDA; Recall@1 \== ![][image55]1`  

---

## 1. Master Matrix Realignment Summary
| Field | Specification |
| :--- | :--- |
| **Capability Title** | STAIR Structural AST & 5-Layer Memory |
| **Enterprise Toolkit** | @ast-grep/cli \+ Python ast.walk \+ OpenViking Port 19331 |
| **ICM Layer / Stage** | **Stage 01\_spec/** Structural Outline Discovery1 |
| **Primary Verification Gate** | `pytest tests/phase13\_stair\_memory\_eval/ \-q1` |
| **Hardware Assertion** | 0.0 MiB CUDA; Recall@1 \== ![][image55]1 |

---

## 2. Exhaustive Phase Specification
Phase 13 executes @ast-grep/cli \>= 0.45.3 and Python ast.walk inside extract\_workspace\_ast paired with OpenViking Port 19331. Governing **Stage 01\_spec/ Reconnaissance**, it populates 01\_spec/spec.md with exact line-bounded symbol tables (L\<start\>-L\<end\>: ClassDef/FunctionDef) so the model never loads entire 1,000-line files into active context1. All AST parsing and BGE-small vector lookups execute 100% on CPU (0.0 MiB CUDA delta; Recall@1 \== 100.0%; 5/5 tests pass in 0.48s)1. The exact verification contract (![][image73]) is:

---

## 3. Operational Invariants for Active Stage
1. **Sub-8K Context Discipline**: Read ONLY this file during Stage `01_spec`. Do not load other phases.
2. **Turn 1 Reconnaissance**: Emit `<deliberation><global>...</global></deliberation>`, call `jev_compile_intent` and `extract_workspace_ast`.
3. **Task Formulation**: Populate `02_impl/task.md` with target files and symbols before advancing to Stage `02_impl`.


<!-- Embedded Formula References -->
[image55]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADgAAAASCAYAAAAOsR1OAAADD0lEQVR4Xu2XW8hOQRSGl/MhcsypkCQRLpwpKSRcIUrhVyRygRQpxwslIWeF5HwsZ0WO/wUi5ZcLQqIQF0qRlBve91uz/2/ttff+zJ3U/9Rbe96Zb82smb1n5hOpo45/wWDoLLQaau/qElpAe71J6kE9vGmYDV2DHoh20j1dXaITdBC6Cz2C5qerK/K3+IOg51A3aDL0HpoKNQj1TGwa9ARaGrwSXUR/cBO6YCsMi6CnUIdQXgt9NmXCGX0m2pZ0hV5D65MGFYiJfxTaYcq3RH93DDoPPYTOiE5QkrQsFh3UbuiX5CfYEfoJTTdefdEZXG68raKxLAuhL1Aj51ti47+A1pjyFmiYKZOT0ADn1fJD8hOcB/2W7A85g9dN+Z3oDFrGiP52lPMtsfE5eetMmRPKbzKBcTaacoaiBLm6HABfOQtfi+9QU9Fvj232pVrod0Ofm0IRMfEJX8Xt5Wq5AbUKz+z/MdSsXJ2lKEF6HACDWE4Hv6foTPKZg7X0D/4h51ti4hO+jm+hdtBY6EDwCZMfZ8q5FCXImcobwIng94FGh2efYN/gH3e+JSZ+wgyoWrSfZGXZ95GkQSWKErwq+QPgoOn3gkaEZ58gB0e/0gBi4hfRELoj5TOxJbRZdPUzMMGL3hRdfnbU2fmngs9Xpnd43pNqIdIv+Nucb4mJX8Qy0fOT8ByvhuaK7swZihLkh82O/CWAbelzS+cM8pmHvGVI8O327omJnwfbcyNK4DfITamofSnBS94Ec0Q7Guj8e9B9U34FnTNlMlH0t5Ocb4mN77ki6dvOKuiDKWdggpe9CdpA36Aq4zUWPcCXGG8D9FL0VUngQf1J0gf9LGikKcfGt8wUfT0tK6CPzqulieht4rakB5jAq5y9AvGOWSPlnYzwmTPOtoRnEleVCSUMF12tr8YjMfETWoveWWuvY4EJoouU8nnT4B2OybFj6o3ovZSXV8t40R2Km8JOqG26ugS9ldBhaD80JVWrHz9XhvE9MfHJLtELhIdvCSdpAdTc1f03DIU2edPAfxr8Nmv+AGqoys9PLbH2AAAAAElFTkSuQmCC>

[image73]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEEAAAAVCAYAAAAZ6IOkAAACnElEQVR4Xu2XW4hOURTH/24R5VJueZA7eZOS5OFLLgmRwhNNCY1mXB/cGbkToUSiBiGXEnKJRimUS7yIIk+SZ4+88P+31nb2bIOvmTMvp/OvX9/ea+2zzz7rrL3O/oBSpUqVKvWHOpDb5Bv56bwnE+NB1Fn3ic9kUXN3MTQX9oBnUoerI3lD5qSOImkcLAj3UoernuxKjUVTT2RbIdVA8oh0Th1F1FfyHVYnYp0noxNbYfUMlg0DIttssi7qF16XYEGY4P1ebkszI09NSQ05qdXz7oUFYb73j5Ahv735S7XmaGrMSVdSQ7VaAQvCKjKJLG3uzlU9yEXkHwRl7XryOnVUq+mwIBwn+xJf0AzSRDbCDlCdYDc+5H1du8nHKpBvSSNsPj3wbvcpXR+SJ2QbGUumkQ/kFqwYaz5Jdemkj9tDurtd0jruwuZdS4bBzjpfYONnZkOr01BYELSQvolPGk4+kT6kH+whBpFacjoad50s9/Ya2Hxdva/rx3hbi0wzYSt5SkaQOrctIyu9vYMc9LZOrVqDNBVWv6QK2pAJOhX+gL3tlqSo30+NsEXXRH2l4x1v65AVFie9Q3YkbykIyqJjiU3ZNs99N8hlt+sem8OgSBW0IQj/kxat1Ev1Eva2gnSy1OFK0hu8EPkUBG0TKQ5CqOZ60MPeDrpJDnhbGXbV28qCsPViVZAFodVfib9pJOxA1dv7k93WgOxhupDnsC0iqcimQdB1kvbwKdKNbHGbfuMgaD5tUd1H2kCukZ1kCSwQ4RNeA8ua8bD7SO1y1J9FXsAm19dEUqFSmjbCCl2w67zxALagBbA9rn+r58hg0t/bCsQo2Bt8TD7CtlHQflg2NJDV5BVZ7L7tyAq16oKkoJyAFeuFbiv1L/0CauSEJ1Lri1UAAAAASUVORK5CYII=>

