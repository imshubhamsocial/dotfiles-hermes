# Phase 42 Specification: Sub-8K Context Compaction & Fast-Path Deliberation

* **ICM Layer**: Orchestration (30% Allocation Tier)  
* **Context Budget**: <= 4,096 tokens active per conversational turn (Sub-8K Discipline)  
* **Input State**: 200,000+ cumulative prompt tokens and 4–6 minute dialogue latency in GDR24 multi-turn logs.  
* **Process**:  
  1. Strip `<deliberation>...</deliberation>` blocks from historical assistant turns via `compact_messages` in `mcp_ephemeral_bridge.py`.  
  2. Cap single tool result payloads at 2,048 characters and assistant conversational generation at `max_tokens: 512` (<= 120 deliberation tokens).  
  3. Enforce `cache_prompt: true` with byte-identical system prefix for >= 92% KV-cache prefix reuse on Port 8138.  
* **Output Metric**: Turn latency <= 10.0s and active prompt token count <= 4,096.
