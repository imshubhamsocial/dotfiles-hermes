"""Data pipeline for streaming telemetry records."""

from typing import Dict, Any, List, Optional


class DataPipeline:
    def __init__(self):
        self.processed_count = 0

    def process_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Processes a telemetry record.
        
        Expected payload format:
        {
            "metadata": {"source": "..."},
            "metrics": [{"name": "cpu", "value": 0.5}],
            "payload": {
                "events": [{"event_id": "e1", "type": "heartbeat"}]
            }
        }
        """
        if not record or not isinstance(record, dict):
            return {"status": "skipped", "error": "empty_record"}

        events = record.get("payload", {}).get("events", [])
        if not events:
            return {"status": "empty_events"}

        first_event = events[0]
        event_id = first_event.get("event_id") or first_event.get("id", "UNKNOWN")

        self.processed_count += 1
        return {
            "status": "ok",
            "event_id": event_id,
            "metric_count": len(record.get("metrics", []))
        }
