# Phase 47 Specification: OpenViking TrieHI Skill Distiller & Zero-VRAM Live Web Cognition Pipeline

* **ICM Layer**: Closed-Loop AGI / Orchestration & Cognition
* **Context Budget**: < 3,500 tokens (Sub-8K Compliant)
* **Input State**: Knowledge obsolescence past cutoff dates and lack of persistent contrastive repair learning without backprop.
* **Process**:
  1. Deploy `scripts/hermes_skill_distiller.py`:
     - Monitor `/tmp/hermes_verified_receipt.json` on task completions with strikes $\ge 1$ or MCTS leaf selection.
     - Extract Minimal Contrastive Repair Tuples $\langle \sigma, a_{\text{failed}}, e_{\text{trace}}, a_{\text{verified}}, \delta_{\text{diff}} \rangle$.
     - Verify 3-Gate Epistemic Quarantine ($V_{\text{epistemic}} == 1.0$) and compile into `~/.hermes/skills/<domain>/<skill_slug>/SKILL.md`.
     - Ingest into OpenViking TrieHI (`viking://skills/`) with L0 (256-char abstract), L1 (4,000-char overview), and L2 (full code) tiers.
  2. Deploy `scripts/hermes_zero_vram_web.py`:
     - 4-stage pipeline: `01_search` (federated search APIs), `02_harvest` (CPU headless Chromium `--disable-gpu` 0.0 MiB VRAM), `03_firewall` (prompt injection sanitizer), `04_ingest` (TrieHI documentation indexer into `viking://resources/live_web/`).
  3. Validate `HF_TOKEN` environment availability for GAIA gated benchmark evaluation.
* **Output Artifacts**:
  - `scripts/hermes_skill_distiller.py`
  - `scripts/hermes_zero_vram_web.py`
