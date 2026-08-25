"""frontier_levers.py — Batch-I wired levers F-2 / F-6 / F-8 (Hermes middleware).

Canonical repo source. Installed (synced) into the lever profiles' plugins
dirs by bin/sync_lever_plugins.sh — live copies at
~/.hermes/profiles/{lever-thinking,frontier-stack}/plugins/frontier_levers.py.

Implements the Batch-I run-1 verdicts (BATCH_I_ANALYSIS_2026-08-13.md §4 —
WIRE F-2 / F-6 / F-8; the sibling plugin adaptive_thinking.py owns F-7). All
hooks are llm_request middleware (schema hermes.middleware.v1), fail-open,
deterministic, and CACHE-SAFE: they only (a) append to the FIRST-request
system message (becomes part of the cached prefix) or (b) append to the LAST
user/developer message (which is new content every turn) — they NEVER mutate
historical turns (the exact-byte llama.cpp prefix cache must survive).

- F-2 task_budget pacing (WIRE #3): trailing
  "[System: Task budget — ~X of Y seconds remain …]" suffix on the current
  user message. Budget from HILO_BUDGET_STATE_FILE (authoritative,
  driver-written JSON {"total_s", "remaining_s"}) else elapsed-since-first-
  request vs HILO_TASK_BUDGET_S (default 2400 = e24 ceiling).
- F-6 Wait! halt-and-re-verify (WIRE #1): (a) on request #1, append the
  halt-and-re-verify directive to the system message (the s1 doubt-token made
  4B-appropriate — GDR: Qwen arch is highly responsive to injected doubt);
  (b) when the PREVIOUS assistant turn ended terminal-short (final answer,
  no tool call, short text) and budget remains, append a "Wait, let me
  check…" continuation directive to the current prompt, capped
  HILO_WAIT_MAX_PER_TURN (default 3). This is the Hermes-native approximation
  of mid-stream budget forcing: Hermes' llm_execution next_call is single-use
  (middleware.py _DownstreamExecutionError), so true stream interception is
  engine-internal — the doubt-token instead lands at the start of the model's
  next reasoning pass, which is the mechanism s1 exploits.
- F-8 anti-early-stop (WIRE, paired w/ F-2): when ample budget remains
  (>= 50 % of total) AND the conversation is long (>= 12 messages), append
  the continuation reassurance line to the current user message — kills the
  4B sycophancy failure ("session getting long, want me to summarize?").
  Only fires when F-2's budget state says time genuinely remains.

Env knobs (all default ON in the lever profiles; off = fail-open no-op):
HILO_TASK_BUDGET_ENABLED (default 1) · HILO_WAIT_ENABLED (default 1) ·
HILO_ANTI_EARLY_STOP_ENABLED (default 1) · HILO_TASK_BUDGET_S (default 2400)
· HILO_BUDGET_STATE_FILE (driver-written JSON, authoritative when fresh) ·
HILO_WAIT_MAX_PER_TURN (default 3).
"""

import json
import os
import time

_SYSTEM_LINE = (
    '\n\n[Constraint: Before finalizing any tool call or file write, explicitly '
    'halt and re-verify: "Wait, let me check..." against the available evidence '
    '(exit codes, diffs, schemas). Only then commit.]'
)
_WAIT_DIRECTIVE = (
    '\n\n[System: Wait — the previous step concluded without a verified result. '
    'Explicitly halt, re-verify the last step\'s evidence (exit codes, diffs, '
    'schemas), and only then continue. Do not repeat the previous approach '
    'blindly.]'
)
_ANTI_EARLY_STOP_LINE = (
    '\n\n[System: You have ample context remaining. Do not stop, summarize, or '
    'suggest a new session on account of context limits. Continue the work.]'
)

_SHORT_ANSWER_CHARS = 200       # terminal answers below this = "premature" candidates
_LONG_CONVERSATION_MESSAGES = 12
_AMPlE_BUDGET_FRACTION = 0.5

_START = time.monotonic()
_SYSTEM_LINE_INJECTED = False
_WAIT_COUNTS = {}               # turn_id -> injections this turn (cap)


def register(ctx):
    ctx.register_middleware("llm_request", frontier_request)


def _env_flag(name, default=True):
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() not in ("0", "false", "off", "no")


def _budget_state():
    """(total_s, remaining_s) — driver state file wins, else elapsed-based."""
    total = float(os.environ.get("HILO_TASK_BUDGET_S", "2400") or 2400)
    remaining = total
    path = os.environ.get("HILO_BUDGET_STATE_FILE")
    if path:
        try:
            if os.path.getmtime(path) > time.time() - 300:  # fresh (< 5 min)
                d = json.load(open(path, encoding="utf-8"))
                total = float(d.get("total_s", total))
                remaining = float(d.get("remaining_s", remaining))
                return total, remaining
        except Exception:
            pass
    remaining = max(0.0, total - (time.monotonic() - _START))
    return total, remaining


