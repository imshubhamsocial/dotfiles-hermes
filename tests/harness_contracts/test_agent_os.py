"""
Contract Spike: Phase 7 Persistent Agent OS Daemon & Event Dispatch
====================================================================
Tests task submission, event queue processing, failure handling,
and 7-layer system status reporting.
"""

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import pytest

from hermes_core.agent_os import (
    AgentEvent,
    AgentOSDaemon,
    create_agent_os_daemon,
)


def test_agent_os_event_lifecycle_and_dispatch():
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td) / "workspace"
        ws.mkdir()
        db_p = Path(td) / "os_exp.json"
        
        daemon = create_agent_os_daemon(workspace_root=ws, db_path=db_p, mode="supervised")
        
        # Submit task event
        evt_task = daemon.submit_task("t100", "Build parser", "Implement parser")
        assert evt_task.event_type == "TASK_SUBMITTED"
        
        # Git trigger event
        evt_git = daemon.on_git_event("push", "commit_abc123")
        assert evt_git.event_type == "GIT_EVENT"
        
        # Schedule cron tick
        evt_cron = daemon.on_schedule_tick()
        assert evt_cron.event_type == "SCHEDULE_TICK"
        
        # Process pending events
        processed = daemon.process_all_events()
        assert len(processed) == 3
        
        status = daemon.get_system_status()
        assert status["status"] == "HEALTHY"
        assert status["processed_events_count"] == 3
        assert status["pending_events"] == 0


def test_agent_os_failure_handling_and_recovery():
    with tempfile.TemporaryDirectory() as td:
        ws = Path(td) / "workspace"
        ws.mkdir()
        db_p = Path(td) / "os_fail.json"
        
        daemon = create_agent_os_daemon(workspace_root=ws, db_path=db_p, mode="yolo")
        
        daemon.on_task_failure("t_fail_1", "SyntaxError: Unexpected token '}'")
        daemon.process_all_events()
        
        status = daemon.get_system_status()
        assert status["total_episodes_recorded"] == 1
        assert status["negative_constraints_active"] >= 1
