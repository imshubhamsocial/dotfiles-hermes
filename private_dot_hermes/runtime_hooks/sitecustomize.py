"""Hermes Agent OS v4.4.0 — GDR15 Zero-Diff Runtime Interceptor (Directives A, B, C, D).

Installed at .hermes/runtime_hooks/sitecustomize.py and symlinked into
.local/lib/python3.13/site-packages/sitecustomize.py and
.venv/lib/python3.13/site-packages/sitecustomize.py to preserve 100% Tier 3
upstream git purity in .hermes/hermes-agent.
"""
from __future__ import annotations

import contextlib
import difflib
import json
import logging
import os
import pathlib
import re
import shlex
import shutil
import subprocess
import sys
from typing import Any

logger = logging.getLogger("hermes.gdr15")

WORKSPACE_ROOT = pathlib.Path(
    os.environ.get("HERMES_WORKSPACE_ROOT", "/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes")
).resolve()
MANIFEST_LATEST_PATH = WORKSPACE_ROOT / ".hermes" / "cache" / "intent_manifests" / "latest_active.json"

_SHELL_COMMAND_VERBS = frozenset({
    "mkdir", "cd", "touch", "rm", "echo", "pytest", "python", "python3",
    "git", "cat", "ls", "cp", "mv", "grep", "find", "sed", "awk", "chmod",
})
_PRIMARY_GUARDED_VERBS = frozenset({
    "rm", "mkdir", "cd", "touch", "cp", "mv", "ls", "cat", "pytest", "git",
})
_CONTROL_SPLIT_RE = re.compile(r"(?:&&|\|\||;|\||\n)")
_DIR_EXTRACT_RE = re.compile(r"\b((?:tests|benchmarks|src)/[a-zA-Z0-9_\-]+(?:/[a-zA-Z0-9_\-]+)*)/?")
_PYFILE_EXTRACT_RE = re.compile(r"\b([a-zA-Z0-9_]+\.py)\b")


class _GDR15SessionState:
    def __init__(self) -> None:
        self.sandbox_target: str | None = None
        self.canonical_files: list[str] = []
        self.tool_history: list[dict[str, Any]] = []
        self.seeded_commits: set[str] = set()
        self.bootstrapped: bool = False

    def load_or_bootstrap_from_text(self, text: str) -> None:
        if self.bootstrapped and self.sandbox_target:
            return
        if MANIFEST_LATEST_PATH.exists():
            with contextlib.suppress(Exception):
                data = json.loads(MANIFEST_LATEST_PATH.read_text(encoding="utf-8"))
                if data.get("sandbox_target") and data["sandbox_target"] != "workspace:root":
                    self.sandbox_target = data["sandbox_target"].strip("/")
                    self.canonical_files = data.get("canonical_files", [])
                    self._ensure_sandbox_initialized()
                    self.bootstrapped = True
                    return
        if not text:
            return
        dir_matches = _DIR_EXTRACT_RE.findall(text)
        if dir_matches:
            candidate = dir_matches[0].strip("/")
            if candidate.endswith(".py"):
                candidate = str(pathlib.Path(candidate).parent)
            self.sandbox_target = candidate
            self.canonical_files = list(dict.fromkeys(_PYFILE_EXTRACT_RE.findall(text)))
            self._ensure_sandbox_initialized()
            self.bootstrapped = True

    def _ensure_sandbox_initialized(self) -> None:
        if not self.sandbox_target:
            return
        target_path = (WORKSPACE_ROOT / self.sandbox_target).resolve()
        target_path.mkdir(parents=True, exist_ok=True)
        git_dir = target_path / ".git"
        if not git_dir.exists():
            subprocess.run(["git", "init", "-q"], cwd=str(target_path), check=False)
            subprocess.run(["git", "config", "user.email", "hermes@local"], cwd=str(target_path), check=False)
            subprocess.run(["git", "config", "user.name", "Hermes OS"], cwd=str(target_path), check=False)
            gitignore = target_path / ".gitignore"
            if not gitignore.exists():
                gitignore.write_text("__pycache__/\n*.pyc\n.pytest_cache/\n", encoding="utf-8")
            root_conftest = WORKSPACE_ROOT / "conftest.py"
            local_conftest = target_path / "conftest.py"
            if root_conftest.exists() and not local_conftest.exists():
                shutil.copy2(root_conftest, local_conftest)
            subprocess.run(["git", "add", ".gitignore", "conftest.py"], cwd=str(target_path), check=False)
            subprocess.run(
                ["git", "commit", "-q", "-m", "chore: bootstrap isolated testbed"],
                cwd=str(target_path),
                check=False,
            )


