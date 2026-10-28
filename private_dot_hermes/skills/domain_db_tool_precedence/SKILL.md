---
name: domain_db_tool_precedence
version: 1.0.0
category: procedural_tool_orchestration
triggers:
  - multi-turn database lookup and state mutation workflows
  - identity verification with partial or secondary user credentials
  - policy-governed escalation vs. autonomous resolution decisions
openviking_uri: viking://user/hermes/memories/skills/domain_db_tool_precedence.md
l0_abstract: Enforces strict read-tool exhaustion and secondary-key lookup precedence prior to invoking terminal escalation or human transfer actions.
---

# Procedural Skill: Domain Database Lookup & Escalation Precedence

## 1. Core Epistemic Principle (The Exhaustion Invariant)
In any tool-augmented environment governed by domain policies, a terminal escalation action (such as transferring to a human operator or aborting a workflow) is an irreversible, last-resort transition. The agent must never escalate due to a missing primary identifier if the active tool schema provides an alternative lookup function whose required parameters can be satisfied by secondary identifiers already present in the dialogue or obtainable from the user.

## 2. Pre-Escalation Decision Protocol (System-2 Deliberation Checklist)
Before emitting any terminal transfer action or concluding that authentication cannot proceed, the agent must execute the following 4-step verification sequence inside `<deliberation>`:

- Step 1 — Inventory Active Read Tools: Enumerate all non-mutating lookup and query functions declared in the current tool specification and list their exact required input parameter signatures.
- Step 2 — Map Known Entity Attributes: Extract all entity attributes provided across the conversation history (full name, first and last name components, postal or ZIP code, phone number, account handle, or transaction reference).
- Step 3 — Evaluate Secondary Key Satisfiability: If the user cannot provide Primary Key $K_1$ (such as an email address) but has provided Secondary Key Tuple $K_2$ (such as first name, last name, and postal code), and a lookup tool $T_{\text{lookup}}(K_2)$ exists in the active schema, the agent MUST invoke $T_{\text{lookup}}(K_2)$ immediately. If one component of $K_2$ is still missing, prompt the user specifically for that missing attribute rather than escalating.
- Step 4 — Sequential Read-Verify-Mutate Chaining: Once $T_{\text{lookup}}$ resolves the canonical entity identifier (such as `user_id` or `account_id`), chain immediately into the dependent inspection tool (such as retrieving user details or transaction records) to inspect target item states and policy preconditions before executing any state-mutating write tool.

## 3. Valid vs. Invalid Escalation Boundaries

| Scenario Condition | Required Agent Action | Rationale |
| :--- | :--- | :--- |
| Primary identifier unavailable, but secondary lookup tool parameters are satisfied by user input | Invoke Secondary Lookup Tool -> Chain into Record Inspection -> Execute Authorized Mutation | Authentication is fully satisfiable via secondary relational keys. |
| User requests an action that explicitly violates an immutable domain policy constraint (e.g., prohibited refund destination or unauthorized state transition) | Invoke Terminal Escalation / Human Transfer | Policy explicitly forbids autonomous execution of the requested mutation. |
| All declared lookup tools require parameters that the user explicitly confirms are unavailable | Invoke Terminal Escalation / Human Transfer | Lookup tool space is provably exhausted. |
