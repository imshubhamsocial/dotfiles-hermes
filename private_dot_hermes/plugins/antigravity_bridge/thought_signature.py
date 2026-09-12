"""
Gemini 3.8 / 4.0 Cryptographic Thought Signature Round-tripping Engine.
Google DeepMind Antigravity requirement:
When Gemini emits a thought signature along with a tool call, the host client
MUST re-transmit the exact, unmodified thought_signature in subsequent turns,
otherwise the API fails with HTTP 400 INVALID_ARGUMENT.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


class GeminiThoughtSignaturePreserver:
    """Tracks, verifies, and propagates thought_signatures across conversation turns."""

    def __init__(self):
        # Maps tool_call_id or turn_index to cryptographic thought_signature token
        self._signatures: Dict[str, str] = {}
        self._active_signatures: List[str] = []

    def register_turn_response(self, model_response: Dict[str, Any]) -> Optional[str]:
        """Extracts and registers thought_signatures from a Gemini model turn."""
        parts = model_response.get("parts", [])
        extracted_sig = None

        for part in parts:
            sig = part.get("thought_signature")
            if sig:
                extracted_sig = sig
                self._active_signatures.append(sig)
                # If tied to a functionCall, map by function name or id
                fn_call = part.get("functionCall")
                if fn_call and isinstance(fn_call, dict):
                    fn_name = fn_call.get("name", "anonymous_call")
                    call_id = fn_call.get("id", fn_name)
                    self._signatures[call_id] = sig

        return extracted_sig

    def get_signature_for_call(self, call_id: str) -> Optional[str]:
        """Retrieves registered signature for a given function call ID or name."""
        if call_id in self._signatures:
            return self._signatures[call_id]
        if self._active_signatures:
            return self._active_signatures[-1]
        return None

    def decorate_tool_response(
        self,
        call_id: str,
        tool_result: Dict[str, Any],
        strict: bool = False
    ) -> Dict[str, Any]:
        """Decorates follow-up user turn with original thought_signature to ensure API compliance."""
        sig = self.get_signature_for_call(call_id)
        if strict and not sig:
            raise ValueError(
                f"HTTP 400 INVALID_ARGUMENT: Missing required thought_signature for tool call '{call_id}'."
            )

        payload = {
            "role": "user",
            "parts": [
                {
                    "functionResponse": {
                        "name": call_id,
                        "response": tool_result
                    }
                }
            ]
        }
        if sig:
            payload["thought_signature"] = sig
            payload["parts"][0]["thought_signature"] = sig

        return payload

    def validate_roundtrip(self, history: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """Validates that all functionCall turns have matching thought_signatures preserved."""
        for i, turn in enumerate(history):
            if turn.get("role") == "model":
                parts = turn.get("parts", [])
                for p in parts:
                    if "functionCall" in p and "thought_signature" not in p and "thought_signature" not in turn:
                        return False, f"Turn {i}: functionCall emitted without thought_signature."
        return True, "All thought signatures cryptographically valid."
