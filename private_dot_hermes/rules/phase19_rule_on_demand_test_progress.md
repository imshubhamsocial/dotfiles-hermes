---
phase: "Phase 19"
authority: "Golden Law 13: On-Demand Test Progress Monitoring & Zero Polling Invariant"
testbed: "tests/phase19_looped_attractor_eval/"
status: "Operational & Certified"
---

# Behavioral Invariant: On-Demand Test Progress Monitoring (Golden Law 13)

> **Authority**: System-2 Cognitive Discipline & User Directives  
> **Target Scope**: All AI Coding Agents, Background Testbeds, and Verification Tasks

---

## 1. Zero Polling Invariant
* AI agents operating within Hermes Agent OS must **never poll, spin, or periodically sleep-check running tests, daemon tasks, or background evaluations in an automated loop**.
* Setting artificial sleep loops or querying inference server slot progress (`curl /slots`) without an explicit user prompt wastes GPU memory bus bandwidth, incurs CPU context-switching overhead, and clutters the conversation trajectory.

## 2. On-Demand Inspection Protocol
* Progress checks and test status evaluations must be performed strictly **on demand**:
  1. When an explicit user request specifically asks for current progress, metrics, or logs.
  2. When an asynchronous notification event (e.g., systemd unit exit, background task completion receipt) is received.
* When a testbed or evaluation runs in the background or in a persistent Konsole window (`--hold`), allow it to run unhindered to completion. Do not generate intermediate status polls.
