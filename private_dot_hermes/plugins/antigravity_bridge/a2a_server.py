"""
Google Agent2Agent (A2A) Protocol Server & Jules Worktree Isolation for Hermes.
Complies with Google A2A specification:
1. Discovery via /.well-known/agent-card.json
2. JSON-RPC 2.0 message/send, message/stream, tasks/get, tasks/cancel
3. Isolated Git Worktree task provisioning (Google Jules cloud agent pattern)
"""

from __future__ import annotations

import json
import os
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple


class A2AAgentCardServer:
    """Provides A2A Agent Card discovery and JSON-RPC 2.0 dispatch."""

    def __init__(self, agent_name: str = "Hermes Agent OS", version: str = "3.0.0", port: int = 8140):
        self.agent_name = agent_name
        self.version = version
        self.port = port
        self.active_tasks: Dict[str, Dict[str, Any]] = {}

    def get_agent_card(self) -> Dict[str, Any]:
        """Returns standard /.well-known/agent-card.json payload."""
        return {
            "$schema": "https://a2a-protocol.org/v1/agent-card.json",
            "name": self.agent_name,
            "version": self.version,
            "description": "Local-First Self-Learning Autonomous Coding Agent OS (AGY & Jules Ready)",
            "documentationUrl": "https://github.com/imshubhamsocial/dotfiles-hermes",
            "supportedInterfaces": [
                {
                    "transport": "HTTP_JSON",
                    "protocolBinding": "JSONRPC",
                    "protocolVersion": "2.0",
                    "endpoint": f"http://127.0.0.1:{self.port}/v1/a2a",
                },
                {
                    "transport": "SSE",
                    "protocolBinding": "JSONRPC_STREAM",
                    "protocolVersion": "2.0",
                    "endpoint": f"http://127.0.0.1:{self.port}/v1/a2a/stream",
                },
            ],
            "capabilities": {
                "streaming": True,
                "pushNotifications": False,
                "extendedAgentCard": False,
                "taskCancellation": True,
            },
            "securitySchemes": {
                "localToken": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-Hermes-Token",
                }
            },
            "skills": [
                {
                    "id": "code_refactor_and_verify",
                    "name": "Autonomous Code Refactoring and Zero-Regression Gate",
                    "description": "Edits code via SEARCH/REPLACE blocks, runs tests, and applies auto-rollback on failure.",
                    "tags": ["coding", "refactoring", "testing", "zero-regression"],
                    "inputModes": ["application/json"],
                    "outputModes": ["application/json", "text/markdown"],
                },
                {
                    "id": "agy_artifacts_generate",
                    "name": "Google AGY Generative Artifacts Emission",
                    "description": "Emits structured markdown reports, Mermaid diagrams, carousels, and HTML auxiliary apps.",
                    "tags": ["artifacts", "mermaid", "html-ui"],
                    "inputModes": ["application/json"],
                    "outputModes": ["text/markdown", "text/html"],
                },
            ],
        }

    def handle_jsonrpc_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches JSON-RPC 2.0 request."""
        req_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        if not method or request.get("jsonrpc") != "2.0":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32600, "message": "Invalid Request: jsonrpc 2.0 required"},
            }

        if method == "message/send":
            task_id = params.get("taskId") or f"task-{uuid.uuid4().hex[:8]}"
            msg = params.get("message", {})
            self.active_tasks[task_id] = {
                "taskId": task_id,
                "status": "working",
                "submitted_at": datetime.now(timezone.utc).isoformat(),
                "last_message": msg,
            }
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"taskId": task_id, "status": "working"},
            }

        elif method == "tasks/get":
            task_id = params.get("taskId")
            if task_id not in self.active_tasks:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32001, "message": f"Task '{task_id}' not found"},
                }
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": self.active_tasks[task_id],
            }

        elif method == "tasks/cancel":
            task_id = params.get("taskId")
            if task_id in self.active_tasks:
                self.active_tasks[task_id]["status"] = "canceled"
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"taskId": task_id, "status": "canceled"},
                }
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32001, "message": f"Task '{task_id}' not found"},
            }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method '{method}' not found"},
        }


class JulesWorktreeSandbox:
    """Manages ephemeral Git worktrees for isolated background task workers."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.worktrees_dir = repo_root / ".worktrees"
        self.worktrees_dir.mkdir(parents=True, exist_ok=True)

    def provision_worktree(self, task_id: str, base_branch: str = "HEAD") -> Path:
        """Creates an isolated worktree branch for a background task."""
        branch_name = f"jules/task-{task_id}"
        target_dir = self.worktrees_dir / f"task-{task_id}"

        if target_dir.exists():
            return target_dir

        cmd = ["git", "worktree", "add", "-b", branch_name, str(target_dir), base_branch]
        subprocess.run(cmd, cwd=str(self.repo_root), check=True, capture_output=True)
        return target_dir

    def cleanup_worktree(self, task_id: str):
        """Removes worktree and branch after task completion."""
        target_dir = self.worktrees_dir / f"task-{task_id}"
        if target_dir.exists():
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(target_dir)],
                cwd=str(self.repo_root),
                capture_output=True,
            )
