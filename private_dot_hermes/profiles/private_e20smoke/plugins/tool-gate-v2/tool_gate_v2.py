"""tool_gate_v2.py — Phase-aware tool FILTERING (not directives).

v1 FOLD verdict: adding text directives to user messages makes the model
overthink (+3.8× tokens, +2.3× wall). The fix: don't TELL the model what
to do — REMOVE the tools it shouldn't use.

Mechanism (deterministic, fail-open, zero prompt overhead):

1. PHASE DETECTION: Tracks conversation phase (discovery → implementation →
   verification) by counting tool call classes in the history.

2. TOOL FILTERING: Removes tools from the `tools` list based on phase:
   - Discovery: keep read/search tools only
   - Implementation: keep write/execute tools only
   - Verification: keep execute tools only

3. LOOP BREAKER: If the model calls the same tool class 5+ times in a row,
   remove that class from the available tools (force a behavior change).

This approach is aligned with When2Tool (2605.09252) which shows models
already know when to skip tools — the problem is they HAVE too many options.
Reducing the option set is more effective than adding instructions.

Env knobs:
    HILO_TOOL_GATE_V2_ENABLED (default 1) — master switch.
    HILO_TOOL_GATE_V2_LOOP_LIMIT (default 5) — same-class call limit.
"""

import os

_INJECTED = False
_CALL_HISTORY = []  # list of (tool_class, tool_name) tuples this session
_PHASE = "discovery"  # current phase


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
    return _env_flag("HILO_TOOL_GATE_V2_ENABLED", True)


def reset_state():
    """Reset for a new task/session."""
    global _INJECTED, _PHASE
    _INJECTED = False
    _PHASE = "discovery"
    _CALL_HISTORY.clear()


# --- Tool classification ---

# Tool name → class mapping
TOOL_CLASSES = {
    "read_files": "read",
    "list_directory": "read",
    "glob": "read",
    "code_search": "search",
    "web_search": "search",
    "read_url": "search",
    "write_file": "write",
    "str_replace": "write",
    "run_terminal_command": "execute",
    "skill": "load",
    "ask_user": "interact",
    "suggest_followups": "interact",
    "render_ui": "interact",
    "gravity_index": "search",
}

# Phase → allowed tool classes
PHASE_FILTERS = {
    "discovery": {"read", "search", "load", "interact"},
    "implementation": {"write", "execute", "read", "search", "load", "interact"},
    "verification": {"execute", "read", "search", "load", "interact"},
}

# Phase detection thresholds (by assistant turn count)
PHASE_THRESHOLDS = [
    (3, "discovery"),     # turns 0-2: discovery
    (8, "implementation"), # turns 3-7: implementation
    (999, "verification"), # turns 8+: verification
]


def classify_tool(tool_name):
    """Map a tool name to its class."""
    return TOOL_CLASSES.get(tool_name, "other")


def _detect_phase():
    """Detect current phase from call history."""
    global _PHASE

    call_count = len(_CALL_HISTORY)

    for threshold, phase in PHASE_THRESHOLDS:
        if call_count < threshold:
            if _PHASE != phase:
                _PHASE = phase
            return phase

    _PHASE = "verification"
    return _PHASE


def _check_loop():
    """Check if the model is looping on the same tool class.

    Returns (is_looping: bool, loop_class: str).
    """
    limit = _env_int("HILO_TOOL_GATE_V2_LOOP_LIMIT", 5)
    if len(_CALL_HISTORY) < limit:
        return False, ""

    tail = _CALL_HISTORY[-limit:]
    classes = [c for c, _ in tail]
    if len(set(classes)) == 1:
        return True, classes[0]

    return False, ""


def record_tool_call(tool_name):
    """Record a tool call for tracking."""
    _CALL_HISTORY.append((classify_tool(tool_name), tool_name))


def _filter_tools(request):
    """Filter tools from the request based on phase and loop detection.

    Returns (filtered_tools: list or None, reason: str).
    None means no filtering was needed (fail-open).
    """
    if not isinstance(request, dict):
        return None, "not a dict"
    tools = request.get("tools")
    if not isinstance(tools, list) or not tools:
        return None, "no tools in request"

    # Detect phase
    phase = _detect_phase()
    allowed = PHASE_FILTERS.get(phase, set())

    # Check for loop — if looping, remove the looping class
    is_looping, loop_class = _check_loop()
    if is_looping and loop_class in allowed:
        allowed = allowed - {loop_class}
        reason = f"phase={phase}, loop-break: removed {loop_class}"
    else:
        reason = f"phase={phase}, allowed={sorted(allowed)}"

    # Filter tools
    filtered = []
    removed = []
    for t in tools:
        name = t.get("function", {}).get("name", "") if isinstance(t, dict) else ""
        cls = classify_tool(name)
        if cls in allowed or cls == "other":  # unknown tools pass through
            filtered.append(t)
        else:
            removed.append(f"{name}({cls})")

    if not removed:
        return None, reason + " — no tools removed"

    return filtered, f"{reason}; removed: {removed}"


def register(ctx):
    """Register the llm_request middleware."""
    def _middleware(**kwargs):
        try:
            req = kwargs.get("request")
            if not isinstance(req, dict):
                return None

            request = dict(req)
            filtered, reason = _filter_tools(request)

            if filtered is not None:
                request["tools"] = filtered
                return {
                    "request": request,
                    "source": "tool-gate-v2",
                    "reason": reason,
                }

            return None  # fail-open: untouched
        except Exception:
            return None  # absolute fail-open

    ctx.register_middleware("llm_request", _middleware)
