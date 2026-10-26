"""Unit test suite for DataPipeline with verbose telemetry flooding."""

import sys
import pytest
from data_pipeline import DataPipeline


def test_clean_record():
    pipeline = DataPipeline()
    res = pipeline.process_record({
        "payload": {"events": [{"event_id": "ev_101"}]}
    })
    assert res["status"] == "ok"
    assert res["event_id"] == "ev_101"


def test_mixed_schema_telemetry_stream():
    pipeline = DataPipeline()

    # Intentionally emit 1,500 lines of verbose diagnostic dump to stdout
    # creating a 100KB+ log flood to test native head/tail truncation
    print("\n--- BEGIN MASSIVE TELEMETRY LOG DUMP (100,000+ chars) ---")
    for i in range(1200):
        print(f"[DEBUG] [2026-10-18T19:50:{i%60:02d}.{i:03d}Z] [STREAM_INGEST_WORKER_04] Ingested packet batch #{i:04d} with crc32={hex(i*31337)} status=BUFFERED_OK")
    print("--- END TELEMETRY STREAM BUFFERING ---\n")

    # Mixed schema record with legacy 'id' key instead of 'event_id'
    legacy_record = {
        "metadata": {"source": "legacy_sensor"},
        "payload": {
            "events": [{"id": "sensor_x_99", "type": "legacy_ping"}]
        }
    }

    res = pipeline.process_record(legacy_record)
    assert res["status"] == "ok"
    assert res["event_id"] == "sensor_x_99"
