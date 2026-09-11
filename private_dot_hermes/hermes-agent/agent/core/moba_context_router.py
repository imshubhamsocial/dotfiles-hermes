"""
Hermes MoBA (Mixture of Block Attention) Context Router (Phase II.1)
====================================================================
Inspired by Moonshot AI's MoBA architecture (arXiv:2502.13189):
- Applies Mixture-of-Experts principles to long-context attention at the application layer.
- Splits large contexts (up to 500K+ tokens) into cohesive blocks of size B (default 512 tokens).
- Dynamic Sparse Routing:
  1. Sink Block (Block 0): Pinned for primacy bias and system directives.
  2. Recent Block (Last Block): Pinned for recency bias and current turn intent.
  3. Top-K Routed Blocks: Selected via BM25 + term-frequency relevance scoring.
  4. Chronological Reassembly: Preserves topological causality and sequence coherence.
- Bounded Compute: O(N^2) quadratic explosion reduced to fixed O(K * B) footprint.
- Persistent SQLite cache for sub-millisecond block lookups.
"""

from __future__ import annotations

import math
import os
import re
import sqlite3
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25Okapi = None
    BM25_AVAILABLE = False


def estimate_tokens(text: str) -> int:
    """Estimates tokens using standard ~4 chars/token heuristic."""
    if not text:
        return 0
    return max(1, len(text) // 4)


@dataclass
class ContextBlock:
    block_index: int
    doc_id: str
    text: str
    token_count: int
    is_sink: bool = False
    is_recent: bool = False
    score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MoBARouteResult:
    doc_id: str
    total_tokens: int
    total_blocks: int
    routed_blocks: List[ContextBlock]
    routed_tokens: int
    routed_text: str
    compression_ratio: float
    duration_ms: float
    strategy: str = "moba_sparse_routing"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["routed_blocks"] = [b.to_dict() if isinstance(b, ContextBlock) else b for b in self.routed_blocks]
        return d


class MoBAContextRouter:
    """
    Application-layer Mixture of Block Attention (MoBA) Router.
    Enables Hermes to process massive contexts (500K+ tokens) within a fixed
    4,096-token KV attention budget.
    """

    DEFAULT_BLOCK_SIZE = 512  # Tokens per block
    DEFAULT_TOP_K = 8         # 8 blocks * 512 = 4,096 tokens active window

    def __init__(
        self,
        db_path: Optional[Path] = None,
        block_size: int = DEFAULT_BLOCK_SIZE,
        top_k: int = DEFAULT_TOP_K,
    ):
        self.block_size = block_size
        self.top_k = top_k

        if db_path is None:
            shm = Path("/dev/shm")
            if shm.exists() and shm.is_dir():
                self.db_path = shm / "hermes_moba_blocks.db"
            else:
                cache_dir = Path.home() / ".hermes/cache"
                cache_dir.mkdir(parents=True, exist_ok=True)
                self.db_path = cache_dir / "moba_blocks.db"
        else:
            self.db_path = Path(db_path)

        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS moba_blocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id TEXT NOT NULL,
                block_index INTEGER NOT NULL,
                text TEXT NOT NULL,
                token_count INTEGER NOT NULL,
                is_sink INTEGER NOT NULL DEFAULT 0,
                is_recent INTEGER NOT NULL DEFAULT 0,
                UNIQUE(doc_id, block_index)
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_moba_doc ON moba_blocks(doc_id)")
        conn.commit()
        conn.close()

    def _chunk_text_to_token_size(self, text: str, max_tokens: int) -> List[str]:
        words = text.split()
        chunks = []
        cur = []
        cur_tok = 0
        for w in words:
            w_tok = max(1, len(w) // 4)
            if cur_tok + w_tok > max_tokens and cur:
                chunks.append(" ".join(cur))
                cur = [w]
                cur_tok = w_tok
            else:
                cur.append(w)
                cur_tok += w_tok
        if cur:
            chunks.append(" ".join(cur))
        return chunks

    def split_into_blocks(self, text: str, doc_id: str = "active_context") -> List[ContextBlock]:
        """
        Splits raw text into cohesive blocks bounded strictly by block_size tokens,
        respecting paragraph and word boundaries.
        """
        paragraphs = text.split("\n\n")
        blocks: List[ContextBlock] = []
        current_chunk: List[str] = []
        current_tokens = 0
        block_idx = 0

        for p in paragraphs:
            p_tokens = estimate_tokens(p)
            if p_tokens > self.block_size:
                if current_chunk:
                    block_text = "\n\n".join(current_chunk)
                    blocks.append(ContextBlock(
                        block_index=block_idx,
                        doc_id=doc_id,
                        text=block_text,
                        token_count=current_tokens,
                    ))
                    block_idx += 1
                    current_chunk = []
                    current_tokens = 0

                sub_chunks = self._chunk_text_to_token_size(p, self.block_size)
                for sc in sub_chunks:
                    sc_tokens = estimate_tokens(sc)
                    blocks.append(ContextBlock(
                        block_index=block_idx,
                        doc_id=doc_id,
                        text=sc,
                        token_count=sc_tokens,
                    ))
                    block_idx += 1
                continue

            if current_tokens + p_tokens > self.block_size and current_chunk:
                block_text = "\n\n".join(current_chunk)
                blocks.append(ContextBlock(
                    block_index=block_idx,
                    doc_id=doc_id,
                    text=block_text,
                    token_count=current_tokens,
                ))
                block_idx += 1
                current_chunk = [p]
                current_tokens = p_tokens
            else:
                current_chunk.append(p)
                current_tokens += p_tokens

        if current_chunk:
            block_text = "\n\n".join(current_chunk)
            blocks.append(ContextBlock(
                block_index=block_idx,
                doc_id=doc_id,
                text=block_text,
                token_count=current_tokens,
            ))

        if not blocks and text:
            blocks.append(ContextBlock(
                block_index=0,
                doc_id=doc_id,
                text=text,
                token_count=estimate_tokens(text),
            ))

        total = len(blocks)
        for i, b in enumerate(blocks):
            if i == 0:
                b.is_sink = True
            if i == total - 1 and total > 1:
                b.is_recent = True

        return blocks

    def ingest_document(self, doc_id: str, text: str) -> int:
        """Stores a document's MoBA blocks in SQLite for fast sparse retrieval."""
        blocks = self.split_into_blocks(text, doc_id=doc_id)
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        cur.execute("DELETE FROM moba_blocks WHERE doc_id = ?", (doc_id,))
        for b in blocks:
            cur.execute("""
                INSERT OR REPLACE INTO moba_blocks (doc_id, block_index, text, token_count, is_sink, is_recent)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (doc_id, b.block_index, b.text, b.token_count, 1 if b.is_sink else 0, 1 if b.is_recent else 0))
        conn.commit()
        conn.close()
        return len(blocks)

    def _score_blocks_bm25(self, query: str, blocks: List[ContextBlock]) -> List[Tuple[ContextBlock, float]]:
        query_terms = re.findall(r"\w+", query.lower())
        if not query_terms:
            return [(b, 0.0) for b in blocks]

        if BM25_AVAILABLE:
            tokenized_corpus = [re.findall(r"\w+", b.text.lower()) for b in blocks]
            try:
                bm25 = BM25Okapi(tokenized_corpus)
                scores = bm25.get_scores(query_terms)
                return [(b, float(scores[i])) for i, b in enumerate(blocks)]
            except Exception:
                pass

        # Native BM25 fallback
        avg_len = sum(len(b.text.split()) for b in blocks) / max(1, len(blocks))
        doc_count = len(blocks)
        scored: List[Tuple[ContextBlock, float]] = []

        for b in blocks:
            words = b.text.lower().split()
            doc_len = len(words)
            score = 0.0
            for t in query_terms:
                tf = words.count(t)
                if tf > 0:
                    df = sum(1 for blk in blocks if t in blk.text.lower())
                    idf = math.log(1.0 + (doc_count - df + 0.5) / (df + 0.5))
                    k1 = 1.5
                    b_param = 0.75
                    norm = 1 - b_param + b_param * (doc_len / max(1.0, avg_len))
                    score += idf * (tf * (k1 + 1)) / (tf + k1 * norm)
            scored.append((b, score))

        return scored

    def route_context(
        self,
        doc_id: str,
        query: str,
        top_k: Optional[int] = None,
    ) -> MoBARouteResult:
        """
        Executes MoBA Sparse Attention Routing:
        - Retrieves all blocks for doc_id
        - Pins Sink Block (Block 0) and Recent Block (Last Block)
        - Computes block attention relevance for intermediate blocks
        - Assembles top-K blocks chronologically
        """
        start_time = time.time()
        k = top_k or self.top_k

        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()
        cur.execute("""
            SELECT block_index, text, token_count, is_sink, is_recent
            FROM moba_blocks WHERE doc_id = ? ORDER BY block_index ASC
        """, (doc_id,))
        rows = cur.fetchall()
        conn.close()

        if not rows:
            return MoBARouteResult(
                doc_id=doc_id,
                total_tokens=0,
                total_blocks=0,
                routed_blocks=[],
                routed_tokens=0,
                routed_text="",
                compression_ratio=1.0,
                duration_ms=(time.time() - start_time) * 1000,
            )

        all_blocks = [
            ContextBlock(
                block_index=r[0],
                doc_id=doc_id,
                text=r[1],
                token_count=r[2],
                is_sink=bool(r[3]),
                is_recent=bool(r[4]),
            )
            for r in rows
        ]

        total_tokens = sum(b.token_count for b in all_blocks)
        total_blocks = len(all_blocks)

        # If total blocks fits within budget, return full context
        if total_blocks <= k:
            routed_text = "\n\n".join(b.text for b in all_blocks)
            duration_ms = (time.time() - start_time) * 1000
            return MoBARouteResult(
                doc_id=doc_id,
                total_tokens=total_tokens,
                total_blocks=total_blocks,
                routed_blocks=all_blocks,
                routed_tokens=total_tokens,
                routed_text=routed_text,
                compression_ratio=1.0,
                duration_ms=duration_ms,
            )

        # MoBA Partitioning:
        # Pinned: Sink (first) and Recent (last)
        sink_block = all_blocks[0]
        recent_block = all_blocks[-1]
        intermediate_blocks = all_blocks[1:-1]

        # Score intermediate blocks
        scored = self._score_blocks_bm25(query, intermediate_blocks)
        scored.sort(key=lambda x: x[1], reverse=True)

        slots_available = max(1, k - 2)
        top_intermediate = [b for b, score in scored[:slots_available]]
        for b, s in scored[:slots_available]:
            b.score = s

        # Recombine selected blocks in chronological order
        selected_blocks = [sink_block] + top_intermediate + [recent_block]
        selected_blocks.sort(key=lambda b: b.block_index)

        # Deduplicate blocks
        seen = set()
        final_blocks = []
        for b in selected_blocks:
            if b.block_index not in seen:
                seen.add(b.block_index)
                final_blocks.append(b)

        routed_tokens = sum(b.token_count for b in final_blocks)
        routed_text = "\n\n--- [MoBA BLOCK BREAK] ---\n\n".join(b.text for b in final_blocks)
        duration_ms = (time.time() - start_time) * 1000
        compression_ratio = total_tokens / max(1, routed_tokens)

        return MoBARouteResult(
            doc_id=doc_id,
            total_tokens=total_tokens,
            total_blocks=total_blocks,
            routed_blocks=final_blocks,
            routed_tokens=routed_tokens,
            routed_text=routed_text,
            compression_ratio=compression_ratio,
            duration_ms=duration_ms,
        )

    def route_raw_text(
        self,
        text: str,
        query: str,
        doc_id: str = "temp_doc",
        top_k: Optional[int] = None,
    ) -> MoBARouteResult:
        """One-shot ingestion and routing of arbitrary raw long text."""
        self.ingest_document(doc_id, text)
        return self.route_context(doc_id, query, top_k=top_k)


_GLOBAL_MOBA_ROUTER: Optional[MoBAContextRouter] = None


def get_moba_context_router() -> MoBAContextRouter:
    global _GLOBAL_MOBA_ROUTER
    if _GLOBAL_MOBA_ROUTER is None:
        _GLOBAL_MOBA_ROUTER = MoBAContextRouter()
    return _GLOBAL_MOBA_ROUTER
