"""
Hermes Plugin: embedding_gemma
==============================
On-Device Lightweight Semantic Retrieval with Strict CPU-Only Enforcement.
Guarantees 0 MiB GPU VRAM consumption to prevent contention with Gemma 4B on 6GB RTX GPU.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Invariant: Never allow CUDA/GPU offloading for embeddings
ALLOWED_DEVICES = {"cpu"}


class VRAMInvariantViolation(ValueError):
    """Raised when any code attempts to offload embedding models to GPU VRAM."""
    pass


_EMBEDDER_INSTANCE = None


def get_embedder(model_name: str = "BAAI/bge-small-en-v1.5", device: str = "cpu"):
    """
    Returns a cached embedding model instance strictly constrained to CPU.
    """
    global _EMBEDDER_INSTANCE
    dev = device.lower().strip()
    if dev not in ALLOWED_DEVICES:
        raise VRAMInvariantViolation(
            f"VRAM Invariant Violation: Attempted to load embedding model onto '{device}'. "
            f"EmbeddingGemma must strictly run on CPU to prevent VRAM thrashing with Gemma 4B on 6GB GPU."
        )

    if _EMBEDDER_INSTANCE is None:
        from fastembed import TextEmbedding
        _EMBEDDER_INSTANCE = TextEmbedding(model_name=model_name)

    return _EMBEDDER_INSTANCE


def embed_texts(texts: List[str], device: str = "cpu") -> List[List[float]]:
    """Generates normalized vector embeddings strictly on CPU."""
    embedder = get_embedder(device=device)
    embeddings = list(embedder.embed(texts))
    return [e.tolist() for e in embeddings]


def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    dot = np.dot(v1, v2)
    norm = np.linalg.norm(v1) * np.linalg.norm(v2)
    if norm <= 1e-12:
        return 0.0
    return float(dot / norm)


def semantic_search(
    query: str,
    corpus: List[str],
    top_k: int = 5,
    device: str = "cpu",
) -> List[Dict[str, Any]]:
    """Performs semantic similarity search over a text corpus on CPU."""
    if not corpus:
        return []

    embedder = get_embedder(device=device)
    query_vec = list(embedder.embed([query]))[0]
    corpus_vecs = list(embedder.embed(corpus))

    scored = []
    for idx, doc_vec in enumerate(corpus_vecs):
        sim = cosine_similarity(query_vec, doc_vec)
        scored.append({
            "index": idx,
            "text": corpus[idx],
            "score": round(sim, 4),
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


def register(ctx=None):
    """Registers embedding_gemma into Hermes runtime."""
    if not ctx:
        return True

    # 1. Native CLI command: hermes embed search <query> [--corpus <file>]
    if hasattr(ctx, "register_cli_command"):
        def setup_embed(parser):
            parser.description = "Semantic embedding and retrieval (strictly on CPU)"
            subparsers = parser.add_subparsers(dest="subcommand", help="Embedding actions")

            search_p = subparsers.add_parser("search", help="Perform semantic search over concept vault")
            search_p.add_argument("query", help="Query string")
            search_p.add_argument("--top-k", type=int, default=3, help="Number of results to return")
            search_p.add_argument("--json", action="store_true", help="Output results as JSON")

        def handle_embed(args):
            subcmd = getattr(args, "subcommand", None) or "search"
            if subcmd == "search":
                from hermes_constants import get_hermes_home
                concepts_dir = get_hermes_home() / "knowledge" / "concepts"
                files = list(concepts_dir.glob("*.md")) if concepts_dir.exists() else []
                if not files:
                    print("No concept documents found in vault.")
                    return 0

                corpus = [f.read_text(encoding="utf-8", errors="replace")[:1000] for f in files]
                results = semantic_search(args.query, corpus, top_k=args.top_k)

                if getattr(args, "json", False):
                    formatted = [
                        {"file": files[r["index"]].name, "score": r["score"], "snippet": r["text"][:160]}
                        for r in results
                    ]
                    print(json.dumps(formatted, indent=2))
                else:
                    print(f"Semantic Search for '{args.query}' (CPU Embeddings):")
                    for r in results:
                        fname = files[r["index"]].name
                        print(f"  [{r['score']:.3f}] {fname}")
                return 0
            return 0

        ctx.register_cli_command("embed", "Semantic search and CPU embeddings", setup_embed, handle_embed)

    # 2. Native Slash command: /embed <query>
    if hasattr(ctx, "register_command"):
        def slash_embed(raw_args: str) -> str:
            query = raw_args.strip()
            if not query:
                return "Usage: /embed <search_query>"
            from hermes_constants import get_hermes_home
            concepts_dir = get_hermes_home() / "knowledge" / "concepts"
            files = list(concepts_dir.glob("*.md")) if concepts_dir.exists() else []
            if not files:
                return "No concepts found in vault."
            corpus = [f.read_text(encoding="utf-8", errors="replace")[:1000] for f in files]
            results = semantic_search(query, corpus, top_k=3)
            lines = [f"**Semantic Search**: `{query}`"]
            for r in results:
                fname = files[r["index"]].name
                lines.append(f"- **{fname}** (score: `{r['score']:.3f}`)")
            return "\n".join(lines)

        ctx.register_command("embed", slash_embed, "Semantic search over knowledge vault", "<query>")

    # 3. LLM-callable tool
    if hasattr(ctx, "register_tool"):
        def search_knowledge_vault(query: str) -> str:
            """Performs CPU-based semantic search over knowledge concepts."""
            from hermes_constants import get_hermes_home
            concepts_dir = get_hermes_home() / "knowledge" / "concepts"
            files = list(concepts_dir.glob("*.md")) if concepts_dir.exists() else []
            if not files:
                return "Knowledge vault is empty."
            corpus = [f.read_text(encoding="utf-8", errors="replace")[:1000] for f in files]
            results = semantic_search(query, corpus, top_k=3)
            output = []
            for r in results:
                output.append(f"File: {files[r['index']].name} (Score: {r['score']})\nSnippet: {r['text'][:300]}")
            return "\n\n---\n\n".join(output)

        try:
            ctx.register_tool(
                name="search_knowledge_vault",
                toolset="knowledge",
                schema={
                    "name": "search_knowledge_vault",
                    "description": "Semantically searches the local COG Second Brain knowledge vault on CPU.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"}
                        },
                        "required": ["query"],
                    }
                },
                handler=search_knowledge_vault,
            )
        except Exception:
            pass

    return True


__all__ = [
    "get_embedder",
    "embed_texts",
    "semantic_search",
    "VRAMInvariantViolation",
    "register",
]
