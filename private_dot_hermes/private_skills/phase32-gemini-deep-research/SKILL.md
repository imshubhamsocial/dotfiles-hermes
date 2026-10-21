---
name: gemini-deep-research
description: Gemini-style autonomous deep research
---

# Gemini-Style Autonomous Deep Research

## When to Use
Use when tasked with multi-hop technical, academic, or market research requiring web traversal, source triangulation, and long-form report synthesis.

## Quick Reference
* Search & Extract: `mcp_openjev(jev_web_research_ground)`, `web_search`, `web_extract`
* Hypothesis DAG: `mcp_openjev(jev_taskdag_plan)`
* Contradiction Gate: `mcp_openjev(jev_decide)` + `mcp_openjev(jev_latent_deliberate)`
* Memory Target: `viking://research/L0/index` (Port 1933)

## Procedure
1. Invoke `jev_compile_intent` on Turn 1 to sanitize input and set `<global>` attention regime.
2. Decompose the research topic into 4-8 orthogonal sub-questions via `jev_taskdag_plan`.
3. For each node, run `jev_web_research_ground` and `web_search` to gather primary sources, extracting full text and tables via `web_extract`.
4. Cross-examine conflicting claims via `jev_decide` and `jev_latent_deliberate` (6 Banach loops on CPU).
5. Synthesize a publication-grade report with Markdown tables, LaTeX equations, and verified citations, then persist L0/L1/L2 summaries to OpenViking Port 1933.

## Pitfalls
* Never cite unverified snippets without extracting full context on primary claims.
* Never run GPU-based web scrapers; keep all extraction and MRL clustering 100% on CPU RAM (`CUDA_VISIBLE_DEVICES=""`).
