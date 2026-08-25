"""code_mode.py — #58 Code Mode SDK rail (Hermes middleware).

Canonical repo source (Batch-K #58, DeepSeek Harness "Code Mode SDK"
mechanism: a sequence that would take N tool round-trips becomes ONE
model-written program). Installed (synced) into the lever profiles' plugins
dirs by bin/sync_lever_plugins.sh.

What it does (three deterministic pieces, no LLM in the loop):
1. build_sdk_text(): generate a compact Python SDK from the harness arena
   tool bundle — one typed function stub per tool (def name(params) +
   one-line docstring). The model composes N operations as ONE program
   against this SDK instead of making N separate tool-call round trips
   (targets the P0/P2-measured call-count wall: 34 vs 16 req/task).
2. CODE_MODE_RAIL: an instruction block appended to the FIRST-request system
   message (cache-safe prefix — the exact-byte llama.cpp prefix cache must
   survive) telling the model to prefer program-composition (write one
   program, run it, return combined results) over single-shot tool calls,
   and that the program MUST pass ast.parse before execution.
3. validate_program(): the standing-rule gate — ast.parse the model's
   generated program BEFORE any execution. A syntax error is a finding, not
   a retry reason (AGENTS.md §5.1 rule 2: never blind-run generated code).

This is a llm_request middleware, fail-open, deterministic, CACHE-SAFE: it
only APPENDS to the FIRST-request system message and NEVER mutates historical
turns. No LLM calls, no network, no tool execution in this module.

Env knobs (all default ON; off = fail-open no-op):
HILO_CODE_MODE_ENABLED (default 1) · HILO_CODE_MODE_SRC (default: the harness
arena bundle at fastmcp_tool_server.ARENA_TOOLS; a JSON path is accepted) ·
HILO_CODE_MODE_MAX_SDK_CHARS (default 3000, caps the SDK block).
"""

import ast
import json
import os
import sys
from pathlib import Path

_INJECTED = False
_SDK_CACHE = None  # (sdk_text, rail_block) computed once per process


def _env_flag(name, default=True):
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() not in ("0", "false", "off", "no")


def _load_arena_tools():
    """Lift the harness's canonical arena tool bundle as SDK input."""
    src = os.environ.get("HILO_CODE_MODE_SRC")
    if src and Path(src).exists():
        raw = json.load(open(src, encoding="utf-8"))
        tools = raw if isinstance(raw, list) else raw.get("tools", raw)
        return [
            {"name": t["name"], "description": t.get("description", t.get("desc", "")),
             "params": t.get("params") or {}}
            for t in tools
        ]
    try:
        from fastmcp_tool_server import ARENA_TOOLS  # noqa: E402
    except Exception:
        return None
    return [
        {"name": t["name"], "description": t.get("desc", ""), "params": t.get("params") or {}}
        for t in ARENA_TOOLS
    ]


def build_sdk_text(tools, max_chars=3000):
    """Generate a compact Python SDK stub (one function per tool)."""
    if not tools:
        return ""
    lines = ["# Code Mode SDK — compose tool operations as ONE program.",
             "# Each function maps to one tool. Call several in a single",
             "# program, run it, and return the combined results.",
             "import subprocess  # noqa: F401  (example)", ""]
    for t in tools:
        name = t["name"]
        params = t.get("params") or {}
        args = []
        for p, spec in params.items():
            required = spec.get("required", True)
            default = spec.get("default")
            if default is not None:
                args.append(f"{p}={default!r}")
            elif not required:
                args.append(f"{p}=None")
            else:
                args.append(p)
        desc = (t.get("description") or name).replace("\n", " ")[:120]
        lines.append(f"def {name}({', '.join(args)}):")
        lines.append(f"    \"\"\"{desc}\"\"\"")
        lines.append(f"    ...  # tool call: {name}")
        lines.append("")
    text = "\n".join(lines)
    if len(text) > max_chars:
        text = text[:max_chars] + "\n# (truncated)"
    return text


CODE_MODE_RAIL = (
    "# CODE MODE\n"
    "- Prefer COMPOSING operations into ONE program against the SDK below,\n"
    "  then run it once and return combined results — over making many\n"
    "  separate single tool calls (each call re-sends the full context).\n"
    "- The program you emit MUST be valid Python: it will be checked with\n"
    "  ast.parse BEFORE any execution. A syntax error is not retried.\n"
    "- Never echo input back; actually apply the fix and verify.\n"
)


def _build_blocks(tools, max_chars):
    sdk = build_sdk_text(tools, max_chars=max_chars)
    if not sdk:
        return None
    return sdk, CODE_MODE_RAIL


def _get_blocks():
    global _SDK_CACHE
    if _SDK_CACHE is None:
        tools = _load_arena_tools()
        max_chars = int(os.environ.get("HILO_CODE_MODE_MAX_SDK_CHARS", "3000"))
        _SDK_CACHE = _build_blocks(tools, max_chars)
    return _SDK_CACHE


def validate_program(source):
    """Standing-rule gate: ast.parse BEFORE any execution of model code.

    Returns (ok, error). A SyntaxError/IndentationError is a finding, not a
    retry reason. Also rejects empty or obviously-non-Python input.
    """
    if not source or not source.strip():
        return False, "empty program"
    try:
        ast.parse(source)
    except SyntaxError as e:
        return False, f"SyntaxError: {e.msg} (line {e.lineno})"
    except (ValueError, TypeError) as e:
        return False, f"parse error: {e}"
    return True, ""


def llm_request(request, context=None):
    """Middleware: append the Code Mode SDK + rail to the FIRST-request system
    message only (cache-safe — historical turns untouched). Fail-open."""
    global _INJECTED
    if not _env_flag("HILO_CODE_MODE_ENABLED"):
        return request
    if _INJECTED:
        return request
    try:
        blocks = _get_blocks()
        if blocks is None:
            return request
        sdk, rail = blocks
        messages = (request.get("request") or {}).get("messages") or request.get("messages") or []
        if not messages:
            return request
        first = messages[0]
        content = first.get("content") or ""
        sep = "\n\n" if content else ""
        first["content"] = f"{content}{sep}{rail}\n\n{sdk}"
        _INJECTED = True
    except Exception:
        pass  # fail-open: never break the request path
    return request
