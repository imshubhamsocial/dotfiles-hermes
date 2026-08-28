"""
U2: Event-Driven Lifecycle Hooks (pre_tool_call / post_tool_call)
=================================================================
Roadmap Phase 2.1 — turns the manual Observer Gate into an automatic law:

  pre_tool_call : every mutating tool payload (write_file / patch_file) is
                  validated BEFORE it can touch disk. Rejection returns an
                  EXACT 5-line surgical error slice (Trap-1 countermeasure:
                  precise slices prevent 4B re-emission death spirals).
                  Patches additionally pass the U12 AST Diff Size Gate.
  post_tool_call: successful mutations trigger a shadow snapshot into
                  ephemeral RAMdisk (/dev/shm, btrfs zero-wear Rule) plus a
                  structured TrajectoryEvent line for later distillation.

Hooks are deterministic Python — no LLM self-grading (Zero-Sorry rule).
"""

import json
import re
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

RAMDISK = Path("/dev/shm")
SHADOW_DIR = RAMDISK / "hermes_shadow"

_MUTATING_TOOLS = {"write_file", "patch_file"}
_DANGEROUS = [
    (r"\beval\s*\(", "eval() call detected"),
    (r"\bnew\s+Function\s*\(", "Function constructor detected"),
    (r"__proto__\s*[=\[]", "__proto__ mutation detected"),
    (r":\(\)\{ :\|:& \};:", "fork bomb detected"),
]


def _load_observer_gate():
    import importlib.util
    candidates = [
        Path.home() / ".hermes" / "bin" / "observer_gate.py",
        Path(__file__).resolve().parents[2] / ".hermes" / "bin" / "observer_gate.py",
        Path(__file__).resolve().parents[1] / ".hermes" / "bin" / "observer_gate.py",
    ]
    gate_path = next((p for p in candidates if p.exists()), candidates[0])
    spec = importlib.util.spec_from_file_location("observer_gate_hooks", gate_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _workspace_root() -> Path:
    from .tools import DEFAULT_WORKSPACE
    return DEFAULT_WORKSPACE


def _resolve(filepath: str) -> Path:
    p = Path(filepath)
    root = _workspace_root()
    return p if p.is_absolute() else root / p


def error_slice(content: str, line_no: int, span: int = 5) -> str:
    """Exact <=5-line numbered slice centered on the defect line."""
    lines = content.splitlines()
    lo = max(0, min(line_no, len(lines)) - 3)
    hi = min(len(lines), lo + span)
    lo = max(0, hi - span)
    return "\n".join(f"{i+1}: {lines[i]}" for i in range(lo, hi))


def _syntax_defect(filepath: str, content: str) -> Optional[Tuple[int, str]]:
    """Language-appropriate syntax probe. Returns (line_no, message) or None."""
    suffix = Path(filepath).suffix.lower()
    if suffix == ".py":
        import ast
        try:
            ast.parse(content)
            return None
        except SyntaxError as e:
            return (e.lineno or 1, f"Python SyntaxError: {e.msg}")
    if suffix in {".js", ".html", ".htm"}:
        og = _load_observer_gate()
        if suffix == ".js":
            verdict = og.check_brace_balance(f"<script>{content}</script>")
            if not verdict["passed"]:
                return (1, f"JS structure: {verdict['detail']}")
        else:
            verdict = og.check_brace_balance(content)
            if not verdict["passed"]:
                return (1, f"HTML/JS structure: {verdict['detail']}")
        for pat, desc in _DANGEROUS:
            if re.search(pat, content):
                m = re.search(pat, content)
                line_no = content[:m.start()].count("\n") + 1
                return (line_no, desc)
    return None


class LifecycleHookEngine:
    """Registry-free static engine; one instance per orchestrator loop."""

    def __init__(self):
        self._og = None

    @property
    def observer_gate(self):
        if self._og is None:
            self._og = _load_observer_gate()
        return self._og

    # ------------------------------------------------------------------
    def pre_tool_call(self, role: str, tool_name: str, params: Dict) -> Tuple[bool, str]:
        if tool_name not in _MUTATING_TOOLS:
            return True, "no hook for read-only tool."

        if tool_name == "write_file":
            filepath = params.get("filepath", "")
            content = params.get("content", "")
            defect = _syntax_defect(filepath, content)
            if defect:
                line_no, msg = defect
                return False, (
                    f"PRE_TOOL_CALL REJECTED [{tool_name}] {filepath}:{line_no} — {msg}\n"
                    + error_slice(content, line_no)
                )
            return True, "payload validated."

        if tool_name == "patch_file":
            filepath = params.get("filepath", "")
            old_block = params.get("target_block", "")
            new_block = params.get("replacement_block", "")
            if not old_block.strip():
                return False, "PRE_TOOL_CALL REJECTED [patch_file]: empty target_block."
            if old_block == new_block:
                return False, "PRE_TOOL_CALL REJECTED [patch_file]: no-op patch."

            # U12 AST Diff Size Gate (bloat >3x + sibling obliteration).
            g7 = self.observer_gate.check_ast_diff_size(old_block, new_block)
            if not g7["passed"]:
                return False, f"PRE_TOOL_CALL REJECTED [patch_file]: {g7['detail']}"

            target = _resolve(filepath)
            if target.exists():
                content = target.read_text(encoding="utf-8", errors="replace")
                if content.count(old_block) == 1:
                    defect = _syntax_defect(filepath, content.replace(old_block, new_block, 1))
                    if defect:
                        line_no, msg = defect
                        return False, (
                            f"PRE_TOOL_CALL REJECTED [patch_file] {filepath}:{line_no} — "
                            f"{msg}\n" + error_slice(content.replace(old_block, new_block, 1), line_no)
                        )
            return True, "patch payload validated."

        return True, "allowed."

    # ------------------------------------------------------------------
    def post_tool_call(self, tool_name: str, params: Dict, result: str) -> Dict:
        event = {
            "ts": int(time.time() * 1000),
            "tool": tool_name,
            "params_head": {k: str(v)[:80] for k, v in params.items()},
            "ok": not str(result).lower().startswith(("error", "rejected")),
            "shadow_snapshot": None,
        }
        if tool_name in _MUTATING_TOOLS and event["ok"]:
            snapshot_path = self._shadow_snapshot(params.get("filepath", ""))
            event["shadow_snapshot"] = str(snapshot_path) if snapshot_path else None
        try:
            SHADOW_DIR.mkdir(parents=True, exist_ok=True)
            with open(SHADOW_DIR / "events.jsonl", "a", encoding="utf-8") as fh:
                fh.write(json.dumps(event) + "\n")
        except Exception:
            pass
        return event

    def _shadow_snapshot(self, filepath: str) -> Optional[Path]:
        try:
            src = _resolve(filepath)
            if not src.exists():
                return None
            SHADOW_DIR.mkdir(parents=True, exist_ok=True)
            dst = SHADOW_DIR / f"{int(time.time()*1000)}_{Path(filepath).name}"
            dst.write_bytes(src.read_bytes())
            return dst
        except Exception:
            return None


if __name__ == "__main__":
    eng = LifecycleHookEngine()
    ok, msg = eng.pre_tool_call("coder", "write_file", {"filepath": "t.py", "content": "def x(:\n  pass"})
    print(ok, "|", msg[:120])
