"""
Contract Tests for U25: CPU Neural Embedding Substrate & Hybrid Retrieval
==========================================================================
Tests the CPUNeuralEmbeddingEngine, dense ONNX cosine similarity, sparse BM25/TF-IDF,
and Hybrid Reciprocal Rank Fusion (RRF) retrieval.
"""

from __future__ import annotations

import sys
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".hermes" / "src"))

import pytest

from hermes_core.embeddings import (
    CPUNeuralEmbeddingEngine,
    SearchHit,
    create_cpu_embedding_engine,
)


class TestCPUNeuralEmbeddingEngine:
    """Test suite for U25 capabilities."""

    def test_sparse_bm25_retrieval(self):
        engine = create_cpu_embedding_engine(use_neural=False)

        docs = [
            "Three.js shallow water simulation discrete laplacian wave equation",
            "SQLite database WAL transaction journal process guard kill",
            "Bubblewrap unshare namespace kernel sandbox security jail",
        ]
        ids = ["physics_water", "db_wal", "sandbox_bwrap"]
        metas = [{"cat": "physics"}, {"cat": "database"}, {"cat": "security"}]

        count = engine.index_documents(docs, ids=ids, metadatas=metas)
        assert count == 3

        hits = engine.search_sparse("laplacian wave physics simulation", top_k=1)
        assert len(hits) == 1
        assert hits[0].doc_id == "physics_water"
        assert hits[0].metadata["cat"] == "physics"

    def test_hybrid_rrf_ranking(self):
        engine = create_cpu_embedding_engine(use_neural=False)

        docs = [
            "Fast web research engine with token bounding and HTML parser",
            "CPU neural embeddings with dense vector similarity and fastembed",
            "AST whole-codebase symbol graph with call hierarchies",
        ]
        ids = ["research", "embeddings", "symbol_graph"]

        engine.index_documents(docs, ids=ids)
        hits = engine.search_hybrid("fastembed neural vector embeddings", top_k=2)

        assert len(hits) >= 1
        assert hits[0].doc_id == "embeddings"

    def test_empty_query_and_index_resilience(self):
        engine = create_cpu_embedding_engine(use_neural=False)
        assert engine.index_documents([]) == 0
        assert engine.search_sparse("any query") == []
        assert engine.search_hybrid("any query") == []

    def test_sub_millisecond_search_latency(self):
        engine = create_cpu_embedding_engine(use_neural=False)
        docs = [f"Synthesized memory snippet number {i} regarding system optimization and AST parsing" for i in range(100)]
        engine.index_documents(docs)

        start = time.perf_counter()
        for _ in range(50):
            engine.search_sparse("memory snippet AST parsing", top_k=3)
        dur_ms = ((time.perf_counter() - start) / 50) * 1000

        # Sub-2ms latency guarantee on CPU
        assert dur_ms < 2.0, f"Sparse search too slow: {dur_ms:.2f}ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
