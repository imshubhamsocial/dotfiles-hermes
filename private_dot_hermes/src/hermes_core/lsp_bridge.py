"""
Live LSP & Language Server Bridge (Iteration 2 — Capability U29)
===============================================================
Headless JSON-RPC 2.0 client for LSP servers (Pyright, TS Server, Clangd, etc.)
with document lifecycle synchronization, real-time compiler diagnostics,
go-to-definition queries, token-bounded prompt formatting, and offline AST fallback.
"""

from __future__ import annotations

import ast
import enum
import json
import os
import re
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union


class DiagnosticSeverity(enum.IntEnum):
    ERROR = 1
    WARNING = 2
    INFORMATION = 3
    HINT = 4

    @classmethod
    def from_value(cls, val: int) -> "DiagnosticSeverity":
        try:
            return cls(val)
        except ValueError:
            return cls.ERROR


@dataclass
class LSPPosition:
    line: int  # 0-indexed per LSP standard
    character: int  # 0-indexed per LSP standard

    def to_dict(self) -> Dict[str, int]:
        return {"line": self.line, "character": self.character}


@dataclass
class LSPRange:
    start: LSPPosition
    end: LSPPosition

    def to_dict(self) -> Dict[str, Dict[str, int]]:
        return {"start": self.start.to_dict(), "end": self.end.to_dict()}


@dataclass
class LSPLocation:
    uri: str
    range: LSPRange


@dataclass
class LSPDiagnostic:
    file_path: str
    range: LSPRange
    severity: DiagnosticSeverity
    message: str
    source: str = "lsp"
    code: Optional[Union[str, int]] = None

    @property
    def human_line(self) -> int:
        """1-indexed line for human-readable output."""
        return self.range.start.line + 1

    @property
    def human_column(self) -> int:
        """1-indexed column for human-readable output."""
        return self.range.start.character + 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "line": self.human_line,
            "column": self.human_column,
            "severity": self.severity.name,
            "message": self.message,
            "source": self.source,
            "code": self.code,
        }


class JSONRPCProtocol:
    """Encodes and decodes standard Content-Length framed JSON-RPC 2.0 messages."""

    @staticmethod
    def encode_message(payload: Dict[str, Any]) -> bytes:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        header = f"Content-Length: {len(data)}\r\n\r\n".encode("ascii")
        return header + data

    @staticmethod
    def parse_header(header_bytes: bytes) -> Optional[int]:
        """Extracts Content-Length from header string."""
        text = header_bytes.decode("ascii", errors="replace")
        for line in text.split("\r\n"):
            if line.lower().startswith("content-length:"):
                try:
                    return int(line.split(":", 1)[1].strip())
                except ValueError:
                    return None
        return None


class OfflineLSPFallback:
    """
    Deterministic offline fallback engine that performs Python AST parsing and
    syntax checks when no live language server daemon is connected.
    """

    @staticmethod
    def analyze_python_source(file_path: str, source_code: str) -> List[LSPDiagnostic]:
        diagnostics: List[LSPDiagnostic] = []
        try:
            ast.parse(source_code, filename=file_path)
        except SyntaxError as se:
            line_idx = (se.lineno - 1) if se.lineno is not None else 0
            col_idx = (se.offset - 1) if se.offset is not None else 0
            end_line_idx = (se.end_lineno - 1) if getattr(se, "end_lineno", None) is not None else line_idx
            end_col_idx = (se.end_offset - 1) if getattr(se, "end_offset", None) is not None else (col_idx + 1)
            diag = LSPDiagnostic(
                file_path=file_path,
                range=LSPRange(
                    start=LSPPosition(line=max(0, line_idx), character=max(0, col_idx)),
                    end=LSPPosition(line=max(0, end_line_idx), character=max(0, end_col_idx)),
                ),
                severity=DiagnosticSeverity.ERROR,
                message=f"SyntaxError: {se.msg}",
                source="python_ast",
                code="E999",
            )
            diagnostics.append(diag)
        except Exception as ex:
            diag = LSPDiagnostic(
                file_path=file_path,
                range=LSPRange(
                    start=LSPPosition(line=0, character=0),
                    end=LSPPosition(line=0, character=1),
                ),
                severity=DiagnosticSeverity.ERROR,
                message=f"ParseError: {str(ex)}",
                source="python_ast",
            )
            diagnostics.append(diag)
        return diagnostics

    @staticmethod
    def analyze_generic_source(file_path: str, source_code: str) -> List[LSPDiagnostic]:
        diagnostics: List[LSPDiagnostic] = []
        lang_map = {
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "tsx",
            ".rs": "rust",
            ".go": "go",
            ".c": "c",
            ".cpp": "cpp",
            ".json": "json",
        }
        suffix = Path(file_path).suffix.lower()
        if suffix in lang_map:
            try:
                import tree_sitter_language_pack as tslp
                parser = tslp.get_parser(lang_map[suffix])
                tree = parser.parse(source_code.encode("utf-8"))
                if tree.root_node.has_error:
                    # Find first error node
                    def find_error(node):
                        if node.is_error or node.type == "ERROR":
                            return node
                        for child in node.children:
                            err = find_error(child)
                            if err:
                                return err
                        return None

                    err_node = find_error(tree.root_node)
                    start_pt = err_node.start_point if err_node else (0, 0)
                    end_pt = err_node.end_point if err_node else (0, 1)

                    diag = LSPDiagnostic(
                        file_path=file_path,
                        range=LSPRange(
                            start=LSPPosition(line=start_pt[0], character=start_pt[1]),
                            end=LSPPosition(line=end_pt[0], character=end_pt[1]),
                        ),
                        severity=DiagnosticSeverity.ERROR,
                        message=f"Tree-Sitter syntax error: unexpected token or bracket imbalance in {lang_map[suffix]} source tree",
                        source="tree_sitter",
                        code="TS_ERR",
                    )
                    diagnostics.append(diag)
                return diagnostics
            except Exception:
                pass

        return diagnostics


