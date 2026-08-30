"""
Post-Turn Integrity Hook (Roadmap 6 - Milestone 1)
=================================================
Executes after every agent turn to append deterministic SHA256 hashes to the session sidecar.
"""

import hashlib
import json
import os
from pathlib import Path


def on_turn_complete(session_id: str, turn_index: int, turn_data: dict | str, logs_dir: Path | None = None) -> str:
    """Appends the SHA256 of the completed turn to the session integrity sidecar."""
    if logs_dir is None:
        logs_dir = Path.home() / ".hermes/logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    sidecar_path = logs_dir / f"{session_id}.integrity"

    if isinstance(turn_data, dict):
        line = json.dumps(turn_data, sort_keys=True)
    else:
        line = str(turn_data).strip()

    h = hashlib.sha256(line.encode("utf-8")).hexdigest()

    with open(sidecar_path, "a", encoding="utf-8") as sf:
        sf.write(f"{turn_index}:{h}\n")

    return h


if __name__ == "__main__":
    # Self-test
    test_hash = on_turn_complete("test_session_sample", 0, {"role": "assistant", "content": "test turn"})
    print(f"Hook self-test OK. Turn 0 hash: {test_hash}")
