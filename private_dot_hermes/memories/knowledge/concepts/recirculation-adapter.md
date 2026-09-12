---
id: "recirculation-adapter"
title: "Google DeepMind Recirculation: Dynamical System-2 Prefill Loops"
category: ["reasoning", "system-2", "prefill"]
tags: ["deepmind", "recirculation", "lyapunov", "test-time-compute"]
source: "Google DeepMind Recirculation Paper (2025/2026)"
era: "Era 1 & Era 4"
status: "active"
verified: true
---

# Google DeepMind Recirculation: Dynamical System-2 Prefill Loops

## Concept
Rather than emitting tokens immediately upon receiving a complex task specification, Recirculation runs an internal prefill dynamical loop:
- The specification is recirculated through the attention layers across multiple virtual reasoning cycles.
- A Lyapunov energy convergence proxy evaluates whether the internal hidden state has stabilized before tool tokens are generated.
- In small language models (Gemma 4B), recirculation provides +20% to +35% reasoning lift by allocating test-time compute to task decomposition before mutation.

## Hermes Implementation
Wired into `recirculation_adapter` plugin:
- Hooks into `pre_tool_call` and prompt preparation.
- Manages 5-slot context formatting (System Prompt, System Tools, Standards & Two-Tier Plans, Dynamic Skills, Conversational History).
- Prevents context degradation and stabilizes multi-step agent plans.
