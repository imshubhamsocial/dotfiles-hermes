"""recency_zone.py — G-4 d3 recency-zone re-injection plugin (Hermes middleware).

Canonical repo source. Installed (synced) into the lever profiles' plugins
dirs by bin/sync_lever_plugins.sh — live copies at
~/.hermes/profiles/{lever-thinking,frontier-stack}/plugins/recency_zone.py.

Implements the GDR-round-1 d3 plan (FRONTIER_COVERAGE_MATRIX row d3 / G-4):
J-curve attention (primacy + recency only) — re-inject critical constraints
+ negative rules at the BOTTOM of the context before each generation, with
metadata tags (`### [CONSTRAINT: ABSOLUTE NEGATIVE]`) and a file cap. Rides
Hermes micro-compaction (compression.micro_compact — the base machinery that
folds the middle; this policy re-states the rules that must survive).

Hook: llm_request middleware (schema hermes.middleware.v1), fail-open,
deterministic, and CACHE-SAFE: it only appends to the LAST user/developer
message (which is new content every turn — becomes the cached suffix), never
mutating historical turns (the exact-byte llama.cpp prefix cache must
survive). This is the same constraint as frontier_levers.py F-6/F-8.

Behavior:
- On plugin load, read the constraint source (default: <repo>/AGENTS.md
  Discipline Rail §5 — negative rules, size caps, self-edit review gate).
- Extract constraint sections between markers, tag them with
  `### [CONSTRAINT: ...]` metadata, and cap the block at
  HILO_RECENCY_MAX_CHARS (default 2400 chars ~ 700 tokens).
- On every llm_request, append the block to the last user/developer message —
  the recency zone at the bottom of the context.
- Deterministic: same source → same block; no network, no randomness.

Env knobs (all default ON in the lever profiles; off = fail-open no-op):
HILO_RECENCY_ENABLED (default 1) · HILO_RECENCY_SOURCE (default
<repo>/AGENTS.md) · HILO_RECENCY_MAX_CHARS (default 2400).
"""

import os
import re
from pathlib import Path

_SECTION_START = re.compile(r"^### 5\.[123]\s", re.MULTILINE)
_SECTION_END = re.compile(r"^## |^### 5\.4\b", re.MULTILINE)
_TAG_RE = re.compile(r"^### (?=\S)", re.MULTILINE)

# Metadata tags per d3: the hard NOs are ABSOLUTE NEGATIVE constraints.
_TAG_RULES = {
    "5.1": "CONSTRAINT: ABSOLUTE NEGATIVE",
    "5.2": "CONSTRAINT: SIZE CAP",
    "5.3": "CONSTRAINT: SELF-EDIT GATE",
}

_BLOCK = None            # cached, deterministic constraint block
_BLOCK_SOURCE = None


def _default_source():
    """<repo>/AGENTS.md — the master constraint document (Discipline Rail §5).

    Resolves robustly from BOTH the canonical repo location and the synced
    profile copies (~/.hermes/profiles/...): the launcher exports
    HILO_AMD_MEMORY_DIR = repo root, and the canonical path works for the
    repo copy. First existing candidate wins; falls back to the canonical
    repo layout for direct imports.
    """
    here = Path(__file__).resolve()
    candidates = []
    env_root = os.environ.get("HILO_AMD_MEMORY_DIR")
    if env_root:
        candidates.append(Path(env_root) / "AGENTS.md")
    # canonical repo copy: plugins/prototypes/harness/09-arena/researches -> root
    candidates.append(here.parents[5] / "AGENTS.md")
    # synced profile copy: walk up looking for a repo marker (AGENTS.md)
    for parent in here.parents:
        cand = parent / "AGENTS.md"
        if cand.is_file():
            candidates.append(cand)
            break
    for cand in candidates:
        if cand.is_file():
            return cand
    return candidates[0]  # fail-open: extract() returns '' when missing


def extract_constraint_block(source, max_chars=2400):
    """Deterministically extract the Discipline Rail §5 constraint block.

    Returns a tagged, capped string ('' when nothing is found — fail-open).
    """
    try:
        text = Path(source).read_text(encoding="utf-8")
    except (OSError, TypeError):
        return ""
    # Locate the Discipline Rail section (## 5.) and cut at the next ##
    start = text.find("## 5.")
    if start < 0:
        return ""
    end = text.find("\n## ", start + 4)
    if end < 0:
        end = len(text)
    section = text[start:end]

    parts = []
    for m in _SECTION_START.finditer(section):
        # section header line: "### 5.1 Negative rules (the hard NOs)"
        head_end = section.find("\n", m.start())
        if head_end < 0:
            head_end = len(section)
        header = section[m.start():head_end].strip()
        # header is "### 5.1 Negative rules (the hard NOs)" — drop the ###
        num = header.lstrip("#").strip().split(" ", 1)[0].rstrip(".")  # "5.1"
        tag = _TAG_RULES.get(num, "CONSTRAINT")
        # section body: until the next ### 5.x or end
        body_end = _SECTION_START.search(section, head_end)
        body_end = body_end.start() if body_end else len(section)
        body = section[head_end:body_end].strip()
        if not body:
            continue
        parts.append(f"### [{tag}]\n\n{body}")

    if not parts:
        return ""
    block = "\n\n".join(parts)
    if len(block) > max_chars:
        block = block[:max_chars].rsplit("\n", 1)[0]
    return block


def _get_block():
    global _BLOCK, _BLOCK_SOURCE
    source = os.environ.get("HILO_RECENCY_SOURCE") or str(_default_source())
    max_chars = int(os.environ.get("HILO_RECENCY_MAX_CHARS", "2400") or 2400)
    if _BLOCK is None or source != _BLOCK_SOURCE:
        _BLOCK = extract_constraint_block(source, max_chars=max_chars)
        _BLOCK_SOURCE = source
    return _BLOCK


def register(ctx):
    ctx.register_middleware("llm_request", recency_zone_request)


def _env_flag(name, default=True):
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() not in ("0", "false", "off", "no")


def _append_text(content, suffix):
    """Append a text suffix to a message content (str or parts-list), cache-safe."""
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


def _last_user_message_index(messages):
    for i in range(len(messages) - 1, -1, -1):
        m = messages[i]
        if isinstance(m, dict) and m.get("role") in ("user", "developer"):
            return i
    return -1


def recency_zone_request(**kwargs):
    """Append the tagged constraint block to the last user message (recency zone)."""
    if not _env_flag("HILO_RECENCY_ENABLED"):
        return None  # fail-open: disabled
    try:
        req = kwargs.get("request")
        if not isinstance(req, dict):
            return None
        request = dict(req)
        messages = request.get("messages")
        if not isinstance(messages, list) or not messages:
            return None
        block = _get_block()
        if not block:
            return None  # fail-open: no constraints extracted
        user_idx = _last_user_message_index(messages)
        if user_idx < 0:
            return None
        user_msg = messages[user_idx]
        user_msg["content"] = _append_text(
            user_msg.get("content"), "\n\n" + block)
        return {
            "request": request,
            "source": "recency-zone",
            "reason": f"d3 re-injection ({len(block)} chars constraint block)",
        }
    except Exception:
        return None  # fail-open: never break a live request
