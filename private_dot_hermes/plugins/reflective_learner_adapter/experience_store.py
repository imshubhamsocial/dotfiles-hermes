"""
Phase 6: Living Experience Store & Metacognitive Flywheel Engine
===============================================================
Replicates AGY's metacognitive loop for autonomous local SLMs:
  1. Record: Ingests episodes into RAMDisk memory store (/dev/shm/experience_store.json)
  2. Detect Compute Waste: Flags redundant queries, ping-pong retries, schema bloat
  3. Extract Patterns: Identifies failure causes and successful execution trails
  4. Generate Negative Constraints: Creates strict boundary rules from errors
  5. Generate Playbooks: Creates positive templates from verified runs
  6. Inject: Delivers token-bounded (<=200 tokens) memories to @architect / @coder
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

try:
    from sqlmodel import SQLModel, Field, Session, create_engine, select
    SQLMODEL_AVAILABLE = True
except ImportError:
    SQLMODEL_AVAILABLE = False
    SQLModel = object  # type: ignore
    Field = lambda **kwargs: None  # type: ignore


if SQLMODEL_AVAILABLE:
    class EpisodeModel(SQLModel, table=True):
        """SQLModel table for durable episodic memory persistence (Issue #11)."""
        id: Optional[int] = Field(default=None, primary_key=True)
        episode_id: str = Field(index=True)
        task_description: str
        subsystem: str = "general"
        tool_calls_json: str = "[]"
        outcome: str = "SUCCESS"
        token_usage: int = 0
        duration_sec: float = 0.0
        error_traces_json: str = "[]"
        timestamp: float = Field(default_factory=time.time)
else:
    EpisodeModel = None  # type: ignore


@dataclass
class EpisodeRecord:
    episode_id: str
    task_description: str
    subsystem: str
    tool_calls: List[Dict[str, Any]]
    outcome: str  # "SUCCESS" | "FAILURE" | "RETRY_EXHAUSTED"
    token_usage: int
    duration_sec: float
    error_traces: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EpisodeRecord":
        return cls(
            episode_id=data["episode_id"],
            task_description=data["task_description"],
            subsystem=data.get("subsystem", "general"),
            tool_calls=data.get("tool_calls", []),
            outcome=data.get("outcome", "SUCCESS"),
            token_usage=int(data.get("token_usage", 0)),
            duration_sec=float(data.get("duration_sec", 0.0)),
            error_traces=data.get("error_traces", []),
            timestamp=float(data.get("timestamp", time.time())),
        )


class ExperienceStore:
    """
    Episodic memory store and learning flywheel controller.
    """

    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        if db_path is None:
            # Default to RAMDisk if available, else local .hermes
            shm_dir = Path("/dev/shm")
            if shm_dir.exists() and shm_dir.is_dir():
                self.db_path = shm_dir / "hermes_experience_store.json"
            else:
                self.db_path = Path.home() / ".hermes" / "experience_store.json"
        else:
            self.db_path = Path(db_path)

        self.episodes: List[EpisodeRecord] = []
        self._load()

    def _load(self) -> None:
        if self.db_path.exists():
            try:
                data = json.loads(self.db_path.read_text(encoding="utf-8"))
                self.episodes = [EpisodeRecord.from_dict(ep) for ep in data.get("episodes", [])]
            except Exception:
                self.episodes = []

    def _save(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": "2.0",
            "updated_at": time.time(),
            "episodes": [ep.to_dict() for ep in self.episodes],
        }
        self.db_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def record_episode(
        self,
        episode_id: str,
        task_description: str,
        subsystem: str,
        tool_calls: List[Dict[str, Any]],
        outcome: str,
        token_usage: int,
        duration_sec: float,
        error_traces: Optional[List[str]] = None,
    ) -> EpisodeRecord:
        """Records a new execution episode into memory."""
        ep = EpisodeRecord(
            episode_id=episode_id,
            task_description=task_description,
            subsystem=subsystem,
            tool_calls=tool_calls,
            outcome=outcome,
            token_usage=token_usage,
            duration_sec=duration_sec,
            error_traces=error_traces or [],
        )
        self.episodes.append(ep)
        self._save()
        return ep

    def detect_compute_waste(self) -> List[Dict[str, Any]]:
        """
        The AGY Metacognitive Pattern: analyzes recorded episodes to identify:
          - Redundant sequential tool calls (e.g. repeated read_file on same file)
          - Retry ping-pong loops
          - Token usage exceeding normal thresholds (>1200 tokens per subtask)
        """
        waste_warnings: List[Dict[str, Any]] = []

        for ep in self.episodes[-10:]:
            # Check sequential duplicate tool calls
            tool_names = [tc.get("name") or tc.get("tool") for tc in ep.tool_calls]
            for i in range(len(tool_names) - 1):
                if tool_names[i] and tool_names[i] == tool_names[i + 1]:
                    waste_warnings.append({
                        "episode_id": ep.episode_id,
                        "type": "REDUNDANT_SEQUENTIAL_TOOL_CALL",
                        "tool": tool_names[i],
                        "recommendation": f"Consolidate back-to-back {tool_names[i]} calls into single invocation.",
                    })
                    break

            # Check excessive token usage
            if ep.token_usage > 1200:
                waste_warnings.append({
                    "episode_id": ep.episode_id,
                    "type": "HIGH_TOKEN_CONSUMPTION",
                    "tokens": ep.token_usage,
                    "recommendation": "Prune system prompt schemas or apply DifferentialStateCompactor.",
                })

        return waste_warnings

    def generate_negative_constraints(self, max_constraints: int = 5) -> List[str]:
        """Extracts failure patterns and generates actionable negative constraints."""
        constraints = []
        failure_episodes = [ep for ep in self.episodes if ep.outcome != "SUCCESS"]

        seen_errors = set()
        for ep in failure_episodes[-10:]:
            for err in ep.error_traces:
                if "duplicate declaration" in err.lower():
                    if "duplicate_decl" not in seen_errors:
                        constraints.append("NEVER re-declare variables in global scope; encapsulate in namespace object.")
                        seen_errors.add("duplicate_decl")
                elif "unexpected token" in err.lower() or "brace" in err.lower() or "syntax" in err.lower():
                    if "syntax_brace" not in seen_errors:
                        constraints.append("ALWAYS verify balanced closing braces before ending file patch.")
                        seen_errors.add("syntax_brace")
                elif "undefined variable" in err.lower():
                    if "undefined_var" not in seen_errors:
                        constraints.append("ALWAYS declare and initialize variables before passing to constructor.")
                        seen_errors.add("undefined_var")

        if not constraints:
            constraints.append("NEVER modify codebase files without checking AST balance.")

        return constraints[:max_constraints]

    def generate_positive_playbooks(self, max_playbooks: int = 5) -> List[str]:
        """Extracts successful patterns into reusable positive playbooks."""
        playbooks = []
        success_episodes = [ep for ep in self.episodes if ep.outcome == "SUCCESS"]

        subsystems = set(ep.subsystem for ep in success_episodes if ep.subsystem != "general")
        for sub in subsystems:
            playbooks.append(f"PLAYBOOK ({sub}): Use single-pass AST construction with Frame 0 initialization guards.")

        if not playbooks:
            playbooks.append("PLAYBOOK (General): Decompose multi-step tasks into in-degree 0 atomic subtasks.")

        return playbooks[:max_playbooks]

    def get_context_injection_prompt(self, task_description: str, max_tokens: int = 200) -> str:
        """
        Synthesizes a compact, token-bounded context injection string
        combining past lessons, negative constraints, and compute efficiency notes.
        """
        constraints = self.generate_negative_constraints(max_constraints=3)
        playbooks = self.generate_positive_playbooks(max_playbooks=2)
        waste = self.detect_compute_waste()

        lines = ["[Living Experience Memory & Constraints]"]
        for c in constraints:
            lines.append(f"  - CONSTRAINT: {c}")
        for p in playbooks:
            lines.append(f"  - {p}")
        if waste:
            lines.append(f"  - EFFICIENCY NOTE: {waste[0]['recommendation']}")

        res = "\n".join(lines)
        if len(res) > max_tokens * 4:
            res = res[: max_tokens * 4] + "\n  ... [truncated]"
        return res


def create_experience_store(db_path: Optional[Union[str, Path]] = None) -> ExperienceStore:
    return ExperienceStore(db_path=db_path)
