#!/usr/bin/env bash  
# bootstrap_phase01.sh — 60% Infrastructure Provisioning inside ws-hermes Distrobox  
set -euo pipefail

export HERMES_WORKSPACE="/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes"  
export HERMES_HOME="${HERMES_WORKSPACE}/.hermes"  
export TMPDIR="/tmp"

mkdir -p "${HERMES_HOME}/cache/intent_manifests" \\  
         "${HERMES_HOME}/cache/shadow_backups" \\  
         "${HERMES_HOME}/cache/dream_worlds" \\  
         "${HERMES_HOME}/cache/slots" \\  
         "${HERMES_HOME}/skills" \\  
         "${HERMES_HOME}/rules" \\  
         "${HERMES_HOME}/memories"

# 1. Enforce 100% Upstream Git Purity in .hermes/hermes-agent  
if [ ! -d "${HERMES_HOME}/hermes-agent/.git" ]; then  
    git clone https://github.com/NousResearch/hermes-agent.git "${HERMES_HOME}/hermes-agent"  
fi  
git -C "${HERMES_HOME}/hermes-agent" checkout -f main  
git -C "${HERMES_HOME}/hermes-agent" clean -fd  
test -z "$(git -C "${HERMES_HOME}/hermes-agent" status --porcelain)"

# 2. Permanently Retire Legacy Monkey-Patches and Short-Circuit Files (VULN-A1-01)  
rm -f "${HERMES_WORKSPACE}/.hermes.md" "${HERMES_WORKSPACE}/HERMES.md" \\  
      "${HERMES_HOME}/sitecustomize.py"  
rm -rf "${HERMES_HOME}/runtime_hooks"

# 3. Repair Container pip & uv Toolchain Entrypoints (VULN-A1-04)  
/usr/bin/python3.13 -m ensurepip --default-pip --upgrade  
/usr/bin/python3.13 -m pip install --upgrade pip uv wheel setuptools  
/usr/bin/python3.13 -m pip install \\  
    "pydantic>=2.9.0" "pydantic-settings>=2.5.0" "fastmcp>=0.4.0" "mcp>=1.2.0" \\  
    "google-adk>=2.9.0" "langgraph>=0.2.35" "nemoguardrails>=0.24.0" \\  
    "fastembed>=0.3.0" "pytest>=9.1.1" "ruff>=0.7.0" "nvidia-ml-py>=12.0.0" \\  
    "sympy>=1.13.0" "diskcache>=5.6.3" "httpx>=0.27.0" "numpy>=2.0.0"

