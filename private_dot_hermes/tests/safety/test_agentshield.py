"""
Contract Tests: Pillar V — ECC Security & AgentShield Hardening
================================================================
Validates:
  1. SecretScanner clean text produces zero false positives.
  2. SecretScanner detects OpenAI API key pattern and masks token.
  3. SecretScanner detects GitHub personal access token (PAT).
  4. SecretScanner detects PEM private key headers.
  5. SecretScanner Shannon entropy math correctly separates high/low variance strings.
  6. SecretScanner detects high-entropy tokens without known prefixes.
  7. SecretScanner scans clean files and returns clean=True.
  8. SecretScanner scans leaking files and identifies line findings.
  9. BlastRadiusCalculator handles new files with minimal risk score.
 10. BlastRadiusCalculator extracts Python AST exported symbols.
 11. BlastRadiusCalculator scales risk level based on workspace references.
 12. IntentClassifier identifies standard developer operations as SAFE.
 13. IntentClassifier identifies destructive git resets as RISKY.
 14. IntentClassifier blocks recursive root deletion attempts (rm -rf /).
 15. IntentClassifier blocks fork bombs and raw device writes.
 16. ImmutableAuditTrail initializes genesis block seq=1.
 17. ImmutableAuditTrail appends entries with cryptographic SHA256 linkage.
 18. ImmutableAuditTrail verifies 100% mathematical integrity across chain.
 19. ImmutableAuditTrail detects manual tampering or broken hash links.
 20. ParallelToolDispatcher runs read-only callables concurrently with asyncio.
"""

from __future__ import annotations

import asyncio
import sqlite3
import tempfile
from pathlib import Path
import pytest

from plugins.agentshield import (
    SecretScanner,
    BlastRadiusCalculator,
    IntentClassifier,
    ImmutableAuditTrail,
    ParallelToolDispatcher,
    register,
)


def test_secret_scanner_clean_text():
    clean_code = "def calculate_sum(a: int, b: int) -> int:\n    return a + b\n"
    findings = SecretScanner.scan_text(clean_code)
    assert len(findings) == 0


def test_secret_scanner_openai_key():
    fake_key = "export OPENAI_API_KEY='sk-abcdefghijklmnopqrstuvwxyz0123456789'"
    findings = SecretScanner.scan_text(fake_key)
    assert len(findings) >= 1
    assert any("OpenAI" in f["name"] for f in findings)
    assert findings[0]["masked"].startswith("sk-a")
    assert "..." in findings[0]["masked"]


def test_secret_scanner_github_pat():
    fake_pat = "GITHUB_TOKEN = 'ghp_abcdefghijklmnopqrstuvwxyz0123456789'"
    findings = SecretScanner.scan_text(fake_pat)
    assert len(findings) >= 1
    assert any("GitHub Personal Access Token" in f["name"] for f in findings)


def test_secret_scanner_private_key():
    priv = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0\n-----END RSA PRIVATE KEY-----"
    findings = SecretScanner.scan_text(priv)
    assert len(findings) >= 1
    assert any("Private Key Header" in f["name"] for f in findings)


def test_secret_scanner_shannon_entropy_calculation():
    low_entropy = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    high_entropy = "4kL9z!Q8m@P2v#X7c$W1b%N6y^R0e&"
    h_low = SecretScanner.calculate_shannon_entropy(low_entropy)
    h_high = SecretScanner.calculate_shannon_entropy(high_entropy)
    assert h_low == 0.0
    assert h_high > 4.5


def test_secret_scanner_high_entropy_detection():
    # Long random high-entropy token without prefix
    high_entropy_token = "K9vP2xM7qL4wN8jR1bY6zC0tF3sH5g"
    findings = SecretScanner.scan_text(f"API_SECRET='{high_entropy_token}'")
    assert len(findings) >= 1


def test_secret_scanner_file_scan_clean(tmp_path):
    f = tmp_path / "app.py"
    f.write_text("print('All clean')\n")
    res = SecretScanner.scan_file(f)
    assert res["clean"] is True
    assert len(res["findings"]) == 0


def test_secret_scanner_file_scan_leaks(tmp_path):
    f = tmp_path / "leaking.py"
    f.write_text("API_KEY='sk-1234567890abcdef1234567890abcdef'\n")
    res = SecretScanner.scan_file(f)
    assert res["clean"] is False
    assert len(res["findings"]) >= 1


