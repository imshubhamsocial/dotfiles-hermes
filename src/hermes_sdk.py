"""
Hermes Code Mode SDK (U1: Programmatic Batching Fast-Path)
==========================================================
Micro-SDK exposing exactly 5 flat, dead-simple bindings so a 4B SLM can emit
ONE linear batch script (read -> patch -> gate -> test) executed in a single
sub-25s pass instead of 5 sequential multi-minute tool roundtrips.

Design laws (docs/evolution Phase 1.1):
  - Fail-Fast: any method failure immediately aborts execution and raises
    HermesSDKError carrying an exact line-error slice (no silent corruption).
  - Micro-Surface: ONLY read_range / search / apply_patch / run_observer_gate /
    run_test exist. Anything else is a hallucination by definition.
  - Flat Pipelines Only: scripts consuming this SDK must stay linear, <=20 lines.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path


SDK_ROOT = Path(__file__).resolve().parent.parent if (Path(__file__).resolve().parent.parent / "bin").exists() else Path(__file__).resolve().parents[2]

_CONTAINER_PREFIX_CACHE = None


def _container_prefix():
    """
    Resolve the ws-ai distrobox execution prefix via the repo's single source
    of truth (bin/container_cmd.py): plain `distrobox enter ws-ai` on the host,
    or the `flatpak-spawn --host` bridge when already inside a sandbox.
    ALL test/tool execution MUST land inside the ws-ai container toolchain.
    """
    global _CONTAINER_PREFIX_CACHE
    if _CONTAINER_PREFIX_CACHE is None:
        import importlib.util
        spec = importlib.util.spec_from_file_location("container_cmd", SDK_ROOT / "bin" / "container_cmd.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _CONTAINER_PREFIX_CACHE = mod.get_distrobox_cmd()
    return list(_CONTAINER_PREFIX_CACHE)


class HermesSDKError(Exception):
    """Fail-fast abort with an exact surgical error slice."""

    def __init__(self, method: str, detail: str, filepath: str = "", line: int = 0, context: str = ""):
        self.method = method
        self.filepath = filepath
        self.line = line
        self.context = context
        super().__init__(f"[{method}] FAIL: {detail}" + (f" @ {filepath}:{line}" if filepath else "") + (f"\n{context}" if context else ""))


def _resolve(filepath: str) -> Path:
    p = Path(filepath)
    return p if p.is_absolute() else Path(os.environ.get("HERMES_SDK_WORKSPACE", str(SDK_ROOT))) / p


def _line_slice(lines: list, line_no: int, span: int = 2) -> str:
    lo = max(0, line_no - 1 - span)
    hi = min(len(lines), line_no + span)
    return "\n".join(f"{i+1}: {lines[i]}" for i in range(lo, hi))


class HermesSDK:
    """Flat binding surface. 5 methods. Nothing else."""

    def read_range(self, filepath: str, start: int, end: int) -> str:
        target = _resolve(filepath)
        if not target.exists():
            raise HermesSDKError("read", f"File not found: {filepath}", filepath)
        lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
        s = max(1, int(start)) - 1
        e = min(len(lines), int(end))
        if s >= e:
            raise HermesSDKError("read", f"Invalid range {start}-{end} (file has {len(lines)} lines)", filepath)
        return "\n".join(f"{i+s+1}: {lines[i]}" for i in range(s, e))

    def search(self, pattern: str, path: str = ".") -> list:
        root = _resolve(path)
        if not root.exists():
            raise HermesSDKError("search", f"Path not found: {path}", path)
        rx = re.compile(pattern)
        hits = []
        files = root.rglob("*") if root.is_dir() else [root]
        for f in files:
            if not f.is_file() or any(part.startswith(".") for part in f.parts):
                continue
            try:
                for i, ln in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                    if rx.search(ln):
                        hits.append({"file": str(f.relative_to(SDK_ROOT)) if f.is_relative_to(SDK_ROOT) else str(f), "line": i, "text": ln.strip()[:200]})
                        if len(hits) >= 50:
                            return hits
            except Exception:
                continue
        return hits

    def apply_patch(self, filepath: str, old_block: str, new_block: str) -> bool:
        if not old_block.strip():
            raise HermesSDKError("patch", "old_block cannot be empty", filepath)
        if old_block == new_block:
            raise HermesSDKError("patch", "old_block == new_block (no-op rejected)", filepath)
        target = _resolve(filepath)
        if not target.exists():
            raise HermesSDKError("patch", f"File not found: {filepath}", filepath)
        content = target.read_text(encoding="utf-8", errors="replace")
        n = content.count(old_block)
        if n != 1:
            lines = content.splitlines()
            probe_line = next((i + 1 for i, l in enumerate(lines) if old_block.splitlines()[0].strip() in l), 0)
            raise HermesSDKError(
                "patch",
                f"old_block matched {n} times (need exactly 1)",
                filepath,
                probe_line,
                _line_slice(lines, probe_line) if probe_line else "",
            )
        target.write_text(content.replace(old_block, new_block, 1), encoding="utf-8")
        return True

    def run_observer_gate(self, filepath: str) -> dict:
        target = _resolve(filepath)
        if not target.exists():
            raise HermesSDKError("gate", f"File not found: {filepath}", filepath)
        gate = SDK_ROOT / "bin" / "observer_gate.py"
        res = subprocess.run(
            [sys.executable, str(gate), str(target)],
            capture_output=True, text=True, timeout=60,
        )
        try:
            verdict = json.loads(res.stdout)
        except Exception:
            raise HermesSDKError("gate", f"Gate crashed: {res.stderr.strip()[-300:]}", filepath)
        if res.returncode != 0 or not verdict.get("passed"):
            failed = [c for c in verdict.get("checks", []) if not c.get("passed")]
            raise HermesSDKError("gate", "; ".join(c.get("detail", "?") for c in failed) or verdict.get("verdict", "blocked"), filepath)
        return verdict

    def run_test(self, command: str) -> dict:
        if not command.strip():
            raise HermesSDKError("test", "command cannot be empty")
        workspace = os.environ.get("HERMES_SDK_WORKSPACE", str(SDK_ROOT))
        try:
            res = subprocess.run(
                _container_prefix() + ["bash", "-c", command],
                capture_output=True, text=True, timeout=120, cwd=workspace,
            )
        except subprocess.TimeoutExpired:
            raise HermesSDKError("test", "command timed out after 120s", context=command)
        out = (res.stdout + res.stderr).strip()
        if res.returncode != 0:
            tail = "\n".join(out.splitlines()[-5:])
            raise HermesSDKError("test", f"exit={res.returncode}", context=tail)
        return {"passed": True, "output": out[-2000:]}


sdk = HermesSDK()

if __name__ == "__main__":
    print("HermesSDK micro-surface:", sorted(m for m in dir(HermesSDK) if not m.startswith("_")))
