"""Offline tests for the convergence-queue staleness/zombie hardening
(2026-08-15 driver-death audit).

The failure: every driver death was rc=143 (SIGTERM) with no swap-abort/OOM/
journald trace, and the queue's `_gpu_driver_alive()` used bare `pgrep -f` —
a DEFUNCT (zombie) process still matches pgrep, so an orphaned driver
blocked auto-resume for 2h23m (18:53:57 → 21:16:44) purely by existing.

The fix: (1) zombies never count as alive, (2) a non-zombie driver that has
written no checkpoint for STALE_DRIVER_S is stalled, not working — the queue
must relaunch it (resume-safe), and (3) `_cleanup_stale_drivers()` SIGKILLs
zombie/stalled pids before a relaunch so the new chain's single-run guard
never ABORTs on the leftover.

Deterministic by construction: temp RESULTS dir, synthetic checkpoints,
mocked pgrep/zombie/stale primitives — no real processes, no network.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from bin import convergence_queue as CQ  # noqa: E402


def _write_checkpoint(results: Path, run_dir: str, age_s: float) -> None:
    """Write a synthetic checkpoint with `age_s`-old mtime (now - age_s)."""
    rd = results / run_dir
    rd.mkdir(parents=True, exist_ok=True)
    ck = rd / "checkpoint.json"
    ck.write_text(json.dumps({"cells": {}}), encoding="utf-8")
    import time as _t
    os.utime(ck, (_t.time() - age_s, _t.time() - age_s))


class TestGpuDriverAlive(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._results = Path(self._tmp.name)
        patcher = mock.patch.object(CQ, "RESULTS", self._results)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self._tmp.cleanup)

    def test_no_driver_pids_false(self):
        with mock.patch.object(CQ, "_driver_pids", return_value=[]):
            self.assertFalse(CQ._gpu_driver_alive())

    def test_zombie_never_counts_as_alive(self):
        """A defunct process matches pgrep but can never do work — the exact
        2h23m HOLD bug. Zombie pids must be ignored entirely."""
        _write_checkpoint(self._results, "run_hilo_fleet_thinking_long", 10)
        with mock.patch.object(CQ, "_driver_pids", return_value=[1234]), \
             mock.patch.object(CQ, "_pid_is_zombie", return_value=True):
            self.assertFalse(CQ._gpu_driver_alive())

    def test_mixed_zombie_and_live_driver_is_alive(self):
        """One live (non-zombie, fresh-checkpoint) driver = alive even if a
        zombie sibling lingers."""
        _write_checkpoint(self._results, "run_hilo_fleet_thinking_long", 10)
        with mock.patch.object(CQ, "_driver_pids", return_value=[111, 222]), \
             mock.patch.object(CQ, "_pid_is_zombie",
                               side_effect=lambda p: p == 111):
            self.assertTrue(CQ._gpu_driver_alive())

    def test_live_driver_with_fresh_checkpoint_alive(self):
        _write_checkpoint(self._results, "run_hilo_fleet_thinking_long", 10)
        with mock.patch.object(CQ, "_driver_pids", return_value=[1234]), \
             mock.patch.object(CQ, "_pid_is_zombie", return_value=False):
            self.assertTrue(CQ._gpu_driver_alive())

    def test_stalled_driver_not_alive(self):
        """A non-zombie driver that has written NO checkpoint for
        STALE_DRIVER_S is hung, not working — the queue must relaunch."""
        _write_checkpoint(self._results, "run_hilo_fleet_thinking_long",
                          CQ.STALE_DRIVER_S + 60)
        with mock.patch.object(CQ, "_driver_pids", return_value=[1234]), \
             mock.patch.object(CQ, "_pid_is_zombie", return_value=False):
            self.assertFalse(CQ._gpu_driver_alive())

    def test_fresh_checkpoint_any_dir_counts(self):
        """Progress in ANY run dir proves a driver is working (the stall test
        scans all checkpoints under RESULTS)."""
        _write_checkpoint(self._results, "run_hilo_fleet_thinking_short", 5)
        with mock.patch.object(CQ, "_driver_pids", return_value=[1234]), \
             mock.patch.object(CQ, "_pid_is_zombie", return_value=False):
            self.assertTrue(CQ._gpu_driver_alive())

    def test_no_checkpoints_at_all_counts_stale(self):
        """No checkpoint anywhere → newest mtime 0 → stale (a driver that
        never wrote anything cannot be trusted as working)."""
        with mock.patch.object(CQ, "_driver_pids", return_value=[1234]), \
             mock.patch.object(CQ, "_pid_is_zombie", return_value=False):
            self.assertFalse(CQ._gpu_driver_alive())


class TestCleanupStaleDrivers(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._results = Path(self._tmp.name)
        patcher = mock.patch.object(CQ, "RESULTS", self._results)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self._tmp.cleanup)

    def test_kills_zombie_pids(self):
        import signal as _sig
        _write_checkpoint(self._results, "run_hilo_fleet_thinking_long", 10)
        with mock.patch.object(CQ, "_driver_pids", return_value=[999]), \
             mock.patch.object(CQ, "_pid_is_zombie", return_value=True), \
             mock.patch.object(CQ, "os") as mock_os:
            CQ._cleanup_stale_drivers()
            mock_os.kill.assert_called_once_with(999, _sig.SIGKILL)

    def test_kills_stalled_live_pid(self):
        import signal as _sig
        _write_checkpoint(self._results, "run_hilo_fleet_thinking_long",
                          CQ.STALE_DRIVER_S + 60)
        with mock.patch.object(CQ, "_driver_pids", return_value=[999]), \
             mock.patch.object(CQ, "_pid_is_zombie", return_value=False), \
             mock.patch.object(CQ, "os") as mock_os:
            CQ._cleanup_stale_drivers()
            mock_os.kill.assert_called_once_with(999, _sig.SIGKILL)

    def test_never_touches_fresh_driver(self):
        _write_checkpoint(self._results, "run_hilo_fleet_thinking_long", 5)
        with mock.patch.object(CQ, "_driver_pids", return_value=[999]), \
             mock.patch.object(CQ, "_pid_is_zombie", return_value=False), \
             mock.patch.object(CQ, "os") as mock_os:
            CQ._cleanup_stale_drivers()
            mock_os.kill.assert_not_called()

    def test_kill_missing_pid_is_safe(self):
        """A pid that vanished between pgrep and kill must not raise."""
        _write_checkpoint(self._results, "run_hilo_fleet_thinking_long", 10)

        def _raise(*a, **k):
            raise ProcessLookupError

        with mock.patch.object(CQ, "_driver_pids", return_value=[999]), \
             mock.patch.object(CQ, "_pid_is_zombie", return_value=True), \
             mock.patch.object(CQ, "os") as mock_os:
            mock_os.kill.side_effect = _raise
            CQ._cleanup_stale_drivers()  # must not raise


class TestAdvanceReloadWithStaleDriver(unittest.TestCase):
    """cmd_advance end-to-end: a STALE (non-zombie) driver must trigger
    AUTO-RESUME (not HOLD) and the cleanup must run before launch."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._state = Path(self._tmp.name) / "CONVERGENCE_QUEUE.json"
        self._results = Path(self._tmp.name) / "results"
        patcher = mock.patch.object(CQ, "STATE", self._state)
        patcher.start()
        self.addCleanup(patcher.stop)
        p2 = mock.patch.object(CQ, "RESULTS", self._results)
        p2.start()
        self.addCleanup(p2.stop)

    def _cp(self, **over):
        base = {"cp": "cp1", "kind": "gpu", "script": "bin/run_hilo_full2x2.sh",
                "gate": "cells_terminal:a+b", "state": "running", "verdict": "",
                "started_at": "2026-08-14T00:00:00"}
        base.update(over)
        return base

    def test_stale_driver_auto_resumes_and_cleans_up(self):
        CQ._atomic_write(self._state, {"meta": {}, "queue": [self._cp()]})
        _write_checkpoint(self._results, "run_hilo_fleet_thinking_long",
                          CQ.STALE_DRIVER_S + 60)
        with mock.patch.object(CQ, "_driver_pids", return_value=[444187]), \
             mock.patch.object(CQ, "_pid_is_zombie", return_value=False), \
             mock.patch.object(CQ, "_gate_passed", return_value=False), \
             mock.patch.object(CQ, "_cleanup_stale_drivers") as cleanup, \
             mock.patch.object(CQ, "_launch") as launch:
            CQ.cmd_advance()
            launch.assert_called_once()
            cleanup.assert_called_once()


if __name__ == "__main__":
    unittest.main()
