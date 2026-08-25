"""amd_memory.py (plugin) — Agent Memory Distillation (AMD) Hermes middleware.

Canonical repo source. Installed (synced) into the lever profiles' plugins
dirs by bin/sync_lever_plugins.sh — live copies at
~/.hermes/profiles/{lever-thinking,frontier-stack}/plugins/amd_memory.py.

Implements the CP-3 AMD rail (CONVERGENCE_PLAN_2026-08-13 §9 CP-3; Batch-H
#34 + Batch-I R8) as Hermes middleware (schema hermes.middleware.v1),
fail-open, deterministic, CACHE-SAFE (only appends to the first-request
system message — joins the cached prefix — or to the LAST user message which
is new content every turn; never mutates historical turns).

Injection protocol (the AMD recipe, exactly):
- WORKFLOW (Text tier): PROACTIVE at task start — on request #1, append the
  workflow strategy prose to the system message (once per process).
- SUBTASK (Code tier): PROACTIVE, retrieved dynamically — when the LAST
  message is a fresh user instruction (no tool call in the turn yet), the
  instruction IS the query; retrieve k=1 subtask memory and prefix it to the
  current user message (a compact code example the 4B can pattern-match).
- FUNCTION (Code tier): REACTIVE on tool errors ONLY — tool_execution detects
  a failing tool result, retrieves k=1 function memory for the called
  function, and stashes it; the NEXT llm_request appends it to the current
  user message (exactly once).
- Retrieval is k=1 (HARD — AMD ablation: k>1 collapses 49.4%->33.3%).

Env knobs (all default ON):
HILO_AMD_ENABLED (default 1) · HILO_AMD_MEMORY_DIR (default: $PWD/memory-bank
or $AMD_MEMORY_DIR; the per-project bank root) · HILO_AMD_RETRIEVER
(auto|dense|bm25, default auto) · HILO_AMD_EMBED_MODEL (default
all-MiniLM-L6-v2) · HILO_AMD_CORE_DIR (repo prototypes dir for the core
module; auto-detected, with an inline fallback so the plugin still works when
the repo is absent).
"""

import json
import os
import re
import sys
import time
from pathlib import Path

_SYSTEM_AMD_INJECTED = False
_PENDING_FUNCTION = None          # stashed by tool_execution, consumed by next request


def register(ctx):
    ctx.register_middleware("llm_request", amd_request)
    ctx.register_middleware("tool_execution", amd_tool_execution)


def _env_flag(name, default=True):
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() not in ("0", "false", "off", "no")


def _core():
    """Import the core rail (amd_memory.py) — repo path first, else None.

    Self-guard: the core module must be a DIFFERENT file that actually
    defines MemoryBank. Without it, a self-match (this plugin body contains
    the literal marker string in its own detection code) or a stale path
    resolves to this file itself and the rail silently no-ops."""
    try:
        d = os.environ.get("HILO_AMD_CORE_DIR") or _default_core_dir()
        if not d:
            return None
        sys.path.insert(0, d)
        import amd_memory as A  # noqa: PLC0415
        if getattr(A, "MemoryBank", None) is None:
            return None
        if getattr(A, "__file__", "") and os.path.abspath(A.__file__) == os.path.abspath(__file__):
            return None  # resolved to the plugin body itself — not the core
        return A
    except Exception:
        return None


def _default_core_dir():
    here = Path(__file__).resolve()
    # The CORE module (a DIFFERENT amd_memory.py containing MemoryBank) lives:
    #   repo:    prototypes/amd_memory.py            (plugin at plugins/…)
    #   profile: <profile>/amd_memory.py             (plugin at plugins/<name>/…)
    # Walk ancestors (up to 4 levels) and return the first dir whose
    # amd_memory.py really contains the MemoryBank class — full-file scan so
    # a truncated marker can never force the wrong fallback. Never returns
    # this plugin file itself (it has no MemoryBank).
    me = here
    for cand in (here.parent, here.parent.parent, here.parent.parent.parent,
                 here.parent.parent.parent.parent):
        p = cand / "amd_memory.py"
        try:
            if p.resolve() == me:
                continue  # never the plugin body itself
            if p.exists() and "class MemoryBank:" in p.read_text(
                    encoding="utf-8", errors="ignore"):
                return str(cand)
        except Exception:
            continue
    return str(here.parent.parent)


def _bank():
    """MemoryBank root — fail-open to None when no project memory exists."""
    root = os.environ.get("HILO_AMD_MEMORY_DIR") or os.environ.get("AMD_MEMORY_DIR")
    if not root:
        for cand in (Path.cwd(), Path.cwd() / "..", Path.cwd() / "memory-bank"):
            p = cand / "memory-bank" if cand.name != "memory-bank" else cand
            if p.exists():
                root = str(cand)
                break
    if not root:
        return None
    A = _core()
    if A is None:
        return None
    try:
        return A.MemoryBank(root)
    except Exception:
        return None


def _append_text(content, suffix):
    if content is None:
        return suffix
    if isinstance(content, str):
        return content + suffix
    if isinstance(content, list):
        try:
            return list(content) + [{"type": "text", "text": suffix.lstrip("\n")}]
        except Exception:
            return content
    return content


def _last_user_index(messages):
    for i in range(len(messages) - 1, -1, -1):
        m = messages[i]
        if isinstance(m, dict) and m.get("role") in ("user", "developer"):
            return i
    return -1