_STATE = _GDR15SessionState()


class _RootPinnedCWDMap(dict):
    """Directive A: Pins terminal_tool._session_cwd to WORKSPACE_ROOT across turns."""
    def __getitem__(self, key: Any) -> str:
        return str(WORKSPACE_ROOT)

    def get(self, key: Any, default: Any = None) -> str:
        return str(WORKSPACE_ROOT)

    def setdefault(self, key: Any, default: Any = None) -> str:
        return str(WORKSPACE_ROOT)

    def __setitem__(self, key: Any, value: Any) -> None:
        super().__setitem__(key, str(WORKSPACE_ROOT))


def _canonicalize_file_path(raw_path: str, for_write: bool = False) -> str:
    """Directive A & D: Snaps truncated/fuzzy test paths to locked sandbox_target."""
    clean = raw_path.strip().lstrip("./")
    if not _STATE.sandbox_target:
        _STATE.load_or_bootstrap_from_text("")
    sandbox = _STATE.sandbox_target
    if not sandbox:
        return raw_path

    p = pathlib.Path(clean)
    filename = p.name

    # Snap fuzzy filename (e.g., test_reaper_torture_test.py -> test_reaper_torture.py)
    if filename.endswith(".py") and _STATE.canonical_files and filename not in _STATE.canonical_files:
        best_matches = difflib.get_close_matches(filename, _STATE.canonical_files, n=1, cutoff=0.65)
        if best_matches:
            filename = best_matches[0]

    # Case 1: Bare filename (e.g., read_file("state_ledger.py"))
    if len(p.parts) == 1 and filename != "conftest.py":
        root_candidate = WORKSPACE_ROOT / filename
        sandbox_candidate = WORKSPACE_ROOT / sandbox / filename
        if for_write or sandbox_candidate.exists() or not root_candidate.exists():
            return f"{sandbox}/{filename}"

    # Case 2: Path under tests/ with truncated or slash-split directory name
    if p.parts and p.parts[0] == "tests" and len(p.parts) >= 2:
        dir_part = str(p.parent)
        if dir_part != sandbox:
            sim = difflib.SequenceMatcher(None, dir_part.replace("/", "_"), sandbox.replace("/", "_")).ratio()
            if sim >= 0.55 or dir_part.startswith("tests/argon_"):
                return f"{sandbox}/{filename}"

    return raw_path


