"""
Contract Tests: D7-13 Google ADK CustomAgent Orchestrator Wrapper
=================================================================
Validates:
  1. HermesADKCustomAgent initialization, validation, and metadata.
  2. ADK Content / Event bidirectional conversions.
  3. Non-blocking async execution through google.adk.runners.Runner.
  4. Context variables / state delta synchronization with ADK Session.
  5. Session history reconstruction from multi-turn ADK event streams.
  6. Swarm agent transfer propagation via ADK EventActions(transfer_to_agent).
  7. Sequential workflow composition using ADK SequentialAgent.
"""

import asyncio
from unittest.mock import MagicMock
import pytest
from google.adk.agents import BaseAgent, SequentialAgent
from google.adk.events import Event, EventActions
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from hermes_core.agent import Agent, Response, Result
from hermes_core.adk_custom_agent import (
    HermesADKCustomAgent,
    adk_content_to_str,
    hermes_response_to_adk_event,
)
from hermes_core.swarm_engine import HermesOrchestrator


class TestADKOrchestrator:
    """Contract tests for D7-13 Google ADK CustomAgent integration."""

    def test_agent_instantiation_and_fields(self):
        """HermesADKCustomAgent initializes with correct fields and inherits BaseAgent."""
        agent = HermesADKCustomAgent(
            name="test_orchestrator",
            description="Autonomous testing agent",
            preset="minimal",
            max_turns=5,
            verbose=False,
            auto_handoff=True,
        )
        assert isinstance(agent, BaseAgent)
        assert agent.name == "test_orchestrator"
        assert agent.preset == "minimal"
        assert agent.max_turns == 5
        assert agent.auto_handoff is True

    def test_invalid_name_validation(self):
        """Rejects invalid identifier names as required by ADK BaseAgent."""
        with pytest.raises(ValueError):
            HermesADKCustomAgent(name="invalid-name-with-hyphens")

    def test_adk_content_to_str_extraction(self):
        """Correctly extracts text across multiple content representations."""
        assert adk_content_to_str(None) == ""
        assert adk_content_to_str("direct string") == "direct string"

        content = types.Content(
            parts=[
                types.Part.from_text(text="Hello "),
                types.Part.from_text(text="World!"),
            ]
        )
        assert adk_content_to_str(content) == "Hello World!"

    def test_hermes_response_to_adk_event_conversion(self):
        """Converts Hermes Response into a valid ADK Event."""
        resp = Response(
            messages=[
                {"role": "user", "content": "Run tests"},
                {"role": "assistant", "content": "Tests passed successfully."},
            ],
            agent=Agent(name="runner_agent"),
            context_variables={"test_count": 42, "status": "GREEN"},
        )

        event = hermes_response_to_adk_event(resp, author="runner_agent")
        assert event.author == "runner_agent"
        assert event.content.parts[0].text == "Tests passed successfully."
        assert event.actions.state_delta == {"test_count": 42, "status": "GREEN"}
        assert event.actions.transfer_to_agent is None

    def test_hermes_response_transfer_to_agent_propagation(self):
        """Agent handoff sets actions.transfer_to_agent on the ADK Event."""
        next_bot = Agent(name="refactor_specialist")
        resp = Response(
            messages=[
                {"role": "assistant", "content": "Delegating to refactor specialist."}
            ],
            agent=next_bot,
            context_variables={"target_file": "core.py"},
        )

        event = hermes_response_to_adk_event(resp, author="triage_agent")
        assert event.author == "triage_agent"
        assert event.actions.transfer_to_agent == "refactor_specialist"
        assert event.actions.state_delta["target_file"] == "core.py"

    def test_adk_runner_execution_flow(self):
        """Runs HermesADKCustomAgent inside official ADK Runner with InMemorySessionService."""
        async def _run():
            mock_orch = MagicMock()
            mock_orch.run.return_value = Response(
                messages=[{"role": "assistant", "content": "Mocked Hermes execution response"}],
                agent=Agent(name="hermes_bot"),
                context_variables={"execution_id": "exec_999"},
            )

            bot = HermesADKCustomAgent(
                name="hermes_bot",
                orchestrator=mock_orch,
                max_turns=3,
            )

            service = InMemorySessionService()
            runner = Runner(agent=bot, session_service=service, app_name="hermes_test_app")
            session = await service.create_session(app_name="hermes_test_app", user_id="tester")

            user_content = types.Content(parts=[types.Part.from_text(text="Solve bug #101")])
            events = []
            async for ev in runner.run_async(
                session_id=session.id,
                user_id="tester",
                new_message=user_content,
            ):
                events.append(ev)

            assert len(events) >= 1
            agent_event = [e for e in events if e.author == "hermes_bot"][0]
            assert "Mocked Hermes execution response" in agent_event.content.parts[0].text
            assert agent_event.actions.state_delta == {"execution_id": "exec_999"}
            assert mock_orch.run.called

        asyncio.run(_run())

    def test_session_history_reconstruction(self):
        """Reconstructs full multi-turn conversation messages from prior session events."""
        async def _run():
            recorded_messages = []

            def fake_run(agent, messages, context_variables, max_turns, verbose, preset):
                recorded_messages.extend(messages)
                return Response(
                    messages=messages + [{"role": "assistant", "content": "Turn processed"}],
                    agent=agent,
                )

            mock_orch = MagicMock()
            mock_orch.run.side_effect = fake_run

            bot = HermesADKCustomAgent(
                name="history_bot",
                orchestrator=mock_orch,
            )

            service = InMemorySessionService()
            runner = Runner(agent=bot, session_service=service, app_name="history_app")
            session = await service.create_session(app_name="history_app", user_id="tester")

            # Turn 1
            async for _ in runner.run_async(
                session_id=session.id,
                user_id="tester",
                new_message=types.Content(parts=[types.Part.from_text(text="Turn 1 Prompt")]),
            ):
                pass

            # Turn 2
            recorded_messages.clear()
            async for _ in runner.run_async(
                session_id=session.id,
                user_id="tester",
                new_message=types.Content(parts=[types.Part.from_text(text="Turn 2 Prompt")]),
            ):
                pass

            # Verify history includes earlier turns
            user_prompts = [m["content"] for m in recorded_messages if m["role"] == "user"]
            assert "Turn 1 Prompt" in user_prompts
            assert "Turn 2 Prompt" in user_prompts

        asyncio.run(_run())

    def test_sequential_workflow_composition(self):
        """Composes multiple HermesADKCustomAgents in an ADK SequentialAgent pipeline."""
        async def _run():
            orch_a = MagicMock()
            orch_a.run.return_value = Response(
                messages=[{"role": "assistant", "content": "Stage 1 output"}],
                context_variables={"stage": 1},
            )

            orch_b = MagicMock()
            orch_b.run.return_value = Response(
                messages=[{"role": "assistant", "content": "Stage 2 output"}],
                context_variables={"stage": 2},
            )

            bot_a = HermesADKCustomAgent(name="bot_a", orchestrator=orch_a)
            bot_b = HermesADKCustomAgent(name="bot_b", orchestrator=orch_b)

            pipeline = SequentialAgent(name="two_stage_pipeline", sub_agents=[bot_a, bot_b])

            service = InMemorySessionService()
            runner = Runner(agent=pipeline, session_service=service, app_name="pipe_app")
            session = await service.create_session(app_name="pipe_app", user_id="tester")

            emitted_authors = []
            async for ev in runner.run_async(
                session_id=session.id,
                user_id="tester",
                new_message=types.Content(parts=[types.Part.from_text(text="Run pipeline")]),
            ):
                if ev.author in ("bot_a", "bot_b"):
                    emitted_authors.append(ev.author)

            assert "bot_a" in emitted_authors
            assert "bot_b" in emitted_authors

        asyncio.run(_run())

    def test_tool_execution_parity_in_adk(self):
        """Validates tool execution and context variable updates flowing into ADK events."""
        async def _run():
            def calculate_square(n: int) -> Result:
                return Result(value=str(n * n), context_variables={"last_square": n * n})

            tool_agent = Agent(
                name="math_bot",
                instructions="Compute squares",
                functions=[calculate_square],
            )

            mock_orch = MagicMock()
            mock_orch.run.return_value = Response(
                messages=[
                    {"role": "user", "content": "Square 7"},
                    {"role": "assistant", "content": "49"},
                ],
                agent=tool_agent,
                context_variables={"last_square": 49},
            )

            bot = HermesADKCustomAgent(
                name="math_bot",
                hermes_agent=tool_agent,
                orchestrator=mock_orch,
            )

            service = InMemorySessionService()
            runner = Runner(agent=bot, session_service=service, app_name="math_app")
            session = await service.create_session(app_name="math_app", user_id="tester")

            events = []
            async for ev in runner.run_async(
                session_id=session.id,
                user_id="tester",
                new_message=types.Content(parts=[types.Part.from_text(text="Square 7")]),
            ):
                events.append(ev)

            math_event = [e for e in events if e.author == "math_bot"][0]
            assert "49" in math_event.content.parts[0].text
            assert math_event.actions.state_delta["last_square"] == 49

        asyncio.run(_run())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
