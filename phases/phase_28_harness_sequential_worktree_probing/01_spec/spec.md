# Phase 28: Harness² Sequential Worktree Probing — Specification Manifest

> **Phase ID**: `phase_28_harness_sequential_worktree_probing`  
> **Canonical Enterprise Tool / Framework**: `jev\_harness2\_probe\_compose \+ fcntl.flock Slot 0 Mutex1`  
> **ICM Architectural Layer**: `**Stage 02\_impl/** Isolated Git Worktree Probing (/tmp/hermes\_probe\_\*)1`  
> **Hardware Boundary Assertion**: `0.0 MiB CUDA delta (sequential Slot 0 lock)1`  

---

## 1. Master Matrix Realignment Summary
| Field | Specification |
| :--- | :--- |
| **Capability Title** | Harness² Sequential Worktree Probing |
| **Enterprise Toolkit** | jev\_harness2\_probe\_compose \+ fcntl.flock Slot 0 Mutex1 |
| **ICM Layer / Stage** | **Stage 02\_impl/** Isolated Git Worktree Probing (/tmp/hermes\_probe\_\*)1 |
| **Primary Verification Gate** | `pytest tests/phase28\_harness2\_worktree\_eval/ \-q1` |
| **Hardware Assertion** | 0.0 MiB CUDA delta (sequential Slot 0 lock)1 |

---

## 2. Exhaustive Phase Specification
Phase 28 binds jev\_harness2\_probe\_compose to isolated Git worktrees (/tmp/hermes\_probe\_inv\_\<hash\> and /tmp/hermes\_probe\_dom\_\<hash\>) synchronized by POSIX fcntl.flock on /tmp/hermes\_port8138\_slot0.lock (LATENT-03)1. Governing **Stage 02\_impl/ Sandboxed Probing**, it evaluates invariant-hardened (![][image91]) vs. domain-specialized (![][image92]) patches in clean directories without polluting the main repository tree or overflowing the single GPU slot (0.0 MiB CUDA delta; 6/6 tests pass in 0.87s)1. The exact verification contract (![][image73]) is:

---

## 3. Operational Invariants for Active Stage
1. **Sub-8K Context Discipline**: Read ONLY this file during Stage `01_spec`. Do not load other phases.
2. **Turn 1 Reconnaissance**: Emit `<deliberation><global>...</global></deliberation>`, call `jev_compile_intent` and `extract_workspace_ast`.
3. **Task Formulation**: Populate `02_impl/task.md` with target files and symbols before advancing to Stage `02_impl`.


<!-- Embedded Formula References -->
[image73]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEEAAAAVCAYAAAAZ6IOkAAACnElEQVR4Xu2XW4hOURTH/24R5VJueZA7eZOS5OFLLgmRwhNNCY1mXB/cGbkToUSiBiGXEnKJRimUS7yIIk+SZ4+88P+31nb2bIOvmTMvp/OvX9/ea+2zzz7rrL3O/oBSpUqVKvWHOpDb5Bv56bwnE+NB1Fn3ic9kUXN3MTQX9oBnUoerI3lD5qSOImkcLAj3UoernuxKjUVTT2RbIdVA8oh0Th1F1FfyHVYnYp0noxNbYfUMlg0DIttssi7qF16XYEGY4P1ebkszI09NSQ05qdXz7oUFYb73j5Ahv735S7XmaGrMSVdSQ7VaAQvCKjKJLG3uzlU9yEXkHwRl7XryOnVUq+mwIBwn+xJf0AzSRDbCDlCdYDc+5H1du8nHKpBvSSNsPj3wbvcpXR+SJ2QbGUumkQ/kFqwYaz5Jdemkj9tDurtd0jruwuZdS4bBzjpfYONnZkOr01BYELSQvolPGk4+kT6kH+whBpFacjoad50s9/Ya2Hxdva/rx3hbi0wzYSt5SkaQOrctIyu9vYMc9LZOrVqDNBVWv6QK2pAJOhX+gL3tlqSo30+NsEXXRH2l4x1v65AVFie9Q3YkbykIyqJjiU3ZNs99N8hlt+sem8OgSBW0IQj/kxat1Ev1Eva2gnSy1OFK0hu8EPkUBG0TKQ5CqOZ60MPeDrpJDnhbGXbV28qCsPViVZAFodVfib9pJOxA1dv7k93WgOxhupDnsC0iqcimQdB1kvbwKdKNbHGbfuMgaD5tUd1H2kCukZ1kCSwQ4RNeA8ua8bD7SO1y1J9FXsAm19dEUqFSmjbCCl2w67zxALagBbA9rn+r58hg0t/bCsQo2Bt8TD7CtlHQflg2NJDV5BVZ7L7tyAq16oKkoJyAFeuFbiv1L/0CauSEJ1Lri1UAAAAASUVORK5CYII=>

[image91]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACYAAAAVCAYAAAAq05ytAAABqklEQVR4Xu2WzSsFURjGH/KRbEiyIsqCP0A+y8LGzoYNf4DyvZIUpQgbycfKhhRloexEIQvFAgtZKDZIbLAhSTzvvGfc6b25qztT6v7qtzjnmbnv25wzZy6QIkUKj3q6S1/pN32jh7SZptFteumyL3pCp707I2ITWrzMBqQdmg3ZIGzkyTzRUxs4VqGNVdkgbKqhhadsQDLoC32g6SYLnRFoY002II3QbN0GUSCbXYonsuv36ojIgxbes4HjAJpXBubq6A0tCMwlnVZo4TEbkFzoEXFv5ovoMM0y80llEX/vrxZotmSDKJDD84Pm2IDMQxvrMPOj9JyWQ5f1gi7TSTpLx911pdAt8g5dGRk/Qs/MhE+7Alp43waOM2iebwNoAWlMGKBXNNuNr6G/LcgelsaK3XgGCY4dObeO6Se0sOwh+SzJcspNW/TZZaJkE96dMe4Qa6yXrgUyWYWawHiD9tNC2h2YD4VbxBqTo0S+Dj7SmCyxj+zVI9oJbS5U5Cn7jfUhvrGGwDgTuvTyooXKIPSFmaO1dAfaTBvtgf5TWaEl/g1kAfEv0f/gB+djYp4UTYctAAAAAElFTkSuQmCC>

[image92]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAC0AAAAVCAYAAADSM2daAAACAElEQVR4Xu2WwUtUYRTFT2mEurE/oZ2tJQUVg1zYKje5qU0bLaVE1EUuAkNEo42obZJgQlEoMVqIUVEiKqiQG3EhuDTRTboJIkLPmfvpe16caDHjKMyBH3zzzvvgzHv3u/cBOeWU05lTJflM9sg++UVmyS1ygXwka8H7S5bI8+TOM6BJWLCr3qDuwrwn3sim9ER3yHdvBI3AQl/3RjZVDgvV5w0qn+ySLXLReVnVU1joGm9QN2DeuDeyLR08BfsXzUd3H1ceKSPXvJFJFcNCffVG0AzMTxWqlHwhCXc9o7oDC/XMG1QRrM1tesPpIU459Eukruc6mDfsDadGnHJoDY7fpMAb1CAs9D13/RJswLwjLeQNotBqny/IazJAOsP1CrIKu6+XDJFR2HDTPWqr/9VSS2ChvnkjaAXmX3HX28j72G8NnURYN5FXkYUJ2JuQWsk6uRx+b5COsL5NPoT1iVJfXiR/YKFUsxrlKhH1Ym3+GTwhrye50zQNC3AoPe1EWM+T+0cO0E6mwvoxGYt5esvVYV0L62IZk7pFfKTHQy+ThshCN6LOpLapMjiUQleFtULPxby0SyUQHzbx8ugi/WGt2tcb1f2S/lyq0PpAW4h5aZcGylvY2Neh04H8ATtQhbB6T8Ce3APbkhxAn2BB68kj2JelDvFNWNlsI6r/868DEIJ3pNYIwmMAAAAASUVORK5CYII=>

