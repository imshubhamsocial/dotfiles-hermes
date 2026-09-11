#!/usr/bin/env bash
# Hermes Agent OS — Daily Self-Monitoring & Health Audit
# Runs daily at 06:00 IST
set -euo pipefail

WORKSPACE="/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes"
HERMES_DIR="${HOME}/.hermes"
LOGS_DIR="${HERMES_DIR}/logs"
DATE_STR="$(date +%Y-%m-%d)"
LOG_FILE="${LOGS_DIR}/daily_health_${DATE_STR}.log"

mkdir -p "${LOGS_DIR}"

echo "========================================================" > "${LOG_FILE}"
echo "Hermes Agent OS Daily Health Report — ${DATE_STR}" >> "${LOG_FILE}"
echo "Generated at: $(date -Iseconds)" >> "${LOG_FILE}"
echo "========================================================" >> "${LOG_FILE}"

# Step 1: Run native in-process capability & integrity check
echo "" >> "${LOG_FILE}"
echo "--- 1. Native Capability & Invariant Check ---" >> "${LOG_FILE}"
cd "${WORKSPACE}"
if python3 "${HERMES_DIR}/bin/verify_harness_integrity.py" --standalone >> "${LOG_FILE}" 2>&1; then
    echo "Result: PASS (All native capabilities verified green)" >> "${LOG_FILE}"
else
    echo "Result: FAIL (Anomaly detected in native capabilities)" >> "${LOG_FILE}"
fi

# Step 2: Check disk usage of cache and state.db
echo "" >> "${LOG_FILE}"
echo "--- 2. Storage & Database Footprint ---" >> "${LOG_FILE}"
du -sh "${HERMES_DIR}/cache" >> "${LOG_FILE}" 2>/dev/null || echo "Cache dir not found" >> "${LOG_FILE}"
ls -lh "${HERMES_DIR}/state.db" >> "${LOG_FILE}" 2>/dev/null || echo "state.db not found" >> "${LOG_FILE}"

# Step 3: Check experiential memory growth
echo "" >> "${LOG_FILE}"
echo "--- 3. Experiential Memory Growth ---" >> "${LOG_FILE}"
if [ -f "${HERMES_DIR}/memories/experiential.jsonl" ]; then
    BYTES=$(wc -c < "${HERMES_DIR}/memories/experiential.jsonl")
    LINES=$(wc -l < "${HERMES_DIR}/memories/experiential.jsonl")
    echo "experiential.jsonl: ${BYTES} bytes across ${LINES} sessions." >> "${LOG_FILE}"
else
    echo "experiential.jsonl: Missing or 0 bytes." >> "${LOG_FILE}"
fi

# Step 4: Capability Dashboard & AGI Equivalence Audit
echo "" >> "${LOG_FILE}"
echo "--- 4. Capability Dashboard & AGI Equivalence Snapshot ---" >> "${LOG_FILE}"
python3 "${HERMES_DIR}/bin/capability_dashboard.py" --append-log >> "${LOG_FILE}" 2>&1 || true

echo "" >> "${LOG_FILE}"
echo "Health check complete. Log saved to: ${LOG_FILE}" >> "${LOG_FILE}"
