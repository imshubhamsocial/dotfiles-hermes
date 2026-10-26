# Phase 14: Declarative Attention & LoopCD Scoping — Specification Manifest

> **Phase ID**: `phase_14_declarative_attention_loopcd_scoping`  
> **Canonical Enterprise Tool / Framework**: `Apple LoopCD Logprob Margin \+ \[SWA\_ANCHOR\] Tail Injection1`  
> **ICM Architectural Layer**: `**Layer 2** Sub-8K Context Discipline (\<global\>/\<focus\>/\<local\>)1`  
> **Hardware Boundary Assertion**: `Slot 0 KV cache hit rate ![][image56] (![][image57] delta)1`  

---

## 1. Master Matrix Realignment Summary
| Field | Specification |
| :--- | :--- |
| **Capability Title** | Declarative Attention & LoopCD Scoping |
| **Enterprise Toolkit** | Apple LoopCD Logprob Margin \+ \[SWA\_ANCHOR\] Tail Injection1 |
| **ICM Layer / Stage** | **Layer 2** Sub-8K Context Discipline (\<global\>/\<focus\>/\<local\>)1 |
| **Primary Verification Gate** | `pytest tests/phase14\_da\_loopcd\_eval/ \-q1` |
| **Hardware Assertion** | Slot 0 KV cache hit rate ![][image56] (![][image57] delta)1 |

---

## 2. Exhaustive Phase Specification
Phase 14 implements Apple LoopCD (arXiv:2610.02185) logprob entropy gating alongside LATENT-01 \[SWA\_ANCHOR \| FOCUS: \<symbol\> \| SANDBOX: \<dir\> \| V\_CONTRACT: pytest \<dir\> \-q\] tail injection1. Within **Layer 2 Position-Addressed Attention Anchoring**, appending a 1-line SWA anchor to the tail of every FastMCP tool response keeps the active symbol and verification contract inside the 4,096-token SWA window (85.71% token reduction, \+65.0% Pass@1 gain, and 92.5% KV slot cache hit rate on Port 8138 with 0.0 MiB CUDA expansion; 4/4 tests pass in 0.76s)1. The exact verification contract (![][image73]) is:

---

## 3. Operational Invariants for Active Stage
1. **Sub-8K Context Discipline**: Read ONLY this file during Stage `01_spec`. Do not load other phases.
2. **Turn 1 Reconnaissance**: Emit `<deliberation><global>...</global></deliberation>`, call `jev_compile_intent` and `extract_workspace_ast`.
3. **Task Formulation**: Populate `02_impl/task.md` with target files and symbols before advancing to Stage `02_impl`.


<!-- Embedded Formula References -->
[image56]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAC8AAAASCAYAAADLw4ffAAADH0lEQVR4Xu2WWahOURiGX/M8ZcpQJ2WeIoq4ECUhUy5cUCc35kzJlLk4IlxIuTGPkTlkiEwpU+YLhEwXXFEUJd7Xt9Z/vr3ax+HOhaee/n99e+39r73Wt771A//5j6hCF9I9dFByzTOcjvGBLvQ6vUNf0rH+YqAa3Uzf09d0N22Z6VE2i5HtW0QPuLbQoBfRhvQc3YHsPV3pavqM1onBjvQDHRba3elbOjB2COyjG2lTOop+pC9oXd8ph0r0R+J3OtX1aRvijUN7AD1MS+h2epWeog9ROk5UoI/omxgI6KbHrt2fXoL1j0yB/eBaF8ujMv1M79N3sBlP02Ic7FmRevSEa4sesNUo0Bp20zUfJBNDXKsi5tFvdFahhy2p+mj2f0dF+iQNJiiH9Sz1FbXpkdLLqEpvw1a9QDfYTZd9kIwPcc2ImB3a2wo9gAYhpj1QHuUNvj3sWY1CW2mzqvQyVtIJrv2LVrCbriTxmSE+J7RVCYqRze9+sD4XXKwsnsJy/CRssx+jTTI9gEN0ASzNTtM2Id6Jnkc2ZQso57WDPcpLDWxdEveo8qhPmr95fKJDw/casMqmF/HUp3vpGdjMR/QiHVw7Q2/Y0sdB9IHtAQ1sReyUoGVWxVAJ/BM6J+24p8p7ce0F/xt6qaOwFSrQjh6E1VfV2kmwh+szpSa9h2z+/y1DYM/flF5wqJafhZ0vYjBsxZRuqnRlopNOD9eG9ijvtLRbYPX7T9DBonNDlS0S90t6UHl0pvR17YuwqpdBubgTNqMRrcJd144sgy1bLGlig/uehza0BurzeESIrXExTy9kV0UTpVKtdMugY14Pim+pA+IrnVboYYymN2gtF1P91eEV0WZUWW3hYuvpDNcWyln9plYgRdVG6ataH9FkfUFOGmspNMvVYaVwK92PbGlSudLfAR0UevAt+gr2krtcv7mwQansRZrB7mke2qrlz2Grncd8OjINwsp5ZqMK1XAdAsq/m3Q6smkh9BdAg8pzueunTaUqtMTFRE96HJZCevGlyN8zRbCJy0Mv9ABWUouTa/8EWkWfcimTYWdSyU+AuK15RakQ+AAAAABJRU5ErkJggg==>

