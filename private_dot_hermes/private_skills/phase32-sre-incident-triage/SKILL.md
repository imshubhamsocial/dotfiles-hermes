---
name: sre-incident-triage
description: Systemd, NVML & DevOps incident triage
---

# Production SRE Incident Triage & DevOps

## When to Use
Use for diagnosing daemon crashes, GPU VRAM spikes, systemd unit failures, and executing safe Domain B configuration rollbacks.

## Quick Reference
* Omniscient Audit: `mcp_openjev(jev_verify_arsi_omniscient)`
* Live VRAM Check: `mcp_openjev(query_live_nvml_vram)`
* Logs: `journalctl --user -u hermes-llama-server -n 100 --no-pager`

## Procedure
1. Invoke `jev_compile_intent` and `jev_verify_arsi_omniscient` on Turn 1 to inspect VRAM (<= 4,812.0 MiB) and Ports 8138, 8139, 1933.
2. Inspect service logs using 40/60 head-tail truncation to isolate root-cause stack traces.
3. Ensure write-once `<file>.hermes.bak` exists before editing any service unit or config file.
4. Validate syntax (`bash -n`), restart affected user daemon, confirm `hermes doctor` exit 0, and record post-mortem in `EXPERIENCE.md`.
