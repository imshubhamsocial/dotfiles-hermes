#!/usr/bin/env python3
"""
Horizon 4 In-Process Verification Harness: Autonomous Internal Self-Diagnosis
& Hermes Self-Repair (TraceFailureAnalyzer, Atomic .bak Patcher, Auto-Rollback)
==============================================================================
Verifies:
  1. Log Diagnostic Engine & Traceback Call-Stack Divergence Extraction
  2. Failure Mode Categorization (Syntax Drift, Broken Import, Plugin Failure)
  3. Atomic Patcher & Automatic .bak Backup Creation
  4. End-to-End Self-Healing of Intentionally Broken Plugin (Gate X.3)
  5. Automatic /rollback Execution on Integrity Regression
  6. CLI Slash Command Dispatch Interface (/loop repair & /loop rollback)
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path

# Resolve hermes-agent path dynamically
_hermes_dir = Path(os.environ.get("HERMES_HOME", Path(__file__).resolve().parents[1]))
for p in [
    _hermes_dir / "hermes-agent",
    Path.home() / ".hermes" / "hermes-agent",
]:
    if p.is_dir() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

from agent.core.meta_harness import AtomicPatcher, HarnessIntegrityGate
from agent.core.self_healer import (
    InternalErrorDiagnostic,
    LogDiagnosticEngine,
    HermesSelfHealer,
)
from hermes_cli.loops import dispatch_loop_command


def verify_traceback_parsing_and_divergence() -> None:
    print("[1/6] Verifying Log Diagnostic Engine & traceback frame divergence isolation...")
    sample_traceback = """
Traceback (most recent call last):
  File "/usr/lib64/python3.14/site-packages/urllib3/connectionpool.py", line 467, in _make_request
    six.reraise(*sys.exc_info())
  File "/home/hermes/.hermes/hermes-agent/plugins/custom_gateway/__init__.py", line 42, in connect
    result = execute_gateway_rpc(target_host, timeout=30)
  File "/home/hermes/.hermes/hermes-agent/agent/core/rpc_bridge.py", line 88, in execute_gateway_rpc
    raise ConnectionRefusedError("Connection refused by peer port 8138")
ConnectionRefusedError: Connection refused by peer port 8138
"""
    diag = LogDiagnosticEngine.parse_traceback(sample_traceback)
    assert diag is not None, "Failed to parse traceback"
    assert diag.error_type == "ConnectionRefusedError"
    assert "agent/core/rpc_bridge.py" in diag.culprit_file
    assert diag.culprit_line == 88
    assert diag.failing_symbol == "execute_gateway_rpc"
    assert len(diag.traceback_frames) == 3
    print(f"  ✓ Culprit frame isolated: {diag.culprit_file}:{diag.culprit_line} ({diag.failing_symbol})")


def verify_failure_mode_categorization() -> None:
    print("[2/6] Verifying failure mode categorization (Syntax, Import, Plugin)...")
    syntax_tb = """
Traceback (most recent call last):
  File "/home/hermes/.hermes/hermes-agent/plugins/broken_plugin/__init__.py", line 15
    def initialize_plugin()
                          ^
SyntaxError: expected ':'
"""
    diag_syntax = LogDiagnosticEngine.parse_traceback(syntax_tb)
    assert diag_syntax.error_category == "SYNTAX_DRIFT"

    import_tb = """
Traceback (most recent call last):
  File "/home/hermes/.hermes/hermes-agent/agent/core/router.py", line 4, in <module>
    from agent.core.missing_module import non_existent_function
ImportError: cannot import name 'non_existent_function' from 'agent.core.missing_module'
"""
    diag_import = LogDiagnosticEngine.parse_traceback(import_tb)
    assert diag_import.error_category == "BROKEN_IMPORT"
    print("  ✓ Failure modes correctly categorized into SYNTAX_DRIFT and BROKEN_IMPORT.")


def verify_atomic_patcher_and_backup(temp_dir: Path) -> None:
    print("[3/6] Verifying Atomic Patcher & mandatory .bak backup creation...")
    test_file = temp_dir / "sample_module.py"
    initial_code = "def sample():\n    return 42\n"
    test_file.write_text(initial_code, encoding="utf-8")

    mutated_code = "def sample():\n    return 100\n"
    receipt = AtomicPatcher.apply_patch(test_file, mutated_code)

    assert receipt.applied
    assert Path(receipt.backup_path).exists(), f"Backup file {receipt.backup_path} must exist"
    assert Path(receipt.backup_path).read_text() == initial_code
    assert test_file.read_text() == mutated_code

    # Verify rollback
    rolled_back = AtomicPatcher.rollback(receipt)
    assert rolled_back
    assert test_file.read_text() == initial_code
    print("  ✓ Atomic patching and .bak rollback verified with checksum integrity.")


def verify_end_to_end_self_healing(temp_dir: Path) -> None:
    print("[4/6] Verifying end-to-end self-healing on broken internal plugin (Gate X.3)...")
    # Create an intentionally broken plugin file (missing colon on function def)
    broken_plugin = temp_dir / "broken_plugin.py"
    broken_code = """
