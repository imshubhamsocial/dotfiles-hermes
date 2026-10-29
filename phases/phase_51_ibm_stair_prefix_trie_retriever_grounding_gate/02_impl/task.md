# Phase 51 Implementation Plan: IBM STAIR Prefix-Trie Retriever & Pre-Execution Grounding Gate

## Target Symbols
- `STAIRLeafNode` (dataclass in `scripts/hermes_stair_retriever.py`)
- `STAIRPrefixTrie` (class in `scripts/hermes_stair_retriever.py`)
- `HermesSTAIRVerifier` (class in `scripts/hermes_stair_retriever.py`)
- `verify_tool_call_grounding()` (method and integration point in `.hermes/mcp_ephemeral_bridge.py`)

## Causal Hypotheses
1. Constructing a prefix-trie over valid leaf node IDs ($LN_{\mathcal{D}}$) eliminates hallucinated document paths and phantom markdown anchors by construction (0.00% invalid section citations).
2. Two-stage Matryoshka Representation Learning (256d coarse -> 768d fine) executed on CPU cores 6–11 preserves GPU VRAM at 0.0 MiB while sustaining high retrieval precision (SearchTome Recall@1 baseline ~82.6%).
3. Intercepting state-mutating tool calls to enforce entity existence in prior read outputs prevents phantom updates and premature mutations on benchmarks like Tau-bench.

## Implementation Steps
1. Create `scripts/hermes_stair_retriever.py` with `STAIRLeafNode`, `STAIRPrefixTrie`, and `HermesSTAIRVerifier`.
2. Ensure integration with `EmbeddingGemmaCPUClient` (Port 8139 / fallback) using canonical prompt prefixes.
3. Update `.hermes/mcp_ephemeral_bridge.py` to instantiate `HermesSTAIRVerifier` and invoke `verify_tool_call_grounding()` on tool calls.
4. Deploy updated bridge to `~/.hermes/mcp_ephemeral_bridge.py`.
5. Run pre-commit linter gate (`ruff check`).
6. Advance to stage `03_verify` and execute verification contract.
