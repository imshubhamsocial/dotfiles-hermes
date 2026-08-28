"""
U15: Codex 6x Token Economy State Engine
========================================
Adopts OpenAI Codex Harness primitives (Apache-2.0) for local 6 GB GPU runs:

  1. Differential State Compaction — execution state lives as structured
     diffs/milestones instead of appending full file texts every turn;
     resolved intermediate tool turns are pruned on milestone verification.
  2. Ephemeral Tool Execution Context — subprocess/linter/compiler streams go
     into isolated RAMdisk (/dev/shm, btrfs zero-wear) buffers; ONLY the compact
     verdict + 5-line failure slice ever enters model context.
  3. Immutable Goal Anchor — a persistent <=10-line anchor (.hermes/plan.json +
     current_target) pinned at the top of the user turn survives ALL prunings,
     eliminating over-pruning goal drift (Trap 1).
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

RAMDISK = Path("/dev/shm")
PLAN_PATH = Path(".hermes/plan.json")
KEEP_RECENT_TURNS = 4


def estimate_tokens(text: str) -> int:
    return max(1, len(" ".join(str(text).split())) // 4)


class GoalAnchor:
    """Immutable <=10-line anchor pinned across all compaction passes."""

    def __init__(self, goal: str = "", current_target: str = "", constraints: Optional[List[str]] = None):
        self.goal = goal
        self.current_target = current_target
        self.constraints = (constraints or [])[:6]

    def to_dict(self) -> Dict:
        return {"goal": self.goal, "current_target": self.current_target, "constraints": self.constraints}

    @classmethod
    def load(cls, path: Path = PLAN_PATH) -> "GoalAnchor":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls(data.get("goal", ""), data.get("current_target", ""), data.get("constraints", []))
        except Exception:
            return cls()

    def save(self, path: Path = PLAN_PATH):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    def format_prompt_block(self) -> str:
        lines = ["<|GOAL_ANCHOR|>", f"GOAL: {self.goal}", f"TARGET: {self.current_target}"]
        lines += [f"- {c}" for c in self.constraints]
        lines.append("</|GOAL_ANCHOR|>")
        return "\n".join(lines[:10])


class EphemeralToolBuffer:
    """Context manager: full tool stream -> RAMdisk buffer; context gets verdict + 5-line slice."""

    def __init__(self, label: str = "tool", keep_tail_lines: int = 5):
        self.label = label
        self.keep_tail_lines = keep_tail_lines
        self.buffer_path = RAMDISK / f"hermes_ephemeral_{label}_{int(time.time()*1000)}.log"
        self._chunks: List[str] = []

    def __enter__(self) -> "EphemeralToolBuffer":
        RAMDISK.mkdir(parents=True, exist_ok=True)
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is not None:
            self.write(f"[exception] {exc_type.__name__}: {exc}")
        return False

    def write(self, text: str):
        self._chunks.append(text)

    def finalize(self, exit_code: int) -> str:
        """Persist FULL stream to /dev/shm; return ONLY compact verdict (+5-line slice on failure)."""
        full = "".join(self._chunks)
        try:
            self.buffer_path.write_text(full, encoding="utf-8")
            self.buffer_path.chmod(0o600)
        except Exception:
            pass
        lines = [l for l in full.splitlines() if l.strip()]
        if exit_code == 0:
            return f"[{self.label}] PASS (exit=0). Full log: {self.buffer_path}"
        slice_ = "\n".join(lines[-self.keep_tail_lines:])
        return f"[{self.label}] FAIL (exit={exit_code}). Last {self.keep_tail_lines} lines:\n{slice_}\nFull log: {self.buffer_path}"


class DifferentialStateCompactor:
    """
    Prunes resolved intermediate turns from history while preserving:
      - messages[0]: goal-anchor user turn (immutable)
      - the last KEEP_RECENT_TURNS turns (active reasoning window)
      - milestone verdicts (assistant VERIFIED/FAILED markers)

    Resolved rule: an (assistant-with-tool_calls + its tool result) pair is
    resolved when BOTH a later successful patch/test event exists AND the turn
    index predates that milestone. Resolved pairs collapse into one summary.
    """

    MILESTONE_HINTS = ("PASS", "VERIFIED", "Successfully patched", "Successfully wrote")

    def __init__(self, keep_recent: int = KEEP_RECENT_TURNS, keep_head: int = 2):
        self.keep_recent = keep_recent
        self.keep_head = keep_head

    def _is_milestone_tool_msg(self, msg: Dict) -> bool:
        return msg.get("role") == "tool" and any(h in str(msg.get("content", "")) for h in self.MILESTONE_HINTS)

    def find_last_milestone_index(self, history: List[Dict]) -> int:
        last = -1
        for i, m in enumerate(history):
            if self._is_milestone_tool_msg(m):
                last = i
        return last

    def compact(self, history: List[Dict]) -> List[Dict]:
        if len(history) <= self.keep_head + self.keep_recent:
            return list(history)
        last_ms = self.find_last_milestone_index(history)
        head, tail = history[: self.keep_head], history[-self.keep_recent :]
        middle = history[self.keep_head : len(history) - self.keep_recent]

        kept: List[Dict] = []
        i = 0
        resolved_count = 0
        while i < len(middle):
            msg = middle[i]
            is_resolved_pair = (
                msg.get("role") == "assistant"
                and msg.get("tool_calls")
                and i < (last_ms if last_ms >= 0 else 0)
                and i + 1 < len(middle)
                and middle[i + 1].get("role") == "tool"
            )
            if is_resolved_pair:
                names = ",".join(tc["function"]["name"] for tc in msg["tool_calls"][:3])
                kept.append({"role": "user", "content": f"[compacted] Turn resolved via {names}."})
                resolved_count += 1
                i += 2
                continue
            kept.append(msg)
            i += 1

        if resolved_count:
            kept.append({"role": "user", "content": f"[state] {resolved_count} intermediate tool turn(s) differentially compacted."})
        return head + kept + tail

    @staticmethod
    def reduction_ratio(baseline_history: List[Dict], compacted_history: List[Dict]) -> float:
        base = sum(estimate_tokens(m.get("content", "")) for m in baseline_history)
        comp = sum(estimate_tokens(m.get("content", "")) for m in compacted_history)
        return base / max(1, comp)


if __name__ == "__main__":
    print(f"token_engine self-test: anchor tokens ~ {estimate_tokens(GoalAnchor('demo', 'f.py').format_prompt_block())}")
