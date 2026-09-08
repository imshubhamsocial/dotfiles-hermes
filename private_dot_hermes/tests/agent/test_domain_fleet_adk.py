"""
Internal Unit Test Suite: Milestone D7-14
Native Google ADK Fleet Composition & Domain Bot Mapping
"""

from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from hermes_core.domain_fleet import DomainFleetManager, create_domain_fleet_manager
from hermes_core.adk_custom_agent import HermesADKCustomAgent
from hermes_core.agent import Response


class TestDomainFleetADK:
    @pytest.fixture
    def fleet(self) -> DomainFleetManager:
        return create_domain_fleet_manager()

    def test_adk_agent_generation(self, fleet: DomainFleetManager):
        agent_arch = fleet.build_adk_agent("architect", task_prompt="Design DAG")
        assert isinstance(agent_arch, HermesADKCustomAgent)
        assert agent_arch.name == "bot_architect"
        assert "=== ROLE: @architect ===" in agent_arch.instructions
        assert "Topological DAG" in agent_arch.instructions or "DAG" in agent_arch.description

    def test_adk_bot_isolation_purity(self, fleet: DomainFleetManager):
        agent_coder = fleet.build_adk_agent("coder", task_prompt="Write unit tests")
        assert isinstance(agent_coder, HermesADKCustomAgent)
        assert agent_coder.name == "bot_coder"
        # Invariant R5-3: Coder must not contain forbidden researcher constraints
        assert "Never write or edit code files directly" not in agent_coder.instructions
        assert "Adhere strictly to .hermes/plan.json" in agent_coder.instructions

    def test_adk_fleet_dictionary_generation(self, fleet: DomainFleetManager):
        fleet_dict = fleet.build_adk_fleet(["architect", "coder", "tester", "security"])
        assert "architect" in fleet_dict
        assert "coder" in fleet_dict
        assert "tester" in fleet_dict
        assert "security" in fleet_dict

        for b_name, bot in fleet_dict.items():
            assert isinstance(bot, HermesADKCustomAgent)
            assert bot.name == f"bot_{b_name.replace('-', '_')}"

    def test_adk_pipeline_composition(self, fleet: DomainFleetManager):
        stages = ["architect", "coder", "tester"]
        pipeline = fleet.build_adk_pipeline(stages, pipeline_name="tdd_cycle")
        assert pipeline.name == "tdd_cycle"
        assert len(pipeline.sub_agents) == 3
        assert [a.name for a in pipeline.sub_agents] == ["bot_architect", "bot_coder", "bot_tester"]

    def test_adk_bot_turn_execution(self, fleet: DomainFleetManager):
        import asyncio
        from hermes_core.adk_custom_agent import adk_content_to_str

        async def _run():
            mock_orchestrator = MagicMock()
            mock_orchestrator.run.return_value = Response(
                messages=[{"role": "assistant", "content": "Spec approved: milestone 1"}],
                agent=None,
                context_variables={"status": "approved"},
            )

            agent = fleet.build_adk_agent("architect", orchestrator=mock_orchestrator)
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


