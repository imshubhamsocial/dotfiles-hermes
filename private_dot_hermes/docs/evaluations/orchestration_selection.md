# Architectural Evaluation & Selection: Primary Orchestration Layer (Google ADK vs. LangGraph)

> **Milestone**: D7-15 & D7-16  
> **Status**: Completed & Certified  
> **Decision**: **Select Google ADK as Hermes's Sole Primary Agent Orchestration Layer**  
> **Rejection**: **LangGraph Rejected** (Redundant abstraction, state schema bloat, database collision)

---

## 1. Executive Context & Decision Rationale

As defined in **Roadmap 7 Part 3.4 & Part 5 (Milestones D7-15 & D7-16)**:
Google ADK and LangGraph both compete for the primary agent orchestration layer. Running both frameworks simultaneously would directly violate **Law #8 of Hermes OS** (*Upstream Engine + Hardware Calibration Adapter First*) and introduce severe duplicate framework bloat into `ws-hermes`.

Following the empirical evaluation of Google ADK in Milestone D7-13 ([`docs/evaluations/google_adk_evaluation.md`](./google_adk_evaluation.md)) and the successful migration of Hermes's domain bot fleet in Milestone D7-14 ([`hermes_core.domain_fleet`](../../.hermes/src/hermes_core/domain_fleet.py)), this document formalizes the comparative architectural analysis and final selection.

---

## 2. Comparative Analysis Matrix

| Evaluation Dimension | Google Agent Development Kit (ADK 2.8.0) | LangGraph (`langgraph` / `langgraph-swarm`) | Advantage / Verdict |
| :--- | :--- | :--- | :--- |
| **Agent Abstraction** | Clean `BaseAgent`, `LlmAgent`, `CustomAgent` hierarchy | Dict-based `StateGraph` nodes requiring explicit TypedDict state schemas | 🟢 **ADK**: Natural object model; zero schema boilerplate |
| **Event & Telemetry Stream** | Native typed `Event` stream with `EventActions` (state deltas, transfers) | Custom stream generators requiring adapter serialization | 🟢 **ADK**: Direct alignment with OpenLIT / OpenTelemetry |
| **A2A Multi-Bot Delegation** | First-class `transfer_to_agent` recognized by native `Runner` | Conditional edge routing via router functions and state annotations | 🟢 **ADK**: 1-line dynamic delegation |
| **Local Inference Alignment** | Non-blocking execution via `asyncio.to_thread` against `llama-server` port 8138 | Synchronous invoke wrappers or heavy LangChain OpenAI clients | 🟢 **ADK**: Fully non-blocking event loop preserved |
| **Memory / Database Layer** | Abstract `SessionService` adapts directly to existing `state.db` | Requires separate checkpoint savers (`MemorySaver`, `SqliteSaver`) | 🟢 **ADK**: Zero collision with Hermes SQLite WAL database |
| **Workspace Git Rollback** | Delegated cleanly to domain-specific `branch_swapper.py` | Over-engineered checkpoint rollback state machines | 🟢 **ADK + Custom Swapper**: 200 LOC focused Git tree reset |
| **Token & Prompt Footprint** | Minimal prompt overhead; prefix-cache friendly byte alignment | Pushes conversational histories and state dumps into LLM context | 🟢 **ADK**: Respects SLM 350-token budgets |
| **Dependency Weight** | Lightweight (`google-adk`, `pydantic`) | Heavy dependency graph (`langchain-core`, `langgraph-checkpoint`, etc.) | 🟢 **ADK**: Clean installation in `ws-hermes` |

---

## 3. Concrete Architectural Findings

### 3.1 Why LangGraph was Rejected
1. **Redundant Framework Bloat**: LangGraph introduces another full abstraction layer (`StateGraph`, `START`, `END`, custom reducer functions) that duplicates what Google ADK's `Workflow` and `HermesOrchestrator` already provide.
2. **State Storage Collision**: LangGraph forces its own checkpointing database schema (`checkpoints`, `writes`), creating dual-database lock contention with Hermes's canonical SQLite WAL `state.db`.
3. **Irreplaceable Custom Primitives (Part 4 Alignment)**: As documented in `docs/roadmap.md`, Hermes's 2-strike Tabu branch swapper (`branch_swapper.py`) requires actual OS-level Git working tree checkouts and commit resets (`git reset --hard HEAD~1`). Neither LangGraph nor ADK can replace this OS-level git operation; keeping `branch_swapper.py` custom is mathematically required.

### 3.2 Why Google ADK was Selected
1. **Production Parity with Antigravity**: ADK provides the exact architectural patterns (hierarchical agents, sub-agents, reactive events) used by Google Antigravity.
2. **100% Contract Test Certification**:
   - `test_adk_orchestrator.py`: 9/9 passed.
   - `test_domain_fleet_adk.py`: 5/5 passed.
   - Total 14/14 tests pass green in <4 seconds.
3. **Hardware-Calibrated Adapter Pattern**:
   `HermesADKCustomAgent` and `domain_fleet.py` inject Hermes's strict local constraints (RTX 3050 VRAM $\le 4,812\text{ MiB}$, Gemma-4, port 8138, token ceilings $\le 350$) into standard ADK workflows without mutating upstream internals.

---

## 4. Implementation Directives & Closure of Domain 7

1. **Remove LangGraph from roadmap requirements**: No installation of `langgraph` or `langgraph-swarm` is required or permitted.
2. **Standardize on ADK Agent Composition**:
   - All multi-bot workflows (`@architect`, `@coder`, `@tester`, `@reviewer`, `@security`) use `DomainFleetManager.build_adk_agent()` and `DomainFleetManager.build_adk_pipeline()`.
3. **Milestones Closed**:
   - **D7-13**: Evaluated Google ADK (`HermesADKCustomAgent`) ✅ Completed.
   - **D7-14**: Migrated `domain_fleet.py` to Google ADK composition ✅ Completed.
   - **D7-15**: Evaluated LangGraph vs ADK state machines ✅ Completed.
   - **D7-16**: Selected Google ADK as primary orchestration layer ✅ Completed.
