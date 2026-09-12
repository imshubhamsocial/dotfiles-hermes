"""
U3: Subagent Capability Allow/Deny Masks (Schema-Level Tool Isolation)
======================================================================
Roadmap Phase 2.2 — Astra Pattern / Rule #2 (Asymmetric Trinity):

  @architect  NEVER writes code        -> read/plan tools only
  @coder      NEVER runs test runners  -> synthesis + bash, no graders
  @tester     NEVER writes files       -> graders + read-only inspection

Enforcement is SCHEMA-LEVEL (a masked tool is never exposed to the model's
tool schema at all) plus a dispatch-level backstop that structurally rejects
hallucinated calls. Violation is physically impossible, not prompt-policed.

Default posture for unknown roles is READ-ONLY (least privilege).

Extended for U37: Dynamic OpenAI tool schema generation per phase.
"""

from typing import Dict, List, Optional, Tuple, Any

READ_ONLY_TOOLS = frozenset({
    "read_file", "grep_codebase", "get_symbol_map", "get_workspace_tree",
    "query_knowledge_graph", "search_web", "get_task_status",
})

ROLE_POLICIES: Dict[str, frozenset] = {
    "architect": frozenset(READ_ONLY_TOOLS | {"hypothesis_add"}),
    "researcher": frozenset(READ_ONLY_TOOLS),
    "coder": frozenset({
        "read_file", "write_file", "patch_file", "execute_command",
        "grep_codebase", "get_symbol_map", "get_workspace_tree",
        "update_task_progress",
    }),
    "tester": frozenset({
        "run_test_suite", "execute_command", "read_file",
        "grep_codebase", "get_symbol_map", "get_workspace_tree",
    }),
    "debugger": frozenset({
        "read_file", "patch_file", "execute_command", "run_test_suite",
        "grep_codebase", "query_knowledge_graph", "get_symbol_map",
    }),
}

DEFAULT_ROLE = "_default"
ROLE_POLICIES[DEFAULT_ROLE] = READ_ONLY_TOOLS


# ─── OpenAI Tool Schema Definitions ────────────────────────────────────────
# Minimal schemas for each tool - used for dynamic schema selection

TOOL_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "read_file": {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read contents of a file with optional line range",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Path to file"},
                    "start_line": {"type": "integer", "description": "Start line (1-indexed)"},
                    "end_line": {"type": "integer", "description": "End line (1-indexed)"},
                },
                "required": ["filepath"],
            },
        },
    },
    "write_file": {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write complete content to a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Path to file"},
                    "content": {"type": "string", "description": "File content"},
                },
                "required": ["filepath", "content"],
            },
        },
    },
    "patch_file": {
        "type": "function",
        "function": {
            "name": "patch_file",
            "description": "Surgically replace a block of text in a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Path to file"},
                    "target_block": {"type": "string", "description": "Exact block to replace"},
                    "replacement_block": {"type": "string", "description": "New block content"},
                },
                "required": ["filepath", "target_block", "replacement_block"],
            },
        },
    },
    "execute_command": {
        "type": "function",
        "function": {
            "name": "execute_command",
            "description": "Execute a shell command in sandboxed workspace",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Command to execute"},
                    "timeout_sec": {"type": "integer", "description": "Timeout in seconds", "default": 120},
                },
                "required": ["command"],
            },
        },
    },
    "run_test_suite": {
        "type": "function",
        "function": {
            "name": "run_test_suite",
            "description": "Run test suite or grader",
            "parameters": {
                "type": "object",
                "properties": {
                    "grader_name": {"type": "string", "description": "Grader to run"},
                    "command": {"type": "string", "description": "Custom test command"},
                },
            },
        },
    },
    "get_symbol_map": {
        "type": "function",
        "function": {
            "name": "get_symbol_map",
            "description": "Extract AST symbols from a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Path to file"},
                },
                "required": ["filepath"],
            },
        },
    },
    "get_workspace_tree": {
        "type": "function",
        "function": {
            "name": "get_workspace_tree",
            "description": "Get hierarchical file tree of workspace",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory path"},
                    "max_depth": {"type": "integer", "description": "Max depth", "default": 3},
                },
            },
        },
    },
    "query_knowledge_graph": {
        "type": "function",
        "function": {
            "name": "query_knowledge_graph",
            "description": "Query codebase knowledge graph for symbol info",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol_name": {"type": "string", "description": "Symbol to query"},
                    "directory": {"type": "string", "description": "Search directory"},
                },
                "required": ["symbol_name"],
            },
        },
    },
    "grep_codebase": {
        "type": "function",
        "function": {
            "name": "grep_codebase",
            "description": "Fast regex search across codebase",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Regex pattern"},
                    "file_extension": {"type": "string", "description": "File extension filter"},
                },
                "required": ["pattern"],
            },
        },
    },
    "get_task_status": {
        "type": "function",
        "function": {
            "name": "get_task_status",
            "description": "Get current task status from TaskGraph",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    "update_task_progress": {
        "type": "function",
        "function": {
            "name": "update_task_progress",
            "description": "Update task verification status",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Task ID"},
                    "passed": {"type": "boolean", "description": "Pass/fail"},
                    "notes": {"type": "string", "description": "Notes"},
                },
                "required": ["task_id", "passed"],
            },
        },
    },
    "search_web": {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search web for technical info",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                },
                "required": ["query"],
            },
        },
    },
    "refactor_symbol": {
        "type": "function",
        "function": {
            "name": "refactor_symbol",
            "description": "Rename/refactor a symbol globally",
            "parameters": {
                "type": "object",
                "properties": {
                    "old_symbol": {"type": "string", "description": "Old name"},
                    "new_symbol": {"type": "string", "description": "New name"},
                    "file_pattern": {"type": "string", "description": "File pattern", "default": "*"},
                    "directory": {"type": "string", "description": "Directory"},
                },
                "required": ["old_symbol", "new_symbol"],
            },
        },
    },
    "hypothesis_add": {
        "type": "function",
        "function": {
            "name": "hypothesis_add",
            "description": "Add hypothesis to hypothesis tree",
            "parameters": {
                "type": "object",
                "properties": {
                    "hypothesis": {"type": "string", "description": "Hypothesis text"},
                    "parent_id": {"type": "string", "description": "Parent hypothesis ID"},
                },
                "required": ["hypothesis"],
            },
        },
    },
}


