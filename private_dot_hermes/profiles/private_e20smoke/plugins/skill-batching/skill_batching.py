"""skill_batching.py — #4k Skill-guided batching (Second Thought 2608.13667 + E4 cluster-plan).

Reduces wall time by tracking which tool cluster the model is currently in
and injecting turn-level guidance to complete the current cluster before
switching. Based on:

- Second Thought (HF 2608.13667): parallel reasoning during tool-execution
  idle window — the model can plan the NEXT step while the current tool
  runs. We approximate this without GPU headroom by making the cluster
  plan more actionable.
- E4 cluster-plan (compound_tools.py): already injected, but the model
  doesn't always follow it. This plugin adds turn-level enforcement.
- Measured wall: 34 calls/task vs optimal 16. The overhead comes from
  "cluster switching" — the model interleaving reads and writes, causing
  redundant context processing.

What it does (deterministic, no LLM in the loop):
1. CLUSTER TRACKING: Monitors which tool class is being called and tracks
   the current cluster (read/search cluster → write cluster → execute cluster).
2. SWITCH NUDGE: When the model switches clusters prematurely (e.g., writes
   a file before finishing all reads), injects a "complete the current cluster
   first" directive.
3. COMPLETION HINTS: When the model has been in a cluster for many turns,
   injects a "you're done with this cluster, move to the next" nudge.

This is a llm_request middleware, fail-open, deterministic, CACHE-SAFE:
it only APPENDS to the LAST user/developer message (new content every turn)
and NEVER mutates historical turns.

Env knobs:
    HILO_SKILL_BATCHING_ENABLED (default 1) — set 0 to disable.
    HILO_SKILL_BATCHING_SWITCH_THRESHOLD (default 2) — nudge after N same-cluster calls.
    HILO_SKILL_BATCHING_COMPLETION_THRESHOLD (default 5) — hint after N calls in cluster.
"""

import os
from typing import Optional, Tuple

_INJECTED = False

# Cluster definitions (mirrors tool_gate.py TOOL_CLASSES)
CLUSTERS = {
    "read": "gathering",
    "search": "gathering",
    "write": "implementation",
    "execute": "verification",
    "load": "setup",
    "interact": "interaction",
}

# Ordered cluster sequence (typical task flow)
CLUSTER_SEQUENCE = ["gathering", "implementation", "verification"]

# Directives
_SWITCH_NUDGE = (
    "\n\n[Skill batching: You switched from {prev_cluster} to {new_cluster} "
    "after only {count} calls. Complete ALL planned {prev_cluster} operations "
    "before switching — interleaving clusters wastes context tokens.]"
)

_COMPLETION_HINT = (
    "\n\n[Skill batching: You've made {count} calls in the {cluster} phase. "
    "If all {cluster} tasks are done, proceed to the next phase. "
    "If not, continue — but batch remaining operations.]"
)

# State
_current_cluster: Optional[str] = None
_cluster_call_count: int = 0
_last_cluster: Optional[str] = None


def _env_flag(name, default=True):
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() not in ("0", "false", "off", "no")


def _env_int(name, default):
    v = os.environ.get(name)
    if v is None:
        return default
    try:
        return int(v)
    except (ValueError, TypeError):
        return default


def is_enabled():
    return _env_flag("HILO_SKILL_BATCHING_ENABLED", True)


def reset_state():
    """Reset cluster tracking state (for testing or new task)."""
    global _current_cluster, _cluster_call_count, _last_cluster, _INJECTED
    _current_cluster = None
    _cluster_call_count = 0
    _last_cluster = None
    _INJECTED = False


def track_tool_call(tool_name: str) -> Tuple[Optional[str], bool]:
    """Track a tool call and detect cluster switches.

    Returns (cluster_name: str, switched: bool).
    """
    global _current_cluster, _cluster_call_count, _last_cluster

    # Map tool name to cluster
    from tool_gate import classify_tool_call
    tool_class = classify_tool_call(tool_name)
    cluster = CLUSTERS.get(tool_class, "other")

    switched = False
    if _current_cluster is not None and cluster != _current_cluster:
        _last_cluster = _current_cluster
        switched = True
        _cluster_call_count = 1
    else:
        _cluster_call_count += 1

    _current_cluster = cluster
    return cluster, switched


def get_batching_directive() -> Optional[str]:
    """Get a batching directive to inject based on current state.

    Returns a directive string or None if no nudge needed.
    """
    global _cluster_call_count

    if _current_cluster is None:
        return None

    switch_threshold = _env_int("HILO_SKILL_BATCHING_SWITCH_THRESHOLD", 2)
    completion_threshold = _env_int("HILO_SKILL_BATCHING_COMPLETION_THRESHOLD", 5)

    # Check for premature switch
    if _last_cluster is not None and _cluster_call_count <= switch_threshold:
        return _SWITCH_NUDGE.format(
            prev_cluster=_last_cluster,
            new_cluster=_current_cluster,
            count=_cluster_call_count,
        )

    # Check for completion hint
    if _cluster_call_count >= completion_threshold:
        return _COMPLETION_HINT.format(
            count=_cluster_call_count,
            cluster=_current_cluster,
        )

    return None


def _append_text(content, suffix):
    """Append a text suffix to message content (str or parts-list), cache-safe."""
    if content is None:
        return suffix
    if isinstance(content, str):
        return content + suffix
    if isinstance(content, list):
        try:
            return list(content) + [{"type": "text", "text": suffix.lstrip("\n")}]
        except Exception:
            return content
    return content  # fail-open


def _last_user_message_index(messages):
    for i in range(len(messages) - 1, -1, -1):
        m = messages[i]
        if isinstance(m, dict) and m.get("role") in ("user", "developer"):
            return i
    return -1


def _on_request(request):
    """Core logic: inject skill-batching directives."""
    global _INJECTED

    if not is_enabled():
        return None

    messages = request.get("messages")
    if not isinstance(messages, list) or not messages:
        return None

    # Check if there's a tool call in the request (assistant message with tool_calls)
    # or if we should inject based on current state
    directive = get_batching_directive()
    if directive is None:
        return None

    user_idx = _last_user_message_index(messages)
    if user_idx < 0:
        return None

    user_content = messages[user_idx].get("content", "")
    messages[user_idx]["content"] = _append_text(user_content, directive)

    return {
        "request": request,
        "source": "skill-batching",
        "reason": f"cluster {_current_cluster} (count={_cluster_call_count})",
    }


def register(ctx):
    """Register the llm_request middleware under the hermes.v1 contract."""
    def _middleware(**kwargs):
        try:
            req = kwargs.get("request")
            if not isinstance(req, dict):
                return None
            request = dict(req)
            return _on_request(request)
        except Exception:
            return None  # absolute fail-open: never break the request path

    ctx.register_middleware("llm_request", _middleware)