def _validate_and_sanitize_shell_command(cmd: str) -> tuple[bool, str]:
    """Directive C: Intercepts delimiter-free compound commands and normalizes CWD/pytest."""
    _STATE.load_or_bootstrap_from_text(cmd)
    segments = [s.strip() for s in _CONTROL_SPLIT_RE.split(cmd) if s.strip()]

    for seg in segments:
        try:
            tokens = shlex.split(seg, posix=True)
        except ValueError:
            tokens = seg.split()
        if not tokens:
            continue
        lead_verb = os.path.basename(tokens[0])
        if lead_verb in _PRIMARY_GUARDED_VERBS and len(tokens) > 2:
            for idx, tok in enumerate(tokens[1:], start=1):
                if tok in ("-c", "-m", "-exec", "xargs"):
                    break
                if tok in _SHELL_COMMAND_VERBS and not tok.startswith("-"):
                    # Allow 'git commit/add/diff/status' subcommands
                    if lead_verb == "git" and idx == 1:
                        continue
                    return (
                        False,
                        (
                            f"CommandSyntaxError (GDR15-DEFECT-04): Multiple shell commands detected "
                            f"without '&&' or ';' delimiters (found unquoted command verb '{tok}' inside "
                            f"'{lead_verb}' arguments). Separate commands with ' && ' or use native "
                            f"write_file/read_file tools."
                        ),
                    )

    # Check mkdir -p <dirA> && cd <dirB> consistency
    mkdir_m = re.search(r"\bmkdir\s+(?:-p\s+)?(tests/[a-zA-Z0-9_\-/]+)", cmd)
    cd_m = re.search(r"\bcd\s+(tests/[a-zA-Z0-9_\-/]+)", cmd)
    if mkdir_m and cd_m and mkdir_m.group(1).rstrip("/") != cd_m.group(1).rstrip("/"):
        target_hint = _STATE.sandbox_target or mkdir_m.group(1)
        return (
            False,
            (
                f"PathMismatchError (GDR15-DEFECT-04): 'mkdir -p {mkdir_m.group(1)}' does not match "
                f"'cd {cd_m.group(1)}'. Active canonical sandbox is '{target_hint}'. "
                f"Do not run mkdir/cd; use write_file('{target_hint}/<file>.py', ...) directly."
            ),
        )

    # Rewrite bare 'pytest' to scope to sandbox_target if active
    if _STATE.sandbox_target and re.fullmatch(r"pytest(?:\s+-q|\s+-v)?", cmd.strip()):
        sb = _STATE.sandbox_target
        return (
            True,
            f'PYTHONPATH=".:{sb}:$PYTHONPATH" pytest {sb} -q',
        )
    return True, cmd


def _extract_shingles(tool_name: str, args_str: str) -> set[str]:
    tokens = re.findall(r"[a-zA-Z0-9]+", f"{tool_name} {args_str}".lower())
    stop = {"tests", "argon", "the", "and", "touch", "mkdir", "echo", "starting", "implementation"}
    stems = {t for t in tokens if len(t) >= 3 and t not in stop}
    return stems or set(tokens)


def _check_sprl_circuit_breaker(tool_name: str, args_str: str, failed_or_empty: bool) -> str | None:
    """Directive B: 3-Signal Semantic Rotational Loop Circuit Breaker (<= 5 turns)."""
    shingles = _extract_shingles(tool_name, args_str)
    _STATE.tool_history.append({
        "tool": tool_name,
        "shingles": shingles,
        "failed": failed_or_empty,
    })

    # Signal 3c: Check sibling directory proliferation under tests/argon_*
    tests_dir = WORKSPACE_ROOT / "tests"
    if tests_dir.exists() and _STATE.sandbox_target:
        canonical_name = pathlib.Path(_STATE.sandbox_target).name
        stray_dirs = [
            d for d in tests_dir.iterdir()
            if d.is_dir() and d.name.startswith("argon_") and d.name != canonical_name
        ]
        if len(stray_dirs) >= 1:
            for sd in stray_dirs:
                for pyf in sd.rglob("*.py"):
                    dest = WORKSPACE_ROOT / _STATE.sandbox_target / pyf.name
                    if not dest.exists():
                        shutil.copy2(pyf, dest)
                shutil.rmtree(sd, ignore_errors=True)
            return (
                f"\n[SPRL_CIRCUIT_BREAKER_HEALED (GDR15-DEFECT-03): Purged {len(stray_dirs)} stray "
                f"directory variation(s) and consolidated files into canonical '{_STATE.sandbox_target}/'. "
                f"Do NOT run mkdir or cd. Operate strictly inside '{_STATE.sandbox_target}/'.]"
            )

    if len(_STATE.tool_history) < 4:
        return None
    window = _STATE.tool_history[-4:]
    distinct_tools = {w["tool"] for w in window}
    fail_count = sum(1 for w in window if w["failed"])

    # Compute mean pairwise Jaccard overlap across the 4-turn window
    pairs = []
    for i in range(len(window)):
        for j in range(i + 1, len(window)):
            s1, s2 = window[i]["shingles"], window[j]["shingles"]
            union = len(s1 | s2)
            pairs.append(len(s1 & s2) / union if union else 1.0)
    mean_jaccard = sum(pairs) / len(pairs) if pairs else 0.0

    if len(distinct_tools) >= 2 and mean_jaccard >= 0.65 and fail_count >= 2:
        sb = _STATE.sandbox_target or "workspace_root"
        return (
            f"\n[SPRL_CIRCUIT_BREAKER_TRIPPED (GDR15-DEFECT-03): Heterogeneous rotational loop "
            f"detected across {len(distinct_tools)} tools (Jaccard={mean_jaccard:.2f} >= 0.65, "
            f"errors={fail_count}). CWD is locked to '{WORKSPACE_ROOT}'. Target testbed is '{sb}'. "
            f"Use canonical root-relative paths '{sb}/<filename>.py'.]"
        )
    return None


