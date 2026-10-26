# Phase 04: Two-Tier Progressive Skill Catalog — Specification Manifest

> **Phase ID**: `phase_04_two_tier_progressive_skill_catalog`  
> **Canonical Enterprise Tool / Framework**: `Upstream Hermes Skills Hub \+ YAML Frontmatter Validator1`  
> **ICM Architectural Layer**: `**Layer 3** Deferred Tool/Skill Loading (.hermes/skills/\*/SKILL.md)2`  
> **Hardware Boundary Assertion**: `0.0 MiB CUDA (lazy-loaded Markdown)1`  

---

## 1. Master Matrix Realignment Summary
| Field | Specification |
| :--- | :--- |
| **Capability Title** | Two-Tier Progressive Skill Catalog |
| **Enterprise Toolkit** | Upstream Hermes Skills Hub \+ YAML Frontmatter Validator1 |
| **ICM Layer / Stage** | **Layer 3** Deferred Tool/Skill Loading (.hermes/skills/\*/SKILL.md)2 |
| **Primary Verification Gate** | `python3 \-m pytest tests/phase20\_continuous\_rsi\_eval/ \-k skill \-q1` |
| **Hardware Assertion** | 0.0 MiB CUDA (lazy-loaded Markdown)1 |

---

## 2. Exhaustive Phase Specification
Phase 04 utilizes the upstream Hermes Skills Engine (skill\_view, skill\_manage) with strict YAML frontmatter validation (description \<= 40 chars, total frontmatter ![][image23] bytes) across 34+ skills stored in .hermes/skills/\<skill-name\>/SKILL.md1. This realizes Van Clief’s **Layer 3 Dynamic Skills & Deferred Tool Loading** principle by keeping static skill bodies out of the root prompt; only L0 skill identifiers appear in the index while full procedural playbooks hydrate into the active stage folder on demand1. Because skills are lazy-loaded Markdown files, they incur 0.0 MiB CUDA delta and save ![][image76] static prompt tokens per turn in Port 8138 KV cache1. The exact verification contract (![][image73]) is:

---

## 3. Operational Invariants for Active Stage
1. **Sub-8K Context Discipline**: Read ONLY this file during Stage `01_spec`. Do not load other phases.
2. **Turn 1 Reconnaissance**: Emit `<deliberation><global>...</global></deliberation>`, call `jev_compile_intent` and `extract_workspace_ast`.
3. **Task Formulation**: Populate `02_impl/task.md` with target files and symbols before advancing to Stage `02_impl`.


<!-- Embedded Formula References -->
[image23]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADUAAAAVCAYAAADmSqZGAAACqUlEQVR4Xu2WS6hOURTHl/fjlvLII3SH3uWZDHTzjgk3U2HikZm3hD4yUF4DFCJEZCCSDC4RZUAoDIR05ZFHCpNbV4n//661z7fOdjiH+zG4fb/61V1r73u+vc/ea+8jUqVKm6QLPAg/wFfwFByU6qH0h0fhdXgbLkk3t9ARboPX4D24C3ZL9fhPnIH7YD9YD7/ARtjD9ekDH8IVFg+Gz2ApdDD4LL4UTq4rvCg6wYowDO4XffDvmAJvwHYux4F/hztdbrfopDzL4UfYyeK5ov/XN+khMtxyE13uj6kT3UolOCDdlMl6+BWudDluPQ6EqxV4Ac+6mEwV7TfZ4hPwfbm5Ba7YN7gxyufSGS6Ax+Bii4uySnRg/N9AT8uxxghrifGhpIcyzvKbLOZKPi43J3yCDXHyV/SGW0SLd3rUVhRunUWSrh+uNgcbamG8xdzOnlGWDy/ks/y8Rck7+DxOxvBNLhXdZnxwpeFzOdhZFodJxpMK9cKDgfDvrEm9ga/jpGeaaA0sjBsqxFDRGtjscpMke1I8jJhnLZEmyZ4UJ9QYJz28U1bDl/AqnJlubhXd4QNJ1xcZIjr4A1F+pOX3WswxPSo3J7wVvbNyYS1wtW6aPJpbA4/006L12SFq4x3FwbPNM8HyYVXvi95dMbz3rsTJPEaL/uB5OCZqK0oJXoDtXS6sAHkKz7mYzBad1ByLj4iedB6uPvvsiPKFGSg6EP54+KEizId3YI3L8VrgpRzYDp9I+pJeK7q1wuU7Q3QCtUkPvXSZG+tyfwWP5zXwkuR/d40Q3R7c89wid0VroxmedP34ZXILzrOYz+Xq8X708Ftvj4v5jPh+++fwU4hvMsutrh/pBTfA4/Cw6HdiDLfvMtGTkttxneWqtAnqRPd+ES9L/ld6lUrzA92gmMy9En19AAAAAElFTkSuQmCC>

