"""
U20: IDE Knowledge Substrate & Type Signature Resolver
======================================================
Pre-LLM IDE developer speed architecture for 4B SLMs.

Three components:
  1. TypeSignatureResolver — loads authoritative type definitions from
     `/ws-ai/types/` (POSIX C, Three.js, Node.js) and returns exact
     single-line signatures on demand. Eliminates parametric memory
     hallucination (4B Trap: deprecated API calls like Geometry vs
     BufferGeometry).

  2. SymbolIndex — lightweight AST symbol indexer backed by SQLite in
     RAMDisk (`/dev/shm/symbol_graph.db`). Provides sub-2ms cross-file
     signature lookups so @coder never needs to read full sibling files.

  3. ScaffoldRegistry — pre-baked gold-standard project templates.
     @architect emits `"template: <name>, customize: [field]"` allowing
     @coder to emit surgical 5-line patches instead of hallucinating
     300 lines of boilerplate.

All queries return structured dicts. No LLM self-grading (Zero-Sorry).
"""

import os
import re
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# 1. Type Signature Resolver
# ---------------------------------------------------------------------------

def _resolve_types_root() -> Path:
    pkg_types = Path(__file__).resolve().parent / "types"
    if pkg_types.is_dir():
        return pkg_types
    user_types = Path.home() / ".hermes" / "types"
    if user_types.is_dir():
        return user_types
    legacy = Path(__file__).resolve().parents[2] / "types"
    return legacy


_TYPES_ROOT = _resolve_types_root()


def _load_type_file(path: Path) -> Dict[str, str]:
    """Parse a type definition file (key: signature lines)."""
    symbols = {}
    if not path.exists():
        return symbols
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, sig = line.partition(":")
            symbols[key.strip()] = sig.strip()
    return symbols


def _discover_type_files(root: Path) -> Dict[str, Dict[str, str]]:
    """Walk types root and load all .types files into a nested dict."""
    registry: Dict[str, Dict[str, str]] = {}
    if not root.is_dir():
        return registry
    for category_dir in sorted(root.iterdir()):
        if not category_dir.is_dir():
            continue
        cat_name = category_dir.name
        cat_symbols: Dict[str, str] = {}
        for tf in sorted(category_dir.glob("*.types")):
            cat_symbols.update(_load_type_file(tf))
        if cat_symbols:
            registry[cat_name] = cat_symbols
    return registry


