---
name: dangerous-command-verifier
description: Stops destructive commands for explicit verification.
---
# ⚠️ Dangerous Command Verification Protocol

This skill enforces a mandatory safety gate for any destructive, irreversible, or system-critical operation (e.g., `rm -rf`, `reboot`, `format`).

## Protocol Execution Steps:

1.  **Identification (The Trigger):** When a command containing high-risk keywords (e.g., "rm", "delete", "wipe", "reboot", "format", "kill -9") is detected, execution must be paused.
2.  **Risk Assessment:** The agent must classify the command's risk level (Low, Medium, Catastrophic).
    *   *Catastrophic:* Data loss, system failure. (Requires explicit user confirmation/query).
    *   *High:* Significant change to code/config. (Requires internal review and `clarify` to validate scope).
3.  **Mandatory Query Generation:** For Catastrophic risks, the agent must generate a question to the user that explicitly states the consequences of the command, requiring an affirmative response before proceeding.
    *   Example: "WARNING: The command `rm -rf ~/.hermes` will irrevocably delete all project data. Do you confirm this action?"
4.  **Execution Gate:** Only upon successful validation (explicit user confirmation, successful internal risk mitigation) is the command executed.
5.  **Post-Mortem Logging:** After any dangerous operation, record the action in the session ledger to maintain an audit trail.

## Guardrail Interception Logic (The NeMo Principle):
The core principle is: Never execute a destructive command without an explicit, verified consent boundary. The agent must treat the user's request as a proposal requiring verification against the system's core invariants.