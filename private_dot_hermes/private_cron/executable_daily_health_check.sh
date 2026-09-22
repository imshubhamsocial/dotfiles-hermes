#!/usr/bin/env bash
# Hermes Agent OS — Daily Health Check (upstream commands only)
set -euo pipefail
hermes doctor
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader
echo "Daily health check complete: $(date -Iseconds)"
