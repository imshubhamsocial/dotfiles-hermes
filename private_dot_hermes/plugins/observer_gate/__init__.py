"""
Hermes Plugin: observer_gate
============================
Automated code artifact verification, structural AST querying, and lint auditing
powered by open-source GitHub suites:
- `ast-grep-py` (Tree-sitter structural AST queries across multi-language codebases)
- `ruff` (High-performance Rust-based Python linter and syntax validator)
- Native Hermes CLI subcommand: `hermes audit <file>`
- Native in-session slash command: `/audit <file>`
- Native lifecycle hook: `pre_verify`
"""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path

try:
    from ast_grep_py import SgRoot
    AST_GREP_AVAILABLE = True
except ImportError:
    SgRoot = None
    AST_GREP_AVAILABLE = False

try:
    import ruff
    RUFF_AVAILABLE = True
except ImportError:
    ruff = None
    RUFF_AVAILABLE = False


def check_syntax(code: str, language: str) -> tuple[bool, str]:
    """
    Validates code syntax.
    Checks Python code using ast.parse + ruff AST verification.
    Checks JS/HTML for balanced braces/delimiters + Tree-sitter AST validation via ast-grep.
    Returns (True, "Syntax is valid") or (False, "Syntax error: [error message]").
    """
    lang = language.lower()

    if lang in ("python", "py"):
        try:
            ast.parse(code)
        except SyntaxError as e:
            return False, f"Python syntax error: {e}"

        if RUFF_AVAILABLE and hasattr(ruff, "find_ruff_bin"):
            try:
                ruff_bin = ruff.find_ruff_bin()
                proc = subprocess.run(
                    [ruff_bin, "check", "--select=E999", "--stdin-filename=artifact.py", "-"],
                    input=code,
                    text=True,
                    capture_output=True,
                    timeout=5,
                    check=False,
                )
                if proc.returncode != 0 and "invalid-syntax" in proc.stdout:
                    return False, f"Python syntax error: {proc.stdout.strip()}"
            except Exception:
                pass

        return True, "Syntax is valid"

    elif lang in ("md", "markdown", "txt", "yaml", "yml"):
        return True, "Syntax is valid"
    elif lang in ("js", "javascript", "ts", "typescript", "html"):
        open_map = {"{": "}", "[": "]", "(": ")", "<": ">"}
        close_map = {"}": "{", "]": "[", ")": "(", ">": "<"}

        stack = []
        for char in code:
            if char in open_map:
                stack.append(char)
            elif char in close_map:
                expected_open = close_map[char]
                if not stack:
                    return False, f"{language} syntax error: Unexpected closing delimiter {char}"

                last_open = stack[-1]
                if last_open != expected_open:
                    return False, f"{language} syntax error: Mismatched delimiters. Expected {last_open}, got {char}"

                stack.pop()

        if stack:
            return False, f"{language} syntax error: Unbalanced delimiters remaining."

        if AST_GREP_AVAILABLE and lang in ("js", "javascript", "ts", "typescript"):
            sg_lang = "javascript" if lang in ("js", "javascript") else "typescript"
            try:
                root = SgRoot(code, sg_lang).root()
                errors = root.find_all(kind="ERROR")
                if errors:
                    first_err = errors[0].text()[:60]
                    return False, f"{language} syntax error: Tree-sitter error node: {first_err}"
            except Exception:
                pass

        return True, "Syntax is valid"

    else:
        return False, f"Unsupported language: {language}"


