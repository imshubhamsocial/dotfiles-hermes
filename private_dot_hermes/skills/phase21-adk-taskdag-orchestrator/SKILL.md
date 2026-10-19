---
name: adk-taskdag-orchestrator
description: "ADK 2.9 TaskDAG A2A subagent router"
---

# ADK 2.9 TaskDAG & A2A Subagent Router

## Purpose
Decomposes complex, multi-faceted engineering goals into a Directed Acyclic Graph (DAG) executed by sandboxed persona subagents communicating via typed Agent2Agent (A2A) JSON-RPC 2.0 events.

## When to Hydrate
Hydrate this skill when:
- A goal involves multiple distinct engineering phases: architectural specification, code refactoring, compiler verification, and trajectory evaluation.
- Operating under high-risk refactorings where strict persona sandboxing prevents accidental diff thrashing or premature test assertions.

## Execution Protocol

1. **DAG Graph Topology**:
   - Model the task as $\mathcal{G}_{\text{task}} = (\mathcal{V}, \mathcal{E})$.
   - Verify topological ordering using cycle detection:
     - Root nodes: `@architect` (AST symbol analysis, contract creation).
     - Middle nodes: `@coder` (Surgical patches, Karpathy U12 $\le 3\times$ line bound).
     - Verification nodes: `@tester` (Compiler and pytest validation).
     - Terminal node: `@critic` (Harness² trajectory scoring).

2. **Persona Sandboxing**:
   - Enforce strict tool permissions per persona.
   - Prohibit `@architect` from mutating code or `@coder` from running verification commands.

3. **Zero Context Pollution**:
   - Strip all raw terminal telemetry floods and stack trace logs.
   - Transmit only compact, typed JSON-RPC 2.0 payloads via `transfer_to_agent`.
   - Maintain `context_pollution_tokens == 0`.
