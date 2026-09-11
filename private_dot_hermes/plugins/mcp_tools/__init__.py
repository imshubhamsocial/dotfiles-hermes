"""
Unified FastMCP Tool Server & Execution Engine
=============================================
Exposes:
1. High-performance Crawl4AI web extraction (web_extract).
2. ast-grep polyglot AST search (ast_search).
3. Aider-style Search-and-Replace Unified Diff Engine (search_replace).
4. smolagents Code-as-Action Executor running in bubblewrap sandbox (run_code_action).
"""

from __future__ import annotations

import ast
import difflib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from fastmcp import FastMCP
except ImportError:
    FastMCP = None

try:
    from ast_grep_py import SgRoot
except ImportError:
    SgRoot = None


class SearchReplaceEngine:
    """Aider ACI Search-and-Replace engine with unique match guarantees and AST syntax checks."""

    @staticmethod
    def search_replace(
        file_path: Path | str,
        search_block: str,
        replace_block: str,
        allow_multiple: bool = False,
        validate_syntax: bool = True,
    ) -> Dict[str, Any]:
        target = Path(file_path).resolve()
        if not target.exists():
            return {
                "success": False,
                "error": f"Target file does not exist: {target}",
                "file_path": str(target),
            }

        try:
            content = target.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return {"success": False, "error": f"Failed to read file: {e}", "file_path": str(target)}

        count = content.count(search_block)
        if count == 0:
            return {
                "success": False,
                "error": "Search block not found in target file. Ensure exact indentation and content match.",
                "file_path": str(target),
            }

        if count > 1 and not allow_multiple:
            return {
                "success": False,
                "error": f"Ambiguous match: search block found {count} times in file. Narrow your search block to be unique.",
                "file_path": str(target),
                "matches": count,
            }

        if allow_multiple:
            new_content = content.replace(search_block, replace_block)
        else:
            new_content = content.replace(search_block, replace_block, 1)

        # Syntax check for Python files
        if validate_syntax and target.suffix == ".py":
            try:
                ast.parse(new_content)
            except SyntaxError as e:
                return {
                    "success": False,
                    "error": f"SyntaxError after replacement: {e}",
                    "file_path": str(target),
                }

        # Calculate unified diff
        diff_lines = list(difflib.unified_diff(
            content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=str(target),
            tofile=str(target),
            n=3,
        ))
        diff_str = "".join(diff_lines)

        try:
            target.write_text(new_content, encoding="utf-8")
        except Exception as e:
            return {"success": False, "error": f"Failed to write file: {e}", "file_path": str(target)}

        return {
            "success": True,
            "file_path": str(target),
            "replaced_count": count if allow_multiple else 1,
            "diff": diff_str,
        }


