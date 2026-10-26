# Phase 26: Turn-0 Zero-Spoon Intent Compiler — Specification Manifest

> **Phase ID**: `phase_26_turn_0_zero_spoon_intent_compiler`  
> **Canonical Enterprise Tool / Framework**: `jev\_compile\_intent \+ /proc/\<ppid\>/cmdline Inspector1`  
> **ICM Architectural Layer**: `**Stage 01\_spec/** Turn-0 Sandbox Lock & Manifest Creation3`  
> **Hardware Boundary Assertion**: `0.0 MiB CUDA (![][image68] CPU latency)1`  

---

## 1. Master Matrix Realignment Summary
| Field | Specification |
| :--- | :--- |
| **Capability Title** | Turn-0 Zero-Spoon Intent Compiler |
| **Enterprise Toolkit** | jev\_compile\_intent \+ /proc/\<ppid\>/cmdline Inspector1 |
| **ICM Layer / Stage** | **Stage 01\_spec/** Turn-0 Sandbox Lock & Manifest Creation3 |
| **Primary Verification Gate** | `pytest tests/phase26\_zero\_spoon\_eval/ \-q1` |
| **Hardware Assertion** | 0.0 MiB CUDA (![][image68] CPU latency)1 |

---

## 2. Exhaustive Phase Specification
Phase 26 implements jev\_compile\_intent in .hermes/mcp\_openjev.py with /proc/\<ppid\>/cmdline (sys.argv) Turn-0 extraction and T5Gemma 2 CPU canonicalization1. Acting as the **Stage 01\_spec/ Automatic Bootstrapper**, it compiles raw, un-spoon-fed user prompts into .hermes/cache/intent\_manifests/\<hash\>.json, classifies the operational domain (DOMAIN\_A\_GUI, DOMAIN\_B\_HOME, DOMAIN\_C\_REPO), and locks sandbox\_target before Turn 1 in 1.46 ms on CPU RAM (0.0 MiB CUDA delta; 7/7 tests pass in 0.88s)1. The exact verification contract (![][image73]) is:

---

## 3. Operational Invariants for Active Stage
1. **Sub-8K Context Discipline**: Read ONLY this file during Stage `01_spec`. Do not load other phases.
2. **Turn 1 Reconnaissance**: Emit `<deliberation><global>...</global></deliberation>`, call `jev_compile_intent` and `extract_workspace_ast`.
3. **Task Formulation**: Populate `02_impl/task.md` with target files and symbols before advancing to Stage `02_impl`.


<!-- Embedded Formula References -->
[image68]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADsAAAASCAYAAADlhqZNAAACtUlEQVR4Xu2WS6hNURzGP295UyJRRAZCHiXvV5RQZECkbpkYiDKUkYEBSsqrJBkx8ibyqOst72cG8ojkMRAJUeL7/P/73v9Zd5/jnjM4t7hf/Tp7fWvvfda311r/vYFmNeufVAsyIDXL0AzyPDVdfch2cpmcJksLu6snDWQ+OUMOJX2NVRtyl7xKO6gh5CVZ7u3J5AsZWndGlbSK3CfbyA9UHnY1+Y78sFfJidDeSH6hCWdX0tOuJGxPcgMWSDMYNQcWbHHwBsOWdNfgVV2VhtXAZ5JjaDizu2FhRyR+k6uSsNqPB/04L+x1WFg9jPPkGtlBesWTEo0iT2DX7SfDYQ9U2+EA6e+or5acJfNQqFlkH7lI7iV9f1RJ2FNkkB/nhX0KG/Rx2LJVxd8FqxMdw3lRPcg08pY8htUTFUDpCrlJDqP+gW2B/U9rb+u+72HbS+rmvwUqN6z24+bQzgv7BhZW1T7TSPdUHEvpFvlI2gdvK+zascFbkngLyAfUh82VwuqJNUatyCXSPXh5YR/CBpLNvtTXPS2xUtIW0ExGaRZ1bdvgLXJvorcHkp+w2dU7fb37BSon7EqyIvHywtbCBtIleL3dexC8PGmPXki8LGy2ZKUs7KTgzYWNRb5oIIU9kppFpGDZjfLY6+dlg4tLqp97f5tZzWo5Yad4exgZ7cedyUI/LpDCHk1Nl55afFfm6TYazuwE2EDGB0/VVt664OVJy7icsFO9XQMrgkXVjnwj52AVM0rtz7AbaqDFpP2pgpRqD6wadyAtYe9ezWqpjwr9pyrxncTP3tvx2mXuzfa2wn4i4+rOcE2HvfsUNFuCKuP6Tu4UztPg3sFeC6nWkheov17Ha0K/lpI+EZ95305Y8GIaAwua3e8RbOAaZ+a9hn1uKrw+U+V9JRtgYTd5n3KcxP+k390CvKX4qOgTAAAAAElFTkSuQmCC>

[image73]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEEAAAAVCAYAAAAZ6IOkAAACnElEQVR4Xu2XW4hOURTH/24R5VJueZA7eZOS5OFLLgmRwhNNCY1mXB/cGbkToUSiBiGXEnKJRimUS7yIIk+SZ4+88P+31nb2bIOvmTMvp/OvX9/ea+2zzz7rrL3O/oBSpUqVKvWHOpDb5Bv56bwnE+NB1Fn3ic9kUXN3MTQX9oBnUoerI3lD5qSOImkcLAj3UoernuxKjUVTT2RbIdVA8oh0Th1F1FfyHVYnYp0noxNbYfUMlg0DIttssi7qF16XYEGY4P1ebkszI09NSQ05qdXz7oUFYb73j5Ahv735S7XmaGrMSVdSQ7VaAQvCKjKJLG3uzlU9yEXkHwRl7XryOnVUq+mwIBwn+xJf0AzSRDbCDlCdYDc+5H1du8nHKpBvSSNsPj3wbvcpXR+SJ2QbGUumkQ/kFqwYaz5Jdemkj9tDurtd0jruwuZdS4bBzjpfYONnZkOr01BYELSQvolPGk4+kT6kH+whBpFacjoad50s9/Ya2Hxdva/rx3hbi0wzYSt5SkaQOrctIyu9vYMc9LZOrVqDNBVWv6QK2pAJOhX+gL3tlqSo30+NsEXXRH2l4x1v65AVFie9Q3YkbykIyqJjiU3ZNs99N8hlt+sem8OgSBW0IQj/kxat1Ev1Eva2gnSy1OFK0hu8EPkUBG0TKQ5CqOZ60MPeDrpJDnhbGXbV28qCsPViVZAFodVfib9pJOxA1dv7k93WgOxhupDnsC0iqcimQdB1kvbwKdKNbHGbfuMgaD5tUd1H2kCukZ1kCSwQ4RNeA8ua8bD7SO1y1J9FXsAm19dEUqFSmjbCCl2w67zxALagBbA9rn+r58hg0t/bCsQo2Bt8TD7CtlHQflg2NJDV5BVZ7L7tyAq16oKkoJyAFeuFbiv1L/0CauSEJ1Lri1UAAAAASUVORK5CYII=>

