# Phase 03: Ebbinghaus Memory Forgetting & Spillover Gate — Implementation Checklist

> **Phase Directory**: `phase_03_ebbinghaus_memory_forgetting_spillover_gate`  
> **Status**: Stage `02_impl` execution complete  

---

## 1. Targeted Symbols & Code Modules
- Target File(s):
  - `.hermes/mcp_openjev.py`: implement `_auto_spillover_memory_md` tool and bind it
  - `.hermes/config.yaml`: verify `memory_char_limit: 2200`
  - `.hermes/memories/MEMORY.md`: preserve immutable `CORE_HEADER_SET` §1–§8 under 2,200 chars
- Module Stems:
  - `_auto_spillover_memory_md`
- Required Skills:
  - `karpathy-surgical-diff`

---

## 2. Causal Hypotheses
1. Without `_auto_spillover_memory_md`, memory growth can expand unbounded across sessions, increasing context length and breaching Port 8138 VRAM limits. Enforcing the 2,200 character cap on `MEMORY.md` while routing overflow notes into `EXPERIENCE.md` maintains strict sub-8K context discipline.
2. The verification contract asserts `len(MEMORY.md) <= 2200 and "§1" in m`. `MEMORY.md` is currently 1,296 characters, contains all §1–§8 headers, and fulfills this invariant.

---

## 3. Surgical Implementation Plan
- [x] Step 1: Formulate single-cause causal hypothesis.
- [x] Step 2: Ensure non-git backup exists (`<target>.hermes.bak`) if mutating Domain B files.
- [x] Step 3: Add `_auto_spillover_memory_md` to `mcp_openjev.py`.
- [x] Step 4: Verify `contract.sh` passes and `/tmp/hermes_verified_receipt.json` is sealed.
- [x] Step 5: Advance stage to `03_verify` in `03_verify/status.json`.
