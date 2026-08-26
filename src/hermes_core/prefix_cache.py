"""
U8 Byte-Static Prefix Cache Alignment (Phase 3.2)
=================================================
Dynamic system-prompt bytes destroy llama-server KV prefix reuse every turn
(roadmap §3.2 Trap-1). This module makes the cached prefix provably stable:

  1. `build_static_system_prompt()` composes the system prompt from a
     fixed-order segment list -> byte-identical output for identical inputs.
  2. Dynamic metadata (working-memory anchors, boundary constraints,
     timestamps, git hash) MUST be appended at the tail of the latest USER
     turn via `append_dynamic_tail()` — never inside the system prefix.
  3. Trap-1 lint: `assert_byte_static()` pins the first
     `PREFIX_BUDGET_TOKENS` tokens against a registered sha256 digest and
     raises `PrefixCacheViolation` on any byte drift.

Verification target (roadmap §3.2): >90% KV prefix-cache hits on tokens
0-1024 for turns 2+ under live llama-server traffic.
"""

import copy
import hashlib
from typing import Any, Dict, List, Optional

try:
    from .presets import estimate_prompt_tokens
except ImportError:  # packageless loaders (integrity probes) hit this branch
    from hermes_core.presets import estimate_prompt_tokens

PREFIX_BUDGET_TOKENS = 1024
_CHARS_PER_TOKEN = 4  # heuristic aligned with presets.estimate_prompt_tokens


class PrefixCacheViolation(AssertionError):
    """Raised when a composed system prompt drifts from its registered prefix."""


def build_static_system_prompt(*segments: str) -> str:
    """Deterministic fixed-order join; empty/whitespace segments are dropped."""
    return "\n\n".join(s.strip() for s in segments if s and s.strip())


def prefix_window_bytes(n_tokens: int = PREFIX_BUDGET_TOKENS) -> int:
    return n_tokens * _CHARS_PER_TOKEN


def static_prefix_hash(system_prompt: str, n_tokens: int = PREFIX_BUDGET_TOKENS) -> str:
    window = system_prompt.encode("utf-8")[: prefix_window_bytes(n_tokens)]
    return hashlib.sha256(window).hexdigest()


def assert_byte_static(system_prompt: str, expected_hash: str,
                       n_tokens: int = PREFIX_BUDGET_TOKENS) -> None:
    actual = static_prefix_hash(system_prompt, n_tokens)
    if actual != expected_hash:
        raise PrefixCacheViolation(
            f"U8 Trap-1 lint: system-prefix drift detected "
            f"(expected {expected_hash[:12]}, got {actual[:12]}); "
            f"dynamic metadata must move to the user-turn tail."
        )


def append_dynamic_tail(user_content: str, dynamic_block: str) -> str:
    """Append one dynamic block at the very end of a user-turn payload."""
    base = user_content.rstrip() if user_content else ""
    return f"{base}\n\n{dynamic_block.strip()}" if base else dynamic_block.strip()


def inject_dynamic_into_last_user_turn(history: List[Dict[str, Any]],
                                       dynamic_block: str) -> List[Dict[str, Any]]:
    """Return an augmented COPY of history with dynamic_block at the tail of
    the most recent user turn (a fresh user turn is appended when none exists).
    Tool-role ordering is preserved; the input list is never mutated."""
    if not dynamic_block or not dynamic_block.strip():
        return history
    out = [dict(m) for m in history]
    user_idx = next((i for i in range(len(out) - 1, -1, -1)
                     if out[i].get("role") == "user"), None)
    if user_idx is None:
        out.append({"role": "user", "content": dynamic_block.strip()})
    else:
        msg = dict(out[user_idx])
        msg["content"] = append_dynamic_tail(str(msg.get("content") or ""), dynamic_block)
        out[user_idx] = msg
    return out


def prefix_stats(system_prompt: str) -> Dict[str, Any]:
    """Registry payload for a static prefix (hash + token footprint)."""
    return {
        "hash": static_prefix_hash(system_prompt),
        "estimated_tokens": estimate_prompt_tokens(system_prompt),
        "window_bytes": prefix_window_bytes(),
    }
