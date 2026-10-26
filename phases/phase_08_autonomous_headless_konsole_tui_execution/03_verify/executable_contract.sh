#!/usr/bin/env bash
# Verification Contract (V_contract) for Phase 08: Autonomous Headless & Konsole TUI Execution
set -euo pipefail

distrobox enter ws-hermes -- bash -c 'python3 -c "import os; assert len(os.environ.get(\"TMPDIR\", \"/tmp\")) <= 16" && hermes doctor'
