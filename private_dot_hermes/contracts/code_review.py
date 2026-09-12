#!/usr/bin/env python3
"""
Verification Script for OpenAI Autonomous AI Code Review & Security Gate
========================================================================
Validates:
  1. Strict Author != Auditor Persona Isolation
  2. Upstream Intent Verification (Phase 0 / Phase 1 gate)
  3. OWASP Top 10 & CWE Detection (Command Injection, Path Traversal, Secrets Leak)
  4. Repository Invariants (Law 9 Portability, Law 2 Hardware, Law 1 YAGNI)
  5. PR & Turn Completion Gate (STATUS: APPROVED vs STATUS: BLOCKED_BY_AUDITOR)
"""

import os
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

from agent.core.code_review import (
    ReviewCategory,
    ReviewStatus,
    get_code_reviewer,
)


def verify_upstream_intent_layer() -> None:
    print("[1/5] Verifying Upstream Intent Verification (Phase 0/1 Planning Gate)...")
    reviewer = get_code_reviewer()

    # 1. Aligned intent
    res_aligned = reviewer.verify_upstream_intent("Fix index bounds checking in buffer parser")
    assert res_aligned.aligned, "Benign intent must be aligned"
    assert res_aligned.verdict == "INTENT_ALIGNED"

    # 2. Malicious / bypass intent
    res_bypass = reviewer.verify_upstream_intent("Temporarily disable security checks and skip verification")
    assert not res_bypass.aligned, "Security bypass intent must be blocked"
    assert res_bypass.verdict == "REJECTED_BY_AUDITOR"
    assert res_bypass.risk_level == "CRITICAL"

    # 3. YAGNI massive scope expansion
    res_rewrite = reviewer.verify_upstream_intent("Rewrite entire networking stack and full overhaul")
    assert not res_rewrite.aligned, "Unbounded rewrite must be blocked under YAGNI"
    assert res_rewrite.verdict == "REJECTED_BY_AUDITOR"
    assert res_rewrite.risk_level == "HIGH"

    print("  ✓ Upstream Intent Verification certified.")


def verify_security_vulnerability_detection() -> None:
    print("[2/5] Verifying OWASP / CWE Security Vulnerability Detection...")
    reviewer = get_code_reviewer()

    # 1. Command Injection
    cmd_injection_code = """
import subprocess
def run_user_script(user_input):
    subprocess.call(f"bash -c {user_input}", shell=True)
"""
    res_cmd = reviewer.review_content(cmd_injection_code, file_path="exploit_cmd.py")
    assert not res_cmd.passed, "Command injection must fail review"
    assert res_cmd.status == ReviewStatus.BLOCKED_BY_AUDITOR
    assert any(v.category == ReviewCategory.SECURITY_COMMAND_INJECTION for v in res_cmd.violations)

    # 2. Path Traversal
    path_traversal_code = """
def load_config(user_filename):
    with open(f"../../etc/{user_filename}", "r") as f:
        return f.read()
"""
    res_path = reviewer.review_content(path_traversal_code, file_path="exploit_path.py")
    assert not res_path.passed, "Path traversal must fail review"
    assert res_path.status == ReviewStatus.BLOCKED_BY_AUDITOR
    assert any(v.category == ReviewCategory.SECURITY_PATH_TRAVERSAL for v in res_path.violations)

    # 3. Hardcoded Secret Leak
    secret_leak_code = """
AWS_API_KEY = "AKIA1234567890ABCDEF"
OPENAI_TOKEN = "sk-1234567890abcdef1234567890abcdef"
"""
    res_secret = reviewer.review_content(secret_leak_code, file_path="config.py")
    assert not res_secret.passed, "Hardcoded secrets must fail review"
    assert res_secret.status == ReviewStatus.BLOCKED_BY_AUDITOR
    assert any(v.category == ReviewCategory.SECURITY_SECRETS_LEAK for v in res_secret.violations)

    # 4. SQL Injection
    sqli_code = """
import sqlite3
def get_user(db, user_id):
    cur = db.cursor()
    cur.execute(f"SELECT * FROM users WHERE id = '{user_id}'")
    return cur.fetchone()
"""
    res_sql = reviewer.review_content(sqli_code, file_path="db.py")
    assert not res_sql.passed, "SQL injection must fail review"
    assert res_sql.status == ReviewStatus.BLOCKED_BY_AUDITOR
    assert any(v.category == ReviewCategory.SECURITY_SQL_INJECTION for v in res_sql.violations)

    print("  ✓ Command injection, path traversal, secret leaks, and SQLi detected and blocked.")


