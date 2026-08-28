"""
Transactional SQLite-backed Directed Acyclic Graph (DAG) Task Engine
=====================================================================
Decomposes complex user goals into atomic, bounded sub-tasks (<350 tokens),
resolves execution dependencies, tracks retries, and coordinates git rollbacks
upon repeated failures.

Also maintains backward compatibility with the original TaskGraph/SubTask/HardwareBudgets
for existing code (U1-U20 baseline).
"""

import json
import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from enum import Enum
from pydantic import BaseModel, Field


# =============================================================================
# NEW U21: TaskDAG - SQLite-backed DAG Task Engine
# =============================================================================

class TaskStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CycleDetectedError(Exception):
    """Raised when a cycle is detected in the task dependency graph."""
    pass


@dataclass
class Task:
    id: str
    title: str
    prompt: str
    status: TaskStatus
    retry_count: int
    max_retries: int
    result: str
    created_at: float
    updated_at: float


class TaskDAG:
    """
    SQLite-backed DAG task engine with WAL mode persistence.
    
    Supports both persistent (~/.hermes/state.db) and ephemeral (/dev/shm/harness_brain.db or :memory:) paths.
    """
    
    def __init__(self, db_path: str = "/dev/shm/harness_brain.db"):
        self.db_path = db_path
        self._local = threading.local()
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection with WAL mode enabled."""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA foreign_keys=ON")
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn
    
    def _init_database(self):
        """Initialize database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Create dag_tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dag_tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                prompt TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING',
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                result TEXT DEFAULT '',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        
        # Create dag_edges table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dag_edges (
                parent_id TEXT NOT NULL,
                child_id TEXT NOT NULL,
                PRIMARY KEY (parent_id, child_id),
                FOREIGN KEY (parent_id) REFERENCES dag_tasks(id) ON DELETE CASCADE,
                FOREIGN KEY (child_id) REFERENCES dag_tasks(id) ON DELETE CASCADE
            )
        """)
        
        # Create dag_snapshots table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dag_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                git_commit_hash TEXT NOT NULL,
                created_at REAL NOT NULL,
                FOREIGN KEY (task_id) REFERENCES dag_tasks(id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dag_tasks_status ON dag_tasks(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dag_edges_parent ON dag_edges(parent_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dag_edges_child ON dag_edges(child_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dag_snapshots_task ON dag_snapshots(task_id)")
        
        conn.commit()
    
    def add_task(self, task_id: str, title: str, prompt: str, max_retries: int = 3) -> None:
        """Add a new task to the DAG."""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = time.time()
        
        cursor.execute("""
            INSERT INTO dag_tasks (id, title, prompt, status, retry_count, max_retries, result, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (task_id, title, prompt, TaskStatus.PENDING.value, 0, max_retries, "", now, now))
        
        conn.commit()
    
    def add_dependency(self, parent_id: str, child_id: str) -> None:
        """Add a dependency edge from parent to child."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Verify both tasks exist
        cursor.execute("SELECT id FROM dag_tasks WHERE id IN (?, ?)", (parent_id, child_id))
        existing = {row['id'] for row in cursor.fetchall()}
        
        if parent_id not in existing:
            raise ValueError(f"Parent task '{parent_id}' does not exist")
        if child_id not in existing:
            raise ValueError(f"Child task '{child_id}' does not exist")
        
        cursor.execute("""
            INSERT OR IGNORE INTO dag_edges (parent_id, child_id)
            VALUES (?, ?)
        """, (parent_id, child_id))
        
        conn.commit()
    
    def get_ready_tasks(self) -> List[Dict]:
        """Returns all tasks in PENDING state whose upstream parent dependencies are ALL in COMPLETED state."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT t.id, t.title, t.prompt, t.status, t.retry_count, t.max_retries, t.result, t.created_at, t.updated_at
            FROM dag_tasks t
            WHERE t.status = 'PENDING'
            AND NOT EXISTS (
                SELECT 1 FROM dag_edges e
                JOIN dag_tasks p ON e.parent_id = p.id
                WHERE e.child_id = t.id
                AND p.status != 'COMPLETED'
            )
        """)
        
        tasks = []
        for row in cursor.fetchall():
            tasks.append({
                'id': row['id'],
                'title': row['title'],
                'prompt': row['prompt'],
                'status': row['status'],
                'retry_count': row['retry_count'],
                'max_retries': row['max_retries'],
                'result': row['result'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })
        
        return tasks
    
    def update_task_status(self, task_id: str, status: str, result: str = "") -> None:
        """Update task status directly (compatibility method)."""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = time.time()
        cursor.execute("""
            UPDATE dag_tasks
            SET status = ?, result = ?, updated_at = ?
            WHERE id = ?
        """, (status, result, now, task_id))
        conn.commit()
    
    def mark_running(self, task_id: str) -> None:
        """Mark a task as RUNNING."""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = time.time()
        
        cursor.execute("""
            UPDATE dag_tasks
            SET status = ?, updated_at = ?
            WHERE id = ?
        """, (TaskStatus.RUNNING.value, now, task_id))
        
        conn.commit()
    
    def mark_completed(self, task_id: str, result: str = "") -> None:
        """Mark a task as COMPLETED with optional result."""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = time.time()
        
        cursor.execute("""
            UPDATE dag_tasks
            SET status = ?, result = ?, updated_at = ?
            WHERE id = ?
        """, (TaskStatus.COMPLETED.value, result, now, task_id))
        
        conn.commit()
    
    def mark_failed(self, task_id: str, error: str = "") -> bool:
        """
        Increment retry_count. If retry_count < max_retries, returns True (can retry).
        If retry_count >= max_retries, marks status as FAILED and returns False (triggers branch/rollback).
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        now = time.time()
        
        # Get current retry count and max retries
        cursor.execute("SELECT retry_count, max_retries FROM dag_tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        
        if row is None:
            raise ValueError(f"Task '{task_id}' does not exist")
        
        retry_count = row['retry_count'] + 1
        max_retries = row['max_retries']
        
        if retry_count < max_retries:
            # Can retry - update retry count and set back to PENDING
            cursor.execute("""
                UPDATE dag_tasks
                SET retry_count = ?, status = ?, result = ?, updated_at = ?
                WHERE id = ?
            """, (retry_count, TaskStatus.PENDING.value, error, now, task_id))
            conn.commit()
            return True
        else:
            # Exhausted retries - mark as FAILED
            cursor.execute("""
                UPDATE dag_tasks
                SET retry_count = ?, status = ?, result = ?, updated_at = ?
                WHERE id = ?
            """, (retry_count, TaskStatus.FAILED.value, error, now, task_id))
            conn.commit()
            return False
    
    def record_snapshot(self, task_id: str, git_hash: str) -> None:
        """Record a git snapshot for a task."""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = time.time()
        
        cursor.execute("""
            INSERT INTO dag_snapshots (task_id, git_commit_hash, created_at)
            VALUES (?, ?, ?)
        """, (task_id, git_hash, now))
        
        conn.commit()
    
    def get_topological_order(self) -> List[str]:
        """
        Computes topological execution order using Kahn's algorithm.
        Raises CycleDetectedError if a cycle exists.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get all tasks
        cursor.execute("SELECT id FROM dag_tasks")
        all_tasks = {row['id'] for row in cursor.fetchall()}
        
        if not all_tasks:
            return []
        
        # Build adjacency list and in-degree count
        adj: Dict[str, Set[str]] = {task_id: set() for task_id in all_tasks}
        in_degree: Dict[str, int] = {task_id: 0 for task_id in all_tasks}
        
        cursor.execute("SELECT parent_id, child_id FROM dag_edges")
        for row in cursor.fetchall():
            parent = row['parent_id']
            child = row['child_id']
            if parent in adj and child in adj:
                if child not in adj[parent]:
                    adj[parent].add(child)
                    in_degree[child] += 1
        
        # Kahn's algorithm
        queue = [task_id for task_id in all_tasks if in_degree[task_id] == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            for neighbor in adj[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        if len(result) != len(all_tasks):
            raise CycleDetectedError("Cycle detected in task dependency graph")
        
        return result
    
    def is_dag_complete(self) -> bool:
        """Returns True if all tasks are COMPLETED."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM dag_tasks")
        total = cursor.fetchone()['total']
        
        if total == 0:
            return True
        
        cursor.execute("SELECT COUNT(*) as completed FROM dag_tasks WHERE status = 'COMPLETED'")
        completed = cursor.fetchone()['completed']
        
        return completed == total
    
    def has_fatal_failure(self) -> bool:
        """Returns True if any task reached FAILED state."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as failed FROM dag_tasks WHERE status = 'FAILED'")
        failed = cursor.fetchone()['failed']
        
        return failed > 0
    
    def export_summary(self) -> Dict:
        """Returns task count, completed count, failed count, and execution progress percentage."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM dag_tasks")
        total = cursor.fetchone()['total']
        
        if total == 0:
            return {
                'total_tasks': 0,
                'completed_tasks': 0,
                'failed_tasks': 0,
                'pending_tasks': 0,
                'running_tasks': 0,
                'progress_percentage': 100.0
            }
        
        cursor.execute("SELECT status, COUNT(*) as count FROM dag_tasks GROUP BY status")
        status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
        
        completed = status_counts.get('COMPLETED', 0)
        failed = status_counts.get('FAILED', 0)
        pending = status_counts.get('PENDING', 0)
        running = status_counts.get('RUNNING', 0)
        
        progress = (completed / total) * 100.0 if total > 0 else 100.0
        
        return {
            'total_tasks': total,
            'completed_tasks': completed,
            'failed_tasks': failed,
            'pending_tasks': pending,
            'running_tasks': running,
            'progress_percentage': progress
        }
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """Get a task by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, prompt, status, retry_count, max_retries, result, created_at, updated_at
            FROM dag_tasks WHERE id = ?
        """, (task_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                'id': row['id'],
                'title': row['title'],
                'prompt': row['prompt'],
                'status': row['status'],
                'retry_count': row['retry_count'],
                'max_retries': row['max_retries'],
                'result': row['result'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }
        return None
    
    def get_all_tasks(self) -> List[Dict]:
        """Get all tasks."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, prompt, status, retry_count, max_retries, result, created_at, updated_at
            FROM dag_tasks ORDER BY created_at
        """)
        
        tasks = []
        for row in cursor.fetchall():
            tasks.append({
                'id': row['id'],
                'title': row['title'],
                'prompt': row['prompt'],
                'status': row['status'],
                'retry_count': row['retry_count'],
                'max_retries': row['max_retries'],
                'result': row['result'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })
        
        return tasks
    
    def get_dependencies(self, task_id: str) -> List[str]:
        """Get all parent dependencies of a task."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT parent_id FROM dag_edges WHERE child_id = ?", (task_id,))
        return [row['parent_id'] for row in cursor.fetchall()]
    
    def get_dependents(self, task_id: str) -> List[str]:
        """Get all child dependents of a task."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT child_id FROM dag_edges WHERE parent_id = ?", (task_id,))
        return [row['child_id'] for row in cursor.fetchall()]
    
    def close(self):
        """Close the database connection."""
        if hasattr(self._local, 'conn') and self._local.conn is not None:
            self._local.conn.close()
            self._local.conn = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Convenience function for persistent storage