def test_blast_radius_new_file(tmp_path):
    new_f = tmp_path / "non_existent.py"
    res = BlastRadiusCalculator.calculate_file_blast_radius(new_f)
    assert res["risk_level"] == "LOW"
    assert res["score"] <= 0.2


def test_blast_radius_existing_file_symbols(tmp_path):
    f = tmp_path / "module.py"
    f.write_text("class MyService:\n    pass\n\ndef my_helper():\n    pass\n")
    symbols = BlastRadiusCalculator.inspect_python_ast(f.read_text())
    assert "MyService" in symbols
    assert "my_helper" in symbols


def test_blast_radius_score_scaling(tmp_path):
    f = tmp_path / "shared_util.py"
    f.write_text("def shared_func():\n    return 1\n")
    # File in workspace referencing it
    caller = tmp_path / "caller.py"
    caller.write_text("import shared_util\nshared_util.shared_func()\n")

    res = BlastRadiusCalculator.calculate_file_blast_radius(f, workspace_root=tmp_path)
    assert res["exported_symbols_count"] >= 1
    assert res["score"] >= 0.05


def test_intent_classifier_safe():
    res = IntentClassifier.classify("pytest tests/ -v")
    assert res["verdict"] == "SAFE"

    res2 = IntentClassifier.classify("python3 -m ruff check .")
    assert res2["verdict"] == "SAFE"


def test_intent_classifier_risky():
    res = IntentClassifier.classify("git reset --hard HEAD~1")
    assert res["verdict"] == "RISKY"


def test_intent_classifier_block_rm_root():
    res = IntentClassifier.classify("rm -rf /")
    assert res["verdict"] == "BLOCK"
    assert "Destructive" in res["reason"]

    res2 = IntentClassifier.classify("rm -rf /etc/passwd")
    assert res2["verdict"] == "BLOCK"


def test_intent_classifier_block_fork_bomb():
    bomb = ":(){ :|:& };:"
    res = IntentClassifier.classify(bomb)
    assert res["verdict"] == "BLOCK"


def test_audit_trail_genesis_block(tmp_path):
    db_file = tmp_path / "audit.db"
    trail = ImmutableAuditTrail(db_file)
    entries = trail.get_recent()
    assert len(entries) == 1
    assert entries[0]["seq"] == 1
    assert entries[0]["action"] == "GENESIS"


def test_audit_trail_append_and_chaining(tmp_path):
    db_file = tmp_path / "audit.db"
    trail = ImmutableAuditTrail(db_file)
    e1 = trail.append_entry("WRITE", "config.yaml", payload="foo: bar")
    e2 = trail.append_entry("EXEC", "pytest", payload="test output")

    assert e1["seq"] == 2
    assert e2["seq"] == 3
    assert e2["prev_hash"] == e1["entry_hash"]


def test_audit_trail_verify_integrity(tmp_path):
    db_file = tmp_path / "audit.db"
    trail = ImmutableAuditTrail(db_file)
    trail.append_entry("TOOL_A", "file1.py")
    trail.append_entry("TOOL_B", "file2.py")

    ok, msg = trail.verify_chain()
    assert ok is True
    assert "Verified 100% integrity" in msg


def test_audit_trail_detect_tampering(tmp_path):
    db_file = tmp_path / "audit.db"
    trail = ImmutableAuditTrail(db_file)
    trail.append_entry("TOOL_A", "file1.py")
    trail.append_entry("TOOL_B", "file2.py")

    # Manually tamper with an entry hash in SQLite
    conn = sqlite3.connect(str(db_file))
    conn.execute("UPDATE audit_chain SET entry_hash = 'tampered_hash_value' WHERE seq = 2")
    conn.commit()
    conn.close()

    ok, msg = trail.verify_chain()
    assert ok is False
    assert "mismatch" in msg or "Broken" in msg


def test_parallel_tool_dispatcher_concurrency():
    async def sample_work(x: int) -> int:
        await asyncio.sleep(0.01)
        return x * 2

    tasks = [(sample_work, (i,), {}) for i in range(5)]
    results = asyncio.run(ParallelToolDispatcher.dispatch_parallel(tasks))
    assert results == [0, 2, 4, 6, 8]


