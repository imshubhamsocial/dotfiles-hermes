"""
U36: Multi-File Context Compactor & AST Sieve (PageRank Spine)
==============================================================
High-speed multi-file context compactor that dynamically extracts
architectural PageRank spines (<1,000 tokens) and targeted function
slices (<500 tokens) to prevent context drowning on 4B SLMs.

Integrates with:
  - SymbolGraph (U22): whole-codebase AST symbol graph + call edges
  - SymbolIndexer: per-file symbol maps
  - token_engine: token estimation for budget enforcement

Cache: /dev/shm/context_sieve.db (SQLite WAL) for fast re-query.
"""

import ast
import os
import re
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set

from .token_engine import estimate_tokens

# RAMDisk cache for hot re-query
DEFAULT_DB = "/dev/shm/context_sieve.db"


@dataclass
class SymbolNode:
    """Lightweight symbol node for spine computation."""
    id: str
    name: str
    kind: str
    file_path: str
    line_start: int
    line_end: int
    signature: str = ""
    parent: str = ""
    pagerank: float = 0.0


class ContextSieve:
    """
    Extracts whole-repo architectural PageRank spines (<1,000 tokens)
    and targeted function slices (<500 tokens) from a codebase.

    Uses SQLite WAL cache at /dev/shm/context_sieve.db for fast re-query.
    """

    SPINE_TOKEN_BUDGET = 1000
    SLICE_TOKEN_BUDGET = 500
    SUPPORTED_EXTS = {".py", ".js", ".ts"}

    def __init__(self, db_path: str = DEFAULT_DB, graph=None):
        self.db_path = db_path
        self._local = threading.local()
        self._graph = graph
        self._init_cache()

    # ── Cache Layer ───────────────────────────────────────────────────────
    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_cache(self):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS spine_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                root_dir TEXT NOT NULL,
                computed_at REAL NOT NULL,
                spine_text TEXT NOT NULL,
                UNIQUE(root_dir)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS slice_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                root_dir TEXT NOT NULL,
                target_symbols TEXT NOT NULL,
                computed_at REAL NOT NULL,
                slice_text TEXT NOT NULL,
                UNIQUE(root_dir, target_symbols)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS diff_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                patch_hash TEXT NOT NULL,
                computed_at REAL NOT NULL,
                diff_text TEXT NOT NULL,
                UNIQUE(file_path, patch_hash)
            )
        """)
        conn.commit()

    # ── Symbol Extraction ───────────────────────────────────────────────────
    def _scan_files(self, root_dir: str) -> List[Path]:
        root = Path(root_dir)
        files = []
        for ext in self.SUPPORTED_EXTS:
            files.extend(root.rglob(f"*{ext}"))
        # Filter out noise
        ignore = {".git", "__pycache__", "node_modules", ".venv", "venv"}
        return [
            f for f in files
            if not any(part in ignore for part in f.parts)
            and not f.name.startswith(".")
        ]

    def _extract_symbols(self, file_path: Path) -> List[SymbolNode]:
        """Extract symbols from a single file using AST."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return []

        if file_path.suffix != ".py":
            return self._extract_generic(file_path, content)

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return []

        nodes: List[SymbolNode] = []
        lines = content.splitlines()
        parent_stack: List[str] = []

        class Visitor(ast.NodeVisitor):
            def visit_ClassDef(self, node):
                sid = f"{file_path}::{node.name}"
                nodes.append(SymbolNode(
                    id=sid, name=node.name, kind="class",
                    file_path=str(file_path), line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    signature=_class_sig(node, lines),
                ))
                parent_stack.append(node.name)
                self.generic_visit(node)
                parent_stack.pop()

            def visit_FunctionDef(self, node):
                self._add_fn(node)

            def visit_AsyncFunctionDef(self, node):
                self._add_fn(node)

            def _add_fn(self, node):
                sid = f"{file_path}::{node.name}"
                parent = parent_stack[-1] if parent_stack else ""
                nodes.append(SymbolNode(
                    id=sid, name=node.name, kind="function",
                    file_path=str(file_path), line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    signature=_fn_sig(node, lines),
                    parent=parent,
                ))

        Visitor().visit(tree)
        return nodes

    @staticmethod
    def _fn_sig(node, lines) -> str:
        if node.lineno - 1 < len(lines):
            line = lines[node.lineno - 1].strip()
            if line.startswith("def ") or line.startswith("async def "):
                return line.rstrip(":")
        return f"def {node.name}(...)"

    @staticmethod
    def _class_sig(node, lines) -> str:
        if node.lineno - 1 < len(lines):
            line = lines[node.lineno - 1].strip()
            if line.startswith("class "):
                return line.rstrip(":")
        return f"class {node.name}(...)"

    def _extract_generic(self, file_path: Path, content: str) -> List[SymbolNode]:
        """Fallback for JS/TS using simple regex extraction."""
        nodes = []
        # Classes
        for m in re.finditer(r'class\s+([A-Za-z0-9_$]+)', content):
            line_no = content[:m.start()].count("\n") + 1
            nodes.append(SymbolNode(
                id=f"{file_path}::{m.group(1)}", name=m.group(1), kind="class",
                file_path=str(file_path), line_start=line_no, line_end=line_no,
                signature=f"class {m.group(1)}",
            ))
        # Functions
        for m in re.finditer(r'(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(', content):
            line_no = content[:m.start()].count("\n") + 1
            nodes.append(SymbolNode(
                id=f"{file_path}::{m.group(1)}", name=m.group(1), kind="function",
                file_path=str(file_path), line_start=line_no, line_end=line_no,
                signature=f"function {m.group(1)}()",
            ))
        return nodes

    # ── PageRank Spine ──────────────────────────────────────────────────────
    def _compute_edges(self, nodes: List[SymbolNode], root_dir: str) -> Dict[str, Set[str]]:
        """Compute call edges from source code for PageRank."""
        edges: Dict[str, Set[str]] = {n.id: set() for n in nodes}
        name_to_ids: Dict[str, List[str]] = {}
        for n in nodes:
            name_to_ids.setdefault(n.name, []).append(n.id)

        for n in nodes:
            try:
                content = Path(n.file_path).read_text(encoding="utf-8", errors="ignore")
                block = "\n".join(content.splitlines()[n.line_start - 1:n.line_end])
            except Exception:
                continue

            # Find called names in this block
            called = set(re.findall(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*\(', block))
            for c in called:
                if c in name_to_ids:
                    for tid in name_to_ids[c]:
                        if tid != n.id:
                            edges[n.id].add(tid)
        return edges

    def _pagerank(self, edges: Dict[str, Set[str]], damping: float = 0.85, iterations: int = 20) -> Dict[str, float]:
        """Compute PageRank centrality over the call graph."""
        nodes = list(edges.keys())
        if not nodes:
            return {}

        # Build reverse edges
        rev: Dict[str, List[str]] = {n: [] for n in nodes}
        for src, dsts in edges.items():
            for d in dsts:
                rev[d].append(src)

        # Out-degree
        out_deg = {n: max(1, len(edges[n])) for n in nodes}

        # Init
        pr = {n: 1.0 / len(nodes) for n in nodes}

        for _ in range(iterations):
            new_pr = {}
            for n in nodes:
                # Sum of incoming PR / out-degree
                incoming = sum(pr[s] / out_deg[s] for s in rev[n])
                new_pr[n] = (1 - damping) / len(nodes) + damping * incoming
            pr = new_pr

        return pr

    def build_repo_spine(self, root_dir: str, max_tokens: int = SPINE_TOKEN_BUDGET) -> str:
        """
        Builds high-level structural outline of repo symbols, classes,
        and entrypoints using PageRank centrality. Budget: <1,000 tokens.
        """
        cache_key = os.path.abspath(root_dir)
        cached = self._get_cached_spine(cache_key)
        if cached is not None:
            return cached

        files = self._scan_files(root_dir)
        nodes: List[SymbolNode] = []
        for f in files:
            nodes.extend(self._extract_symbols(f))

        if not nodes:
            return "# [ContextSieve] No symbols found in repo"

        # PageRank over call graph
        edges = self._compute_edges(nodes, root_dir)
        pr = self._pagerank(edges)

        for n in nodes:
            n.pagerank = pr.get(n.id, 0.0)

        # Sort by PageRank (architectural importance)
        nodes.sort(key=lambda n: n.pagerank, reverse=True)

        # Build spine with token budget
        lines = [f"# REPO SPINE: {Path(root_dir).name} ({len(nodes)} symbols, {len(files)} files)"]
        total_tokens = estimate_tokens("\n".join(lines))

        for n in nodes:
            entry = f"{'  ' if n.kind == 'function' and n.parent else ''}{n.kind}: {n.name} [{Path(n.file_path).name}:{n.line_start}] PR={n.pagerank:.3f}"
            if n.signature:
                entry += f"\n    {n.signature}"
            entry_tokens = estimate_tokens(entry)
            if total_tokens + entry_tokens > max_tokens:
                lines.append(f"... ({len(nodes) - len(lines) + 1} more symbols truncated)")
                break
            lines.append(entry)
            total_tokens += entry_tokens

        spine = "\n".join(lines)
        self._cache_spine(cache_key, spine)
        return spine

    # ── Targeted Slice ──────────────────────────────────────────────────────
    def slice_relevant_context(self, root_dir: str, target_symbols: List[str], max_tokens: int = SLICE_TOKEN_BUDGET) -> str:
        """
        Slices only the targeted functions/classes and their immediate
        caller/callee signatures. Budget: <500 tokens.
        """
        cache_key = ",".join(sorted(target_symbols))
        cached = self._get_cached_slice(os.path.abspath(root_dir), cache_key)
        if cached is not None:
            return cached

        files = self._scan_files(root_dir)
        symbol_map: Dict[str, SymbolNode] = {}
        for f in files:
            for n in self._extract_symbols(f):
                symbol_map[n.name] = n

        # Collect targets + immediate neighbors
        selected: Set[str] = set()
        for target in target_symbols:
            if target in symbol_map:
                node = symbol_map[target]
                selected.add(target)
                # Find callers/callees via source scan
                for other_name, other_node in symbol_map.items():
                    if other_name == target:
                        continue
                    if self._is_related(node, other_node):
                        selected.add(other_name)

        # Build slice with token budget
        lines = [f"# SLICE: {', '.join(target_symbols)}"]
        total_tokens = estimate_tokens("\n".join(lines))

        for name in sorted(selected):
            node = symbol_map[name]
            entry = f"{node.kind}: {node.name} [{Path(node.file_path).name}:{node.line_start}]"
            if node.signature:
                entry += f"\n  {node.signature}"
            entry_tokens = estimate_tokens(entry)
            if total_tokens + entry_tokens > max_tokens:
                lines.append(f"... (+{len(selected) - len(lines) + 1} more)")
                break
            lines.append(entry)
            total_tokens += entry_tokens

        slice_text = "\n".join(lines)
        self._cache_slice(os.path.abspath(root_dir), cache_key, slice_text)
        return slice_text

    def _is_related(self, a: SymbolNode, b: SymbolNode) -> bool:
        """Check if two symbols are related (caller/callee/sibling)."""
        # Same file + close lines = likely related
        if a.file_path == b.file_path:
            if abs(a.line_start - b.line_start) < 50:
                return True
        # Same parent class
        if a.parent and a.parent == b.parent:
            return True
        # a calls b or b calls a (scan sources)
        if self._calls(a, b.name) or self._calls(b, a.name):
            return True
        return False

    def _calls(self, node: SymbolNode, target_name: str) -> bool:
        """Check if node's source block calls target_name."""
        try:
            content = Path(node.file_path).read_text(encoding="utf-8", errors="ignore")
            block = "\n".join(content.splitlines()[node.line_start - 1:node.line_end])
            return f"{target_name}(" in block
        except Exception:
            return False

    # ── Diff Compression ─────────────────────────────────────────────────────
    def compress_diff_context(self, file_path: str, proposed_patch: str) -> str:
        """
        Minimizes token overhead for code diff generation.
        Returns a compact unified diff with only changed hunks.
        """
        import hashlib
        patch_hash = hashlib.md5(proposed_patch.encode()).hexdigest()[:12]
        cached = self._get_cached_diff(file_path, patch_hash)
        if cached is not None:
            return cached

        p = Path(file_path)
        if not p.exists():
            return f"# [ContextSieve] File not found: {file_path}"

        try:
            original = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return f"# [ContextSieve] Cannot read: {file_path}"

        orig_lines = original.splitlines()
        patch_lines = proposed_patch.splitlines()

        # Compute line-level diff (simple LCS-based)
        diff = self._minimal_diff(orig_lines, patch_lines)

        result = f"# DIFF: {p.name} ({len(diff)} changed lines)"
        result += f"\n```diff\n{diff}\n```"

        self._cache_diff(file_path, patch_hash, result)
        return result

    def _minimal_diff(self, a: List[str], b: List[str]) -> str:
        """Compute a minimal line-level diff using LCS."""
        # LCS DP
        m, n = len(a), len(b)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(m - 1, -1, -1):
            for j in range(n - 1, -1, -1):
                if a[i] == b[j]:
                    dp[i][j] = dp[i + 1][j + 1] + 1
                else:
                    dp[i][j] = max(dp[i + 1][j], dp[i][j + 1])

        i = j = 0
        out = []
        while i < m and j < n:
            if a[i] == b[j]:
                out.append(f"  {a[i]}")
                i += 1
                j += 1
            elif dp[i + 1][j] >= dp[i][j + 1]:
                out.append(f"- {a[i]}")
                i += 1
            else:
                out.append(f"+ {b[j]}")
                j += 1
        while i < m:
            out.append(f"- {a[i]}")
            i += 1
        while j < n:
            out.append(f"+ {b[j]}")
            j += 1

        return "\n".join(out)

    # ── Cache API ────────────────────────────────────────────────────────────
    def _get_cached_spine(self, root_dir: str) -> Optional[str]:
        try:
            cur = self._get_conn().cursor()
            cur.execute("SELECT spine_text FROM spine_cache WHERE root_dir = ?", (root_dir,))
            row = cur.fetchone()
            return row["spine_text"] if row else None
        except Exception:
            return None

    def _cache_spine(self, root_dir: str, spine: str) -> None:
        try:
            conn = self._get_conn()
            conn.execute(
                "INSERT OR REPLACE INTO spine_cache (root_dir, computed_at, spine_text) VALUES (?, ?, ?)",
                (root_dir, time.time(), spine),
            )
            conn.commit()
        except Exception:
            pass

    def _get_cached_slice(self, root_dir: str, symbols_key: str) -> Optional[str]:
        try:
            cur = self._get_conn().cursor()
            cur.execute(
                "SELECT slice_text FROM slice_cache WHERE root_dir = ? AND target_symbols = ?",
                (root_dir, symbols_key),
            )
            row = cur.fetchone()
            return row["slice_text"] if row else None
        except Exception:
            return None

    def _cache_slice(self, root_dir: str, symbols_key: str, slice_text: str) -> None:
        try:
            conn = self._get_conn()
            conn.execute(
                "INSERT OR REPLACE INTO slice_cache (root_dir, target_symbols, computed_at, slice_text) VALUES (?, ?, ?, ?)",
                (root_dir, symbols_key, time.time(), slice_text),
            )
            conn.commit()
        except Exception:
            pass

    def _get_cached_diff(self, file_path: str, patch_hash: str) -> Optional[str]:
        try:
            cur = self._get_conn().cursor()
            cur.execute(
                "SELECT diff_text FROM diff_cache WHERE file_path = ? AND patch_hash = ?",
                (file_path, patch_hash),
            )
            row = cur.fetchone()
            return row["diff_text"] if row else None
        except Exception:
            return None

    def _cache_diff(self, file_path: str, patch_hash: str, diff_text: str) -> None:
        try:
            conn = self._get_conn()
            conn.execute(
                "INSERT OR REPLACE INTO diff_cache (file_path, patch_hash, computed_at, diff_text) VALUES (?, ?, ?, ?)",
                (file_path, patch_hash, time.time(), diff_text),
            )
            conn.commit()
        except Exception:
            pass


# Module-level signature helpers for Visitor class
def _fn_sig(node, lines) -> str:
    if node.lineno - 1 < len(lines):
        line = lines[node.lineno - 1].strip()
        if line.startswith("def ") or line.startswith("async def "):
            return line.rstrip(":")
    return f"def {node.name}(...)"


def _class_sig(node, lines) -> str:
    if node.lineno - 1 < len(lines):
        line = lines[node.lineno - 1].strip()
        if line.startswith("class "):
            return line.rstrip(":")
    return f"class {node.name}(...)"


# Convenience factory
def create_ramdisk_sieve() -> ContextSieve:
    """Create a ContextSieve with RAMDisk SQLite WAL cache."""
    return ContextSieve(DEFAULT_DB)


__all__ = ["ContextSieve", "create_ramdisk_sieve", "SymbolNode"]
