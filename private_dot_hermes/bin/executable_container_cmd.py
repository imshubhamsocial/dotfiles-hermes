#!/usr/bin/env python3
"""
Shared Container Command Resolver
=================================
Single source of truth for reaching the `ws-ai` Distrobox container.

distrobox is natively installed on the host (`/usr/bin/distrobox`). When a
script runs directly on the host, plain `distrobox` works. When executed from
inside a sandbox/container that lacks the binary (e.g. an agent shell that
only sees distrobox's helper scripts), we bridge to the real host via
`flatpak-spawn --host distrobox` (the same shim as the user's
`~/.local/emacs-bin/distrobox` wrapper).

Use `get_distrobox_cmd()` (cached) instead of hardcoding a prefix anywhere.
"""

import shutil
import subprocess

_DISTROBOX_CMD_CACHE = None


def _resolve_distrobox_cmd():
    import os
    if os.environ.get("CONTAINER_ID") == "ws-hermes":
        return []
    if shutil.which("distrobox"):
        return ["distrobox", "enter", "ws-hermes", "--"]
    try:
        probe = subprocess.run(["flatpak-spawn", "--host", "distrobox", "--version"],
                               capture_output=True, text=True, timeout=10)
        if probe.returncode == 0 and probe.stdout.strip():
            return ["flatpak-spawn", "--host", "distrobox", "enter", "ws-hermes", "--"]
    except Exception:
        pass
    # Last resort: the harness is expected to execute ON the host, so native
    # distrobox is the correct default even if PATH detection missed it.
    return ["distrobox", "enter", "ws-hermes", "--"]


def get_distrobox_cmd():
    """Return the cached ws-ai container prefix (e.g. ['distrobox','enter','ws-ai','--'])."""
    global _DISTROBOX_CMD_CACHE
    if _DISTROBOX_CMD_CACHE is None:
        _DISTROBOX_CMD_CACHE = _resolve_distrobox_cmd()
    return list(_DISTROBOX_CMD_CACHE)


if __name__ == "__main__":
    print(" ".join(get_distrobox_cmd()))
