# 03. Active Milestone Prompt: U50 (Codebase Memory Tree-Sitter MCP Structural Knowledge Graph)

> **Current Execution Target**: Milestone 4 Phase 1 — Specification `U50`  
> **Authoritative Roadmap**: `docs/roadmaps/active/roadmap4_frontier_cognitive_os.md`  
> **Research Archive**: `docs/roadmaps/active/archive/06_codebase_memory_mcp.md` & `10_schema_org_structured_data.md`  
> **Hardware Context**: `docs/prompts/01_environment_and_hardware.md`  
> **Coding & Invariant Rules**: `docs/prompts/02_rules_conventions_and_standards.md`

---

## 1. Milestone Objective (`U50`)

Implement the **Codebase Memory Tree-Sitter MCP Structural Knowledge Graph Subsystem** (`src/hermes_core/codebase_memory_mcp.py`):

1. **Tree-Sitter Structural Symbol Graph & Call-Graph Extraction (`src/hermes_core/codebase_memory_mcp.py`)**:
   * Parse Python, JavaScript/TypeScript, and C/C++ AST syntax via native Tree-sitter bindings.
   * Extract high-precision symbol signatures, class hierarchies, function definitions, and caller-callee relationship edges.
   * Replaces crude whole-file dumping with targeted, sub-millisecond AST symbol queries (`get_symbol`, `get_callers`, `get_callees`, `get_class_hierarchy`).

2. **MCP JSON-RPC Server & Tool Schema Interface**:
   * Expose the structural graph over standard Model Context Protocol (MCP) tool endpoints:
     * `mcp_query_symbol(symbol_name: str)`: Returns exact definition line range and docstring.
     * `mcp_query_call_graph(function_name: str, depth: int = 1)`: Returns upstream and downstream call graph edges.
     * `mcp_query_dependencies(file_path: str)`: Returns AST import dependency graph.
   * Format responses into concise AST slices consuming $<150\text{ tokens}$ per query.

3. **Strict Hardware Envelope Bounds**:
   * Pure CPU / RAMDisk execution ($0\text{ MB GPU VRAM}$).
   * Incremental AST indexing with cache invalidation on file modification.

---

## 2. Implementation Deliverables

* `src/hermes_core/codebase_memory_mcp.py`: Tree-sitter structural symbol graph indexer and MCP tool provider.
* Integration into the tool registry for Slot 4 / agent tool invocation.

---

## 3. Dedicated Contract Test Suite

Author `tests/harness_contracts/test_roadmap4_u50_codebase_memory_mcp.py` asserting:
1. `test_tree_sitter_symbol_extraction()`: Validates parsing and extraction of functions, classes, and methods across languages.
2. `test_call_graph_caller_callee_relationship()`: Validates deterministic caller-callee edge construction.
3. `test_mcp_symbol_query_endpoint()`: Validates JSON-RPC MCP query returning accurate symbol definition and line range.
4. `test_ast_symbol_token_budget()`: Validates that symbol query output stays within $<150\text{ tokens}$.
5. `test_codebase_memory_mcp_zero_gpu_vram()`: Validates $0\text{ MB GPU VRAM}$ overhead.

---

## 4. Execution & Verification Directives

1. Execute and verify inside `ws-hermes`:
   ```bash
   distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/test_roadmap4_u50_codebase_memory_mcp.py -v
   distrobox enter ws-hermes -- python3.13 -m pytest tests/harness_contracts/ -q
   ```
2. Ensure **100% pass rate** across all 481 existing tests + new U50 tests.
3. Stage and commit changes cleanly in Chezmoi:
   ```bash
   distrobox enter ws-hermes -- bash -c "chezmoi add src/hermes_core/codebase_memory_mcp.py tests/harness_contracts/test_roadmap4_u50_codebase_memory_mcp.py docs/prompts/03_active_milestone_prompt.md && chezmoi git -- add -A && chezmoi git -- commit -m 'feat(roadmap4): implement U50 codebase memory tree-sitter MCP structural knowledge graph'"
   ```