# ---------------------------------------------------------------------------
# Tier-3 In-Process Tool Patching Hooks
# ---------------------------------------------------------------------------
def _patch_terminal_tool_module(mod: Any) -> None:
    """Applies Directive A & C to tools.terminal_tool."""
    try:
        if not isinstance(getattr(mod, "_session_cwd", None), _RootPinnedCWDMap):
            mod._session_cwd = _RootPinnedCWDMap()

        orig_terminal_tool = getattr(mod, "terminal_tool", None)
        if orig_terminal_tool and not getattr(orig_terminal_tool, "_gdr15_wrapped", False):
            def wrapped_terminal_tool(
                command: str,
                background: bool = False,
                timeout: int | None = None,
                task_id: str | None = None,
                session_id: str | None = None,
                force: bool = False,
                workdir: str | None = None,
                pty: bool = False,
                notify_on_complete: bool = False,
                watch_patterns: list[str] | None = None,
                _host_local: bool = False,
            ) -> str:
                ok, sanitized_or_err = _validate_and_sanitize_shell_command(command)
                if not ok:
                    cb_note = _check_sprl_circuit_breaker("terminal", command, True)
                    err_out = sanitized_or_err + (cb_note or "")
                    return json.dumps({"output": "", "exit_code": 1, "error": err_out})

                result = orig_terminal_tool(
                    sanitized_or_err,
                    background=background,
                    timeout=timeout,
                    task_id=task_id,
                    session_id=session_id,
                    force=force,
                    workdir=workdir,
                    pty=pty,
                    notify_on_complete=notify_on_complete,
                    watch_patterns=watch_patterns,
                    _host_local=_host_local,
                )

                with contextlib.suppress(Exception):
                    res_dict = json.loads(result) if isinstance(result, str) and result.startswith("{") else None
                    if isinstance(res_dict, dict):
                        failed = res_dict.get("exit_code", 0) != 0 or bool(res_dict.get("error"))
                        cb_note = _check_sprl_circuit_breaker("terminal", sanitized_or_err, failed)
                        if cb_note and "output" in res_dict:
                            res_dict["output"] = str(res_dict["output"]) + cb_note
                        if _STATE.sandbox_target and "output" in res_dict:
                            footer = f"\n[CWD_SYNC: workspace_root | ACTIVE_SANDBOX: {_STATE.sandbox_target}]"
                            if footer not in str(res_dict["output"]):
                                res_dict["output"] = str(res_dict["output"]) + footer
                        result = json.dumps(res_dict)

                return result

            wrapped_terminal_tool._gdr15_wrapped = True  # type: ignore[attr-defined]
            mod.terminal_tool = wrapped_terminal_tool
    except Exception as exc:  # noqa: BLE001
        logger.debug("Failed to patch tools.terminal_tool: %s", exc)


