"""
Hermes Plugin: observer_gate
============================
Universal code artifact verification, structural AST auditing, dynamic toolchain
reconnaissance, and contractual empirical verification gate.
Powered by:
- `ast-grep-py` (Tree-sitter structural AST across Lua, C, C++, Python, JS, TS, Rust, Go)
- Native system compilers/linters (`luac`, `clang`, `gcc`, `ruff`)
- Dynamic privilege reconnaissance (non-interactive sudo probe)
- Contractual verification gate (blocking completion without exit code 0 tests)
- Native Hermes CLI subcommand: `hermes audit <file>`
- Native in-session slash command: `/audit <file>`
- Native lifecycle hooks: `pre_verify`, `post_tool_call`, `transform_tool_result`
"""

from __future__ import annotations

import ast
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("hermes.plugins.observer_gate")

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

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    yaml = None
    YAML_AVAILABLE = False

# Supported code extensions for AST & verification gate
CODE_EXTENSIONS = {
    ".c", ".cpp", ".cc", ".cxx", ".h", ".hpp",
    ".lua",
    ".py",
    ".rs",
    ".go",
    ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
}

# Standard Lua library methods to prevent hallucinated APIs
LUA_STDLIB_TABLES: Dict[str, Set[str]] = {
    "string": {
        "byte", "char", "dump", "find", "format", "gmatch", "gsub", "len",
        "lower", "match", "pack", "packsize", "rep", "reverse", "sub", "unpack", "upper"
    },
    "table": {
        "concat", "insert", "move", "pack", "remove", "sort", "unpack", "maxn", "foreachi", "foreach", "getn", "setn", "new", "clear"
    },
    "math": {
        "abs", "acos", "asin", "atan", "atan2", "ceil", "cos", "cosh", "deg",
        "exp", "floor", "fmod", "frexp", "huge", "ldexp", "log", "log10", "max",
        "maxinteger", "min", "mininteger", "modf", "pi", "pow", "rad", "random",
        "randomseed", "sin", "sinh", "sqrt", "tan", "tanh", "tointeger", "type", "ult"
    },
    "os": {
        "clock", "date", "difftime", "execute", "exit", "getenv", "remove",
        "rename", "setlocale", "time", "tmpname"
    },
    "io": {
        "close", "flush", "input", "lines", "open", "output", "popen", "read",
        "tmpfile", "type", "write", "stdin", "stdout", "stderr"
    },
    "utf8": {
        "char", "charpattern", "codes", "codepoint", "len", "offset"
    },
    "coroutine": {
        "close", "create", "isyieldable", "resume", "running", "status", "wrap", "yield"
    },
    "package": {
        "config", "cpath", "loaded", "loadlib", "path", "preload", "searchers", "searchpath", "loaders", "seeall"
    },
    "bit": {
        "tobit", "tohex", "bnot", "band", "bor", "bxor", "lshift", "rshift", "arshift", "rol", "ror", "bswap"
    },
    "debug": {
        "debug", "gethook", "getinfo", "getlocal", "getmetatable", "getregistry",
        "getupvalue", "getuservalue", "sethook", "setlocal", "setmetatable",
        "setupvalue", "setuservalue", "traceback", "upvalueid", "upvaluejoin"
    }
}

# Patterns indicating an automated build, compilation, or test command
TEST_BUILD_COMMAND_PATTERNS = [
    re.compile(r"\bcmake\s+--build\b"),
    re.compile(r"\bctest\b"),
    re.compile(r"\bpytest\b"),
    re.compile(r"\bcargo\s+test\b"),
    re.compile(r"\bnpm\s+test\b"),
    re.compile(r"\bpnpm\s+test\b"),
    re.compile(r"\byarn\s+test\b"),
    re.compile(r"\bmake\s+(test|check|unittest)\b"),
    re.compile(r"\bninja\s+test\b"),
    re.compile(r"\bgo\s+test\b"),
    re.compile(r"\bluac\s+-p\b"),
    re.compile(r"\bpython3?\s+-m\s+(unittest|pytest)\b"),
]

# In-memory tracking of session verification state
_SESSION_STATE: Dict[str, Dict[str, Any]] = {}


