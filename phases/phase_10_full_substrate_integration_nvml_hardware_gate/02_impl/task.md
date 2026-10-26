# Phase 10: Full Substrate Integration & NVML Hardware Gate — Implementation Checklist

> **Phase Directory**: `phase_10_full_substrate_integration_nvml_hardware_gate`  
> **Status**: Stage `02_impl` execution complete  

---

## 1. Targeted Symbols & Code Modules
- Target File(s):
  - `.hermes/mcp_openjev.py`: `query_live_nvml_vram` hardware quorum gate
- Module Stems:
  - `query_live_nvml_vram`
- Required Skills:
  - `karpathy-surgical-diff`

---

## 2. Causal Hypotheses
1. Without live hardware monitoring, inference sessions can exceed physical GPU GDDR6 capacity during long context or multi-turn generation. Integrating real-time NVML telemetry via `query_live_nvml_vram()` verifies `used_mib <= 5400.0` deterministically on CPU RAM.
2. The NVML query executes with 0.0 MiB tool overhead, leaving full hardware headroom for pinned inference and vision/memory sidecars.

---

## 3. Surgical Implementation Plan
- [x] Step 1: Formulate single-cause causal hypothesis.
- [x] Step 2: Ensure non-git backup exists (`<target>.hermes.bak`) if mutating Domain B files.
- [x] Step 3: Verify `query_live_nvml_vram()` returns valid VRAM metrics adhering to `used_mib <= 5400.0`.
- [x] Step 4: Execute `contract.sh` and seal `/tmp/hermes_verified_receipt.json`.
- [x] Step 5: Advance stage to `03_verify` in `03_verify/status.json`.
