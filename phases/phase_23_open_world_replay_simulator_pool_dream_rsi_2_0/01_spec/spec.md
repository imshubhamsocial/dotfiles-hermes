# Phase 23: Open-World Replay Simulator Pool (Dream-RSI 2.0) — Specification Manifest

> **Phase ID**: `phase_23_open_world_replay_simulator_pool_dream_rsi_2_0`  
> **Canonical Enterprise Tool / Framework**: `ReplaySimulatorPool \+ Content-Addressed SHA-256 Disk Trees1`  
> **ICM Architectural Layer**: `**Layer 2** Offline Counterfactual Evaluation (0.054 ms)1`  
> **Hardware Boundary Assertion**: `0.0 MiB CUDA; ![][image64] LLM call reduction1`  

---

## 1. Master Matrix Realignment Summary
| Field | Specification |
| :--- | :--- |
| **Capability Title** | Open-World Replay Simulator Pool (Dream-RSI 2.0) |
| **Enterprise Toolkit** | ReplaySimulatorPool \+ Content-Addressed SHA-256 Disk Trees1 |
| **ICM Layer / Stage** | **Layer 2** Offline Counterfactual Evaluation (0.054 ms)1 |
| **Primary Verification Gate** | `pytest tests/phase23\_dream\_rsi2\_eval/ \-q1` |
| **Hardware Assertion** | 0.0 MiB CUDA; ![][image64] LLM call reduction1 |

---

## 2. Exhaustive Phase Specification
Phase 23 implements Google DeepMind / UMD Dream-RSI 2.0 (arXiv:2609.14858) and Google RRSI (arXiv:2609.24972) in ReplaySimulatorPool1. Serving as the **Layer 2 Position-Addressed Simulation Store**, it evaluates candidate skill and prompt mutations offline using Doubly Robust (DR) value estimation across 100+ cached SHA-256 disk replay trees in .hermes/cache/dream\_worlds/ on CPU RAM (0.0 MiB CUDA delta), achieving 0.054 ms evaluation latency and 26.0x LLM call reduction (8/8 tests pass in 0.02s)1. The exact verification contract (![][image73]) is:

---

## 3. Operational Invariants for Active Stage
1. **Sub-8K Context Discipline**: Read ONLY this file during Stage `01_spec`. Do not load other phases.
2. **Turn 1 Reconnaissance**: Emit `<deliberation><global>...</global></deliberation>`, call `jev_compile_intent` and `extract_workspace_ast`.
3. **Task Formulation**: Populate `02_impl/task.md` with target files and symbols before advancing to Stage `02_impl`.


<!-- Embedded Formula References -->
[image64]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAC4AAAASCAYAAAAkAezhAAACxklEQVR4Xu2WWahOURiGX/NMKSJzuUAkU9zInBRRXJDioFCGJEmUC24kJCGKHENRuOCSMuVCMkWRKSVCZCyixPv+31r/v/Z39j7O4Uqdt57+1rvWXuvba3/rWz/QoAbVW2PIdfIl/C7KdpfVgqwlF8h5spU0yYzIV1OyCfbcTbKNtMqM+AsNI4/IWNKdnCC/yJpkjNQOtvARWLCdyWOyNB1UoOPkGOwFWpKzsLn+Sdq5yUlbu/qMfCWdEl+7+y70S1NhL7i/PCJf02Hj9KJRA4I3MvHqpcaw9NDOdUj8fbCJY8p0JN/I3vIIoA3ZTQYmXp4OkzfO087/JOudX2dpgrewIPsm/o7grQjt+aG9sjyi7rpLHniT+kDOOW8iLCWLNIT0jI3BZHylryRNqEAnhPb20F5MzpAr5BQZHvpr00dY8F6vyVPnjYLN38z50mhyGdnMyKgP+U6ukkbBOwQL/CHpH7x55DP+nCp6Li/wl+SFN6kZsPXi2lIXco10TbwaUtV4DqswUaoKCkApFKWJlWYnEy9POuR5gStoFYE8LYedJ62hAqEKNCgzwmkOeY+au6hJFPhC598nP0hb56fSJtzzJvUKVtOLtApWsS7CcrtQqufagRG+g9oMC3ya87WT8mv7hLdgVcvrE6wUF0lzamP0RVX9ctWDPIEdgKhxsHyTZsICnFXpLknVQr5KY5EOwCpIqtaw57Y4P0o5fYMMJUtINbI5X5JuMl3zSpNUG1DZYS2kxddVuksT6UJKb0Bd46tJt8SbBAuyV+Lp4pGnwLx0Ud1G9usuI3vggq+GBaXPdgm2iwpIE/crjwIWwFJJX0eqgh2w9NDof4yeO514kv6bpAf7KPJvXF10Cnqu74BdVrtioz1soSKax4FBenPV3juwF+2d6QWmwG7Ejc5XjuqT66ZV6ugF8/J2J5ntzUQHYZfU/6nfhAGZIDEwuckAAAAASUVORK5CYII=>

[image73]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEEAAAAVCAYAAAAZ6IOkAAACnElEQVR4Xu2XW4hOURTH/24R5VJueZA7eZOS5OFLLgmRwhNNCY1mXB/cGbkToUSiBiGXEnKJRimUS7yIIk+SZ4+88P+31nb2bIOvmTMvp/OvX9/ea+2zzz7rrL3O/oBSpUqVKvWHOpDb5Bv56bwnE+NB1Fn3ic9kUXN3MTQX9oBnUoerI3lD5qSOImkcLAj3UoernuxKjUVTT2RbIdVA8oh0Th1F1FfyHVYnYp0noxNbYfUMlg0DIttssi7qF16XYEGY4P1ebkszI09NSQ05qdXz7oUFYb73j5Ahv735S7XmaGrMSVdSQ7VaAQvCKjKJLG3uzlU9yEXkHwRl7XryOnVUq+mwIBwn+xJf0AzSRDbCDlCdYDc+5H1du8nHKpBvSSNsPj3wbvcpXR+SJ2QbGUumkQ/kFqwYaz5Jdemkj9tDurtd0jruwuZdS4bBzjpfYONnZkOr01BYELSQvolPGk4+kT6kH+whBpFacjoad50s9/Ya2Hxdva/rx3hbi0wzYSt5SkaQOrctIyu9vYMc9LZOrVqDNBVWv6QK2pAJOhX+gL3tlqSo30+NsEXXRH2l4x1v65AVFie9Q3YkbykIyqJjiU3ZNs99N8hlt+sem8OgSBW0IQj/kxat1Ev1Eva2gnSy1OFK0hu8EPkUBG0TKQ5CqOZ60MPeDrpJDnhbGXbV28qCsPViVZAFodVfib9pJOxA1dv7k93WgOxhupDnsC0iqcimQdB1kvbwKdKNbHGbfuMgaD5tUd1H2kCukZ1kCSwQ4RNeA8ua8bD7SO1y1J9FXsAm19dEUqFSmjbCCl2w67zxALagBbA9rn+r58hg0t/bCsQo2Bt8TD7CtlHQflg2NJDV5BVZ7L7tyAq16oKkoJyAFeuFbiv1L/0CauSEJ1Lri1UAAAAASUVORK5CYII=>

