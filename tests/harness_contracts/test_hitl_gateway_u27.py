"""
Contract Tests for U27: Interactive HITL Checkpoint & Supervisory Gate
========================================================================
Tests risk assessment (LOW, MEDIUM, HIGH, CRITICAL), visual DAG dashboard
rendering, unified diff generation, policy auto-approvals, and critical blocks.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import pytest

from hermes_core.hitl_gateway import (
    HITLSupervisoryGateway,
    RiskLevel,
    ApprovalVerdict,
    assess_risk,
    render_dag_dashboard,
    format_patch_diff,
    create_hitl_gateway,
)


class TestHITLSupervisoryGateway:
    """Test suite for U27 capabilities."""

    def test_risk_assessment_classification(self):
        # Critical commands
        assert assess_risk("shell_command", "", "rm -rf /var/lib") == RiskLevel.CRITICAL
        assert assess_risk("shell_command", "", "DROP TABLE users;") == RiskLevel.CRITICAL
        assert assess_risk("file_write", "/etc/passwd", "root:x:0:0:::") == RiskLevel.CRITICAL

        # High risk commands
        assert assess_risk("shell_command", "", "git reset --hard HEAD~1") == RiskLevel.HIGH

        # Low risk commands
        assert assess_risk("shell_command", "", "pytest tests/") == RiskLevel.LOW
        assert assess_risk("file_write", "src/module.py", "print('hello')") == RiskLevel.LOW

    def test_visual_dag_dashboard_rendering(self):
        nodes = [
            {"id": "step_1", "name": "Plan Physics Blueprint", "status": "COMPLETED", "retry_count": 0},
            {"id": "step_2", "name": "Code Shallow Water Shaders", "status": "RUNNING", "retry_count": 1},
            {"id": "step_3", "name": "Run Playwright Verification", "status": "PENDING", "retry_count": 0},
        ]
        dashboard = render_dag_dashboard(nodes)

        assert "TASK DAG EXECUTION STATE" in dashboard
        assert "step_1" in dashboard
        assert "Plan Physics Blueprint" in dashboard
        assert "DONE" in dashboard
        assert "ACTIVE" in dashboard
        assert "[R:1]" in dashboard

    def test_format_patch_diff(self):
        orig = "def add(a, b):\n    return a - b\n"
        mod = "def add(a, b):\n    return a + b\n"
        diff = format_patch_diff(orig, mod, filepath="math.py")

        assert "--- a/math.py" in diff
        assert "+++ b/math.py" in diff
        assert "-    return a - b" in diff
        assert "+    return a + b" in diff

    def test_gateway_policy_auto_approval_and_critical_block(self):
        # In YOLO mode, low risk is auto-approved, but critical operations are blocked
        gateway = create_hitl_gateway(mode="yolo")

        # 1. Low risk operation
        decision_low = gateway.request_checkpoint(
            action_id="act_1",
            action_type="shell_command",
            target="",
            summary="Run unit tests",
            diff_or_payload="pytest tests/",
        )
        assert decision_low.verdict == ApprovalVerdict.AUTO_APPROVED

        # 2. Critical operation
        decision_crit = gateway.request_checkpoint(
            action_id="act_2",
            action_type="shell_command",
            target="",
            summary="Delete root files",
            diff_or_payload="rm -rf /etc",
        )
        assert decision_crit.verdict == ApprovalVerdict.REJECTED
        assert "CRITICAL" in decision_crit.reason


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
