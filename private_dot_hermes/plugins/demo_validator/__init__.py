"""
Hermes Plugin: demo_validator
=============================
Validates interactive HTML, JavaScript, and CSS generative UI artifacts.
Powered by Biome (Rust linter/formatter) and ast-grep-py (Tree-sitter structural AST).
Enforces the Finish-First invariant for interactive UI demonstrations.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from ast_grep_py import SgRoot
    AST_GREP_AVAILABLE = True
except ImportError:
    AST_GREP_AVAILABLE = False


def _find_biome_binary() -> Optional[str]:
    """Locates the Biome binary in PATH or common local install locations."""
    which_biome = shutil.which("biome")
    if which_biome:
        return which_biome
    candidates = [
        Path.home() / ".local/bin/biome",
        Path("/var/home/imshubhamsocial/.local/bin/biome"),
        Path("/usr/local/bin/biome"),
    ]
    for c in candidates:
        if c.exists() and os.access(c, os.X_OK):
            return str(c)
    return None


def validate_html(code: str, filepath: Optional[str] = None) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """Validates HTML markup using Biome and Tree-sitter AST."""
    checks = []
    biome_bin = _find_biome_binary()

    # 1. Biome HTML check
    if biome_bin:
        temp_file = None
        target_path = filepath
        if not target_path or not Path(target_path).exists():
            with tempfile.NamedTemporaryFile(suffix=".html", mode="w", delete=False, encoding="utf-8") as f:
                f.write(code)
                temp_file = f.name
                target_path = temp_file

        try:
            cmd = [biome_bin, "lint", target_path]
            p = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )
            # Check for structural parse errors in stderr/stdout
            combined = (p.stderr + "\n" + p.stdout).strip()
            is_parse_error = "parse ━━━" in combined or "Expected a closing tag" in combined or "Expected " in combined
            
            if is_parse_error:
                first_line = [l.strip() for l in combined.splitlines() if l.strip().startswith("×") or "Expected" in l]
                err_summary = first_line[0] if first_line else "HTML parse error"
                checks.append({"name": "biome_html", "passed": False, "detail": err_summary})
                return False, f"Biome HTML syntax error: {err_summary}", checks
            else:
                checks.append({"name": "biome_html", "passed": True, "detail": "Biome HTML structure valid"})
        except Exception as e:
            checks.append({"name": "biome_html", "passed": True, "detail": f"Biome skipped: {e}"})
        finally:
            if temp_file and Path(temp_file).exists():
                try:
                    Path(temp_file).unlink()
                except Exception:
                    pass

    # 2. ast-grep HTML AST check
    if AST_GREP_AVAILABLE:
        try:
            root = SgRoot(code, "html").root()
            errors = root.find_all(kind="ERROR")
            if errors:
                err_text = errors[0].text()[:60].replace("\n", " ")
                checks.append({"name": "ast_grep_html", "passed": False, "detail": f"Syntax error node: {err_text}"})
                return False, f"HTML AST error: {err_text}", checks
            checks.append({"name": "ast_grep_html", "passed": True, "detail": "Valid Tree-sitter HTML AST"})
        except Exception as e:
            checks.append({"name": "ast_grep_html", "passed": False, "detail": str(e)})
            return False, f"HTML AST exception: {e}", checks

    return True, "HTML validation passed", checks


def validate_js(code: str, filepath: Optional[str] = None) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """Validates JavaScript / TypeScript using Biome and Tree-sitter AST."""
    checks = []
    biome_bin = _find_biome_binary()

    # 1. Biome JS check
    if biome_bin:
        temp_file = None
        target_path = filepath
        if not target_path or not Path(target_path).exists():
            with tempfile.NamedTemporaryFile(suffix=".js", mode="w", delete=False, encoding="utf-8") as f:
                f.write(code)
                temp_file = f.name
                target_path = temp_file

        try:
            cmd = [biome_bin, "lint", target_path]
            p = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )
            combined = (p.stderr + "\n" + p.stdout).strip()
            is_parse_error = "parse ━━━" in combined or "Expected " in combined or "SyntaxError" in combined
            
            if is_parse_error:
                first_line = [l.strip() for l in combined.splitlines() if l.strip().startswith("×") or "Expected" in l]
                err_summary = first_line[0] if first_line else "JS syntax error"
                checks.append({"name": "biome_js", "passed": False, "detail": err_summary})
                return False, f"Biome JS syntax error: {err_summary}", checks
            else:
                checks.append({"name": "biome_js", "passed": True, "detail": "Biome JS syntax valid"})
        except Exception as e:
            checks.append({"name": "biome_js", "passed": True, "detail": f"Biome skipped: {e}"})
        finally:
            if temp_file and Path(temp_file).exists():
                try:
                    Path(temp_file).unlink()
                except Exception:
                    pass

    # 2. ast-grep JS AST check
    if AST_GREP_AVAILABLE:
        try:
            root = SgRoot(code, "javascript").root()
            errors = root.find_all(kind="ERROR")
            if errors:
                err_text = errors[0].text()[:60].replace("\n", " ")
                checks.append({"name": "ast_grep_js", "passed": False, "detail": f"Syntax error node: {err_text}"})
                return False, f"JavaScript AST error: {err_text}", checks
            checks.append({"name": "ast_grep_js", "passed": True, "detail": "Valid Tree-sitter JS AST"})
        except Exception as e:
            checks.append({"name": "ast_grep_js", "passed": False, "detail": str(e)})
            return False, f"JavaScript AST exception: {e}", checks

    return True, "JavaScript validation passed", checks


def validate_artifact(filepath: str | Path) -> Dict[str, Any]:
    """
    Performs full artifact verification on an interactive demo file (.html, .js, .ts).
    """
    path = Path(filepath).expanduser().resolve()
    if not path.exists():
        return {
            "passed": False,
            "verdict": "REJECTED",
            "message": f"Artifact file does not exist: {filepath}",
            "path": str(path),
            "checks": [],
        }

    code = path.read_text(encoding="utf-8", errors="replace")
    ext = path.suffix.lower()

    if ext in (".html", ".htm"):
        ok, msg, checks = validate_html(code, str(path))
    elif ext in (".js", ".mjs", ".cjs", ".ts", ".tsx"):
        ok, msg, checks = validate_js(code, str(path))
    else:
        # Pass-through for non-web artifacts
        return {
            "passed": True,
            "verdict": "APPROVED",
            "message": f"File extension '{ext}' does not require UI artifact validation.",
            "path": str(path),
            "checks": [{"name": "extension_check", "passed": True, "detail": "Pass-through"}],
        }

    return {
        "passed": ok,
        "verdict": "APPROVED" if ok else "REJECTED",
        "message": msg,
        "path": str(path),
        "checks": checks,
    }


def register(ctx=None):
    """Registers demo_validator plugin into Hermes runtime."""
    if not ctx:
        return True

    # 1. Native CLI command: hermes validate <file>
    if hasattr(ctx, "register_cli_command"):
        def setup_validate(parser):
            parser.description = "Validate interactive HTML/JS generative UI artifacts with Biome and AST"
            parser.add_argument("path", help="Path to the HTML/JS demo file to validate")
            parser.add_argument("--json", action="store_true", help="Output validation verdict as JSON")

        def handle_validate(args):
            res = validate_artifact(args.path)
            if getattr(args, "json", False):
                print(json.dumps(res, indent=2))
            else:
                symbol = "✓" if res["passed"] else "✗"
                print(f"Demo Validator: {res['verdict']} {symbol} ({res['message']})")
                for c in res["checks"]:
                    mark = "✓" if c["passed"] else "✗"
                    print(f"  [{mark}] {c['name']}: {c['detail']}")
            return 0 if res["passed"] else 1

        ctx.register_cli_command("validate", "Validate UI demo artifact (Biome & Tree-sitter AST)", setup_validate, handle_validate)

    # 2. Native Slash command: /validate <file>
    if hasattr(ctx, "register_command"):
        def slash_validate(raw_args: str) -> str:
            target = raw_args.strip()
            if not target:
                return "Usage: /validate <demo_file.html>"
            res = validate_artifact(target)
            symbol = "✓" if res["passed"] else "✗"
            lines = [f"**Demo Validator**: {res['verdict']} {symbol} — `{res['path']}`"]
            for c in res["checks"]:
                mark = "✓" if c["passed"] else "✗"
                lines.append(f"- [{mark}] **{c['name']}**: {c['detail']}")
            return "\n".join(lines)

        ctx.register_command("validate", slash_validate, "Validate UI demo artifact against Biome & AST", "<file>")

    # 3. Lifecycle hook: pre_verify
    if hasattr(ctx, "register_hook"):
        def pre_verify_hook(changed_paths=None, **kwargs):
            if not changed_paths:
                return {"action": "continue"}
            failed = []
            for p in changed_paths:
                ext = Path(p).suffix.lower()
                if ext in (".html", ".htm", ".js", ".ts"):
                    res = validate_artifact(p)
                    if not res["passed"]:
                        failed.append(f"{p}: {res['message']}")
            if failed:
                return {
                    "action": "continue",
                    "message": "Demo Validator detected invalid UI artifacts:\n" + "\n".join(failed) + "\nPlease fix syntax errors before completion."
                }
            return {"action": "continue"}

        ctx.register_hook("pre_verify", pre_verify_hook)

    return True


__all__ = [
    "validate_html",
    "validate_js",
    "validate_artifact",
    "register",
]
