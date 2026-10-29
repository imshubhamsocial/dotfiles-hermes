#!/usr/bin/env python3
"""
Hermes 60% Infrastructure Gate: Ruff Pre-Commit Verification Gate
Executes AST / static analysis verification on code before test execution.
Selects: F821 (undefined names), F841 (unused variables), plus native AST syntax errors.
"""
import subprocess
import sys
import tempfile
from pathlib import Path


def execute_ruff_precommit_gate(
    code_or_file_path: str,
    is_content: bool = True,
    extra_rules: str = "F821,F841"
) -> tuple[bool, int, str]:
    """
    Run ruff pre-commit verification on Python code.
    Returns:
        (passed: bool, error_count: int, report: str)
    """
    if is_content:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tmp:
            tmp.write(code_or_file_path)
            tmp_path = Path(tmp.name)
        target = str(tmp_path)
    else:
        target = code_or_file_path
        tmp_path = None

    try:
        cmd = [
            sys.executable,
            "-m",
            "ruff",
            "check",
            f"--select={extra_rules}",
            target,
        ]
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        passed = res.returncode == 0
        output = (res.stdout + "\n" + res.stderr).strip()

        # Count errors
        error_count = 0
        rules_list = [r.strip() for r in extra_rules.split(",") if r.strip()]
        for line in output.splitlines():
            if ":" in line and (
                any(f": {r}" in line or f":{r}" in line for r in rules_list)
                or "syntax error" in line.lower()
            ):
                error_count += 1
        if not passed and error_count == 0:
            error_count = 1

        return passed, error_count, output
    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: hermes_ruff_precommit.py <file_path>")
        sys.exit(1)
    file_path = sys.argv[1]
    ok, count, rep = execute_ruff_precommit_gate(file_path, is_content=False)
    print(f"Ruff Pre-commit: {'PASSED' if ok else 'FAILED'} (errors: {count})")
    if not ok:
        print(rep)
        sys.exit(1)