def create_persistent_dag() -> TaskDAG:
    """Create a TaskDAG with persistent storage at ~/.hermes/state.db"""
    from pathlib import Path
    db_path = Path.home() / ".hermes" / "state.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return TaskDAG(str(db_path))


# Convenience function for ephemeral storage
def create_ephemeral_dag() -> TaskDAG:
    """Create a TaskDAG with ephemeral storage at /dev/shm/harness_brain.db"""
    return TaskDAG("/dev/shm/harness_brain.db")


# Convenience function for in-memory storage (testing)
def create_memory_dag() -> TaskDAG:
    """Create a TaskDAG with in-memory storage (:memory:)"""
    return TaskDAG(":memory:")


# =============================================================================
# BACKWARD COMPATIBILITY: Original TaskGraph/SubTask/HardwareBudgets (U1-U20)
# =============================================================================

WORKSPACE_ROOT = Path("/dev/shm/hermes_workspace")


class SubTask(BaseModel):
    id: str
    title: str
    description: str
    phase: str = "PENDING"  # PENDING, RESEARCHING, PLANNING, CODING, TESTING, DEBUGGING, VERIFIED
    dependencies: List[str] = Field(default_factory=list)
    target_files: List[str] = Field(default_factory=list)
    passes: bool = False
    error_trace: Optional[str] = None
    token_budget: int = 4000
    tokens_used: int = 0


