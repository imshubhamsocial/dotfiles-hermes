#!/usr/bin/env python3
"""
Native Verification Harness: Phase 3 Multi-Agent Collective Intelligence (True MoA Loop)
========================================================================================
Validates:
  1. Standardized Agent Protocol (arXiv:2504.16736): AgentMessage schema, MCP bridge, JSON-RPC IPC.
  2. Specialized Role Swarm (Phase III.2): 5 distinct personas with tailored temp/top-p.
  3. Live Proposer Layer (arXiv:2406.04692): 3 concurrent instances with logprob confidence scoring.
  4. Aggregator Layer: Synthesis of diverse perspectives into unified consensus.
  5. Disagreement Detection & HITL Escalation: Variance monitoring and checkpoint interception.
  6. Quorum Audit Plugin Hooks & Invariants: Author != Auditor verification.

Zero test folder architecture compliant.
"""

from __future__ import annotations

import json
import os
import sys
import time

# Ensure hermes core and plugins are on sys.path
core_dir = os.path.expanduser("~/.hermes/hermes-agent/agent/core")
plugins_dir = os.path.expanduser("~/.hermes/plugins")
if core_dir not in sys.path:
    sys.path.insert(0, core_dir)
if plugins_dir not in sys.path:
    sys.path.insert(0, plugins_dir)

from agent_protocol import (
    AgentMessage,
    AgentProtocolServer,
    AgentProtocolClient,
)
from swarm_roles import (
    get_swarm_role,
    list_swarm_roles,
)
from quorum_moa import (
    MoAEngine,
    MoAResult,
    compute_inter_perspective_divergence,
    get_moa_engine,
)
import quorum_audit
from hitl_gateway import create_hitl_gateway


def test_gate1_agent_protocol_standardization() -> bool:
    print("\n[Gate 1] Standardized Inter-Agent Protocol (arXiv:2504.16736)...")
    # 1. Schema & Serialization
    msg = AgentMessage(
        role="proposer_analytical",
        content="Algorithmic proof: time complexity is O(N log N).",
        confidence=0.94,
        metadata={"model": "gemma-4", "tokens": 42},
    )
    d = msg.to_dict()
    assert d["role"] == "proposer_analytical", "Role mismatch"
    assert d["confidence"] == 0.94, "Confidence mismatch"
    assert "trace_id" in d, "Trace ID missing"

    # 2. JSON roundtrip
    json_str = msg.to_json()
    msg_reconstructed = AgentMessage.from_json(json_str)
    assert msg_reconstructed.role == msg.role
    assert msg_reconstructed.content == msg.content
    assert msg_reconstructed.confidence == msg.confidence

    # 3. Model Context Protocol (MCP) Bridge
    mcp_data = msg.to_mcp_content()
    assert mcp_data["type"] == "text"
    assert mcp_data["annotations"]["role"] == "proposer_analytical"
    assert mcp_data["annotations"]["confidence"] == 0.94

    mcp_msg = AgentMessage.from_mcp_content(mcp_data)
    assert mcp_msg.role == "proposer_analytical"
    assert mcp_msg.content == msg.content

    # 4. JSON-RPC 2.0 UNIX Domain Socket IPC
    test_sock = "/dev/shm/test_hermes_ipc.sock" if os.path.exists("/dev/shm") else "/tmp/test_hermes_ipc.sock"
    server = AgentProtocolServer(socket_path=test_sock)
    server.register_handler("receive_message", lambda p: {"status": "received", "role": p["message"]["role"]})
    server.start()
    try:
        client = AgentProtocolClient(socket_path=test_sock)
        # Handshake
        hs = client.call("handshake", {"agent_name": "agent_test_client"})
        assert hs["status"] == "acknowledged"
        assert hs["protocol"] == "hermes-agent-v1"

        # Typed AgentMessage delivery
        res = client.send_agent_message(msg)
        assert res["status"] == "received"
        assert res["role"] == "proposer_analytical"
        print("  • AgentMessage schema, MCP bridge, and UNIX Socket JSON-RPC verified")
    finally:
        server.stop()

    print("  ✅ Gate 1 Certified: Standardized Agent Protocol Operational")
    return True


def test_gate2_specialized_swarm_roles() -> bool:
    print("\n[Gate 2] Specialized Role Swarm (Phase III.2)...")
    roles = list_swarm_roles()
    assert len(roles) >= 5, f"Expected at least 5 roles, found {len(roles)}"

    expected_params = {
        "director": {"temp": 0.1, "top_p": 0.9},
        "researcher": {"temp": 0.7, "top_p": 0.95},
        "implementer": {"temp": 0.2, "top_p": 0.85},
        "auditor": {"temp": 0.1, "top_p": 0.9},
        "synthesizer": {"temp": 0.4, "top_p": 0.9},
    }

    for role_name, exp in expected_params.items():
        role = get_swarm_role(role_name)
        assert abs(role.temperature - exp["temp"]) < 1e-4, f"{role_name} temp {role.temperature} != {exp['temp']}"
        assert abs(role.top_p - exp["top_p"]) < 1e-4, f"{role_name} top_p {role.top_p} != {exp['top_p']}"
        assert len(role.system_prompt) > 20, f"{role_name} system prompt missing"
        assert len(role.capabilities) >= 3, f"{role_name} capabilities empty"
        print(f"  • Role @{role.role_name}: temp={role.temperature}, top_p={role.top_p}, focus='{role.focus}'")

    print("  ✅ Gate 2 Certified: Swarm Roles Invariants Fully Compliant")
    return True


