# Phase 27: Two-Stage Zero-Eviction Decision Router — Specification Manifest

> **Phase ID**: `phase_27_two_stage_zero_eviction_decision_router`  
> **Canonical Enterprise Tool / Framework**: `jev\_decide \+ \_GemmaCPUSidecarPool (EmbeddingGemma 2 \+ T5Gemma 2\)1`  
> **ICM Architectural Layer**: `**Layer 3** Stage 0/1/2 Routing Gate1`  
> **Hardware Boundary Assertion**: `0.0 MiB CUDA; ![][image69] Slot 0 KV cache preserved1`  

---

## 1. Master Matrix Realignment Summary
| Field | Specification |
| :--- | :--- |
| **Capability Title** | Two-Stage Zero-Eviction Decision Router |
| **Enterprise Toolkit** | jev\_decide \+ \_GemmaCPUSidecarPool (EmbeddingGemma 2 \+ T5Gemma 2\)1 |
| **ICM Layer / Stage** | **Layer 3** Stage 0/1/2 Routing Gate1 |
| **Primary Verification Gate** | `pytest tests/phase27\_decision\_router\_eval/ \-q1` |
| **Hardware Assertion** | 0.0 MiB CUDA; ![][image69] Slot 0 KV cache preserved1 |

---

## 2. Exhaustive Phase Specification
Phase 27 deploys jev\_decide in .hermes/mcp\_openjev.py powered by \_GemmaCPUSidecarPool (EmbeddingGemma 2 256d MRL margin scoring ![][image32] \+ T5Gemma 2 seq2seq tie-breaker)1. Operating as the **Layer 3 Zero-Eviction Router**, it bypasses LLM calls on read-only 01\_spec/ recon at Stage 0 (gate\_bypassed: True, 0 LLM calls) and resolves high-uncertainty 02\_impl/ mutations on CPU RAM (0.0 MiB CUDA delta) while preserving 100% of Port 8138 Slot 0 KV cache (cache\_preserved: True; 7/7 tests pass in 0.88s)1. The exact verification contract (![][image73]) is:

---

## 3. Operational Invariants for Active Stage
1. **Sub-8K Context Discipline**: Read ONLY this file during Stage `01_spec`. Do not load other phases.
2. **Turn 1 Reconnaissance**: Emit `<deliberation><global>...</global></deliberation>`, call `jev_compile_intent` and `extract_workspace_ast`.
3. **Task Formulation**: Populate `02_impl/task.md` with target files and symbols before advancing to Stage `02_impl`.


<!-- Embedded Formula References -->
[image32]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFsAAAAVCAYAAAApZJKFAAAEGElEQVR4Xu2Ya6ilYxTHl+u4kzu5HDK5ZNK4U4wQ8cUtt0ZixEzDB0MuhWZcCrlF7pdcwmRCQ2415GDGNJhIQ7kmkkgURUj8f9azz1nv8p69373PGfnw/ur/4fk/z3n33utdz3rWc8xaWlpaWmrYUnpAelVaJp1dne7KAdLT0mvSsHRwZdbZWLpHek5aIN0sbVJZMQAvSedn83/OptL70uwy3lb6RJrXWdCF/aWvpX3L+HDpV+nQkRVmq0ovSIcF7yJpubR68PriSOkv6Ttp7TQ3UZBF10rb54lxcJN5sCOzpO+lNZKfeVu6LXmPSc+GMS8gjmE16XPpiOQ3YhVpqflDCfgV1ekJZQfpVukuabc0NwhfSE8kj8zkdxyU/Mhk8zXnJX+u9JONZu1Z0sfS+iMrnHel45LXCB54p3nGsY1+Nt+OK5MtpOulx626bfuBWk3AqKeRvYp/efIjJ5uvOS35c4o/rYwpH4zfk7Yr3n7SNzZABVhT+lTapoxvN3/4vSMrVi4bShdLz5gHgBrZlL3NvyvfOTKl+A8mP3KB+Ro+M3Ju8WeUMRn+QfEosZxpZPWBZb4v2EY3hPFW0i/Sb9JOwa9jurRIell6RRqqzPbHJOkc6XnpTGt2+JB9dcGmPOE/mvwIWV8XbOo9/szg7Wh+LuAjGonNwnwj1pJWmJ/okRutd2acLi0xr/fAF6AOjxeCTHv1lbRumstw4NYFe9fiP5z8yCVWH2yCjE9p7XCSebmjC+kEnOzeIKzpCVviqmyaB59D4g8bO7s5TN80Dw4Bv0PavbKiP3gOL5At+4Z5d9SLnc1/OJ8d4Xvg35L8CL04a05JPi0k/vFlzHlCQrLzgHLLbmZNrAhdIavpR6mZddCi8cBH8kThaht9y3Qy+aBpCmcGW/cj80wkW5tCUvD5XGgi+xS/W1d1gvmaM5J/YfEPKeNh+/fdg8C/Jb2e/DFhS1yWzQA/5Efz7KZNyhAkDhH6XF4a64bigh7Qq5Jd75h/j82r042hLXsqeUeZB+zo5EeGzNfkQJJkdGQblTFdR91zOF8ooz1Zx3xr5N4xM8/8C8Xax9X1Q/NeuUOn1eq0Rt3gMznxXzR/WZ3tOSjXmO+KztkBJBJBipcaeu5Twxi4ot+XPMrjk2E8bP4CMldK12WzDtoerqnUnm5abB7EP83rI0yVfpdOLGO4VLo7jMdimvn/F7gMxOCMB8ohGXZsGdP7ku2xrPFZ3B34LXsGnwvWZ9LWZUwX84ON/lagrNHyzTU/sNmRx5iXkPXCulo4iL600XrbVPfzxwXaJjJgoXnt5iIwUcEbBHYbL/wh8/tB3c2OQ/db87WRXcyzdL55N7VHdfofOHDZ3VzvSUJ2Di+5paXlP4eanc+FscS/Ndut2tKMvwFN8OmnFtbISQAAAABJRU5ErkJggg==>