def test_blast_radius_token_cache(tmp_path):
    f1 = tmp_path / "mod1.py"
    f2 = tmp_path / "mod2.py"
    f1.write_text("class MyService:\n    def execute(self):\n        pass\n")
    f2.write_text("from mod1 import MyService\ns = MyService()\n")

    res1 = BlastRadiusCalculator.calculate_file_blast_radius(f1, workspace_root=tmp_path)
    assert res1["exported_symbols_count"] >= 1
    assert res1["external_references_found"] >= 1
    assert "cache_size" in res1
    assert res1["cache_size"] > 0

    # Second run should use cached token set
    res2 = BlastRadiusCalculator.calculate_file_blast_radius(f1, workspace_root=tmp_path)
    assert res2["score"] == res1["score"]


def test_audit_trail_prune(tmp_path):
    db_file = tmp_path / "audit_prune.db"
    trail = ImmutableAuditTrail(db_file)
    for i in range(15):
        trail.append_entry("ACTION", f"target_{i}")

    res = trail.prune_chain(max_entries=5)
    assert res["pruned"] is True
    assert res["archived"] == 12
    recent = trail.get_recent(limit=20)
    assert len(recent) == 5


def test_audit_selective_logging(tmp_path, monkeypatch):
    class DummyCtx:
        def __init__(self):
            self.hooks = {}
            self.cmds = {}
            self.cli_cmds = {}

        def register_hook(self, name, fn):
            self.hooks[name] = fn

        def register_command(self, *a, **k):
            pass

        def register_cli_command(self, *a, **k):
            pass

    ctx = DummyCtx()
    register(ctx)
    hook = ctx.hooks["pre_tool_call"]

    monkeypatch.setenv("HERMES_AUDIT_MODE", "mutations_only")
    res_read = hook(tool_name="view_file", tool_args={"path": "sample.py"})
    assert res_read["action"] == "continue"

    res_write = hook(tool_name="write_to_file", tool_args={"TargetFile": "sample.py", "CodeContent": "print(1)"})
    assert res_write["action"] == "continue"


def test_role_security_enforcer_architect_whitelist():
    from plugins.agentshield import RoleSecurityEnforcer
    allowed, msg = RoleSecurityEnforcer.check_tool_allowed("architect", "view_file")
    assert allowed is True
    allowed_find, _ = RoleSecurityEnforcer.check_tool_allowed("architect", "find_by_name")
    assert allowed_find is True


def test_role_security_enforcer_architect_blocks_mutations():
    from plugins.agentshield import RoleSecurityEnforcer
    allowed, msg = RoleSecurityEnforcer.check_tool_allowed("architect", "write_file")
    assert allowed is False
    assert "restricted from calling 'write_file'" in msg

    allowed_bash, _ = RoleSecurityEnforcer.check_tool_allowed("architect", "bash")
    assert allowed_bash is False


def test_role_security_enforcer_coder_permissions():
    from plugins.agentshield import RoleSecurityEnforcer
    allowed_w, _ = RoleSecurityEnforcer.check_tool_allowed("coder", "write_file")
    assert allowed_w is True
    allowed_r, _ = RoleSecurityEnforcer.check_tool_allowed("coder", "view_file")
    assert allowed_r is True


def test_role_security_enforcer_tester_permissions():
    from plugins.agentshield import RoleSecurityEnforcer
    allowed_test, _ = RoleSecurityEnforcer.check_tool_allowed("tester", "pytest")
    assert allowed_test is True
    allowed_bash, _ = RoleSecurityEnforcer.check_tool_allowed("tester", "bash")
    assert allowed_bash is True
    allowed_edit, _ = RoleSecurityEnforcer.check_tool_allowed("tester", "edit_file")
    assert allowed_edit is False


def test_constitutional_preflight_scoring():
    from plugins.reward_scorer import ConstitutionalRewardScorer
    violation_action = {"tool": "write_file", "args": {"path": "/home/developer/app.py"}}
    res = ConstitutionalRewardScorer.score_action(violation_action)
    assert res["passed"] is False
    assert res["verdict"] == "BLOCK"
    assert any("Law 5" in v for v in res["violations"])

    safe_action = {"tool": "write_file", "args": {"path": ".hermes/config.yaml"}}
    res_safe = ConstitutionalRewardScorer.score_action(safe_action)
    assert res_safe["passed"] is True
    assert res_safe["verdict"] == "ALLOW"
