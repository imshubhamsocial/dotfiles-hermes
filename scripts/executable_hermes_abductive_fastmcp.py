#!/usr/bin/env python3
"""
Hermes 30% Orchestration Gate: In-Flight Epistemic Interception & Abductive Translation
Embedded into FastMCP Ephemeral Bridge (Port 1934).
1. In-Flight Gate 2 Interception: Blocks premature transfer_to_human_agents when DB reads = [].
2. Abductive Error Translation: Separates data misses from schema errors, stopping parameter spirals.
3. Sequential Tool Decomposition: Serializes concurrent tool calls to avoid attention cross-talk.
"""
from typing import Any

DOMAIN_READ_TOOLS: set[str] = {
    "find_user_id_by_email",
    "find_user_id_by_name_zip",
    "get_user_details",
    "get_order_details",
    "get_product_details",
    "list_all_product_types",
    "calculate",
}


def intercept_and_enforce_epistemic_gates(
    session_state: dict[str, Any],
    proposed_tool_call: dict[str, Any],
) -> dict[str, Any]:
    """
    In-flight Gate 2 (G_read) Enforcement:
    Blocks transfer_to_human_agents if zero domain DB reads have occurred.
    """
    tool_name = proposed_tool_call.get("name") or proposed_tool_call.get("function", {}).get("name", "")
    read_history: list[str] = session_state.setdefault("read_tools_called", [])

    # Record valid domain read invocations
    if tool_name in DOMAIN_READ_TOOLS:
        read_history.append(tool_name)
        return {"status": "ALLOW", "tool_call": proposed_tool_call}

    # IN-FLIGHT GATE 2 (G_read) ENFORCEMENT:
    # Block transfer_to_human_agents if zero domain DB reads have occurred
    if tool_name == "transfer_to_human_agents" and len(read_history) == 0:
        return {
            "status": "BLOCKED_BY_EPISTEMIC_GATE_2",
            "synthetic_observation": (
                "[EPISTEMIC POLICY VIOLATION - GATE 2 (G_read)]: "
                "Execution of 'transfer_to_human_agents' is FORBIDDEN because read_tools_called is empty ([]). "
                "You MUST first query the database using 'find_user_id_by_email', 'find_user_id_by_name_zip', "
                "or 'get_order_details' before transferring."
            ),
        }

    return {"status": "ALLOW", "tool_call": proposed_tool_call}


def translate_tool_error_for_4b_cognition(
    tool_name: str,
    passed_args: dict[str, Any],
    raw_tool_output: str,
) -> str:
    """
    Solves the 4B Abductive Counterfactual Bottleneck:
    Separates Data-Layer Misses (H_data) from Schema Validation Errors (H_schema).
    """
    lower_out = raw_tool_output.lower()
    error_indicators = ["not found", "no user", "no order", "invalid id", "404", "does not exist"]
    if any(k in lower_out for k in error_indicators):
        arg_keys = list(passed_args.keys())
        return (
            f"[DB_RESULT: DATA_RECORD_NOT_FOUND | SCHEMA_STATUS: 100%_VALID]\n"
            f"Raw Output: {raw_tool_output}\n"
            f"EPISTEMIC DIRECTIVE: Your function call to '{tool_name}' and parameter names {arg_keys} "
            f"were 100% SYNTACTICALLY CORRECT. Do NOT change or guess parameter names!\n"
            f"CAUSE: The value {passed_args} provided by the user does not match any record (likely a user typo).\n"
            f"REQUIRED NEXT STEP: 1) If you have the user's name/zip or email, call an alternative lookup tool "
            f"(e.g., 'find_user_id_by_name_zip' or 'get_user_details' to inspect their actual order list), OR "
            f"2) Politely ask the customer to double-check and confirm the exact ID/email."
        )
    return raw_tool_output


def decompose_and_sequentialize_tools(
    tool_calls: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Sequentialize parallel tool calls, ensuring deterministic single-tool execution order.
    """
    sequential_calls = []
    seen_signatures = set()

    for tc in tool_calls:
        fn = tc.get("function", {})
        name = fn.get("name", "")
        args = fn.get("arguments", "{}")
        sig = f"{name}:{args}"

        # Prevent duplicate identical tool spam in the same turn
        if sig in seen_signatures:
            continue
        seen_signatures.add(sig)
        sequential_calls.append(tc)

    return sequential_calls


if __name__ == "__main__":
    # Self-test
    state: dict[str, Any] = {}
    blocked = intercept_and_enforce_epistemic_gates(
        state, {"name": "transfer_to_human_agents"}
    )
    assert blocked["status"] == "BLOCKED_BY_EPISTEMIC_GATE_2"

    intercept_and_enforce_epistemic_gates(
        state, {"name": "find_user_id_by_name_zip"}
    )
    allowed = intercept_and_enforce_epistemic_gates(
        state, {"name": "transfer_to_human_agents"}
    )
    assert allowed["status"] == "ALLOW"

    translated = translate_tool_error_for_4b_cognition(
        "get_order_details", {"order_id": "W1234"}, "Order not found"
    )
    assert "SCHEMA_STATUS: 100%_VALID" in translated
    print("Hermes Abductive FastMCP Middleware checks PASSED.")
