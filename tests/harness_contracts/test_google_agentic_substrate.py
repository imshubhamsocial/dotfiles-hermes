"""
Contract Test Suite: Google Agentic Substrate & Subagent Delegation Engine
==========================================================================
Verifies Google-Standard Tool Calling Schemas and Antigravity Subagent Engine.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from hermes_core.google_agentic_substrate import (
    GoogleToolSchemaRegistry,
    GoogleSubagentDelegationEngine,
    SubagentSpec,
    create_google_subagent_engine,
)


def test_google_tool_schemas_integrity():
    schemas = GoogleToolSchemaRegistry.get_all_schemas()
    assert len(schemas) == 13

    schema_map = {s["name"]: s for s in schemas}
    for req_tool in ["run_command", "replace_file_content", "invoke_subagent", "send_message", "manage_subagents"]:
        assert req_tool in schema_map
        s = schema_map[req_tool]
        assert "description" in s
        assert "parameters" in s
        props = s["parameters"]["properties"]
        assert "toolAction" in props
        assert "toolSummary" in props
        assert "toolAction" in s["parameters"]["required"]
        assert "toolSummary" in s["parameters"]["required"]


def test_google_subagent_delegation_engine():
    with tempfile.TemporaryDirectory() as td:
        engine = create_google_subagent_engine(scratchpad_root=Path(td))

        # 1. Invoke Subagents
        spawned = engine.invoke_subagents([
            {
                "TypeName": "architect",
                "Role": "System-2 Pre-Planner",
                "Prompt": "Formulate DAG specification for Three.js WebGL simulation",
                "Model": "pro",
                "Workspace": "branch",
            },
            {
                "TypeName": "coder",
                "Role": "Modular Coder",
                "Prompt": "Synthesize ESM module",
                "Model": "flash",
                "Workspace": "branch",
            },
        ])

        assert len(spawned) == 2
        conv_id_1 = spawned[0]["conversationId"]
        conv_id_2 = spawned[1]["conversationId"]

        # 2. Check Branched Workspace Directories
        assert (Path(td) / conv_id_1).exists()
        assert (Path(td) / conv_id_2).exists()

        # 3. Test Agent-to-Agent Messaging
        sent = engine.send_message(conv_id_1, "Architect spec received. Handoff to coder.")
        assert sent is True
        assert engine.subagents[conv_id_1].inbox[0] == "Architect spec received. Handoff to coder."

        # 4. Test Subagent Listing
        listing = engine.manage_subagents("list")
        assert listing["active_count"] == 2
        assert len(listing["subagents"]) == 2

        # 5. Test Targeted Kill
        kill_res = engine.manage_subagents("kill", [conv_id_1])
        assert conv_id_1 in kill_res["killed"]
        assert engine.subagents[conv_id_1].state == "killed"

        # 6. Test Kill All
        kill_all_res = engine.manage_subagents("kill_all")
        assert kill_all_res["killed_count"] == 2
        assert engine.subagents[conv_id_2].state == "killed"
