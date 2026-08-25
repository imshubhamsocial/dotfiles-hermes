#!/usr/bin/env python3
"""E3 — EASYTOOL-style MCP/OpenAI tool-schema compressor (offline, deterministic).

Paper alignment: EASYTOOL (NAACL'25) — distill verbose tool docs into concise
unified instructions (−70% tool-doc tokens, higher execution success).
Plan row: E3 (Batch-E §5 / RESEARCH_PLAN E3) — the direct fix for the
"4B JSON-schema collapse": a 4B model mis-parses verbose JSON-schema tool
definitions (type/required drift, hallucinated arg keys). We pre-compress every
tool schema OFFLINE, before it reaches the model — no LLM in the loop, so it is
deterministic and free.

Input  (MCP list-tools / OpenAI tools shape):
    [{"name": str, "description": str,
      "inputSchema": {"type": "object",
                      "properties": {arg: {"type": str, "description": str,
                                           "default": ..., "enum": [...]}},
                      "required": [str, ...]}}, ...]

Output (unified instruction per tool — the EASYTOOL "concise unified
instruction" idea, rule-based):
    name(arg: type★, arg2: type=…) → distilled description
      Use for: <folded from description/property hints>
      Avoid:   <folded from explicit negatives, else omitted>

Invariants (the offline-test contract):
    1. Every tool survives; every REQUIRED arg + its type survives.
    2. Deterministic (pure function; stable ordering).
    3. Lossy on prose ONLY: property descriptions, defaults, enums, examples,
       `additionalProperties` are dropped or folded — never required args.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List

# Documented arena token estimate (3.4 chars/token) — same convention as the
# skills budgeter, so compression ratios are comparable across the repo.
CHARS_PER_TOKEN = 3.4

# Hard caps for the compressed body (EASYTOOL: concise, not terse-to-useless).
MAX_DESC_CHARS = 160      # distilled "what it does" line (first sentence)
MAX_USE_FOR_CHARS = 110   # folded "use for" hint (second sentence)
MAX_AVOID_CHARS = 90      # folded "avoid" hint (negative clause)

# Words that mark a description clause as a negative constraint worth keeping.
_AVOID_MARKERS = ("never ", "do not ", "don't use", "avoid ", "not for ",
                  "instead of ", "does not support", "cannot ")


def _trim(text: str, limit: int) -> str:
    """Smart-cut `text` to `limit` chars at a word boundary (append …)."""
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    cut = text[: limit - 1]
    idx = cut.rfind(" ")
    if idx > limit // 2:
        cut = cut[:idx]
    return cut.rstrip(" ,.;:") + "…"


def _sentences(text: str) -> list:
    """Split a description into sentences (stable; keeps abbrev. dots intact)."""
    return [p.strip() for p in re.split(r"(?<=[.!?])\s+", text.strip()) if p.strip()]


def _fold_avoid(description: str) -> str:
    """Pull a negative-constraint clause out of a description, if one exists."""
    low = description.lower()
    for marker in _AVOID_MARKERS:
        idx = low.find(marker)
        if idx >= 0:
            return _trim(description[idx:], MAX_AVOID_CHARS)
    return ""


def _fmt_default(value: Any) -> str:
    """Compact default rendering for the arg table."""
    if isinstance(value, str):
        if len(value) > 24:
            # Path-like defaults keep their basename (the useful part) and
            # collapse the prefix — far denser than a blind 21-char cut.
            if "/" in value:
                return "…/" + value.rstrip("/").split("/")[-1]
            return value[:21] + "…"
        return value
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    return json.dumps(value, separators=(",", ":"))[:24]


def _fmt_type(schema: Dict[str, Any]) -> str:
    """Resolve a property schema to a compact type token (with enum hint)."""
    t = schema.get("type")
    if t == "array":
        items = schema.get("items", {})
        it = items.get("type", "any") if isinstance(items, dict) else "any"
        return f"{it}[]"
    if isinstance(t, list):
        return "|".join(t)
    enum = schema.get("enum")
    if enum:
        short = [str(e)[:10] for e in enum[:3]]
        return f"{t or 'any'}∈{{{','.join(short)}{',' if len(enum) > 3 else ''}}}"
    return t or "any"


def compress_tool(tool: Dict[str, Any]) -> Dict[str, Any]:
    """Compress ONE tool schema into a unified instruction.

    Returns a dict with keys: name, signature, desc, use_for, avoid.
    Raises ValueError on a malformed entry (missing name / non-object schema).
    """
    name = tool.get("name")
    if not name or not isinstance(name, str):
        raise ValueError(f"tool missing string 'name': {tool!r}")
    schema = tool.get("inputSchema") or {}
    if not isinstance(schema, dict):
        raise ValueError(f"tool {name}: inputSchema must be an object")

    props = schema.get("properties") or {}
    if not isinstance(props, dict):
        raise ValueError(f"tool {name}: properties must be an object")
    required = schema.get("required") or []
    if not isinstance(required, list):
        raise ValueError(f"tool {name}: required must be a list")

    full_desc = tool.get("description") or f"{name} tool"
    sentences = _sentences(full_desc)
    desc = _trim(sentences[0], MAX_DESC_CHARS) if sentences else _trim(full_desc, MAX_DESC_CHARS)

    arg_parts: List[str] = []
    # Stable ordering: required args first (alpha), then optional (alpha).
    for arg in sorted(required) + sorted(k for k in props if k not in required):
        prop = props[arg]
        if not isinstance(prop, dict):
            prop = {"type": "any"}
        t = _fmt_type(prop)
        if arg in required:
            arg_parts.append(f"{arg}: {t}★")
        else:
            if "default" in prop:
                arg_parts.append(f"{arg}: {t}={_fmt_default(prop['default'])}")
            else:
                arg_parts.append(f"{arg}: {t}?")

    # "Use for" = the description's SECOND sentence (the "use this when…"
    # clause MCP descriptions conventionally carry) — NOT a re-trim of desc,
    # which would just duplicate the first line and kill the compression ratio.
    use_for = _trim(sentences[1], MAX_USE_FOR_CHARS) if len(sentences) > 1 else ""
    avoid = _fold_avoid(full_desc)

    return {
        "name": name,
        "signature": f"{name}({', '.join(arg_parts)})",
        "desc": desc,
        "use_for": use_for,
        "avoid": avoid,
    }


def render_unified(compressed: Dict[str, Any]) -> str:
    """Render ONE compressed tool as the compact block the model will see."""
    c = compressed
    lines = [f"- {c['signature']} — {c['desc']}"]
    if c["use_for"] and c["use_for"] != c["desc"]:
        lines.append(f"    Use for: {c['use_for']}")
    if c["avoid"]:
        lines.append(f"    Avoid: {c['avoid']}")
    return "\n".join(lines)


def compress_bundle(tools: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compress a whole tool bundle (MCP server / OpenAI tool list).

    Returns {"tools": [compressed...], "block": str, "stats": {...}}.
    Order: input order (stable); block rendered in the same order.
    """
    compressed = [compress_tool(t) for t in tools]
    block = "\n\n".join(render_unified(c) for c in compressed)
    raw_chars = sum(len(json.dumps(t, separators=(",", ":"))) for t in tools)
    out_chars = len(block)
    return {
        "tools": compressed,
        "block": block,
        "stats": {
            "n_tools": len(tools),
            "raw_chars": raw_chars,
            "out_chars": out_chars,
            "raw_tokens": raw_chars / CHARS_PER_TOKEN,
            "out_tokens": out_chars / CHARS_PER_TOKEN,
            "ratio": (out_chars / raw_chars) if raw_chars else 1.0,
            "reduction_pct": max(0.0, (1 - (out_chars / raw_chars)) * 100)
            if raw_chars else 0.0,
        },
    }


