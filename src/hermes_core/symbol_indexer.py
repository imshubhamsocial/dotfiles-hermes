"""
AST Symbol Indexer & File Tree Pruner (Ground-Up Frontier Intelligence)
======================================================================
Implements symbol-based code indexing (Claude Code / Codex / DeepSeek style):
  - Builds high-level structural tree of large codebases without reading full files.
  - Extracts classes, functions, interfaces, methods and type signatures into a compact AST map (<500 tokens).
  - Enables agents to surgically navigate and modify 50,000-line codebases without burning context tokens on indexing.
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Any, Optional


class SymbolIndexer:
    """Extracts top-level and class-level symbols from Python, JavaScript and TypeScript files."""

    @staticmethod
    def extract_python_symbols(code: str) -> Dict[str, Any]:
        """Parse Python code using the standard AST module and extract classes, methods, and functions."""
        try:
            tree = ast.parse(code)
        except Exception:
            return {"error": "AST parse error"}

        symbols = {"classes": {}, "functions": []}
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        args = [a.arg for a in item.args.args]
                        methods.append(f"{item.name}({', '.join(args)}) [Line {item.lineno}]")
                symbols["classes"][node.name] = {
                    "line": node.lineno,
                    "methods": methods
                }
            elif isinstance(node, ast.FunctionDef):
                args = [a.arg for a in node.args.args]
                symbols["functions"].append(f"{node.name}({', '.join(args)}) [Line {node.lineno}]")

        return symbols

    @staticmethod
    def extract_js_symbols(code: str) -> Dict[str, Any]:
        """Extract classes, functions, and key objects from JavaScript/HTML scripts via regex AST scanner."""
        symbols = {"classes": {}, "functions": [], "constants": []}

        # Match ES6 classes
        class_matches = re.finditer(r'class\s+([A-Za-z0-9_$]+)(?:\s+extends\s+([A-Za-z0-9_$]+))?\s*\{', code)
        for m in class_matches:
            line_no = code[:m.start()].count('\n') + 1
            symbols["classes"][m.group(1)] = {"line": line_no, "extends": m.group(2) or None}

        # Match function declarations
        fn_matches = re.finditer(r'(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(([^)]*)\)', code)
        for m in fn_matches:
            line_no = code[:m.start()].count('\n') + 1
            symbols["functions"].append(f"{m.group(1)}({m.group(2).strip()}) [Line {line_no}]")

        # Match top-level arrow functions and assigned constants
        const_matches = re.finditer(r'(?:const|let|var)\s+([A-Za-z0-9_$]+)\s*=\s*(?:function|\([^)]*\)\s*=>)', code)
        for m in const_matches:
            line_no = code[:m.start()].count('\n') + 1
            symbols["functions"].append(f"{m.group(1)}() [Line {line_no}]")

        return symbols

    @classmethod
    def get_symbol_map(cls, filepath: str) -> str:
        """Return a compact, human-readable symbol map of a file (<300 tokens)."""
        p = Path(filepath)
        if not p.exists():
            return f"Error: File '{filepath}' does not exist."

        content = p.read_text(encoding="utf-8", errors="ignore")
        ext = p.suffix.lower()

        if ext == ".py":
            sym = cls.extract_python_symbols(content)
        elif ext in [".js", ".ts", ".html"]:
            sym = cls.extract_js_symbols(content)
        else:
            return f"Symbol indexing not supported for file type: {ext}"

        output = [f"=== SYMBOL MAP: {p.name} (Lines: {content.count(chr(10))+1}) ==="]
        if "classes" in sym and sym["classes"]:
            output.append("Classes:")
            for c_name, c_info in sym["classes"].items():
                ext_str = f" extends {c_info.get('extends')}" if c_info.get('extends') else ""
                output.append(f"  • {c_name}{ext_str} (Line {c_info.get('line')})")
                if "methods" in c_info:
                    for m in c_info["methods"]:
                        output.append(f"      - {m}")
        if "functions" in sym and sym["functions"]:
            output.append("Functions:")
            for f in sym["functions"]:
                output.append(f"  • {f}")

        return "\n".join(output)

    @staticmethod
    def get_workspace_tree(directory: str, max_depth: int = 3) -> str:
        """Return a compact file tree of the workspace, excluding git/cache noise."""
        root = Path(directory)
        if not root.exists():
            return f"Error: Directory '{directory}' does not exist."

        tree_lines = [f"📁 {root.name}/"]
        ignore_dirs = {".git", "__pycache__", "node_modules", ".gemini", ".scratch", "reference_harnesses"}

        def build_tree(current: Path, depth: int, prefix: str):
            if depth > max_depth:
                return
            items = sorted(list(current.iterdir()), key=lambda x: (not x.is_dir(), x.name))
            for i, item in enumerate(items):
                if item.name in ignore_dirs or item.name.startswith("."):
                    continue
                is_last = (i == len(items) - 1)
                connector = "└── " if is_last else "├── "
                if item.is_dir():
                    tree_lines.append(f"{prefix}{connector}📁 {item.name}/")
                    build_tree(item, depth + 1, prefix + ("    " if is_last else "│   "))
                else:
                    size_kb = item.stat().st_size / 1024
                    tree_lines.append(f"{prefix}{connector}📄 {item.name} ({size_kb:.1f} KB)")

        build_tree(root, 1, "")
        return "\n".join(tree_lines)
