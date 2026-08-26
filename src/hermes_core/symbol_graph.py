"""
High-Speed Whole-Codebase AST Symbol Indexer and Graph Engine
==============================================================
Builds call hierarchies, inheritance trees, and cross-file references stored in
RAMDisk (/dev/shm/symbol_graph.db or in-memory) to provide sub-2ms symbol
lookups without LLM token overhead.
"""

import ast
import os
import re
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from fnmatch import fnmatch


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
        if not hasattr(self._local, 'conn') or self._local.conn is None:
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
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbols_file ON symbols(file_path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbols_kind ON symbols(kind)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbols_parent ON symbols(parent_symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_refs_caller ON symbol_references(caller_symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_refs_target ON symbol_references(target_symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_refs_type ON symbol_references(ref_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_refs_source ON symbol_references(source_file)")
        
        conn.commit()
    
    def index_source(self, file_path: str, content: str) -> int:
        """
        Parses AST (Python ast module), extracts definitions and references,
        writes to SQLite, returns indexed symbol count.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Normalize file path
        file_path = os.path.abspath(file_path)
        
        # Clear existing symbols for this file
        cursor.execute("DELETE FROM symbols WHERE file_path = ?", (file_path,))
        cursor.execute("DELETE FROM symbol_references WHERE source_file = ?", (file_path,))
        
        try:
            tree = ast.parse(content, filename=file_path)
        except SyntaxError:
            # If parsing fails, still commit the deletion and return 0
            conn.commit()
            return 0
        
        # Extract symbols and references
        extractor = PythonSymbolExtractor(file_path, content)
        extractor.visit(tree)
        
        # Insert symbols
        symbol_count = 0
        for symbol in extractor.symbols:
            cursor.execute("""
                INSERT OR REPLACE INTO symbols 
                (id, file_path, name, kind, line_start, line_end, signature, docstring, parent_symbol)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol.id,
                symbol.file_path,
                symbol.name,
                symbol.kind,
                symbol.line_start,
                symbol.line_end,
                symbol.signature,
                symbol.docstring,
                symbol.parent_symbol
            ))
            symbol_count += 1
        
        # Insert references
        for ref in extractor.references:
            cursor.execute("""
                INSERT INTO symbol_references 
                (source_file, caller_symbol, target_symbol, ref_type)
                VALUES (?, ?, ?, ?)
            """, (
                ref.source_file,
                ref.caller_symbol,
                ref.target_symbol,
                ref.ref_type
            ))
        
        conn.commit()
        return symbol_count
    
    def index_directory(self, root_dir: str, patterns: List[str] = None) -> Dict[str, int]:
        """
        Scans directory, skips gitignored/.venv paths, indexes files,
        returns summary statistics.
        """
        if patterns is None:
            patterns = ["*.py"]
        
        root_path = Path(root_dir).resolve()
        
        # Load gitignore patterns
        gitignore_patterns = self._load_gitignore(root_path)
        
        stats = {
            'files_indexed': 0,
            'total_symbols': 0,
            'total_references': 0,
            'errors': 0
        }
        
        for pattern in patterns:
            for file_path in root_path.rglob(pattern):
                # Skip excluded directories
                if self._should_skip(file_path, root_path, gitignore_patterns):
                    continue
                
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    symbol_count = self.index_source(str(file_path), content)
                    stats['files_indexed'] += 1
                    stats['total_symbols'] += symbol_count
                except Exception:
                    stats['errors'] += 1
        
        # Get reference count after indexing
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM symbol_references")
        stats['total_references'] = cursor.fetchone()['count']
        
        return stats
    
    def _load_gitignore(self, root_path: Path) -> List[str]:
        """Load .gitignore patterns."""
        gitignore_path = root_path / ".gitignore"
        patterns = []
        if gitignore_path.exists():
            for line in gitignore_path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith('#'):
                    patterns.append(line)
        # Always exclude common patterns
        patterns.extend(['.venv', '__pycache__', '.git', 'node_modules', '*.pyc', '.pytest_cache'])
        return patterns
    
    def _should_skip(self, file_path: Path, root_path: Path, gitignore_patterns: List[str]) -> bool:
        """Check if file should be skipped."""
        rel_path = file_path.relative_to(root_path)
        
        for pattern in gitignore_patterns:
            if fnmatch(str(rel_path), pattern) or fnmatch(file_path.name, pattern):
                return True
            # Check if any parent directory matches the pattern
            for parent in rel_path.parents:
                if fnmatch(str(parent), pattern) or fnmatch(parent.name, pattern):
                    return True
        return False
    
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
                'id': row['id'],
                'file_path': row['file_path'],
                'name': row['name'],
                'kind': row['kind'],
                'line_start': row['line_start'],
                'line_end': row['line_end'],
                'signature': row['signature'],
                'docstring': row['docstring'],
                'parent_symbol': row['parent_symbol']
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
            parent = s.get('parent_symbol')
            if parent:
                children_by_parent.setdefault(parent, []).append(s)
            else:
                root_items.append(s)

        for item in root_items:
            item['children'] = children_by_parent.get(item['name'], [])

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
            caller_sym = row['caller_symbol']
            results.append({
                'source_file': row['source_file'],
                'caller_symbol': caller_sym,
                'caller_kind': row['caller_kind'],
                'caller_line': row['caller_line'],
                'ref_type': row['ref_type']
            })
            # Also provide the unqualified caller symbol if it is class-qualified
            if '.' in caller_sym:
                short_name = caller_sym.split('.')[-1]
                results.append({
                    'source_file': row['source_file'],
                    'caller_symbol': short_name,
                    'caller_kind': row['caller_kind'],
                    'caller_line': row['caller_line'],
                    'ref_type': row['ref_type']
                })
        
        return results
    
    def get_callees(self, symbol_name: str) -> List[str]:
        """Returns all symbols called by the given symbol."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT target_symbol FROM symbol_references
            WHERE (caller_symbol = ? OR caller_symbol LIKE '%.' || ?) AND ref_type = 'call'
        """, (symbol_name, symbol_name))
        
        return [row['target_symbol'] for row in cursor.fetchall()]
    
    def get_inheritance_tree(self, class_name: str) -> Dict:
        """Returns inheritance hierarchy for a class."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Find the class symbol
        cursor.execute("""
            SELECT file_path FROM symbols WHERE name = ? AND kind = 'class' LIMIT 1
        """, (class_name,))
        row = cursor.fetchone()
        if not row:
            return {'class': class_name, 'file_path': '', 'parents': [], 'children': []}
        
        file_path = row['file_path']
        
        # Get direct parent classes: references WHERE caller_symbol = class_name AND ref_type = 'inheritance'
        cursor.execute("""
            SELECT DISTINCT target_symbol FROM symbol_references
            WHERE caller_symbol = ? AND ref_type = 'inheritance'
        """, (class_name,))
        
        parents = []
        for row in cursor.fetchall():
            parent_name = row['target_symbol']
            cursor.execute("""
                SELECT name, file_path FROM symbols WHERE name = ? AND kind = 'class'
            """, (parent_name,))
            parent_row = cursor.fetchone()
            if parent_row:
                parents.append({'name': parent_row['name'], 'file_path': parent_row['file_path']})
            else:
                parents.append({'name': parent_name, 'file_path': ''})
        
        # Get derived subclasses: references WHERE target_symbol = class_name AND ref_type = 'inheritance'
        cursor.execute("""
            SELECT DISTINCT caller_symbol FROM symbol_references
            WHERE target_symbol = ? AND ref_type = 'inheritance'
        """, (class_name,))
        
        children = []
        for row in cursor.fetchall():
            child_name = row['caller_symbol']
            cursor.execute("""
                SELECT name, file_path FROM symbols WHERE name = ? AND kind = 'class'
            """, (child_name,))
            child_row = cursor.fetchone()
            if child_row:
                children.append({'name': child_row['name'], 'file_path': child_row['file_path']})
        
        return {
            'class': class_name,
            'file_path': file_path,
            'parents': parents,
            'children': children
        }
    
    def export_symbol_graph_summary(self) -> Dict:
        """Total symbols, files indexed, reference count."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM symbols")
        total_symbols = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(DISTINCT file_path) as count FROM symbols")
        files_indexed = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM symbol_references")
        total_references = cursor.fetchone()['count']
        
        cursor.execute("SELECT kind, COUNT(*) as count FROM symbols GROUP BY kind")
        by_kind = {row['kind']: row['count'] for row in cursor.fetchall()}
        
        return {
            'total_symbols': total_symbols,
            'files_indexed': files_indexed,
            'total_references': total_references,
            'symbols_by_kind': by_kind
        }
    
    def clear(self):
        """Clear all data."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM symbols")
        cursor.execute("DELETE FROM symbol_references")
        conn.commit()
    
    def close(self):
        """Close the database connection."""
        if hasattr(self._local, 'conn') and self._local.conn is not None:
            self._local.conn.close()
            self._local.conn = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# =============================================================================
# Python AST Symbol Extractor
# =============================================================================

@dataclass
class ExtractedSymbol:
    id: str
    file_path: str
    name: str
    kind: str
    line_start: int
    line_end: int
    signature: str
    docstring: str
    parent_symbol: str


@dataclass
class ExtractedReference:
    source_file: str
    caller_symbol: str
    target_symbol: str
    ref_type: str  # call, inheritance, import, instantiation


class PythonSymbolExtractor(ast.NodeVisitor):
    """Extracts symbols and references from Python AST."""
    
    def __init__(self, file_path: str, content: str):
        self.file_path = file_path
        self.content = content
        self.lines = content.splitlines()
        self.symbols: List[ExtractedSymbol] = []
        self.references: List[ExtractedReference] = []
        self._symbol_stack: List[str] = []  # Track parent symbol names for nesting
        self._current_class: Optional[str] = None
        self._imported_names: Dict[str, str] = {}  # alias -> full name
        self._current_function: Optional[str] = None  # Current function name
        self._visited_imports: Set[int] = set()  # Track visited import line numbers to avoid double-visit
    
    def _get_symbol_id(self, node: ast.AST) -> str:
        """Generate unique symbol ID."""
        name = getattr(node, 'name', 'unknown')
        return f"{self.file_path}:{name}:{node.lineno}"
    
    def _get_signature(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
        """Extract function signature as string."""
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
        """Extract class signature (base classes)."""
        bases = []
        for base in node.bases:
            bases.append(ast.unparse(base))
        if bases:
            return f"({', '.join(bases)})"
        return ""
    
    def _get_docstring(self, node: ast.AST) -> str:
        """Extract docstring from node."""
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef, ast.Module)):
            docstring = ast.get_docstring(node)
            return docstring if docstring else ""
        return ""
    
    def _get_full_caller_name(self) -> str:
        """Get the full caller name including class context."""
        if self._symbol_stack:
            return ".".join(self._symbol_stack)
        return self._current_function or ""
    
    def _add_symbol(self, node: ast.AST, name: str, kind: str, signature: str, parent: str = ""):
        """Add a symbol to the list."""
        symbol = ExtractedSymbol(
            id=self._get_symbol_id(node),
            file_path=self.file_path,
            name=name,
            kind=kind,
            line_start=node.lineno,
            line_end=getattr(node, 'end_lineno', node.lineno),
            signature=signature,
            docstring=self._get_docstring(node),
            parent_symbol=parent
        )
        self.symbols.append(symbol)
    
    def _add_reference(self, caller: str, target: str, ref_type: str):
        """Add a reference."""
        if caller and target and caller != target:
            self.references.append(ExtractedReference(
                source_file=self.file_path,
                caller_symbol=caller,
                target_symbol=target,
                ref_type=ref_type
            ))
    
    def visit_Module(self, node: ast.Module):
        """Process module-level imports first, then generic visit."""
        # Process imports first to populate _imported_names
        for stmt in node.body:
            if isinstance(stmt, (ast.Import, ast.ImportFrom)):
                self.visit(stmt)
        # Then visit the rest
        self.generic_visit(node)
    
    def visit_Import(self, node: ast.Import):
        """Handle import statements - only index the imported names as symbols."""
        # Avoid double-visiting
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
                kind='import',
                line_start=node.lineno,
                line_end=getattr(node, 'end_lineno', node.lineno),
                signature=sig,
                docstring="",
                parent_symbol=""
            ))
        # Don't call generic_visit - we handled it
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Handle from ... import statements - only index the imported names."""
        # Avoid double-visiting
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
                kind='import',
                line_start=node.lineno,
                line_end=getattr(node, 'end_lineno', node.lineno),
                signature=sig,
                docstring="",
                parent_symbol=""
            ))
        # Don't call generic_visit - we handled it
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Handle class definitions."""
        # Parent is the current enclosing class/function (before pushing this class)
        parent = self._symbol_stack[-1] if self._symbol_stack else ""
        signature = self._get_class_signature(node)
        self._add_symbol(node, node.name, 'class', signature, parent)
        
        # Track base class references - caller is the derived class, target is the base
        for base in node.bases:
            base_name = ast.unparse(base)
            self._add_reference(node.name, base_name, 'inheritance')
        
        # Push this class to stack for nested definitions
        self._symbol_stack.append(node.name)
        old_class = self._current_class
        self._current_class = node.name
        self.generic_visit(node)
        self._current_class = old_class
        self._symbol_stack.pop()
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Handle function definitions."""
        # Parent is the current enclosing class/function
        parent = self._symbol_stack[-1] if self._symbol_stack else ""
        signature = self._get_signature(node)
        self._add_symbol(node, node.name, 'function', signature, parent)
        
        # Push this function to stack for nested definitions
        self._symbol_stack.append(node.name)
        old_func = self._current_function
        self._current_function = node.name
        self.generic_visit(node)
        self._current_function = old_func
        self._symbol_stack.pop()
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Handle async function definitions."""
        parent = self._symbol_stack[-1] if self._symbol_stack else ""
        signature = self._get_signature(node)
        self._add_symbol(node, node.name, 'function', signature, parent)
        
        self._symbol_stack.append(node.name)
        old_func = self._current_function
        self._current_function = node.name
        self.generic_visit(node)
        self._current_function = old_func
        self._symbol_stack.pop()
    
    def visit_Assign(self, node: ast.Assign):
        """Handle variable assignment (instantiations or expressions)."""
        target_name = ""
        if node.targets and isinstance(node.targets[0], ast.Name):
            target_name = node.targets[0].id
            self._last_assigned_var = target_name
        self.generic_visit(node)
        self._last_assigned_var = None

    def visit_Call(self, node: ast.Call):
        """Handle function/method calls."""
        # Determine caller (current function context with class or top-level target)
        caller = self._get_full_caller_name()
        if not caller:
            if getattr(self, '_last_assigned_var', None):
                caller = self._last_assigned_var
            elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                caller = node.func.value.id
        
        if caller:
            # Try to get the called function name
            if isinstance(node.func, ast.Name):
                target = node.func.id
                # Resolve import aliases
                target = self._imported_names.get(target, target)
                self._add_reference(caller, target, 'call')
            elif isinstance(node.func, ast.Attribute):
                # Method call like obj.method() or Class.method()
                target = node.func.attr
                self._add_reference(caller, target, 'call')
        
        self.generic_visit(node)
    
    def visit_Await(self, node: ast.Await):
        """Handle await expressions (treated as calls)."""
        caller = self._get_full_caller_name()
        
        if caller and isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name):
                target = node.value.func.id
                target = self._imported_names.get(target, target)
                self._add_reference(caller, target, 'call')
            elif isinstance(node.value.func, ast.Attribute):
                target = node.value.func.attr
                self._add_reference(caller, target, 'call')
        
        self.generic_visit(node)


# =============================================================================
# Convenience Functions
# =============================================================================

def create_ramdisk_graph() -> SymbolGraph:
    """Create a SymbolGraph with RAMDisk storage."""
    return SymbolGraph("/dev/shm/symbol_graph.db")


def create_persistent_graph() -> SymbolGraph:
    """Create a SymbolGraph with persistent storage at ~/.hermes/symbol_graph.db"""
    from pathlib import Path
    db_path = Path.home() / ".hermes" / "symbol_graph.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return SymbolGraph(str(db_path))


def create_memory_graph() -> SymbolGraph:
    """Create a SymbolGraph with in-memory storage."""
    return SymbolGraph(":memory:")


# Export for external use
__all__ = [
    'SymbolGraph',
    'create_ramdisk_graph',
    'create_persistent_graph',
    'create_memory_graph',
]
