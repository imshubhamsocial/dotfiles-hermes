"""
Contract Tests: Native Google ADK Fleet Composition & Sequential Pipelines
==========================================================================
Validates:
  1. HermesADKCustomAgent role instantiation and instruction encapsulation.
  2. Multi-agent sequential pipeline composition via google.adk.agents.SequentialAgent.
  3. Single-turn async event execution across ADK custom agent instances.
"""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock
import pytest
from google.adk.agents import SequentialAgent

from plugins.adk_orchestrator.adk_custom_agent import (
    HermesADKCustomAgent,
    adk_content_to_str,
)
from plugins.adk_orchestrator.agent import Response


class TestDomainFleetADK:
    def test_adk_agent_generation(self):
        agent_arch = HermesADKCustomAgent(
            name="bot_architect",
            description="Design DAG",
            instructions="=== ROLE: @architect ===\nTopological DAG design",
        )
        assert isinstance(agent_arch, HermesADKCustomAgent)
        assert agent_arch.name == "bot_architect"
        assert "=== ROLE: @architect ===" in agent_arch.instructions
        assert "Topological DAG" in agent_arch.instructions

    def test_adk_bot_isolation_purity(self):
        agent_coder = HermesADKCustomAgent(
            name="bot_coder",
            description="Write unit tests",
            instructions="Adhere strictly to .hermes/plan.json",
        )
        assert isinstance(agent_coder, HermesADKCustomAgent)
        assert agent_coder.name == "bot_coder"
        assert "Never write or edit code files directly" not in agent_coder.instructions
        assert "Adhere strictly to .hermes/plan.json" in agent_coder.instructions

    def test_adk_pipeline_composition(self):
        bot_arch = HermesADKCustomAgent(name="bot_architect", description="Design")
        bot_coder = HermesADKCustomAgent(name="bot_coder", description="Code")
        bot_tester = HermesADKCustomAgent(name="bot_tester", description="Test")

        pipeline = SequentialAgent(
            name="tdd_cycle",
            sub_agents=[bot_arch, bot_coder, bot_tester],
        )
        assert pipeline.name == "tdd_cycle"
        assert len(pipeline.sub_agents) == 3
        assert [a.name for a in pipeline.sub_agents] == ["bot_architect", "bot_coder", "bot_tester"]

    def test_adk_bot_turn_execution(self):
        async def _run():
            mock_orchestrator = MagicMock()
            mock_orchestrator.run.return_value = Response(
                messages=[{"role": "assistant", "content": "Spec approved: milestone 1"}],
                agent=None,
                context_variables={"status": "approved"},
            )

            agent = HermesADKCustomAgent(
                name="bot_architect",
                description="Architect agent",
                orchestrator=mock_orchestrator,
            )
            mock_ctx = MagicMock()
            mock_ctx.session.events = []
            mock_ctx.session.state = {}

            events = []
            async for ev in agent._run_async_impl(mock_ctx):
                events.append(ev)

            assert len(events) == 1
            assert events[0].author == "bot_architect"
            assert adk_content_to_str(events[0].message) == "Spec approved: milestone 1"
            assert events[0].actions.state_delta.get("status") == "approved"

        asyncio.run(_run())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