def _turn_has_tool_call(messages):
    """True when the most recent assistant turn made a tool call (so the
    current user message is a tool result follow-up, NOT a fresh instruction)."""
    for i in range(len(messages) - 1, -1, -1):
        m = messages[i]
        if not isinstance(m, dict):
            continue
        if m.get("role") == "assistant":
            return bool(m.get("tool_calls"))
        if m.get("role") in ("user", "developer"):
            return False
    return False


def _is_tool_error(result):
    """True when a tool result signals a failure.

    Real Hermes tool results are usually STRINGS (the tool's raw output —
    e.g. a terminal transcript), sometimes dicts. Handle both shapes;
    anything with a nonzero rc / exit code or an error marker counts.
    """
    if isinstance(result, str):
        text = result[:4000]
    elif isinstance(result, dict):
        content = result.get("content")
        text = content if isinstance(content, str) else json.dumps(content)[:4000]
    else:
        text = json.dumps(result)[:4000]
    low = text.lower()
    return bool(re.search(r"\b(rc|exit|code)\s*[=:]?\s*[1-9]\d*", low) or
                re.search(r"\b(error|failed|failure|exception|traceback)\b", low))


def amd_request(**kwargs):
    """llm_request: proactive workflow (request #1) + proactive subtask
    (fresh instruction) + reactive function (stashed by tool_execution)."""
    global _SYSTEM_AMD_INJECTED, _PENDING_FUNCTION
    try:
        if not _env_flag("HILO_AMD_ENABLED"):
            return None
        req = kwargs.get("request")
        if not isinstance(req, dict):
            return None
        request = dict(req)
        messages = request.get("messages")
        if not isinstance(messages, list) or not messages:
            return None
        A = _core()
        bank = _bank()
        reasons = []
        changed = False

        # Reactive Function injection (consume the stash first — it is the
        # highest-value corrective guidance and must land immediately).
        if _PENDING_FUNCTION:
            fidx = _last_user_index(messages)
            if fidx >= 0:
                messages[fidx]["content"] = _append_text(
                    messages[fidx].get("content"),
                    "\n\n[AMD function memory]\n" + _PENDING_FUNCTION)
                changed = True
                reasons.append("AMD reactive function memory (tool error)")
            _PENDING_FUNCTION = None

        # Proactive Workflow at task start (once per process).
        if not _SYSTEM_AMD_INJECTED and bank is not None:
            wf = bank.render_workflow()
            if wf:
                first = messages[0]
                if isinstance(first, dict) and first.get("role") in ("system", "developer"):
                    first["content"] = _append_text(
                        first.get("content"), "\n\n[AMD workflow memory]\n" + wf)
                    _SYSTEM_AMD_INJECTED = True
                    changed = True
                    reasons.append("AMD proactive workflow (task start)")

        # Proactive Subtask on a fresh instruction (no tool call in the turn).
        if bank is not None and not _turn_has_tool_call(messages):
            uid = _last_user_index(messages)
            if uid >= 0:
                content = messages[uid].get("content")
                query = content if isinstance(content, str) else str(content)
                if query.strip():
                    hit = bank.retrieve("subtask", query, k=1,
                                        backend=os.environ.get("HILO_AMD_RETRIEVER", "auto"))
                    if hit and hit.get("entry"):
                        block = bank.render_subtask(hit["entry"])
                        messages[uid]["content"] = _append_text(
                            messages[uid].get("content"),
                            "\n\n[AMD subtask memory — retrieved k=1 (%s)]\n%s"
                            % (hit.get("backend", "?"), block))
                        changed = True
                        reasons.append("AMD proactive subtask (fresh instruction)")

        if not changed:
            return None
        return {"request": request, "source": "amd-memory",
                "reason": "; ".join(reasons)}
    except Exception:
        return None  # fail-open


def amd_tool_execution(**kwargs):
    """tool_execution: run the tool downstream, then on a FAILING result
    retrieve function memory k=1 and stash it for the next llm_request.

    HERMES CONTRACT (Entry 72 — live smoke caught this): the middleware
    MUST call ``next_call(args)`` to actually run the tool, and its return
    value IS the tool result. The old implementation read a ``result``
    kwarg Hermes never passes, never called ``next_call``, and returned
    None — so EVERY tool result became None ("4 chars") and agents
    blind-looped. This is observe-only: the downstream result is ALWAYS
    returned unchanged; the stash happens as a side effect.
    """
    global _PENDING_FUNCTION
    next_call = kwargs.get("next_call")
    args = kwargs.get("args")
    tool_name = kwargs.get("tool_name") or ""
    try:
        if next_call is None:
            # Not a live chain (direct unit-test call) — nothing to run.
            return None
        # 1. MUST run the tool downstream — its result IS the tool result.
        result = next_call(args if isinstance(args, dict) else {})
        # 2. Observe (never mutate): on a failing result, stash function
        #    memory for the NEXT llm_request to inject.
        if _env_flag("HILO_AMD_ENABLED"):
            bank = _bank()
            if bank is not None and _is_tool_error(result):
                hit = bank.retrieve("function", tool_name or "error", k=1,
                                    backend=os.environ.get("HILO_AMD_RETRIEVER",
                                                            "auto"))
                if hit and hit.get("entry"):
                    _PENDING_FUNCTION = bank.render_function(hit["entry"])
        # 3. ALWAYS pass the real tool result through unchanged.
        return result
    except Exception:
        return None