[image69]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACoAAAASCAYAAAAt6kybAAAC1UlEQVR4Xu2WSaiPURjGH2RWxkzhnyRDKGNkTLphYSiuul0sDImilLIwFQslQ4YMJYQMmVNk3CA2yM5UimJh5SalxPPc95z/936n72NnIU/9uuc85/y/857pPRf4r39HPchBso8MTtq8NpCBqSk1IX1T02khuUEekfOkkm9uVHdylNwnT8iyfDPakVdkGulHPpB1wZeakankArkUvKp6kjnkNrmctEWtJM9J11DfRD65utSFvID1lXqT12RL7EAtJc9cfTPZTo6Q07DJnYVNoJfrh9Wwj+8n31EcaDfyjcx3XlPyHrYaUTth3/JaQT6T5qF+GLYgUbOQ/4a0CtlkC/UVxYEuIT/JsMS/Q266+jtyztUlbaN+OzHUtSD6XdRsstbV+5MHsGNYqrJA9XENpq300hlqIK1gZ1N9tGJeI4OviyEtJ0+z5sZjMT2UFdw9MrTaWqKyQOVpMAXjpbMkX5diVChrUl4aVP6xUO9A3pAJsPP9EHaBJJ3fraH8W5UFegvFgerwyx9EJodyGqjSj/xTzhsO+6YmWgleZ1jQ2p0/qizQ6ygOVIPL17kaF8ppoJqE/BOJn+oAmeLquoRXyTznVaVAr6QmdRI2mBK115ngazUGhLIG9BoS/N2J7zUGlp6itpFDpBOyI5NTWaB7YIOlj4H6yleqUg5VWcnea3TwNyZ+lNKWMkfHUG8Pu6DaIalP+JuTAtVyp1oMG2xE4iuN6FxF6cW56OrSDNhvZyZ+1HqywNUnwfrryJRKgV5LTdhsv5BFzmsBS+RrnKcte4l8DlQy/4gs4Xtph9Jnciws0NL/AVrCXp+7KE62emL1xsdUojdcT6G/pSprhdVXag1b5fpqj7wUZJqb25AfZHyoV2KDXo7HsCA1E/EW9szFfxSiasgO2OXaCzvsqeRpO4/DLsjcXGumWtjzXaRdsDG0YOmZ/6tqC7sLcXdS6ZgozWnB6n4B0P+dxOqyRRcAAAAASUVORK5CYII=>

[image73]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEEAAAAVCAYAAAAZ6IOkAAACnElEQVR4Xu2XW4hOURTH/24R5VJueZA7eZOS5OFLLgmRwhNNCY1mXB/cGbkToUSiBiGXEnKJRimUS7yIIk+SZ4+88P+31nb2bIOvmTMvp/OvX9/ea+2zzz7rrL3O/oBSpUqVKvWHOpDb5Bv56bwnE+NB1Fn3ic9kUXN3MTQX9oBnUoerI3lD5qSOImkcLAj3UoernuxKjUVTT2RbIdVA8oh0Th1F1FfyHVYnYp0noxNbYfUMlg0DIttssi7qF16XYEGY4P1ebkszI09NSQ05qdXz7oUFYb73j5Ahv735S7XmaGrMSVdSQ7VaAQvCKjKJLG3uzlU9yEXkHwRl7XryOnVUq+mwIBwn+xJf0AzSRDbCDlCdYDc+5H1du8nHKpBvSSNsPj3wbvcpXR+SJ2QbGUumkQ/kFqwYaz5Jdemkj9tDurtd0jruwuZdS4bBzjpfYONnZkOr01BYELSQvolPGk4+kT6kH+whBpFacjoad50s9/Ya2Hxdva/rx3hbi0wzYSt5SkaQOrctIyu9vYMc9LZOrVqDNBVWv6QK2pAJOhX+gL3tlqSo30+NsEXXRH2l4x1v65AVFie9Q3YkbykIyqJjiU3ZNs99N8hlt+sem8OgSBW0IQj/kxat1Ev1Eva2gnSy1OFK0hu8EPkUBG0TKQ5CqOZ60MPeDrpJDnhbGXbV28qCsPViVZAFodVfib9pJOxA1dv7k93WgOxhupDnsC0iqcimQdB1kvbwKdKNbHGbfuMgaD5tUd1H2kCukZ1kCSwQ4RNeA8ua8bD7SO1y1J9FXsAm19dEUqFSmjbCCl2w67zxALagBbA9rn+r58hg0t/bCsQo2Bt8TD7CtlHQflg2NJDV5BVZ7L7tyAq16oKkoJyAFeuFbiv1L/0CauSEJ1Lri1UAAAAASUVORK5CYII=>

