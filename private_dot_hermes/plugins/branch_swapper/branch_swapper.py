"""
U38: Autonomous Hypothesis Tree Branch Swapper & Tabu Pruner
=============================================================
Detects fixations and repair loops in 4B SLM execution:
  - Tracks repair-turn counts per task/hypothesis node
  - Upon 2 consecutive failed repair turns on same file/hypothesis → triggers branch swap
  - Injects negative boundary constraints & tabu patterns into new exploratory branch
  - Preserves state history in RAMDisk SQLite WAL (/dev/shm/branch_swapper.db)

Integrates with:
  - HypothesisTree (backtracking engine)
  - LifecycleHookEngine (Observer Gate rejections)
  - TaskDAG (task status tracking)
"""

import json
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum

DB_PATH = "/dev/shm/branch_swapper.db"


class SwapTrigger(Enum):
    CONSECUTIVE_FAILURES = "consecutive_failures"
    MAX_REPAIR_TURNS = "max_repair_turns"
    TABU_PATTERN_MATCH = "tabu_pattern_match"
    LOOP_DETECTED = "loop_detected"


@dataclass
class RepairTurn:
    """Single repair attempt record."""
    turn_id: str
    task_id: str
    hypothesis_id: str
    file_path: str
    tool_name: str
    error_signature: str
    timestamp: float
    is_failure: bool


@dataclass
class TabuPattern:
    """Tabu (forbidden) pattern to avoid repeating."""
    pattern_id: str
    error_signature: str
    file_path: str
    tool_name: str
    occurrence_count: int
    created_at: float
    last_seen: float


@dataclass
class NegativeConstraint:
    """Boundary constraint learned from failure."""
    constraint_id: str
    task_id: str
    hypothesis_id: str
    description: str
    pattern: str  # e.g., "duplicate_declaration", "brace_mismatch", "missing_import"
    created_at: float


