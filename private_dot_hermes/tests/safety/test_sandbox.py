#!/usr/bin/env python3
"""
Phase-3 Contract Spike: Sandbox Isolation & VRAM Bounds (U5)
============================================================
Versioned contract test for Phase 3 (roadmap §3.4-B).

  - U5 Bubblewrap Sandbox: every untrusted agent shell command executes
    inside a bwrap namespace jail. Workspace root is the ONLY writable
    mount; ~/.ssh, /etc, /var are physically absent from the mount table
    (kernel-level isolation, roadmap §3.1).
  - U5 Trap-1 Countermeasure: sandbox permission denials touching
    protected roots collapse into one canonical guidance line so a 4B
    model cannot enter sudo/chmod retry loops.
  - VRAM Guard: GPU stays within the RTX 3050 4.7 GB envelope.

Run: pytest tests/harness_contracts/test_sandbox_isolation_and_vram_bounds.py -q
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".hermes" / "src"))

from hermes_core.sandbox import (
    BWRAP_BIN,
    DEFAULT_WORKSPACE,
    SANDBOX_DENIAL_GUIDANCE,
    build_bwrap_cmd,
    run as sandbox_run,
    sanitize_output,
)


# ─── U5: Static Jail Construction ────────────────────────────────────────────

def test_bwrap_binary_present():
    assert Path(BWRAP_BIN).exists(), "bwrap binary missing; U5 cannot be enforced"


def test_build_cmd_contains_mandatory_isolation_flags():
    cmd = build_bwrap_cmd("true")
    joined = " ".join(cmd)
    for flag in ("--unshare-all", "--proc", "/proc", "--dev", "/dev",
                 "--ro-bind", "/usr", "/lib", "/lib64", "--chdir"):
        assert flag in joined or [f for f in cmd if f == flag], f"missing isolation element: {flag}"
    assert cmd[-3:-1] == ["bash", "-c"]


def test_build_cmd_never_binds_protected_roots():
    argv = [str(x) for x in build_bwrap_cmd("true")]
    for protected in ("/etc", str(Path.home() / ".ssh"), "/root"):
        bind_positions = [i for i, a in enumerate(argv) if a in ("--bind", "--ro-bind")]
        for i in bind_positions:
            assert argv[i + 2] != protected and argv[i + 1] != protected


def test_workspace_is_writable_bind():
    argv = [str(x) for x in build_bwrap_cmd("true")]
    ws = str(DEFAULT_WORKSPACE)
    assert "--bind" in argv and ws in argv


# ─── U5: Live Kernel Isolation (spec verification tests) ─────────────────────

@pytest.mark.skipif(not Path(BWRAP_BIN).exists(), reason="bwrap unavailable")
def test_etc_shadow_kernel_blocked_and_sanitized():
    rc, out = sandbox_run("cat /etc/shadow")
    assert SANDBOX_DENIAL_GUIDANCE in out, "denial must collapse to canonical guidance"
    assert "root:" not in out and "$6$" not in out, "shadow content must never leak"
    assert out.count(SANDBOX_DENIAL_GUIDANCE) == 1, "single guidance line only (no retry bait)"


@pytest.mark.skipif(not Path(BWRAP_BIN).exists(), reason="bwrap unavailable")
def test_ssh_keys_kernel_blocked_and_sanitized():
    rc, out = sandbox_run("cat ~/.ssh/id_rsa 2>&1; cat /root/.ssh/id_rsa 2>&1")
    assert SANDBOX_DENIAL_GUIDANCE in out
    assert "PRIVATE KEY" not in out, "ssh key material must never leak"


@pytest.mark.skipif(not Path(BWRAP_BIN).exists(), reason="bwrap unavailable")
def test_workspace_write_roundtrip_allowed():
    probe = DEFAULT_WORKSPACE / ".u5_probe.txt"
    rc, out = sandbox_run(f"echo u5_ok > {probe} && cat {probe}")
    assert rc == 0
    assert "u5_ok" in out
    assert probe.exists() and probe.read_text().strip() == "u5_ok"
    probe.unlink(missing_ok=True)


@pytest.mark.skipif(not Path(BWRAP_BIN).exists(), reason="bwrap unavailable")
def test_toolchain_reachable_inside_jail():
    rc, out = sandbox_run("python3 --version")
    assert rc == 0 and "Python 3" in out


@pytest.mark.skipif(not Path(BWRAP_BIN).exists(), reason="bwrap unavailable")
def test_no_retry_loop_semantics_on_repeat_attempts():
    _, first = sandbox_run("cat /etc/passwd")
    _, second = sandbox_run("cat /etc/passwd")
    assert first == second == SANDBOX_DENIAL_GUIDANCE.replace("\n", " ").strip() or \
           (SANDBOX_DENIAL_GUIDANCE in first and SANDBOX_DENIAL_GUIDANCE in second)
    assert "sudo" not in first.lower() and "chmod" not in first.lower()


# ─── U5: Sanitizer Unit Contracts ────────────────────────────────────────────

def test_sanitize_collapses_protected_denials():
    raw = "cat: /etc/shadow: No such file or directory"
    assert sanitize_output(raw) == SANDBOX_DENIAL_GUIDANCE
    raw2 = "head: cannot open '/root/.bashrc': Permission denied"
    assert sanitize_output(raw2) == SANDBOX_DENIAL_GUIDANCE


def test_sanitize_leaves_normal_errors_untouched():
    normal = "Traceback (most recent call last):\nValueError: bad input"
    assert sanitize_output(normal) == normal
    workspace_err = "cat: /dev/shm/hermes_workspace/missing.py: No such file or directory"
    assert sanitize_output(workspace_err) == workspace_err


def test_sanitize_fail_closed_without_bwrap(monkeypatch):
    from hermes_core import sandbox
    monkeypatch.setattr(sandbox, "BWRAP_BIN", "/nonexistent/bwrap")
    rc, out = sandbox.run("echo should_not_run")
    assert rc == 127
    assert "refused" in out or "unavailable" in out


# ─── VRAM Guard ──────────────────────────────────────────────────────────────

VRAM_BUDGET_MIB = 4812  # 4.7 GB RTX 3050 envelope (roadmap hardware constants)

def test_vram_within_budget():
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10,
        ).stdout.strip().splitlines()[0]
    except (FileNotFoundError, IndexError):
        pytest.skip("no NVIDIA GPU visible in this environment")
    assert int(out) <= VRAM_BUDGET_MIB, f"VRAM {out} MiB exceeds {VRAM_BUDGET_MIB} MiB budget"


# ─── U8: Byte-Static Prefix Cache Alignment ──────────────────────────────────

from hermes_core.prefix_cache import (
    PREFIX_BUDGET_TOKENS,
    PrefixCacheViolation,
    append_dynamic_tail,
    assert_byte_static,
    build_static_system_prompt,
    inject_dynamic_into_last_user_turn,
    prefix_stats,
    static_prefix_hash,
)
from hermes_core.middleware import MythosCognitiveGovernor


U8_INSTRUCTIONS = "You are @coder. Synthesize surgically via write_file and patch_file."


def _u8_static() -> str:
    return build_static_system_prompt(
        MythosCognitiveGovernor.wrap_instructions(U8_INSTRUCTIONS, coder=True)
    )


def test_u8_static_builder_deterministic_across_invocations():
    s1, s2, s3 = _u8_static(), _u8_static(), _u8_static()
    assert s1 == s2 == s3
    assert static_prefix_hash(s1) == static_prefix_hash(s2) == static_prefix_hash(s3)


def test_u8_hash_covers_prefix_window_only():
    long_instructions = (U8_INSTRUCTIONS + "\n" + "Stable law text. " * 400)
    s = build_static_system_prompt(
        MythosCognitiveGovernor.wrap_instructions(long_instructions, coder=True))
    assert len(s.encode("utf-8")) > PREFIX_BUDGET_TOKENS * 4, "test needs prompt longer than window"
    far_tail_mutated = s[:-8] + "MUTATED!"
    assert static_prefix_hash(s) == static_prefix_hash(far_tail_mutated)


def test_u8_different_instructions_produce_different_hashes():
    a = build_static_system_prompt(U8_INSTRUCTIONS)
    b = build_static_system_prompt(U8_INSTRUCTIONS.replace("coder", "architect"))
    assert static_prefix_hash(a) != static_prefix_hash(b)


def test_u8_trap1_lint_accepts_stable_and_rejects_drift():
    s = _u8_static()
    h = static_prefix_hash(s)
    assert_byte_static(s, h)  # must not raise
    drifted = s.replace("@coder", "@coder v2")
    with pytest.raises(PrefixCacheViolation):
        assert_byte_static(drifted, h)


def test_u8_dynamic_tail_lands_at_user_turn_end():
    out = append_dynamic_tail("Do the task.", "[ANCHOR]\npinned_symbol=foo")
    assert out.startswith("Do the task.") and out.endswith("pinned_symbol=foo")


def test_u8_injection_never_mutates_input_history():
    history = [
        {"role": "user", "content": "plan it"},
        {"role": "assistant", "content": "", "tool_calls": [{"id": "c1"}]},
        {"role": "tool", "tool_call_id": "c1", "content": "ok"},
    ]
    snapshot = [dict(m) for m in history]
    aug = inject_dynamic_into_last_user_turn(history, "[BOUNDARY CONSTRAINTS]\n- never X")
    assert history == snapshot, "input history was mutated"
    user_msg = next(m for m in aug if m["role"] == "user")
    assert "BOUNDARY CONSTRAINTS" in user_msg["content"]
    assert aug[-1]["role"] == "tool" and aug[-1]["content"] == "ok"


def test_u8_injection_appends_user_turn_when_last_is_toolless_assistant():
    aug = inject_dynamic_into_last_user_turn(
        [{"role": "assistant", "content": "hi"}], "[ANCHOR]")
    assert aug[-1]["role"] == "user" and "[ANCHOR]" in aug[-1]["content"]


def test_u8_injection_noop_on_empty_block():
    history = [{"role": "user", "content": "q"}]
    assert inject_dynamic_into_last_user_turn(history, "") is history
    assert inject_dynamic_into_last_user_turn(history, "   ") is history


def test_u8_prefix_stats_registry_payload_shape():
    stats = prefix_stats(_u8_static())
    assert set(stats) == {"hash", "estimated_tokens", "window_bytes"}
    assert len(stats["hash"]) == 64 and stats["window_bytes"] == PREFIX_BUDGET_TOKENS * 4
    assert stats["estimated_tokens"] > 0


# ─── U10: Hardened POSIX Process Group Teardown ──────────────────────────────

import os
import time as _time

from hermes_core.process_guard import (
    TEARDOWN_BUDGET_MS,
    _group_members_alive,
    run_with_group_teardown,
)


HANG_TREE = "sleep 311 & sleep 312 & sleep 313 & sleep 314 & sleep 315 & sleep 316"


def test_u10_fast_command_passthrough():
    rc, out, meta = run_with_group_teardown("echo u10_ok", timeout_sec=10)
    assert rc == 0 and "u10_ok" in out
    assert meta["timed_out"] is False and meta["pgid"] > 0


def test_u10_nonzero_exit_code_propagates():
    rc, _out, meta = run_with_group_teardown("exit 7", timeout_sec=10)
    assert rc == 7 and meta["timed_out"] is False


def test_u10_five_child_hang_tree_killed_within_budget():
    t0 = _time.perf_counter()
    rc, out, meta = run_with_group_teardown(HANG_TREE, timeout_sec=1.5)
    wall_ms = (_time.perf_counter() - t0) * 1000
    assert meta["timed_out"] is True and meta["killed_signal"] == "SIGKILL"
    assert meta["teardown_ms"] is not None and meta["teardown_ms"] <= TEARDOWN_BUDGET_MS, meta
    assert meta["survivors_after_kill"] == [], meta
    assert wall_ms < 4000  # no lingering wait past the kill


def test_u10_zero_survivors_in_proc_after_teardown():
    rc, _out, meta = run_with_group_teardown(HANG_TREE, timeout_sec=1.2)
    assert meta["pgid"] is not None
    assert _group_members_alive(meta["pgid"]) == []


def test_u10_group_member_scanner_detects_live_group():
    proc = subprocess.Popen(["bash", "-c", "sleep 20 & wait"],
                            stdout=subprocess.DEVNULL, start_new_session=True)
    try:
        members = []
        for _ in range(10):
            _time.sleep(0.1)
            members = _group_members_alive(proc.pid)
            if proc.pid in members and len(members) >= 2:
                break
        assert proc.pid in members and len(members) >= 2  # leader + sleep child
    finally:
        proc.kill()
        proc.wait()


def test_u10_wired_execute_command_reports_group_teardown():
    from hermes_core.tools import execute_command
    r = execute_command("sleep 30", timeout_sec=2)
    assert "U10: process group" in r and "SIGKILLed" in r and "survivors=0" in r


def test_u10_no_defunct_entries_from_teardown():
    before = _proc_zombie_count()
    run_with_group_teardown(HANG_TREE, timeout_sec=1.0)
    _time.sleep(0.3)
    assert _proc_zombie_count() <= before


def _proc_zombie_count() -> int:
    n = 0
    for pid in (p for p in os.listdir("/proc") if p.isdigit()):
        try:
            with open(f"/proc/{pid}/stat", "rb") as fh:
                stat = fh.read()
            fields = stat[stat.rindex(b")") + 2:].split()
            if fields[0] == b"Z":
                n += 1
        except (OSError, ValueError, IndexError):
            continue
    return n
