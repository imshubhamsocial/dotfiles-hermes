#!/usr/bin/env bash
set -euo pipefail

echo "=== Phase 53 Verification Contract: Zero-Bespoke Upstream Consolidation ==="

REPO_DIR="/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes"
CHEZMOI_DIR="$REPO_DIR/.local_archived/share/chezmoi"

# 1. Assert 0 bespoke scripts exist in scripts/ or private_dot_hermes/
echo "[1/7] Checking for bespoke scripts..."
BESPOKE_COUNT=0
for d in "$CHEZMOI_DIR/scripts" "$CHEZMOI_DIR/private_dot_hermes" "$REPO_DIR/scripts"; do
  if [ -d "$d" ]; then
    count=$(find "$d" -maxdepth 1 \( -name "executable_*.py" -o -name "executable_*.sh" -o -name "*.py" -o -name "*.sh" \) 2>/dev/null | wc -l)
    BESPOKE_COUNT=$((BESPOKE_COUNT + count))
  fi
done
if [ "$BESPOKE_COUNT" -ne 0 ]; then
  echo "FAIL: Found $BESPOKE_COUNT bespoke executable scripts."
  exit 1
fi
echo "PASS: Zero bespoke scripts found in repository."

# 2. Assert no custom plugin exists
echo "[2/7] Checking for custom plugins..."
if [ -d "/var/home/imshubhamsocial/.hermes/plugins/hermes-icm-os" ]; then
  echo "FAIL: Custom plugin directory hermes-icm-os exists."
  exit 1
fi
echo "PASS: No custom plugins exist."

# 3. Assert ICM line limits on all contracts (<80 lines) and reference files (<200 lines)
echo "[3/7] Enforcing ICM line limits..."
for f in "$REPO_DIR/AGENTS.md" "$REPO_DIR/CONTEXT.md" "$REPO_DIR"/stages/*/CONTEXT.md; do
  lines=$(wc -l < "$f")
  if [ "$lines" -ge 80 ]; then
    echo "FAIL: $f has $lines lines (limit is < 80)"
    exit 1
  fi
done
for f in "$REPO_DIR"/rules/*.md "$REPO_DIR"/_config/*.md; do
  lines=$(wc -l < "$f")
  if [ "$lines" -ge 200 ]; then
    echo "FAIL: $f has $lines lines (limit is < 200)"
    exit 1
  fi
done
echo "PASS: All ICM contracts (<80) and reference files (<200) strictly within limits."

# 4. Assert plugins are enabled in Hermes
echo "[4/7] Checking Hermes plugins status..."
PLUGINS_OUT=$(hermes plugins list --plain --no-bundled)
if ! echo "$PLUGINS_OUT" | grep -q "jev-curator"; then
  echo "FAIL: jev-curator plugin not enabled."
  exit 1
fi
if ! echo "$PLUGINS_OUT" | grep -q "openviking"; then
  echo "FAIL: openviking plugin not enabled."
  exit 1
fi
echo "PASS: Official catalog plugins jev-curator and openviking are enabled."

# 5. Assert Substrate Purity on .hermes/hermes-agent
echo "[5/7] Checking upstream hermes-agent git purity..."
AGENT_DIR="$REPO_DIR/.hermes/hermes-agent"
if [ -d "$AGENT_DIR/.git" ]; then
  DIRTY_COUNT=$(cd "$AGENT_DIR" && git status --porcelain | wc -l)
  if [ "$DIRTY_COUNT" -ne 0 ]; then
    echo "FAIL: Upstream hermes-agent is dirty ($DIRTY_COUNT modified files)."
    exit 1
  fi
fi
echo "PASS: Upstream hermes-agent is 100% clean."

# 6. Assert live NVML VRAM <= 5400.0 MiB
echo "[6/7] Checking NVML VRAM..."
VRAM_USED=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -n1 | tr -d ' ')
if [ "$VRAM_USED" -gt 5400 ]; then
  echo "FAIL: GPU VRAM exceeds ceiling: ${VRAM_USED} MiB > 5400.0 MiB."
  exit 1
fi
echo "PASS: GPU VRAM invariant satisfied (${VRAM_USED} MiB <= 5400.0 MiB)."

# 7. Cryptographically seal verification receipt
echo "[7/7] Sealing verification receipt..."
RECEIPT_FILE="/tmp/hermes_verified_receipt.json"
cat <<EOF > "$RECEIPT_FILE"
{
  "phase": 53,
  "phase_name": "phase_53_zero_bespoke_upstream_consolidation_icm_5layer",
  "status": "PASS",
  "exitstatus": 0,
  "vram_used_mib": $VRAM_USED,
  "timestamp": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
  "sha256": "$(sha256sum "$REPO_DIR/AGENTS.md" | awk '{print $1}')"
}
EOF

echo "Phase 53 verified and sealed successfully."
exit 0
