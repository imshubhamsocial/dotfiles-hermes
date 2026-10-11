# Architectural Invariant: Research 2.0 Integration Gauntlet

This document certifies that the following substrates and operational invariants of the Hermes Agent system have been verified as functioning autonomously and natively, without requiring bespoke scripts or external wrappers.

## Substrates Verified:
1. **OpenViking & OpenJev MCP Registration**: Confirms robust integration of the OpenViking knowledge base and the OpenJev Machine Code Platform (MCP) for durable knowledge indexing and advanced decision-making.
2. **Memory Forgetting Gate**: Verifies the integrity of the memory system, ensuring persistent facts (e.g., `MEMORY.md`) remain under the specified character budget constraint (<= 2200 chars).
3. **Two-Tier Skill Catalog**: Confirms a scalable, modular skill architecture, demonstrated by the accessibility of core diagnostic skills like `diagnosing-bugs`.
4. **Invariant Rule Distillation**: Confirms the system's ability to distill complex, multi-step workflows into declarative, durable architectural rules.
5. **Jev Decision Gate Execution**: Verifies the low-latency evaluation of test hypotheses against the OpenJev MCP, maintaining performance metrics (< 300ms).
6. **VRAM Health**: Confirms adequate and correctly managed GPU resource allocation, maintaining high-performance inference capabilities.
7. **Substrate Purity**: Validates that the core `.hermes` directory contains zero bespoke Python scripts, relying only on upstream, native mechanisms (e.g., `mcp_openjev.py`).

## Invariant Declaration:
The Hermes Agent operates on a set of natively integrated, self-validating components. These components enforce strict boundaries (e.g., OpenViking, OpenJev, Memory Gate) and rely exclusively on upstream, standardized APIs, ensuring robustness, maintainability, and zero dependency on custom, ephemeral scripts.

**Status:** Research 2.0 Substrates are verified and fully integrated.