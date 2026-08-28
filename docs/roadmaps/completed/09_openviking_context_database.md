# 09. OpenViking: Hierarchical Virtual Filesystem Context Database

> **Research Source Reference**: `https://github.com/volcengine/OpenViking`  
> **Topic Category**: Virtual Filesystem Context & Tiered Information Retrieval  
> **Sequential Index**: `09 / 11`

---

## 1. What the Reference Means

`OpenViking` (by Volcengine / ByteDance) is an open-source context database designed specifically for AI agents that replaces flat vector stores with a **hierarchical virtual filesystem paradigm** (`viking://`).

---

## 2. Core Architectural Mechanisms

1. **VFS Navigation Paradigm**: Agents query and navigate context using natural POSIX tools (`ls`, `tree`, `find`, `grep`) over structured knowledge hierarchies.
2. **3-Tier Context Representation**:
   * **L0 (Abstract)**: $\approx 100\text{ token}$ ultra-compact summaries for instant routing.
   * **L1 (Overview)**: $\approx 2,000\text{ token}$ structural outline for high-level planning.
   * **L2 (Full Detail)**: Complete unabridged documents loaded only when an exact symbol/file is modified.
3. **Directory Recursive Retrieval**: Combines semantic vector embeddings with tree traversal to prune unneeded context subtrees before retrieving content.

---

## 3. Key Takeaways for Agent OS Design

* **Hierarchical Token Scaling**: Structure agent knowledge and memory in L0/L1/L2 layers to maximize context efficiency.
* **Tool Familiarity**: Expose context retrieval through standard filesystem abstractions that code-generation models already excel at using.
