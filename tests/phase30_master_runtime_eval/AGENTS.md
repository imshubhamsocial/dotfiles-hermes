# AGENTS.md — Phase 30 Production Omniscient Master Runtime Evaluation

> **Project**: Hermes Agent OS — Phase 30 Evaluation Harness  
> **Literature**: NVIDIA *LoGRA* (arXiv:2610.06647), Frobenius-Normalized *NoRA* (arXiv:2608.31036), ADR-2  
> **Target Scenario**: `scenario/live_omniscient.py` (Live NVML VRAM telemetry, Port 8138 health, state.db sessions)  
> **Verification Gate**: `pytest scenario/ -q`

---

## 1. Scope & Verification Contract
- **Target Module**: `scenario/live_omniscient.py`
- **Test Module**: `scenario/test_live_omniscient.py`
- **Verification Command**: `pytest scenario/ -q`