# Broken internal plugin
def handle_incoming_event(event)
    return {"status": "ok", "event": event}
"""
    broken_plugin.write_text(broken_code, encoding="utf-8")

    # Syntax fails initially
    ok_init, _ = HarnessIntegrityGate.verify_syntax(broken_plugin)
    assert not ok_init, "Initial file must fail syntax parse"

    # Simulate traceback
    broken_tb = f"""
Traceback (most recent call last):
  File "{broken_plugin}", line 3
    def handle_incoming_event(event)
                                   ^
SyntaxError: expected ':'
"""
    diag = LogDiagnosticEngine.parse_traceback(broken_tb)
    assert diag is not None

    healer = HermesSelfHealer()
    receipt = healer.execute_self_repair(diag)

    assert receipt.status == "SUCCESS", f"Expected repair SUCCESS, got {receipt.status}: {receipt.remediation_summary}"
    assert "Repaired missing colon" in receipt.remediation_summary

    # Verify file now parses clean
    ok_post, msg_post = HarnessIntegrityGate.verify_syntax(broken_plugin)
    assert ok_post, f"Post-repair file must parse clean: {msg_post}"
    assert "def handle_incoming_event(event):" in broken_plugin.read_text()
    print("  ✓ Intentionally broken plugin successfully diagnosed and self-repaired in-process.")


def verify_automatic_rollback_on_regression(temp_dir: Path) -> None:
    print("[5/6] Verifying automatic /rollback execution upon post-patch regression...")
    original_file = temp_dir / "fragile_system.py"
    pristine_code = """
def stable_operation(x: int) -> int:
    return x * 2
"""
    original_file.write_text(pristine_code, encoding="utf-8")

    # Malformed patch that introduces an invalid syntax error
    bad_patch = """
def stable_operation(x: int) -> int:
    return x * 2 ??? ILLEGAL SYNTAX ???
"""
    diag = InternalErrorDiagnostic(
        error_type="SyntaxError",
        error_message="testing regression rollback",
        culprit_file=str(original_file),
        culprit_line=2,
        failing_symbol="stable_operation",
        error_category="SYNTAX_DRIFT",
    )

    healer = HermesSelfHealer()
    receipt = healer.execute_self_repair(diag, repaired_content=bad_patch)

    assert receipt.status == "ROLLEDBACK", f"Expected ROLLEDBACK status, got {receipt.status}"
    assert "Automatic /rollback executed" in receipt.integrity_message

    # Confirm original file was restored to pristine condition
    restored_code = original_file.read_text(encoding="utf-8")
    assert restored_code == pristine_code, "Original file must be restored byte-for-byte after rollback"
    print("  ✓ Regression immediately triggered automatic /rollback; pristine file preserved.")


def verify_cli_repair_commands() -> None:
    print("[6/6] Verifying CLI slash command integration (/loop repair & /loop rollback)...")
    # Test dispatching /loop repair
    res_repair = dispatch_loop_command(None, "repair")
    assert "output" in res_repair
    assert "[Self-Repair" in res_repair["output"]

    # Test dispatching /loop rollback
    res_rollback = dispatch_loop_command(None, "rollback")
    assert "output" in res_rollback
    assert "[Rollback]" in res_rollback["output"]
    print("  ✓ CLI /loop repair and /loop rollback command dispatch verified.")


def main():
    print("=" * 66)
    print("  HORIZON 4 IN-PROCESS VERIFICATION: HERMES SELF-REPAIR ENGINE    ")
    print("  (Log Diagnostic, Culprit Frame Isolation, Auto-Rollback)       ")
    print("=" * 66)

    temp_dir = Path(tempfile.mkdtemp(prefix="hermes_self_repair_test_"))
    try:
        verify_traceback_parsing_and_divergence()
        verify_failure_mode_categorization()
        verify_atomic_patcher_and_backup(temp_dir)
        verify_end_to_end_self_healing(temp_dir)
        verify_automatic_rollback_on_regression(temp_dir)
        verify_cli_repair_commands()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    print("=" * 66)
    print("  ✅ HORIZON 4 VERIFICATION 100% COMPLETE — ALL CONTRACTS GREEN   ")
    print("=" * 66)


if __name__ == "__main__":
    main()
