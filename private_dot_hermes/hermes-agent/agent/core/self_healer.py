"""
Hermes Self-Repair Diagnostic Loop & Trace Failure Analyzer (Horizon 4)
=======================================================================
Autonomous internal self-diagnosis and self-repair for Hermes Agent OS:
  - Ingests uncaught exceptions and tracebacks from ~/.hermes/logs/
  - Analyzes traceback call stack to isolate earliest point of divergence
  - Creates atomic .bak backups before code mutations
  - Validates harness integrity post-repair
  - Executes automatic /rollback upon regression or test failure
"""

from __future__ import annotations

import ast
import os
import re
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .meta_harness import AtomicPatcher, HarnessIntegrityGate, PatchReceipt


@dataclass
class InternalErrorDiagnostic:
    """Structured diagnosis of an internal Hermes exception."""
    error_type: str
    error_message: str
    culprit_file: str
    culprit_line: int
    failing_symbol: str
    traceback_frames: List[Dict[str, Any]] = field(default_factory=list)
    root_cause_frame: Dict[str, Any] = field(default_factory=dict)
    context_snippet: str = ""
    error_category: str = "UNKNOWN"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_type": self.error_type,
            "error_message": self.error_message,
            "culprit_file": self.culprit_file,
            "culprit_line": self.culprit_line,
            "failing_symbol": self.failing_symbol,
            "error_category": self.error_category,
            "frames_count": len(self.traceback_frames),
            "root_cause_frame": self.root_cause_frame,
            "context_snippet": self.context_snippet,
        }


@dataclass
class SelfRepairReceipt:
    """Structured receipt documenting self-repair outcome."""
    repair_id: str
    status: str  # SUCCESS, ROLLEDBACK, NO_REPAIR_NEEDED, CANNOT_REPAIR
    culprit_file: str
    culprit_line: int
    error_type: str
    integrity_message: str
    remediation_summary: str
    patch_receipt: Optional[PatchReceipt] = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repair_id": self.repair_id,
            "status": self.status,
            "culprit_file": self.culprit_file,
            "culprit_line": self.culprit_line,
            "error_type": self.error_type,
            "integrity_message": self.integrity_message,
            "remediation_summary": self.remediation_summary,
            "reverted": self.patch_receipt.reverted if self.patch_receipt else False,
            "timestamp": self.timestamp,
        }


class LogDiagnosticEngine:
    """
    Parses ~/.hermes/logs/agent.log and errors.log or raw traceback strings
    to locate failing internal modules and stack frames.
    """

    DEFAULT_LOGS_DIR = Path.home() / ".hermes/logs"

    @classmethod
    def parse_traceback(cls, tb_str: str) -> Optional[InternalErrorDiagnostic]:
        """
        Parses a standard Python traceback string to extract stack frames,
        culprit file, line number, and root-cause exception.
        """
        lines = tb_str.strip().splitlines()
        if not lines:
            return None

        # Regex matching: File "/path/to/file.py", line 123, in func_name
        frame_re = re.compile(r'File "([^"]+)", line (\d+)(?:, in ([\w<>]+))?')
        frames: List[Dict[str, Any]] = []

        for line in lines:
            m = frame_re.search(line)
            if m:
                frames.append({
                    "file": m.group(1),
                    "line": int(m.group(2)),
                    "func": m.group(3) or "<module>",
                })

        # Last line typically contains: ExceptionType: message
        last_line = lines[-1].strip()
        exc_match = re.match(r"^([A-Za-z0-9_]+Error|[A-Za-z0-9_]+Exception|Exception):\s*(.*)$", last_line)
        if exc_match:
            error_type = exc_match.group(1)
            error_msg = exc_match.group(2)
        else:
            error_type = "RuntimeError"
            error_msg = last_line

        if not frames:
            return None

        # Isolate earliest internal Hermes frame (root-cause)
        # Avoid external libraries or site-packages
        internal_frames = [
            f for f in frames
            if (".hermes" in f["file"] or "hermes-agent" in f["file"] or "agent/core" in f["file"])
            and "site-packages" not in f["file"]
        ]

        # Target the deepest internal frame where the error surfaced
        culprit = internal_frames[-1] if internal_frames else frames[-1]

        # Read context snippet
        snippet = ""
        c_path = Path(culprit["file"])
        if c_path.exists():
            try:
                src_lines = c_path.read_text(encoding="utf-8", errors="replace").splitlines()
                idx = culprit["line"] - 1
                start = max(0, idx - 2)
                end = min(len(src_lines), idx + 3)
                snippet = "\n".join(
                    f"{'>' if i == idx else ' '} {i+1}: {src_lines[i]}"
                    for i in range(start, end)
                )
            except Exception:
                pass

        # Classify error category
        category = "UNKNOWN"
        if "SyntaxError" in error_type:
            category = "SYNTAX_DRIFT"
        elif "ImportError" in error_type or "ModuleNotFoundError" in error_type:
            category = "BROKEN_IMPORT"
        elif "AttributeError" in error_type:
            category = "ATTRIBUTE_REGRESSION"
        elif "Plugin" in error_type or "plugin" in culprit["file"]:
            category = "PLUGIN_COLLISION"

        return InternalErrorDiagnostic(
            error_type=error_type,
            error_message=error_msg,
            culprit_file=culprit["file"],
            culprit_line=culprit["line"],
            failing_symbol=culprit["func"],
            traceback_frames=frames,
            root_cause_frame=culprit,
            context_snippet=snippet,
            error_category=category,
        )

    @classmethod
    def read_recent_errors(cls, logs_dir: Optional[Path] = None, max_lines: int = 150) -> Optional[InternalErrorDiagnostic]:
        """Reads recent error entries from ~/.hermes/logs/errors.log."""
        ld = Path(logs_dir) if logs_dir else cls.DEFAULT_LOGS_DIR
        err_log = ld / "errors.log"
        if not err_log.exists():
            return None

        try:
            content = err_log.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()[-max_lines:]
            tail_text = "\n".join(lines)

            # Search for Traceback (most recent call last)
            if "Traceback (most recent call last):" in tail_text:
                parts = tail_text.split("Traceback (most recent call last):")
                latest_tb = "Traceback (most recent call last):" + parts[-1]
                return cls.parse_traceback(latest_tb)
        except Exception:
            pass

        return None


