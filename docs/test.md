# Benchmark Methodology & Evaluation Guide

This guide outlines how the Hermes harness, internal subsystems, and skills are benchmarked using modern industry evaluation standards from Google DeepMind, NVIDIA, Anthropic, and Nous Research.

---

## 1. Core Benchmarking Pillars

```
┌─────────────────────────┐     ┌─────────────────────────┐     ┌─────────────────────────┐
│   Hardware & Latency    │     │   Agentic Correctness   │     │    Skill Evolution      │
│ (NVIDIA NVML / TTFT /   │ ──► │  (Google Env-Harness /  │ ──► │  (GEPA-Lite Pareto /    │
│  KV-Cache Slot Re-use)  │     │   Quorum Audit Gates)   │     │   Regression Sieves)    │
└─────────────────────────┘     └─────────────────────────┘     └─────────────────────────┘
```

---

## 2. Subsystem Benchmarks

### A. Hardware & VRAM Boundary Benchmarking (NVIDIA Standard)
* **Metric**: Maximum VRAM allocation during multi-turn generation.
* **Ceiling Invariant**: $\le 4,812\text{ MiB}$ physical limit on NVIDIA RTX 3050 (6GB).
* **Measurement Tool**: Direct NVML querying via `nvidia-ml-py` (`nvmlDeviceGetMemoryInfo`).
* **Validation Command**:
  ```bash
  python3.13 tests/runners/run_final_integration_exam.py
  ```

### B. KV-Cache & Prefix Cache Hit Ratio (llama.cpp / StillWarm Standard)
* **Metric**: Prefix token cache hit percentage across conversational turns.
* **Target Invariant**: Mean Hit Ratio $\ge 95\%$ across consecutive turns.
* **Benchmark Test**: `test_roadmap4_u45_prompt_slotting_and_compactor.py`.

### C. Agentic Integrity & Anti-Hallucination (Google Env-Harness Standard)
* **Metric**: Generalization Gap ($\Delta_{\text{gen}} \le 0.15$) and strict AST validity.
* **Gates**:
  1. **AST Syntax Gate**: Code mutations must produce valid Tree-Sitter / Python AST parse trees.
  2. **Draft Detective Fact-Checking**: Verification of all claimed file paths and symbol names against the real workspace.
* **Validation Command**:
  ```bash
  python3.13 .hermes/bin/executable_verify_harness_integrity.py
  ```

### D. Multi-Agent Consensus (Quorum Benchmark)
* **Metric**: Independent auditor agreement score before commit.
* **Standard**: Cross-model audit gate with structural separation (`author != auditor`).
* **Threshold**: Minimum fitness score $\ge 0.85$.
* **Benchmark Test**: `tests/test_quorum_and_gepa.py`.

### E. Skill & Prompt Optimization (GEPA-Lite Pareto Benchmark)
* **Metric**: Multi-objective Pareto frontier over $(\text{Task Accuracy} \uparrow, \text{Token Cost} \downarrow)$.
* **Evaluation Cycle**: Offline nightly batch evaluation over trajectory streams.
* **Benchmark Test**: `tests/harness_contracts/test_roadmap4_u59_skill_evolution.py`.

---

## 3. Quick Benchmark Commands

| Scope | Command | Expected Output |
|---|---|---|
| **All Contract Spikes** | `pytest tests/harness_contracts/ -q` | `602 passed` |
| **Complete Domain Suite** | `pytest tests/ -q` | `620 passed` |
| **Harness Capability Audit** | `python3.13 .hermes/bin/executable_verify_harness_integrity.py` | `APPROVED: All capabilities verified` |
| **Live Integration Exam** | `python3.13 tests/runners/run_final_integration_exam.py` | `🟢 FINAL INTEGRATION EXAM PASSED` |
| **Plugin Contract Doctor** | `hermes plugins doctor <plugin-name>` | `OK: runtime discovery passed` |