class TaskGraph(BaseModel):
    project_goal: str
    total_budget: int = 32000  # Hardware ceiling: 32k context total across turns
    active_task_id: Optional[str] = None
    tasks: Dict[str, SubTask] = Field(default_factory=dict)
    history_log: List[Dict[str, Any]] = Field(default_factory=list)

    def add_task(self, task: SubTask):
        self.tasks[task.id] = task

    def get_next_runnable_task(self) -> Optional[SubTask]:
        """Return the highest-priority task whose dependencies have all passed."""
        for t_id, task in self.tasks.items():
            if not task.passes:
                deps_met = all(self.tasks[d].passes for d in task.dependencies if d in self.tasks)
                if deps_met:
                    self.active_task_id = t_id
                    return task
        return None

    def mark_task_verified(self, task_id: str):
        if task_id in self.tasks:
            self.tasks[task_id].passes = True
            self.tasks[task_id].phase = "VERIFIED"
            self.history_log.append({
                "task_id": task_id,
                "status": "VERIFIED",
                "timestamp": time.time()
            })

    def mark_task_failed(self, task_id: str, error_trace: str):
        if task_id in self.tasks:
            self.tasks[task_id].passes = False
            self.tasks[task_id].phase = "DEBUGGING"
            self.tasks[task_id].error_trace = error_trace
            self.history_log.append({
                "task_id": task_id,
                "status": "FAILED",
                "trace": error_trace[:300],
                "timestamp": time.time()
            })

    def save_state(self, filepath: Optional[str] = None):
        p = Path(filepath) if filepath else WORKSPACE_ROOT / "task_graph.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.model_dump_json(indent=2), encoding="utf-8")

    @classmethod
    def load_state(cls, filepath: Optional[str] = None) -> "TaskGraph":
        p = Path(filepath) if filepath else WORKSPACE_ROOT / "task_graph.json"
        if p.exists():
            try:
                return cls.model_validate_json(p.read_text(encoding="utf-8"))
            except Exception:
                pass
        return cls(project_goal="Autonomous Task")


