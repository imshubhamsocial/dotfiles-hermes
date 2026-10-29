#!/usr/bin/env python3
"""
Hermes 60% Infrastructure Gate: Sliding-Window Shannon Entropy Watchdog
Monitors streaming generation tokens to prevent infinite loops (e.g. HumanEval/130).
Fires POST http://127.0.0.1:8138/slots/0?action=erase and truncates at AST boundary.
"""
import ast
import math
import sys
import urllib.error
import urllib.request
from collections import Counter


class SlidingWindowShannonEntropyWatchdog:
    """
    Sliding-window monitor calculating 4-gram repetition ratio and Shannon entropy.
    """

    def __init__(
        self,
        window_size: int = 64,
        check_interval: int = 16,
        max_repetition_ratio: float = 0.85,
        min_shannon_entropy: float = 1.5,
        consecutive_triggers_required: int = 2,
        server_url: str = "http://127.0.0.1:8138",
    ) -> None:
        self.window_size = window_size
        self.check_interval = check_interval
        self.max_repetition_ratio = max_repetition_ratio
        self.min_shannon_entropy = min_shannon_entropy
        self.consecutive_triggers_required = consecutive_triggers_required
        self.server_url = server_url.rstrip("/")

        self.token_buffer: list[str] = []
        self.text_buffer: str = ""
        self.tokens_since_check: int = 0
        self.consecutive_loop_violations: int = 0
        self.loop_detected: bool = False

    @staticmethod
    def calculate_4gram_repetition_ratio(text: str) -> float:
        """Calculate character 4-gram repetition ratio."""
        if len(text) < 4:
            return 0.0
        grams = [text[i : i + 4] for i in range(len(text) - 3)]
        total = len(grams)
        unique = len(set(grams))
        return (total - unique) / total if total > 0 else 0.0

    @staticmethod
    def calculate_token_shannon_entropy(tokens: list[str]) -> float:
        """Calculate token-level Shannon entropy: H = - sum(p * log2(p))."""
        if not tokens:
            return 0.0
        counts = Counter(tokens)
        total = len(tokens)
        entropy = 0.0
        for count in counts.values():
            p = count / total
            entropy -= p * math.log2(p)
        return entropy

    def feed_token(self, token: str) -> bool:
        """
        Feed single token to watchdog.
        Returns True if a runaway loop was detected and slot erase was triggered.
        """
        self.token_buffer.append(token)
        self.text_buffer += token
        self.tokens_since_check += 1

        if self.tokens_since_check >= self.check_interval:
            self.tokens_since_check = 0
            return self._evaluate_window()
        return False

    def _evaluate_window(self) -> bool:
        window_tokens = self.token_buffer[-self.window_size :]
        window_text = "".join(window_tokens)

        rep_ratio = self.calculate_4gram_repetition_ratio(window_text)
        entropy = self.calculate_token_shannon_entropy(window_tokens)

        # Violation condition: repetition > 0.85 OR entropy < 1.5
        is_violation = (rep_ratio >= self.max_repetition_ratio) or (
            len(window_tokens) >= 16 and entropy <= self.min_shannon_entropy
        )

        if is_violation:
            self.consecutive_loop_violations += 1
        else:
            self.consecutive_loop_violations = max(0, self.consecutive_loop_violations - 1)

        if self.consecutive_loop_violations >= self.consecutive_triggers_required:
            self.loop_detected = True
            self.trigger_slot_erase()
            return True
        return False

    def trigger_slot_erase(self, slot_id: int = 0) -> bool:
        """Issue POST /slots/<id>?action=erase to llama-server."""
        url = f"{self.server_url}/slots/{slot_id}?action=erase"
        req = urllib.request.Request(url, data=b"", method="POST")
        try:
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                return resp.status == 200
        except (urllib.error.URLError, TimeoutError, OSError):
            return False

    @staticmethod
    def truncate_at_last_complete_ast_boundary(code: str) -> str:
        """
        Walk backwards line-by-line to find the last point where AST parsing succeeds.
        """
        lines = code.splitlines()
        for i in range(len(lines), 0, -1):
            candidate = "\n".join(lines[:i])
            try:
                ast.parse(candidate)
                return candidate
            except SyntaxError:
                continue
        return code


if __name__ == "__main__":
    watchdog = SlidingWindowShannonEntropyWatchdog(
        window_size=32,
        check_interval=8,
        consecutive_triggers_required=2,
    )
    # Simulate cyclic loop
    cyclic_tokens = ["1", ", ", "3", ", ", "2", ", "] * 20
    triggered = False
    for tok in cyclic_tokens:
        if watchdog.feed_token(tok):
            triggered = True
            break
    print(f"Watchdog trigger status: {triggered}")
    sys.exit(0 if triggered else 1)