[image57]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAASCAYAAAAdZl26AAACoElEQVR4Xu2WS6gPYRjGX+S2oEhRLmUlIsWxUGQIhQUWNrKkEEkSp6izQC65FMo1x21hIYWdcqSIssFCSE6US0lJbHmeed/vP++8/5lhYaPOr5765vne+f7zzHeZv0gfffwzxkDnoR7oMbSu3N1GB/QraGKposwiaa8nw6Dn0AO7JrekvdbrPbSlVQ1GQc+gjXY9HnoNdaWCBpZBb0UH7gx9nlPQE9G6Cc4fC32DvkL9nc92qh/t/EHQJvO7k3lYNIBnPfQFGhj8SAadEH2Ap+WuFkOgy9Ad0R/mC/PMgBYEj9yX6npyV4pZlF7oWqtL4YAsmBv8SCb6Ai6I1vNhIqug1VIfoI6mAOfEAnDts3G61C0y0/xdwY9kogGWiNYfLPUqV0XXel2AAdD04JGmANwzeYC0GbkMPNPM55ttIhMNwIf4LLrB+rn+EdAla1cF+GRe/jCBqgCDobPmb6Yxzy5igCnmXwl+JBMNQDgG7/HreS203NpVAYaLLt+mAD2i91IfoJ/QVrEXNduKYoDJ5l8MfiSTIsB80Xu4PhM3pTgIqgKQQ+ZHqmaAD80j/jt0m8YkKzrpishU848GP5JBR6zNwbmEeCINhcZJOUxdgAPmR6oCJLaJ3cNONvgR88wyf3fwI5kUAUh6mzx5dkCLXV9dgL3mR5oCpD2a8wq6XvTlpFNlafAjmZQDpOA8eXhWc3Mn6gLsMz/SFCCtkJw90Espnx7boY/ydx8yH4C8EN1ox4JfF2C/+ZGmADvF3cMvJc/VFXbN9ctZWZMKGtgAPRI9tRJdooPzgPDcM5/fHs9x8/1sEY5L3/+VIAuhH9A7b44UTdUNnYFW+s4KOkQH90r7hdPba21yQ9pr0wM/dNdvoDny5z9znF3+t6qamf+L36O80SVtOAvNAAAAAElFTkSuQmCC>

[image73]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEEAAAAVCAYAAAAZ6IOkAAACnElEQVR4Xu2XW4hOURTH/24R5VJueZA7eZOS5OFLLgmRwhNNCY1mXB/cGbkToUSiBiGXEnKJRimUS7yIIk+SZ4+88P+31nb2bIOvmTMvp/OvX9/ea+2zzz7rrL3O/oBSpUqVKvWHOpDb5Bv56bwnE+NB1Fn3ic9kUXN3MTQX9oBnUoerI3lD5qSOImkcLAj3UoernuxKjUVTT2RbIdVA8oh0Th1F1FfyHVYnYp0noxNbYfUMlg0DIttssi7qF16XYEGY4P1ebkszI09NSQ05qdXz7oUFYb73j5Ahv735S7XmaGrMSVdSQ7VaAQvCKjKJLG3uzlU9yEXkHwRl7XryOnVUq+mwIBwn+xJf0AzSRDbCDlCdYDc+5H1du8nHKpBvSSNsPj3wbvcpXR+SJ2QbGUumkQ/kFqwYaz5Jdemkj9tDurtd0jruwuZdS4bBzjpfYONnZkOr01BYELSQvolPGk4+kT6kH+whBpFacjoad50s9/Ya2Hxdva/rx3hbi0wzYSt5SkaQOrctIyu9vYMc9LZOrVqDNBVWv6QK2pAJOhX+gL3tlqSo30+NsEXXRH2l4x1v65AVFie9Q3YkbykIyqJjiU3ZNs99N8hlt+sem8OgSBW0IQj/kxat1Ev1Eva2gnSy1OFK0hu8EPkUBG0TKQ5CqOZ60MPeDrpJDnhbGXbV28qCsPViVZAFodVfib9pJOxA1dv7k93WgOxhupDnsC0iqcimQdB1kvbwKdKNbHGbfuMgaD5tUd1H2kCukZ1kCSwQ4RNeA8ua8bD7SO1y1J9FXsAm19dEUqFSmjbCCl2w67zxALagBbA9rn+r58hg0t/bCsQo2Bt8TD7CtlHQflg2NJDV5BVZ7L7tyAq16oKkoJyAFeuFbiv1L/0CauSEJ1Lri1UAAAAASUVORK5CYII=>