def _patch_file_tools_module(mod: Any) -> None:
    """Applies Directive A & D to tools.file_tools."""
    try:
        orig_read = getattr(mod, "read_file_tool", None)
        if orig_read and not getattr(orig_read, "_gdr15_wrapped", False):
            def wrapped_read_file_tool(path: str, offset: int = 1, limit: int = 200, task_id: str = "default") -> str:
                canon_path = _canonicalize_file_path(path, for_write=False)
                res = orig_read(canon_path, offset=offset, limit=limit, task_id=task_id)
                failed = False
                try:
                    res_dict = json.loads(res) if isinstance(res, str) and res.startswith("{") else None
                    if isinstance(res_dict, dict) and bool(res_dict.get("error")):
                        failed = True
                except Exception:  # noqa: BLE001
                    failed = "error" in res.lower()
                cb_note = _check_sprl_circuit_breaker("read_file", canon_path, failed)
                if cb_note:
                    try:
                        res_dict = json.loads(res) if isinstance(res, str) and res.startswith("{") else None
                        if isinstance(res_dict, dict) and "content" in res_dict:
                            res_dict["content"] = str(res_dict["content"]) + cb_note
                            return json.dumps(res_dict)
                    except Exception:  # noqa: BLE001
                        return res + cb_note
                return res

            wrapped_read_file_tool._gdr15_wrapped = True  # type: ignore[attr-defined]
            mod.read_file_tool = wrapped_read_file_tool

        orig_write = getattr(mod, "write_file_tool", None)
        if orig_write and not getattr(orig_write, "_gdr15_wrapped", False):
            def wrapped_write_file_tool(path: str, content: str, task_id: str = "default", **kwargs: Any) -> str:
                canon_path = _canonicalize_file_path(path, for_write=True)
                res = orig_write(canon_path, content, task_id=task_id, **kwargs)

                # Directive D: Automatic git baseline commit on initial creation of testbed file
                if _STATE.sandbox_target and canon_path.startswith(_STATE.sandbox_target):
                    target_dir = WORKSPACE_ROOT / _STATE.sandbox_target
                    filename = pathlib.Path(canon_path).name
                    if filename not in _STATE.seeded_commits and filename.endswith(".py"):
                        _STATE.seeded_commits.add(filename)
                        subprocess.run(["git", "add", filename], cwd=str(target_dir), check=False)
                        subprocess.run(
                            ["git", "commit", "-q", "-m", f"seed: initial {filename} creation"],
                            cwd=str(target_dir),
                            check=False,
                        )

                cb_note = _check_sprl_circuit_breaker("write_file", canon_path, False)
                if cb_note:
                    try:
                        res_dict = json.loads(res) if isinstance(res, str) and res.startswith("{") else None
                        if isinstance(res_dict, dict) and "resolved_path" in res_dict:
                            res_dict["resolved_path"] = str(res_dict["resolved_path"]) + cb_note
                            return json.dumps(res_dict)
                    except Exception:  # noqa: BLE001
                        return res + cb_note
                return res

            wrapped_write_file_tool._gdr15_wrapped = True  # type: ignore[attr-defined]
            mod.write_file_tool = wrapped_write_file_tool

        orig_patch = getattr(mod, "patch_tool", None)
        if orig_patch and not getattr(orig_patch, "_gdr15_wrapped", False):
            def wrapped_patch_tool(mode: str = "replace", path: str | None = None, **kwargs: Any) -> str:
                if path:
                    path = _canonicalize_file_path(path, for_write=False)
                return orig_patch(mode=mode, path=path, **kwargs)

            wrapped_patch_tool._gdr15_wrapped = True  # type: ignore[attr-defined]
            mod.patch_tool = wrapped_patch_tool
    except Exception as exc:  # noqa: BLE001
        logger.debug("Failed to patch tools.file_tools: %s", exc)


