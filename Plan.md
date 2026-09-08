# Master Execution Plan: Domain 7 Finalization & Certification

> **Status**: Active Living Execution Plan  
> **Target**: 100% Zero-Bloat, Native Upstream Packages with Local Hardware Calibrations, Clean Test Isolation  
> **Hardware Boundary**: NVIDIA RTX 3050 Laptop (6GB VRAM, ≤ 4,812 MiB limit), llama-server port 8138  

---

## 4-Step Execution Matrix

| Step | Scope & Description | Status | Verification Evidence |
| :--- | :--- | :---: | :--- |
| **Step 1** | **Clean Up Root `tests/` Directory (Benchmark Isolation)**<br>• Remove duplicate domain tests from root `tests/`<br>• Delete orphan `test_math_engine.py`<br>• Update `tests/conftest.py` sys.path<br>• Wire `Makefile` `test-internal` to `.hermes/tests/` | ✅ **DONE** | 184 internal tests pass in `.hermes/tests/`<br>602 contract tests pass in `tests/harness_contracts/` |
| **Step 2** | **Harmonize Package Manifests (`pyproject.toml`, `setup.sh`, `Makefile`)**<br>• Formally declare `google-adk`, `nemoguardrails`, `openlit`, `crawl4ai`<br>• Remove deprecated `duckduckgo-search`<br>• Omit rejected `langgraph` framework<br>• Commit all package pins to Chezmoi | ✅ **DONE** | `pyproject.toml` updated<br>`Makefile` `py-deps` updated<br>Committed in Chezmoi (`03827b6`) |
| **Step 3** | **Retire Redundant Custom Substrates (`google_agentic_substrate.py`)**<br>• Rationalize `google_agentic_substrate.py` (~444 LOC)<br>• Formally deprecate in favor of native `google-adk` (HermesADKCustomAgent & DomainFleetManager)<br>• Retained strictly as a lightweight compatibility shim for U80 contract tests | ✅ **DONE** | Deprecation notice added<br>U80 contract test passing (602/602 green)<br>Committed in Chezmoi (`1bcd2fb`) |
| **Step 4** | **Master Certification & NVML Hardware Audit**<br>• Run `.hermes/bin/verify_harness_integrity.py` (30/30 capabilities)<br>• Run `make doctor` (audit 9 plugins & health contracts)<br>• Run live `run_final_integration_exam.py` vs champion model<br>• Final Chezmoi sync & git commit | ✅ **DONE** | • `run_final_integration_exam.py`: ALL EXAMS PASSED (E2E, U6, U7, U8, U17, U18, VRAM)<br>• `verify_harness_integrity.py`: APPROVED (all capabilities + contract spikes pass)<br>• `make doctor`: ALL 9 PLUGINS PASS (OK)<br>• `make test`: 786/786 tests pass (100% green)<br>• Chezmoi: 100% synced (`a16c6c9`) |

---

## Live End-to-End Verification Evidence

```json
{
  "timestamp_utc": "2026-09-08T21:21:59Z",
  "all_passed": true,
  "champion": "gemma-4-E4B-it-Q4_K_M + mtp-gemma-4-E4B-it-Q4_0 @ 8138",
  "exams": {
    "exam_e2e_engine_u6_chain": {
      "passed": true,
      "wall_seconds": 6.2,
      "events": 7,
      "chain": "chain intact: 7 events",
      "dialect_complete": ["gate_check", "response", "tool_call", "tool_result", "turn_end", "turn_start"],
      "artifact_written": true
    },
    "exam_u7_replay_match": {
      "passed": true,
      "replayed_steps": 1,
      "drifted_steps": 0
    },
    "exam_u17_supervisor_quiet": {
      "passed": true,
      "interventions": []
    },
    "exam_u18_commit_gate": {
      "passed": true,
      "clean_variant_committed": true,
      "bloat_blocked_reason": "token bloat blocked (128 > 33)"
    },
    "exam_u8_prefix_cache": {
      "passed": true,
      "mean_hit_ratio": 1.0,
      "turns_sampled": 11,
      "trap1_lint_registry_armed": true
    },
    "exam_vram_guard": {
      "passed": true,
      "start_mib": 4281,
      "end_mib": 4301,
      "budget_mib": 4812
    }
  }
}
```

## Non-Negotiable Invariant Rules
1. **Never Deviate**: Work strictly in the numbered order: Step 1 ➔ Step 2 ➔ Step 3 ➔ Step 4.
2. **Law #8 Compliance**: Upstream official tools first (`google-adk`, `nemoguardrails`, `fastmcp`, `crawl4ai`). Never write custom framework boilerplate.
3. **Hardware Ceiling**: GPU VRAM allocation across `llama-server` and workers must never exceed 4,812 MiB.
4. **Test Integrity**: Every step must preserve 100% green pass rate across both `.hermes/tests/` and `tests/harness_contracts/`.
