# Phase 12: SoL-Pi Runtime Harness & Two-Strike Tabu — Specification Manifest

> **Phase ID**: `phase_12_sol_pi_runtime_harness_two_strike_tabu`  
> **Canonical Enterprise Tool / Framework**: `Upstream run\_agent.py \+ FastMCP 40/60 Truncation \+ Git1`  
> **ICM Architectural Layer**: `**Layer 1** Law 6 \+ **Stage 02\_impl/** Two-Strike Rollback1`  
> **Hardware Boundary Assertion**: `0.0 MiB CUDA; ![][image54] token reduction1`  

---

## 1. Master Matrix Realignment Summary
| Field | Specification |
| :--- | :--- |
| **Capability Title** | SoL-Pi Runtime Harness & Two-Strike Tabu |
| **Enterprise Toolkit** | Upstream run\_agent.py \+ FastMCP 40/60 Truncation \+ Git1 |
| **ICM Layer / Stage** | **Layer 1** Law 6 \+ **Stage 02\_impl/** Two-Strike Rollback1 |
| **Primary Verification Gate** | `pytest tests/phase12\_sol\_pi\_eval/ \-q1` |
| **Hardware Assertion** | 0.0 MiB CUDA; ![][image54] token reduction1 |

---

## 2. Exhaustive Phase Specification
Phase 12 combines Claude Code SoL-Pi 40/60 head-tail output truncation (preserving the final 600 bytes of Python tracebacks) with the Two-Strike Tabu hard revert (git checkout HEAD \-- \<file\>) inside FastMCP execution wrappers1. This enforces **Layer 1 Law 6** and the **Stage 02\_impl/ Rollback Pattern**, preventing traceback floods from violating the Sub-8K Context Discipline (76.91% measured token reduction) and reverting 02\_impl/ to clean HEAD on two consecutive failures with 0.0 MiB CUDA delta (5/5 tests pass in 0.42s)1. The exact verification contract (![][image73]) is:

---

## 3. Operational Invariants for Active Stage
1. **Sub-8K Context Discipline**: Read ONLY this file during Stage `01_spec`. Do not load other phases.
2. **Turn 1 Reconnaissance**: Emit `<deliberation><global>...</global></deliberation>`, call `jev_compile_intent` and `extract_workspace_ast`.
3. **Task Formulation**: Populate `02_impl/task.md` with target files and symbols before advancing to Stage `02_impl`.


<!-- Embedded Formula References -->
[image54]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADgAAAASCAYAAAAOsR1OAAADWUlEQVR4Xu2XWaiOURSGX/M8z8kYRaHMQ+SCC0TJUMpMITIkiYwlZB4jUeZ5SopCHJI55IIkQ+HCUIqkSLyv9e1z1r/P9/+HKylvPZ1/r72+vb/17bXX3gf4r//6G+pAjpD5pGbUF1SRbAmNCWRzQV9OlSGzyUVynqwkJTI80lWNnCQPyFuygpTO8MhUQ6SP2548hPUPJC/JIBT4KrAh5C6ZkdiwjPzIQdPErxIssD2wAWuTJ2RS0p9NFchN2McoTuqSPLLE+UgKuC1ZTN7DViqW5t7g2hfIZLKXnCA3yGFyDe4DHUDhoAIHgxPsBTWxVlHqD/PZlu+Rrq0wvxbO1pd8h61EkFbjDCwz5J8W4COywLVXk86uLSmeNt5wldTwBthXvpX8laqTL3B5DVsZpXYrZ0vTM9gLyz+oZWJLW31tgWwBKsUXufYaZPqNJ8td+5fWxgbqLOnn2qNhk05ztt/VO9izZZ1NaZ9t9XMFqFRc79rnSJXktxbjNilX0J2ucSgctL6UJlVBOkWukGNIf4lY2qd61k/cLrFprFi5AlQ6PodlXC+y3fUp+N6unarK5A1pFNl3wiZ9DEsvaRT5iKJTNOzBUKykqYlN2yBWrgClYbAipe0RsqIn2R0ccmk6rJzHUrHRpH5li8HS76izpakWLHWWwqpoA7IfNt4l5xdUVICxSsKqezgTVe1XkUP5Hok0uQrCwrgDVlw0qdLXS2fSV9j5k0uadB2sfGtFu8DGU6CxQoAd444smklGJr/10fNg71knOAR1gw08NO6AnVnqGxDZVdVkrxfZi1IP2HNpRetPAmwCO/+CtAc/wRarkGbBBu4ed1CDYX26JXjpXJLdHwGxmsNSvLWzKbBvsMtCrBBgp7gjRaeRWS/mkVeunSHtJQ2sCherPPlA5jib0kEHv/I/SJVSKVPf2SbCxp3rbKrCunGkKQQYH+CxhsPm8tKzryNbvq7DBs5WFcfCSrSKhDQG9rX8yoSXO+5sXWGXhGakFOxqpdRW8UmTaoDG0DGQTVVhZ3V8X+1DPqfYf2kHLABdjLNpCnlK7sOuVI0zeguuYHGhGkH2kTtkI+xmFGsXeQELTqh4XYZ9kFibYBfvWPqAKmTKGmXdPyntTf03kk2632pv3vsJB7DFL9CM5bcAAAAASUVORK5CYII=>

[image73]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEEAAAAVCAYAAAAZ6IOkAAACnElEQVR4Xu2XW4hOURTH/24R5VJueZA7eZOS5OFLLgmRwhNNCY1mXB/cGbkToUSiBiGXEnKJRimUS7yIIk+SZ4+88P+31nb2bIOvmTMvp/OvX9/ea+2zzz7rrL3O/oBSpUqVKvWHOpDb5Bv56bwnE+NB1Fn3ic9kUXN3MTQX9oBnUoerI3lD5qSOImkcLAj3UoernuxKjUVTT2RbIdVA8oh0Th1F1FfyHVYnYp0noxNbYfUMlg0DIttssi7qF16XYEGY4P1ebkszI09NSQ05qdXz7oUFYb73j5Ahv735S7XmaGrMSVdSQ7VaAQvCKjKJLG3uzlU9yEXkHwRl7XryOnVUq+mwIBwn+xJf0AzSRDbCDlCdYDc+5H1du8nHKpBvSSNsPj3wbvcpXR+SJ2QbGUumkQ/kFqwYaz5Jdemkj9tDurtd0jruwuZdS4bBzjpfYONnZkOr01BYELSQvolPGk4+kT6kH+whBpFacjoad50s9/Ya2Hxdva/rx3hbi0wzYSt5SkaQOrctIyu9vYMc9LZOrVqDNBVWv6QK2pAJOhX+gL3tlqSo30+NsEXXRH2l4x1v65AVFie9Q3YkbykIyqJjiU3ZNs99N8hlt+sem8OgSBW0IQj/kxat1Ev1Eva2gnSy1OFK0hu8EPkUBG0TKQ5CqOZ60MPeDrpJDnhbGXbV28qCsPViVZAFodVfib9pJOxA1dv7k93WgOxhupDnsC0iqcimQdB1kvbwKdKNbHGbfuMgaD5tUd1H2kCukZ1kCSwQ4RNeA8ua8bD7SO1y1J9FXsAm19dEUqFSmjbCCl2w67zxALagBbA9rn+r58hg0t/bCsQo2Bt8TD7CtlHQflg2NJDV5BVZ7L7tyAq16oKkoJyAFeuFbiv1L/0CauSEJ1Lri1UAAAAASUVORK5CYII=>