class TraceFailureAnalyzer:
    """
    Analyzes root-cause failure diagnostics and generates surgical patches.
    """

    @classmethod
    def synthesize_patch(
        cls,
        diagnostic: InternalErrorDiagnostic,
        custom_fix: Optional[str] = None,
    ) -> Tuple[bool, str, str]:
        """
        Synthesizes a minimal surgical replacement for the culprit file.
        Returns: (can_repair: bool, explanation: str, new_content: str)
        """
        c_path = Path(diagnostic.culprit_file)
        if not c_path.exists():
            return False, f"Culprit file does not exist: {c_path}", ""

        old_content = c_path.read_text(encoding="utf-8", errors="replace")

        # If custom replacement is explicitly provided
        if custom_fix is not None:
            return True, "Applied custom targeted remediation.", custom_fix

        # Automatic repair for common syntax errors
        if diagnostic.error_category == "SYNTAX_DRIFT":
            lines = old_content.splitlines()
            line_idx = diagnostic.culprit_line - 1
            if 0 <= line_idx < len(lines):
                target_line = lines[line_idx]

                # Case A: Missing colon at end of def/class/if/for/while
                if re.match(r"^\s*(def|class|if|elif|else|for|while|try|except|finally|with)\b", target_line) and not target_line.rstrip().endswith(":"):
                    lines[line_idx] = target_line.rstrip() + ":"
                    new_content = "\n".join(lines) + ("\n" if old_content.endswith("\n") else "")
                    return True, f"Repaired missing colon on line {diagnostic.culprit_line}.", new_content

                # Case B: Trailing illegal syntax artifact (e.g. rogue prompt markers)
                if any(target_line.strip().endswith(m) for m in [";;", "```", "===="]):
                    lines[line_idx] = re.sub(r"(;;|```|====)+$", "", target_line).rstrip()
                    new_content = "\n".join(lines) + ("\n" if old_content.endswith("\n") else "")
                    return True, f"Repaired rogue delimiter on line {diagnostic.culprit_line}.", new_content

        # Automatic repair for missing/broken import
        if diagnostic.error_category == "BROKEN_IMPORT":
            # Check if import can be safely guarded with try...except
            lines = old_content.splitlines()
            line_idx = diagnostic.culprit_line - 1
            if 0 <= line_idx < len(lines):
                target_line = lines[line_idx]
                if target_line.strip().startswith(("import ", "from ")):
                    indent = len(target_line) - len(target_line.lstrip())
                    spaces = " " * indent
                    wrapped = (
                        f"{spaces}try:\n"
                        f"{spaces}    {target_line.strip()}\n"
                        f"{spaces}except (ImportError, ModuleNotFoundError):\n"
                        f"{spaces}    pass"
                    )
                    lines[line_idx] = wrapped
                    new_content = "\n".join(lines) + ("\n" if old_content.endswith("\n") else "")
                    return True, f"Wrapped failing import on line {diagnostic.culprit_line} with safe fallback.", new_content

        return False, f"Could not determine automated surgical patch for {diagnostic.error_type}: {diagnostic.error_message}", ""


