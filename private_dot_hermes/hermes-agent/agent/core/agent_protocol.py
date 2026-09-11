"""
Standardized Inter-Agent Protocol (Milestone Phase III.3)
=========================================================
Based on arXiv:2504.16736 (AI Agent Protocols Survey).
Provides standardized schemas and transport mechanisms for inter-agent communication:
  1. Standardized Schema: AgentMessage { role, content, confidence, metadata, trace_id, timestamp }
  2. Internal Transport: JSON-RPC 2.0 over UNIX domain socket (/dev/shm/hermes_agent_ipc.sock)
  3. External Bridge: Model Context Protocol (MCP) compatible serialization/deserialization.
"""

from __future__ import annotations

import json
import os
import socket
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Callable, Union


# ─── 1. Core Standardized Schema ───

@dataclass
class AgentMessage:
    """Standardized inter-agent message conforming to arXiv:2504.16736 survey specification."""
    role: str
    content: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    trace_id: str = field(default_factory=lambda: f"tr-{uuid.uuid4().hex[:12]}")
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        self.confidence = max(0.0, min(1.0, float(self.confidence)))
        if not isinstance(self.metadata, dict):
            self.metadata = dict(self.metadata) if self.metadata else {}

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
        return cls(
            role=str(data.get("role", "unknown")),
            content=str(data.get("content", "")),
            confidence=float(data.get("confidence", 1.0)),
            metadata=dict(data.get("metadata", {})),
            trace_id=str(data.get("trace_id", f"tr-{uuid.uuid4().hex[:12]}")),
            timestamp=float(data.get("timestamp", time.time())),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "AgentMessage":
        data = json.loads(json_str)
        return cls.from_dict(data)

    def to_mcp_content(self) -> Dict[str, Any]:
        """Convert to standard Model Context Protocol (MCP) TextContent representation."""
        return {
            "type": "text",
            "text": self.content,
            "annotations": {
                "role": self.role,
                "confidence": self.confidence,
                "trace_id": self.trace_id,
                "timestamp": self.timestamp,
                **self.metadata,
            }
        }

    @classmethod
    def from_mcp_content(cls, mcp_dict: Dict[str, Any]) -> "AgentMessage":
        """Construct AgentMessage from MCP TextContent with annotations."""
        text = str(mcp_dict.get("text", ""))
        annotations = mcp_dict.get("annotations", {}) or {}
        return cls(
            role=annotations.get("role", "mcp_peer"),
            content=text,
            confidence=float(annotations.get("confidence", 1.0)),
            metadata={k: v for k, v in annotations.items() if k not in ("role", "confidence", "trace_id", "timestamp")},
            trace_id=annotations.get("trace_id", f"mcp-tr-{uuid.uuid4().hex[:8]}"),
            timestamp=float(annotations.get("timestamp", time.time())),
        )


# ─── 2. JSON-RPC 2.0 Specification ───

@dataclass
class JsonRpcRequest:
    method: str
    params: Dict[str, Any] = field(default_factory=dict)
    id: Union[str, int] = field(default_factory=lambda: uuid.uuid4().hex[:8])
    jsonrpc: str = "2.0"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict()) + "\n"

    @classmethod
    def from_json(cls, json_str: str) -> "JsonRpcRequest":
        data = json.loads(json_str.strip())
        return cls(
            method=data["method"],
            params=data.get("params", {}),
            id=data.get("id", 1),
            jsonrpc=data.get("jsonrpc", "2.0"),
        )


@dataclass
class JsonRpcResponse:
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: Union[str, int] = 1
    jsonrpc: str = "2.0"

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"jsonrpc": self.jsonrpc, "id": self.id}
        if self.error is not None:
            d["error"] = self.error
        else:
            d["result"] = self.result
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict()) + "\n"

    @classmethod
    def from_json(cls, json_str: str) -> "JsonRpcResponse":
        data = json.loads(json_str.strip())
        return cls(
            result=data.get("result"),
            error=data.get("error"),
            id=data.get("id", 1),
            jsonrpc=data.get("jsonrpc", "2.0"),
        )


# ─── 3. UNIX Domain Socket IPC Server & Client ───

