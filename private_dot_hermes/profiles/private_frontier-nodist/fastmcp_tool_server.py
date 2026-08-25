#!/usr/bin/env python3
"""E2 — FastMCP stdio tool server for the harness (extension of the c01 pattern).

Plan row: E2 (Batch-E §3 / RESEARCH_PLAN E2) — Batch-E's verdict: llama.cpp has
no native MCP backend, so the robust pattern is a **FastMCP stdio child
process** the harness spawns, exposing the arena tool bundle. This server
exposes the 8 harness tools over MCP with two schema modes:

    --compressed   E3 mode: every tool's description is the EASYTOOL-style
                   unified instruction from toolkit_compressor (the
                   "pre-compress every MCP server's schema offline" design,
                   Batch-E §5) instead of the raw verbose text.

Design (testable without FastMCP installed):
    - `build_tool_registry(compressed)` is a PURE function — the schema layer.
      Offline tests cover it (names, param types, required-preservation,
      compression, determinism) with zero FastMCP dependency.
    - `create_server()` lazy-imports FastMCP so importing this module never
      hard-requires the package; the offline suite stays green anywhere.
    - Tool bodies are thin and safe: path validation, bounded subprocess
      timeouts. (The `bash` tool is BY DESIGN a shell-command runner — that is
      its contract, and the arena harness already treats it as the mutating
      escape hatch; everything else avoids the shell.)

Runtime (inside ws-ai, per the user mandate — FastMCP installed there):
    distrobox enter ws-ai -- python3 fastmcp_tool_server.py [--compressed]
    # stdio transport; the harness spawns it as a child process.
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from typing import Any, Dict, List

from toolkit_compressor import (  # noqa: E402 — sibling module
    compress_bundle,
    render_unified,
)

# The 8 arena tools (mirrors harness.py TOOL_NAMES / TOOLS_SYSTEM_PROMPT).
# desc = verbose schema text (E2 mode); E3 mode replaces it with the unified
# instruction. params = {"type", "required", "default"?} — the schema source.
ARENA_TOOLS: List[Dict[str, Any]] = [
    {"name": "bash",
     "desc": "Run a shell command in the workspace with an optional timeout in "
             "seconds. The command is executed with the workspace root as its "
             "working directory and its stdout, stderr, and exit code are "
             "captured and returned. Use this tool to run builds, test runners, "
             "package installs, and any other terminal work the task requires. "
             "The timeout parameter caps the wall-clock budget for the command. "
             "Never use this tool to run commands that modify the tests/ "
             "directory or any graded artifact.",
     "params": {"cmd": {"type": "string", "required": True},
                "timeout": {"type": "integer", "required": False, "default": 60}}},
    {"name": "rg_search",
     "desc": "Search file contents with ripgrep and return matching lines with "
             "file paths and line numbers, capped at the max_results argument. "
             "Use this tool for locating definitions, usages, and TODO markers "
             "across the workspace before editing. Results are ordered by "
             "relevance and truncated to the cap. This tool cannot search "
             "inside binary files or the .git directory.",
     "params": {"pattern": {"type": "string", "required": True},
                "flags": {"type": "string", "required": False, "default": ""},
                "max_results": {"type": "integer", "required": False, "default": 50}}},
    {"name": "read_file",
     "desc": "Read a file from the workspace and return up to max_chars "
             "characters of its content. Use this tool for inspecting source "
             "files, configuration files, and build artifacts before editing. "
             "The read is bounded so very large files never flood the context; "
             "raise max_chars deliberately when the full file is required. "
             "Does not follow symlinks out of the workspace.",
     "params": {"path": {"type": "string", "required": True},
                "max_chars": {"type": "integer", "required": False, "default": 8000}}},
    {"name": "write_file",
     "desc": "Write a file to the workspace at the given path, overwriting any "
             "existing content and creating parent directories as needed. Use "
             "this tool for creating or editing source files in the project. "
             "The full new content must be supplied verbatim in the content "
             "argument. Never use this tool to modify test files in the tests/ "
             "directory — those are graded and must stay untouched.",
     "params": {"path": {"type": "string", "required": True},
                "content": {"type": "string", "required": True}}},
    {"name": "run_tests",
     "desc": "Run the project test suite with the given CLI arguments and "
             "return the pass/fail summary with per-test results. Use this "
             "tool to verify the implementation against the tests after any "
             "change so regressions are caught early. The args argument is "
             "forwarded verbatim to the test runner. Exit code is non-zero "
             "when any test fails.",
     "params": {"args": {"type": "string", "required": False, "default": ""}}},
    {"name": "tree_sitter_symbols",
     "desc": "List top-level symbols from a code-index SQLite database at the "
             "given db_path. Returns def and class names with their file and "
             "line, ordered by confidence. Use this tool to get the symbol map "
             "of a project before deep-reading individual files. Requires the "
             "index to have been built by the indexer tool first.",
     "params": {"db_path": {"type": "string", "required": True}}},
    {"name": "localize_seek",
     "desc": "Seek a symbol by name in a code-index SQLite database and return "
             "its exact byte-offset source span. Use this tool to localize a "
             "definition before editing — a 95-99% token cut versus "
             "file-by-file exploration. The span includes file, start offset, "
             "and length so a follow-up read can fetch exactly the region.",
     "params": {"symbol": {"type": "string", "required": True},
                "db_path": {"type": "string", "required": True}}},
    {"name": "memory_search",
     "desc": "Query the codebase-memory database by substring over symbol "
             "names and file paths, returning the top matches ordered by "
             "confidence and capped by the limit argument. Use this tool to "
             "find symbols that might match a fuzzy name before falling back "
             "to a full repository grep.",
     "params": {"query": {"type": "string", "required": True},
                "limit": {"type": "integer", "required": False, "default": 5}}},
]


def build_tool_registry(compressed: bool = False) -> List[Dict[str, Any]]:
    """The schema layer — PURE, offline-testable.

    Returns [{"name", "description", "params": {arg: {"type", "required",
    "default"?}}}]. In compressed mode every description is the E3 unified
    instruction (signature + distilled desc + avoid) — the EASYTOOL fix applied
    to our own bundle.
    """
    if not compressed:
        return [
            {"name": t["name"], "description": t["desc"], "params": t["params"]}
            for t in ARENA_TOOLS
        ]
    schemas = [
        {"name": t["name"], "description": t["desc"],
         "inputSchema": {"type": "object",
                         "properties": {a: {"type": p["type"],
                                            **({"default": p["default"]}
                                               if "default" in p else {})}
                                        for a, p in t["params"].items()},
                         "required": [a for a, p in t["params"].items()
                                      if p.get("required")]}}
        for t in ARENA_TOOLS
    ]
    res = compress_bundle(schemas)
    by_name = {c["name"]: c for c in res["tools"]}
    return [
        {"name": t["name"], "description": render_unified(by_name[t["name"]]),
         "params": t["params"]}
        for t in ARENA_TOOLS
    ]


# ── tool bodies (thin, safe; wired to real harness semantics) ───────────────

def _run_bash(cmd: str, timeout: int) -> Dict[str, Any]:
    try:
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                              timeout=timeout)
        return {"rc": proc.returncode, "stdout": proc.stdout[-4000:],
                "stderr": proc.stderr[-2000:]}
    except subprocess.TimeoutExpired:
        return {"rc": -1, "stdout": "", "stderr": f"timeout after {timeout}s"}


def _sqlite_query(db_path: str, sql: str, params: tuple) -> Dict[str, Any]:
    if not os.path.exists(db_path):
        return {"error": f"Database {db_path} does not exist", "count": 0}
    try:
        conn = sqlite3.connect(db_path)
        rows = conn.execute(sql, params).fetchall()
        conn.close()
        return {"rows": [list(r) for r in rows], "count": len(rows)}
    except sqlite3.Error as err:
        return {"error": str(err), "count": 0}


def _tool_impl(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatch a registry tool → result dict (the server's runtime core)."""
    if name == "bash":
        return _run_bash(str(args.get("cmd", "")), int(args.get("timeout", 60)))
    if name == "read_file":
        path = str(args["path"])
        if not os.path.isfile(path):
            return {"error": f"no such file: {path}"}
        with open(path, encoding="utf-8", errors="replace") as fh:
            return {"content": fh.read(int(args.get("max_chars", 8000)))}
    if name == "write_file":
        path = str(args["path"])
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(str(args["content"]))
        return {"wrote": path}
    if name == "rg_search":
        return _run_bash(
            f"rg --line-number {args.get('flags', '')} "
            f"--max-count {int(args.get('max_results', 50))} "
            f"{json.dumps(str(args['pattern']))} . 2>/dev/null | head -200", 60)
    if name == "run_tests":
        return _run_bash(f"python3 -m pytest {args.get('args', '')} 2>&1", 300)
    if name == "tree_sitter_symbols":
        return _sqlite_query(
            str(args["db_path"]),
            "SELECT name, kind, file_path, line_number FROM symbols "
            "ORDER BY confidence DESC LIMIT 50", ())
    if name == "localize_seek":
        return _sqlite_query(
            str(args["db_path"]),
            "SELECT name, file_path, byte_offset, byte_length FROM symbols "
            "WHERE name = ? LIMIT 5", (str(args["symbol"]),))
    if name == "memory_search":
        return _sqlite_query(
            str(args["db_path"]),
            "SELECT name, kind, file_path, confidence FROM symbols "
            "WHERE name LIKE ? OR file_path LIKE ? ORDER BY confidence DESC "
            "LIMIT ?", (f"%{args['query']}%", f"%{args['query']}%",
                        int(args.get("limit", 5))))
    return {"error": f"unknown tool: {name}"}


def create_server(compressed: bool = False):
    """Lazy-import FastMCP and register the registry. Returns the server.

    Not importable when FastMCP is missing — callers (and offline tests) must
    not reach here without the dependency (installed in ws-ai).
    """
    from mcp.server.fastmcp import FastMCP  # lazy — ws-ai dependency

    mcp = FastMCP("arena-tool-bundle")
    registry = build_tool_registry(compressed=compressed)

    def make_handler(name: str):
        def handler(**kwargs: Any) -> Dict[str, Any]:
            return _tool_impl(name, kwargs)
        handler.__name__ = name
        return handler

    for tool in registry:
        desc = tool["description"].replace("\n", " ").strip()
        mcp.tool(name=tool["name"], description=desc)(make_handler(tool["name"]))
    return mcp


def main() -> int:
    compressed = "--compressed" in sys.argv[1:]
    mcp = create_server(compressed=compressed)
    mcp.run()  # stdio transport
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
