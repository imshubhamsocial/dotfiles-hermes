---
id: "adk-orchestrator"
title: "Google Agent Development Kit (ADK 2.8.0) Computational Graphs"
category: ["orchestration", "multi-agent", "graph", "adk"]
tags: ["google-adk", "sequential-agent", "parallel-agent", "loop-agent", "dag"]
source: "Google ADK 2.8.0 / Google Cloud"
era: "Era 1 & Era 4"
status: "active"
verified: true
---

# Google Agent Development Kit (ADK 2.8.0) Computational Graphs

## Computational Graph Topologies
Google ADK 2.8.0 models multi-agent workflows not as loose conversational chat rooms, but as deterministic computational graphs:
- **`SequentialAgent`**: Chains sub-agents in a strict pipeline where output from step $N$ feeds into step $N+1$.
- **`ParallelAgent`**: Fans out tasks to independent sub-agents concurrently, aggregating results via quorum arbitration.
- **`LoopAgent`**: Iteratively refines output until a deterministic stopping condition or test arbiter passes.
- **`RouterAgent`**: Evaluates incoming task specifications against routing policies to dispatch to the optimal domain agent.

## Hermes Integration
In Hermes Agent OS, `adk_orchestrator` exposes TaskDAG composition:
- Bridges high-level engineering plans into structured ADK sub-agent workflows.
- Eliminates ad-hoc conversational agent swarms in favor of verifiable execution graphs.
