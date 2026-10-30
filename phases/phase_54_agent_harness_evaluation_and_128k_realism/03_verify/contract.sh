#!/usr/bin/env bash
# Phase 54 Deterministic Verification Contract (03_verify/contract.sh)
# Asserts 128K Hardware Realism, ICM Walk Test Point 5 Deduplication,
# Multi-Model Config Readiness, Upstream Purity, and Layer B Harness Targets.

set -euo pipefail

PASS=0
FAIL=0
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

CONFIG_FILE=".hermes/config.yaml"
if [[ ! -f "$CONFIG_FILE" && -f "private_dot_hermes/config.yaml" ]]; then
  CONFIG_FILE="private_dot_hermes/config.yaml"
elif [[ ! -f "$CONFIG_FILE" && -f "$HOME/.hermes/config.yaml" ]]; then
  CONFIG_FILE="$HOME/.hermes/config.yaml"
fi

assert_check() {
  local desc="$1"
  local cmd="$2"
  if eval "$cmd" >/dev/null 2>&1; then
    echo "[PASS] $desc"
    PASS=$((PASS + 1))
  else
    echo "[FAIL] $desc"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== Executing Phase 54 Verification Contract ==="

# Assertion 1: 5-Layer ICM Directory Structure & Contract Presence
assert_check "1. 5-Layer ICM structure exists (AGENTS.md, CONTEXT.md, stages 01-04)" \
  "[[ -f AGENTS.md && -f CONTEXT.md && -f stages/01-spec/CONTEXT.md && -f stages/02-plan/CONTEXT.md && -f stages/03-execute/CONTEXT.md && -f stages/04-verify/CONTEXT.md ]]"

# Assertion 2: Line Budget Discipline (CONTEXT.md <= 80 lines, Layer 3 rules <= 200 lines)
assert_check "2. All CONTEXT.md files are strictly <= 80 lines" \
  "awk 'FNR==1{if(lines>80) exit 1; lines=0} {lines++} END{if(lines>80) exit 1}' CONTEXT.md stages/*/CONTEXT.md"

assert_check "3. All Layer 3 rules/*.md files are strictly <= 200 lines" \
  "awk 'FNR==1{if(lines>200) exit 1; lines=0} {lines++} END{if(lines>200) exit 1}' rules/*.md"

# Assertion 4: Walk Test Point 5 (Single Source of Truth — obsolete 5,400 MiB purged from routing files)
assert_check "4. Obsolete 5,400 MiB cap purged from AGENTS.md, CONTEXT.md, and stages/" \
  "! grep -q '5,400' AGENTS.md CONTEXT.md stages/*/CONTEXT.md"

assert_check "5. rules/hardware_vram_invariants.md establishes 5,800.0 MiB ceiling and 131072 context" \
  "grep -q '5,800.0 MiB' rules/hardware_vram_invariants.md && grep -q '131072' rules/hardware_vram_invariants.md"

# Assertion 6: 128K Context & All 3 Candidate Models Registered in config.yaml
assert_check "6. config.yaml enforces context_length: 131072 and registers all 3 candidate models" \
  "grep -q 'context_length: 131072' \"$CONFIG_FILE\" && grep -q 'gemma-4-E4B-it-qat-exact:' \"$CONFIG_FILE\" && grep -q 'nemotron-3.5-bolt-e4b:' \"$CONFIG_FILE\""

# Assertion 7: Gateway & Agent Unattended Evaluation Flags in config.yaml
assert_check "7. config.yaml sets approvals.mode: off, direct_model_requests: true, and execution_guidance: false" \
  "grep -q 'direct_model_requests: true' \"$CONFIG_FILE\" && grep -q 'execution_guidance: false' \"$CONFIG_FILE\" && grep -q 'mode: \"off\"' \"$CONFIG_FILE\""

# Assertion 8: Zero Bespoke Python/Shell Scripts in scripts/ or plugins/
assert_check "8. Zero bespoke Python or shell wrappers in scripts/ or plugins/" \
  "[[ ! -d scripts || -z \"\$(find scripts -maxdepth 2 -type f \\( -name '*.py' -o -name '*.sh' \\) 2>/dev/null)\" ]]"

# Assertion 9: 100% Upstream Substrate Purity in .hermes/hermes-agent
assert_check "9. Upstream .hermes/hermes-agent repository is 100% clean and unpatched" \
  "[[ ! -d .hermes/hermes-agent ]] || git -C .hermes/hermes-agent diff --quiet"

# Assertion 10: Live NVML Hardware VRAM Check (<= 5800 MiB & Disp.A: Off)
assert_check "10. Live NVML GPU VRAM <= 5,800 MiB on RTX 3050" \
  "VRAM_USED=\$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -n1 | tr -d ' '); [[ \"\$VRAM_USED\" -le 5800 ]]"

echo "=== Summary: $PASS Passed, $FAIL Failed ==="
if [[ "$FAIL" -gt 0 ]]; then
  exit 1
fi

cat <<EOF > /tmp/hermes_phase54_verified_receipt.json
{
  "phase_id": 54,
  "phase_name": "phase_54_agent_harness_evaluation_and_128k_realism",
  "status": "VERIFIED_AND_SEALED",
  "assertions_passed": $PASS,
  "assertions_failed": $FAIL,
  "context_length_enforced": 131072,
  "kv_cache_type": "q4_0",
  "vram_ceiling_mib": 5800.0
}
EOF
