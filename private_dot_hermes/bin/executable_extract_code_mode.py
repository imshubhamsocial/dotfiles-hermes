#!/usr/bin/env python3
"""
Code Mode Deterministic Extractor (U1 Trap-1 Countermeasure)
============================================================
4B SLMs wrap batch scripts in conversational prose ("Here is the script:")
and markdown fences, crashing direct interpreter execution with SyntaxError.

This module deterministically strips ALL prose and fence escapes and returns
interpreter-ready code. Zero heuristics beyond regex; zero LLM involvement.

Verification contract (roadmap 1.1 Trap 1):
  Feed N raw model outputs containing mixed markdown/prose fences;
  assert 100% clean AST parsing with zero unstripped fence escapes.
"""

import ast
import re
import sys

_FENCE_RE = re.compile(r"^[ \t]*(?:```+|~~~+)[ \t]*[a-zA-Z0-9_-]*[ \t]*\r?\n", re.MULTILINE)
_CLOSE_RE = re.compile(r"^[ \t]*(?:```+|~~~+)[ \t]*\r?\n?$", re.MULTILINE)
_PROSE_PREFIX_RE = re.compile(
    r"^\s*(?:here(?:'s| is)[^\n:]*:|sure[^\n:]*:|below[^\n:]*:|this script[^\n:]*:|"
    r"(?:i'll|i will)[^\n:]*:|note[^\n:]*:)\s*\r?\n?",
    re.IGNORECASE,
)


def _unescape_fences(code: str) -> str:
    """Unescape escaped-backtick artifacts models emit inside fenced blocks."""
    code = code.replace("\\`\\`\\`", "```")
    code = code.replace("\\u0060", "`").replace("\\`", "`")
    return code


def extract_code(raw: str) -> str:
    """Strip conversational prose + markdown fences; return pure executable code."""
    text = raw.strip()

    # 1. Pull fenced bodies if any fences exist anywhere in the output.
    if "```" in text or "~~~" in text:
        # Find all fenced code blocks
        blocks = re.findall(r"(?:```+|~~~+)[ \t]*[a-zA-Z0-9_-]*\r?\n(.*?)\r?\n(?:```+|~~~+)", text, re.DOTALL)
        if not blocks:
            # Handle open-ended fence at end of generation
            blocks = re.findall(r"(?:```+|~~~+)[ \t]*[a-zA-Z0-9_-]*\r?\n(.*)", text, re.DOTALL)

        code_chunks = []
        for block in blocks:
            candidate = _unescape_fences(block).strip()
            if candidate:
                code_chunks.append(candidate)

        if not code_chunks:
            raise ValueError("extract_code: fenced output contained no parsable code body")
        return "\n\n".join(code_chunks)

    # 2. Unfenced: strip leading prose lines / conversational prefixes.
    text = _PROSE_PREFIX_RE.sub("", text)
    lines = text.splitlines()
    code_lines = []
    for ln in lines:
        stripped = ln.strip()
        if (
            not stripped
            or stripped.startswith(("```", "~~~"))
            or re.match(r"^(?:this|the) (?:script|code|program)", stripped, re.IGNORECASE)
            or (ln == lines[0] and stripped.endswith(":") and not stripped[-2:-1].isalnum())
        ):
            continue
        code_lines.append(ln)

    body = _unescape_fences("\n".join(code_lines)).strip()
    if not body:
        raise ValueError("extract_code: no code found after prose stripping")
    return body


def extract_code_validated(raw: str) -> str:
    """Extract then hard-verify Python AST parseability. Raises on any pollution."""
    body = extract_code(raw)
    # Fence escapes / line-start fences are fatal; backticks INSIDE string
    # literals are valid Python and must not false-positive.
    if re.search(r"^[ \t]*(?:```+|~~~+)", body, re.MULTILINE) or "\\`" in body or "\\u0060" in body or "\x00" in body:
        raise ValueError("extract_code: unstripped fence escape survived extraction")
    try:
        ast.parse(body)
    except SyntaxError as e:
        raise ValueError(f"extract_code: extracted code failed AST parse at line {e.lineno}: {e.msg}") from e
    return body


def main():
    src = sys.stdin.read() if len(sys.argv) < 2 else open(sys.argv[1], encoding="utf-8", errors="replace").read()
    try:
        print(extract_code_validated(src))
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