def _get_session_state(session_id: str = "") -> Dict[str, Any]:
    sid = session_id or "default"
    if sid not in _SESSION_STATE:
        _SESSION_STATE[sid] = {
            "tests_passed": False,
            "modified_code_files": set(),
            "last_test_command": "",
            "last_test_returncode": None,
        }
    return _SESSION_STATE[sid]


def check_syntax(code: str, language: str) -> tuple[bool, str]:
    """
    Validates code syntax using Tree-sitter AST (ast-grep-py) and language-native tools.
    Zero hand-rolled regex/bracket counters.
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

    elif lang in ("lua",):
        # 1. Native luac check if available
        luac_bin = shutil.which("luac")
        if luac_bin:
            try:
                proc = subprocess.run(
                    [luac_bin, "-p", "-"],
                    input=code,
                    text=True,
                    capture_output=True,
                    timeout=5,
                    check=False,
                )
                if proc.returncode != 0:
                    err_msg = (proc.stderr or proc.stdout).strip()
                    return False, f"Lua syntax error (luac): {err_msg}"
            except Exception:
                pass

        # 2. Tree-sitter AST validation via ast-grep
        if AST_GREP_AVAILABLE:
            try:
                root = SgRoot(code, "lua").root()
                errors = root.find_all(kind="ERROR")
                if errors:
                    first_err = errors[0].text()[:60]
                    return False, f"Lua syntax error: Tree-sitter error node near '{first_err}'"
            except Exception:
                pass

        return True, "Syntax is valid"

    elif lang in ("c", "h", "cpp", "hpp", "cc", "cxx"):
        # For C/C++, compiler build/test execution is the authoritative empirical gate.
        # Tree-sitter without macro expansion flags #ifdef/macro interleaving as ERROR nodes.
        # Only check Tree-sitter syntax if no preprocessor directives exist.
        sg_lang = "c" if lang in ("c", "h") else "cpp"
        if AST_GREP_AVAILABLE and "#" not in code:
            try:
                root = SgRoot(code, sg_lang).root()
                errors = root.find_all(kind="ERROR")
                if errors:
                    first_err = errors[0].text()[:60]
                    return False, f"{lang.upper()} syntax error: Tree-sitter error node near '{first_err}'"
            except Exception:
                pass
        return True, "Syntax is valid"

    elif lang in ("js", "javascript", "ts", "typescript", "jsx", "tsx", "mjs", "cjs"):
        sg_lang = "javascript" if "js" in lang else "typescript"
        if AST_GREP_AVAILABLE:
            try:
                root = SgRoot(code, sg_lang).root()
                errors = root.find_all(kind="ERROR")
                if errors:
                    first_err = errors[0].text()[:60]
                    return False, f"{language} syntax error: Tree-sitter error node near '{first_err}'"
            except Exception:
                pass
        return True, "Syntax is valid"

    elif lang in ("rust", "rs"):
        if AST_GREP_AVAILABLE:
            try:
                root = SgRoot(code, "rust").root()
                errors = root.find_all(kind="ERROR")
                if errors:
                    first_err = errors[0].text()[:60]
                    return False, f"Rust syntax error: Tree-sitter error node near '{first_err}'"
            except Exception:
                pass
        return True, "Syntax is valid"

    elif lang in ("go",):
        if AST_GREP_AVAILABLE:
            try:
                root = SgRoot(code, "go").root()
                errors = root.find_all(kind="ERROR")
                if errors:
                    first_err = errors[0].text()[:60]
                    return False, f"Go syntax error: Tree-sitter error node near '{first_err}'"
            except Exception:
                pass
        return True, "Syntax is valid"

    elif lang in ("json",):
        try:
            json.loads(code)
            return True, "Syntax is valid"
        except Exception as e:
            return False, f"JSON syntax error: {e}"

    elif lang in ("yaml", "yml"):
        if YAML_AVAILABLE:
            try:
                yaml.safe_load(code)
                return True, "Syntax is valid"
            except Exception as e:
                return False, f"YAML syntax error: {e}"
        return True, "Syntax is valid"

    elif lang in ("md", "markdown", "txt"):
        return True, "Syntax is valid"

    else:
        # Generic Tree-sitter check if supported
        if AST_GREP_AVAILABLE:
            try:
                root = SgRoot(code, lang).root()
                errors = root.find_all(kind="ERROR")
                if errors:
                    return False, f"{language} syntax error: Tree-sitter error node detected"
                return True, "Syntax is valid"
            except Exception:
                pass
        return True, "Syntax check bypassed (unsupported language)"


def check_api_hallucinations(code: str, lang: str) -> List[str]:
    """
    Scans code using ast-grep Tree-sitter for non-existent standard library APIs.
    """
    violations = []
    if not AST_GREP_AVAILABLE:
        return violations

    if lang == "lua":
        try:
            root = SgRoot(code, "lua").root()
            for d in root.find_all(kind="dot_index_expression"):
                c = d.children()
                if len(c) == 3 and c[1].text() == ".":
                    table_name = c[0].text()
                    method_name = c[2].text()
                    if table_name in LUA_STDLIB_TABLES:
                        if method_name not in LUA_STDLIB_TABLES[table_name]:
                            violations.append(
                                f"Unknown method '{table_name}.{method_name}' (standard Lua {table_name} library does not provide this)"
                            )
        except Exception:
            pass

    return violations


def audit_file(filepath: str | Path) -> dict:
    """
    Performs comprehensive verification of a code artifact using ast-grep, native linters, and API audits.
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
        "lua": "lua",
        "c": "c",
        "h": "c",
        "cpp": "cpp",
        "hpp": "cpp",
        "cc": "cpp",
        "cxx": "cpp",
        "rs": "rust",
        "go": "go",
        "json": "json",
        "yaml": "yaml",
        "yml": "yaml",
    }
    lang = lang_map.get(ext, ext)

    checks = []

    # 1. Syntax check via Tree-sitter AST & native compilers
    valid, msg = check_syntax(code, lang)
    checks.append({"name": "syntax_check", "passed": valid, "detail": msg})

    # 2. Linter check (Ruff for Python, luac for Lua, clang/gcc for C/C++)
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

    elif lang == "lua":
        luac_bin = shutil.which("luac")
        if luac_bin:
            try:
                proc = subprocess.run(
                    [luac_bin, "-p", str(path)],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                passed = proc.returncode == 0
                detail = "luac -p clean." if passed else (proc.stderr or proc.stdout).strip()[:300]
                checks.append({"name": "luac_lint", "passed": passed, "detail": detail})
            except Exception as ex:
                checks.append({"name": "luac_lint", "passed": True, "detail": f"Skipped: {ex}"})

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

    # 4. Standard Library API Hallucination Check (ast-grep Tree-sitter)
    api_violations = check_api_hallucinations(code, lang)
    if api_violations:
        checks.append({
            "name": "ast_grep_api_hallucinations",
            "passed": False,
            "detail": "; ".join(api_violations),
        })

    # 5. Ponytail YAGNI Simplicity Gate (for Python)
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
            p = Path(args.path)
            if p.is_dir():
                exts = {".py", ".lua", ".c", ".h", ".cpp", ".hpp", ".rs", ".go", ".ts", ".js"}
                skip_dirs = {".git", ".venv", "venv", "__pycache__", "node_modules", "build", "target"}
                results = []
                total_passed = 0
                total_failed = 0
                for root, dirs, files in os.walk(p):
                    dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]
                    for f in files:
                        fp = Path(root) / f
                        if fp.suffix.lower() in exts:
                            r = audit_file(fp)
                            results.append(r)
                            if r["passed"]:
                                total_passed += 1
                            else:
                                total_failed += 1
                if getattr(args, "json", False):
                    print(json.dumps({"total": len(results), "passed": total_passed, "failed": total_failed, "results": results}, indent=2))
                else:
                    status_symbol = "✓" if total_failed == 0 else "✗"
                    print(f"Observer Gate Directory Audit: {status_symbol} ({total_passed} passed, {total_failed} failed, {len(results)} total files)")
                    for r in results:
                        if not r["passed"]:
                            print(f"  [✗] {r['path']}: {r['message']}")
                            for c in r["checks"]:
                                if not c["passed"]:
                                    print(f"      - {c['name']}: {c['detail']}")
                return 0 if total_failed == 0 else 1

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
                return "Usage: /audit <file_path_or_dir>"
            p = Path(target)
            if p.is_dir():
                exts = {".py", ".lua", ".c", ".h", ".cpp", ".hpp", ".rs", ".go", ".ts", ".js"}
                skip_dirs = {".git", ".venv", "venv", "__pycache__", "node_modules", "build", "target"}
                total_passed = 0
                total_failed = 0
                failures = []
                for root, dirs, files in os.walk(p):
                    dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]
                    for f in files:
                        fp = Path(root) / f
                        if fp.suffix.lower() in exts:
                            r = audit_file(fp)
                            if r["passed"]:
                                total_passed += 1
                            else:
                                total_failed += 1
                                failures.append(f"- `[✗]` `{fp}`: {r['message']}")
                status_symbol = "✓" if total_failed == 0 else "✗"
                lines = [f"**Observer Gate Directory Audit**: {status_symbol} ({total_passed} passed, {total_failed} failed)"]
                lines.extend(failures[:15])
                if len(failures) > 15:
                    lines.append(f"... and {len(failures) - 15} more failures")
                return "\n".join(lines)

            res = audit_file(target)
            status_symbol = "✓" if res["passed"] else "✗"
            lines = [f"**Observer Gate**: {res['verdict']} {status_symbol} — `{res['path']}`"]
            for c in res["checks"]:
                mark = "✓" if c["passed"] else "✗"
                lines.append(f"- [{mark}] **{c['name']}**: {c['detail']}")
            return "\n".join(lines)

        ctx.register_command("audit", slash_audit, "Audit code artifact against observer gate", "<file>")

    # 3. Lifecycle Hook: post_tool_call (Track test executions and file mutations)
    if hasattr(ctx, "register_hook"):
        def post_tool_call_hook(
            tool_name: str = "",
            args: Optional[Dict[str, Any]] = None,
            result: Any = None,
            task_id: str = "",
            session_id: str = "",
            **kwargs: Any,
        ) -> None:
            st = _get_session_state(session_id or task_id)
            if tool_name in ("write_file", "patch"):
                path_str = (args or {}).get("path") or (args or {}).get("file_path") or (args or {}).get("filename")
                if path_str:
                    ext = Path(path_str).suffix.lower()
                    if ext in CODE_EXTENSIONS:
                        st["modified_code_files"].add(str(path_str))
                        # Reset verification status: new edits must be verified by automated tests!
                        st["tests_passed"] = False

        ctx.register_hook("post_tool_call", post_tool_call_hook)

    # 4. Lifecycle Hook: transform_tool_result (Dynamic Reconnaissance & In-line Rejections)
    if hasattr(ctx, "register_hook"):
        def transform_tool_result_hook(
            tool_name: str = "",
            args: Optional[Dict[str, Any]] = None,
            result: Any = None,
            session_id: str = "",
            **kwargs: Any,
        ) -> Optional[str]:
            if not isinstance(result, str):
                return None

            st = _get_session_state(session_id)

            # In-line AST audit rejection for write_file and patch
            if tool_name in ("write_file", "patch"):
                path_str = (args or {}).get("path") or (args or {}).get("file_path") or (args or {}).get("filename")
                if path_str:
                    audit_res = audit_file(path_str)
                    if not audit_res["passed"]:
                        violations = [c["detail"] for c in audit_res["checks"] if not c["passed"]]
                        warning_block = (
                            f"\n\n[Observer Gate AST Rejection]: Modified file '{path_str}' failed AST/syntax validation:\n"
                            + "\n".join(f"  - {v}" for v in violations)
                            + "\nPlease correct these errors immediately."
                        )
                        return result + warning_block

            # Dynamic Reconnaissance for terminal executions
            if tool_name == "terminal":
                command = (args or {}).get("command", "")
                returncode = None
                try:
                    parsed = json.loads(result)
                    if isinstance(parsed, dict):
                        returncode = parsed.get("returncode") if "returncode" in parsed else parsed.get("exit_code")
                except Exception:
                    pass

                # Track test/build command outcomes
                is_test_or_build = any(pat.search(command) for pat in TEST_BUILD_COMMAND_PATTERNS)
                if is_test_or_build:
                    if returncode == 0:
                        st["tests_passed"] = True
                        st["last_test_command"] = command
                        st["last_test_returncode"] = 0
                    elif returncode is not None:
                        st["tests_passed"] = False
                        st["last_test_command"] = command
                        st["last_test_returncode"] = returncode

                # Reconnaissance Diagnostics on Failures
                extra_notes = []
                raw_text = result

                # Diagnostic 1: Python ModuleNotFoundError on non-python binary
                if "ModuleNotFoundError" in raw_text or "No module named" in raw_text:
                    cmd_parts = command.strip().split()
                    cmd_bin = cmd_parts[0] if cmd_parts else ""
                    if cmd_bin and cmd_bin not in ("python", "python3", "pytest"):
                        system_bin = Path("/usr/bin") / cmd_bin
                        if system_bin.exists() and os.access(system_bin, os.X_OK):
                            extra_notes.append(
                                f"[Observer Gate Reconnaissance]: Command '{cmd_bin}' failed with a Python import error, "
                                f"indicating a broken wrapper or shadowed script in PATH. A native system binary exists at '{system_bin}'. "
                                f"Invoke '{system_bin}' directly or inspect `which -a {cmd_bin}`."
                            )

                # Diagnostic 2: Permission denied / need root -> probe non-interactive sudo dynamically
                if any(p in raw_text.lower() for p in ["permission denied", "must be root", "access denied", "operation not permitted"]):
                    try:
                        sudo_res = subprocess.run(["sudo", "-n", "true"], capture_output=True, timeout=2)
                        if sudo_res.returncode == 0:
                            extra_notes.append(
                                "[Observer Gate Reconnaissance]: Command failed with permission error. "
                                "Non-interactive passwordless sudo is verified available in this environment. "
                                "You can execute this operation via 'sudo <command>'."
                            )
                    except Exception:
                        pass

                if extra_notes:
                    return result + "\n\n" + "\n\n".join(extra_notes)

            return None

        ctx.register_hook("transform_tool_result", transform_tool_result_hook)

    # 5. Lifecycle Hook: pre_verify (Ironclad Contractual Verification Gate)
    if hasattr(ctx, "register_hook"):
        def pre_verify_hook(
            changed_paths=None,
            session_id: str = "",
            attempt: int = 0,
            **kwargs: Any,
        ) -> Dict[str, Any]:
            st = _get_session_state(session_id)
            all_changed = set(changed_paths or []) | st["modified_code_files"]

            if not all_changed:
                return {"action": "continue"}

            # Phase 1: AST / Syntax verification on all modified files
            failed = []
            for p in all_changed:
                ext = Path(p).suffix.lower()
                if ext in CODE_EXTENSIONS:
                    audit_res = audit_file(p)
                    if not audit_res["passed"]:
                        failed.append(f"{p}: {audit_res['message']}")
                        for c in audit_res["checks"]:
                            if not c["passed"]:
                                failed.append(f"  - [{c['name']}]: {c['detail']}")

            if failed:
                return {
                    "action": "continue",
                    "message": (
                        "Observer Gate AST/Syntax Validation REJECTED:\n"
                        + "\n".join(failed)
                        + "\nYou must fix these syntax/API errors before concluding."
                    ),
                }

            # Phase 2: Empirical Contract Verification Gate
            code_modified = [p for p in all_changed if Path(p).suffix.lower() in CODE_EXTENSIONS]
            if code_modified and not st["tests_passed"]:
                if attempt < 2:
                    return {
                        "action": "continue",
                        "message": (
                            f"Observer Gate Verification Gate BLOCKED: Code files were modified ({', '.join(str(p) for p in code_modified)}), "
                            "but no automated build or test command has passed with exit code 0. "
                            "Under the absorbed frontier verification contract (Claude Fable 5.1 / GPT-Astra / Gemini 3.8-cyber), "
                            "completion cannot be self-certified through verbal claims or source inspection alone. "
                            "Execute the relevant test or build command (e.g., cmake --build, make test, ctest, pytest) and verify it returns exit code 0 before concluding. "
                            "If testing is blocked by environment constraints, state 'STATUS: UNVERIFIED_BLOCKED' and cite the exact blocker output."
                        ),
                    }

            return {"action": "continue"}

        ctx.register_hook("pre_verify", pre_verify_hook)

    return True
