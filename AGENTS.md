# Workspace Routing & ICM Execution Protocol (AGENTS.md)

> **Architectural Standard**: Jake Van Clief's Interpretable Context Methodology (ICM / MWP, arXiv:2603.16021)  
> **Layering Rule**: **60% Infrastructure** (POSIX/Git) | **30% Orchestration** (ICM Folders + FastMCP Pydantic v2) | **10% AI Cognition** (Gemma-4-E4B on Port 8138)  
> **Working Context Discipline**: Maintain active working context strictly between 2,000 and 8,000 tokens.

---

## 1. Operating Scope & Layering Allocation
- **Active Phase Constraint**: Operate strictly on the active phase defined in `phases/status_ledger.json`.
- **Infrastructure First (60%)**: Enforce POSIX file system integrity, git tracking via Chezmoi (`dotfiles-hermes`), and AST compiler gates before test execution.
- **Orchestration (30%)**: Route tools via Ephemeral FastMCP Bridge (Port 1934) and OpenViking Hierarchical Memory (Port 1933).
- **AI Cognition (10%)**: Bound local model reasoning tokens under tight deliberation budgets.

---

## 2. 3-Tier Permissions Boundary
- **Always (Autonomous Execution)**:
  - Read files, query AST, run pre-commit linters (`ruff check`), and execute phase verification contracts (`contract.sh`).
  - Query local read-only database tools before mutating state.
- **Ask First (User Escalation Required)**:
  - Mutating upstream git remotes outside prescribed phase contracts.
  - Deleting non-temporary files or modifying environment configurations.
- **Never (Hard Forbidden Invariants)**:
  - Never bypass permission checks, credentials, or sandbox boundaries.
  - Never modify canonical test assertions to force passing benchmarks.
  - Never execute with GPU VRAM exceeding 5,400.0 MiB.

---

## 3. ICM 5-Layer Progressive Context Architecture
- **Layer 0 (Global Rules)**: Root `AGENTS.md` (symlinked to `CLAUDE.md`).
- **Layer 1 (Workspace Scope)**: Project `CONTEXT.md` defining goals and explicit Exclusion Tables.
- **Layer 2 (Stage Gate Contracts)**: Numbered stage directories (`01_spec/`, `02_impl/`, `03_verify/`) with `CONTEXT.md` <= 80 lines.
- **Layer 3 (Factory / Immutables)**: Rules, schemas, and references in `rules/` <= 200 lines per file.
- **Layer 4 (Product / Mutables)**: Output artifacts, diffs, and verification receipts.
- **Selective Section Loading**: Stage inputs must be loaded using 4-column tables (`Source | File | Section | Why`), extracting only targeted heading sections.

---

## 4. Stage Gate Machine (Mandatory Order)

### Stage 1: RECON & INTENT (`01_spec`)
- **Deliberation Tag**: Emit `<deliberation><global>...</global></deliberation>`.
- Read **ONLY** `phases/<active_phase>/01_spec/spec.md` and `phases/<active_phase>/03_verify/status.json`.
- Write concrete symbol targets and causal hypotheses into `02_impl/task.md`. Update `status.json` stage to `"02_impl"`.

### Stage 2: SURGICAL IMPLEMENTATION (`02_impl`)
- **Deliberation Tag**: Emit `<deliberation><focus id="target_symbol">...</focus></deliberation>`.
- Read `02_impl/task.md`. Create `<target>.hermes.bak` shadow backups before modifying non-git files.
- Apply focused causal changes (Karpathy U12: <= 15 lines diff per step). Run AST and `ruff check`. Update `status.json` stage to `"03_verify"`.

### Stage 3: DETERMINISTIC VERIFICATION (`03_verify`)
- **Deliberation Tag**: Emit `<deliberation><local>...</local></deliberation>`.
- Execute `phases/<active_phase>/03_verify/contract.sh`. Exit code 0 certifies pass.
- Cryptographically seal `/tmp/hermes_verified_receipt.json`. Update `status.json` to complete and advance ledger.
- **Two-Strike Tabu Rule**: Strike 1 allows 1 new hypothesis; Strike 2 requires clean-slate `git checkout` / shadow restore.

---

## 5. Anti-Rationalization & Epistemic Persistence Gates
- **Anti-Rationalization Rebuttal**: Consult `rules/anti_rationalization_tables.md`. Never use missing attributes as justification to bail out without read-tool queries.
- **Anti-Sycophancy Directives**: Enforce all 17 rules in `rules/anti_sycophancy_directives.md`. Ground truth supersedes authority.
- **Fresh-Session Review**: Verify critical state mutations independently of conversational history to prevent self-referential bias.

---

## 6. Hardware & Cryptographic Invariants
- **NVML VRAM Ceiling**: `query_live_nvml_vram()` MUST verify `used_mib <= 5400.0`.
- **Receipt Sealing**: Tasks are incomplete until `/tmp/hermes_verified_receipt.json` returns `exitstatus == 0`.
- **Substrate Purity**: Upstream `.hermes/hermes-agent` must remain 100% clean (`git status --porcelain == ""`).
