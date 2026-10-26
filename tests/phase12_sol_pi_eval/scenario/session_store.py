"""Session storage manager with time-to-live expiration."""

import time
from typing import Dict, Any, Optional


class SessionStore:
    def __init__(self, ttl_seconds: float = 300.0):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self.ttl_seconds = ttl_seconds

    def set(self, session_id: str, data: Dict[str, Any]) -> None:
        self._sessions[session_id] = {
            "data": data,
            "created_at": time.time(),
            "last_accessed": time.time()
        }

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        session = self._sessions.get(session_id)
        if session:
            session["last_accessed"] = time.time()
            return session["data"]
        return None

    def purge_expired(self, current_time: Optional[float] = None) -> int:
        now = current_time or time.time()
        purged = 0
        # BUG: Direct iteration over dict that is modified inside the loop
        # Triggers RuntimeError: dictionary changed size during iteration
        for session_id, session in list(self._sessions.items()):
            if now - session["last_accessed"] > self.ttl_seconds:
                del self._sessions[session_id]
                purged += 1
        return purged

    def count(self) -> int:
        return len(self._sessions)
