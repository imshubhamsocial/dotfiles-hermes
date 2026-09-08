"""
Contract Tests for Milestone U6 & D7-10: OpenLIT & OpenTelemetry Custom Spans for Trajectory
===========================================================================================
Validates:
  1. OpenLIT & OpenTelemetry initialization helper (init_observability).
  2. TrajectoryRecorder hash-chain events wrapped as OTel custom spans.
  3. Span attributes matching hash-chain headers (seq, hash, prev, session) and LLM conventions.
  4. OTel error status mapping for failed tests, gate rejections, and tool errors.
  5. trace_span context manager auto-sealing trajectory events upon exit.
  6. events_to_otel_spans historical trace export.
  7. Replay runner emitting OTel spans during trajectory replay.
  8. Preserved hash-chain immutability and tamper resistance.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".hermes" / "src"))

import pytest
from opentelemetry.trace import StatusCode
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from hermes_core.trajectory import (
    TrajectoryRecorder,
    init_observability,
    get_trajectory_tracer,
    verify_chain,
    load_events,
    events_to_otel_spans,
    OPENLIT_AVAILABLE,
    OPENTELEMETRY_AVAILABLE,
)
from hermes_core.replay import replay_trajectory, export_replay_to_otel_spans

TEST_PROVIDER = TracerProvider()
TEST_EXPORTER = InMemorySpanExporter()
TEST_PROVIDER.add_span_processor(SimpleSpanProcessor(TEST_EXPORTER))
TEST_TRACER = TEST_PROVIDER.get_tracer("hermes.test.trajectory")


@pytest.fixture
def otel_test_env():
    """Provides an isolated InMemorySpanExporter and Tracer for contract testing."""
    TEST_EXPORTER.clear()
    return TEST_EXPORTER, TEST_TRACER


class TestTrajectoryOpenLITIntegration:
    """Test suite for D7-10 OpenLIT and OpenTelemetry custom span wrapping."""

    def test_observability_availability_flags(self):
        assert isinstance(OPENLIT_AVAILABLE, bool)
        assert isinstance(OPENTELEMETRY_AVAILABLE, bool)
        assert OPENTELEMETRY_AVAILABLE is True

    def test_init_observability_respects_disabled_env(self, monkeypatch):
        monkeypatch.setenv("HERMES_OTEL_DISABLED", "1")
        assert init_observability() is False
        assert get_trajectory_tracer() is None

    def test_trajectory_recorder_emits_custom_spans(self, otel_test_env):
        exporter, tracer = otel_test_env
        with tempfile.TemporaryDirectory() as td:
            traj_path = Path(td) / "trajectory.jsonl"
            rec = TrajectoryRecorder(session_id="otel-session-01", path=traj_path, tracer=tracer)

            # 1. Turn start event
            ev1 = rec.record_turn(turn=1, role="architect", prompt_tokens=1250)
            assert ev1["seq"] == 0
            assert len(ev1["hash"]) == 64

            # 2. Gate check PASS
            ev2 = rec.record_gate(turn=1, tool="file_edit", gate_status="PASS")
            assert ev2["seq"] == 1
            assert ev2["prev"] == ev1["hash"]

            # 3. Tool result OK
            ev3 = rec.record_tool_result(
                turn=1, tool="file_edit", result_head="File written successfully", result_ok=True
            )
            assert ev3["seq"] == 2

            # 4. Test failure
            ev4 = rec.record_test(turn=1, test_passed=False, command="pytest tests/unit")
            assert ev4["seq"] == 3

            # Verify on-disk hash chain
            ok, detail = verify_chain(traj_path)
            assert ok is True
            assert "chain intact: 4 events" in detail

            # Verify emitted OTel custom spans
            spans = exporter.get_finished_spans()
            assert len(spans) == 4

            # Verify span 0: turn_start
            s0 = spans[0]
            assert s0.name == "hermes.trajectory.turn_start"
            assert s0.attributes["hermes.session"] == "otel-session-01"
            assert s0.attributes["hermes.seq"] == 0
            assert s0.attributes["hermes.hash"] == ev1["hash"]
            assert s0.attributes["hermes.prev"] == "GENESIS"
            assert s0.attributes["hermes.role"] == "architect"
            assert s0.attributes["gen_ai.usage.prompt_tokens"] == 1250
            assert s0.status.status_code == StatusCode.OK

            # Verify span 1: gate_check
            s1 = spans[1]
            assert s1.name == "hermes.trajectory.gate_check"
            assert s1.attributes["hermes.seq"] == 1
            assert s1.attributes["hermes.gate_status"] == "PASS"
            assert s1.status.status_code == StatusCode.OK

            # Verify span 3: test_result (Failed -> StatusCode.ERROR)
            s3 = spans[3]
            assert s3.name == "hermes.trajectory.test_result"
            assert s3.attributes["hermes.seq"] == 3
            assert s3.attributes["hermes.test_passed"] is False
            assert s3.status.status_code == StatusCode.ERROR

    def test_gate_reject_sets_span_error_status(self, otel_test_env):
        exporter, tracer = otel_test_env
        with tempfile.TemporaryDirectory() as td:
            traj_path = Path(td) / "trajectory.jsonl"
            rec = TrajectoryRecorder(session_id="gate-test", path=traj_path, tracer=tracer)
            rec.record_gate(turn=1, tool="rm_rf", gate_status="REJECT", reason="Blocked unsafe command")

            spans = exporter.get_finished_spans()
            assert len(spans) == 1
            assert spans[0].name == "hermes.trajectory.gate_check"
            assert spans[0].status.status_code == StatusCode.ERROR
            assert spans[0].status.description == "Blocked unsafe command"

    def test_trace_span_context_manager(self, otel_test_env):
        exporter, tracer = otel_test_env
        with tempfile.TemporaryDirectory() as td:
            traj_path = Path(td) / "trajectory.jsonl"
            rec = TrajectoryRecorder(session_id="ctx-test", path=traj_path, tracer=tracer)

            with rec.trace_span("tool_call", turn=2, role="coder", tool="bash") as fields:
                fields["args_head"] = "echo 'hello'"
                fields["extra_metric"] = 42

            events = load_events(traj_path)
            assert len(events) == 1
            assert events[0]["event"] == "tool_call"
            assert events[0]["args_head"] == "echo 'hello'"
            assert events[0]["extra_metric"] == 42

            spans = exporter.get_finished_spans()
            assert len(spans) == 1
            assert spans[0].name == "hermes.trajectory.tool_call"
            assert spans[0].attributes["hermes.tool"] == "bash"

    def test_events_to_otel_spans_export(self, otel_test_env):
        exporter, tracer = otel_test_env
        with tempfile.TemporaryDirectory() as td:
            traj_path = Path(td) / "trajectory.jsonl"
            rec = TrajectoryRecorder(session_id="export-test", path=traj_path, enable_otel=False)
            rec.record_turn(turn=1, role="tester")
            rec.record_test(turn=1, test_passed=True)

            # Initially no spans because enable_otel=False
            assert len(exporter.get_finished_spans()) == 0

            # Export historical events to OTel spans
            events = load_events(traj_path)
            count = events_to_otel_spans(events, tracer=tracer)
            assert count == 2

            spans = exporter.get_finished_spans()
            assert len(spans) == 2
            assert spans[0].name == "hermes.trajectory.turn_start"
            assert spans[1].name == "hermes.trajectory.test_result"

    def test_replay_with_otel_tracing(self, otel_test_env):
        exporter, tracer = otel_test_env
        with tempfile.TemporaryDirectory() as td:
            traj_path = Path(td) / "trajectory.jsonl"
            rec = TrajectoryRecorder(session_id="replay-test", path=traj_path, tracer=tracer)
            rec.record_tool_call(turn=1, role="coder", tool="echo", args_head='{"text": "hi"}')
            rec.record_gate(turn=1, tool="echo", gate_status="PASS")
            rec.record_tool_result(turn=1, tool="echo", result_head="hi", result_ok=True)

            # Clear spans from recording phase
            exporter.clear()

            # Run replay with tracer
            report = replay_trajectory(traj_path, tracer=tracer)
            assert report.total_events == 3
            assert report.replayed_steps == 1

            # Check exported replay report spans
            export_count = export_replay_to_otel_spans(report, tracer=tracer)
            assert export_count == 1

            spans = [s for s in exporter.get_finished_spans() if s.name.startswith("hermes.replay")]
            assert len(spans) >= 2  # step span + summary span
            replay_step_spans = [s for s in spans if "step" in s.name]
            assert len(replay_step_spans) >= 1
            assert replay_step_spans[0].attributes["hermes.replay.tool"] == "echo"
            assert replay_step_spans[0].attributes["hermes.replay.drift"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
