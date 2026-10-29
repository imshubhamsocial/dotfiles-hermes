# Phase 51 Specification: IBM STAIR Prefix-Trie Retriever & Pre-Execution Tool Grounding Gate

## 1. Intent & Architectural Rationale
In accordance with *STAIR: STructure Aware Information Retriever* (arXiv:2609.03874, revised Oct 2026) and Jake Van Clief's Interpretable Context Methodology (arXiv:2603.16021), standard length-based text chunking severs hierarchical semantic boundaries. 
By structuring the workspace context into Jake Van Clief's 5-Layer ICM hierarchy, Hermes Agent OS possesses an explicit Table of Contents $\mathcal{T}_{\mathcal{D}}$ by construction.
The retrievable atomic units are defined as the Leaf Nodes Set $LN_{\mathcal{D}}$:
$$LN_{\mathcal{D}} = \{ u \in \mathcal{V}_{\mathcal{D}} \mid \text{children}(u) = \emptyset \}$$

## 2. Technical Requirements & Deliverables

### 2.1 STAIR Prefix TokenTrie (`STAIRPrefixTrie`)
- Trie data structure over all valid canonical leaf IDs (`file_path#heading_slug`).
- Hard prefix constraint preventing fabrication of phantom sections or non-existent files.
- Exact slug resolution and `allowed_next_chars(prefix)` grammar constraints.

### 2.2 Hermes STAIR Verifier (`HermesSTAIRVerifier`)
- **Indexing Engine**: Crawls `docs/`, `skills/`, `phases/`, `memories/`, `rules/`, and `_config/` markdown files, parsing `#`, `##`, `###` headings into `STAIRLeafNode` records with canonical breadcrumbs.
- **Two-Stage MRL Retrieval**:
  - Coarse retrieval: 256d Matryoshka vector cosine similarity over top candidate leaves ($k=12$).
  - Fine retrieval: 768d Matryoshka vector cosine re-ranking over coarse candidates to return top-$k$ ($k=3$).
  - Uses `EmbeddingGemmaCPUClient` on Port 8139 (or deterministic offline fallback) to maintain 0.0 MiB GPU VRAM consumption.

### 2.3 Epistemic Pre-Execution Tool Grounding Gate
- Sits in `mcp_ephemeral_bridge.py` (Port 1934) before tool dispatch.
- **Epistemic ID Gate**: Evaluates arguments matching entity ID patterns (`id`, `order`, `user`, `payment`, `item`). Verifies they exist in prior read-tool outputs before state mutation, stopping ungrounded entity fabrication.
- **Semantic Grounding Gate**: Uses `task: fact checking | query: ...` against retrieved leaf embeddings.

### 2.4 Hardware & Security Invariants
- `query_live_nvml_vram()` MUST verify `used_mib <= 5400.0`.
- All background embedding operations run on CPU cores 6–11 with zero GPU memory allocation.
