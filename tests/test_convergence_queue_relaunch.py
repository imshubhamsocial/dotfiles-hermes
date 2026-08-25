"""Offline tests for the convergence-queue AUTO-RESUME rule (Entry 60).

The 2026-08-13 reboot-crash failure mode: a dead 'running' GPU CP was never
relaunched — the queue HOLDed forever and the GPU pipeline stalled until a
session noticed. Entry 60 adds `_should_relaunch` (pure decision) + wiring in
`cmd_advance`: a running GPU cp whose driver is dead gets relaunched after a
backoff window, and NEVER on top of a live run (double-launch = rogue
processes + checkpoint contention).
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from bin import convergence_queue as CQ


def _cp(**over):
    base = {"cp": "cp1", "kind": "gpu", "script": "bin/run_hilo_full2x2.sh",
            "gate": "cells_terminal:a+b", "state": "running", "verdict": ""}
    base.update(over)
    return base


class TestShouldRelaunch(unittest.TestCase):
    def test_relaunches_dead_running_gpu_cp_after_backoff(self):
        cp = _cp(started_at="2026-08-14T00:00:00")
        with mock.patch.object(CQ, "_gpu_driver_alive", return_value=False), \
             mock.patch.object(CQ, "_gate_passed", return_value=False):
            self.assertTrue(CQ._should_relaunch(cp, "2026-08-14T00:20:00"))

    def test_never_relaunches_when_driver_alive(self):
        cp = _cp(started_at="2026-08-14T00:00:00")
        with mock.patch.object(CQ, "_gpu_driver_alive", return_value=True), \
             mock.patch.object(CQ, "_gate_passed", return_value=False):
            self.assertFalse(CQ._should_relaunch(cp, "2026-08-14T00:20:00"))

    def test_never_relaunches_when_gate_passed(self):
        cp = _cp(started_at="2026-08-14T00:00:00")
        with mock.patch.object(CQ, "_gpu_driver_alive", return_value=False), \
             mock.patch.object(CQ, "_gate_passed", return_value=True):
            self.assertFalse(CQ._should_relaunch(cp, "2026-08-14T00:20:00"))

    def test_backoff_blocks_instant_relaunch_loop(self):
        cp = _cp(started_at="2026-08-14T00:00:00")
        with mock.patch.object(CQ, "_gpu_driver_alive", return_value=False), \
             mock.patch.object(CQ, "_gate_passed", return_value=False):
            # 2 min after launch — inside the 10-min backoff → no relaunch
            self.assertFalse(CQ._should_relaunch(cp, "2026-08-14T00:02:00"))
            # 11 min after launch → relaunch allowed
            self.assertTrue(CQ._should_relaunch(cp, "2026-08-14T00:11:00"))

    def test_last_relaunch_at_resets_backoff(self):
        cp = _cp(started_at="2026-08-14T00:00:00",
                 last_relaunch_at="2026-08-14T00:09:00")
        with mock.patch.object(CQ, "_gpu_driver_alive", return_value=False), \
             mock.patch.object(CQ, "_gate_passed", return_value=False):
            self.assertFalse(CQ._should_relaunch(cp, "2026-08-14T00:10:00"))
            self.assertTrue(CQ._should_relaunch(cp, "2026-08-14T00:20:00"))

    def test_user_mark_cp_never_auto_relaunched(self):
        cp = _cp(script="user_mark", gate="user_mark")
        with mock.patch.object(CQ, "_gpu_driver_alive", return_value=False):
            self.assertFalse(CQ._should_relaunch(cp, "2026-08-14T00:20:00"))

    def test_non_gpu_or_scriptless_never_relaunched(self):
        for over in ({"kind": "build"}, {"script": ""}):
            cp = _cp(**over)
            with mock.patch.object(CQ, "_gpu_driver_alive", return_value=False), \
                 mock.patch.object(CQ, "_gate_passed", return_value=False):
                self.assertFalse(CQ._should_relaunch(cp, "2026-08-14T00:20:00"))

    def test_missing_timestamp_allows_first_check(self):
        cp = _cp()  # no started_at
        with mock.patch.object(CQ, "_gpu_driver_alive", return_value=False), \
             mock.patch.object(CQ, "_gate_passed", return_value=False):
            self.assertTrue(CQ._should_relaunch(cp, "2026-08-14T00:20:00"))


class TestAdvanceReload(unittest.TestCase):
    """cmd_advance end-to-end against a temp state file (no real processes)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._state = Path(self._tmp.name) / "CONVERGENCE_QUEUE.json"
        patcher = mock.patch.object(CQ, "STATE", self._state)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self._tmp.cleanup)

    def _write(self, queue):
        CQ._atomic_write(self._state, {"meta": {}, "queue": queue})

    def test_advance_relaunches_dead_running_cp(self):
        self._write([_cp(started_at="2026-08-14T00:00:00")])
        with mock.patch.object(CQ, "_gpu_driver_alive", return_value=False), \
             mock.patch.object(CQ, "_gate_passed", return_value=False), \
             mock.patch.object(CQ, "_launch") as launch:
            CQ.cmd_advance()
            launch.assert_called_once()  # the AUTO-RESUME decision fired
        d = CQ._load()
        # state stays "running" (the relaunch re-launches the same cp); the
        # backoff timestamp is written by the real _launch (mocked here)
        self.assertEqual(d["queue"][0]["state"], "running")

    def test_advance_holds_when_driver_alive(self):
        self._write([_cp(started_at="2026-08-14T00:00:00")])
        with mock.patch.object(CQ, "_gpu_driver_alive", return_value=True), \
             mock.patch.object(CQ, "_gate_passed", return_value=False), \
             mock.patch.object(CQ, "_launch") as launch:
            CQ.cmd_advance()
            launch.assert_not_called()

    def test_advance_completes_on_gate_passed(self):
        self._write([_cp(started_at="2026-08-14T00:00:00")])
        with mock.patch.object(CQ, "_gate_passed", return_value=True), \
             mock.patch.object(CQ, "_launch") as launch:
            CQ.cmd_advance()
            launch.assert_not_called()
        d = CQ._load()
        self.assertEqual(d["queue"][0]["state"], "done")
        self.assertEqual(d["queue"][0]["verdict"], "gate-passed")

    def test_advance_holds_within_backoff(self):
        self._write([_cp(started_at="2026-08-14T00:00:00")])
        # now == started_at → inside backoff
        with mock.patch.object(CQ, "time") as fake_time, \
             mock.patch.object(CQ, "_gpu_driver_alive", return_value=False), \
             mock.patch.object(CQ, "_gate_passed", return_value=False), \
             mock.patch.object(CQ, "_launch") as launch:
            fake_time.strftime.return_value = "2026-08-14T00:01:00"
            CQ.cmd_advance()
            launch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
