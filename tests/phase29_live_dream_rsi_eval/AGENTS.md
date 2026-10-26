# AGENTS.md — Phase 29 Live state.db Dream-RSI 2.0 & MASS Evaluation

> **Project**: Hermes Agent OS — Phase 29 Evaluation Harness  
> **Literature**: Google DeepMind / UMD *Dream-RSI* (arXiv:2609.14858), Sakana AI *MASS* (arXiv:2610.12176), Google *RRSI* (arXiv:2609.24972)  
> **Target Scenario**: `scenario/live_sync.py` (Live state.db session ingestion, replay tree dictionary construction)  
> **Verification Gate**: `pytest scenario/ -q`

---

## 1. Scope & Verification Contract
- **Target Module**: `scenario/live_sync.py`
- **Test Module**: `scenario/test_live_sync.py`
- **Verification Command**: `pytest scenario/ -q`
