# Phase 46 Specification: Zero-VRAM Disk-KV Monte Carlo Tree Search (MCTS) Engine

* **ICM Layer**: AI Cognition (10% Allocation Tier)
* **Context Budget**: < 3,500 tokens (Sub-8K Compliant)
* **Input State**: Standard multi-slot tree search (`-np 4`) OOMs on 6GB RTX 3050. LLM self-scoring is uncalibrated at 4B scale.
* **Process**:
  1. Deploy `scripts/hermes_disk_kv_mcts.py` implementing single-slot time-multiplexed tree search:
     - Persist Slot 0 KV states to `/dev/shm/hermes_mcts_kv/node_{id}.bin` via `POST /slots/0?action=save` and restore via `POST /slots/0?action=restore` with `--swa-full` cache preservation.
     - Evaluate candidates using deterministic CPU value function:
       $$V_{\text{det}} = 0.20 \cdot \mathbb{I}_{\text{AST}} + 0.20 \cdot \frac{1}{1 + \text{RuffErrors}} + 0.40 \cdot \text{TestPassRate} + 0.20 \cdot \mathbb{I}_{\text{Gate2}}$$
     - Implement PUCT tree selection, expansion, evaluation, and backpropagation across shadow Git commits in `/tmp/hermes_shadow_wt`.
* **Output Artifacts**:
  - `scripts/hermes_disk_kv_mcts.py`