DEFAULT_IPC_SOCKET = "/dev/shm/hermes_agent_ipc.sock" if os.path.exists("/dev/shm") else "/tmp/hermes_agent_ipc.sock"


class AgentProtocolServer:
    """Lightweight high-performance UNIX domain socket server running JSON-RPC 2.0 for agents."""

    def __init__(self, socket_path: str = DEFAULT_IPC_SOCKET):
        self.socket_path = socket_path
        self._handlers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self._server_sock: Optional[socket.socket] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None

        self.register_handler("ping", lambda params: {"status": "pong", "server_time": time.time()})
        self.register_handler("handshake", self._handle_handshake)

    def register_handler(self, method: str, handler: Callable[[Dict[str, Any]], Any]) -> None:
        self._handlers[method] = handler

    def _handle_handshake(self, params: Dict[str, Any]) -> Dict[str, Any]:
        peer = params.get("agent_name", "unknown")
        return {
            "status": "acknowledged",
            "protocol": "hermes-agent-v1",
            "server_pid": os.getpid(),
            "peer": peer,
        }

    def start(self) -> None:
        if self._running:
            return

        if os.path.exists(self.socket_path):
            try:
                os.unlink(self.socket_path)
            except OSError:
                pass

        self._server_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._server_sock.bind(self.socket_path)
        self._server_sock.listen(16)
        self._server_sock.settimeout(0.5)
        self._running = True

        self._thread = threading.Thread(target=self._serve_loop, daemon=True, name="HermesAgentIPCServer")
        self._thread.start()

    def _serve_loop(self) -> None:
        while self._running:
            try:
                conn, _ = self._server_sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            client_t = threading.Thread(target=self._handle_client, args=(conn,), daemon=True)
            client_t.start()

    def _handle_client(self, conn: socket.socket) -> None:
        with conn:
            buffer = ""
            while self._running:
                data = conn.recv(4096)
                if not data:
                    break
                buffer += data.decode("utf-8", errors="replace")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        req = JsonRpcRequest.from_json(line)
                        if req.method in self._handlers:
                            res_val = self._handlers[req.method](req.params)
                            resp = JsonRpcResponse(result=res_val, id=req.id)
                        else:
                            resp = JsonRpcResponse(
                                error={"code": -32601, "message": f"Method '{req.method}' not found"},
                                id=req.id,
                            )
                    except Exception as err:
                        resp = JsonRpcResponse(
                            error={"code": -32603, "message": f"Internal error: {str(err)}"},
                            id=1,
                        )
                    conn.sendall(resp.to_json().encode("utf-8"))

    def stop(self) -> None:
        self._running = False
        if self._server_sock:
            try:
                self._server_sock.close()
            except Exception:
                pass
        if os.path.exists(self.socket_path):
            try:
                os.unlink(self.socket_path)
            except OSError:
                pass
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)


class AgentProtocolClient:
    """UNIX domain socket client for JSON-RPC 2.0 communication between agents."""

    def __init__(self, socket_path: str = DEFAULT_IPC_SOCKET):
        self.socket_path = socket_path

    def call(self, method: str, params: Optional[Dict[str, Any]] = None, timeout: float = 3.0) -> Any:
        params = params or {}
        req = JsonRpcRequest(method=method, params=params)

        if not os.path.exists(self.socket_path):
            raise FileNotFoundError(f"Agent IPC socket '{self.socket_path}' not found.")

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            sock.connect(self.socket_path)
            sock.sendall(req.to_json().encode("utf-8"))

            buffer = ""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk.decode("utf-8", errors="replace")
                if "\n" in buffer:
                    break

            line = buffer.strip().split("\n")[0]
            resp = JsonRpcResponse.from_json(line)
            if resp.error:
                raise RuntimeError(f"RPC Error {resp.error.get('code')}: {resp.error.get('message')}")
            return resp.result
        finally:
            sock.close()

    def send_agent_message(self, message: AgentMessage, timeout: float = 3.0) -> Any:
        """Helper sending typed AgentMessage over JSON-RPC."""
        return self.call("receive_message", {"message": message.to_dict()}, timeout=timeout)
