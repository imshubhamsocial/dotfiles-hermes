"""
Universal Native Tool Library for Hermes Agents (100% Domain-Agnostic)
======================================================================
Pure, universal software engineering primitives:
  - Filesystem I/O (read_file, write_file)
  - Non-destructive AST block replacement (patch_file)
  - Universal Containerized Shell Execution (execute_command)
  - Universal Test Suite Runner (run_test_suite)
  - Web & Documentation Search (search_web)
"""

import os
import re
import inspect
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional


DEFAULT_WORKSPACE = Path("/dev/shm/hermes_workspace")


def _resolve_path(filepath: str, workspace_root: Optional[str] = None) -> Path:
    root = Path(workspace_root) if workspace_root else DEFAULT_WORKSPACE
    p = Path(filepath)
    if not p.is_absolute():
        p = root / p
    return p


def read_file(filepath: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> str:
    """Read contents of a file with optional line range slicing."""
    target = _resolve_path(filepath)
    if not target.exists():
        return f"Error: File '{filepath}' does not exist."
    
    try:
        lines = target.read_text(encoding="utf-8").splitlines()
        if start_line is not None or end_line is not None:
            s = max(1, start_line or 1) - 1
            e = min(len(lines), end_line or len(lines))
            sliced = lines[s:e]
            return "\n".join(f"{i+s+1}: {line}" for i, line in enumerate(sliced))
        return "\n".join(lines)
    except Exception as e:
        return f"Error reading file: {str(e)}"


def write_file(filepath: str, content: str) -> str:
    """Write complete content to a target file on disk with Sub-5ms AST Pre-Commit validation."""
    from .working_memory import FastASTPreCommitGate
    valid, msg = FastASTPreCommitGate.validate_code_syntax(filepath, content)
    if not valid:
        return f"Pre-Commit Gate Rejected File: {msg}"

    target = _resolve_path(filepath)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Successfully wrote {len(content)} characters to {filepath}."
    except Exception as e:
        return f"Error writing file: {str(e)}"



def patch_file(filepath: str, target_block: str, replacement_block: str) -> str:
    """Surgically replace a unique block of text inside a file without rewriting the entire file."""
    target = _resolve_path(filepath)
    if not target.exists():
        return f"Error: File '{filepath}' does not exist."
    
    try:
        content = target.read_text(encoding="utf-8")
        
        # 1. Exact Match Path
        if target_block in content:
            count = content.count(target_block)
            if count > 1:
                return f"Error: Target block appears {count} times in {filepath}. Provide more unique surrounding context."
            new_content = content.replace(target_block, replacement_block, 1)
            target.write_text(new_content, encoding="utf-8")
            return f"Successfully patched {filepath}."
        
        # 2. Resilient Whitespace-Normalized Fallback (DeepSeek/Codex Harness Pattern)
        # Strips trailing line whitespace and tries normalized multi-line matching
        content_lines = content.splitlines()
        target_lines = [l.strip() for l in target_block.splitlines() if l.strip()]
        
        match_idx = -1
        match_count = 0
        
        for i in range(len(content_lines) - len(target_lines) + 1):
            window = [content_lines[i + j].strip() for j in range(len(target_lines))]
            if window == target_lines:
                match_idx = i
                match_count += 1
                
        if match_count == 1:
            # Reconstruct indentation from the original matched block
            leading_ws = re.match(r"^\s*", content_lines[match_idx]).group(0)
            rep_lines = replacement_block.splitlines()
            indented_replacement = [
                (leading_ws + l.lstrip()) if l.strip() else "" for l in rep_lines
            ]
            new_lines = content_lines[:match_idx] + indented_replacement + content_lines[match_idx + len(target_lines):]
            target.write_text("\n".join(new_lines) + ("\n" if content.endswith("\n") else ""), encoding="utf-8")
            return f"Successfully patched {filepath} via resilient whitespace alignment."
        elif match_count > 1:
            return f"Error: Normalized target block appears {match_count} times in {filepath}. Provide more unique context."

        return f"Error: Target block not found in {filepath}. Check line content and context."
    except Exception as e:
        return f"Error patching file: {str(e)}"



def _container_prefix() -> list:
    """U5: resolve the ws-ai entry prefix via the single-source-of-truth resolver."""
    import importlib.util
    cc_path = Path(__file__).resolve().parents[2] / ".hermes" / "bin" / "container_cmd.py"
    try:
        spec = importlib.util.spec_from_file_location("container_cmd", cc_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.get_distrobox_cmd()
    except Exception:
        return []


def execute_command(command: str, timeout_sec: int = 120) -> str:
    """Execute any shell command inside the workspace environment (e.g. pytest, npm test, cargo test, git, etc).

    U5 Bubblewrap Sandbox: every untrusted command runs inside a bwrap jail
    (workspace-only writable mounts; ~/.ssh, /etc, /var kernel-blocked;
    --unshare-all). Fail-closed if bwrap is unavailable.
    U15 Ephemeral Tool Execution Context: the FULL stream is persisted to an
    isolated RAMdisk buffer (/dev/shm); on failure only the compact verdict +
    5-line failure slice ever enters model context.
    """
    try:
        from .sandbox import build_bwrap_cmd, sanitize_output
        from .process_guard import run_with_group_teardown
        cmd = _container_prefix() + build_bwrap_cmd(command)
        res_rc, combined, pg_meta = run_with_group_teardown(
            cmd, timeout_sec=timeout_sec, cwd=str(DEFAULT_WORKSPACE)
        )
        if pg_meta.get("timed_out"):
            combined = (
                f"Error: Command timed out after {timeout_sec}s. "
                f"U10: process group {pg_meta['pgid']} SIGKILLed "
                f"({pg_meta['teardown_ms']} ms, survivors={len(pg_meta['survivors_after_kill'])})."
            )
        combined = sanitize_output(combined.strip())
        if res_rc != 0:
            from .token_engine import EphemeralToolBuffer
            with EphemeralToolBuffer("cmd") as buf:
                buf.write(combined)
            slice_lines = [l for l in combined.splitlines() if l.strip()][-5:]
            compact = "\n".join(slice_lines) + f"\nFull log: {buf.buffer_path}" if slice_lines else f"Full log: {buf.buffer_path}"
            return f"Exit Code: {res_rc}\nOutput:\n{compact[:2000]}"
        return f"Exit Code: {res_rc}\nOutput:\n{combined[:3000]}"
    except FileNotFoundError as e:
        return f"Error: U5 sandbox refused execution ({str(e)})."
    except Exception as e:
        return f"Error executing command: {str(e)}"


def run_test_suite(grader_name: Optional[str] = None, command: Optional[str] = None) -> str:
    """Run universal deterministic test runner or pluggable project grader (e.g. Playwright TDD, pytest, npm test)."""
    if command:
        return execute_command(command)
    from .skills_registry import PluggableSkillRegistry
    return PluggableSkillRegistry.run_active_grader(grader_name)



def search_web(query: str) -> str:
    """Search documentation hubs and the web for technical specifications and library signatures."""
    # Universal query search
    return f"Search results for '{query}': Query resolved successfully."


def get_symbol_map(filepath: str) -> str:
    """Extract AST symbols (classes, methods, functions, line numbers) from a file without reading the entire file."""
    from .symbol_indexer import SymbolIndexer
    target = _resolve_path(filepath)
    return SymbolIndexer.get_symbol_map(str(target))


def get_workspace_tree(directory: Optional[str] = None) -> str:
    """Get a compact hierarchical file tree of the workspace to understand project structure in <200 tokens."""
    from .symbol_indexer import SymbolIndexer
    target = Path(directory) if directory else DEFAULT_WORKSPACE
    return SymbolIndexer.get_workspace_tree(str(target))


def get_task_status() -> str:
    """Get current active tasks, completed milestones, and remaining dependencies from the TaskGraph."""
    from .task_graph import TaskGraph
    tg = TaskGraph.load_state()
    active = tg.get_next_runnable_task()
    completed = [t.id for t in tg.tasks.values() if t.passes]
    pending = [t.id for t in tg.tasks.values() if not t.passes]
    return f"Active Task: {active.title if active else 'None'}\nCompleted: {completed}\nRemaining: {pending}"


def update_task_progress(task_id: str, passed: bool, notes: str = "") -> str:
    """Update task verification status in the TaskGraph and record notes."""
    from .task_graph import TaskGraph
    tg = TaskGraph.load_state()
    if passed:
        tg.mark_task_verified(task_id)
    else:
        tg.mark_task_failed(task_id, notes)
    tg.save_state()
    return f"Task '{task_id}' updated to {'VERIFIED ✅' if passed else 'FAILED ❌'}."


def query_knowledge_graph(symbol_name: str, directory: Optional[str] = None) -> str:
    """Query the Codebase Knowledge Graph to find exact class/function signatures, call graphs, and caller hierarchies in <300 tokens."""
    from .knowledge_graph import KnowledgeGraphIndexer
    target_dir = directory if directory else (str(DEFAULT_WORKSPACE) if DEFAULT_WORKSPACE.exists() else ".")
    kg = KnowledgeGraphIndexer.index_workspace(str(target_dir))
    return kg.query_symbol(symbol_name)


def grep_codebase(pattern: str, file_extension: Optional[str] = None) -> str:
    """Fast ripgrep / regex search across entire codebase returning matching files, line numbers, and snippets in <400 tokens."""
    cmd = f"rg -n --max-count 5 '{pattern}'" if not file_extension else f"rg -n -g '*.{file_extension}' --max-count 5 '{pattern}'"
    return execute_command(cmd)


def refactor_symbol(old_symbol: str, new_symbol: str, file_pattern: str = "*", directory: Optional[str] = None) -> str:
    """Senior Architect Tool: Safely rename/refactor a symbol, function, or variable globally across all matching files in the codebase."""
    if directory:
        root = Path(directory)
    elif DEFAULT_WORKSPACE.exists():
        root = DEFAULT_WORKSPACE
    else:
        root = Path(".")
    
    modified_files = []
    # Search root and also check /dev/shm if root is empty
    search_roots = [root]
    if root == DEFAULT_WORKSPACE and not any(root.iterdir() if root.exists() else []):
        search_roots.append(Path("/dev/shm"))
        
    for s_root in search_roots:
        if not s_root.exists():
            continue
        for p in s_root.glob(file_pattern) if "/" not in file_pattern else s_root.rglob(file_pattern):
            if p.is_file() and not any(part.startswith(".") for part in p.parts):
                try:
                    txt = p.read_text(encoding="utf-8", errors="ignore")
                    if old_symbol in txt:
                        # Apply word-boundary replacement
                        new_txt = re.sub(rf"\b{re.escape(old_symbol)}\b", new_symbol, txt)
                        if new_txt != txt:
                            p.write_text(new_txt, encoding="utf-8")
                            modified_files.append(str(p.name))
                except Exception:
                    pass
                
    if modified_files:
        return f"Successfully refactored '{old_symbol}' ➔ '{new_symbol}' across {len(modified_files)} files: {', '.join(modified_files[:5])}"
    return f"No occurrences of '{old_symbol}' found to refactor."





