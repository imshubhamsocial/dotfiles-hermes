"""
Hermes Plugin: trajectory_recorder
==================================
Comprehensive Trajectory & Session Observability Engine.
Records every prompt, System-2 reasoning trace, tool invocation, observation,
exit code, and test outcome into an offline SQLite WAL store.
Features SWE-agent observation windowing (head/tail truncation) to prevent context rot.
"""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def get_trajectories_db_path() -> Path:
    """Returns canonical SQLite database path for trajectories."""
    hermes_home = os.environ.get("HERMES_HOME")
    if hermes_home:
        base = Path(hermes_home) / "cache"
    else:
        base = Path.home() / ".hermes" / "cache"
    base.mkdir(parents=True, exist_ok=True)
    return base / "trajectories.db"


class TrajectoryRecorder:
    """Core engine recording agent interaction trajectories and execution feedback."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or get_trajectories_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    turns_count INTEGER DEFAULT 0,
                    final_status TEXT DEFAULT 'RUNNING',
                    avg_reward REAL DEFAULT 1.0
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trajectories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    turn_index INTEGER NOT NULL,
                    role TEXT DEFAULT 'coder',
                    prompt TEXT,
                    reasoning_trace TEXT,
                    action_code TEXT,
                    tool_name TEXT,
                    tool_args TEXT,
                    tool_output TEXT,
                    windowed_output TEXT,
                    exit_code INTEGER DEFAULT 0,
                    test_status TEXT DEFAULT 'PENDING',
                    constitutional_score REAL DEFAULT 1.0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_traj_session ON trajectories (session_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_traj_score ON trajectories (constitutional_score);")

    @staticmethod
    def window_observation(output: str, max_lines: int = 50, command: str = "") -> str:
        """SWE-agent observation windowing: truncates output keeping head and tail lines.
        Expands window for package manager commands (dnf, apt, pip, cargo, npm) to allow up to 2048 chars / 100 lines.
        """
        if not output:
            return ""
        cmd_str = (command or "").lower()
        is_pkg_mgr = any(pkg in cmd_str for pkg in ("dnf", "apt", "pip", "cargo", "npm", "yum", "pacman"))
        effective_max = 100 if is_pkg_mgr else max_lines
        lines = output.splitlines()
        if len(lines) <= effective_max:
            return output
        
        half = effective_max // 2
        truncated_count = len(lines) - (half * 2)
        head = "\n".join(lines[:half])
        tail = "\n".join(lines[-half:])
        return f"{head}\n\n[... {truncated_count} lines truncated by observation windowing ...]\n\n{tail}"

    def record_turn(
        self,
        session_id: str,
        turn_index: int,
        role: str = "coder",
        prompt: Optional[str] = None,
        reasoning_trace: Optional[str] = None,
        action_code: Optional[str] = None,
        tool_name: Optional[str] = None,
        tool_args: Optional[Dict[str, Any]] = None,
        tool_output: Optional[str] = None,
        exit_code: int = 0,
        test_status: str = "PENDING",
        constitutional_score: float = 1.0,
    ) -> int:
        """Records a single interactive turn into SQLite store."""
        now = datetime.now(timezone.utc).isoformat()
        args_json = json.dumps(tool_args or {}) if tool_args else None
        raw_output = tool_output or ""
        cmd = (tool_args or {}).get("command", "") if isinstance(tool_args, dict) else ""
        windowed = self.window_observation(raw_output, command=cmd)

        with self._get_conn() as conn:
            # Ensure session entry exists
            conn.execute("""
                INSERT INTO sessions (session_id, started_at, turns_count, final_status, avg_reward)
                VALUES (?, ?, 1, 'RUNNING', ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    turns_count = turns_count + 1,
                    avg_reward = (avg_reward + excluded.avg_reward) / 2.0;
            """, (session_id, now, constitutional_score))

            cursor = conn.execute("""
                INSERT INTO trajectories (
                    session_id, turn_index, role, prompt, reasoning_trace,
                    action_code, tool_name, tool_args, tool_output, windowed_output,
                    exit_code, test_status, constitutional_score, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, turn_index, role, prompt, reasoning_trace,
                action_code, tool_name, args_json, raw_output, windowed,
                exit_code, test_status, constitutional_score, now
            ))
            return cursor.lastrowid

    def end_session(self, session_id: str, final_status: str = "COMPLETED") -> None:
        """Marks a session as finished with its final status."""
        now = datetime.now(timezone.utc).isoformat()
        with self._get_conn() as conn:
            conn.execute("""
                UPDATE sessions
                SET ended_at = ?, final_status = ?
                WHERE session_id = ?;
            """, (now, final_status, session_id))

    def list_trajectories(self, limit: int = 10, frontier_only: bool = False) -> List[Dict[str, Any]]:
        """Lists sessions, optionally filtering to the [0.3, 0.7] learnability frontier."""
        query = """
            SELECT session_id, started_at, ended_at, turns_count, final_status, avg_reward
            FROM sessions
        """
        params = []
        if frontier_only:
            query += " WHERE avg_reward >= 0.3 AND avg_reward <= 0.7"
        query += " ORDER BY started_at DESC LIMIT ?"
        params.append(limit)

        results = []
        with self._get_conn() as conn:
            cur = conn.execute(query, params)
            for row in cur.fetchall():
                results.append({
                    "session_id": row[0],
                    "started_at": row[1],
                    "ended_at": row[2],
                    "turns_count": row[3],
                    "final_status": row[4],
                    "avg_reward": round(row[5], 3),
                })
        return results

    def get_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieves all turns for a specific session."""
        turns = []
        with self._get_conn() as conn:
            cur = conn.execute("""
                SELECT turn_index, role, prompt, reasoning_trace, action_code,
                       tool_name, tool_args, windowed_output, exit_code, test_status,
                       constitutional_score, created_at
                FROM trajectories
                WHERE session_id = ?
                ORDER BY turn_index ASC;
            """, (session_id,))
            for row in cur.fetchall():
                turns.append({
                    "turn_index": row[0],
                    "role": row[1],
                    "prompt": row[2],
                    "reasoning_trace": row[3],
                    "action_code": row[4],
                    "tool_name": row[5],
                    "tool_args": json.loads(row[6]) if row[6] else {},
                    "windowed_output": row[7],
                    "exit_code": row[8],
                    "test_status": row[9],
                    "constitutional_score": row[10],
                    "created_at": row[11],
                })
        return turns

    def export_dataset(self, output_file: Path, frontier_only: bool = False) -> int:
        """Exports trajectories into JSONL dataset format for SFT and RL post-training."""
        output_file.parent.mkdir(parents=True, exist_ok=True)
        count = 0

        with self._get_conn() as conn:
            query = "SELECT session_id FROM sessions"
            if frontier_only:
                query += " WHERE avg_reward >= 0.3 AND avg_reward <= 0.7"
            query += " ORDER BY started_at ASC"

            cur = conn.execute(query)
            session_ids = [r[0] for r in cur.fetchall()]

        with open(output_file, "w", encoding="utf-8") as f:
            for sid in session_ids:
                turns = self.get_session(sid)
                if not turns:
                    continue
                entry = {
                    "session_id": sid,
                    "conversations": [
                        {
                            "turn": t["turn_index"],
                            "role": t["role"],
                            "prompt": t["prompt"],
                            "thought": t["reasoning_trace"],
                            "tool": t["tool_name"],
                            "args": t["tool_args"],
                            "observation": t["windowed_output"],
                            "test_status": t["test_status"],
                            "score": t["constitutional_score"],
                        }
                        for t in turns
                    ]
                }
                f.write(json.dumps(entry) + "\n")
                count += 1

        return count


_GLOBAL_RECORDER: Optional[TrajectoryRecorder] = None


def get_trajectory_recorder() -> TrajectoryRecorder:
    global _GLOBAL_RECORDER
    if _GLOBAL_RECORDER is None:
        _GLOBAL_RECORDER = TrajectoryRecorder()
    return _GLOBAL_RECORDER


def register(ctx=None):
    """Registers trajectory_recorder commands and hooks into Hermes runtime."""
    if not ctx:
        return True

    recorder = get_trajectory_recorder()

    # 1. Register CLI Subcommand
    if hasattr(ctx, "register_cli_command"):
        def setup_trajectory(parser):
            parser.description = "Inspect, list, and export agent session trajectories"
            sub = parser.add_subparsers(dest="traj_cmd")

            # hermes trajectory list [--limit N] [--frontier-only]
            list_p = sub.add_parser("list", help="List recorded agent trajectories")
            list_p.add_argument("--limit", type=int, default=10, help="Max entries to show")
            list_p.add_argument("--frontier-only", action="store_true", help="Filter to [0.3, 0.7] learnability frontier")

            # hermes trajectory show <session_id>
            show_p = sub.add_parser("show", help="Show full turn details for a session")
            show_p.add_argument("session_id", help="Session ID to inspect")

            # hermes trajectory export [--output file] [--frontier-only]
            export_p = sub.add_parser("export", help="Export trajectories to JSONL for offline training")
            export_p.add_argument("--output", default="training_buffer/trajectories_export.jsonl", help="Output path")
            export_p.add_argument("--frontier-only", action="store_true", help="Filter to [0.3, 0.7] learnability frontier")

        def handle_trajectory(args):
            cmd = getattr(args, "traj_cmd", "list") or "list"
            if cmd == "list":
                items = recorder.list_trajectories(limit=args.limit, frontier_only=args.frontier_only)
                if not items:
                    print("No recorded trajectories found.")
                    return 0
                print(f"Recorded Agent Trajectories (Count: {len(items)}):")
                for item in items:
                    status = item["final_status"]
                    print(f"  • [{item['session_id']}] Turns: {item['turns_count']} | Status: {status} | Score: {item['avg_reward']}")
                return 0

            elif cmd == "show":
                turns = recorder.get_session(args.session_id)
                if not turns:
                    print(f"No turns found for session '{args.session_id}'.")
                    return 1
                print(f"=== Session Trajectory: {args.session_id} ({len(turns)} turns) ===")
                for t in turns:
                    print(f"\n[Turn {t['turn_index']}] Role: {t['role']} | Status: {t['test_status']} | Score: {t['constitutional_score']}")
                    if t.get("prompt"):
                        print(f"  Prompt: {t['prompt'][:100]}...")
                    if t.get("reasoning_trace"):
                        print(f"  Reasoning: {t['reasoning_trace'][:120]}...")
                    if t.get("tool_name"):
                        print(f"  Tool: {t['tool_name']} {json.dumps(t['tool_args'])}")
                    if t.get("windowed_output"):
                        print(f"  Output:\n    {t['windowed_output'][:200]}...")
                return 0

            elif cmd == "export":
                out_path = Path(args.output)
                count = recorder.export_dataset(out_path, frontier_only=args.frontier_only)
                print(f"✓ Exported {count} trajectories to {out_path} (frontier_only={args.frontier_only})")
                return 0

            return 0

        ctx.register_cli_command("trajectory", "Manage and inspect agent trajectory database", setup_trajectory, handle_trajectory)

    # 2. Register Slash Command
    if hasattr(ctx, "register_command"):
        def slash_trajectory(raw_args: str) -> str:
            items = recorder.list_trajectories(limit=5)
            if not items:
                return "No recorded trajectories in database."
            out = ["**Recent Agent Trajectories**:"]
            for item in items:
                out.append(f"- `{item['session_id']}` ({item['turns_count']} turns, reward: {item['avg_reward']}, {item['final_status']})")
            return "\n".join(out)

        ctx.register_command("trajectory", slash_trajectory, "List recent trajectories", "")

    # 3. Register Lifecycle Hooks
    if hasattr(ctx, "register_hook"):
        def trajectory_post_tool_hook(**kwargs):
            session_id = kwargs.get("session_id") or "live_session"
            turn_index = kwargs.get("turn_index", 0)
            tool_name = kwargs.get("tool_name", "unknown")
            tool_args = kwargs.get("tool_args", {})
            output = kwargs.get("output", "")
            role = kwargs.get("role", "coder")
            score = kwargs.get("score", 1.0)
            status = kwargs.get("test_status", "PENDING")

            recorder.record_turn(
                session_id=session_id,
                turn_index=turn_index,
                role=role,
                tool_name=tool_name,
                tool_args=tool_args,
                tool_output=str(output),
                test_status=status,
                constitutional_score=score,
            )
            return {"action": "continue"}

        ctx.register_hook("post_tool_call", trajectory_post_tool_hook)

    return True


__all__ = [
    "TrajectoryRecorder",
    "get_trajectories_db_path",
    "get_trajectory_recorder",
    "register",
]