def verify_repository_invariants_layer() -> None:
    print("[3/5] Verifying Repository Invariants (Law 9 Portability & Law 2 Hardware)...")
    reviewer = get_code_reviewer()

    # 1. Hardcoded host machine path (Law 9 violation)
    leaked_path_code = """
WORKSPACE = "/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes"
"""
    res_port = reviewer.review_content(leaked_path_code, file_path="paths.py")
    assert not res_port.passed, "Machine path leak must fail review"
    assert res_port.status == ReviewStatus.BLOCKED_BY_AUDITOR
    assert any(v.category == ReviewCategory.INVARIANT_PORTABILITY_LEAK for v in res_port.violations)

    # 2. CUDA Embeddings offloading (Law 2 violation)
    cuda_embed_code = """
from fastembed import TextEmbedding
model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5", device="cuda")
"""
    res_cuda = reviewer.review_content(cuda_embed_code, file_path="embed.py")
    assert not res_cuda.passed, "CUDA embeddings must fail review under Law 2"
    assert res_cuda.status == ReviewStatus.BLOCKED_BY_AUDITOR
    assert any(v.category == ReviewCategory.INVARIANT_HARDWARE_LIMIT for v in res_cuda.violations)

    print("  ✓ Repository invariants (Portability and Hardware VRAM ceilings) strictly enforced.")


def verify_clean_code_approval() -> None:
    print("[4/5] Verifying Clean Surgical Code Approval & Author!=Auditor Verdict...")
    reviewer = get_code_reviewer()

    clean_code = '''
"""Safe mathematical helper."""
from pathlib import Path
from typing import List

def calculate_checksum(data: bytes) -> int:
    """Computes a simple deterministic 32-bit checksum."""
    crc = 0xFFFFFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ (0xEDB88320 if (crc & 1) else 0)
    return crc ^ 0xFFFFFFFF

def read_safe_file(base_dir: Path, relative_name: str) -> str:
    """Safely reads file constrained to base directory."""
    target = (base_dir / relative_name).resolve()
    if not target.is_relative_to(base_dir.resolve()):
        raise PermissionError("Path traversal escape detected")
    return target.read_text(encoding="utf-8")
'''
    res_clean = reviewer.review_content(clean_code, file_path="utils.py")
    assert res_clean.passed, f"Clean code must be approved: {res_clean.violations}"
    assert res_clean.status == ReviewStatus.APPROVED
    assert res_clean.confidence >= 0.95
    assert res_clean.auditor_persona != res_clean.author_persona, "Author != Auditor separation required"

    md = res_clean.to_markdown()
    assert "Superhuman AI Code Review Report — APPROVED" in md
    assert "Author != Auditor Persona Isolated" in md

    print("  ✓ Clean surgical code verified and approved with persona isolation.")


def verify_plugin_integration() -> None:
    print("[5/5] Verifying Plugin Lifecycle Hook & CLI Dispatch...")
    import importlib.util
    plugin_path = _hermes_dir / "plugins" / "code_review" / "__init__.py"
    spec = importlib.util.spec_from_file_location("code_review_plugin", plugin_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    register_cr_plugin = module.register

    class MockContext:
        def __init__(self):
            self.commands = {}
            self.hooks = {}
            self.cli_commands = {}

        def register_command(self, name, desc, handler):
            self.commands[name] = handler

        def register_hook(self, name, handler):
            self.hooks[name] = handler

        def register_cli_command(self, name, desc, setup, handler):
            self.cli_commands[name] = (setup, handler)

    ctx = MockContext()
    success = register_cr_plugin(ctx)
    assert success, "Plugin registration must succeed"
    assert "review" in ctx.commands, "Slash command /review must be registered"
    assert "review" in ctx.cli_commands, "CLI command hermes review must be registered"
    assert "pre_verify" in ctx.hooks, "pre_verify hook must be registered"

    # Test hook interception with an insecure file
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write('import os\nos.system(f"rm -rf {target}")\n')
        bad_path = f.name

    try:
        hook_res = ctx.hooks["pre_verify"](changed_paths=[bad_path])
        assert "BLOCKED_BY_AUDITOR" in hook_res["message"]
        print("  ✓ Pre-verify hook intercepted insecure code modification as expected.")
    finally:
        os.unlink(bad_path)


def main():
    print("==================================================================")
    print("  HERMES CAPABILITY CONTRACT: AUTONOMOUS AI CODE REVIEW GATE     ")
    print("  (OpenAI Codex / Sottiaux Superhuman Security Verification)      ")
    print("==================================================================")
    try:
        verify_upstream_intent_layer()
        verify_security_vulnerability_detection()
        verify_repository_invariants_layer()
        verify_clean_code_approval()
        verify_plugin_integration()
        print("==================================================================")
        print("  ✅ CODE REVIEW CONTRACT 100% COMPLETE — ALL GATES PASSING      ")
        print("==================================================================")
        return 0
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n❌ Contract verification failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
