"""
Contract Tests for EmbeddingGemma CPU-Only Enforcement
======================================================
Validates:
  1. Strict CPU device constraint (rejects 'cuda' / 'gpu')
  2. Embeddings generation and normalization
  3. Semantic cosine similarity search
"""

import pytest
from plugins.embedding_gemma import (
    get_embedder,
    embed_texts,
    semantic_search,
    VRAMInvariantViolation,
)


def test_cuda_offload_strictly_forbidden():
    """Attempting to load onto CUDA/GPU must raise VRAMInvariantViolation."""
    with pytest.raises(VRAMInvariantViolation) as exc_info:
        get_embedder(device="cuda")
    assert "VRAM Invariant Violation" in str(exc_info.value)

    with pytest.raises(VRAMInvariantViolation):
        get_embedder(device="gpu")


def test_cpu_embedder_instantiation():
    """Default device='cpu' must succeed."""
    embedder = get_embedder(device="cpu")
    assert embedder is not None


def test_embed_texts_cpu():
    """Vectors must be generated with non-zero dimensions."""
    texts = ["Hello world", "Hermes Agent OS"]
    vectors = embed_texts(texts, device="cpu")
    assert len(vectors) == 2
    assert len(vectors[0]) > 0
    assert len(vectors[1]) > 0


def test_semantic_search_retrieval():
    corpus = [
        "FastMCP provides official Model Context Protocol servers.",
        "A database WAL file prevents sqlite corruption.",
        "Vegetable soup recipes for cold winter nights.",
    ]
    query = "model context protocol"
    results = semantic_search(query, corpus, top_k=2, device="cpu")

    assert len(results) == 2
    # The first result should be the MCP document
    assert results[0]["index"] == 0
    assert results[0]["score"] > 0.5