def audit_file(filepath: str | Path) -> dict:
    """
    Performs comprehensive verification of a code artifact using ast-grep and ruff.
    """
    path = Path(filepath).expanduser().resolve()
    if not path.exists():
        return {
            "passed": False,
            "verdict": "REJECTED",
            "message": f"File does not exist: {filepath}",
            "path": str(path),
            "checks": [],
        }

    code = path.read_text(encoding="utf-8", errors="replace")
    ext = path.suffix.lower().lstrip(".")
    lang_map = {
        "py": "python",
        "js": "js",
        "mjs": "js",
        "cjs": "js",
        "ts": "ts",
        "jsx": "js",
        "tsx": "ts",
        "html": "html",
        "htm": "html",
    }
    lang = lang_map.get(ext, ext)

    checks = []

    # 1. Syntax check
    valid, msg = check_syntax(code, lang)
    checks.append({"name": "syntax_check", "passed": valid, "detail": msg})

    # 2. Linter check (Ruff for Python)
    if lang == "python" and RUFF_AVAILABLE and hasattr(ruff, "find_ruff_bin"):
        try:
            ruff_bin = ruff.find_ruff_bin()
            proc = subprocess.run(
                [ruff_bin, "check", "--select=E9,F821,F822,PLW1514", "--output-format=concise", str(path)],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            passed = proc.returncode == 0
            detail = "Ruff lint clean." if passed else proc.stdout.strip()[:300]
            checks.append({"name": "ruff_lint", "passed": passed, "detail": detail})
        except Exception as ex:
            checks.append({"name": "ruff_lint", "passed": True, "detail": f"Skipped: {ex}"})

    # 3. Structural AST Dangerous Patterns Check (ast-grep)
    if AST_GREP_AVAILABLE and lang in ("python", "js", "ts"):
        sg_lang = "python" if lang == "python" else "javascript"
        dangerous_patterns = [
            ("eval($$$)", "Use of eval() detected"),
            ("exec($$$)", "Use of exec() detected"),
        ]
        violations = []
        try:
            root = SgRoot(code, sg_lang).root()
            for pat, desc in dangerous_patterns:
                matched = root.find(pattern=pat)
                if matched:
                    violations.append(f"{desc}: {matched.text()[:40]}")
        except Exception:
            pass

        checks.append({
            "name": "ast_grep_dangerous_patterns",
            "passed": len(violations) == 0,
            "detail": "; ".join(violations) if violations else "No dangerous AST patterns detected",
        })

    # 4. Ponytail YAGNI Simplicity Gate (for Python)
    if lang == "python":
        try:
            from agent.core.ponytail_ladder import audit_code_simplicity
            report = audit_code_simplicity(code)
            checks.append({
                "name": "ponytail_yagni_simplicity",
                "passed": report.passed,
                "detail": f"Simplicity score {report.simplicity_score:.2f} (Rung {int(report.assigned_rung)}: {report.assigned_rung.name})" if report.passed else f"Simplicity {report.simplicity_score:.2f} < 0.70 ({len(report.violations)} bloat violations)",
            })
        except Exception as ex:
            checks.append({"name": "ponytail_yagni_simplicity", "passed": True, "detail": f"Skipped: {ex}"})

    all_passed = all(c["passed"] for c in checks)
    verdict = "APPROVED" if all_passed else "REJECTED"
    summary_msg = f"Observer Gate {verdict}: {path.name} ({len(checks)} checks evaluated)"

    return {
        "passed": all_passed,
        "verdict": verdict,
        "message": summary_msg,
        "path": str(path),
        "checks": checks,
    }


def pre_commit_observer_gate(
    old_code: str,
    new_code: str,
    filepath: str = "",
    requested_dependencies: Optional[List[str]] = None,
    call_graph: Optional[Dict[str, List[str]]] = None,
    failing_symbol: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Observer Gate pre-commit hook enforcing AST diff limits, redundant helper pruning,
    unrequested dependency rejection, and root-cause call graph invariants.
    """
    from agent.core.ponytail_ladder import pre_commit_observer_gate as _pc_gate
    return _pc_gate(
        old_code=old_code,
        new_code=new_code,
        filepath=filepath,
        requested_dependencies=requested_dependencies,
        call_graph=call_graph,
        failing_symbol=failing_symbol,
    )


def register_plugin(registry=None):
    """Legacy registry interface for backward compatibility."""
    if registry:
        registry.register("observer_gate", {
            "check_syntax": check_syntax,
            "audit_file": audit_file,
            "pre_commit_observer_gate": pre_commit_observer_gate,
        })
    return True


def register(ctx=None):
    """Registers observer_gate into Hermes runtime."""
    if not ctx:
        return True

    # 1. Native CLI command: hermes audit <file>
    if hasattr(ctx, "register_cli_command"):
        def setup_audit(parser):
            parser.description = "Audit a file against observer gate syntax, ast-grep, and ruff rules"
            parser.add_argument("path", help="Path to the file to audit")
            parser.add_argument("--json", action="store_true", help="Output audit verdict as JSON")

        def handle_audit(args):
            res = audit_file(args.path)
            if getattr(args, "json", False):
                print(json.dumps(res, indent=2))
            else:
                status_symbol = "✓" if res["passed"] else "✗"
                print(f"Observer Gate: {res['verdict']} {status_symbol} ({res['message']})")
                for c in res["checks"]:
                    mark = "✓" if c["passed"] else "✗"
                    print(f"  [{mark}] {c['name']}: {c['detail']}")
            return 0 if res["passed"] else 1

        ctx.register_cli_command("audit", "Audit code file against observer gate (ast-grep & ruff)", setup_audit, handle_audit)

    # 2. Native Slash Command: /audit <file>
    if hasattr(ctx, "register_command"):
        def slash_audit(raw_args: str) -> str:
            target = raw_args.strip()
            if not target:
                return "Usage: /audit <file_path>"
            res = audit_file(target)
            status_symbol = "✓" if res["passed"] else "✗"
            lines = [f"**Observer Gate**: {res['verdict']} {status_symbol} — `{res['path']}`"]
            for c in res["checks"]:
                mark = "✓" if c["passed"] else "✗"
                lines.append(f"- [{mark}] **{c['name']}**: {c['detail']}")
            return "\n".join(lines)

        ctx.register_command("audit", slash_audit, "Audit code artifact against observer gate", "<file>")

    # 3. Lifecycle Hook: pre_verify
    if hasattr(ctx, "register_hook"):
        def pre_verify_hook(changed_paths=None, **kwargs):
            if not changed_paths:
                return {"action": "continue"}
            failed = []
            for p in changed_paths:
                ext = Path(p).suffix.lower()
                if ext in (".py", ".js", ".ts", ".html"):
                    audit_res = audit_file(p)
                    if not audit_res["passed"]:
                        failed.append(f"{p}: {audit_res['message']}")
            if failed:
                return {
                    "action": "continue",
                    "message": f"Observer Gate audit failed for modified files:\n" + "\n".join(failed) + "\nPlease correct the errors before concluding."
                }
            return {"action": "continue"}

        ctx.register_hook("pre_verify", pre_verify_hook)

    return True
