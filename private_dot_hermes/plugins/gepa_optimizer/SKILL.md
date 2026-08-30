---
name: gepa-optimizer
description: Offline reflective Pareto prompt and skill optimization using execution feedback.
tags: [evolution, pareto, optimization]
---

# GEPA-Lite Prompt & Skill Optimizer

Implements Genetic-Pareto evolution with natural language self-reflection for prompt/skill optimization:

## Optimization Loop
1. **Candidate Pool**: Initialize diverse candidate prompt variants.
2. **Score Matrix**: Evaluate candidate accuracy on benchmark QA sets.
3. **Pareto Dominance**: Filter non-dominated frontier over $(\text{Score} \uparrow, \text{Tokens} \downarrow)$.
4. **Reflective Mutation**: Apply structured error feedback to mutate prompts without context bloat.
5. **Nightly Ingestion**: Ingest trajectory streams for offline refinement.
