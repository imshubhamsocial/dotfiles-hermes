#!/usr/bin/env python3
"""Demo plugin pre-commit hook: delegates to demo_validator AST and syntax validation."""
from pathlib import Path
from plugins.demo_validator import validate_artifact


def run(context: dict) -> dict:
    filepath = context.get("filepath", "")
    if not filepath:
        return {"ok": True, "detail": "No filepath provided."}

    path = Path(filepath)
    suffix = path.suffix.lower()

    if suffix in (".html", ".htm", ".js", ".ts", ".jsx", ".tsx"):
        res = validate_artifact(path)
        return {
            "ok": res["passed"],
            "detail": res["message"],
            "checks": res.get("checks", []),
        }

    return {"ok": True, "detail": f"Pass-through for {suffix}."}