def _patch_registry_module(mod: Any) -> None:
    """Wraps registry.register so newly registered tool handlers inherit GDR15 interceptors."""
    try:
        reg = getattr(mod, "registry", None)
        if reg and not getattr(reg, "_gdr15_wrapped", False):
            orig_register = reg.register

            def wrapped_register(name: str, toolset: str, schema: dict, handler: Any, *args: Any, **kwargs: Any) -> Any:
                if name == "terminal":
                    def wrapped_terminal_handler(*h_args: Any, **h_kwargs: Any) -> Any:
                        cmd = h_kwargs.get("command") or (h_args[0] if h_args else "")
                        ok, sanitized_or_err = _validate_and_sanitize_shell_command(cmd)
                        if not ok:
                            cb_note = _check_sprl_circuit_breaker("terminal", cmd, True)
                            err_out = sanitized_or_err + (cb_note or "")
                            return json.dumps({"output": "", "exit_code": 1, "error": err_out})
                        if "command" in h_kwargs:
                            h_kwargs["command"] = sanitized_or_err
                        elif h_args:
                            h_args = (sanitized_or_err, *h_args[1:])
                        res = handler(*h_args, **h_kwargs)
                        with contextlib.suppress(Exception):
                            res_dict = json.loads(res) if isinstance(res, str) and res.startswith("{") else None
                            if isinstance(res_dict, dict):
                                failed = res_dict.get("exit_code", 0) != 0 or bool(res_dict.get("error"))
                                cb_note = _check_sprl_circuit_breaker("terminal", sanitized_or_err, failed)
                                if cb_note and "output" in res_dict:
                                    res_dict["output"] = str(res_dict["output"]) + cb_note
                                if _STATE.sandbox_target and "output" in res_dict:
                                    footer = f"\n[CWD_SYNC: workspace_root | ACTIVE_SANDBOX: {_STATE.sandbox_target}]"
                                    if footer not in str(res_dict["output"]):
                                        res_dict["output"] = str(res_dict["output"]) + footer
                                res = json.dumps(res_dict)
                        return res
                    handler = wrapped_terminal_handler

                elif name == "read_file":
                    def wrapped_read_handler(*h_args: Any, **h_kwargs: Any) -> Any:
                        p = h_kwargs.get("path") or (h_args[0] if h_args else "")
                        canon = _canonicalize_file_path(p, for_write=False)
                        if "path" in h_kwargs:
                            h_kwargs["path"] = canon
                        elif h_args:
                            h_args = (canon, *h_args[1:])
                        return handler(*h_args, **h_kwargs)
                    handler = wrapped_read_handler

                elif name == "write_file":
                    def wrapped_write_handler(*h_args: Any, **h_kwargs: Any) -> Any:
                        p = h_kwargs.get("path") or (h_args[0] if h_args else "")
                        canon = _canonicalize_file_path(p, for_write=True)
                        if "path" in h_kwargs:
                            h_kwargs["path"] = canon
                        elif h_args:
                            h_args = (canon, *h_args[1:])
                        res = handler(*h_args, **h_kwargs)
                        if _STATE.sandbox_target and canon.startswith(_STATE.sandbox_target):
                            target_dir = WORKSPACE_ROOT / _STATE.sandbox_target
                            fname = pathlib.Path(canon).name
                            if fname not in _STATE.seeded_commits and fname.endswith(".py"):
                                _STATE.seeded_commits.add(fname)
                                subprocess.run(["git", "add", fname], cwd=str(target_dir), check=False)
                                subprocess.run(
                                    ["git", "commit", "-q", "-m", f"seed: initial {fname} creation"],
                                    cwd=str(target_dir),
                                    check=False,
                                )
                        return res
                    handler = wrapped_write_handler

                return orig_register(name, toolset, schema, handler, *args, **kwargs)

            reg.register = wrapped_register
            reg._gdr15_wrapped = True
    except Exception as exc:  # noqa: BLE001
        logger.debug("Failed to patch tools.registry: %s", exc)


# Execute auto-patching if modules are already imported or can be imported
for mod_name, patch_fn in [
    ("tools.terminal_tool", _patch_terminal_tool_module),
    ("tools.file_tools", _patch_file_tools_module),
    ("tools.registry", _patch_registry_module),
]:
    if mod_name in sys.modules:
        patch_fn(sys.modules[mod_name])

# Also eagerly patch registry if discoverable
with contextlib.suppress(Exception):
    import tools.terminal_tool
    _patch_terminal_tool_module(tools.terminal_tool)

with contextlib.suppress(Exception):
    import tools.file_tools
    _patch_file_tools_module(tools.file_tools)

with contextlib.suppress(Exception):
    import tools.registry
    _patch_registry_module(tools.registry)
