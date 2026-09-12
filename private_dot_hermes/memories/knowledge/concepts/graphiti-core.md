---
id: "graphiti-core"
title: "Graphiti Core: Bi-Temporal Knowledge Graph & Episodic Memory"
category: ["memory", "graph", "temporal"]
tags: ["graphiti", "knowledge-graph", "temporal-memory", "wal"]
source: "Zep AI / Graphiti OSS"
era: "Era 1 & Era 5"
status: "active"
verified: true
---

# Graphiti Core: Bi-Temporal Knowledge Graph

## Architecture
Graphiti replaces static flat vector stores and fragile naive key-value memory with an asynchronous, bi-temporal knowledge graph:
- **Bi-temporal Dimensions**: Tracks both *event time* (when an event occurred in the external world) and *ingestion time* (when the agent learned about the fact).
- **Entity Resolution**: Automatically consolidates duplicate entities across conversation turns and tool outputs.
- **Episodic Edge Evolution**: Invalidates obsolete relationships without deleting history, preventing hallucination during multi-session workflows.

## Hermes Integration
In Hermes Agent OS, Graphiti is wired into `reflective_learner_adapter`:
1. At session end (`on_session_end`), session summaries and verified code modifications are ingested into local Graphiti.
2. Ingested entities are queried via `mcp_tools` or semantic search to provide grounded temporal context across developer sessions.
