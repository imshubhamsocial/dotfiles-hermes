# Phase 53 Implementation Task: Zero-Bespoke Upstream Consolidation

> Execution Record for Phase 53.

---

## 1. Safety Archival & Script Decommissioning
- [x] Tag repository at commit `8d58ee0` as `v52.0-pre-gdr28-zero-code`.
- [x] Stop and disable user services: `hermes-ephemeral-bridge.service` and `hermes-rsi-daemon.service`.
- [x] Remove all 17 bespoke scripts via `git rm -f` (13 in `scripts/`, 4 in `private_dot_hermes/`).
- [x] Ensure `~/.hermes/plugins/hermes-icm-os` does not exist.

## 2. Official Plugins & Ecosystem Skills
- [x] Initialize OpenViking server via `openviking-server init` and verify with `openviking-server doctor`.
- [x] Install and enable official catalog plugin `openviking` (v2.1.2).
- [x] Install and enable official plugin `jev-curator` (v0.1.0) with zero tool override privileges.
- [x] Verify Jake Van Clief's official `icm-architect` skill in `~/.hermes/skills/icm-architect/SKILL.md`.
- [x] Create nightly Gateway cron job `nightly_icm_architect` (`0 3 * * *`).

## 3. Declarative Config & 5-Layer ICM Workspace
- [x] Deploy canonical `~/.hermes/config.yaml` with declarative fixes for Issues #28825 & #56360.
- [x] Deploy canonical `~/.hermes/.env` with local auth keys and OpenViking bindings.
- [x] Deploy Layer 0 `AGENTS.md` (< 60 lines) and `SOUL.md`.
- [x] Deploy Layer 1 `CONTEXT.md` (< 80 lines).
- [x] Deploy Layer 2 stage contracts (`stages/01-spec/` to `stages/04-verify/`, each < 80 lines).
- [x] Deploy Layer 3 reference files in `_config/` and `rules/` (< 200 lines each).
- [x] Deploy `.pre-commit-config.yaml` for Ruff and POSIX line limit checks.
