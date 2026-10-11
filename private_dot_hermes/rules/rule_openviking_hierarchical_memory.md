# OpenViking Hierarchical Memory Provider Invariant

**Scope:** Core System Architecture (Phase 5 Invariant)
**Location:** OpenViking Daemon (Port 1933)

OpenViking is the mandated long-term memory provider for the Hermes Agent OS. It provides a durable, indexed knowledge graph that adheres to strict resource constraints.

### 1. Architectural Constraints
*   **Memory Backend:** Zero VRAM overhead. All embeddings and knowledge retrieval are executed using CPU-based methods.
*   **Daemon Lifecycle:** The OpenViking daemon runs persistently on `http://127.0.0.1:1933`. Its lifecycle management must be robust and external to the core application logic.
*   **Data Structure:** Knowledge is stored hierarchically, indexed by type (e.g., `viking://user/default/memories/entities/X/Y.md`) to ensure context isolation and efficient retrieval.

### 2. Retrieval Process
1.  **Input:** Semantic queries are processed by the OpenViking daemon.
2.  **Retrieval:** The system performs tiered context browsing, prioritizing specific node URIs (`viking://user/default/memories/`) over general search to minimize hallucination and ensure data provenance.
3.  **Output:** Retrieved information is a set of verifiable, cited memory snippets, not a generalized text summary.

### 3. Operational Rule
*   The primary interface for interacting with the memory must be the dedicated `viking_*` tools (`viking_search`, `viking_read`, `viking_browse`). Direct file system access to memory files is discouraged unless explicitly for maintenance.