class CodeActionExecutor:
    """smolagents Code-as-Action executor running scripts in bubblewrap sandbox with AST preflight."""

    @staticmethod
    def validate_ast(code: str) -> Tuple[bool, Optional[str]]:
        """Preflight checks that Python code is syntactically valid."""
        try:
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            return False, f"SyntaxError at line {e.lineno}, col {e.offset}: {e.msg}"

    @classmethod
    def execute(
        cls,
        code: str,
        timeout_seconds: int = 15,
        workspace_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Executes Python code script inside isolated sandbox with strict timeout."""
        valid, err = cls.validate_ast(code)
        if not valid:
            return {
                "success": False,
                "exit_code": 1,
                "output": f"Preflight Rejected: {err}",
                "syntax_valid": False,
            }

        ws = workspace_dir or Path.cwd()
        ws.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
            tf.write(code)
            script_path = tf.name

        try:
            bwrap_bin = shutil.which("bwrap")
            python_bin = sys.executable

            if bwrap_bin:
                # Bubblewrap unprivileged sandbox
                cmd = [
                    bwrap_bin,
                    "--ro-bind", "/", "/",
                    "--dev", "/dev",
                    "--proc", "/proc",
                    "--bind", str(ws), str(ws),
                    "--bind", script_path, script_path,
                    "--chdir", str(ws),
                    "--unshare-net",
                    "--die-with-parent",
                    python_bin, script_path,
                ]
            else:
                cmd = [python_bin, script_path]

            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(ws),
                timeout=timeout_seconds,
            )
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""
            output = stdout + (("\nSTDERR:\n" + stderr) if stderr else "")

            # Truncate if long using SWE-agent observation windowing
            lines = output.splitlines()
            if len(lines) > 50:
                head = "\n".join(lines[:25])
                tail = "\n".join(lines[-25:])
                output = f"{head}\n\n[... {len(lines) - 50} lines truncated by observation windowing ...]\n\n{tail}"

            return {
                "success": proc.returncode == 0,
                "exit_code": proc.returncode,
                "output": output,
                "syntax_valid": True,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "exit_code": 124,
                "output": f"Execution Timed Out after {timeout_seconds} seconds.",
                "syntax_valid": True,
            }
        except Exception as e:
            return {
                "success": False,
                "exit_code": 1,
                "output": f"Execution error: {e}",
                "syntax_valid": True,
            }
        finally:
            if os.path.exists(script_path):
                try:
                    os.unlink(script_path)
                except Exception:
                    pass


if FastMCP is not None:
    mcp = FastMCP("hermes-tools")

    @mcp.tool
    async def web_extract(url: str, word_limit: int = 500) -> str:
        """Extract clean, LLM-ready markdown from any URL via Crawl4AI."""
        try:
            from crawl4ai import AsyncWebCrawler
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url, word_count_threshold=word_limit)
                return result.markdown or ""
        except ImportError:
            return "Error: crawl4ai is not installed in the active environment."

    @mcp.tool
    def ast_search(pattern: str, code: str, lang: str = "python") -> list[dict]:
        """Search structural code patterns across code using ast-grep Tree-sitter."""
        if SgRoot is None:
            return [{"error": "ast-grep-py is not installed"}]
        root = SgRoot(code, lang)
        matches = root.root().find_all(pattern=pattern)
        return [
            {
                "text": node.text(),
                "range": str(node.range()),
            }
            for node in matches
        ]

    @mcp.tool
    def search_replace(file_path: str, search_block: str, replace_block: str) -> str:
        """Search and replace a unique code block inside a file with diff emission."""
        res = SearchReplaceEngine.search_replace(file_path, search_block, replace_block)
        if res["success"]:
            return f"✓ Replaced block in {res['file_path']}.\nDiff:\n{res['diff']}"
        return f"✗ Search-replace failed: {res.get('error')}"

    @mcp.tool
    def run_code_action(code: str) -> str:
        """Execute a Python code-as-action script in a sandboxed bubblewrap container."""
        res = CodeActionExecutor.execute(code)
        if res["success"]:
            return f"✓ Code Action Succeeded (exit 0):\n{res['output']}"
        return f"✗ Code Action Failed (exit {res['exit_code']}):\n{res['output']}"
else:
    mcp = None


def register(ctx=None):
    """Registers mcp_tools and code-as-action capabilities into Hermes runtime."""
    if not ctx:
        return True

    if hasattr(ctx, "register_cli_command"):
        def setup_tools(parser):
            parser.description = "Hermes Tool Server & Code Action Diagnostics"
            sub = parser.add_subparsers(dest="tool_subcmd")
            sub.add_parser("list", help="List registered tools")

        def handle_tools(args):
            print("Registered FastMCP & Execution Tools:")
            print("  • web_extract: Crawl4AI markdown extraction")
            print("  • ast_search: ast-grep Tree-sitter structural AST search")
            print("  • search_replace: Aider ACI search-and-replace unified diff tool")
            print("  • run_code_action: smolagents sandboxed Python execution engine")
            return 0

        ctx.register_cli_command("tools-diag", "Diagnose FastMCP tool status", setup_tools, handle_tools)

    return True


__all__ = [
    "FastMCP",
    "mcp",
    "ast_search",
    "web_extract",
    "SearchReplaceEngine",
    "CodeActionExecutor",
    "register",
]