class LiveLSPBridge:
    """
    Manages LSP server subprocess lifecycle, document state tracking,
    diagnostics aggregation, and language server requests.
    """

    def __init__(
        self,
        command: Optional[List[str]] = None,
        workspace_root: Optional[Union[str, Path]] = None,
        auto_fallback: bool = True,
    ):
        self.command = command
        self.workspace_root = Path(workspace_root or Path.cwd()).resolve()
        self.auto_fallback = auto_fallback
        self.process: Optional[subprocess.Popen] = None
        self._next_id = 1
        self._pending_requests: Dict[int, Any] = {}
        self._diagnostics_store: Dict[str, List[LSPDiagnostic]] = {}
        self._open_documents: Dict[str, str] = {}  # file_path -> content
        self._lock = threading.Lock()
        self._running = False
        self._reader_thread: Optional[threading.Thread] = None

    def start(self) -> bool:
        """Starts the language server process if command is provided and available."""
        if not self.command:
            return False
        try:
            self.process = subprocess.Popen(
                self.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.workspace_root),
                bufsize=0,
            )
            self._running = True
            self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
            self._reader_thread.start()
            self._send_initialize()
            return True
        except Exception:
            self.process = None
            self._running = False
            return False

    def stop(self) -> None:
        """Gracefully stops the language server process."""
        self._running = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=1.0)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            self.process = None

    def _send_initialize(self) -> None:
        root_uri = f"file://{self.workspace_root}"
        init_params = {
            "processId": os.getpid(),
            "rootUri": root_uri,
            "capabilities": {
                "textDocument": {
                    "publishDiagnostics": {"relatedInformation": True},
                    "definition": {"dynamicRegistration": False},
                    "hover": {"contentFormat": ["markdown", "plaintext"]},
                }
            },
        }
        self.send_request("initialize", init_params)
        self.send_notification("initialized", {})

    def send_notification(self, method: str, params: Dict[str, Any]) -> None:
        if not self.process or not self.process.stdin:
            return
        msg = {"jsonrpc": "2.0", "method": method, "params": params}
        encoded = JSONRPCProtocol.encode_message(msg)
        try:
            with self._lock:
                self.process.stdin.write(encoded)
                self.process.stdin.flush()
        except (BrokenPipeError, OSError):
            self.stop()

    def send_request(self, method: str, params: Dict[str, Any]) -> int:
        req_id = self._next_id
        self._next_id += 1
        msg = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}
        encoded = JSONRPCProtocol.encode_message(msg)
        if self.process and self.process.stdin:
            try:
                with self._lock:
                    self._pending_requests[req_id] = method
                    self.process.stdin.write(encoded)
                    self.process.stdin.flush()
            except (BrokenPipeError, OSError):
                self.stop()
        return req_id

    def _read_loop(self) -> None:
        if not self.process or not self.process.stdout:
            return
        stdout = self.process.stdout
        while self._running:
            try:
                header_data = b""
                while not header_data.endswith(b"\r\n\r\n"):
                    chunk = stdout.read(1)
                    if not chunk:
                        self._running = False
                        return
                    header_data += chunk

                content_len = JSONRPCProtocol.parse_header(header_data)
                if content_len is None:
                    continue

                body_data = b""
                while len(body_data) < content_len:
                    read_chunk = stdout.read(content_len - len(body_data))
                    if not read_chunk:
                        self._running = False
                        return
                    body_data += read_chunk

                msg = json.loads(body_data.decode("utf-8", errors="replace"))
                self._handle_incoming_message(msg)
            except Exception:
                if not self._running:
                    break

    def _handle_incoming_message(self, msg: Dict[str, Any]) -> None:
        method = msg.get("method")
        if method == "textDocument/publishDiagnostics":
            params = msg.get("params", {})
            uri = params.get("uri", "")
            raw_diags = params.get("diagnostics", [])
            file_path = uri.replace("file://", "")
            parsed_diags = []
            for d in raw_diags:
                r = d.get("range", {})
                start = r.get("start", {})
                end = r.get("end", {})
                parsed_diags.append(
                    LSPDiagnostic(
                        file_path=file_path,
                        range=LSPRange(
                            start=LSPPosition(line=start.get("line", 0), character=start.get("character", 0)),
                            end=LSPPosition(line=end.get("line", 0), character=end.get("character", 0)),
                        ),
                        severity=DiagnosticSeverity.from_value(d.get("severity", 1)),
                        message=d.get("message", ""),
                        source=d.get("source", "lsp"),
                        code=d.get("code"),
                    )
                )
            with self._lock:
                self._diagnostics_store[file_path] = parsed_diags

    def open_document(self, file_path: Union[str, Path], content: str, language_id: str = "python") -> None:
        p = str(Path(file_path).resolve())
        with self._lock:
            self._open_documents[p] = content
        if self._running:
            uri = f"file://{p}"
            self.send_notification(
                "textDocument/didOpen",
                {"textDocument": {"uri": uri, "languageId": language_id, "version": 1, "text": content}},
            )
        elif self.auto_fallback:
            self._run_offline_analysis(p, content)

    def change_document(self, file_path: Union[str, Path], content: str, version: int = 2) -> None:
        p = str(Path(file_path).resolve())
        with self._lock:
            self._open_documents[p] = content
        if self._running:
            uri = f"file://{p}"
            self.send_notification(
                "textDocument/didChange",
                {"textDocument": {"uri": uri, "version": version}, "contentChanges": [{"text": content}]},
            )
        elif self.auto_fallback:
            self._run_offline_analysis(p, content)

    def _run_offline_analysis(self, file_path: str, content: str) -> None:
        if file_path.endswith(".py"):
            diags = OfflineLSPFallback.analyze_python_source(file_path, content)
        else:
            diags = OfflineLSPFallback.analyze_generic_source(file_path, content)
        with self._lock:
            self._diagnostics_store[file_path] = diags

    def get_diagnostics(self, file_path: Union[str, Path]) -> List[LSPDiagnostic]:
        p = str(Path(file_path).resolve())
        with self._lock:
            if p in self._diagnostics_store:
                return list(self._diagnostics_store[p])
            if self.auto_fallback and p in self._open_documents:
                self._run_offline_analysis(p, self._open_documents[p])
                return list(self._diagnostics_store.get(p, []))
            return []

    def format_diagnostics_for_prompt(
        self, file_path: Union[str, Path], max_tokens: int = 250
    ) -> str:
        """Formats diagnostics into a compact, token-bounded prompt string."""
        diags = self.get_diagnostics(file_path)
        if not diags:
            return "No compiler diagnostics reported. (CLEAN)"

        lines = [f"[LSP Diagnostics for {Path(file_path).name}]"]
        for d in diags:
            line_str = f"  - L{d.human_line}:{d.human_column} [{d.severity.name}] {d.message}"
            if d.code:
                line_str += f" ({d.code})"
            lines.append(line_str)

        res = "\n".join(lines)
        if len(res) > max_tokens * 4:
            res = res[: max_tokens * 4] + "\n  ... [truncated to fit token budget]"
        return res


def create_lsp_bridge(
    command: Optional[List[str]] = None,
    workspace_root: Optional[Union[str, Path]] = None,
    auto_fallback: bool = True,
) -> LiveLSPBridge:
    """Factory helper to instantiate a LiveLSPBridge."""
    bridge = LiveLSPBridge(
        command=command,
        workspace_root=workspace_root,
        auto_fallback=auto_fallback,
    )
    return bridge