class BranchSwapper:
    """
    Monitors repair turns and triggers branch swaps when fixation detected.
    
    Fixation criteria (configurable):
      - 2+ consecutive failures on same file/hypothesis
      - 5+ identical tool failures (FM-06 loop lock)
      - Tabu pattern match (previously failed approach)
    """

    MAX_CONSECUTIVE_FAILURES = 2
    MAX_IDENTICAL_FAILURES = 5
    TABU_WINDOW_SECONDS = 300  # 5 minutes

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA foreign_keys=ON")
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_db(self):
        conn = self._get_conn()
        cur = conn.cursor()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS repair_turns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                turn_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                hypothesis_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                error_signature TEXT NOT NULL,
                timestamp REAL NOT NULL,
                is_failure INTEGER NOT NULL
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tabu_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id TEXT UNIQUE NOT NULL,
                error_signature TEXT NOT NULL,
                file_path TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                occurrence_count INTEGER NOT NULL,
                created_at REAL NOT NULL,
                last_seen REAL NOT NULL
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS negative_constraints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                constraint_id TEXT UNIQUE NOT NULL,
                task_id TEXT NOT NULL,
                hypothesis_id TEXT NOT NULL,
                description TEXT NOT NULL,
                pattern TEXT NOT NULL,
                created_at REAL NOT NULL
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS branch_swaps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                swap_id TEXT UNIQUE NOT NULL,
                trigger_type TEXT NOT NULL,
                from_task_id TEXT NOT NULL,
                from_hypothesis_id TEXT NOT NULL,
                to_task_id TEXT NOT NULL,
                to_hypothesis_id TEXT NOT NULL,
                constraints_injected TEXT NOT NULL,
                tabu_patterns_injected TEXT NOT NULL,
                timestamp REAL NOT NULL
            )
        """)
        
        # Indexes for fast lookup
        cur.execute("CREATE INDEX IF NOT EXISTS idx_repair_task ON repair_turns(task_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_repair_hypothesis ON repair_turns(hypothesis_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_repair_file ON repair_turns(file_path)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_repair_signature ON repair_turns(error_signature)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tabu_signature ON tabu_patterns(error_signature)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tabu_file ON tabu_patterns(file_path)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_constraints_task ON negative_constraints(task_id)")
        
        conn.commit()

    # ── Repair Turn Tracking ──────────────────────────────────────────────
    def record_repair_turn(
        self,
        task_id: str,
        hypothesis_id: str,
        file_path: str,
        tool_name: str,
        error_message: str,
        is_failure: bool
    ) -> RepairTurn:
        """Record a repair turn (success or failure)."""
        if not is_failure or not error_message:
            error_sig = ""
        else:
            error_sig = self._compute_error_signature(error_message, tool_name, file_path)
        
        turn = RepairTurn(
            turn_id=uuid.uuid4().hex[:12],
            task_id=task_id,
            hypothesis_id=hypothesis_id,
            file_path=file_path,
            tool_name=tool_name,
            error_signature=error_sig,
            timestamp=time.time(),
            is_failure=is_failure
        )
        
        conn = self._get_conn()
        conn.execute("""
            INSERT INTO repair_turns 
            (turn_id, task_id, hypothesis_id, file_path, tool_name, error_signature, timestamp, is_failure)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (turn.turn_id, turn.task_id, turn.hypothesis_id, turn.file_path,
              turn.tool_name, turn.error_signature, turn.timestamp, int(turn.is_failure)))
        conn.commit()
        
        # Update tabu patterns
        if is_failure:
            self._update_tabu_pattern(turn)
        
        return turn

    def _compute_error_signature(self, error_msg: str, tool_name: str, file_path: str) -> str:
        """Compute a normalized error signature for pattern matching."""
        # Extract key error type
        import re
        # Normalize line numbers, paths, variable names
        normalized = re.sub(r'line \d+', 'line N', error_msg)
        normalized = re.sub(r'[/\\][\w/\\.-]+', '<path>', normalized)
        normalized = re.sub(r'\b\w+\.py', '<file>.py', normalized)
        normalized = re.sub(r'"[^"]*"', '"<string>"', normalized)
        normalized = re.sub(r"'[^']*'", "'<string>'", normalized)
        return f"{tool_name}:{normalized[:200]}"

    def _update_tabu_pattern(self, turn: RepairTurn):
        """Update or create tabu pattern for this failure signature."""
        conn = self._get_conn()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT pattern_id, occurrence_count FROM tabu_patterns
            WHERE error_signature = ? AND file_path = ? AND tool_name = ?
        """, (turn.error_signature, turn.file_path, turn.tool_name))
        
        row = cur.fetchone()
        if row:
            new_count = row["occurrence_count"] + 1
            cur.execute("""
                UPDATE tabu_patterns
                SET occurrence_count = ?, last_seen = ?
                WHERE pattern_id = ?
            """, (new_count, time.time(), row["pattern_id"]))
        else:
            pattern_id = uuid.uuid4().hex[:12]
            cur.execute("""
                INSERT INTO tabu_patterns
                (pattern_id, error_signature, file_path, tool_name, occurrence_count, created_at, last_seen)
                VALUES (?, ?, ?, ?, 1, ?, ?)
            """, (pattern_id, turn.error_signature, turn.file_path, turn.tool_name, time.time(), time.time()))
        conn.commit()

    # ── Fixation Detection ────────────────────────────────────────────────
    def check_fixation(self, task_id: str, hypothesis_id: str, file_path: str) -> Tuple[bool, Optional[SwapTrigger]]:
        """
        Check if the current task/hypothesis is fixated.
        Returns (should_swap, trigger_type).
        """
        conn = self._get_conn()
        cur = conn.cursor()
        
        # 1. Check for identical failure loops (FM-06) first - highest priority
        cur.execute("""
            SELECT is_failure, error_signature, timestamp
            FROM repair_turns
            WHERE task_id = ? AND hypothesis_id = ? AND file_path = ?
            ORDER BY timestamp DESC
            LIMIT 5
        """, (task_id, hypothesis_id, file_path))
        
        recent = cur.fetchall()
        
        if recent:
            first_sig = recent[0]["error_signature"]
            cur.execute("""
                SELECT COUNT(*) as cnt FROM repair_turns
                WHERE task_id = ? AND hypothesis_id = ? AND error_signature = ? AND is_failure = 1
            """, (task_id, hypothesis_id, first_sig))
            count = cur.fetchone()["cnt"]
            if count >= self.MAX_IDENTICAL_FAILURES:
                return True, SwapTrigger.LOOP_DETECTED
        
        # 2. Check consecutive failures on same task/hypothesis/file
        # Only check the MOST RECENT turns (up to MAX_CONSECUTIVE_FAILURES)
        if len(recent) >= self.MAX_CONSECUTIVE_FAILURES:
            # Check if the most recent MAX_CONSECUTIVE_FAILURES turns are all failures
            recent_slice = recent[:self.MAX_CONSECUTIVE_FAILURES]
            all_fail = all(r["is_failure"] for r in recent_slice)
            if all_fail:
                return True, SwapTrigger.CONSECUTIVE_FAILURES
        
        # 3. Check tabu pattern match - from OTHER tasks/hypotheses on same file
        # (prevent repeating failed approaches from different branches)
        cur.execute("""
            SELECT DISTINCT t.error_signature 
            FROM tabu_patterns t
            JOIN repair_turns r ON t.error_signature = r.error_signature
            WHERE r.file_path = ? 
              AND (r.task_id != ? OR r.hypothesis_id != ?)
              AND t.last_seen > ?
            ORDER BY t.occurrence_count DESC
            LIMIT 10
        """, (file_path, task_id, hypothesis_id, time.time() - self.TABU_WINDOW_SECONDS))
        
        tabu_sigs = {r["error_signature"] for r in cur.fetchall()}
        if tabu_sigs:
            # Check if current error matches a tabu pattern from another branch
            if recent and recent[0]["error_signature"] in tabu_sigs:
                return True, SwapTrigger.TABU_PATTERN_MATCH
        
        return False, None

    # ── Negative Constraint Injection ─────────────────────────────────────
    def inject_negative_constraints(
        self,
        from_task_id: str,
        from_hypothesis_id: str,
        to_task_id: str,
        to_hypothesis_id: str
    ) -> Tuple[List[str], List[str]]:
        """
        Extract negative constraints from failed branch and inject into new branch.
        Returns (constraint_descriptions, tabu_pattern_descriptions).
        """
        conn = self._get_conn()
        cur = conn.cursor()
        
        # Get all negative constraints from failed hypothesis
        cur.execute("""
            SELECT description, pattern FROM negative_constraints
            WHERE task_id = ? AND hypothesis_id = ?
        """, (from_task_id, from_hypothesis_id))
        
        constraints = [f"{row['pattern']}: {row['description']}" for row in cur.fetchall()]
        
        # Get tabu patterns associated with this file/task
        cur.execute("""
            SELECT DISTINCT error_signature, tool_name, file_path FROM tabu_patterns
            WHERE file_path IN (
                SELECT DISTINCT file_path FROM repair_turns
                WHERE task_id = ? AND hypothesis_id = ?
            )
            ORDER BY occurrence_count DESC
            LIMIT 10
        """, (from_task_id, from_hypothesis_id))
        
        tabu_patterns = [
            f"tabu:{row['tool_name']}:{row['file_path']}:{row['error_signature'][:80]}"
            for row in cur.fetchall()
        ]
        
        # Store the swap event
        swap_id = uuid.uuid4().hex[:12]
        cur.execute("""
            INSERT INTO branch_swaps
            (swap_id, trigger_type, from_task_id, from_hypothesis_id,
             to_task_id, to_hypothesis_id, constraints_injected, tabu_patterns_injected, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (swap_id, "manual", from_task_id, from_hypothesis_id,
              to_task_id, to_hypothesis_id,
              json.dumps(constraints), json.dumps(tabu_patterns), time.time()))
        conn.commit()
        
        return constraints, tabu_patterns

    def learn_constraint_from_failure(
        self,
        task_id: str,
        hypothesis_id: str,
        description: str,
        pattern: str
    ) -> str:
        """Learn a new negative constraint from a failure."""
        constraint_id = uuid.uuid4().hex[:12]
        conn = self._get_conn()
        conn.execute("""
            INSERT INTO negative_constraints
            (constraint_id, task_id, hypothesis_id, description, pattern, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (constraint_id, task_id, hypothesis_id, description, pattern, time.time()))
        conn.commit()
        return constraint_id

    def get_negative_constraints(self, task_id: str) -> List[NegativeConstraint]:
        """Get all negative constraints for a task."""
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT constraint_id, task_id, hypothesis_id, description, pattern, created_at
            FROM negative_constraints WHERE task_id = ?
        """, (task_id,))
        return [
            NegativeConstraint(
                constraint_id=row["constraint_id"],
                task_id=row["task_id"],
                hypothesis_id=row["hypothesis_id"],
                description=row["description"],
                pattern=row["pattern"],
                created_at=row["created_at"]
            )
            for row in cur.fetchall()
        ]

    def get_tabu_patterns(self, file_path: str) -> List[TabuPattern]:
        """Get active tabu patterns for a file."""
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT pattern_id, error_signature, file_path, tool_name, occurrence_count, created_at, last_seen
            FROM tabu_patterns WHERE file_path = ? AND last_seen > ?
            ORDER BY occurrence_count DESC
        """, (file_path, time.time() - self.TABU_WINDOW_SECONDS))
        return [
            TabuPattern(
                pattern_id=row["pattern_id"],
                error_signature=row["error_signature"],
                file_path=row["file_path"],
                tool_name=row["tool_name"],
                occurrence_count=row["occurrence_count"],
                created_at=row["created_at"],
                last_seen=row["last_seen"]
            )
            for row in cur.fetchall()
        ]

    def get_repair_history(self, task_id: str, hypothesis_id: str, limit: int = 20) -> List[RepairTurn]:
        """Get repair turn history for a task/hypothesis."""
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT turn_id, task_id, hypothesis_id, file_path, tool_name, error_signature, timestamp, is_failure
            FROM repair_turns
            WHERE task_id = ? AND hypothesis_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (task_id, hypothesis_id, limit))
        return [
            RepairTurn(
                turn_id=row["turn_id"],
                task_id=row["task_id"],
                hypothesis_id=row["hypothesis_id"],
                file_path=row["file_path"],
                tool_name=row["tool_name"],
                error_signature=row["error_signature"],
                timestamp=row["timestamp"],
                is_failure=bool(row["is_failure"])
            )
            for row in cur.fetchall()
        ]

    # ── Branch Swap Execution ─────────────────────────────────────────────
    def execute_swap(
        self,
        from_task_id: str,
        from_hypothesis_id: str,
        to_task_id: str,
        to_hypothesis_id: str,
        trigger: SwapTrigger
    ) -> Dict:
        """
        Execute a branch swap: inject constraints/tabu from failed branch into new branch.
        """
        constraints, tabu_patterns = self.inject_negative_constraints(
            from_task_id, from_hypothesis_id, to_task_id, to_hypothesis_id
        )
        
        # Record the swap
        swap_id = uuid.uuid4().hex[:12]
        conn = self._get_conn()
        conn.execute("""
            INSERT INTO branch_swaps
            (swap_id, trigger_type, from_task_id, from_hypothesis_id,
             to_task_id, to_hypothesis_id, constraints_injected, tabu_patterns_injected, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (swap_id, trigger.value, from_task_id, from_hypothesis_id,
              to_task_id, to_hypothesis_id,
              json.dumps(constraints), json.dumps(tabu_patterns), time.time()))
        conn.commit()
        
        return {
            "swap_id": swap_id,
            "trigger": trigger.value,
            "from_task": from_task_id,
            "from_hypothesis": from_hypothesis_id,
            "to_task": to_task_id,
            "to_hypothesis": to_hypothesis_id,
            "injected_constraints": constraints,
            "injected_tabu": tabu_patterns,
            "timestamp": time.time()
        }

    # ── Integration with HypothesisTree ───────────────────────────────────
    def on_observer_gate_rejection(
        self,
        task_id: str,
        hypothesis_id: str,
        file_path: str,
        tool_name: str,
        error_message: str
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Called when Observer Gate rejects a mutation.
        Returns (should_swap, swap_info).
        """
        # Record the failure
        self.record_repair_turn(
            task_id, hypothesis_id, file_path, tool_name, error_message, is_failure=True
        )
        
        # Check for fixation
        should_swap, trigger = self.check_fixation(task_id, hypothesis_id, file_path)
        
        if should_swap:
            # Learn constraint from this failure
            self.learn_constraint_from_failure(
                task_id, hypothesis_id,
                f"Observer Gate rejected {tool_name} on {file_path}",
                self._classify_error(error_message)
            )
            
            # The actual branch swap is handled by the orchestrator
            # which creates a new hypothesis in HypothesisTree
            return True, {"trigger": trigger.value}
        
        return False, None

    def _classify_error(self, error_msg: str) -> str:
        """Classify error into pattern category."""
        error_lower = error_msg.lower()
        if "duplicate" in error_lower:
            return "duplicate_declaration"
        if "brace" in error_lower or "{" in error_msg or "}" in error_msg:
            return "brace_mismatch"
        if "import" in error_lower or "module" in error_lower:
            return "missing_import"
        if "syntax" in error_lower:
            return "syntax_error"
        if "indent" in error_lower:
            return "indentation_error"
        if "undefined" in error_lower or "not defined" in error_lower:
            return "undefined_reference"
        return "other"

    def clear_task_history(self, task_id: str):
        """Clear history for a task (e.g., on task completion)."""
        conn = self._get_conn()
        conn.execute("DELETE FROM repair_turns WHERE task_id = ?", (task_id,))
        conn.execute("DELETE FROM negative_constraints WHERE task_id = ?", (task_id,))
        conn.commit()


def create_branch_swapper() -> BranchSwapper:
    """Factory for RAMDisk-backed BranchSwapper."""
    return BranchSwapper(DB_PATH)


__all__ = ["BranchSwapper", "create_branch_swapper", "RepairTurn", "TabuPattern", "NegativeConstraint", "SwapTrigger"]
