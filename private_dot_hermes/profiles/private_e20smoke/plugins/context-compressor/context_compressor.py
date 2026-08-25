"""context_compressor.py — #4e2 + #4j Enhanced context-token reduction.

Combines Meta-Harness (2603.28052) + SWE-Pruner Pro (2607.18213) insights.
Reduces per-call token count by compressing old conversation turns and
pruning tool outputs to keep only decision-relevant content.

What it does (deterministic, no LLM in the loop):
1. IDENTIFIES compressible turns: old tool results, completed file reads,
   intermediate reasoning blocks, repeated context.
2. PER-TOOL-OUTPUT PRUNING (#4j): Keeps first 3 + last 3 lines of tool
   outputs (most-referenced content per SWE-Pruner Pro finding that 70%+
   of tokens are tool outputs). Approximates hidden-state importance by
   keeping structural anchors (start/end) and any error lines.
3. MEMORY-BANK COMPACTION (#4j): For memory-bank entries, only keeps
   entries whose keywords match the current task (top-3 by relevance).
4. SMARTER SUMMARIES: Preserves error details, file paths, and line numbers
   — the information the model needs for correction cycles.
5. PRESERVES: system prompt, recent N turns, all assistant responses with
   tool calls (the decision chain).

Env knobs:
    HILO_CONTEXT_COMPRESS_ENABLED (default 1)
    HILO_CONTEXT_COMPRESS_KEEP_RECENT (default 4 — preserve last N turn pairs)
    HILO_CONTEXT_COMPRESS_MAX_CHARS (default 500 — max chars per summary)
    HILO_CONTEXT_COMPRESS_PRUNE_TOOL_OUTPUTS (default 1 — #4j pruning)
    HILO_CONTEXT_COMPRESS_PRUNE_KEEP_LINES (default 6 — first N + last N)
    HILO_CONTEXT_COMPRESS_MEMORY_BANK (default 0 — enable memory-bank compaction)
"""

import os
import re
from collections import Counter

_INJECTED = False


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


# --- Detection helpers ---

def _is_tool_result(message):
    """Check if a message is a tool result (role=tool or contains tool output)."""
    if not isinstance(message, dict):
        return False
    role = message.get("role", "")
    if role == "tool":
        return True
    content = message.get("content", "")
    if isinstance(content, str) and role == "user":
        if "<tool_call>" in content or "tool_result" in content.lower():
            return True
    return False


def _is_reasoning_block(content):
    """Check if content contains <think>...</think> blocks."""
    if not isinstance(content, str):
        return False
    return "<think>" in content and "</think>" in content


def _is_error_content(content):
    """Check if content contains error indicators."""
    if not isinstance(content, str):
        return False
    return any(kw in content.lower() for kw in [
        "error", "failed", "exception", "traceback", "errno",
        "exit code", "return code", "panic", "abort",
    ])


# --- Compression functions (existing, enhanced) ---

def _compress_tool_result(content, max_chars=500):
    """Compress a tool result to a structured summary."""
    if not isinstance(content, str):
        return content

    tool_match = re.search(r'(?:tool_call|function|name)["\s:]+(\w+)', content[:200])
    tool_name = tool_match.group(1) if tool_match else "unknown"
    is_error = _is_error_content(content)
    status = "ERROR" if is_error else "OK"

    # For errors, preserve the error message (critical for correction cycles)
    if is_error:
        error_lines = [l.strip() for l in content.split('\n')
                       if any(kw in l.lower() for kw in ['error', 'traceback', 'exception', 'errno'])]
        key_content = ' | '.join(error_lines[:3])[:200] if error_lines else ""
    else:
        lines = [l.strip() for l in content.split('\n')
                 if l.strip() and not l.strip().startswith('```')]
        key_content = ' '.join(lines[:3])[:200] if lines else ""

    summary = f"[TOOL: {tool_name}, {status}, {len(content)} chars"
    if key_content:
        summary += f" — {key_content}"
    summary += "]"

    if len(summary) > max_chars:
        summary = summary[:max_chars - 3] + "..."
    return summary


