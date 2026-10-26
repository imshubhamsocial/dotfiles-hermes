"""Unit tests for DataPipeline (Phase 26 scenario)."""

import pytest
from scenario.data_pipeline import DataPipeline


def test_datapipeline_modern_record():
    pipeline = DataPipeline("TestEngine")
    record = {"event_id": "EVT_1001", "status": "VERIFIED", "payload": {"val": 42}}
    result = pipeline.process_record(record)
    assert result["event_id"] == "EVT_1001"
    assert result["status"] == "VERIFIED"
    assert pipeline.processed_count == 1


def test_datapipeline_legacy_record_missing_event_id():
    """Validates that legacy records missing 'event_id' do not raise KeyError."""
    pipeline = DataPipeline("LegacyIngest")
    record = {"status": "LEGACY_DATA", "payload": {"metric": "temp", "val": 28.5}}
    result = pipeline.process_record(record)
    assert result["event_id"] == "UNKNOWN"
    assert result["status"] == "LEGACY_DATA"
    assert pipeline.processed_count == 1


def test_datapipeline_batch_processing():
    pipeline = DataPipeline("BatchRunner")
    records = [
        {"event_id": "EVT_1", "status": "OK"},
        {"status": "LEGACY", "payload": "sample"},
        {"event_id": "EVT_2", "status": "OK"}
    ]
    results = pipeline.process_batch(records)
    assert len(results) == 3
    assert results[0]["event_id"] == "EVT_1"
    assert results[1]["event_id"] == "UNKNOWN"
    assert results[2]["event_id"] == "EVT_2"
