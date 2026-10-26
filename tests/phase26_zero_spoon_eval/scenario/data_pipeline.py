"""DataPipeline telemetry processor module (Phase 26 scenario)."""

from typing import Any


class DataPipeline:
    """Processes legacy and modern telemetry event records."""

    def __init__(self, pipeline_name: str = "TelemetryIngest"):
        self.pipeline_name = pipeline_name
        self.processed_count = 0

    def process_record(self, record: dict[str, Any]) -> dict[str, Any]:
        """Process a single telemetry record dictionary.
        
        Legacy records may lack 'event_id' which causes KeyError defect unless safely accessed.
        """
        # Defect: direct dict indexing raises KeyError on missing legacy event_id
        event_id = record.get("event_id", "UNKNOWN")
        payload = record.get("payload", {})
        status = record.get("status", "ACTIVE")

        self.processed_count += 1
        return {
            "pipeline": self.pipeline_name,
            "event_id": event_id,
            "status": status,
            "payload_size": len(str(payload)),
        }

    def process_batch(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Process an entire batch of telemetry event records."""
        return [self.process_record(r) for r in records]
