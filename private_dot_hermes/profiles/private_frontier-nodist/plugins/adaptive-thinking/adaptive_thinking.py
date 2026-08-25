"""adaptive_thinking.py — e26 adaptive per-request thinking middleware.

Canonical repo source. Installed (synced) into the lever profiles'
plugins dirs by bin/sync_lever_plugins.sh — the live copies live at
~/.hermes/profiles/{lever-thinking,frontier-stack}/plugins/adaptive_thinking.py.

Policy (v1 + Batch-I F-7, deterministic + fail-open; Hermes llm_request
middleware, schema hermes.middleware.v1 — docs/middleware/README.md):

- DEFAULT: thinking ON at the step-appropriate budget (1024, e24's setting).
- RETRIES (the prompt carries a human-correction turn / "did not satisfy"):
  thinking ALWAYS ON at the HIGH budget (4096) — corrections are hard steps.
- POST-TOOL / INTERLEAVED THINKING (Batch-I F-7, WIRE #2): if the request's
  LAST message is a tool result, force thinking ON at the HIGH budget (4096)
  — the model gets a dedicated <think> block to parse raw tool output
  (grep/compiler errors) before planning its next action. Pure append =
  prefix-cache-preserving. (GDR run-1 Lever 7: high EV at 4B, low risk.)
- MECHANICAL turns (post-tool verification, small edits, simple format
  fixes, lint/test re-runs): thinking OFF (enable_thinking=false) — the
  e24-vs-e20 data: thinking HURT the R2-F5-class mechanical step (1->2 att).
- Env override: HILO_THINKING_POLICY=on|off|auto (default auto).

The llama.cpp backend (e24 server config) honors per-request thinking via
extra_body.chat_template_kwargs.enable_thinking + reasoning_budget_tokens
(verified server-common.cpp:1073-1138). Server MUST run --reasoning on (e24
config) — per-request OFF works, per-request ON cannot override an OFF server.
"""

import os

MECHANICAL = (
    "fix typo", "rename ", "format ", "lint", "rerun", "re-run",
    "run the test", "missing exclamation", "add a comment", "verify the diff",
    "print the", "change the string", "syntax error", "typo",
)
HARD = (
    "debug", "refactor", "integrat", "design", "plan", "pipeline",
    "multi-file", "prorate", "round", "migration", "architecture",
    "compose", "orchestrat",
)
RETRY = ("did not satisfy", "[developer]", "still ", "again", "rework", "attempt ")

# Tool-result markers across transports (OpenAI role="tool", or a user/assistant
# message carrying a tool_result block).
_TOOL_RESULT_MARKERS = ("<tool_result>", "[tool_result]", "tool_call_id", "tool result:")


def register(ctx):
    ctx.register_middleware("llm_request", adaptive_thinking)


def _is_post_tool(messages):
    """True when the request's last message is a tool result (F-7 interleaved)."""
    if not messages:
        return False
    last = messages[-1]
    if not isinstance(last, dict):
        return False
    role = last.get("role")
    if role == "tool":
        return True
    if role in ("user", "assistant"):
        c = last.get("content")
        if isinstance(c, str) and any(m in c for m in _TOOL_RESULT_MARKERS):
            return True
    return False


def adaptive_thinking(**kwargs):
    try:
        req = kwargs.get("request")
        if not isinstance(req, dict):
            return None  # fail-open: never touch a malformed request
        request = dict(req)
        policy = os.environ.get("HILO_THINKING_POLICY", "auto").lower()
        if policy == "off":
            return _emit(request, False, 0, "policy=off")
        if policy == "on":
            return _emit(request, True, 1024, "policy=on")
        # classify from the LAST user message
        messages = request.get("messages") or []
        if _is_post_tool(messages):
            return _emit(request, True, 4096, "post-tool -> interleaved thinking high")
        tail = ""
        for msg in reversed(messages):
            if isinstance(msg, dict) and msg.get("role") in ("user", "developer"):
                c = msg.get("content")
                tail = c if isinstance(c, str) else str(c)
                break
        low = tail.lower()
        is_retry = any(k in low for k in RETRY)
        if is_retry:
            return _emit(request, True, 4096, "retry -> thinking high")
        if any(k in low for k in MECHANICAL):
            return _emit(request, False, 0, "mechanical -> thinking off")
        if any(k in low for k in HARD):
            return _emit(request, True, 4096, "hard step -> thinking high")
        return _emit(request, True, 1024, "default -> thinking medium")
    except Exception:
        return None  # fail-open: unchanged request


def _emit(request, enable, budget, reason):
    extra = dict(request.get("extra_body") or {})
    kw = dict(extra.get("chat_template_kwargs") or {})
    kw["enable_thinking"] = enable
    if budget > 0:
        extra["reasoning_budget_tokens"] = budget
    extra["chat_template_kwargs"] = kw
    request["extra_body"] = extra
    return {"request": request, "source": "adaptive-thinking", "reason": reason}
