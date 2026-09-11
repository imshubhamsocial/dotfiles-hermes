"""
Contract Tests: Google DeepMind Antigravity 2.0 (AGY) & Jules Bridge for Hermes.
Validates:
1. Artifacts Subsystem (Alerts, Mermaid, Carousels, HTML Aux UI apps)
2. Thought Signature Cryptographic Round-tripping
3. Hierarchical Rule Walker & Progressive Disclosure (<400 tokens)
4. Magentic-One Dual Ledgers & 2-Turn Stall Circuit Breaker
5. Agent2Agent (A2A) Agent Card & JSON-RPC 2.0 Task Dispatch
6. Shannon Entropy Execution Rails & Deterministic Code PRM
"""

import json
import tempfile
from pathlib import Path
import pytest

from plugins.antigravity_bridge.artifacts import AGYArtifactsManager
from plugins.antigravity_bridge.thought_signature import GeminiThoughtSignaturePreserver
from plugins.antigravity_bridge.rules_walker import HierarchicalRuleWalker, ProgressiveRule
from plugins.antigravity_bridge.dual_ledger import MagenticDualLedger
from plugins.antigravity_bridge.a2a_server import A2AAgentCardServer
from plugins.antigravity_bridge.shannon_prm import ShannonEntropyRail, DeterministicCodePRM


class TestAGYArtifactsSubsystem:
    """Tests compliance with Google AGY artifacts formatting specifications."""

    def test_alert_formatting(self):
        alert_note = AGYArtifactsManager.format_alert("note", "This is an informational notice.")
        assert alert_note.startswith("> [!NOTE]")
        assert "> This is an informational notice." in alert_note

        alert_warn = AGYArtifactsManager.format_alert("warning", "Breaking change ahead.\nProceed carefully.")
        assert alert_warn.startswith("> [!WARNING]")
        assert "> Breaking change ahead." in alert_warn
        assert "> Proceed carefully." in alert_warn

    def test_mermaid_diagram_formatting_and_sanitization(self):
        raw_body = "A[Start (User Request)] --> B[Process Task]\nB --> C{Verified?}"
        diagram = AGYArtifactsManager.format_mermaid("flowchart TD", raw_body)
        assert diagram.startswith("```mermaid\nflowchart TD")
        assert 'A["Start (User Request)"]' in diagram
        assert diagram.endswith("```")

    def test_carousel_formatting(self):
        slides = [
            "```python\ndef baseline(): pass\n```",
            "```python\ndef optimized(): return True\n```"
        ]
        carousel = AGYArtifactsManager.format_carousel(slides)
        assert carousel.startswith("````carousel")
        assert "<!-- slide -->" in carousel
        assert carousel.endswith("````")

    def test_markdown_and_html_artifact_creation(self, tmp_path):
        mgr = AGYArtifactsManager(conversation_id="test-session-123", brain_dir=tmp_path)
        md_file = mgr.create_markdown_artifact(
            filename="architecture-spec.md",
            title="System Architecture",
            content="# Title\nDetails here.",
            summary="Specifies high level architecture",
            user_facing=True,
            request_feedback=True
        )
        assert md_file.exists()
        assert md_file.read_text() == "# Title\nDetails here."

        html_file = mgr.create_html_auxiliary_app(
            filename="dashboard.html",
            title="Telemetry Dashboard",
            html_body="<div id='metrics'>Active</div>",
            js_scripts="console.log('loaded');"
        )
        assert html_file.exists()
        content = html_file.read_text()
        assert "Telemetry Dashboard" in content
        assert "chart.js" in content.lower()
        assert "katex" in content.lower()

        artifacts = mgr.list_artifacts()
        assert len(artifacts) >= 1
        assert artifacts[0]["filename"] == "architecture-spec.md"


class TestGeminiThoughtSignatures:
    """Tests preservation of Gemini 3.8/4.0 thought signatures."""

    def test_signature_extraction_and_decoration(self):
        preserver = GeminiThoughtSignaturePreserver()
        model_turn = {
            "role": "model",
            "parts": [
                {
                    "thought": True,
                    "thought_signature": "cryptographic_sig_xyz_123",
                    "text": "Planning to call file viewer..."
                },
                {
                    "functionCall": {
                        "name": "view_file",
                        "args": {"path": "main.py"}
                    },
                    "thought_signature": "cryptographic_sig_xyz_123"
                }
            ]
        }
        sig = preserver.register_turn_response(model_turn)
        assert sig == "cryptographic_sig_xyz_123"

        # Decorate tool response
        decorated = preserver.decorate_tool_response(
            call_id="view_file",
            tool_result={"content": "print('hello')"},
            strict=True
        )
        assert decorated["role"] == "user"
        assert decorated["thought_signature"] == "cryptographic_sig_xyz_123"
        assert decorated["parts"][0]["thought_signature"] == "cryptographic_sig_xyz_123"

    def test_strict_mode_raises_on_missing_signature(self):
        preserver = GeminiThoughtSignaturePreserver()
        with pytest.raises(ValueError, match="HTTP 400 INVALID_ARGUMENT"):
            preserver.decorate_tool_response("unknown_tool", {}, strict=True)


