# Architectural Rule: Runtime Tool Dispatch Optimization

## 💡 Principle
All tool dispatch mechanisms in Hermes Agent must transition from sequential, unbatched processing to concurrent or batched execution when multiple independent tool requests are presented.

## 🔬 Telemetry Requirement
Any change affecting dispatch latency must first be validated via telemetry analysis of `telemetry/traces.jsonl`. A baseline measurement is required to define the failure signature (e.g., 0.60s latency for 5 requests).

## 🛠 Implementation Pattern: Concurrent Dispatch
When tool requests are independent:
1.  **Identify the Bottleneck:** Locate the sequential loop (`for req in requests`) in the dispatch function.
2.  **Apply Concurrency:** Utilize standard concurrency patterns (e.g., Python's `concurrent.futures.ThreadPoolExecutor`) to submit requests to a pool and await results concurrently.
3.  **Verification:** Run performance-critical tests (e.g., `test_dispatch_performance`) to verify the execution time meets the target latency (e.g., < 0.05s).

## 🛑 Failure Mode
Sequential processing violates the core performance invariant, leading to unacceptable execution times and agent inefficiency. Sequential serialization is a bottleneck, not a feature.

## 🔗 Related Artifact
*   Design Specification: `specs/runtime_optimization.md`
*   Test Suite: `tests/test_runtime_engine.py`