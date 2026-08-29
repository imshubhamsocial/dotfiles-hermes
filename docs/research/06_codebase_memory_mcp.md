# 06. Codebase Memory MCP: High-Performance Structural Graph

> **Research Source Reference**: `https://github.com/DeusData/codebase-memory-mcp`  
> **Topic Category**: Model Context Protocol & Tree-Sitter Codebase Graph  
> **Sequential Index**: `06 / 11`

---

## 1. What the Reference Means

`codebase-memory-mcp` is a native, single-binary Model Context Protocol (MCP) server that indexes codebases into a persistent structural knowledge graph (call chains, class hierarchies, HTTP endpoints, cross-service links) using Tree-sitter.

---

## 2. Core Architectural Mechanisms

1. **99% Token Reduction**: Instead of dumping entire files into the prompt, the agent queries the MCP server for exact structural relationships (e.g. `who_calls_function`, `find_subclasses`, `get_api_route`).
2. **Blazing Fast Local Indexing**: Single static binary with zero external runtime dependencies; indexes entire repositories in milliseconds.
3. **Multi-Language Tree-Sitter Support**: Native support across 150+ languages for exact AST parsing without LLM hallucinations.

---

## 3. Key Takeaways for Agent OS Design

* **Structural Graph Navigation over Raw Text Dumps**: Equip Hermes with Tree-sitter structural query tools to resolve symbol dependencies in sub-millisecond time.
* **Standardized MCP Interface**: Serve repository knowledge via standard Model Context Protocol endpoints for seamless inter-agent tool use.