class TypeSignatureResolver:
    """Resolve exact type signatures from the authoritative type repository.

    Usage:
        resolver = TypeSignatureResolver()
        sig = resolver.resolve("THREE.BufferGeometry")
        # Returns: "class BufferGeometry extends BufferAttribute"
    """

    def __init__(self, types_root: Optional[Path] = None):
        self._root = types_root or _TYPES_ROOT
        self._registry: Optional[Dict[str, Dict[str, str]]] = None

    def _ensure_loaded(self):
        if self._registry is None:
            self._registry = _discover_type_files(self._root)

    def resolve(self, query: str) -> Optional[str]:
        """Look up an exact type signature by fully-qualified name.

        Supports:
          - Direct match: "THREE.BufferGeometry" → look in 'threejs' category
          - Prefix match: "epoll_event" → look in 'posix' category
          - Cross-category fallback: search all categories
        """
        self._ensure_loaded()
        if not self._registry:
            return None

        # Try category-prefixed lookup (e.g. "THREE.BufferGeometry" → threejs)
        parts = query.split(".", 1)
        if len(parts) == 2:
            prefix = parts[0].upper()
            name = parts[1]
            category_map = {
                "THREE": "threejs",
                "POSIX": "posix",
                "NODE": "nodejs",
            }
            cat = category_map.get(prefix)
            if cat and cat in self._registry:
                sig = self._registry[cat].get(name)
                if sig:
                    return sig

        # Cross-category fallback
        for cat_symbols in self._registry.values():
            sig = cat_symbols.get(query)
            if sig:
                return sig
            # Try partial match (末尾匹配)
            for sym_name, sym_sig in cat_symbols.items():
                if sym_name.endswith(query) or query.endswith(sym_name):
                    return sym_sig
        return None

    def list_categories(self) -> List[str]:
        self._ensure_loaded()
        return sorted(self._registry.keys()) if self._registry else []

    def list_symbols(self, category: Optional[str] = None) -> List[str]:
        self._ensure_loaded()
        if not self._registry:
            return []
        if category and category in self._registry:
            return sorted(self._registry[category].keys())
        result = []
        for cat_symbols in self._registry.values():
            result.extend(cat_symbols.keys())
        return sorted(result)

    def summary_tokens(self) -> int:
        """Estimate token cost of loading all type summaries."""
        cats = self.list_categories()
        syms = self.list_symbols()
        text = f"types:{len(cats)} cats,{len(syms)} syms"
        return max(1, len(text) // 4)


# ---------------------------------------------------------------------------
# 2. Symbol Index (SQLite-backed, RAMDisk)
# ---------------------------------------------------------------------------

_DEFAULT_DB = Path("/dev/shm/symbol_graph.db")


class SymbolIndex:
    """Lightweight workspace symbol indexer backed by SQLite.

    Symbols are extracted via regex (Python def/class, JS function/const/class).
    For production, tree-sitter would replace this regex layer — the SQLite
    storage and query interface remain identical.

    Sub-2ms query latency on /dev/shm (RAMDisk).
    """

    def __init__(self, db_path: Optional[Path] = None):
        self._db_path = db_path or _DEFAULT_DB
        self._conn: Optional[sqlite3.Connection] = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self._db_path))
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS symbols (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    file TEXT NOT NULL,
                    line INTEGER,
                    signature TEXT
                )
            """)
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_name ON symbols(name)"
            )
            self._conn.commit()
        return self._conn

    def index_file(self, filepath: str, content: Optional[str] = None) -> int:
        """Index symbols from a source file. Returns count of symbols indexed."""
        conn = self._get_conn()
        if content is None:
            try:
                content = Path(filepath).read_text(encoding="utf-8", errors="replace")
            except Exception:
                return 0

        symbols = []
        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            # Python: def, class
            m = re.match(r"^(?:async\s+)?def\s+(\w+)\s*\(", stripped)
            if m:
                symbols.append((m.group(1), "function", filepath, i, stripped[:120]))
                continue
            m = re.match(r"^class\s+(\w+)", stripped)
            if m:
                symbols.append((m.group(1), "class", filepath, i, stripped[:120]))
                continue
            # JS: function, const/let/var =, class
            m = re.match(r"(?:export\s+)?(?:async\s+)?function\s+(\w+)", stripped)
            if m:
                symbols.append((m.group(1), "function", filepath, i, stripped[:120]))
                continue
            m = re.match(r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=", stripped)
            if m:
                symbols.append((m.group(1), "variable", filepath, i, stripped[:120]))
                continue
            m = re.match(r"(?:export\s+)?class\s+(\w+)", stripped)
            if m:
                symbols.append((m.group(1), "class", filepath, i, stripped[:120]))
                continue

        if symbols:
            conn.executemany(
                "INSERT INTO symbols (name, kind, file, line, signature) "
                "VALUES (?, ?, ?, ?, ?)",
                symbols,
            )
            conn.commit()
        return len(symbols)

    def query(self, name: str) -> List[Dict]:
        """Query symbols by name (exact or substring). Sub-2ms on /dev/shm."""
        conn = self._get_conn()
        t0 = time.perf_counter()
        rows = conn.execute(
            "SELECT name, kind, file, line, signature FROM symbols "
            "WHERE name = ? OR name LIKE ? ORDER BY name",
            (name, f"%{name}%"),
        ).fetchall()
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return [
            {"name": r[0], "kind": r[1], "file": r[2], "line": r[3],
             "signature": r[4], "query_ms": round(elapsed_ms, 3)}
            for r in rows
        ]

    def clear(self):
        conn = self._get_conn()
        conn.execute("DELETE FROM symbols")
        conn.commit()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None


# ---------------------------------------------------------------------------
# 3. Scaffold Registry
# ---------------------------------------------------------------------------

_TEMPLATES_ROOT = _TYPES_ROOT / "templates"


class ScaffoldRegistry:
    """Pre-baked gold-standard project templates.

    @architect emits: "template: webgl_canvas_boilerplate.html, customize: [physics_loop]"
    @coder reads the template and applies surgical patches instead of
    hallucinating 300 lines of boilerplate.
    """

    def __init__(self, templates_root: Optional[Path] = None):
        self._root = templates_root or _TEMPLATES_ROOT

    def list_templates(self) -> List[Dict[str, str]]:
        """Return metadata for all available templates."""
        if not self._root.is_dir():
            return []
        templates = []
        for f in sorted(self._root.iterdir()):
            if f.is_file() and not f.name.startswith("."):
                content = f.read_text(encoding="utf-8", errors="replace")
                templates.append({
                    "name": f.name,
                    "path": str(f),
                    "size_bytes": len(content.encode()),
                    "first_line": content.splitlines()[0] if content else "",
                })
        return templates

    def get_template(self, name: str) -> Optional[str]:
        """Load full template content by name."""
        path = self._root / name
        if path.exists() and path.is_file():
            return path.read_text(encoding="utf-8")
        return None

    def get_summary(self, name: str) -> Optional[str]:
        """Load first N lines of a template (Tier-1 lightweight preview)."""
        content = self.get_template(name)
        if content is None:
            return None
        lines = content.splitlines()[:5]
        return "\n".join(lines)

    def scaffold_tokens(self) -> int:
        """Estimate token cost of listing all template names."""
        names = [t["name"] for t in self.list_templates()]
        text = " ".join(names)
        return max(1, len(text) // 4)


# ---------------------------------------------------------------------------
# Convenience API for @hermes/sdk integration
# ---------------------------------------------------------------------------

_resolver_instance: Optional[TypeSignatureResolver] = None
_scaffold_instance: Optional[ScaffoldRegistry] = None


def get_type_signature(query: str) -> Optional[str]:
    """Global convenience: resolve a type signature on demand."""
    global _resolver_instance
    if _resolver_instance is None:
        _resolver_instance = TypeSignatureResolver()
    return _resolver_instance.resolve(query)


def get_scaffold(name: str) -> Optional[str]:
    """Global convenience: load a scaffold template."""
    global _scaffold_instance
    if _scaffold_instance is None:
        _scaffold_instance = ScaffoldRegistry()
    return _scaffold_instance.get_template(name)


if __name__ == "__main__":
    r = TypeSignatureResolver()
    print(f"Categories: {r.list_categories()}")
    print(f"Symbols: {len(r.list_symbols())}")
    print(f"BufferGeometry: {r.resolve('BufferGeometry')}")
    s = ScaffoldRegistry()
    print(f"Templates: {[t['name'] for t in s.list_templates()]}")