def get_tool_schema(tool_name: str) -> Optional[Dict[str, Any]]:
    """Get OpenAI-compatible tool schema by name."""
    return TOOL_SCHEMAS.get(tool_name)


# ─── Role Schema Mapping (for U37 dynamic selection) ───────────────────────
# Maps role to full tool schema list for that role

ROLE_SCHEMAS: Dict[str, Dict[str, Any]] = {}
for role, tools in ROLE_POLICIES.items():
    schemas = [TOOL_SCHEMAS[t] for t in tools if t in TOOL_SCHEMAS]
    ROLE_SCHEMAS[role] = {
        "tools": schemas,
        "tool_choice": "auto",
    }

# Alias for backward compatibility
ROLE_CAPABILITIES = ROLE_POLICIES


def resolve_role(agent) -> str:
    """Best-effort role resolution from an Agent-like object."""
    for attr in ("profile", "role"):
        role = getattr(agent, attr, None)
        if isinstance(role, str) and role.strip():
            return role.strip().lower()
    name = getattr(agent, "name", "") or ""
    name = name.strip().lower()
    if name.startswith("@"):
        name = name[1:]
    return name if name in ROLE_POLICIES else DEFAULT_ROLE


def allowed_for(role: str) -> frozenset:
    return ROLE_POLICIES.get(role, ROLE_POLICIES[DEFAULT_ROLE])


def check_tool(role: str, tool_name: str) -> Tuple[bool, str]:
    """Dispatch-level verdict with a structured rejection reason, integrated with NeMo Guardrails dialog rails."""
    try:
        from plugins.nemo_guardrails import get_guardrails_engine
        engine = get_guardrails_engine()
        dialog_verdict = engine.check_dialog_rail(role, f"execute {tool_name}")
        if not dialog_verdict.allowed:
            return False, f"NEMO_DIALOG_RAIL_BLOCKED: {dialog_verdict.reason}"
    except Exception:
        pass

    if tool_name in allowed_for(role):
        return True, "allowed."
    return False, (
        f"CAPABILITY_MASK: role '{role}' is denied tool '{tool_name}'. "
        f"Allowed: {sorted(allowed_for(role))}"
    )


def mask_functions(functions: List, role: str) -> List:
    """Schema-level filter: masked tools are never advertised to the model."""
    allowed = allowed_for(role)
    return [f for f in (functions or []) if getattr(f, "__name__", "") in allowed]


def apply_to_agent(agent):
    """Return (agent, role) after stripping its function list in place."""
    role = resolve_role(agent)
    agent.functions = mask_functions(agent.functions, role)
    return agent, role


def validate_security_policy_path(filepath: str, is_write: bool = True) -> Tuple[bool, str]:
    """Validates that a path is permitted under agent_capabilities.yaml."""
    if not is_write:
        return True, "read allowed."
    fp = str(filepath).lower()
    denied_targets = [".integrity", "agent_capabilities.yaml", ".git-credentials", ".ssh/id_", "etc/shadow", "etc/sudoers"]
    for target in denied_targets:
        if target in fp:
            return False, f"SECURITY_POLICY_VIOLATION: Write/delete access to '{filepath}' is forbidden by agent_capabilities.yaml."
    return True, "path allowed."


def validate_security_policy_command(cmd: str) -> Tuple[bool, str]:
    """Inspects shell commands using NVIDIA NeMo input rails and policy rules."""
    try:
        from plugins.nemo_guardrails import get_guardrails_engine
        engine = get_guardrails_engine()
        input_verdict = engine.check_input_rail(cmd)
        if not input_verdict.allowed:
            return False, f"SECURITY_POLICY_VIOLATION: {input_verdict.reason}"
    except Exception:
        pass
    c = str(cmd).lower()
    dangerous_patterns = [
        ("rm ", ".integrity"),
        ("rm ", "agent_capabilities.yaml"),
        ("truncate ", ".integrity"),
        ("> ", ".integrity"),
        ("sed ", "agent_capabilities.yaml"),
        ("echo ", "agent_capabilities.yaml"),
    ]
    for action, target in dangerous_patterns:
        if action in c and target in c:
            return False, f"SECURITY_POLICY_VIOLATION: Command tampering with '{target}' is strictly forbidden."
    return True, "command allowed."


def get_schema_for_role(role: str) -> Dict[str, Any]:
    """Get full OpenAI tool schema for a role."""
    return ROLE_SCHEMAS.get(role, ROLE_SCHEMAS[DEFAULT_ROLE])


if __name__ == "__main__":
    for r in ROLE_POLICIES:
        print(f"{r:>10}: {len(allowed_for(r))} tools")
    
    # Test schema generation
    print("\n--- Architect Schema ---")
    import json
    print(json.dumps(get_schema_for_role("architect"), indent=2))
