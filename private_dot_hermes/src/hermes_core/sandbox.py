"""
U5 OS-Level Bubblewrap Sandboxing (Phase 3.1)
=============================================
Wraps every untrusted agent shell command in a bubblewrap namespace jail
(OpenAI Codex :workspace profile, roadmap §3.1):

  - ONLY the workspace root and /tmp are writable mounts.
  - ~/.ssh, /etc, /var, /root are never entered into the mount table,
    so access attempts fail at the KERNEL layer (physically absent paths).
  - --unshare-all severs network/PID/IPC/user namespaces from the host.
  - --share-net retains network namespace (required in containerized envs).

Trap-1 countermeasure (Permission Error Hallucination Loops): sandbox
denials are sanitized to a single canonical guidance line so a 4B model
cannot enter sudo/chmod retry loops on blocked system paths.

Fail-closed policy: if the bwrap binary is missing, execution is REFUSED
(never silently downgraded to an unsandboxed shell).
"""

import shutil
import subprocess
from pathlib import Path

BWRAP_BIN = shutil.which("bwrap") or "/usr/bin/bwrap"
DEFAULT_WORKSPACE = Path("/dev/shm/hermes_workspace")

SANDBOX_DENIAL_GUIDANCE = (
    "Environment is strictly isolated to workspace root. "
    "Modify paths relative to active project."
)

_PROTECTED_MARKERS = ("/etc", "/root", "/var", "/proc/sys", ".ssh")
_DENIAL_MARKERS = (
    "permission denied",
    "no such file or directory",
    "operation not permitted",
    "read-only file system",
)


def build_bwrap_cmd(command: str, workspace: Path = DEFAULT_WORKSPACE) -> list:
    """Assemble the bwrap argv for one untrusted shell command."""
    ws = str(workspace)
    return [
        BWRAP_BIN,
        "--ro-bind", "/usr", "/usr",
        "--ro-bind", "/lib", "/lib",
        "--ro-bind", "/lib64", "/lib64",
        "--proc", "/proc",
        "--dev", "/dev",
        "--bind", "/tmp", "/tmp",
        "--bind", ws, ws,
        "--chdir", ws,
        "--unshare-all",
        "--share-net",
        "--die-with-parent",
        "bash", "-c", command,
    ]


def sanitize_output(output: str) -> str:
    """Collapse kernel denials touching protected roots into canonical guidance."""
    # Check for bwrap NETLINK/loopback errors (container environment)
    if "loopback" in output.lower() and "netlink" in output.lower():
        return SANDBOX_DENIAL_GUIDANCE
    
    if any(p in output for p in _PROTECTED_MARKERS) and any(
        m in output.lower() for m in _DENIAL_MARKERS
    ):
        return SANDBOX_DENIAL_GUIDANCE
    return output


def run(command: str, timeout_sec: int = 120, workspace: Path = DEFAULT_WORKSPACE) -> tuple:
    """Execute one command inside the jail. Returns (returncode, sanitized_output)."""
    try:
        workspace.mkdir(parents=True, exist_ok=True)
        res = subprocess.run(
            build_bwrap_cmd(command, workspace),
            capture_output=True, text=True, timeout=timeout_sec,
        )
        return res.returncode, sanitize_output((res.stdout + res.stderr).strip())
    except subprocess.TimeoutExpired:
        return 124, f"Error: Command timed out after {timeout_sec}s."
    except FileNotFoundError:
        return 127, "Error: U5 sandbox unavailable (bwrap binary not found); execution refused."


if __name__ == "__main__":
    rc, out = run("ls -la && python3 --version")
    print(f"rc={rc}\n{out}")
