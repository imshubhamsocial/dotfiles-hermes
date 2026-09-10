# Google Agent Development Kit (ADK) Architectural Evaluation

> **Milestone**: D7-13  
> **Status**: Completed  
> **Evaluated Version**: `google-adk 2.8.0`  
> **Target Substrate**: `hermes_core` (`HermesOrchestrator`, `HermesADKCustomAgent`)

---

## 1. Executive Summary

As part of Domain 7's framework rationalization, Google Agent Development Kit (ADK) was evaluated as a candidate primary orchestration layer to replace or standardize Hermes's custom Swarm engine (`swarm_engine.py`, ~650 LOC), task graph orchestration (`task_graph.py`, ~1,100 LOC), and multi-agent delegation (`domain_fleet.py` / `multi_bot_delegation.py`, ~390 LOC).

In Milestone D7-13, [`HermesADKCustomAgent`](file://~/.hermes/plugins/adk_orchestrator/adk_custom_agent.py) was built as an official subclass of `google.adk.agents.BaseAgent`, wrapping [`HermesOrchestrator`](file://~/.hermes/plugins/adk_orchestrator/swarm_engine.py) to bridge Hermes's local model inference, cognitive governors, and capability masks into ADK's native `Runner`, `SessionService`, and `Event` stream.

---

## 2. Core Architecture & Mapping Matrix

| Hermes Native Primitive | Google ADK Equivalent | Integration Mechanism | Status |
|---|---|---|---|
| `Agent` (Pydantic model) | `BaseAgent` / `LlmAgent` | `HermesADKCustomAgent(BaseAgent)` | ✅ Verified |
| `Response` (`messages`, `context_vars`) | `Event` (`message`, `actions.state_delta`) | `hermes_response_to_adk_event()` | ✅ Verified |
| A2A handoff (`Result(agent=next)`) | `EventActions(transfer_to_agent=...)` | Native routing in ADK Runner | ✅ Verified |
| Session memory / context variables | `Session.state` | Bi-directional dictionary synchronization | ✅ Verified |
| Multi-turn conversational history | `Session.events` stream | Automatic message history reconstruction | ✅ Verified |
| Pipeline orchestration | `SequentialAgent` / `Workflow` | Composite sub-agent execution | ✅ Verified |
| Tool execution loop | `BaseAgent.tools` / Toolset | Masked Python callables with Pydantic schemas | ✅ Verified |

---

## 3. Implementation Details

1. **Async Non-Blocking Execution**:
   Hermes's model inference loop (`HermesOrchestrator.run`) executes synchronously against local llama-server (or mock endpoints). `HermesADKCustomAgent._run_async_impl` wraps this via `asyncio.to_thread` to preserve non-blocking event-loop semantics inside ADK runners.

2. **Session History Reconstruction**:
   Multi-turn conversational contexts stored in ADK's `Session.events` are automatically extracted and transformed into OpenAI/Hermes role-based message dictionaries (`user`, `assistant`), preserving prior context across repeated invocations.

3. **Dynamic Swarm Transfers**:
   When Hermes's internal swarm engine returns a delegation transfer to another agent (`response.agent.name != self.name`), the wrapper populates `EventActions(transfer_to_agent=...)`. ADK's native `Runner` recognizes this action and transfers control to the matching registered sub-agent.

---

## 4. Evaluation Findings: Strengths & Trade-offs

### Strengths
- **Clean Event Architecture**: Typed `Event` and `EventActions` simplify streaming, debugging, and UI telemetry.
- **Enterprise Session Services**: Built-in abstract `SessionService` with memory and SQLite implementations standardizes persistence.
- **Multi-Agent Composition**: Native support for hierarchical sub-agents, workflows, and dynamic agent transfer.

### Trade-offs & Considerations
- **OpenTelemetry Pinning**: `google-adk 2.8.0` requires `opentelemetry-sdk<=1.42.1`. While compatible with `openlit`, it requires strict version pinning to prevent dependency conflicts with newer OTel instrumentors.
- **SequentialAgent Deprecation**: ADK 2.8.0 emits a deprecation warning on `SequentialAgent` in favor of `Workflow`, which should be adopted during long-term migration.
- **Cyclic State Graph Comparison**: For deterministic multi-branch rollbacks (e.g. `branch_swapper.py` 2-strike tabu search), LangGraph's explicit state graphs and checkpoints offer more granular graph rollback than ADK's agent-transfer model.

---

## 5. Certification & Contract Test Verification

The wrapper is certified via 9 contract tests in [`~/.hermes/tests/agent/test_adk_orchestrator.py`](file://~/.hermes/tests/agent/test_adk_orchestrator.py):
- `test_agent_instantiation_and_fields`
- `test_invalid_name_validation`
- `test_adk_content_to_str_extraction`
- `test_hermes_response_to_adk_event_conversion`
- `test_hermes_response_transfer_to_agent_propagation`
- `test_adk_runner_execution_flow`
- `test_session_history_reconstruction`
- `test_sequential_workflow_composition`
- `test_tool_execution_parity_in_adk`

All 9/9 tests pass green with zero regressions across the 18/18 domain test suite.