class HardwareBudgets:
    """Universal Dynamic Hardware Constraints & Budget Enforcement.
    Dynamically probes host environment (CUDA/Metal/CPU, VRAM, RAMDisk) instead of relying on static constants.
    """
    MAX_VRAM_MB: int = 3800
    MAX_TURN_TOKENS: int = 2048
    MAX_OUTPUT_TOKENS: int = 4096
    MAX_TOTAL_TASK_TURNS: int = 25
    INFERENCE_SPEED_TPS: float = 47.3
    RAMDISK_PATH: str = "/dev/shm"

    @classmethod
    def probe_system_resources(cls, server_url: str = "http://127.0.0.1:8138") -> Dict[str, Any]:
        """Dynamically detect actual available compute, context window, and memory ceiling."""
        import urllib.request
        detected = {
            "vram_mb": cls.MAX_VRAM_MB,
            "ctx_size": cls.MAX_TURN_TOKENS,
            "max_output": cls.MAX_OUTPUT_TOKENS,
            "ramdisk": Path("/dev/shm").exists()
        }

        # 1. Probe live llama-server /props or /slots if accessible
        try:
            req = urllib.request.Request(f"{server_url}/props", headers={"User-Agent": "Hermes-Prober"})
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if "default_generation_settings" in data:
                    detected["ctx_size"] = data.get("default_generation_settings", {}).get("n_ctx", cls.MAX_TURN_TOKENS)
        except Exception:
            pass

        # 2. Check RAMDisk availability
        if not Path("/dev/shm").exists():
            detected["ramdisk"] = False
            cls.RAMDISK_PATH = "/tmp"

        return detected

    @classmethod
    def calculate_eta_seconds(cls, tokens_remaining: int) -> float:
        return tokens_remaining / cls.INFERENCE_SPEED_TPS
