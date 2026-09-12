---
name: substrate-recon
description: Diagnose container/host and install system devel packages.
triggers: ["missing header", "cannot find -l", "missing library", "cmake error", "dnf install", "pkg-config", "devel package"]
---

# Substrate Reconnaissance & Package Discovery

Trigger: Use when a command or compilation fails due to missing system headers or libraries.

## Workflows
- **Devel Packages**: See [docs/fedora-devel-packages.md](docs/fedora-devel-packages.md)

## Quick Probe
```bash
./scripts/find-devel.sh <library-name>
```
