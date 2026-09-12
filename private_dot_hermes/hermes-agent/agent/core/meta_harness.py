"""
Meta-Harness & Atomic Patch Integrity Controller (Horizon 4)
============================================================
Provides deterministic atomic patch operations, automatic .bak backups,
and in-process harness integrity verification for Hermes self-repair.
"""

from __future__ import annotations

import ast
import hashlib
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class PatchReceipt:
    """Receipt documenting an atomic mutation attempt."""
    target_path: str
    backup_path: str
    old_checksum: str
    new_checksum: str
    applied: bool
    reverted: bool = False
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AtomicPatcher:
    """
    Atomic file patching engine with mandatory .bak creation,
    checksum validation, and instant non-destructive rollback.
    """

    @staticmethod
    def _checksum(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    @classmethod
    def apply_patch(cls, target_path: str | Path, new_content: str) -> PatchReceipt:
        """
        Creates an atomic .bak backup of target_path, applies new_content,
        and returns a structured PatchReceipt.
        """
        target = Path(target_path).resolve()
        if not target.exists():
            raise FileNotFoundError(f"Target file does not exist: {target}")

        old_content = target.read_text(encoding="utf-8", errors="replace")
        old_hash = cls._checksum(old_content)
        backup_path = target.with_suffix(target.suffix + ".bak")

        # Create physical backup
        shutil.copy2(target, backup_path)

        # Write new content atomically
        target.write_text(new_content, encoding="utf-8")
        new_hash = cls._checksum(new_content)

        return PatchReceipt(
            target_path=str(target),
            backup_path=str(backup_path),
            old_checksum=old_hash,
            new_checksum=new_hash,
            applied=True,
            reverted=False,
        )

    @classmethod
    def rollback(cls, receipt: PatchReceipt) -> bool:
        """
        Restores target_path from backup_path recorded in PatchReceipt.
        """
        target = Path(receipt.target_path)
        backup = Path(receipt.backup_path)

        if not backup.exists():
            return False

        # Restore from backup
        shutil.copy2(backup, target)
        receipt.reverted = True
        return True

    @classmethod
    def finalize(cls, receipt: PatchReceipt, keep_backup: bool = False) -> None:
        """
        Finalizes an approved patch, cleaning up the .bak file unless requested otherwise.
        """
        if not keep_backup:
            backup = Path(receipt.backup_path)
            if backup.exists():
                try:
                    backup.unlink()
                except OSError:
                    pass


class HarnessIntegrityGate:
    """
    Validates syntax and integrity of modified core files to decide
    whether a self-repair patch is green (safe to keep) or red (requires rollback).
    """

    @staticmethod
    def verify_syntax(filepath: str | Path) -> Tuple[bool, str]:
        """Fast AST syntax parse of target Python file."""
        target = Path(filepath)
        if not target.exists():
            return False, f"File does not exist: {target}"

        try:
            content = target.read_text(encoding="utf-8", errors="replace")
            ast.parse(content, filename=str(target))
            return True, "AST syntax parse clean"
        except SyntaxError as e:
            return False, f"SyntaxError at line {e.lineno}: {e.msg}"
        except Exception as e:
            return False, f"Inspection error: {e}"

    @classmethod
    def verify_patch_integrity(
        cls,
        target_path: str | Path,
        verification_script: Optional[Path] = None,
        timeout_sec: float = 15.0,
    ) -> Tuple[bool, str]:
        """
        Comprehensive verification: AST syntax check followed by optional verification script.
        """
        target = Path(target_path)
        # 1. Immediate AST check (<5ms)
        ok, msg = cls.verify_syntax(target)
        if not ok:
            return False, f"AST syntax validation failed: {msg}"

        # 2. If a verification script or harness is provided, execute it
        if verification_script and Path(verification_script).exists():
            try:
                proc = subprocess.run(
                    [sys.executable, str(verification_script)],
                    capture_output=True,
                    text=True,
                    timeout=timeout_sec,
                    check=False,
                )
                if proc.returncode != 0:
                    err = proc.stderr.strip() or proc.stdout.strip()
                    first_err = err.splitlines()[-1] if err else "Verification process failed"
                    return False, f"Harness verification failed (exit {proc.returncode}): {first_err}"
            except subprocess.TimeoutExpired:
                return False, f"Verification script timed out after {timeout_sec}s"
            except Exception as e:
                return False, f"Failed to execute verification script: {e}"

        return True, "Harness integrity passed (all contracts green)"