def info_preserved(original: Dict[str, Any], compressed: Dict[str, Any]) -> bool:
    """The offline-test contract: every required arg + type survives compression.

    Returns True when, for each original tool, every `required` arg name and its
    declared type token appears in the compressed signature.
    """
    sig = compressed["signature"]
    props = (original.get("inputSchema") or {}).get("properties") or {}
    for arg in (original.get("inputSchema") or {}).get("required") or []:
        if f"{arg}: " not in sig:
            return False
        prop = props.get(arg)
        if isinstance(prop, dict):
            t = _fmt_type(prop)
            if t != "any" and t not in sig:
                return False
    return True


def tool_schemas_from_fastmcp(
    funcs: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Adapter: minimal FastMCP-style func spec → MCP/OpenAI schema shape.

    `funcs` maps tool name → {"description": str, "params": {arg: {"type": str,
    "default": ..., "required": bool}}}. Used to lift real in-repo servers
    (e.g. bin/c01_codebase_memory_mcp.py) into compressor input without a
    FastMCP runtime.
    """
    out: List[Dict[str, Any]] = []
    for name, spec in funcs.items():
        props: Dict[str, Any] = {}
        required: List[str] = []
        for arg, ps in spec["params"].items():
            props[arg] = {"type": ps.get("type", "string")}
            if "default" in ps:
                props[arg]["default"] = ps["default"]
            if ps.get("required", True):
                required.append(arg)
        out.append({
            "name": name,
            "description": spec.get("description", ""),
            "inputSchema": {"type": "object", "properties": props,
                            "required": required},
        })
    return out