def _compress_file_read(content, max_chars=500):
    """Compress a file read result to a structured summary."""
    if not isinstance(content, str):
        return content

    path_match = re.search(r'(?:file|path)["\s:]+([^\s"]+)', content[:300])
    path = path_match.group(1) if path_match else "unknown"

    lines = content.split('\n')
    line_count = len(lines)

    meaningful = [l.strip() for l in lines[:10] if l.strip() and not l.strip().startswith('#')]
    key_content = ' '.join(meaningful[:3])[:150] if meaningful else ""

    summary = f"[FILE: {path}, {line_count} lines"
    if key_content:
        summary += f" — {key_content}"
    summary += "]"

    if len(summary) > max_chars:
        summary = summary[:max_chars - 3] + "..."
    return summary


def _compress_reasoning(content, max_chars=500):
    """Compress <think> blocks to a summary preserving the conclusion."""
    if not isinstance(content, str):
        return content

    think_match = re.search(r'<think>(.*?)</think>', content, re.DOTALL)
    if not think_match:
        return content

    reasoning = think_match.group(1).strip()
    sentences = [s.strip() for s in re.split(r'[.!?]+', reasoning) if s.strip()]
    conclusion = '. '.join(sentences[-2:]) if len(sentences) > 2 else reasoning[:200]

    summary = f"[REASONING: {len(reasoning)} chars — {conclusion}]"
    if len(summary) > max_chars:
        summary = summary[:max_chars - 3] + "..."
    return summary


# --- #4j: Per-tool-output pruning ---

def _prune_tool_output(content, keep_lines=6):
    """Prune a tool output to keep only the most important lines.

    Strategy (SWE-Pruner Pro approximation without hidden states):
    - Keep first 3 lines (headers, context, start of output)
    - Keep last 3 lines (results, summary, error tail)
    - Always keep error/exception lines (critical for correction)
    - Always keep lines with file paths or line numbers
    - Drop the middle (often verbose grep output, repeated content)
    """
    if not content or not isinstance(content, str):
        return content

    lines = content.split('\n')
    if len(lines) <= keep_lines:
        return content  # Already short enough

    half = keep_lines // 2
    first = lines[:half]
    last = lines[-half:]

    # Collect "important" middle lines (errors, paths, line numbers)
    important_middle = []
    for line in lines[half:-half]:
        stripped = line.strip()
        if not stripped:
            continue
        # Always keep error lines
        if _is_error_content(stripped):
            important_middle.append(line)
            continue
        # Keep lines with file paths or line numbers
        if re.search(r'[^/]\:\d+', stripped) or re.search(r'[/\\]\w+\.\w+', stripped):
            important_middle.append(line)
            continue
        # Keep lines with key patterns (assert, return, class, def)
        if re.match(r'\s*(assert|return|class|def|import|from|if|for|while)\b', stripped):
            important_middle.append(line)

    # Cap middle lines to keep output bounded
    max_middle = max(3, keep_lines)
    if len(important_middle) > max_middle:
        # Keep first and last of the important middle
        important_middle = important_middle[:2] + ['...'] + important_middle[-2:]

    pruned = first + important_middle + last
    return '\n'.join(pruned)


# --- #4j: Memory-bank compaction ---

def _extract_task_keywords(text):
    """Extract keywords from the current task for memory-bank relevance matching."""
    if not text or not isinstance(text, str):
        return set()

    # Extract significant words (>= 4 chars, not stopwords)
    stopwords = {
        'this', 'that', 'with', 'from', 'have', 'been', 'were', 'they',
        'their', 'which', 'about', 'would', 'could', 'should', 'will',
        'into', 'also', 'when', 'what', 'your', 'some', 'than', 'then',
        'them', 'each', 'make', 'like', 'just', 'over', 'such', 'after',
        'only', 'very', 'most', 'does', 'done', 'more', 'file', 'code',
        'tool', 'call', 'file', 'read', 'show', 'test', 'help',
    }
    words = set(re.findall(r'\b[a-z]{4,}\b', text.lower()))
    return words - stopwords


def _score_entry_relevance(entry_text, task_keywords):
    """Score how relevant a memory-bank entry is to the current task."""
    if not entry_text or not task_keywords:
        return 0

    entry_words = set(re.findall(r'\b[a-z]{4,}\b', entry_text.lower()))
    overlap = entry_words & task_keywords
    return len(overlap)