def _append_text(content, suffix):
    """Append a text suffix to a message content (str or parts-list), cache-safe."""
    if content is None:
        return suffix
    if isinstance(content, str):
        return content + suffix
    if isinstance(content, list):
        # OpenAI-style parts list: append a text part when it looks compatible
        try:
            return list(content) + [{"type": "text", "text": suffix.lstrip("\n")}]
        except Exception:
            return content
    return content  # fail-open: unknown content shape, leave untouched


def _last_user_message_index(messages):
    for i in range(len(messages) - 1, -1, -1):
        m = messages[i]
        if isinstance(m, dict) and m.get("role") in ("user", "developer"):
            return i
    return -1


def _previous_assistant_terminal_short(messages, user_idx):
    """True when the assistant turn right before the current prompt was a
    terminal-short final answer (no tool call, short text) — an F-6
    premature-conclusion candidate."""
    for i in range(user_idx - 1, -1, -1):
        m = messages[i]
        if not isinstance(m, dict):
            continue
        role = m.get("role")
        if role == "assistant":
            c = m.get("content")
            if not isinstance(c, str):
                return False
            tc = m.get("tool_calls")
            if tc:
                return False
            return len(c.strip()) < _SHORT_ANSWER_CHARS
        if role in ("user", "developer"):
            return False  # reached an earlier user turn boundary — not a chain
    return False


def _inject_system_line(request, reason_parts):
    global _SYSTEM_LINE_INJECTED
    if _SYSTEM_LINE_INJECTED:
        return
    messages = request.get("messages")
    if not isinstance(messages, list) or not messages:
        return
    first = messages[0]
    if not isinstance(first, dict) or first.get("role") not in ("system", "developer"):
        return  # fail-open: no system message to extend
    first["content"] = _append_text(first.get("content"), _SYSTEM_LINE)
    _SYSTEM_LINE_INJECTED = True
    reason_parts.append("F-6 system halt-and-re-verify line (request #1)")


def frontier_request(**kwargs):
    try:
        req = kwargs.get("request")
        if not isinstance(req, dict):
            return None
        request = dict(req)
        messages = request.get("messages")
        if not isinstance(messages, list) or not messages:
            return None

        reason_parts = []
        changed = False
        user_idx = _last_user_message_index(messages)
        total, remaining = _budget_state()

        # F-6 (a): halt-and-re-verify directive into the system message once
        if _env_flag("HILO_WAIT_ENABLED"):
            _inject_system_line(request, reason_parts)

        if user_idx >= 0:
            user_msg = messages[user_idx]

            # F-2: task_budget countdown suffix (WIRE #3)
            if _env_flag("HILO_TASK_BUDGET_ENABLED"):
                line = (
                    f"\n\n[System: Task budget — ~{int(remaining)} of "
                    f"{int(total)} seconds remain. Pace accordingly: if time is "
                    f"low, wrap up gracefully (finalize open edits, state what "
                    f"remains) instead of starting new work.]"
                )
                user_msg["content"] = _append_text(user_msg.get("content"), line)
                changed = True
                reason_parts.append(f"F-2 task-budget suffix ({int(remaining)}s left)")

            # F-6 (b): Wait! continuation directive on terminal-short retries
            if _env_flag("HILO_WAIT_ENABLED") and remaining > 0:
                turn_id = str(kwargs.get("turn_id") or "global")
                count = _WAIT_COUNTS.get(turn_id, 0)
                cap = int(os.environ.get("HILO_WAIT_MAX_PER_TURN", "3") or 3)
                if count < cap and _previous_assistant_terminal_short(messages, user_idx):
                    user_msg["content"] = _append_text(user_msg.get("content"), _WAIT_DIRECTIVE)
                    _WAIT_COUNTS[turn_id] = count + 1
                    changed = True
                    reason_parts.append(
                        f"F-6 Wait-directive (terminal-short prev turn, {count + 1}/{cap})"
                    )

            # F-8: anti-early-stop reassurance (only paired with F-2 budget state)
            if _env_flag("HILO_ANTI_EARLY_STOP_ENABLED") and remaining >= _AMPlE_BUDGET_FRACTION * total \
                    and len(messages) >= _LONG_CONVERSATION_MESSAGES:
                user_msg["content"] = _append_text(user_msg.get("content"), _ANTI_EARLY_STOP_LINE)
                changed = True
                reason_parts.append("F-8 anti-early-stop line (ample budget, long conv)")

        if not changed:
            return None  # fail-open: untouched
        return {
            "request": request,
            "source": "frontier-levers",
            "reason": "; ".join(reason_parts),
        }
    except Exception:
        return None  # fail-open: unchanged request
