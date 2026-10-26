# Phase 08: Autonomous Headless & Konsole TUI Execution — Specification Manifest

> **Phase ID**: `phase_08_autonomous_headless_konsole_tui_execution`  
> **Canonical Enterprise Tool / Framework**: `Systemd User Units \+ Konsole Wayland (--tui \--yolo / \-q)1`  
> **ICM Architectural Layer**: `**60% Infra** (TMPDIR="/tmp", sub-48-byte AF\_UNIX sockets)3`  
> **Hardware Boundary Assertion**: `![][image52] Wayland on dGPU (Iris Xe offload)4`  

---

## 1. Master Matrix Realignment Summary
| Field | Specification |
| :--- | :--- |
| **Capability Title** | Autonomous Headless & Konsole TUI Execution |
| **Enterprise Toolkit** | Systemd User Units \+ Konsole Wayland (--tui \--yolo / \-q)1 |
| **ICM Layer / Stage** | **60% Infra** (TMPDIR="/tmp", sub-48-byte AF\_UNIX sockets)3 |
| **Primary Verification Gate** | `hermes doctor1` |
| **Hardware Assertion** | ![][image52] Wayland on dGPU (Iris Xe offload)4 |

---

## 2. Exhaustive Phase Specification
Phase 08 standardizes Fedora 44 KDE Wayland Konsole (systemd-run \--user) for interactive \--tui \--yolo monitoring and headless batch execution (hermes chat \--yolo \-q "\$PROMPT") with agent.max\_turns: 500 and TMPDIR="/tmp"1. Within the **60% Infrastructure Layer**, setting TMPDIR="/tmp" keeps AF\_UNIX IPC socket paths under 48 bytes, preventing the 108-byte POSIX UNIX\_PATH\_MAX truncation failure in nested directories3. KDE Wayland renders on the integrated Intel Iris Xe GPU (Disp.A: Off), consuming only a static 6 MiB on the discrete RTX 3050 GPU1. The exact verification contract (![][image73]) is:

---

## 3. Operational Invariants for Active Stage
1. **Sub-8K Context Discipline**: Read ONLY this file during Stage `01_spec`. Do not load other phases.
2. **Turn 1 Reconnaissance**: Emit `<deliberation><global>...</global></deliberation>`, call `jev_compile_intent` and `extract_workspace_ast`.
3. **Task Formulation**: Populate `02_impl/task.md` with target files and symbols before advancing to Stage `02_impl`.


<!-- Embedded Formula References -->
[image52]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAASCAYAAAAdZl26AAACsElEQVR4Xu1WS8hOURRd3gy8oryVZCIi/ZIyuJ4lAyMpDBko8vgHGMg/IY9IoRRFZCADhTJQXuVRRKIw8AiJlELMxFrf3ud+557v3vv3lYn6V606Z+19zr3rnn33vUAPevBPMZu8QF4nr/q8Ch3kn4STChlFLEZrvjCYfEre8blwGa25Md+Tm/JsxwryEznH51vJD2SfPKMcy8g3sI13JLEYx8mHsLyJkT6O/EZ+JXtHusYhf1Sk9yc3uH46iGPI7+T2IBD3YEkTIq0MGXkUdgNPiqEcA8mz5DXYniOLYcwiFySacBvl+YKqJJwi9vlkbB4GlpK7onkVMvIgeQq2h24mhU53FaoNVKHOwElEBl6SX5qxtpDBDMiwNtxfiBrOwWq9yoDKdEaiCXUG9M40DAzzwTPYU7oFKx/Vc7+QXYMMZkA38Rn2gvWK4sPJMz4uM6D3Tlr+NCOUGRhAnnB9o4TJPtFGx8i+5FDyAawsukMGMyDoXdBecT2vJZf7uMzAEPK86ymCgRuwteJH8he5Bf6gpnnSb3JEY5lBbUr6zEgrQ4amgfmwNarPgEtonmSZAeGA6ynKTkA3vY78QV6RoBdXSa+jJGG163sSPUVGHvKxNlcJqSMNIsejaKbKQGgiKcoMBHTC16ivanC/EAZWuq6yqkOGpgEhPE11nm3kkihWZWC36ynqDExHtOYR+bgZa2AN2j8BQV9vrVPnUa+OP4RVBnSNdg2E0m9AHUcfsrjrbIYlLIy0MmQoGhCew160w4leZWCv6ynqDOijm69RvaqNdsHqWK1VXeiIz+uwHlZ+UyOtC7b53EgTbro+OtF1Henpb4v2lR7/SgiLyJ/ku1icAjv2Fx5o+VlK0AHbPOZOj+l43/pYuIjW3HDDd6P5K3Ieuv+Z0+nq36rsZP4v/AUyT9PLWkZqVQAAAABJRU5ErkJggg==>

[image73]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEEAAAAVCAYAAAAZ6IOkAAACnElEQVR4Xu2XW4hOURTH/24R5VJueZA7eZOS5OFLLgmRwhNNCY1mXB/cGbkToUSiBiGXEnKJRimUS7yIIk+SZ4+88P+31nb2bIOvmTMvp/OvX9/ea+2zzz7rrL3O/oBSpUqVKvWHOpDb5Bv56bwnE+NB1Fn3ic9kUXN3MTQX9oBnUoerI3lD5qSOImkcLAj3UoernuxKjUVTT2RbIdVA8oh0Th1F1FfyHVYnYp0noxNbYfUMlg0DIttssi7qF16XYEGY4P1ebkszI09NSQ05qdXz7oUFYb73j5Ahv735S7XmaGrMSVdSQ7VaAQvCKjKJLG3uzlU9yEXkHwRl7XryOnVUq+mwIBwn+xJf0AzSRDbCDlCdYDc+5H1du8nHKpBvSSNsPj3wbvcpXR+SJ2QbGUumkQ/kFqwYaz5Jdemkj9tDurtd0jruwuZdS4bBzjpfYONnZkOr01BYELSQvolPGk4+kT6kH+whBpFacjoad50s9/Ya2Hxdva/rx3hbi0wzYSt5SkaQOrctIyu9vYMc9LZOrVqDNBVWv6QK2pAJOhX+gL3tlqSo30+NsEXXRH2l4x1v65AVFie9Q3YkbykIyqJjiU3ZNs99N8hlt+sem8OgSBW0IQj/kxat1Ev1Eva2gnSy1OFK0hu8EPkUBG0TKQ5CqOZ60MPeDrpJDnhbGXbV28qCsPViVZAFodVfib9pJOxA1dv7k93WgOxhupDnsC0iqcimQdB1kvbwKdKNbHGbfuMgaD5tUd1H2kCukZ1kCSwQ4RNeA8ua8bD7SO1y1J9FXsAm19dEUqFSmjbCCl2w67zxALagBbA9rn+r58hg0t/bCsQo2Bt8TD7CtlHQflg2NJDV5BVZ7L7tyAq16oKkoJyAFeuFbiv1L/0CauSEJ1Lri1UAAAAASUVORK5CYII=>

