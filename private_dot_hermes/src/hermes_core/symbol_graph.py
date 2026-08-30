"""
High-Speed Whole-Codebase AST Symbol Indexer and Graph Engine (Issues #08 & #34)
================================================================================
Builds call hierarchies, inheritance trees, and cross-file references stored in
SQLite WAL mode to provide sub-2ms symbol lookups without LLM token overhead.

Features:
- Polyglot Tree-Sitter & Python AST symbol extraction (Python, JS, TS, Rust, Go, C/C++)
- Incremental AST Delta Caching via indexed_files table (mtime + SHA256)
- PathSpec-based exact .gitignore matching
- Unique constraint indexes preventing duplicate reference pollution
"""

import ast
import hashlib
import os
import re
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple

import pathspec


@dataclass
class ExtractedSymbol:
    id: str
    file_path: str
    name: str
    kind: str  # 'function', 'class', 'import', 'method', 'interface', 'struct'
    line_start: int
    line_end: int
    signature: str
    docstring: str = ""
    parent_symbol: str = ""


@dataclass
class ExtractedReference:
    source_file: str
    caller_symbol: str
    target_symbol: str
    ref_type: str  # 'call', 'inheritance', 'import', 'instantiation'


class SymbolGraph:
    """
    SQLite-backed symbol graph engine with WAL mode persistence.
    Supports RAMDisk (/dev/shm/symbol_graph.db), persistent (~/.hermes/symbol_graph.db),
    and in-memory (:memory:) storage paths.
    """

    def __init__(self, db_path: str = "/dev/shm/symbol_graph.db"):
        self.db_path = db_path
        self._local = threading.local()
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection with WAL mode enabled."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA foreign_keys=ON")
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_database(self):
        """Initialize database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Create symbols table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS symbols (
                id TEXT PRIMARY KEY,
                file_path TEXT NOT NULL,
                name TEXT NOT NULL,
                kind TEXT NOT NULL,
                line_start INTEGER NOT NULL,
                line_end INTEGER NOT NULL,
                signature TEXT DEFAULT '',
                docstring TEXT DEFAULT '',
                parent_symbol TEXT DEFAULT '',
                UNIQUE(file_path, name, line_start)
            )
        """)

        # Create symbol_references table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS symbol_references (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_file TEXT NOT NULL,
                caller_symbol TEXT NOT NULL,
                target_symbol TEXT NOT NULL,
                ref_type TEXT NOT NULL
            )
        """)

        # Create incremental delta cache table (Issue #34)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS indexed_files (
                filepath TEXT PRIMARY KEY,
                mtime REAL NOT NULL,
                sha256 TEXT NOT NULL,
                symbol_count INTEGER NOT NULL
            )
        """)

        # Create indexes for performance and deduplication (Issue #08)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbols_file ON symbols(file_path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbols_kind ON symbols(kind)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbols_parent ON symbols(parent_symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_refs_caller ON symbol_references(caller_symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_refs_target ON symbol_references(target_symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_refs_type ON symbol_references(ref_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_refs_source ON symbol_references(source_file)")
        # Deduplicate existing rows if any, then create unique index (Issue #08)
        cursor.execute("""
            DELETE FROM symbol_references WHERE id NOT IN (
                SELECT MIN(id) FROM symbol_references GROUP BY source_file, caller_symbol, target_symbol, ref_type
            )
        """)
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_symbol_ref_uniq ON symbol_references(source_file, caller_symbol, target_symbol, ref_type)")

        conn.commit()

    def index_source(self, file_path: str, content: str) -> int:
        """Parses AST, extracts definitions and references, writes to SQLite."""
        conn = self._get_connection()
        cursor = conn.cursor()

        file_path = os.path.abspath(file_path)
        suffix = Path(file_path).suffix.lower()

        # Clear existing symbols for this file
        cursor.execute("DELETE FROM symbols WHERE file_path = ?", (file_path,))
        cursor.execute("DELETE FROM symbol_references WHERE source_file = ?", (file_path,))

        symbols: List[ExtractedSymbol] = []
        references: List[ExtractedReference] = []

        if suffix in (".py", ".pyi") or not suffix:
            try:
                tree = ast.parse(content, filename=file_path)
                extractor = PythonSymbolExtractor(file_path, content)
                extractor.visit(tree)
                symbols = extractor.symbols
                references = extractor.references
            except SyntaxError:
                conn.commit()
                return 0
        else:
            # Polyglot Tree-Sitter symbol extraction (Issue #08)
            symbols, references = self._extract_tree_sitter_symbols(file_path, content, suffix)

        # Insert symbols
        symbol_count = 0
        for s in symbols:
            cursor.execute("""
                INSERT OR REPLACE INTO symbols 
                (id, file_path, name, kind, line_start, line_end, signature, docstring, parent_symbol)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (s.id, s.file_path, s.name, s.kind, s.line_start, s.line_end, s.signature, s.docstring, s.parent_symbol))
            symbol_count += 1

        # Insert references
        for r in references:
            cursor.execute("""
                INSERT OR IGNORE INTO symbol_references 
                (source_file, caller_symbol, target_symbol, ref_type)
                VALUES (?, ?, ?, ?)
            """, (r.source_file, r.caller_symbol, r.target_symbol, r.ref_type))

        conn.commit()
        return symbol_count

    def _extract_tree_sitter_symbols(self, file_path: str, content: str, suffix: str) -> Tuple[List[ExtractedSymbol], List[ExtractedReference]]:
        """Extract symbols from JS, TS, Rust, Go, C/C++ using Tree-Sitter."""
        symbols: List[ExtractedSymbol] = []
        references: List[ExtractedReference] = []

        lang_map = {
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "tsx",
            ".rs": "rust",
            ".go": "go",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".hpp": "cpp",
        }
        if suffix not in lang_map:
            return symbols, references

        try:
            import tree_sitter_language_pack as tslp
            parser = tslp.get_parser(lang_map[suffix])
            tree = parser.parse(content.encode("utf-8"))

            def traverse(node, parent_name=""):
                if node.type in ("function_declaration", "method_definition", "function_item", "function_definition"):
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        name = content[name_node.start_byte:name_node.end_byte]
                        sig_line = content.splitlines()[node.start_point[0]] if node.start_point[0] < len(content.splitlines()) else name
                        s_id = f"{file_path}:{name}:{node.start_point[0]+1}"
                        symbols.append(ExtractedSymbol(
                            id=s_id,
                            file_path=file_path,
                            name=name,
                            kind="function",
                            line_start=node.start_point[0] + 1,
                            line_end=node.end_point[0] + 1,
                            signature=sig_line.strip(),
                            parent_symbol=parent_name
                        ))
                elif node.type in ("class_declaration", "interface_declaration", "struct_item", "struct_spec"):
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        name = content[name_node.start_byte:name_node.end_byte]
                        sig_line = content.splitlines()[node.start_point[0]] if node.start_point[0] < len(content.splitlines()) else name
                        s_id = f"{file_path}:{name}:{node.start_point[0]+1}"
                        symbols.append(ExtractedSymbol(
                            id=s_id,
                            file_path=file_path,
                            name=name,
                            kind="class",
                            line_start=node.start_point[0] + 1,
                            line_end=node.end_point[0] + 1,
                            signature=sig_line.strip(),
                            parent_symbol=parent_name
                        ))
                        parent_name = name

                for child in node.children:
                    traverse(child, parent_name)

            traverse(tree.root_node)
        except Exception:
            pass

        return symbols, references

    def index_directory(self, root_dir: str, patterns: List[str] = None) -> Dict[str, int]:
        """Scans directory with incremental delta caching and pathspec filtering."""
        if patterns is None:
            patterns = ["*.py"]

        root_path = Path(root_dir).resolve()
        spec = self._load_gitignore_spec(root_path)

        stats = {
            "files_indexed": 0,
            "total_symbols": 0,
            "total_references": 0,
            "skipped_unchanged": 0,
            "errors": 0,
        }

        conn = self._get_connection()
        cursor = conn.cursor()

        for pattern in patterns:
            for file_path in root_path.rglob(pattern):
                if not file_path.is_file():
                    continue

                try:
                    rel_path = str(file_path.relative_to(root_path))
                except ValueError:
                    rel_path = str(file_path)

                if self._should_skip_spec(rel_path, spec):
                    continue

                abs_path = str(file_path.resolve())
                try:
                    st = file_path.stat()
                    mtime = st.st_mtime

                    # Check incremental cache (Issue #34)
                    cursor.execute("SELECT sha256, symbol_count FROM indexed_files WHERE filepath = ? AND mtime = ?", (abs_path, mtime))
                    row = cursor.fetchone()
                    if row is not None:
                        stats["files_indexed"] += 1
                        stats["total_symbols"] += row["symbol_count"]
                        stats["skipped_unchanged"] += 1
                        continue

                    # Read & compute hash
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    sha = hashlib.sha256(content.encode("utf-8")).hexdigest()

                    # Check hash match
                    cursor.execute("SELECT symbol_count FROM indexed_files WHERE filepath = ? AND sha256 = ?", (abs_path, sha))
                    row_sha = cursor.fetchone()
                    if row_sha is not None:
                        cursor.execute("UPDATE indexed_files SET mtime = ? WHERE filepath = ?", (mtime, abs_path))
                        conn.commit()
                        stats["files_indexed"] += 1
                        stats["total_symbols"] += row_sha["symbol_count"]
                        stats["skipped_unchanged"] += 1
                        continue

                    # Re-index changed file
                    symbol_count = self.index_source(abs_path, content)
                    cursor.execute("""
                        INSERT OR REPLACE INTO indexed_files (filepath, mtime, sha256, symbol_count)
                        VALUES (?, ?, ?, ?)
                    """, (abs_path, mtime, sha, symbol_count))
                    conn.commit()

                    stats["files_indexed"] += 1
                    stats["total_symbols"] += symbol_count
                except Exception:
                    stats["errors"] += 1

        cursor.execute("SELECT COUNT(*) as count FROM symbol_references")
        stats["total_references"] = cursor.fetchone()["count"]

        return stats

    def _load_gitignore_spec(self, root_path: Path) -> pathspec.PathSpec:
        """Load .gitignore lines into a PathSpec matcher (Issue #08)."""
        lines = [
            ".git", ".git/", ".venv", ".venv/", "__pycache__", "__pycache__/",
            "node_modules", "node_modules/", "*.pyc", ".pytest_cache", ".pytest_cache/",
            ".hermes_session", ".scratch"
        ]
        gitignore_path = root_path / ".gitignore"
        if gitignore_path.exists():
            try:
                for line in gitignore_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#"):
                        lines.append(line)
            except Exception:
                pass
        return pathspec.PathSpec.from_lines("gitignore", lines)

    def _should_skip_spec(self, rel_path: str, spec: pathspec.PathSpec) -> bool:
        """Check if relative path matches gitignore spec."""
        if any(part in (".git", ".venv", "__pycache__", "node_modules", ".scratch") for part in Path(rel_path).parts):
            return True
        return spec.match_file(rel_path)

    def find_symbol(self, name: str) -> List[Dict]:
        """Fast indexed lookup by symbol name."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, file_path, name, kind, line_start, line_end, signature, docstring, parent_symbol
            FROM symbols WHERE name = ?
            ORDER BY file_path, line_start
        """, (name,))

        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row["id"],
                "file_path": row["file_path"],
                "name": row["name"],
                "kind": row["kind"],
                "line_start": row["line_start"],
                "line_end": row["line_end"],
                "signature": row["signature"],
                "docstring": row["docstring"],
                "parent_symbol": row["parent_symbol"]
            })
        return results

    def get_file_outline(self, file_path: str) -> List[Dict]:
        """Returns hierarchically structured outline of symbols defined in a file."""
        conn = self._get_connection()
        cursor = conn.cursor()
        file_path = os.path.abspath(file_path)

        cursor.execute("""
            SELECT id, name, kind, line_start, line_end, signature, docstring, parent_symbol
            FROM symbols
            WHERE file_path = ? AND kind != 'import'
            ORDER BY line_start ASC
        """, (file_path,))

        all_syms = [dict(row) for row in cursor.fetchall()]

        # Top level symbols (parent_symbol == '')
        root_items = []
        children_by_parent = {}
        for s in all_syms:
            parent = s.get("parent_symbol")
            if parent:
                children_by_parent.setdefault(parent, []).append(s)
            else:
                root_items.append(s)

        for item in root_items:
            item["children"] = children_by_parent.get(item["name"], [])

        return root_items

    def get_callers(self, symbol_name: str) -> List[Dict]:
        """Returns all functions/classes that call or reference this symbol."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT sr.source_file, sr.caller_symbol, sr.ref_type,
                   s.kind as caller_kind, s.line_start as caller_line
            FROM symbol_references sr
            LEFT JOIN symbols s ON (s.name = sr.caller_symbol OR s.name = SUBSTR(sr.caller_symbol, INSTR(sr.caller_symbol, '.') + 1)) AND s.file_path = sr.source_file
            WHERE sr.target_symbol = ? OR sr.target_symbol LIKE '%.' || ?
        """, (symbol_name, symbol_name))

        results = []
        for row in cursor.fetchall():
            caller_sym = row["caller_symbol"]
            results.append({
                "source_file": row["source_file"],
                "caller_symbol": caller_sym,
                "caller_kind": row["caller_kind"],
                "caller_line": row["caller_line"],
                "ref_type": row["ref_type"]
            })
            if "." in caller_sym:
                short_name = caller_sym.split(".")[-1]
                results.append({
                    "source_file": row["source_file"],
                    "caller_symbol": short_name,
                    "caller_kind": row["caller_kind"],
                    "caller_line": row["caller_line"],
                    "ref_type": row["ref_type"]
                })
        return results

    def get_callees(self, symbol_name: str) -> List[str]:
        """Returns all symbol name strings called by the given symbol."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT target_symbol FROM symbol_references
            WHERE (caller_symbol = ? OR caller_symbol LIKE '%.' || ?) AND ref_type = 'call'
        """, (symbol_name, symbol_name))

        return [row["target_symbol"] for row in cursor.fetchall()]

    def get_inheritance_tree(self, class_name: str) -> Dict:
        """Returns inheritance hierarchy for a class."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT file_path FROM symbols WHERE name = ? AND kind = 'class' LIMIT 1
        """, (class_name,))
        row = cursor.fetchone()
        if not row:
            return {"class": class_name, "file_path": "", "parents": [], "children": []}

        file_path = row["file_path"]

        cursor.execute("""
            SELECT DISTINCT target_symbol FROM symbol_references
            WHERE caller_symbol = ? AND ref_type = 'inheritance'
        """, (class_name,))

        parents = []
        for row in cursor.fetchall():
            parent_name = row["target_symbol"]
            cursor.execute("""
                SELECT name, file_path FROM symbols WHERE name = ? AND kind = 'class'
            """, (parent_name,))
            parent_row = cursor.fetchone()
            if parent_row:
                parents.append({"name": parent_row["name"], "file_path": parent_row["file_path"]})
            else:
                parents.append({"name": parent_name, "file_path": ""})

        cursor.execute("""
            SELECT DISTINCT caller_symbol FROM symbol_references
            WHERE target_symbol = ? AND ref_type = 'inheritance'
        """, (class_name,))

        children = []
        for row in cursor.fetchall():
            child_name = row["caller_symbol"]
            cursor.execute("""
                SELECT name, file_path FROM symbols WHERE name = ? AND kind = 'class'
            """, (child_name,))
            child_row = cursor.fetchone()
            if child_row:
                children.append({"name": child_row["name"], "file_path": child_row["file_path"]})

        return {
            "class": class_name,
            "file_path": file_path,
            "parents": parents,
            "children": children
        }

    def get_class_hierarchy(self, class_name: str) -> Dict[str, Any]:
        """Convenience alias for inheritance hierarchy."""
        return self.get_inheritance_tree(class_name)

    def export_symbol_graph_summary(self) -> Dict:
        """Total symbols, files indexed, reference count."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM symbols")
        total_symbols = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(DISTINCT file_path) as count FROM symbols")
        files_indexed = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM symbol_references")
        total_references = cursor.fetchone()["count"]

        cursor.execute("SELECT kind, COUNT(*) as count FROM symbols GROUP BY kind")
        by_kind = {row["kind"]: row["count"] for row in cursor.fetchall()}

        return {
            "total_symbols": total_symbols,
            "files_indexed": files_indexed,
            "total_references": total_references,
            "symbols_by_kind": by_kind
        }

    def clear(self):
        """Clear all data."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM symbols")
        cursor.execute("DELETE FROM symbol_references")
        cursor.execute("DELETE FROM indexed_files")
        conn.commit()

    def close(self):
        """Close the database connection."""
        if hasattr(self._local, "conn") and self._local.conn is not None:
            self._local.conn.close()
            self._local.conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class PythonSymbolExtractor(ast.NodeVisitor):
    """AST visitor that extracts symbols and references from Python code."""

    def __init__(self, file_path: str, content: str):
        self.file_path = file_path
        self.content = content
        self.lines = content.splitlines()
        self.symbols: List[ExtractedSymbol] = []
        self.references: List[ExtractedReference] = []
        self._symbol_stack: List[str] = []
        self._current_class: Optional[str] = None
        self._imported_names: Dict[str, str] = {}
        self._current_function: Optional[str] = None
        self._visited_imports: Set[int] = set()

    def _get_symbol_id(self, node: ast.AST) -> str:
        name = getattr(node, "name", "unknown")
        return f"{self.file_path}:{name}:{node.lineno}"

    def _get_signature(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
        args = []
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            args.append(arg_str)

        if node.args.vararg:
            args.append(f"*{node.args.vararg.arg}")
        if node.args.kwarg:
            args.append(f"**{node.args.kwarg.arg}")

        sig = f"({', '.join(args)})"
        if node.returns:
            sig += f" -> {ast.unparse(node.returns)}"
        return sig

    def _get_class_signature(self, node: ast.ClassDef) -> str:
        bases = []
        for base in node.bases:
            bases.append(ast.unparse(base))
        if bases:
            return f"({', '.join(bases)})"
        return ""

    def _get_docstring(self, node: ast.AST) -> str:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef, ast.Module)):
            docstring = ast.get_docstring(node)
            return docstring if docstring else ""
        return ""

    def _get_full_caller_name(self) -> str:
        if self._symbol_stack:
            return ".".join(self._symbol_stack)
        return self._current_function or ""

    def _add_symbol(self, node: ast.AST, name: str, kind: str, signature: str, parent: str = ""):
        symbol = ExtractedSymbol(
            id=self._get_symbol_id(node),
            file_path=self.file_path,
            name=name,
            kind=kind,
            line_start=node.lineno,
            line_end=getattr(node, "end_lineno", node.lineno),
            signature=signature,
            docstring=self._get_docstring(node),
            parent_symbol=parent
        )
        self.symbols.append(symbol)

    def _add_reference(self, caller: str, target: str, ref_type: str):
        if caller and target and caller != target:
            self.references.append(ExtractedReference(
                source_file=self.file_path,
                caller_symbol=caller,
                target_symbol=target,
                ref_type=ref_type
            ))

    def visit_Module(self, node: ast.Module):
        for stmt in node.body:
            if isinstance(stmt, (ast.Import, ast.ImportFrom)):
                self.visit(stmt)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        if node.lineno in self._visited_imports:
            return
        self._visited_imports.add(node.lineno)
        for alias in node.names:
            name = alias.asname or alias.name
            self._imported_names[name] = alias.name
            import_id = f"{self.file_path}:import:{name}:{node.lineno}"
            sig = f"import {alias.name} as {alias.asname}" if alias.asname else f"import {alias.name}"
            self.symbols.append(ExtractedSymbol(
                id=import_id,
                file_path=self.file_path,
                name=name,
                kind="import",
                line_start=node.lineno,
                line_end=getattr(node, "end_lineno", node.lineno),
                signature=sig,
                docstring="",
                parent_symbol=""
            ))

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.lineno in self._visited_imports:
            return
        self._visited_imports.add(node.lineno)
        module = node.module or ""
        for alias in node.names:
            name = alias.asname or alias.name
            full_name = f"{module}.{alias.name}" if module else alias.name
            self._imported_names[name] = full_name
            import_id = f"{self.file_path}:import:{name}:{node.lineno}"
            sig = f"from {module} import {alias.name} as {alias.asname}" if alias.asname else f"from {module} import {alias.name}"
            self.symbols.append(ExtractedSymbol(
                id=import_id,
                file_path=self.file_path,
                name=name,
                kind="import",
                line_start=node.lineno,
                line_end=getattr(node, "end_lineno", node.lineno),
                signature=sig,
                docstring="",
                parent_symbol=""
            ))

    def visit_ClassDef(self, node: ast.ClassDef):
        parent = self._symbol_stack[-1] if self._symbol_stack else ""
        signature = self._get_class_signature(node)
        self._add_symbol(node, node.name, "class", signature, parent)

        for base in node.bases:
            base_name = ast.unparse(base)
            self._add_reference(node.name, base_name, "inheritance")

        self._symbol_stack.append(node.name)
        old_class = self._current_class
        self._current_class = node.name
        self.generic_visit(node)
        self._current_class = old_class
        self._symbol_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        parent = self._symbol_stack[-1] if self._symbol_stack else ""
        signature = self._get_signature(node)
        self._add_symbol(node, node.name, "function", signature, parent)

        self._symbol_stack.append(node.name)
        old_func = self._current_function
        self._current_function = node.name
        self.generic_visit(node)
        self._current_function = old_func
        self._symbol_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        parent = self._symbol_stack[-1] if self._symbol_stack else ""
        signature = self._get_signature(node)
        self._add_symbol(node, node.name, "function", signature, parent)

        self._symbol_stack.append(node.name)
        old_func = self._current_function
        self._current_function = node.name
        self.generic_visit(node)
        self._current_function = old_func
        self._symbol_stack.pop()

    def visit_Assign(self, node: ast.Assign):
        target_name = ""
        if node.targets and isinstance(node.targets[0], ast.Name):
            target_name = node.targets[0].id
            self._last_assigned_var = target_name
        self.generic_visit(node)
        self._last_assigned_var = None

    def visit_Call(self, node: ast.Call):
        caller = self._get_full_caller_name()
        if not caller:
            if getattr(self, "_last_assigned_var", None):
                caller = self._last_assigned_var
            elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                caller = node.func.value.id

        if caller:
            if isinstance(node.func, ast.Name):
                target = node.func.id
                target = self._imported_names.get(target, target)
                self._add_reference(caller, target, "call")
            elif isinstance(node.func, ast.Attribute):
                target = node.func.attr
                self._add_reference(caller, target, "call")

        self.generic_visit(node)

    def visit_Await(self, node: ast.Await):
        caller = self._get_full_caller_name()
        if caller and isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name):
                target = node.value.func.id
                target = self._imported_names.get(target, target)
                self._add_reference(caller, target, "call")
            elif isinstance(node.value.func, ast.Attribute):
                target = node.value.func.attr
                self._add_reference(caller, target, "call")

        self.generic_visit(node)


def create_ramdisk_graph() -> SymbolGraph:
    return SymbolGraph("/dev/shm/symbol_graph.db")


def create_persistent_graph() -> SymbolGraph:
    db_path = Path.home() / ".hermes" / "symbol_graph.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return SymbolGraph(str(db_path))


def create_memory_graph() -> SymbolGraph:
    return SymbolGraph(":memory:")


__all__ = [
    "SymbolGraph",
    "create_ramdisk_graph",
    "create_persistent_graph",
    "create_memory_graph",
]
