"""
Contract Tests: TrajectoryRecorder & Session Observability Engine
================================================================
Verifies SQLite WAL persistence, SWE-agent observation windowing,
learnability frontier filtering ([0.3, 0.7]), and JSONL dataset export.
"""

import json
from pathlib import Path
import pytest

from plugins.trajectory_recorder import TrajectoryRecorder


@pytest.fixture
def recorder(tmp_path: Path) -> TrajectoryRecorder:
    db_file = tmp_path / "test_trajectories.db"
    return TrajectoryRecorder(db_path=db_file)


class TestTrajectoryRecorder:
    def test_observation_windowing_under_threshold(self):
        short_output = "Line 1\nLine 2\nLine 3"
        windowed = TrajectoryRecorder.window_observation(short_output, max_lines=50)
        assert windowed == short_output

    def test_observation_windowing_over_threshold(self):
        long_lines = [f"Output row {i}" for i in range(100)]
        long_output = "\n".join(long_lines)
        windowed = TrajectoryRecorder.window_observation(long_output, max_lines=50)

        assert "Output row 0" in windowed
        assert "Output row 24" in windowed
        assert "Output row 99" in windowed
        assert "[... 50 lines truncated by observation windowing ...]" in windowed
        assert "Output row 50" not in windowed

    def test_record_turn_and_session_retrieval(self, recorder: TrajectoryRecorder):
        sid = "test_session_001"
        row_id = recorder.record_turn(
            session_id=sid,
            turn_index=1,
            role="coder",
            prompt="Write a function to add two numbers",
            reasoning_trace="Analyzing problem: addition requires a + b.",
            tool_name="edit_file",
            tool_args={"path": "calc.py"},
            tool_output="File updated successfully.",
            test_status="PASS",
            constitutional_score=0.9,
        )
        assert row_id > 0

        turns = recorder.get_session(sid)
        assert len(turns) == 1
        assert turns[0]["turn_index"] == 1
        assert turns[0]["tool_name"] == "edit_file"
        assert turns[0]["constitutional_score"] == 0.9
        assert turns[0]["test_status"] == "PASS"

    def test_learnability_frontier_filtering(self, recorder: TrajectoryRecorder):
        # 1. Easy task (high score 0.95 - outside frontier)
        recorder.record_turn(session_id="s_easy", turn_index=1, constitutional_score=0.95)
        # 2. Hard task (low score 0.1 - outside frontier)
        recorder.record_turn(session_id="s_hard", turn_index=1, constitutional_score=0.1)
        # 3. Frontier task (medium score 0.55 - inside frontier [0.3, 0.7])
        recorder.record_turn(session_id="s_frontier", turn_index=1, constitutional_score=0.55)

        all_items = recorder.list_trajectories(limit=10, frontier_only=False)
        assert len(all_items) == 3

        frontier_items = recorder.list_trajectories(limit=10, frontier_only=True)
        assert len(frontier_items) == 1
        assert frontier_items[0]["session_id"] == "s_frontier"

    def test_dataset_export_jsonl(self, recorder: TrajectoryRecorder, tmp_path: Path):
        recorder.record_turn(
            session_id="s_exp",
            turn_index=1,
            prompt="Refactor authentication",
            reasoning_trace="JWT token verification needed.",
            tool_name="bash",
            tool_args={"cmd": "pytest"},
            tool_output="1 passed",
            constitutional_score=0.6,
        )
        recorder.end_session("s_exp", final_status="SUCCESS")

        out_file = tmp_path / "export.jsonl"
        count = recorder.export_dataset(out_file, frontier_only=True)
        assert count == 1
        assert out_file.exists()

        data = json.loads(out_file.read_text().strip())
        assert data["session_id"] == "s_exp"
        assert len(data["conversations"]) == 1
        assert data["conversations"][0]["score"] == 0.6
