#!/usr/bin/env bash
# Substrate reconnaissance: search and install -devel packages in Fedora distrobox
set -euo pipefail

PKG="${1:-}"
if [ -z "$PKG" ]; then
    echo "Usage: $0 <package-name>" >&2
    exit 1
fi

echo "==> Searching for '$PKG' packages..."
# Limit output to fit in SWE-agent 512-char observation window
dnf search "$PKG" --quiet 2>/dev/null | grep -i "devel\|lib" | head -10 || true

echo "==> Installed status:"
rpm -qa | grep -i "$PKG" || echo "None currently installed"
