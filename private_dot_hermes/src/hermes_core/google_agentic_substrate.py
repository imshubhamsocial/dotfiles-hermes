"""
Google Antigravity & Env-Harness Agentic Substrate (Milestone U80)
===================================================================
NOTE (Domain 7): Superseded by official 'google-adk' runtime (HermesADKCustomAgent
and DomainFleetManager in domain_fleet.py). Retained strictly as a lightweight
compatibility shim for Milestone U80 contract test certification.

Provides:
1. Google-Standard Tool Calling Schemas with exact parameter typing,
   toolAction, toolSummary, enums, and JSON-LD schema bounds.
2. Google Antigravity & Env-Harness Subagent Delegation Engine supporting
   asymmetric clean-room workspaces ('inherit', 'branch', 'share'),
   model tiers ('inherit', 'flash_lite', 'flash', 'pro'), non-blocking
   messaging ('send_message'), and lifecycle management ('manage_subagents').
"""

from __future__ import annotations

import json
import os
import shutil
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


# ============================================================================
# 1. GOOGLE-STANDARD TOOL CALLING SCHEMAS
# ============================================================================

class GoogleToolSchemaRegistry:
    """Maintains official Google Antigravity & Gemini 3.7 tool calling schemas."""

    @staticmethod
    def get_all_schemas() -> List[Dict[str, Any]]:
        return [
            GoogleToolSchemaRegistry.run_command_schema(),
            GoogleToolSchemaRegistry.view_file_schema(),
            GoogleToolSchemaRegistry.replace_file_content_schema(),
            GoogleToolSchemaRegistry.write_to_file_schema(),
            GoogleToolSchemaRegistry.grep_search_schema(),
            GoogleToolSchemaRegistry.find_by_name_schema(),
            GoogleToolSchemaRegistry.search_web_schema(),
            GoogleToolSchemaRegistry.read_url_content_schema(),
            GoogleToolSchemaRegistry.invoke_subagent_schema(),
            GoogleToolSchemaRegistry.send_message_schema(),
            GoogleToolSchemaRegistry.manage_subagents_schema(),
            GoogleToolSchemaRegistry.schedule_schema(),
            GoogleToolSchemaRegistry.ask_question_schema(),
        ]

    @staticmethod
    def run_command_schema() -> Dict[str, Any]:
        return {
            "name": "run_command",
            "description": "PROPOSE a command to run on behalf of the user. Operating System: linux. Shell: bash.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "CommandLine": {"type": "STRING", "description": "The exact command line string to execute."},
                    "Cwd": {"type": "STRING", "description": "The current working directory for the command."},
                    "WaitMsBeforeAsync": {"type": "INTEGER", "description": "Milliseconds to wait synchronously before backgrounding."},
                    "toolAction": {"type": "STRING", "description": "Brief 2-5 word summary of action (e.g. 'Running command')."},
                    "toolSummary": {"type": "STRING", "description": "Brief 2-5 word noun phrase (e.g. 'Command execution')."},
                },
                "required": ["CommandLine", "Cwd", "WaitMsBeforeAsync", "toolAction", "toolSummary"],
            },
        }

    @staticmethod
    def view_file_schema() -> Dict[str, Any]:
        return {
            "name": "view_file",
            "description": "View the contents of a file from the local filesystem with line range support.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "AbsolutePath": {"type": "STRING", "description": "Path to file to view. Must be absolute."},
                    "StartLine": {"type": "INTEGER", "description": "Optional start line number, 1-indexed."},
                    "EndLine": {"type": "INTEGER", "description": "Optional end line number, 1-indexed."},
                    "toolAction": {"type": "STRING", "description": "Brief 2-5 word summary (e.g. 'Viewing file')."},
                    "toolSummary": {"type": "STRING", "description": "Brief 2-5 word noun phrase (e.g. 'File view')."},
                },
                "required": ["AbsolutePath", "toolAction", "toolSummary"],
            },
        }

    @staticmethod
    def replace_file_content_schema() -> Dict[str, Any]:
        return {
            "name": "replace_file_content",
            "description": "Edits an existing file by replacing a single contiguous block of text matching TargetContent.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "TargetFile": {"type": "STRING", "description": "The target file to modify. Must be absolute."},
                    "Instruction": {"type": "STRING", "description": "A description of the changes being made."},
                    "Description": {"type": "STRING", "description": "User-facing rationale for the change."},
                    "TargetContent": {"type": "STRING", "description": "The exact character sequence to be replaced."},
                    "ReplacementContent": {"type": "STRING", "description": "The replacement content to substitute."},
                    "StartLine": {"type": "INTEGER", "description": "Starting line number containing target content."},
                    "EndLine": {"type": "INTEGER", "description": "Ending line number containing target content."},
                    "AllowMultiple": {"type": "BOOLEAN", "description": "Whether to replace multiple occurrences."},
                    "toolAction": {"type": "STRING", "description": "Brief 2-5 word summary (e.g. 'Editing file')."},
                    "toolSummary": {"type": "STRING", "description": "Brief 2-5 word noun phrase (e.g. 'File edit')."},
                },
                "required": ["TargetFile", "Instruction", "Description", "TargetContent", "ReplacementContent", "StartLine", "EndLine", "AllowMultiple", "toolAction", "toolSummary"],
            },
        }

    @staticmethod
    def write_to_file_schema() -> Dict[str, Any]:
        return {
            "name": "write_to_file",
            "description": "Create new files or overwrite existing files with verified code or artifacts.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "TargetFile": {"type": "STRING", "description": "The target file path to create."},
                    "CodeContent": {"type": "STRING", "description": "The exact code content to write."},
                    "Description": {"type": "STRING", "description": "User-facing explanation of what this file does."},
                    "Overwrite": {"type": "BOOLEAN", "description": "Set true to overwrite an existing file."},
                    "toolAction": {"type": "STRING", "description": "Brief 2-5 word summary."},
                    "toolSummary": {"type": "STRING", "description": "Brief 2-5 word noun phrase."},
                },
                "required": ["TargetFile", "CodeContent", "Description", "Overwrite", "toolAction", "toolSummary"],
            },
        }

    @staticmethod
    def grep_search_schema() -> Dict[str, Any]:
        return {
            "name": "grep_search",
            "description": "Fast ripgrep pattern matching across files and directories.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "SearchPath": {"type": "STRING", "description": "Directory or file to search."},
                    "Query": {"type": "STRING", "description": "Search term or regex pattern."},
                    "IsRegex": {"type": "BOOLEAN", "description": "Treat query as regex if true."},
                    "CaseInsensitive": {"type": "BOOLEAN", "description": "Case-insensitive search if true."},
                    "MatchPerLine": {"type": "BOOLEAN", "description": "Return line snippets if true."},
                    "toolAction": {"type": "STRING", "description": "Brief 2-5 word summary."},
                    "toolSummary": {"type": "STRING", "description": "Brief 2-5 word noun phrase."},
                },
                "required": ["SearchPath", "Query", "toolAction", "toolSummary"],
            },
        }

    @staticmethod
    def find_by_name_schema() -> Dict[str, Any]:
        return {
            "name": "find_by_name",
            "description": "Search for files and directories matching a glob pattern using fd.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "SearchDirectory": {"type": "STRING", "description": "Directory to search within."},
                    "Pattern": {"type": "STRING", "description": "Glob pattern to search for."},
                    "toolAction": {"type": "STRING", "description": "Brief 2-5 word summary."},
                    "toolSummary": {"type": "STRING", "description": "Brief 2-5 word noun phrase."},
                },
                "required": ["SearchDirectory", "Pattern", "toolAction", "toolSummary"],
            },
        }

    @staticmethod
    def search_web_schema() -> Dict[str, Any]:
        return {
            "name": "search_web",
            "description": "Performs keyless local SearXNG meta-search returning grounded summaries and URL citations.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "query": {"type": "STRING", "description": "Web search query."},
                    "domain": {"type": "STRING", "description": "Optional priority domain recommendation."},
                    "toolAction": {"type": "STRING", "description": "Brief 2-5 word summary."},
                    "toolSummary": {"type": "STRING", "description": "Brief 2-5 word noun phrase."},
                },
                "required": ["query", "toolAction", "toolSummary"],
            },
        }

    @staticmethod
    def read_url_content_schema() -> Dict[str, Any]:
        return {
            "name": "read_url_content",
            "description": "Fetch content from a URL via HTTP request and convert HTML to clean Markdown.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "Url": {"type": "STRING", "description": "The URL to fetch and convert."},
                    "toolAction": {"type": "STRING", "description": "Brief 2-5 word summary."},
                    "toolSummary": {"type": "STRING", "description": "Brief 2-5 word noun phrase."},
                },
                "required": ["Url", "toolAction", "toolSummary"],
            },
        }

    @staticmethod
    def invoke_subagent_schema() -> Dict[str, Any]:
        return {
            "name": "invoke_subagent",
            "description": "Invokes one or more specialized subagents concurrently in isolated workspaces.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "Subagents": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "TypeName": {"type": "STRING", "description": "Bot type (e.g. 'architect', 'coder', 'tester', 'researcher')."},
                                "Role": {"type": "STRING", "description": "Descriptive job title for the subagent."},
                                "Prompt": {"type": "STRING", "description": "Clear, actionable task description."},
                                "Model": {"type": "STRING", "enum": ["inherit", "flash_lite", "flash", "pro"], "description": "Model tier."},
                                "Workspace": {"type": "STRING", "enum": ["inherit", "branch", "share"], "description": "Workspace isolation mode."},
                            },
                            "required": ["TypeName", "Role", "Prompt"],
                        },
                    },
                    "toolAction": {"type": "STRING", "description": "Brief 2-5 word summary."},
                    "toolSummary": {"type": "STRING", "description": "Brief 2-5 word noun phrase."},
                },
                "required": ["Subagents", "toolAction", "toolSummary"],
            },
        }

    @staticmethod
    def send_message_schema() -> Dict[str, Any]:
        return {
            "name": "send_message",
            "description": "Send a non-blocking message to a running subagent by its conversation ID.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "Recipient": {"type": "STRING", "description": "Conversation ID of the recipient subagent."},
                    "Message": {"type": "STRING", "description": "Message content to deliver."},
                    "toolAction": {"type": "STRING", "description": "Brief 2-5 word summary."},
                    "toolSummary": {"type": "STRING", "description": "Brief 2-5 word noun phrase."},
                },
                "required": ["Recipient", "Message", "toolAction", "toolSummary"],
            },
        }

    @staticmethod
    def manage_subagents_schema() -> Dict[str, Any]:
        return {
            "name": "manage_subagents",
            "description": "List active subagents or terminate specific/all subagents.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "Action": {"type": "STRING", "enum": ["list", "kill", "kill_all"], "description": "Action to perform."},
                    "ConversationIds": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "IDs to kill if Action is 'kill'."},
                    "toolAction": {"type": "STRING", "description": "Brief 2-5 word summary."},
                    "toolSummary": {"type": "STRING", "description": "Brief 2-5 word noun phrase."},
                },
                "required": ["Action", "toolAction", "toolSummary"],
            },
        }

    @staticmethod
    def schedule_schema() -> Dict[str, Any]:
        return {
            "name": "schedule",
            "description": "Schedule a one-shot timer or recurring cron job that sends high-priority notifications.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "DurationSeconds": {"type": "INTEGER", "description": "Number of seconds to wait for one-shot timer."},
                    "CronExpression": {"type": "STRING", "description": "Standard 5-field cron expression for recurring schedules."},
                    "Prompt": {"type": "STRING", "description": "The message to include in notification when timer fires."},
                    "TimerCondition": {"type": "STRING", "description": "'never', 'any', or specific sender task/conv ID."},
                    "toolAction": {"type": "STRING", "description": "Brief 2-5 word summary."},
                    "toolSummary": {"type": "STRING", "description": "Brief 2-5 word noun phrase."},
                },
                "required": ["Prompt", "toolAction", "toolSummary"],
            },
        }

    @staticmethod
    def ask_question_schema() -> Dict[str, Any]:
        return {
            "name": "ask_question",
            "description": "Presents an interactive multi-choice question modal to the user for human-in-the-loop decisions.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "questions": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "question": {"type": "STRING", "description": "The question to ask."},
                                "options": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Selectable options."},
                                "is_multi_select": {"type": "BOOLEAN", "description": "Allow multiple option selections if true."},
                            },
                            "required": ["question", "options"],
                        },
                    },
                    "toolAction": {"type": "STRING", "description": "Brief 2-5 word summary."},
                    "toolSummary": {"type": "STRING", "description": "Brief 2-5 word noun phrase."},
                },
                "required": ["questions", "toolAction", "toolSummary"],
            },
        }


