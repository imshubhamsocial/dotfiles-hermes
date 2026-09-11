"""
Contract Tests: DynamicToolRetriever (DTDR) & Agent2Agent (A2A) Protocols
========================================================================
Validates:
  1. Semantic keyword and name scoring for dynamic tool retrieval.
  2. Prompt injection XML formatting under token budget.
  3. A2A Agent Card role profiles (@architect, @coder, @tester).
  4. Typed machine-to-machine handoff protocol creation and validation.
"""

import pytest

from plugins.skill_intelligence import DynamicToolRetriever, Agent2AgentProtocol


class TestDynamicToolRetriever:
    @pytest.fixture
    def retriever(self) -> DynamicToolRetriever:
        return DynamicToolRetriever()

    def test_tool_retrieval_by_name_and_keyword(self, retriever: DynamicToolRetriever):
        matches = retriever.find_tools("Please edit calc.py with search_replace", top_k=2)
        assert len(matches) >= 1
        assert matches[0]["name"] == "search_replace"

    def test_tool_retrieval_for_code_execution(self, retriever: DynamicToolRetriever):
        matches = retriever.find_tools("Execute a python script to calculate values", top_k=2)
        assert len(matches) >= 1
        tool_names = [m["name"] for m in matches]
        assert "run_code_action" in tool_names

    def test_tool_retrieval_for_web_scraping(self, retriever: DynamicToolRetriever):
        matches = retriever.find_tools("Extract documentation from this web URL", top_k=2)
        assert len(matches) >= 1
        assert matches[0]["name"] == "web_extract"

    def test_format_prompt_injection(self, retriever: DynamicToolRetriever):
        tools = retriever.find_tools("search for AST patterns and edit files", top_k=2)
        xml_block = retriever.format_prompt_injection(tools)
        assert "<dynamic_tools>" in xml_block
        assert "</dynamic_tools>" in xml_block
        for t in tools:
            assert f'<tool name="{t["name"]}"' in xml_block


class TestAgent2AgentProtocol:
    def test_agent_card_discovery(self):
        arch_card = Agent2AgentProtocol.get_agent_card("architect")
        assert arch_card is not None
        assert "ast_search" in arch_card["allowed_tools"]
        assert arch_card["output_contract"] == "SPEC_HANDOFF"

        coder_card = Agent2AgentProtocol.get_agent_card("coder")
        assert coder_card is not None
        assert "search_replace" in coder_card["allowed_tools"]
        assert coder_card["output_contract"] == "PATCH_HANDOFF"

        tester_card = Agent2AgentProtocol.get_agent_card("tester")
        assert tester_card is not None
        assert "run_command" in tester_card["allowed_tools"]

    def test_handoff_creation_and_validation(self):
        spec_payload = {"task": "Add caching to AST scanner", "acceptance": "All tests pass"}
        handoff = Agent2AgentProtocol.create_handoff(
            source_role="architect",
            target_role="coder",
            payload=spec_payload,
        )
        assert handoff["protocol"] == "A2A/1.0"
        assert handoff["source_role"] == "architect"
        assert handoff["target_role"] == "coder"
        assert handoff["contract_type"] == "ARCHITECT_TO_CODER"
        assert handoff["payload"] == spec_payload

        valid, err = Agent2AgentProtocol.validate_handoff(handoff)
        assert valid is True
        assert err is None

    def test_handoff_validation_rejection(self):
        invalid_handoff = {"protocol": "OLD/0.1"}
        valid, err = Agent2AgentProtocol.validate_handoff(invalid_handoff)
        assert valid is False
        assert "Invalid protocol" in err
