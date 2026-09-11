---
id: "nemo-guardrails"
title: "NVIDIA NeMo Guardrails & Colang Safety Policies"
category: ["safety", "guardrails", "colang"]
tags: ["nemo", "guardrails", "colang2", "security", "hitl"]
source: "NVIDIA / nemoguardrails==0.24.0"
era: "Era 2 & Era 5"
status: "active"
verified: true
---

# NVIDIA NeMo Guardrails & Colang Safety Policies

## Architecture
NeMo Guardrails enforces programmatic, deterministic safety rails around LLM input, output, dialog flow, and loop execution:
- **Input Rails**: Intercepts destructive shell commands (`rm -rf /`, `mkfs`, fork bombs) and command-chaining privilege escalation vectors before execution.
- **Output Rails**: Scans generated model completions and redacts sensitive credentials (OpenAI/Gemini/GitHub API keys, AWS tokens, RSA private keys).
- **Dialog Rails**: Restricts role profiles (e.g. read-only `@reviewer` / `@architect` cannot execute file-mutating tools).
- **Loop Rails**: Enforces machine-checkable termination limits to prevent runaway agent loops.

## Colang 2.x Migration
Hermes uses Colang 2.x syntax in `.hermes/guardrails/`:
- Event-driven reactive `flow` definitions.
- Direct integration via `HermesGuardrailsEngine` and `capability_guard` plugin hook `pre_tool_call`.
