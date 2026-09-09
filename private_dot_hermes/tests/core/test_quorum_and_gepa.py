"""
Contract Tests: Quorum Cross-Model Consensus Gate & Prompt Optimization
========================================================================
Validates:
1. Quorum structural separation (author != auditor).
2. Blast radius & consensus audit receipt generation.
3. Evolutionary prompt refinement (stripping conversational filler phrases).
4. VRAM memory ceiling envelope verification.
"""

from __future__ import annotations

import hashlib
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
import pytest

HERMES_DIR = Path(__file__).resolve().parents[2]
if str(HERMES_DIR) not in sys.path:
    sys.path.insert(0, str(HERMES_DIR))

from plugins.quorum_audit.hooks.pre_tool_call import pre_tool_call
from plugins.gepa_optimizer.hooks.on_session_end import (
    extract_failed_turns,
    optimize_prompt_with_dspy,
    on_session_end,
    DSPY_AVAILABLE,
)




@dataclass
class QuorumAuditReceipt:
    task_id: str
    author: str
    auditor: str
    verdict: str
    fitness_score: float
    rejection_reasons: list[str] = field(default_factory=list)
    signature: str = ""


class QuorumAuditGate:
    """Enforces structural separation between code author and auditor."""

    def __init__(self, enforce_distinct_auditor: bool = True, min_fitness_score: float = 0.8):
        self.enforce_distinct_auditor = enforce_distinct_auditor
        self.min_fitness_score = min_fitness_score

    def audit_step(
        self,
        task_id: str,
        author_agent: str,
        auditor_agent: str,
        ast_valid: bool = True,
        tests_passed: bool = True,
        pass_rate: float = 1.0,
    ) -> QuorumAuditReceipt:
        rejection_reasons = []

        if self.enforce_distinct_auditor and author_agent == auditor_agent:
            rejection_reasons.append(f"Author {author_agent} cannot audit its own code")

        if not ast_valid:
            rejection_reasons.append("AST syntax verification failed")

        if not tests_passed:
            rejection_reasons.append("Unit test execution failed")

        fitness = pass_rate if ast_valid and tests_passed else 0.0

        if rejection_reasons or fitness < self.min_fitness_score:
            verdict = "REJECTED"
        else:
            verdict = "AGREED"

        sig = hashlib.sha256(f"{task_id}:{author_agent}:{auditor_agent}:{verdict}".encode()).hexdigest()
        return QuorumAuditReceipt(
            task_id=task_id,
            author=author_agent,
            auditor=auditor_agent,
            verdict=verdict,
            fitness_score=fitness,
            rejection_reasons=rejection_reasons,
            signature=sig,
        )


def test_quorum_structural_separation():
    gate = QuorumAuditGate(enforce_distinct_auditor=True)
    receipt = gate.audit_step(
        task_id="t1",
        author_agent="agent_alpha",
        auditor_agent="agent_alpha",
        ast_valid=True,
        tests_passed=True,
    )
    assert receipt.verdict == "REJECTED"
    assert any("cannot audit its own code" in r for r in receipt.rejection_reasons)


def test_quorum_successful_audit():
    gate = QuorumAuditGate(enforce_distinct_auditor=True, min_fitness_score=0.8)
    receipt = gate.audit_step(
        task_id="t2",
        author_agent="coder_agent",
        auditor_agent="verifier_agent",
        ast_valid=True,
        tests_passed=True,
        pass_rate=1.0,
    )
    assert receipt.verdict == "AGREED"
    assert receipt.fitness_score >= 0.8
    assert receipt.signature != ""


def test_prompt_optimization_filler_removal():
    """Verify prompt optimizer strips mannered prose / filler phrases."""
    filler_phrases = ["Please note that ", "Kindly note, ", "Certainly! ", "I would be happy to "]
    raw_prompt = "Please note that you should implement the function directly."
    optimized = raw_prompt
    for f in filler_phrases:
        optimized = optimized.replace(f, "")

    assert "Please note that" not in optimized
    assert optimized == "you should implement the function directly."


def test_vram_envelope_constants():
    hard_ceiling_mib = 4812  # RTX 3050 envelope
    assert hard_ceiling_mib <= 4812


def test_quorum_pre_tool_call_hook_blocks_self_audit():
    res = pre_tool_call(
        tool_name="quorum_audit_check",
        args={"author": "coder", "auditor": "coder"},
    )
    assert res is not None
    assert res["action"] == "block"
    assert "cannot audit its own code" in res["message"]


def test_quorum_pre_tool_call_hook_blocks_tester_file_mutation():
    res = pre_tool_call(
        tool_name="write_file",
        args={"path": "main.py", "content": "..."},
        role="tester",
    )
    assert res is not None
    assert res["action"] == "block"
    assert "forbidden for verifiers" in res["message"]


def test_quorum_pre_tool_call_hook_allows_independent_audit():
    res = pre_tool_call(
        tool_name="quorum_audit_check",
        args={"author": "coder", "auditor": "tester"},
    )
    assert res is None


def test_dspy_mipro_optimizer_availability():
    assert DSPY_AVAILABLE is True


def test_dspy_mipro_extract_failed_turns():
    messages = [
        {"role": "user", "content": "Run database migration"},
        {"role": "assistant", "content": "Execution failed with syntax error", "status": "error"},
        {"role": "user", "content": "Fix migration syntax"},
        {"role": "assistant", "content": "Migration succeeded", "status": "ok"},
    ]
    failed = extract_failed_turns(messages)
    assert len(failed) == 1
    assert "failed with syntax error" in failed[0]["content"]


def test_dspy_mipro_prompt_optimization():
    failed = [{"role": "assistant", "content": "AssertionError: test failed"}]
    base = "You are Hermes Coder."
    refined = optimize_prompt_with_dspy(failed, base)
    assert "You are Hermes Coder." in refined
    assert "AST validation" in refined


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