class HermesSelfHealer:
    """
    Self-Repair Orchestrator (Horizon 4):
    Integrates diagnosis, atomic backup, surgical patching, integrity verification,
    and automatic rollback.
    """

    def __init__(self):
        self.last_receipt: Optional[SelfRepairReceipt] = None

    def execute_self_repair(
        self,
        diagnostic: InternalErrorDiagnostic,
        repaired_content: Optional[str] = None,
        verification_script: Optional[Path] = None,
    ) -> SelfRepairReceipt:
        """
        Executes atomic self-repair workflow:
          1. Synthesize patch
          2. Create .bak backup & write patch
          3. Verify integrity
          4. If green: keep patch & finalize
          5. If red: immediately rollback
        """
        repair_id = f"repair-{uuid.uuid4().hex[:8]}"
        culprit = Path(diagnostic.culprit_file)

        # 1. Synthesize patch
        can_repair, explanation, new_content = TraceFailureAnalyzer.synthesize_patch(
            diagnostic=diagnostic,
            custom_fix=repaired_content,
        )

        if not can_repair:
            return SelfRepairReceipt(
                repair_id=repair_id,
                status="CANNOT_REPAIR",
                culprit_file=diagnostic.culprit_file,
                culprit_line=diagnostic.culprit_line,
                error_type=diagnostic.error_type,
                integrity_message="Synthesis failed",
                remediation_summary=explanation,
            )

        # 2. Atomic backup & application
        try:
            patch_receipt = AtomicPatcher.apply_patch(culprit, new_content)
        except Exception as e:
            return SelfRepairReceipt(
                repair_id=repair_id,
                status="CANNOT_REPAIR",
                culprit_file=diagnostic.culprit_file,
                culprit_line=diagnostic.culprit_line,
                error_type=diagnostic.error_type,
                integrity_message="Failed to write atomic patch",
                remediation_summary=str(e),
            )

        # 3. Post-patch verification
        passed, ver_msg = HarnessIntegrityGate.verify_patch_integrity(
            target_path=culprit,
            verification_script=verification_script,
        )

        # 4. Success vs Rollback
        if passed:
            AtomicPatcher.finalize(patch_receipt, keep_backup=True)
            receipt = SelfRepairReceipt(
                repair_id=repair_id,
                status="SUCCESS",
                culprit_file=diagnostic.culprit_file,
                culprit_line=diagnostic.culprit_line,
                error_type=diagnostic.error_type,
                integrity_message=ver_msg,
                remediation_summary=explanation,
                patch_receipt=patch_receipt,
            )
        else:
            # Immediate atomic rollback
            AtomicPatcher.rollback(patch_receipt)
            receipt = SelfRepairReceipt(
                repair_id=repair_id,
                status="ROLLEDBACK",
                culprit_file=diagnostic.culprit_file,
                culprit_line=diagnostic.culprit_line,
                error_type=diagnostic.error_type,
                integrity_message=f"Regression detected: {ver_msg}. Automatic /rollback executed.",
                remediation_summary="Rollback executed. Original file state restored cleanly.",
                patch_receipt=patch_receipt,
            )

        self.last_receipt = receipt
        return receipt

    def rollback_last(self) -> bool:
        """Explicit /rollback command execution."""
        if self.last_receipt and self.last_receipt.patch_receipt:
            return AtomicPatcher.rollback(self.last_receipt.patch_receipt)
        return False


_GLOBAL_SELF_HEALER: Optional[HermesSelfHealer] = None

def get_self_healer() -> HermesSelfHealer:
    global _GLOBAL_SELF_HEALER
    if _GLOBAL_SELF_HEALER is None:
        _GLOBAL_SELF_HEALER = HermesSelfHealer()
    return _GLOBAL_SELF_HEALER
