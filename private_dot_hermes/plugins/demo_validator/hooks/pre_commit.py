#!/usr/bin/env python3
"""Demo plugin pre-commit hook: validates syntax before disk write."""
import ast
from pathlib import Path


def run(context: dict) -> dict:
    filepath = context.get("filepath", "")
    content = context.get("content", "")
    suffix = Path(filepath).suffix.lower()

    if suffix == ".py":
        try:
            ast.parse(content)
            return {"ok": True, "detail": "Python syntax valid."}
        except SyntaxError as e:
            return {"ok": False, "detail": f"Python SyntaxError at line {e.lineno}: {e.msg}"}

    return {"ok": True, "detail": f"No syntax probe for {suffix} (pass-through)."}
