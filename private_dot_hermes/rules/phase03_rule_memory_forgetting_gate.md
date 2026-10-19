---
phase: "Phase 03"
authority: "Dynamic Memory Forgetting Gate & Capacity Ceiling"
testbed: "tests/memory_eval/"
status: "Operational & Certified"
---

# Architectural Invariant: Memory Forgetting Gate

This rule enforces the absolute capacity constraint for persistent, durable memory storage, maintaining system integrity and performance predictability.

## ⚙️ Core Invariant
The `memory` persistent memory store is strictly capped at **2,200 characters**. This limit is non-negotiable and is enforced atomically by the MemoryStore layer.

## 🚨 Protocol: Overflow and Refusal
1.  **Detection:** When a proposed `viking_remember` or similar write operation (e.g., `memory.operations`) would cause the total memory content to exceed 2,200 characters, the MemoryStore immediately detects and refuses the write.
2.  **Refusal Protocol:** The write operation fails gracefully, triggering a mandatory consolidation workflow. No data is lost; the operation simply does not complete.

## 🧹 Consolidation Workflow (Memory Forgetting Gate)
When an overflow is detected, the system *must* initiate a consolidation process:
1.  **Identify Candidates:** The system must prioritize stale or low-signal entries.
2.  **Trigger Action:** The developer or agent must explicitly define a `viking_forget` operation (or a batch `memory.operations` list with `action: remove`) targeting the least essential information (e.g., old, repeated session facts, or low-signal notes).
3.  **Execute and Verify:** The memory write/update sequence must then be re-attempted against the reduced total size.

## 🛡️ Summary of Constraint
- **Limit:** 2,200 characters.
- **Failure Mode:** Atomic refusal upon overflow.
- **Mitigation:** Mandatory preceding consolidation step (forgetting/summarization).

This gate ensures that memory remains a bounded, predictable resource, preventing runaway growth and maintaining search efficiency.