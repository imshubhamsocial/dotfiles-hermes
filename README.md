# Hermes Agent OS v4.4.0 — Interpretable Context Architecture (ICM) Workspace

> **Source Specification**: [`Hermes OS GDR17 Implementation Guide.md`](file:///var/home/imshubhamsocial/Desktop/GDR/GDR17/Output/Hermes%20OS%20GDR17%20Implementation%20Guide.md)  
> **Decomposition Standard**: [`Now read this file, See what exactly Jake meant b....md`](file:///var/home/imshubhamsocial/Desktop/GDR/GDR17/Output/Now%20read%20this%20file,%20See%20what%20exactly%20Jake%20meant%20b....md)  
> **Architectural Doctrine**: Jake Van Clief's Interpretable Context Methodology (ICM / MWP, arXiv:2603.16021)  
> **The 60 / 30 / 10 Framework Layering Rule**:
> - **60% Infrastructure**: Linux POSIX substrate, Git, Python 3.13 `.venv`, `uv`, `pytest`, `ruff`, `ast-grep`.
> - **30% Orchestration**: Position-addressed stage folders (`01_spec/`, `02_impl/`, `03_verify/`), `status.json`, FastMCP with Pydantic v2.
> - **10% AI Cognition**: Local Gemma-4-E4B-it on Port 8138 strictly confined to reasoning, AST exploration, and surgical diffs.

---

## 1. Complete Physical Directory Map

```
/var/home/imshubhamsocial/Desktop/GDR/GDR17/AI/
├── AGENTS.md                                 # Layer 1: Hub-and-spoke router & stage transition rules
├── conftest.py                               # 60% Infra: Root epistemic receipt & CPython 3.13 teardown hook
├── README.md                                 # Master architectural orientation & quickstart hub
│
├── scripts/                                  # 60% Infrastructure Provisioning Scripts
│   └── bootstrap_phase01.sh                  # Container toolchain repair & upstream git purity bootstrap
│
├── .hermes/                                  # Hermes Core Runtime Substrate
│   ├── SOUL.md                               # Layer 1: Universal Constitutional Kernel (The 12 Laws)
│   ├── config.yaml                           # 60% Infra: Canonical runtime configuration & FastMCP bindings
│   ├── mcp_openjev.py                        # Layer 3: Unified OpenJev v4.4.0 FastMCP 14-tool kernel
│   ├── hermes_rsi_daemon.py                  # 60% Infra: 24/7 continuous autonomous RSI engine
│   ├── hermes-rsi-daemon.service             # Systemd user daemon unit
│   ├── memories/                             # Layer 2: Position-addressed cognitive state
│   │   ├── MEMORY.md                         # Core Header Set (§1–§8, capped at <= 2,200 chars)
│   │   └── EXPERIENCE.md                     # Auto-spillover target indexed by OpenViking
│   └── skills/                               # Layer 3: Deferred progressive playbooks (YAML frontmatter <= 250B)
│       ├── stair-navigation/SKILL.md         # AST symbol table extraction & outlining
│       ├── karpathy-surgical-diff/SKILL.md   # Surgical diffs under Karpathy U12 limit
│       └── speckit-annealing/SKILL.md        # Spec-Kit clean-slate regeneration on Strike 2
│
├── docs/reference/                           # Cold Storage (NEVER auto-loaded into prompt context)
│   ├── 00_attention_physics_and_telemetry.md # Attention physics, 128K context & Challenge A1 autopsy
│   ├── 01_frontier_prompt_distillation.md    # Leaked frontier system prompt analysis (Claude, o1/o3, Gemini)
│   ├── 02_mathematical_certification_bpe.md  # Proof of BPE suffix jitter neutralization
│   ├── 03_speculative_telemetry_and_master_matrix.md # Speculative inference metrics & Master Matrix
│   ├── 04_mathematical_foundations_rsi.md    # Mathematical foundations of 3-regime RSI architecture
│   ├── 05_master_certification_checklist.md  # 5-Step deterministic verification sequence
│   └── 06_works_cited_and_images.md          # Complete bibliography & all 106 formula definitions
│
├── tests/                                    # Deterministic Testbeds
│   └── phase01_canonical_parity/
│       └── test_phase01_parity.py            # Phase 01 upstream parity & FastMCP verification suite
│
└── phases/                                   # Layer 2: Position-Addressed Compiler Passes (Phases 01 to 32)
    ├── status_ledger.json                    # Global pass tracker (current_phase, verified state)
    ├── phase_01_canonical_parity/
    │   ├── 01_spec/spec.md                   # Single-phase spec, invariants & matrix row
    │   ├── 02_impl/task.md                   # Concrete surgical checklist & symbol targets
    │   └── 03_verify/
    │       ├── contract.sh                   # Exact V_contract bash one-liner (chmod +x)
    │       └── status.json                   # Position-addressed state: stage, strikes, verified
    ├── phase_02_openviking_hierarchical_memory_server/
    │   ├── 01_spec/spec.md
    │   ├── 02_impl/task.md
    │   └── 03_verify/{contract.sh, status.json}
    ├── ... [Phases 03 through 31]
    └── phase_32_asymmetric_attention_production_agi_gauntlet/
        ├── 01_spec/spec.md
        ├── 02_impl/task.md
        └── 03_verify/{contract.sh, status.json}
```

---

## 2. Line-by-Line & Word-by-Word Document Accounting

Every line of the original 1,968-line guide is mapped into this physical directory structure with zero omission:

| Original Guide Section | Source Lines | Destination File / Directory | Layer / Purpose |
| :--- | :-: | :--- | :--- |
| Section 1: Attention Physics & Autopsy | L1–L63 | `docs/reference/00_attention_physics_and_telemetry.md` | Cold Reference Storage |
| Section 2: Frontier Prompts Distillation | L64–L80 | `docs/reference/01_frontier_prompt_distillation.md` | Cold Reference Storage |
| Section 2: Universal Constitutional Kernel | L81–L138 | `.hermes/SOUL.md` (and `AGENTS.md`) | Layer 1 Universal Kernel |
| Section 3: BPE Jitter Mathematical Proof | L139–L148 | `docs/reference/02_mathematical_certification_bpe.md` | Cold Reference Storage |
| Section 3: Step 1 Substrate Bootstrap | L149–L189 | `scripts/bootstrap_phase01.sh` | 60% Infrastructure |
| Section 3: Step 2 Runtime Configuration | L190–L239 | `.hermes/config.yaml` | 60% Infrastructure |
| Section 3: Step 3 OpenJev FastMCP Kernel | L240–L982 | `.hermes/mcp_openjev.py` | Layer 3 FastMCP Kernel |
| Section 3: Step 4 Phase 1 Test Suite | L983–L1049 | `tests/phase01_canonical_parity/test_phase01_parity.py` | Deterministic Verification Gate |
| Section 4: Telemetry & Master Matrix | L1050–L1108 | `docs/reference/03_speculative_telemetry_and_master_matrix.md` | Cold Reference Storage |
| Section 4: Exhaustive Phases 01 to 32 | L1109–L1342 | `phases/phase_01_.../` through `phases/phase_32_.../` (`01_spec/spec.md` + `03_verify/contract.sh`) | Layer 2 Compiler Passes |
| Section 4: Root conftest.py Hook | L1343–L1480 | `conftest.py` | 60% Infrastructure |
| Section 5: Mathematical Foundations of RSI | L1481–L1494 | `docs/reference/04_mathematical_foundations_rsi.md` | Cold Reference Storage |
| Section 5: Systemd Daemon Unit | L1495–L1515 | `.hermes/hermes-rsi-daemon.service` | 60% Infrastructure |
| Section 5: Continuous 24/7 RSI Engine | L1516–L1708 | `.hermes/hermes_rsi_daemon.py` | 60% Infrastructure |
| Section 6: Master Certification Checklist | L1709–L1740 | `docs/reference/05_master_certification_checklist.md` | Cold Reference Storage |
| Section 6: Works Cited & 106 Images | L1741–L1968 | `docs/reference/06_works_cited_and_images.md` | Cold Reference Storage |

---

## 3. How to Run the ICM Agent Workflow

### Step 1: Substrate Provisioning (60% Infrastructure)
```bash
distrobox enter ws-hermes -- bash scripts/bootstrap_phase01.sh
```

### Step 2: Launch the ICM Single-Stage Agent Loop
```bash
distrobox enter ws-hermes -- hermes chat --yolo -q '
Execute the next unverified phase in phases/status_ledger.json following ~/.hermes/SOUL.md and AGENTS.md:
1. Turn 1: Invoke jev_compile_intent and extract_workspace_ast.
2. Read phases/<active_phase>/03_verify/status.json and phases/<active_phase>/01_spec/spec.md. Do not read any other phase folders.
3. Document your surgical plan in 02_impl/task.md, apply mutations strictly via jev_mutate_module, and run 03_verify/contract.sh.
4. Enforce the Two-Strike Tabu rule on test failures: revert to clean state on Strike 2 and invoke jev_anneal_cluster.
5. Do not declare completion until 03_verify/contract.sh exits 0, /tmp/hermes_verified_receipt.json is sealed, and query_live_nvml_vram() confirms used_mib <= 5400.0.
'
```