[image73]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEEAAAAVCAYAAAAZ6IOkAAACnElEQVR4Xu2XW4hOURTH/24R5VJueZA7eZOS5OFLLgmRwhNNCY1mXB/cGbkToUSiBiGXEnKJRimUS7yIIk+SZ4+88P+31nb2bIOvmTMvp/OvX9/ea+2zzz7rrL3O/oBSpUqVKvWHOpDb5Bv56bwnE+NB1Fn3ic9kUXN3MTQX9oBnUoerI3lD5qSOImkcLAj3UoernuxKjUVTT2RbIdVA8oh0Th1F1FfyHVYnYp0noxNbYfUMlg0DIttssi7qF16XYEGY4P1ebkszI09NSQ05qdXz7oUFYb73j5Ahv735S7XmaGrMSVdSQ7VaAQvCKjKJLG3uzlU9yEXkHwRl7XryOnVUq+mwIBwn+xJf0AzSRDbCDlCdYDc+5H1du8nHKpBvSSNsPj3wbvcpXR+SJ2QbGUumkQ/kFqwYaz5Jdemkj9tDurtd0jruwuZdS4bBzjpfYONnZkOr01BYELSQvolPGk4+kT6kH+whBpFacjoad50s9/Ya2Hxdva/rx3hbi0wzYSt5SkaQOrctIyu9vYMc9LZOrVqDNBVWv6QK2pAJOhX+gL3tlqSo30+NsEXXRH2l4x1v65AVFie9Q3YkbykIyqJjiU3ZNs99N8hlt+sem8OgSBW0IQj/kxat1Ev1Eva2gnSy1OFK0hu8EPkUBG0TKQ5CqOZ60MPeDrpJDnhbGXbV28qCsPViVZAFodVfib9pJOxA1dv7k93WgOxhupDnsC0iqcimQdB1kvbwKdKNbHGbfuMgaD5tUd1H2kCukZ1kCSwQ4RNeA8ua8bD7SO1y1J9FXsAm19dEUqFSmjbCCl2w67zxALagBbA9rn+r58hg0t/bCsQo2Bt8TD7CtlHQflg2NJDV5BVZ7L7tyAq16oKkoJyAFeuFbiv1L/0CauSEJ1Lri1UAAAAASUVORK5CYII=>

[image76]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFIAAAAVCAYAAADVcblPAAADeklEQVR4Xu2XaahNURTH/+ZZhhISj5IhQ2SMeMZCKD6QJBkyJrNCpoiQDy8lEU/IPGT6QBlSUoYMH3xAZMiYqVBKrP9b+9y7z37nnrvvva/76f7q3z1rrX3WOXedc/ZeGyhQoECBrGkpquI6Dd1Ex0QXRMdFC5B6bBx9RadFN0TXRQNCUaWqaIPoquieaLuoVmiE4pMrb1SHFmmd6LOoRyiqNIPebBtjVxKdE5UkRvjRR/RW1MvYQ0W/RYMTI5QjokPQgtaEXotFtfHNlTdeiy6Jroj+IbqQfDuWOb62oj+iuo4/jjsoX/zD0EIFjIXeRxPL19H4els+n1wpGSW6KRroBiqA5UhdyAOio46vMXQ8f31g4Tl+vuNfK/oBffsIr/UhGS6Dsb+ilcb2zRVLsega9IJFoUhuxBVyPTR2AvqpkSWis4kR6ZkAzTHZ8S8y/uDleCR6kgwn+Cq6bI59c3kxSXRbtA3+b0UccYXkG/ATGn8IHXtL1NQelIbF0PNZBJt5xj/N2N+gxXR5L3pujn1zZUR/0T7oytbCiWVCXCEJJ/Hv0DEUr+f1CRlWI/rPzzb+WcbmcVQhubC8Mce+ubKCK+8p0UFRFyfmQ7pCboV+4pxSgmLuD42IZwWi/zz/NP3Tjf0L0YVkEV+YY99cOdEO2ludQXI+8yEoZE83IKwSlVp2P9Ez6PjRlj+OmdDxEx3/XOMfZ+xXosfJcIJ30J6S+ObKmoaiLaKPok3Qfs+XVIVkTq6E3R1/a+PndXwYD80/1fFz0aK/2Nj3RU8T0SScVtiiEd9cGcOun33eA+hr3ygc9iIoZNDgBnQy/jqOn3Aa4YPzoQiaZ6Hj3wxtpBsYey90hbapDT03uFaRsdPl8qaaaA50JeVKFrWN8iUopN30knrQmxvh+Al3GyMte7ios2W7cHe0x/GxgT5p2cOg99HK8vGe6LO/Cp9caakhmiG6C52/6ofDWbEGerND3AD0YbH9mCKqDN3NLIW+kQEdoOdzHB9wFJwO2MI0NzZ3LF+g87oNO4Idls3r7LZs4psrJeyR2LCyy6+IApaKXkKLQHHbx6fNiduGiwobcPau51F+xeSW7hP0fE4HqWgPXf25n94l6hoOl8GHxRV4J/RT59dCn4tPrkgGQbdBGc8BeaQE2sAXyJGLrqNA5oyBzrUFcmQjMts25p3/JLDfrXnjhPAAAAAASUVORK5CYII=>

