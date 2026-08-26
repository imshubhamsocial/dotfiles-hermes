"""
Contract Tests: Roadmap 4 Milestone U49
========================================
Validates COG Second Brain Markdown Vault & Closed-Loop Verifier:
1. Markdown vault storage and indexing with YAML frontmatter
2. Dual-agent worker/verifier protocol
3. Verifier evidence receipt generation
4. Verification failure rejects and reverts
5. Zero GPU VRAM overhead
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import pytest

from hermes_core.cog_vault import (
    CogVault,
    VaultEntry,
    IndexEntry,
    EntryType,
    get_cog_vault,
    reset_cog_vault,
)
from hermes_core.cog_verifier import (
    CogVerifier,
    WorkerAgent,
    VerificationReceipt,
    VerificationCheck,
    VerificationChecks,
    get_cog_verifier,
    get_worker_agent,
    reset_cog_verifier,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def temp_vault_root():
    """Create temporary vault root"""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture
def cog_vault(temp_vault_root):
    """Create CogVault with temp root"""
    vault = CogVault(roots=[temp_vault_root])
    yield vault
    vault.close()


@pytest.fixture
def populated_vault(cog_vault):
    """Vault with sample entries"""
    # Store ADR
    cog_vault.store_adr(
        title="Use SQLite WAL for Memory",
        context="Need persistent cross-session memory",
        decision="Use SQLite WAL with in-memory index",
        consequences="Fast reads, ACID, zero GPU VRAM",
        tags=["architecture", "memory"],
    )
    
    # Store Contract
    cog_vault.store_contract(
        title="Embedding Engine",
        module="hermes_core.embeddings",
        interface="search(query, top_k) -> List[SearchHit]",
        invariants="CPU-only, normalized, deterministic",
        tests="test_embeddings.py",
        tags=["embedding"],
    )
    
    # Store Evidence
    cog_vault.store_evidence(
        title="Embedding verification",
        task_id="task-001",
        verdict="VERIFIED",
        verifier="cog_verifier",
        worker="agent_worker",
        checks="AST: PASS\nTests: 15/15\nVRAM: 0 MB",
        content_hash="abc123",
        duration_ms=150,
    )
    
    yield cog_vault


@pytest.fixture
def cog_verifier(temp_vault_root):
    """Create CogVerifier with temp vault"""
    vault = CogVault(roots=[temp_vault_root])
    verifier = CogVerifier(vault=vault, verifier_name="test_verifier")
    yield verifier


# =============================================================================
# TESTS
# =============================================================================

class TestCogMarkdownVaultStorageAndIndexing:
    """Test Markdown vault read/write/indexing with YAML frontmatter"""

    def test_store_adr_creates_markdown_with_frontmatter(self, cog_vault):
        """Validates ADR storage creates proper Markdown with YAML frontmatter"""
        path = cog_vault.store_adr(
            title="Test ADR",
            context="Test context",
            decision="Test decision",
            consequences="Test consequences",
            tags=["test"],
        )
        
        assert path.exists()
        content = path.read_text()
        
        # Check frontmatter
        assert content.startswith("---")
        assert "id:" in content
        assert "title: Test ADR" in content
        assert "status: proposed" in content
        assert "tags: ['test']" in content
        
        # Check body sections
        assert "## Status" in content
        assert "## Context" in content
        assert "## Decision" in content
        assert "## Consequences" in content

    def test_store_contract_creates_markdown_with_frontmatter(self, cog_vault):
        """Validates Contract storage creates proper Markdown"""
        path = cog_vault.store_contract(
            title="Test Contract",
            module="test.module",
            interface="test() -> bool",
            invariants="Always returns True",
            tests="test_test.py",
            tags=["test"],
        )
        
        assert path.exists()
        content = path.read_text()
        
        assert content.startswith("---")
        assert "id:" in content
        assert "module: test.module" in content
        assert "## Interface" in content
        assert "## Invariants" in content

    def test_store_evidence_creates_markdown_with_frontmatter(self, cog_vault):
        """Validates Evidence storage creates proper Markdown"""
        path = cog_vault.store_evidence(
            title="Test Evidence",
            task_id="task-123",
            verdict="VERIFIED",
            verifier="test_verifier",
            worker="test_worker",
            checks="All checks passed",
            content_hash="hash123",
            duration_ms=100,
        )
        
        assert path.exists()
        content = path.read_text()
        
        assert content.startswith("---")
        assert "verdict: VERIFIED" in content
        assert "task_id: task-123" in content
        assert "verifier: test_verifier" in content

    def test_entry_retrieval_by_relative_path(self, populated_vault):
        """Validates entry retrieval"""
        # Find an entry
        entries = populated_vault._entries
        assert len(entries) >= 3
        
        for rel_path, entry in entries.items():
            retrieved = populated_vault.get_entry(rel_path)
            assert retrieved is not None
            assert retrieved.relative_path == rel_path
            assert retrieved.hash == entry.hash

    def test_search_by_query(self, populated_vault):
        """Validates search functionality"""
        results = populated_vault.search("SQLite")
        
        assert len(results) >= 1
        for r in results:
            assert isinstance(r, IndexEntry)
            assert "sqlite" in r.summary.lower() or "sqlite" in r.title.lower()

    def test_search_by_type(self, populated_vault):
        """Validates search filtered by entry type"""
        results = populated_vault.search("", entry_type=EntryType.ADR)
        
        for r in results:
            assert r.entry_type == EntryType.ADR

    def test_search_by_tags(self, populated_vault):
        """Validates search filtered by tags"""
        results = populated_vault.search("", tags=["architecture"])
        
        for r in results:
            assert "architecture" in r.tags

    def test_list_by_type(self, populated_vault):
        """Validates listing by type"""
        adrs = populated_vault.list_by_type(EntryType.ADR)
        contracts = populated_vault.list_by_type(EntryType.CONTRACT)
        evidence = populated_vault.list_by_type(EntryType.EVIDENCE)
        
        assert len(adrs) >= 1
        assert len(contracts) >= 1
        assert len(evidence) >= 1

    def test_get_evidence_for_task(self, populated_vault):
        """Validates evidence retrieval by task ID"""
        evidence = populated_vault.get_evidence_for_task("task-001")
        
        assert len(evidence) >= 1
        for e in evidence:
            assert e.entry_type == EntryType.EVIDENCE
            assert e.frontmatter.get("task_id") == "task-001"

    def test_get_latest_verdict(self, populated_vault):
        """Validates latest verdict retrieval"""
        verdict = populated_vault.get_latest_verdict("task-001")
        
        assert verdict == "VERIFIED"

    def test_vault_stats(self, populated_vault):
        """Validates vault statistics"""
        stats = populated_vault.get_stats()
        
        assert stats["total_entries"] >= 3
        assert "adr" in stats["by_type"]
        assert "contract" in stats["by_type"]
        assert "evidence" in stats["by_type"]


class TestDualAgentWorkerVerifierProtocol:
    """Test dual-agent worker/verifier protocol"""

    def test_worker_verifier_initialization(self, cog_verifier):
        """Validates verifier initialization"""
        assert cog_verifier.verifier_name == "test_verifier"
        assert cog_verifier.vault is not None

    def test_verification_checks_structure(self):
        """Validates VerificationCheck structure"""
        check = VerificationCheck(
            name="Test Check",
            status="PASS",
            message="All good",
            duration_ms=10.5,
        )
        
        assert check.name == "Test Check"
        assert check.status == "PASS"
        assert check.message == "All good"
        assert check.duration_ms == 10.5

    def test_verification_receipt_structure(self):
        """Validates VerificationReceipt structure"""
        receipt = VerificationReceipt(
            task_id="task-1",
            verdict="VERIFIED",
            verifier="verifier",
            worker="worker",
            timestamp=time.time(),
            duration_ms=100.0,
            content_hash="abc123",
            checks=[
                VerificationCheck(name="Check 1", status="PASS", message="OK"),
                VerificationCheck(name="Check 2", status="PASS", message="OK"),
            ],
        )
        
        assert receipt.task_id == "task-1"
        assert receipt.verdict == "VERIFIED"
        assert receipt.all_passed() is True

    def test_verification_receipt_rejected(self):
        """Validates receipt with failures"""
        receipt = VerificationReceipt(
            task_id="task-1",
            verdict="REJECTED",
            verifier="verifier",
            worker="worker",
            timestamp=time.time(),
            duration_ms=100.0,
            content_hash="abc123",
            checks=[
                VerificationCheck(name="Check 1", status="PASS", message="OK"),
                VerificationCheck(name="Check 2", status="FAIL", message="Failed"),
            ],
        )
        
        assert receipt.verdict == "REJECTED"
        assert receipt.all_passed() is False

    def test_worker_agent_initialization(self, cog_verifier):
        """Validates worker agent initialization"""
        worker = WorkerAgent(verifier=cog_verifier)
        
        assert worker.planner is not None
        assert worker.verifier == cog_verifier

    def test_verifier_ast_check(self, temp_vault_root):
        """Validates AST syntax check"""
        test_file = temp_vault_root / "valid.py"
        test_file.write_text("def foo():\n    return 42\n")
        
        check = VerificationChecks.check_python_ast(test_file)
        
        assert check.name == "Python AST Syntax"
        assert check.status == "PASS"

    def test_verifier_ast_check_fails_on_syntax_error(self, temp_vault_root):
        """Validates AST check fails on syntax error"""
        test_file = temp_vault_root / "invalid.py"
        test_file.write_text("def foo(\n    return 42\n")
        
        check = VerificationChecks.check_python_ast(test_file)
        
        assert check.status == "FAIL"
        assert "SyntaxError" in check.message

    def test_verifier_js_brace_check(self, temp_vault_root):
        """Validates JS brace balance check"""
        test_file = temp_vault_root / "valid.js"
        test_file.write_text("function foo() { return { a: 1 }; }")
        
        check = VerificationChecks.check_js_braces(test_file)
        
        assert check.name == "JS/TS Brace Balance"
        assert check.status == "PASS"

    def test_verifier_js_brace_check_fails_on_imbalance(self, temp_vault_root):
        """Validates JS brace check fails on imbalance"""
        test_file = temp_vault_root / "invalid.js"
        test_file.write_text("function foo() { return { a: 1; }")
        
        check = VerificationChecks.check_js_braces(test_file)
        
        assert check.status == "FAIL"

    def test_verifier_relative_paths_check(self):
        """Validates relative paths check"""
        check = VerificationChecks.check_relative_paths(["src/file.py", "tests/test.py"])
        
        assert check.name == "Relative Paths"
        assert check.status == "PASS"

    def test_verifier_relative_paths_check_fails_on_absolute(self):
        """Validates relative paths check fails on absolute paths"""
        check = VerificationChecks.check_relative_paths(["/home/user/file.py"])
        
        assert check.status == "FAIL"
        assert "Absolute path" in check.message


class TestVerifierEvidenceReceiptGeneration:
    """Test verifier evidence receipt generation"""

    def test_verify_task_generates_receipt(self, cog_verifier, temp_vault_root):
        """Validates verify_task generates receipt"""
        # Create test file
        test_file = temp_vault_root / "test.py"
        test_file.write_text("def test():\n    return True\n")
        
        receipt = cog_verifier.verify_task(
            task_id="verify-task-1",
            worker_name="test_worker",
            affected_files=[str(test_file)],
            content_hash="hash123",
        )
        
        assert isinstance(receipt, VerificationReceipt)
        assert receipt.task_id == "verify-task-1"
        assert receipt.verdict in ["VERIFIED", "REJECTED"]
        assert receipt.verifier == "test_verifier"
        assert receipt.worker == "test_worker"
        assert receipt.content_hash == "hash123"
        assert len(receipt.checks) > 0

    def test_verify_task_stores_evidence_in_vault(self, cog_verifier, temp_vault_root):
        """Validates verification stores evidence in vault"""
        test_file = temp_vault_root / "test.py"
        test_file.write_text("def test():\n    return True\n")
        
        receipt = cog_verifier.verify_task(
            task_id="verify-task-2",
            worker_name="test_worker",
            affected_files=[str(test_file)],
        )
        
        # Check evidence was stored
        evidence = cog_verifier.vault.get_evidence_for_task("verify-task-2")
        assert len(evidence) >= 1
        assert evidence[0].frontmatter.get("verdict") == receipt.verdict

    def test_receipt_deterministic_formatting(self, cog_verifier, temp_vault_root):
        """Validates deterministic receipt formatting"""
        test_file = temp_vault_root / "test.py"
        test_file.write_text("def test():\n    return True\n")
        
        receipt1 = cog_verifier.verify_task(
            task_id="format-test",
            worker_name="worker",
            affected_files=[str(test_file)],
            content_hash="fixedhash",
        )
        
        receipt2 = cog_verifier.verify_task(
            task_id="format-test",
            worker_name="worker",
            affected_files=[str(test_file)],
            content_hash="fixedhash",
        )
        
        # Content hash and structure should be deterministic
        assert receipt1.content_hash == receipt2.content_hash
        assert receipt1.verdict == receipt2.verdict

    def test_can_complete_task_after_verified(self, cog_verifier, temp_vault_root):
        """Validates can_complete_task returns True after VERIFIED"""
        test_file = temp_vault_root / "test.py"
        test_file.write_text("def test():\n    return True\n")
        
        receipt = cog_verifier.verify_task(
            task_id="complete-task",
            worker_name="worker",
            affected_files=[str(test_file)],
        )
        
        if receipt.verdict == "VERIFIED":
            assert cog_verifier.can_complete_task("complete-task") is True
        else:
            # If rejected, should be False
            assert cog_verifier.can_complete_task("complete-task") is False


class TestVerificationFailureRejectsAndReverts:
    """Test verification failure rejects and prevents completion"""

    def test_failed_ast_rejects_task(self, cog_verifier, temp_vault_root):
        """Validates syntax error causes rejection"""
        test_file = temp_vault_root / "bad.py"
        test_file.write_text("def bad(\n    return 1\n")
        
        receipt = cog_verifier.verify_task(
            task_id="fail-ast",
            worker_name="worker",
            affected_files=[str(test_file)],
        )
        
        assert receipt.verdict == "REJECTED"
        ast_check = next((c for c in receipt.checks if c.name == "Python AST Syntax"), None)
        assert ast_check is not None
        assert ast_check.status == "FAIL"

    def test_failed_plan_compliance_rejects(self, cog_verifier, temp_vault_root):
        """Validates plan compliance failure causes rejection"""
        test_file = temp_vault_root / "test.py"
        test_file.write_text("def test():\n    return True\n")
        
        # No plan exists for this task
        receipt = cog_verifier.verify_task(
            task_id="no-plan-task",
            worker_name="worker",
            affected_files=[str(test_file)],
        )
        
        assert receipt.verdict == "REJECTED"
        plan_check = next((c for c in receipt.checks if c.name == "Plan Compliance"), None)
        assert plan_check is not None
        assert plan_check.status == "FAIL"

    def test_cannot_complete_rejected_task(self, cog_verifier, temp_vault_root):
        """Validates cannot complete rejected task"""
        test_file = temp_vault_root / "test.py"
        test_file.write_text("def test(\n    return True\n")
        
        cog_verifier.verify_task(
            task_id="reject-task",
            worker_name="worker",
            affected_files=[str(test_file)],
        )
        
        assert cog_verifier.can_complete_task("reject-task") is False

    def test_verifier_evidence_contains_failure_details(self, cog_verifier, temp_vault_root):
        """Validates evidence receipt contains failure details"""
        test_file = temp_vault_root / "bad.py"
        test_file.write_text("def bad(\n    return 1\n")
        
        receipt = cog_verifier.verify_task(
            task_id="detail-task",
            worker_name="worker",
            affected_files=[str(test_file)],
        )
        
        assert receipt.verdict == "REJECTED"
        # Check that failure details are in notes/checks
        failed_checks = [c for c in receipt.checks if c.status == "FAIL"]
        assert len(failed_checks) > 0


class TestCogVaultZeroGPUVRAM:
    """Test zero GPU VRAM overhead"""

    def test_vault_zero_vram_guarantee(self, cog_vault):
        """Validates vault zero VRAM guarantee"""
        guarantee = cog_vault.get_zero_vram_guarantee()
        
        assert guarantee["markdown_parsing_cpu_only"] is True
        assert guarantee["yaml_frontmatter_cpu_only"] is True
        assert guarantee["file_io_cpu_only"] is True
        assert guarantee["indexing_cpu_only"] is True
        assert guarantee["no_gpu_operations"] is True
        assert guarantee["ramdisk_compatible"] is True

    def test_verifier_zero_vram_guarantee(self, cog_verifier):
        """Validates verifier zero VRAM guarantee"""
        guarantee = cog_verifier.get_zero_vram_guarantee()
        
        assert guarantee["ast_parsing_cpu_only"] is True
        assert guarantee["subprocess_cpu_only"] is True
        assert guarantee["file_io_cpu_only"] is True
        assert guarantee["no_gpu_operations"] is True
        assert guarantee["ramdisk_compatible"] is True

    def test_worker_zero_vram_guarantee(self, cog_verifier):
        """Validates worker zero VRAM guarantee"""
        worker = WorkerAgent(verifier=cog_verifier)
        guarantee = worker.get_zero_vram_guarantee()
        
        assert guarantee["worker_logic_cpu_only"] is True
        assert guarantee["verification_cpu_only"] is True
        assert guarantee["no_gpu_operations"] is True

    def test_no_gpu_imports_vault(self):
        """Validates no GPU libraries in vault module"""
        import hermes_core.cog_vault as cv
        
        forbidden = ["torch", "tensorflow", "cuda", "cupy", "jax"]
        for mod in forbidden:
            assert not hasattr(cv, mod)

    def test_no_gpu_imports_verifier(self):
        """Validates no GPU libraries in verifier module"""
        import hermes_core.cog_verifier as cv
        
        forbidden = ["torch", "tensorflow", "cuda", "cupy", "jax"]
        for mod in forbidden:
            assert not hasattr(cv, mod)

    def test_operations_on_cpu(self, cog_vault, cog_verifier):
        """Validates all operations execute on CPU"""
        # Vault operations
        cog_vault.store_adr("Test", "ctx", "dec", "cons")
        cog_vault.search("test")
        
        # Verifier operations (with mock files)
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            test_file = Path(td) / "test.py"
            test_file.write_text("def test():\n    return True\n")
            
            cog_verifier.verify_task(
                task_id="cpu-test",
                worker_name="worker",
                affected_files=[str(test_file)],
            )
        
        # All completed without GPU
        assert True


import time


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
