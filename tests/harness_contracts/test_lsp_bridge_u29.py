"""
Contract Spike: Live LSP & Language Server Bridge (Capability U29)
=================================================================
Verifies JSON-RPC 2.0 framing, document synchronization lifecycle,
LSP diagnostic mapping, offline AST fallback, and prompt formatting.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / ".hermes" / "src"))

import pytest

from hermes_core.lsp_bridge import (
    DiagnosticSeverity,
    JSONRPCProtocol,
    LiveLSPBridge,
    LSPDiagnostic,
    LSPPosition,
    LSPRange,
    OfflineLSPFallback,
    create_lsp_bridge,
)


def test_jsonrpc_framing_encode_parse():
    msg = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"rootUri": "file:///tmp"}}
    encoded = JSONRPCProtocol.encode_message(msg)
    
    assert encoded.startswith(b"Content-Length: ")
    assert b"\r\n\r\n" in encoded
    
    header_part, body_part = encoded.split(b"\r\n\r\n", 1)
    content_len = JSONRPCProtocol.parse_header(header_part + b"\r\n\r\n")
    assert content_len == len(body_part)
    
    decoded = json.loads(body_part.decode("utf-8"))
    assert decoded["method"] == "initialize"
    assert decoded["id"] == 1


def test_offline_python_ast_diagnostics():
    clean_code = "def add(a: int, b: int) -> int:\n    return a + b\n"
    diags_clean = OfflineLSPFallback.analyze_python_source("clean.py", clean_code)
    assert len(diags_clean) == 0
    
    broken_code = "def broken(a, b:\n    return a + b\n"
    diags_broken = OfflineLSPFallback.analyze_python_source("broken.py", broken_code)
    assert len(diags_broken) == 1
    d = diags_broken[0]
    assert d.severity == DiagnosticSeverity.ERROR
    assert "SyntaxError" in d.message
    assert d.human_line == 1
    assert d.source == "python_ast"


def test_offline_generic_syntax_diagnostics():
    clean_js = "function hello() { return [1, 2, 3]; }"
    diags_clean = OfflineLSPFallback.analyze_generic_source("test.js", clean_js)
    assert len(diags_clean) == 0
    
    unbalanced_js = "function bad() { return (1 + 2; }"
    diags_broken = OfflineLSPFallback.analyze_generic_source("bad.js", unbalanced_js)
    assert len(diags_broken) >= 1
    assert any("bracket" in d.message.lower() for d in diags_broken)


def test_lsp_bridge_offline_mode_document_lifecycle():
    bridge = create_lsp_bridge(command=None, auto_fallback=True)
    
    # Open valid file
    bridge.open_document("module.py", "x = 10\ny = 20\n")
    diags = bridge.get_diagnostics("module.py")
    assert len(diags) == 0
    
    clean_prompt = bridge.format_diagnostics_for_prompt("module.py")
    assert "No compiler diagnostics" in clean_prompt
    
    # Change to invalid syntax
    bridge.change_document("module.py", "x = 10\ny = (20 +\n")
    diags_after = bridge.get_diagnostics("module.py")
    assert len(diags_after) == 1
    assert diags_after[0].severity == DiagnosticSeverity.ERROR
    
    err_prompt = bridge.format_diagnostics_for_prompt("module.py")
    assert "[LSP Diagnostics for module.py]" in err_prompt
    assert "SyntaxError" in err_prompt


def test_mock_publish_diagnostics_handler():
    bridge = create_lsp_bridge(command=None, auto_fallback=False)
    
    # Simulate an LSP server textDocument/publishDiagnostics event
    fake_notification = {
        "jsonrpc": "2.0",
        "method": "textDocument/publishDiagnostics",
        "params": {
            "uri": "file:///workspace/app.py",
            "diagnostics": [
                {
                    "range": {
                        "start": {"line": 14, "character": 4},
                        "end": {"line": 14, "character": 12},
                    },
                    "severity": 1,
                    "code": "reportUndefinedVariable",
                    "source": "Pyright",
                    "message": 'Variable "unknown_var" is not defined',
                }
            ],
        },
    }
    
    bridge._handle_incoming_message(fake_notification)
    diags = bridge.get_diagnostics("/workspace/app.py")
    assert len(diags) == 1
    d = diags[0]
    assert d.human_line == 15
    assert d.human_column == 5
    assert d.severity == DiagnosticSeverity.ERROR
    assert d.code == "reportUndefinedVariable"
    assert d.source == "Pyright"
    assert "unknown_var" in d.message
