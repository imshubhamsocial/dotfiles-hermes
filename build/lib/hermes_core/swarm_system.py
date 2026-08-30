"""
Universal 5-Bot Agent Swarm System (100% Domain-Agnostic)
=========================================================
Generic software engineering specialist agents:
  - researcher_agent: Web, documentation and API discovery.
  - architect_agent: System-2 topological planning and task breakdown.
  - coder_agent: Universal code implementation and sliced patching.
  - tester_agent: Deterministic test suite execution (pytest, npm test, cargo test).
  - debugger_agent: 4-phase systematic root-cause elimination and in-place surgery.
"""

from typing import Dict, Any
from .agent import Agent, Result
from .tools import (
    read_file, write_file, patch_file, execute_command, 
    run_test_suite, search_web, get_symbol_map, 
    get_workspace_tree, query_knowledge_graph, grep_codebase, refactor_symbol
)



# ─── 1. Universal Functional Handoffs ───

def handoff_to_architect(blueprint_context: str = "") -> Result:
    """Transfer task to @architect with technical intelligence."""
    return Result(
        value=f"Transferred to @architect with context: {blueprint_context[:200]}...",
        agent=architect_agent
    )

def handoff_to_coder(task_specification: str = "") -> Result:
    """Transfer implementation task to @coder."""
    return Result(
        value=f"Transferred to @coder for implementation: {task_specification[:200]}...",
        agent=coder_agent
    )

def handoff_to_tester(test_command: str = "pytest") -> Result:
    """Transfer project to @tester for deterministic test verification."""
    return Result(
        value=f"Transferred to @tester with test command: '{test_command}'.",
        agent=tester_agent
    )

def handoff_to_debugger(diagnostic_trace: str = "") -> Result:
    """Transfer failing test trace to @debugger for surgical root-cause elimination."""
    return Result(
        value=f"Transferred to @debugger with failure trace: {diagnostic_trace[:200]}...",
        agent=debugger_agent
    )


# ─── 2. Universal Agent Definitions ───

researcher_agent = Agent(
    name="researcher",
    model="qwen3.8-4b",
    temperature=0.2,
    instructions="""You are @researcher. Your responsibility is to discover exact package APIs, documentation, and interface constraints.
- Query tools using `search_web`.
- Distill clean technical briefs with zero prose bloat.
- Once intelligence is gathered, call `handoff_to_architect` to pass findings.""",
    functions=[search_web, handoff_to_architect]
)

architect_agent = Agent(
    name="architect",
    model="qwen3.8-4b",
    temperature=0.2,
    instructions="""You are @architect. Your responsibility is System-2 topological pre-planning and milestone decomposition.
- Use `get_workspace_tree` to orient in large codebases without reading full files.
- Use `query_knowledge_graph` to inspect existing code structures and call graphs in <300 tokens.
- Topologically decompose the project into 3-5 modular milestones.
- Specify exact interfaces, data schemas, and modular insertion anchors.
- NEVER write executable source code files (Zero-Code Invariant).
- Call `handoff_to_coder` to pass the blueprint to @coder for implementation.""",
    functions=[get_workspace_tree, query_knowledge_graph, handoff_to_coder]
)

coder_agent = Agent(
    name="coder",
    model="qwen3.8-4b",
    temperature=0.2,
    instructions="""You are @coder. Your responsibility is surgical, monotonic code synthesis.
- Use `read_file` to inspect existing code slices before modifying.
- Use `write_file` for initial file creation, and `patch_file` for incremental changes.
- Fractal Micro-Patching: Decompose changes into State -> Solvers -> Lifecycle hooks.
- Once code is written, call `handoff_to_tester` to execute the verification suite.""",
    functions=[read_file, write_file, patch_file, handoff_to_tester]
)

tester_agent = Agent(
    name="tester",
    model="qwen3.8-4b",
    temperature=0.1,
    instructions="""You are @tester. Your responsibility is deterministic invariant verification.
- Call `run_test_suite` or `execute_command` to test the codebase.
- If all tests PASS, summarize the verified success.
- If tests FAIL, call `handoff_to_debugger` with the failure output to repair the defect.""",
    functions=[run_test_suite, execute_command, handoff_to_debugger]
)

debugger_agent = Agent(
    name="debugger",
    model="qwen3.8-4b",
    temperature=0.1,
    instructions="""You are @debugger. Your responsibility is systematic root-cause elimination and surgical repair.
- Use `query_knowledge_graph` and `read_file` to locate the failing symbol and scope.
- Use `patch_file` to replace only the defect block.
- NEVER rewrite entire files from scratch.
- Once patched, call `handoff_to_tester` to verify the fix.""",
    functions=[query_knowledge_graph, read_file, patch_file, handoff_to_tester]
)