# ============================================================================
# 2. GOOGLE ANTIGRAVITY & ENV-HARNESS SUBAGENT DELEGATION ENGINE
# ============================================================================

@dataclass
class SubagentSpec:
    TypeName: str
    Role: str
    Prompt: str
    Model: str = "inherit"
    Workspace: str = "inherit"


@dataclass
class SubagentInstance:
    conversation_id: str
    type_name: str
    role: str
    prompt: str
    model: str
    workspace_mode: str
    workspace_dir: Path
    state: str = "running"  # running, idle, waiting_for_message, done, killed
    created_at: float = field(default_factory=time.time)
    inbox: List[str] = field(default_factory=list)
    output: Optional[str] = None


class GoogleSubagentDelegationEngine:
    """Manages asynchronous subagents in clean-room isolated scratchpads."""

    def __init__(self, scratchpad_root: Optional[Path] = None):
        self.scratchpad_root = scratchpad_root or Path("/dev/shm/hermes_subagents")
        self.scratchpad_root.mkdir(parents=True, exist_ok=True)
        self.subagents: Dict[str, SubagentInstance] = {}

    def invoke_subagents(
        self,
        specs: List[Union[SubagentSpec, Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """Spawns one or more subagents concurrently in isolated workspaces."""
        spawned = []
        for s in specs:
            if isinstance(s, dict):
                spec = SubagentSpec(
                    TypeName=s.get("TypeName", "coder"),
                    Role=s.get("Role", "Specialist"),
                    Prompt=s.get("Prompt", ""),
                    Model=s.get("Model", "inherit"),
                    Workspace=s.get("Workspace", "inherit"),
                )
            else:
                spec = s

            conv_id = str(uuid.uuid4())
            if spec.Workspace == "branch":
                ws_dir = self.scratchpad_root / conv_id
                ws_dir.mkdir(parents=True, exist_ok=True)
            elif spec.Workspace == "share":
                ws_dir = Path(os.getcwd())
            else:
                ws_dir = Path(os.getcwd())

            instance = SubagentInstance(
                conversation_id=conv_id,
                type_name=spec.TypeName,
                role=spec.Role,
                prompt=spec.Prompt,
                model=spec.Model,
                workspace_mode=spec.Workspace,
                workspace_dir=ws_dir,
                state="running",
            )
            self.subagents[conv_id] = instance
            spawned.append({
                "conversationId": conv_id,
                "typeName": spec.TypeName,
                "role": spec.Role,
                "workspace": str(ws_dir),
                "state": "running",
            })

        return spawned

    def send_message(self, recipient_id: str, message: str) -> bool:
        """Delivers a non-blocking message to a running subagent."""
        if recipient_id not in self.subagents:
            return False
        agent = self.subagents[recipient_id]
        if agent.state in ["killed", "done"]:
            return False
        agent.inbox.append(message)
        agent.state = "running"
        return True

    def manage_subagents(
        self,
        action: str,
        conversation_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Manages lifecycle: 'list', 'kill', 'kill_all'."""
        if action == "list":
            return {
                "active_count": sum(1 for a in self.subagents.values() if a.state == "running"),
                "subagents": [
                    {
                        "conversationId": a.conversation_id,
                        "type": a.type_name,
                        "role": a.role,
                        "state": a.state,
                        "workspace": str(a.workspace_dir),
                    }
                    for a in self.subagents.values()
                ],
            }
        elif action == "kill":
            killed = []
            for cid in (conversation_ids or []):
                if cid in self.subagents:
                    self.subagents[cid].state = "killed"
                    if self.subagents[cid].workspace_mode == "branch":
                        shutil.rmtree(self.subagents[cid].workspace_dir, ignore_errors=True)
                    killed.append(cid)
            return {"action": "kill", "killed": killed}
        elif action == "kill_all":
            all_ids = list(self.subagents.keys())
            for cid in all_ids:
                self.subagents[cid].state = "killed"
                if self.subagents[cid].workspace_mode == "branch":
                    shutil.rmtree(self.subagents[cid].workspace_dir, ignore_errors=True)
            return {"action": "kill_all", "killed_count": len(all_ids)}
        return {"error": f"Unknown action: {action}"}


def create_google_subagent_engine(scratchpad_root: Optional[Path] = None) -> GoogleSubagentDelegationEngine:
    return GoogleSubagentDelegationEngine(scratchpad_root=scratchpad_root)
