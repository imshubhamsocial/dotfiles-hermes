# Phase 36 Specification: OpenViking L0/L1/L2 Procedural Ingestion & Epistemic Retrieval

## 1. Objective
Compile `domain_db_tool_precedence/SKILL.md` into the OpenViking hierarchical context database on Port 1933 (`CUDA_VISIBLE_DEVICES=""`), generating L0 (`.abstract`), L1 (`.overview`), and L2 (full document) nodes under `viking://user/hermes/memories/skills/`.

## 2. Invariants
- OpenViking daemon on Port 1933 must be active and report healthy on `curl http://127.0.0.1:1933/health`.
- GPU VRAM consumption of OpenViking must be exactly 0.0 MiB.
- Epistemic retrieval via `search(mode="context")` must resolve the L0/L1 context block under 10ms.
- Golden clean snapshot `.openviking/data.golden_clean` must be synchronized.