class TestHierarchicalRuleWalker:
    """Tests 'closer is better' rule resolution and progressive disclosure."""

    def test_progressive_disclosure_token_capping(self, tmp_path):
        root_agents_md = tmp_path / "AGENTS.md"
        root_agents_md.write_text("""---
name: Project Root Rule
description: Must follow clean architecture.
---
# Root Rules
Ensure all tests pass. Do not push broken commits. Never bypass pre-commit hooks.
""")
        walker = HierarchicalRuleWalker(workspace_root=tmp_path)
        context = walker.compile_prompt_context(max_tokens=200)
        assert "Progressive Rules Hierarchy" in context
        assert "Project Root Rule" in context
        # Asserts character count is within bounds (~200 tokens * 4 chars)
        assert len(context) <= 800


class TestMagenticDualLedger:
    """Tests Magentic-One Task & Progress Ledgers with 2-turn stall detection."""

    def test_ledger_milestones_and_facts(self):
        ledger = MagenticDualLedger(objective="Refactor Auth Subsystem")
        ledger.add_fact("Legacy token expires in 3600s.")
        ledger.add_milestone("M1", "Extract JWT validator")
        assert len(ledger.task_ledger["milestones"]) == 1
        assert len(ledger.task_ledger["verified_facts"]) == 1

        ledger.complete_milestone("M1")
        assert ledger.task_ledger["milestones"][0]["completed"] is True

    def test_two_turn_stall_circuit_breaker(self):
        ledger = MagenticDualLedger(objective="Fix Parser Bug")
        
        # Turn 1: No measurable progress
        stalled, msg = ledger.record_step(
            step_index=1,
            agent_role="coder",
            action="grep invalid syntax",
            observation="no matches found",
            success=False,
            measurable_progress=False
        )
        assert stalled is False
        assert ledger.stall_counter == 1

        # Turn 2: Second consecutive non-progress step -> Triggers Circuit Breaker!
        stalled, msg = ledger.record_step(
            step_index=2,
            agent_role="coder",
            action="grep invalid syntax again",
            observation="no matches found",
            success=False,
            measurable_progress=False
        )
        assert stalled is True
        assert "STALL CIRCUIT BREAKER" in msg
        assert ledger.stall_counter == 2

        # Turn 3: Successful step with measurable progress resets stall counter
        stalled, msg = ledger.record_step(
            step_index=3,
            agent_role="coder",
            action="view_file parser.py",
            observation="located syntax error on line 42",
            success=True,
            measurable_progress=True
        )
        assert stalled is False
        assert ledger.stall_counter == 0


class TestA2AAgentCardAndServer:
    """Tests Google A2A protocol card and JSON-RPC dispatch."""

    def test_agent_card_schema(self):
        server = A2AAgentCardServer()
        card = server.get_agent_card()
        assert card["$schema"] == "https://a2a-protocol.org/v1/agent-card.json"
        assert card["name"] == "Hermes Agent OS"
        assert len(card["supportedInterfaces"]) == 2
        assert len(card["skills"]) >= 2

    def test_jsonrpc_message_send_and_get(self):
        server = A2AAgentCardServer()
        req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "message/send",
            "params": {
                "message": {"role": "user", "text": "Run security check"}
            }
        }
        res = server.handle_jsonrpc_request(req)
        assert res["jsonrpc"] == "2.0"
        task_id = res["result"]["taskId"]
        assert task_id is not None
        assert res["result"]["status"] == "working"

        get_req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tasks/get",
            "params": {"taskId": task_id}
        }
        get_res = server.handle_jsonrpc_request(get_req)
        assert get_res["result"]["status"] == "working"


class TestShannonEntropyAndPRM:
    """Tests Shannon Entropy execution rail and deterministic AST PRM."""

    def test_entropy_evaluation(self):
        # Repetitive context bloat
        low_entropy = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        valid, msg = ShannonEntropyRail.evaluate_payload(low_entropy)
        assert valid is False
        assert "Low entropy detected" in msg

        # Natural code/text payload
        normal_payload = "def calculate_sum(a: int, b: int) -> int:\n    '''Calculates the sum of two integers.'''\n    return a + b\n"
        valid, msg = ShannonEntropyRail.evaluate_payload(normal_payload)
        assert valid is True

    def test_deterministic_prm_scoring(self):
        valid_patch = """<<<<<<< SEARCH
def old_fn():
    return False
=======
def old_fn():
    return True
>>>>>>> REPLACE"""
        score, msg = DeterministicCodePRM.score_diff_step(valid_patch)
        assert score == 1.0
        assert "PRM Passed" in msg

        syntax_error_patch = """<<<<<<< SEARCH
def old_fn():
    pass
=======
def broken_fn(
    return True
>>>>>>> REPLACE"""
        score, msg = DeterministicCodePRM.score_diff_step(syntax_error_patch)
        assert score < 1.0
        assert "syntax errors" in msg.lower()

        oversized_patch = "\n".join(["line"] * 100)
        score, msg = DeterministicCodePRM.score_diff_step(oversized_patch)
        assert score < 0.5
        assert "exceeds 80 lines" in msg
