# Implementation Task Checklist: Phase 50

## 1. Concrete Symbol Targets
- `HermesICMValidator` in `scripts/hermes_icm_validator.py`
- `AGENTS.md` (6-section schema + 3-tier permissions + anti-rationalization inline)
- `rules/anti_rationalization_tables.md`
- `rules/anti_sycophancy_directives.md`
- `~/.hermes/skills/icm-architect/SKILL.md`
- `03_verify/contract.sh` in `phases/phase_50_icm_5layer_workspace_restructure_anti_rationalization/03_verify/contract.sh`

## 2. Causal Hypotheses
- **H1 (Progressive Disclosure)**: Restructuring the workspace into 5 progressive layers (Layers 0–4) and capping `CONTEXT.md` at 80 lines prevents context window dilution and maintains working context between 2,000 and 8,000 tokens.
- **H2 (Anti-Rationalization Rebuttal)**: Pre-emptively enumerating and refuting common agentic rationalisations (e.g. "I will ask human", "Tests take too long", "I assume parameter matches") eliminates 100% of premature bailouts in multi-turn customer dialogues.
- **H3 (3-Tier Boundary Enforcement)**: Categorizing operations into `Always` (read, parse AST, run contracts), `Ask First` (mutating git remotes, external API calls), and `Never` (bypassing permissions, editing raw tests) bounds agent agency deterministically.

## 3. Implementation Steps
- [ ] Create `rules/anti_rationalization_tables.md` and `rules/anti_sycophancy_directives.md`.
- [ ] Implement `scripts/hermes_icm_validator.py` with `HermesICMValidator`.
- [ ] Update root `AGENTS.md` to 6-section schema and symlink `CLAUDE.md`.
- [ ] Deploy `~/.hermes/skills/icm-architect/SKILL.md`.
- [ ] Implement and execute `03_verify/contract.sh` validating ICM schema and Walk Test.
