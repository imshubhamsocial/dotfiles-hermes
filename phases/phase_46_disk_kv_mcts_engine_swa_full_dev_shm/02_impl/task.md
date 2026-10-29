# Implementation Task Checklist: Phase 46

## 1. Concrete Symbol Targets
- `MCTSNode` in `scripts/hermes_disk_kv_mcts.py`
- `compute_deterministic_value` in `scripts/hermes_disk_kv_mcts.py`
- `DiskKVMCTSEngine` in `scripts/hermes_disk_kv_mcts.py`
- Verification contract in `phases/phase_46_disk_kv_mcts_engine_swa_full_dev_shm/03_verify/contract.sh`

## 2. Causal Hypotheses
- **H1 (Disk-KV Time Multiplexing)**: By serializing Slot 0 to `/dev/shm/hermes_mcts_kv/node_{id}.bin` and restoring on-demand with `--swa-full`, tree search is achieved with 0.0 MiB additional VRAM footprint and sub-50ms switch latencies.
- **H2 (Deterministic Value Function $V_{\text{det}}$)**: Grounding node scoring directly in AST parsing, Ruff linter diagnostics, pytest assertion passes, and Epistemic Gate 2 compliance eliminates noisy neural hallucination rewards and guarantees monotonic convergence toward correct solutions.

## 3. Implementation Steps
- [x] Implement `scripts/hermes_disk_kv_mcts.py` with `MCTSNode`, `compute_deterministic_value`, and `DiskKVMCTSEngine`.
- [ ] Implement and execute `phases/phase_46_disk_kv_mcts_engine_swa_full_dev_shm/03_verify/contract.sh`.
