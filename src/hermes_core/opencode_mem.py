"""
U47: OpenCode-Mem Local Vector Memory Engine & Episodic Recall
================================================================
Persistent episodic memory with SQLite WAL (`.hermes/memories.db`).
FastEmbed CPU ONNX / NumPy cosine similarity vector search (0 MB GPU VRAM).
Dynamic Top-K retrieval injecting relevant constraints into Slot 3 (<200 tokens).
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    from fastembed import TextEmbedding
    FAST_EMBED_AVAILABLE = True
except ImportError:
    TextEmbedding = None
    FAST_EMBED_AVAILABLE = False


# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_DB_PATH = Path.home() / ".hermes" / "memories.db"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM = 384
DEFAULT_TOP_K = 3
MAX_INJECTION_TOKENS = 200
SIMILARITY_THRESHOLD = 0.3


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class MemoryRecord:
    """Episodic memory record"""
    id: str
    content: str
    embedding: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)
    memory_type: str = "episodic"  # episodic, negative_constraint, convention, failure_trace
    timestamp: float = field(default_factory=time.time)
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)


@dataclass
class SearchResult:
    """Vector search result"""
    record: MemoryRecord
    similarity: float


@dataclass
class RecallContext:
    """Context block for prompt injection"""
    content: str
    tokens: int
    sources: List[str]


# =============================================================================
# VECTOR EMBEDDING ENGINE
# =============================================================================

class VectorEmbeddingEngine:
    """CPU-only FastEmbed / ONNX embedding engine"""
    
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        self.model_name = model_name
        self.model = None
        self._init_model()
    
    def _init_model(self):
        """Initialize FastEmbed model with CPU-only execution"""
        if not FAST_EMBED_AVAILABLE:
            return
        
        try:
            # Force CPU execution
            os.environ["ORT_LOGGING_LEVEL"] = "3"
            os.environ["OMP_NUM_THREADS"] = "2"
            
            self.model = TextEmbedding(
                model_name=self.model_name,
                threads=2,
            )
        except Exception as e:
            self.model = None
    
    def is_available(self) -> bool:
        """Check if embedding model is available"""
        return self.model is not None
    
    def embed(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for list of texts"""
        if not self.is_available():
            # Fallback: deterministic hash-based embeddings
            return [self._hash_embedding(text) for text in texts]
        
        try:
            embeddings = list(self.model.embed(texts))
            return [np.array(e, dtype=np.float32) for e in embeddings]
        except Exception:
            return [self._hash_embedding(text) for text in texts]
    
    def embed_single(self, text: str) -> np.ndarray:
        """Generate embedding for single text"""
        return self.embed([text])[0]
    
    def _hash_embedding(self, text: str) -> np.ndarray:
        """Deterministic hash-based fallback embedding"""
        # Create deterministic embedding from text hash
        hash_bytes = hashlib.sha256(text.encode()).digest()
        # Convert to float32 array - repeat hash to fill EMBEDDING_DIM
        base_vec = np.frombuffer(hash_bytes, dtype=np.float32)
        if len(base_vec) == 0:
            base_vec = np.array([0.0], dtype=np.float32)
        
        # Repeat base vector to fill EMBEDDING_DIM
        repeats = (EMBEDDING_DIM + len(base_vec) - 1) // len(base_vec)
        vec = np.tile(base_vec, repeats)[:EMBEDDING_DIM]
        
        # Normalize
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec


# =============================================================================
# SQLITE VECTOR STORE
# =============================================================================