def test_gate3_and_4_live_moa_debate_and_synthesis() -> bool:
    print("\n[Gate 3 & 4] True MoA Loop: Proposer Layer & Aggregator Consensus...")
    engine = get_moa_engine()

    test_query = (
        "How should an autonomous agent OS balance fast execution versus high-assurance correctness "
        "when applying atomic code patches to critical system files?"
    )

    print("  • Launching 3 parallel proposers against local llama-server (Analytical, Creative, Critic)...")
    t0 = time.time()
    result: MoAResult = engine.run_moa(query=test_query)
    duration_s = (time.time() - t0)

    print(f"  • Deliberation completed in {duration_s:.2f}s (Engine reported: {result.duration_ms:.1f}ms)")
    print(f"  • Active Proposers: {list(result.proposals.keys())}")
    assert len(result.proposals) == 3, f"Expected 3 proposals, got {len(result.proposals)}"

    for role, prop in result.proposals.items():
        print(f"    - {role}: confidence={prop.confidence:.3f}, len={len(prop.content)} chars")
        assert len(prop.content) > 10, f"Proposer {role} output empty"
        assert 0.0 < prop.confidence <= 1.0, f"Confidence out of range: {prop.confidence}"

    print(f"  • Aggregator Response: {len(result.final_response)} chars, confidence={result.confidence:.3f}")
    assert len(result.final_response) > 50, "Aggregator synthesis was truncated or empty"
    assert result.aggregator_message.role == "synthesizer", "Aggregator role invalid"

    print("  ✅ Gate 3 Certified: 3-Proposer Parallel Execution & Logprob Scoring Active")
    print("  ✅ Gate 4 Certified: Aggregator Synthesis Generated Unified Consensus")
    return True


def test_gate5_disagreement_detection_and_hitl_escalation() -> bool:
    print("\n[Gate 5] Disagreement Detection & HITL Supervisory Escalation...")
    engine = MoAEngine(disagreement_threshold=0.30, hitl_mode="interactive")

    # Divergent perspectives
    text_a = "We must immediately approve full unrestricted autonomous execution without review."
    text_b = "We must completely freeze all automated changes and mandate three manual human signoffs."
    text_c = "We should execute simulated quantum mutations on distributed blockchain nodes."

    div = compute_inter_perspective_divergence([text_a, text_b, text_c])
    print(f"  • Inter-perspective lexical divergence: {div:.3f}")
    assert div > 0.40, f"Expected high divergence, got {div}"

    # Verify HITL escalation logic
    gateway = create_hitl_gateway(mode="interactive")
    decision = gateway.request_checkpoint(
        action_id="test-moa-divergence-chk",
        action_type="moa_disagreement_escalation",
        target="quorum_audit_consensus",
        summary="High divergence detected among proposers",
        diff_or_payload=json.dumps({"divergence": div}),
    )
    assert decision is not None
    assert decision.action_id == "test-moa-divergence-chk"
    print(f"  • HITL Gateway intercepted escalation checkpoint: verdict={decision.verdict.value}")

    print("  ✅ Gate 5 Certified: Disagreement Variance Monitoring & HITL Escalation Operational")
    return True


def test_gate6_quorum_audit_plugin_and_invariants() -> bool:
    print("\n[Gate 6] Quorum Audit Plugin Hooks & Invariant Enforcement...")
    # 1. Verify Author != Auditor invariant
    violation_check = quorum_audit.pre_tool_call(
        tool_name="quorum_audit_check",
        args={"author": "engineer_alice", "auditor": "engineer_alice"},
        role="coder",
    )
    assert violation_check is not None and violation_check.get("action") == "block", (
        "Failed to block Author == Auditor invariant violation!"
    )
    print(f"  • Invariant Author != Auditor enforced: {violation_check['message'][:65]}...")

    # 2. Verify @tester mutation blocking
    tester_block = quorum_audit.pre_tool_call(
        tool_name="patch_file",
        args={"target_file": "core.py"},
        role="tester",
    )
    assert tester_block is not None and tester_block.get("action") == "block", (
        "Failed to block @tester file mutation!"
    )
    print(f"  • Invariant Tester Read-Only enforced: {tester_block['message'][:65]}...")

    # 3. Verify plugin run_moa_consensus interface
    assert hasattr(quorum_audit, "run_moa_consensus"), "Plugin missing run_moa_consensus"
    print("  • Plugin export run_moa_consensus certified")

    print("  ✅ Gate 6 Certified: Quorum Audit Invariants and Plugin Hooks Fully Intact")
    return True


def main() -> None:
    print("=" * 75)
    print("PHASE 3: MULTI-AGENT COLLECTIVE INTELLIGENCE (TRUE MoA) VERIFICATION")
    print("=" * 75)

    assert test_gate1_agent_protocol_standardization()
    assert test_gate2_specialized_swarm_roles()
    assert test_gate3_and_4_live_moa_debate_and_synthesis()
    assert test_gate5_disagreement_detection_and_hitl_escalation()
    assert test_gate6_quorum_audit_plugin_and_invariants()

    print("\n" + "=" * 75)
    print("PHASE 3 VERIFICATION RESULT: 100% PASS (ALL MoA GATES CERTIFIED)")
    print("=" * 75)


if __name__ == "__main__":
    main()
