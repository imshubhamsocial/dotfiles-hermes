---
name: runtime-dispatch-optimization
description: Optimize runtime tool dispatch batching.
version: 1.0.0
author: Hermes Agent
license: MIT
---

## Overview
This skill guides the process of transforming sequential tool request dispatch mechanisms into concurrent, batched execution models to eliminate serialization latency.

## Core Procedure
1.  **Diagnosis:** Analyze telemetry (`telemetry/traces.jsonl`) for execution time bottlenecks (e.g., `test_dispatch_performance` failure signature).
2.  **Spec Definition:** Document the required performance threshold and architectural shift in `specs/runtime_optimization.md`.
3.  **Implementation:** Refactor the `dispatch_tool_requests` function (typically in `src/runtime_engine.py`) by replacing the sequential loop with a concurrent executor (e.g., `concurrent.futures.ThreadPoolExecutor`).
4.  **Verification:** Use the `verification-loop` and run full test suite (`./run_tests.sh`) to ensure the fix passes and meets the performance goal.
5.  **Record:** Document the pattern in `rule_runtime_tool_dispatch_optimization.md` and commit the changes.

## References
*   `specs/runtime_optimization.md`: Defines goals and metrics.
*   `rule_runtime_tool_dispatch_optimization.md`: Records the architectural invariant for future reference.
*   `src/runtime_engine.py`: The target of implementation changes.
---