def _compact_memory_bank(content, task_keywords, max_entries=3):
    """Compact memory-bank content to only the most relevant entries.

    Memory-bank entries are typically separated by '---' or '##' headers.
    We score each entry by keyword overlap with the current task and keep
    only the top-N most relevant.
    """
    if not content or not isinstance(content, str) or not task_keywords:
        return content

    # Split into entries (by --- or ## headers)
    entries = re.split(r'\n---\n|(?=^## )', content, flags=re.MULTILINE)
    entries = [e.strip() for e in entries if e.strip()]

    if len(entries) <= max_entries:
        return content  # Already compact enough

    # Score and rank
    scored = [(_score_entry_relevance(e, task_keywords), e) for e in entries]
    scored.sort(key=lambda x: x[0], reverse=True)

    # Keep top entries
    kept = [e for _, e in scored[:max_entries]]
    return '\n\n---\n\n'.join(kept)


# --- Core compression logic ---

def _should_compress(message, turn_index, keep_recent):
    """Determine if a message should be compressed."""
    if not isinstance(message, dict):
        return False

    role = message.get("role", "")

    if role == "system":
        return False

    if turn_index >= -keep_recent:
        return False

    if _is_tool_result(message):
        return True

    if role == "assistant":
        content = message.get("content", "")
        if isinstance(content, str) and _is_reasoning_block(content):
            return True

    if role == "user":
        content = message.get("content", "")
        if isinstance(content, str) and len(content) > 1000:
            return True

    return False


def _compress_message(message, max_chars, prune_tool_outputs, keep_lines):
    """Compress a single message's content."""
    if not isinstance(message, dict):
        return message

    content = message.get("content", "")
    if not isinstance(content, str):
        return message

    role = message.get("role", "")

    if _is_tool_result(message):
        if prune_tool_outputs and len(content) > max_chars:
            # First prune, then summarize if still too long
            pruned = _prune_tool_output(content, keep_lines)
            if len(pruned) > max_chars:
                message["content"] = _compress_tool_result(pruned, max_chars)
            else:
                message["content"] = pruned
        else:
            message["content"] = _compress_tool_result(content, max_chars)
    elif role == "user" and len(content) > 1000:
        message["content"] = _compress_file_read(content, max_chars)
    elif role == "assistant" and _is_reasoning_block(content):
        message["content"] = _compress_reasoning(content, max_chars)

    return message


# --- Middleware entry point ---

def llm_request(request, context=None):
    """Middleware: compress old conversation turns to reduce tokens/call.

    Fail-open: if anything goes wrong, return the request unchanged.
    """
    global _INJECTED

    if not _env_flag("HILO_CONTEXT_COMPRESS_ENABLED"):
        return request

    if _INJECTED:
        return request

    try:
        messages = (request.get("request") or {}).get("messages") or request.get("messages") or []
        if not isinstance(messages, list) or len(messages) < 6:
            return request

        keep_recent = _env_int("HILO_CONTEXT_COMPRESS_KEEP_RECENT", 4)
        max_chars = _env_int("HILO_CONTEXT_COMPRESS_MAX_CHARS", 500)
        prune_tool_outputs = _env_flag("HILO_CONTEXT_COMPRESS_PRUNE_TOOL_OUTPUTS", True)
        keep_lines = _env_int("HILO_CONTEXT_COMPRESS_PRUNE_KEEP_LINES", 6)

        compressed_count = 0
        for i, msg in enumerate(messages):
            if _should_compress(msg, i - len(messages), keep_recent):
                original_len = len(str(msg.get("content", "")))
                _compress_message(msg, max_chars, prune_tool_outputs, keep_lines)
                new_len = len(str(msg.get("content", "")))
                if new_len < original_len:
                    compressed_count += 1

        if compressed_count > 0:
            _INJECTED = True

    except Exception:
        pass  # fail-open: never break the request path

    return request


def register(ctx):
    """Register the llm_request middleware under the hermes.v1 contract."""
    def _middleware(**kwargs):
        try:
            req = kwargs.get("request")
            if not isinstance(req, dict):
                return None
            result = llm_request(req)
            if result is not req:
                return {"request": result, "source": "context-compressor", "reason": "compressed"}
            return None
        except Exception:
            return None  # absolute fail-open
    ctx.register_middleware("llm_request", _middleware)


def reset_state():
    """Reset the injection flag (for testing or new task)."""
    global _INJECTED
    _INJECTED = False