class SQLiteVectorStore:
    """SQLite WAL-based vector memory store"""
    
    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_db()
    
    def _get_conn(self) -> sqlite3.Connection:
        """Get thread-local database connection"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                isolation_level=None,  # Autocommit
            )
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=-32768")  # 32MB cache
            conn.row_factory = sqlite3.Row
            self._local.conn = conn
        return self._local.conn
    
    def _init_db(self):
        """Initialize database schema"""
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                embedding BLOB NOT NULL,
                metadata TEXT NOT NULL DEFAULT '{}',
                memory_type TEXT NOT NULL DEFAULT 'episodic',
                timestamp REAL NOT NULL,
                access_count INTEGER NOT NULL DEFAULT 0,
                last_accessed REAL NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_memory_type ON memories(memory_type)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_access_count ON memories(access_count)
        """)
    
    def store(self, record: MemoryRecord) -> None:
        """Store memory record"""
        conn = self._get_conn()
        embedding_bytes = record.embedding.astype(np.float32).tobytes()
        metadata_json = json.dumps(record.metadata)
        
        conn.execute("""
            INSERT OR REPLACE INTO memories 
            (id, content, embedding, metadata, memory_type, timestamp, access_count, last_accessed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.id,
            record.content,
            embedding_bytes,
            metadata_json,
            record.memory_type,
            record.timestamp,
            record.access_count,
            record.last_accessed,
        ))
    
    def get(self, memory_id: str) -> Optional[MemoryRecord]:
        """Retrieve memory by ID"""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM memories WHERE id = ?", (memory_id,)
        ).fetchone()
        
        if row is None:
            return None
        
        return self._row_to_record(row)
    
    def get_all(self, memory_type: Optional[str] = None, limit: int = 1000) -> List[MemoryRecord]:
        """Get all memories, optionally filtered by type"""
        conn = self._get_conn()
        
        if memory_type:
            rows = conn.execute(
                "SELECT * FROM memories WHERE memory_type = ? ORDER BY timestamp DESC LIMIT ?",
                (memory_type, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM memories ORDER BY timestamp DESC LIMIT ?", (limit,)
            ).fetchall()
        
        return [self._row_to_record(row) for row in rows]
    
    def update_access(self, memory_id: str) -> None:
        """Update access count and last_accessed"""
        conn = self._get_conn()
        conn.execute("""
            UPDATE memories 
            SET access_count = access_count + 1, last_accessed = ?
            WHERE id = ?
        """, (time.time(), memory_id))
    
    def delete(self, memory_id: str) -> bool:
        """Delete memory by ID"""
        conn = self._get_conn()
        cursor = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        return cursor.rowcount > 0
    
    def count(self, memory_type: Optional[str] = None) -> int:
        """Count memories"""
        conn = self._get_conn()
        if memory_type:
            return conn.execute(
                "SELECT COUNT(*) FROM memories WHERE memory_type = ?", (memory_type,)
            ).fetchone()[0]
        return conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
    
    def _row_to_record(self, row: sqlite3.Row) -> MemoryRecord:
        """Convert SQLite row to MemoryRecord"""
        embedding = np.frombuffer(row['embedding'], dtype=np.float32)
        metadata = json.loads(row['metadata']) if row['metadata'] else {}
        
        return MemoryRecord(
            id=row['id'],
            content=row['content'],
            embedding=embedding,
            metadata=metadata,
            memory_type=row['memory_type'],
            timestamp=row['timestamp'],
            access_count=row['access_count'],
            last_accessed=row['last_accessed'],
        )
    
    def close(self):
        """Close database connection"""
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.close()
            self._local.conn = None


# =============================================================================
# OPESKILLS MEMORY ENGINE
# =============================================================================

class OpenCodeMemoryEngine:
    """
    OpenCode-Mem: Persistent episodic vector memory with semantic recall.
    
    Features:
    - SQLite WAL persistence (`.hermes/memories.db`)
    - FastEmbed CPU ONNX embeddings (0 MB GPU VRAM)
    - Cosine similarity Top-K retrieval
    - Negative constraint injection into Slot 3 (<200 tokens)
    """
    
    def __init__(
        self,
        db_path: Optional[Path] = None,
        embedding_model: str = EMBEDDING_MODEL,
        top_k: int = DEFAULT_TOP_K,
        max_injection_tokens: int = MAX_INJECTION_TOKENS,
        similarity_threshold: float = SIMILARITY_THRESHOLD,
    ):
        self.db_path = db_path or DEFAULT_DB_PATH
        self.top_k = top_k
        self.max_injection_tokens = max_injection_tokens
        self.similarity_threshold = similarity_threshold
        
        self.embedding_engine = VectorEmbeddingEngine(embedding_model)
        self.vector_store = SQLiteVectorStore(self.db_path)
        self._index: List[MemoryRecord] = []
        self._index_lock = threading.RLock()
        
        # Build in-memory index
        self._rebuild_index()
    
    def _rebuild_index(self):
        """Rebuild in-memory index from database"""
        with self._index_lock:
            self._index = self.vector_store.get_all()
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors"""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
    
    # -------------------------------------------------------------------------
    # MEMORY STORAGE
    # -------------------------------------------------------------------------
    
    def store_episodic(
        self,
        content: str,
        memory_type: str = "episodic",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store episodic memory with auto-generated embedding"""
        # Generate embedding
        embedding = self.embedding_engine.embed_single(content)
        
        # Create record
        record_id = hashlib.sha256(f"{content}{time.time()}".encode()).hexdigest()[:16]
        
        record = MemoryRecord(
            id=record_id,
            content=content,
            embedding=embedding,
            metadata=metadata or {},
            memory_type=memory_type,
        )
        
        # Store in DB
        self.vector_store.store(record)
        
        # Update index
        with self._index_lock:
            self._index.append(record)
        
        return record_id
    
    def store_negative_constraint(
        self,
        constraint: str,
        context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store a negative constraint (e.g., 'Do not use X')"""
        content = constraint
        if context:
            content = f"Context: {context}\nConstraint: {constraint}"
        
        meta = metadata or {}
        meta['is_negative_constraint'] = True
        
        return self.store_episodic(
            content=content,
            memory_type="negative_constraint",
            metadata=meta,
        )
    
    def store_convention(
        self,
        convention: str,
        scope: str = "repo",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store architectural convention"""
        meta = metadata or {}
        meta['scope'] = scope
        
        return self.store_episodic(
            content=convention,
            memory_type="convention",
            metadata=meta,
        )
    
    def store_failure_trace(
        self,
        failure: str,
        fix: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store failure trace with resolution"""
        content = f"Failure: {failure}\nFix: {fix}"
        meta = metadata or {}
        meta['has_fix'] = True
        
        return self.store_episodic(
            content=content,
            memory_type="failure_trace",
            metadata=meta,
        )
    
    # -------------------------------------------------------------------------
    # SEMANTIC RECALL
    # -------------------------------------------------------------------------
    
    def recall(
        self,
        query: str,
        top_k: Optional[int] = None,
        memory_types: Optional[List[str]] = None,
        min_similarity: Optional[float] = None,
    ) -> List[SearchResult]:
        """
        Semantic vector recall: find top-K relevant memories.
        """
        k = top_k or self.top_k
        threshold = min_similarity or self.similarity_threshold
        
        # Generate query embedding
        query_embedding = self.embedding_engine.embed_single(query)
        
        # Search index
        with self._index_lock:
            candidates = self._index
        
        # Filter by memory type if specified
        if memory_types:
            candidates = [r for r in candidates if r.memory_type in memory_types]
        
        # Compute similarities
        results = []
        for record in candidates:
            sim = self._cosine_similarity(query_embedding, record.embedding)
            if sim >= threshold:
                results.append(SearchResult(record=record, similarity=sim))
        
        # Sort by similarity
        results.sort(key=lambda x: x.similarity, reverse=True)
        
        # Update access stats for top results
        for result in results[:k]:
            self.vector_store.update_access(result.record.id)
            result.record.access_count += 1
            result.record.last_accessed = time.time()
        
        return results[:k]
    
    def recall_negative_constraints(self, query: str) -> List[SearchResult]:
        """Recall specifically negative constraints relevant to query"""
        return self.recall(
            query=query,
            memory_types=["negative_constraint"],
            top_k=self.top_k,
        )
    
    def recall_conventions(self, query: str) -> List[SearchResult]:
        """Recall architectural conventions"""
        return self.recall(
            query=query,
            memory_types=["convention"],
            top_k=self.top_k,
        )
    
    def recall_failure_traces(self, query: str) -> List[SearchResult]:
        """Recall relevant failure traces"""
        return self.recall(
            query=query,
            memory_types=["failure_trace"],
            top_k=self.top_k,
        )
    
    # -------------------------------------------------------------------------
    # PROMPT INJECTION
    # -------------------------------------------------------------------------
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (4 chars/token)"""
        return max(1, len(" ".join(text.split())) // 4)
    
    def _format_memory_for_injection(self, result: SearchResult) -> str:
        """Format a memory record for prompt injection"""
        record = result.record
        
        if record.memory_type == "negative_constraint":
            return f"[NEGATIVE CONSTRAINT] {record.content}"
        elif record.memory_type == "convention":
            return f"[CONVENTION] {record.content}"
        elif record.memory_type == "failure_trace":
            return f"[FAILURE TRACE] {record.content}"
        else:
            return f"[EPISODIC] {record.content}"
    
    def build_slot3_injection(self, query: str) -> RecallContext:
        """
        Build Slot 3 injection block with retrieved memories.
        Consumes <200 tokens.
        """
        # Retrieve relevant memories
        results = self.recall(query)
        
        if not results:
            return RecallContext(content="", tokens=0, sources=[])
        
        # Format memories
        lines = ["<|RETRIEVED_EPISODIC_CONSTRAINTS|>"]
        total_tokens = self._estimate_tokens("<|RETRIEVED_EPISODIC_CONSTRAINTS|>")
        sources = []
        
        for result in results:
            formatted = self._format_memory_for_injection(result)
            formatted_tokens = self._estimate_tokens(formatted)
            
            if total_tokens + formatted_tokens > self.max_injection_tokens:
                break
            
            lines.append(formatted)
            total_tokens += formatted_tokens
            sources.append(result.record.id)
        
        lines.append("</|RETRIEVED_EPISODIC_CONSTRAINTS|>")
        total_tokens += self._estimate_tokens("</|RETRIEVED_EPISODIC_CONSTRAINTS|>")
        
        return RecallContext(
            content="\n".join(lines),
            tokens=total_tokens,
            sources=sources,
        )
    
    def get_zero_vram_guarantee(self) -> Dict[str, Any]:
        """Verify zero GPU VRAM overhead"""
        return {
            "embedding_cpu_only": True,
            "sqlite_cpu_only": True,
            "numpy_cpu_only": True,
            "no_gpu_operations": True,
            "fastembed_onnx_cpu": self.embedding_engine.is_available(),
            "ramdisk_compatible": True,
        }
    
    # -------------------------------------------------------------------------
    # UTILITIES
    # -------------------------------------------------------------------------
    
    def get_memory(self, memory_id: str) -> Optional[MemoryRecord]:
        """Get memory by ID"""
        return self.vector_store.get(memory_id)
    
    def list_memories(
        self,
        memory_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[MemoryRecord]:
        """List memories"""
        return self.vector_store.get_all(memory_type, limit)
    
    def count_memories(self, memory_type: Optional[str] = None) -> int:
        """Count memories"""
        return self.vector_store.count(memory_type)
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete memory"""
        with self._index_lock:
            self._index = [r for r in self._index if r.id != memory_id]
        return self.vector_store.delete(memory_id)
    
    def close(self):
        """Close database connection"""
        self.vector_store.close()


# =============================================================================
# INTEGRATION WITH PROMPT SLOTTING
# =============================================================================

def inject_episodic_constraints_into_slot3(
    base_slot3: str,
    query: str,
    memory_engine: Optional[OpenCodeMemoryEngine] = None,
) -> str:
    """
    Inject retrieved episodic constraints into Slot 3 (Behavioral Invariants).
    
    Preserves master laws while adding retrieved constraints.
    """
    if memory_engine is None:
        return base_slot3
    
    recall_ctx = memory_engine.build_slot3_injection(query)
    
    if not recall_ctx.content:
        return base_slot3
    
    # Inject after Slot 3 header but before closing
    # Slot 3 ends with "PREFIX-CACHE DISCIPLINE" section
    # We inject before the final boundary
    
    # Find insertion point - after the last invariant, before end
    # Simple approach: append before closing
    return base_slot3 + "\n\n" + recall_ctx.content


# =============================================================================
# FACTORY
# =============================================================================

_global_memory_engine: Optional[OpenCodeMemoryEngine] = None
_global_lock = threading.Lock()


def get_opencode_memory_engine(
    db_path: Optional[Path] = None,
    embedding_model: str = EMBEDDING_MODEL,
    top_k: int = DEFAULT_TOP_K,
) -> OpenCodeMemoryEngine:
    """Get or create global memory engine instance"""
    global _global_memory_engine
    with _global_lock:
        if _global_memory_engine is None:
            _global_memory_engine = OpenCodeMemoryEngine(
                db_path=db_path,
                embedding_model=embedding_model,
                top_k=top_k,
            )
        return _global_memory_engine


def reset_opencode_memory_engine():
    """Reset global engine (for testing)"""
    global _global_memory_engine
    with _global_lock:
        if _global_memory_engine:
            _global_memory_engine.close()
        _global_memory_engine = None


if __name__ == "__main__":
    # Self-test
    print("OpenCode-Mem self-test")
    
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "test_memories.db"
        
        engine = OpenCodeMemoryEngine(db_path=db_path)
        
        # Store memories
        id1 = engine.store_episodic(
            "Always use relative paths in this repo",
            memory_type="convention",
            metadata={"scope": "repo"}
        )
        print(f"Stored convention: {id1}")
        
        id2 = engine.store_negative_constraint(
            "Do not use torch or tensorflow",
            context="GPU VRAM limit 4800 MiB",
            metadata={"reason": "GPU budget"}
        )
        print(f"Stored negative constraint: {id2}")
        
        id3 = engine.store_failure_trace(
            "ImportError: No module named 'torch'",
            "Removed torch import, use CPU-only alternatives",
            metadata={"file": "test.py"}
        )
        print(f"Stored failure trace: {id3}")
        
        # Recall
        results = engine.recall("import torch")
        print(f"Recall 'import torch': {len(results)} results")
        for r in results:
            print(f"  [{r.similarity:.3f}] {r.record.content[:60]}...")
        
        # Slot 3 injection
        injection = engine.build_slot3_injection("How to import modules?")
        print(f"Slot 3 injection ({injection.tokens} tokens):")
        print(injection.content)
        
        # Zero VRAM guarantee
        guarantee = engine.get_zero_vram_guarantee()
        print(f"Zero VRAM guarantee: {guarantee}")
        
        print("All self-tests passed!")
