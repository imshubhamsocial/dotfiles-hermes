"""
Harness Contract: Milestones U79-U80 — Speculative Tool Calling (sPTC) & Server Hardening
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".local/lib/python3.13/site-packages"))

import pytest
from hermes_core.speculative_executor import SpeculativeToolExecutor, create_speculative_executor


class TestLatencyAndHardeningContract:
    def test_speculative_programmatic_tool_calling(self):
        executor = create_speculative_executor()

        # Pure handler simulation
        def mock_read_file(query: str):
            time.sleep(0.02)
            return f"Content of {query}"

        executor.register_tool_handler("read_file", mock_read_file)

        partial_stream = "Let's inspect the target: read_file(query='src/main.py')\nNow drafting..."
        launched = executor.observe_stream_delta(partial_stream)
        assert len(launched) == 1

        # Claim the pre-executed promise
        res, was_speculated = executor.claim_or_execute("read_file", {"query": "src/main.py"})
        assert res == "Content of src/main.py"
        assert was_speculated is True

    def test_server_daemon_scripts_exist_and_executable(self):
        daemon_sh = ROOT / ".hermes" / "scripts" / "start_server_daemon.sh"
        swarm_sh = ROOT / ".hermes" / "scripts" / "start_server_swarm.sh"
        assert daemon_sh.exists()
        assert swarm_sh.exists()
        assert "taskset -c 0-11" in daemon_sh.read_text()
        assert "taskset -c 0-11" in swarm_sh.read_text()
