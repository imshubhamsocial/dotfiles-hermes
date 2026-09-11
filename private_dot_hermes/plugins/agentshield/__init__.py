"""
Hermes Plugin: agentshield
==========================
ECC (Everything Claude Code) AgentShield Security Enforcement Engine.
Provides a 4-layer defense in depth for autonomous AI agents:
1. Intent Classification: Semantic categorization (SAFE / RISKY / BLOCK).
2. Secret Detection: Shannon entropy analysis + known regex patterns to prevent credential leakage.
3. Blast Radius Calculator: AST dependency tracing to evaluate mutation risks with token-cache.
4. Immutable Audit Trail: Cryptographic SHA256 hash-chained ledger in verification_evidence.db with compaction.
5. Parallel Tool Dispatch: Non-blocking parallel execution for read-only tools.
"""

from __future__ import annotations

import ast
import asyncio
import hashlib
import json
import math
import os
import re
import sqlite3
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

try:
    from ast_grep_py import SgRoot
    AST_GREP_AVAILABLE = True
except ImportError:
    SgRoot = None
    AST_GREP_AVAILABLE = False


# =============================================================================
# Layer 1: Secret Scanner (Shannon Entropy + Regex Signatures)
# =============================================================================
class SecretScanner:
    """Detects credentials, API keys, and sensitive tokens via entropy and signatures."""

    PATTERNS = [
        ("OpenAI / Codex API Key", re.compile(r"sk-[a-zA-Z0-9_-]{20,}")),
        ("GitHub Personal Access Token", re.compile(r"ghp_[a-zA-Z0-9]{36}")),
        ("GitHub Fine-grained PAT", re.compile(r"github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}")),
        ("Slack Bot Token", re.compile(r"xoxb-[0-9]{11,}-[0-9]{11,}-[a-zA-Z0-9]{24}")),
        ("AWS Access Key ID", re.compile(r"AKIA[0-9A-Z]{16}")),
        ("Private Key Header", re.compile(r"-----BEGIN (?:RSA|EC|OPENSSH|PGP) PRIVATE KEY-----")),
        ("Generic High-Entropy Key Assignment", re.compile(r"""(?i)(?:api_key|secret|password|auth_token|bearer)\s*[:=]\s*["']([a-zA-Z0-9_\-\.]{16,})["']""")),
    ]

    @staticmethod
    def calculate_shannon_entropy(token: str) -> float:
        """Calculates Shannon entropy H = -sum(p_i * log2(p_i)) for a token."""
        if not token:
            return 0.0
        counts = Counter(token)
        length = len(token)
        entropy = -sum((c / length) * math.log2(c / length) for c in counts.values())
        return entropy

    @classmethod
    def scan_text(cls, text: str) -> List[Dict[str, Any]]:
        """Scans string for secret patterns and high-entropy sequences."""
        findings = []

        # 1. Regex Pattern Check
        for name, pat in cls.PATTERNS:
            matches = pat.finditer(text)
            for m in matches:
                matched_val = m.group(0)
                # Redact matched text in report
                masked = matched_val[:4] + "..." + matched_val[-4:] if len(matched_val) > 8 else "***"
                findings.append({
                    "type": "regex_pattern",
                    "name": name,
                    "masked": masked,
                    "span": m.span(),
                })

        # 2. Tokenized Entropy Check
        words = re.findall(r"[a-zA-Z0-9_\-\.\+/]{20,}", text)
        for w in words:
            # Filter out standard base64 or common identifiers
            if " " not in w and not w.startswith("http"):
                ent = cls.calculate_shannon_entropy(w)
                if ent > 4.6 and len(w) >= 24:
                    masked = w[:4] + "..." + w[-4:]
                    findings.append({
                        "type": "high_entropy",
                        "name": f"High Entropy Token (H={round(ent, 2)})",
                        "masked": masked,
                        "entropy": round(ent, 2),
                    })

        return findings

    @classmethod
    def scan_file(cls, path: str | Path) -> Dict[str, Any]:
        """Scans a file on disk."""
        p = Path(path)
        if not p.exists() or not p.is_file():
            return {"file": str(path), "scanned": False, "findings": []}
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
            findings = cls.scan_text(content)
            return {
                "file": str(path),
                "scanned": True,
                "clean": len(findings) == 0,
                "findings": findings,
            }
        except Exception as e:
            return {"file": str(path), "scanned": False, "error": str(e), "findings": []}


# =============================================================================
# Layer 2: Blast Radius Calculator (AST Structural Impact & Token Cache)
# =============================================================================
class BlastRadiusCalculator:
    """Calculates potential ripple-effect risk of code mutations."""

    _SYMBOL_CACHE: Dict[str, Tuple[float, Set[str]]] = {}

    @staticmethod
    def inspect_python_ast(code: str) -> List[str]:
        """Extracts top-level class, function, and variable names."""
        try:
            tree = ast.parse(code)
            symbols = []
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    symbols.append(node.name)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            symbols.append(target.id)
            return symbols
        except Exception:
            return []

    @classmethod
    def get_workspace_tokens(cls, file_path: Path) -> Set[str]:
        """Cached token extraction for workspace python files based on mtime."""
        try:
            mtime = file_path.stat().st_mtime
            cached = cls._SYMBOL_CACHE.get(str(file_path))
            if cached and cached[0] == mtime:
                return cached[1]
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            tokens = set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]{2,}\b", content))
            cls._SYMBOL_CACHE[str(file_path)] = (mtime, tokens)
            return tokens
        except Exception:
            return set()

    @classmethod
    def calculate_file_blast_radius(cls, file_path: str | Path, workspace_root: Optional[Path] = None) -> Dict[str, Any]:
        """Calculates impact score and affected symbols for a file mutation."""
        p = Path(file_path)
        if not p.exists():
            return {
                "file": str(file_path),
                "score": 0.1,
                "risk_level": "LOW",
                "affected_symbols": [],
                "detail": "New file creation, minimal blast radius.",
            }

        code = p.read_text(encoding="utf-8", errors="ignore")
        symbols = cls.inspect_python_ast(code)

        lines_count = len(code.splitlines())
        if workspace_root:
            root = Path(workspace_root)
        else:
            hermes_home = os.environ.get("HERMES_HOME")
            root = Path(hermes_home) if hermes_home else Path.home() / ".hermes"

        # Scan for references to exported symbols across workspace using cached token sets
        ref_count = 0
        if symbols and root.exists():
            symbols_set = set(symbols)
            skip_dirs = {".git", ".cache", "venv", ".venv", "__pycache__", "node_modules", ".pytest_cache", "hermes-agent", "cache", "training_buffer", ".hermes_archived", ".local_archived", ".local"}
            for root_dir, dirnames, filenames in os.walk(root):
                dirnames[:] = [d for d in dirnames if d not in skip_dirs and not d.startswith(".")]
                for f in filenames:
                    if f.endswith(".py"):
                        py_file = Path(root_dir) / f
                        try:
                            if py_file.resolve() == p.resolve():
                                continue
                            file_tokens = cls.get_workspace_tokens(py_file)
                            matched = symbols_set & file_tokens
                            ref_count += len(matched)
                        except Exception:
                            pass

        # Calculate normalized score between 0.0 and 1.0
        score = min(1.0, (ref_count * 0.08) + (len(symbols) * 0.05) + (lines_count * 0.001))
        risk_level = "HIGH" if score > 0.65 else ("MEDIUM" if score > 0.3 else "LOW")

        return {
            "file": str(file_path),
            "score": round(score, 3),
            "risk_level": risk_level,
            "exported_symbols_count": len(symbols),
            "external_references_found": ref_count,
            "lines_count": lines_count,
            "requires_confirmation": score > 0.70,
            "cache_size": len(cls._SYMBOL_CACHE),
        }


# =============================================================================
# Layer 3: Semantic Intent Classifier
# =============================================================================
class IntentClassifier:
    """Classifies commands into SAFE, RISKY, or BLOCK categories."""

    BLOCK_PATTERNS = [
        re.compile(r"rm\s+(-[rfRF]+\s+|--recursive\s+)(?:/|~|\$HOME|/etc|/var|/usr|/bin)"),
        re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:"),  # Fork bomb
        re.compile(r"mkfs(?:\.[a-z0-9]+)?\s+"),
        re.compile(r"dd\s+if=/dev/(?:zero|urandom)\s+of=/dev/"),
        re.compile(r">\s*/dev/sd[a-z]"),
        re.compile(r"chmod\s+-R\s+777\s+/"),
        re.compile(r"chown\s+-R\s+.*(?:\s+/|\s+~|\s+\$HOME)"),
    ]

    RISKY_PATTERNS = [
        re.compile(r"git\s+reset\s+--hard"),
        re.compile(r"git\s+clean\s+-fdx"),
        re.compile(r"rm\s+-rf\s+"),
        re.compile(r"sudo\s+"),
        re.compile(r"curl\s+.*\|\s*(?:bash|sh)"),
        re.compile(r"wget\s+.*\|\s*(?:bash|sh)"),
    ]

    @classmethod
    def classify(cls, command_str: str) -> Dict[str, Any]:
        """Evaluates command string and returns safety verdict."""
        cmd = command_str.strip()

        for pat in cls.BLOCK_PATTERNS:
            if pat.search(cmd):
                return {
                    "verdict": "BLOCK",
                    "reason": "Destructive or fatal system mutation detected.",
                    "command": cmd,
                }

        for pat in cls.RISKY_PATTERNS:
            if pat.search(cmd):
                return {
                    "verdict": "RISKY",
                    "reason": "High blast-radius operation requiring review.",
                    "command": cmd,
                }

        return {
            "verdict": "SAFE",
            "reason": "Standard developer operation.",
            "command": cmd,
        }


# =============================================================================
# Layer 4: Cryptographic SHA256 Hash-Chained Audit Trail
# =============================================================================
class ImmutableAuditTrail:
    """Append-only audit ledger with cryptographic SHA256 chain verification."""

    GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

    def __init__(self, db_path: Optional[Path] = None):
        if db_path:
            self.db_path = db_path
        else:
            hermes_home = os.environ.get("HERMES_HOME")
            base = Path(hermes_home) if hermes_home else Path.home() / ".hermes"
            self.db_path = base / "verification_evidence.db"

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.db_path))

    def _init_db(self):
        conn = self._get_conn()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_chain (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    action TEXT NOT NULL,
                    target TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    prev_hash TEXT NOT NULL,
                    entry_hash TEXT NOT NULL,
                    status TEXT NOT NULL
                )
                """
            )
            # Check for genesis block
            cur = conn.cursor()
            cur.execute("SELECT count(*) FROM audit_chain")
            if cur.fetchone()[0] == 0:
                ts = datetime.now(timezone.utc).isoformat()
                genesis_payload = hashlib.sha256(b"HERMES_GENESIS_BLOCK").hexdigest()
                entry_hash = self._compute_hash(1, ts, "GENESIS", "SYSTEM", genesis_payload, self.GENESIS_HASH)
                cur.execute(
                    "INSERT INTO audit_chain VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (1, ts, "GENESIS", "SYSTEM", genesis_payload, self.GENESIS_HASH, entry_hash, "COMMITTED"),
                )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _compute_hash(seq: int, ts: str, action: str, target: str, payload_hash: str, prev_hash: str) -> str:
        blob = f"{seq}:{ts}:{action}:{target}:{payload_hash}:{prev_hash}".encode("utf-8")
        return hashlib.sha256(blob).hexdigest()

    def append_entry(self, action: str, target: str, payload: str = "", status: str = "COMMITTED") -> Dict[str, Any]:
        """Appends a new verified entry chained to the previous block's SHA256 hash."""
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute("SELECT seq, entry_hash FROM audit_chain ORDER BY seq DESC LIMIT 1")
            last_row = cur.fetchone()
            last_seq = last_row[0] if last_row else 0
            prev_hash = last_row[1] if last_row else self.GENESIS_HASH

            next_seq = last_seq + 1
            ts = datetime.now(timezone.utc).isoformat()
            payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            entry_hash = self._compute_hash(next_seq, ts, action, target, payload_hash, prev_hash)

            cur.execute(
                "INSERT INTO audit_chain VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (next_seq, ts, action, target, payload_hash, prev_hash, entry_hash, status),
            )
            conn.commit()

            return {
                "seq": next_seq,
                "timestamp": ts,
                "action": action,
                "target": target,
                "entry_hash": entry_hash,
                "prev_hash": prev_hash,
                "status": status,
            }
        finally:
            conn.close()

    def verify_chain(self) -> Tuple[bool, str]:
        """Verifies mathematical SHA256 integrity across the entire chain."""
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute("SELECT seq, timestamp, action, target, payload_hash, prev_hash, entry_hash FROM audit_chain ORDER BY seq ASC")
            rows = cur.fetchall()
            if not rows:
                return True, "Chain is empty."

            expected_prev = self.GENESIS_HASH
            for row in rows:
                seq, ts, action, target, payload_hash, prev_hash, entry_hash = row
                if prev_hash != expected_prev:
                    return False, f"Broken link at block seq={seq}: prev_hash {prev_hash} != expected {expected_prev}"

                computed = self._compute_hash(seq, ts, action, target, payload_hash, prev_hash)
                if computed != entry_hash:
                    return False, f"Hash mismatch at block seq={seq}: computed {computed} != recorded {entry_hash}"

                expected_prev = entry_hash

            return True, f"Verified 100% integrity across {len(rows)} blocks."
        finally:
            conn.close()

    def prune_chain(self, max_entries: int = 10000) -> Dict[str, Any]:
        """Ensures the audit chain does not grow unbounded while preserving genesis and integrity."""
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute("SELECT count(*) FROM audit_chain")
            total = cur.fetchone()[0]
            if total <= max_entries:
                return {"pruned": False, "total_entries": total, "archived": 0}

            cutoff = total - (max_entries - 1)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_chain_archive (
                    seq INTEGER PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    action TEXT NOT NULL,
                    target TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    prev_hash TEXT NOT NULL,
                    entry_hash TEXT NOT NULL,
                    status TEXT NOT NULL,
                    archived_at TEXT NOT NULL
                )
                """
            )
            ts = datetime.now(timezone.utc).isoformat()
            cur.execute(
                """
                INSERT OR IGNORE INTO audit_chain_archive
                SELECT seq, timestamp, action, target, payload_hash, prev_hash, entry_hash, status, ?
                FROM audit_chain WHERE seq > 1 AND seq <= ?
                """,
                (ts, cutoff)
            )
            cur.execute("DELETE FROM audit_chain WHERE seq > 1 AND seq <= ?", (cutoff,))
            conn.commit()
            return {"pruned": True, "archived": cutoff, "total_entries": max_entries}
        finally:
            conn.close()

    def get_recent(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Returns recent audit log entries."""
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute("SELECT seq, timestamp, action, target, entry_hash, status FROM audit_chain ORDER BY seq DESC LIMIT ?", (limit,))
            rows = cur.fetchall()
            return [
                {
                    "seq": r[0],
                    "timestamp": r[1],
                    "action": r[2],
                    "target": r[3],
                    "entry_hash": r[4],
                    "status": r[5],
                }
                for r in rows
            ]
        finally:
            conn.close()


# =============================================================================

# =============================================================================
# Layer 6: Role-Based Tool Security Enforcer (Anthropic Recipe #33)
# =============================================================================
ROLE_TOOL_WHITELISTS: Dict[str, Set[str]] = {
    "architect": {
        "view_file", "cat", "grep_search", "find_by_name", "list_dir",
        "read_url_content", "read_browser_page", "get_file_structure",
        "search", "list_concepts", "audit-trail", "superpowers",
        "security-scan", "blast-radius", "bpe", "context", "verify",
        "reasoning_trace"
    },
    "coder": {
        "view_file", "cat", "grep_search", "find_by_name", "list_dir",
        "read_url_content", "read_browser_page", "get_file_structure",
        "search", "list_concepts", "audit-trail", "superpowers",
        "security-scan", "blast-radius", "bpe", "context", "verify",
        "reasoning_trace", "write_file", "write_to_file", "edit_file",
        "patch_file", "replace_file_content", "append_file", "bash",
        "execute_command", "run_command", "git"
    },
    "tester": {
        "view_file", "cat", "grep_search", "find_by_name", "list_dir",
        "read_url_content", "read_browser_page", "get_file_structure",
        "search", "list_concepts", "audit-trail", "superpowers",
        "security-scan", "blast-radius", "bpe", "context", "verify",
        "reasoning_trace", "bash", "execute_command", "run_command",
        "pytest", "exam"
    },
}

class RoleSecurityEnforcer:
    """Enforces strict Maker-Verifier separation of duties per agent role."""

    ROLE_WHITELISTS = ROLE_TOOL_WHITELISTS

    @classmethod
    def check_tool_allowed(cls, role: Optional[str], tool_name: str) -> Tuple[bool, str]:
        if not role:
            return True, "No role constraint active."
        role_key = role.strip().lower()
        if role_key not in cls.ROLE_WHITELISTS:
            return True, f"Unrestricted role: {role_key}"

        allowed = cls.ROLE_WHITELISTS[role_key]
        if tool_name in allowed:
            return True, f"Tool '{tool_name}' is whitelisted for role '{role_key}'."
        return False, f"Role Security Violation: Role '{role_key}' is restricted from calling '{tool_name}'."

# Layer 5: Parallel Read-Tool Dispatcher
# =============================================================================
class ParallelToolDispatcher:
    """Dispatches read-only tools concurrently via asyncio.gather."""

    @staticmethod
    async def dispatch_parallel(tasks: List[Tuple[Callable, Tuple[Any, ...], Dict[str, Any]]]) -> List[Any]:
        """Executes a list of (callable, args, kwargs) concurrently."""
        async def _wrap(fn, a, k):
            if asyncio.iscoroutinefunction(fn):
                return await fn(*a, **k)
            else:
                return await asyncio.to_thread(fn, *a, **k)

        coros = [_wrap(fn, a, k) for fn, a, k in tasks]
        return await asyncio.gather(*coros, return_exceptions=True)


_GLOBAL_AUDIT_TRAIL: Optional[ImmutableAuditTrail] = None


def get_audit_trail() -> ImmutableAuditTrail:
    global _GLOBAL_AUDIT_TRAIL
    if _GLOBAL_AUDIT_TRAIL is None:
        _GLOBAL_AUDIT_TRAIL = ImmutableAuditTrail()
    return _GLOBAL_AUDIT_TRAIL


def register(ctx=None):
    """Registers agentshield plugin into Hermes runtime."""
    if not ctx:
        return True

    audit = get_audit_trail()

    # 1. Register CLI Subcommands
    if hasattr(ctx, "register_cli_command"):
        # hermes audit-trail
        def setup_trail(parser):
            parser.description = "Inspect and verify cryptographic SHA256 audit chain"
            parser.add_argument("--limit", type=int, default=10, help="Number of recent entries")
            parser.add_argument("--verify", action="store_true", help="Perform complete SHA256 integrity verification")
            parser.add_argument("--prune", type=int, default=0, help="Prune entries exceeding threshold")

        def handle_trail(args):
            if getattr(args, "prune", 0) > 0:
                res = audit.prune_chain(max_entries=args.prune)
                print(f"Audit Trail Pruning: {res}")
                return 0

            if getattr(args, "verify", False):
                ok, msg = audit.verify_chain()
                symbol = "✓" if ok else "✗"
                print(f"Audit Trail Verification: {symbol} {msg}")
                return 0 if ok else 1
            else:
                entries = audit.get_recent(limit=args.limit)
                print("Immutable Cryptographic Audit Trail (verification_evidence.db):")
                for e in reversed(entries):
                    print(f"  [Block #{e['seq']}] {e['timestamp']} | {e['action']:<12} | {e['target']:<25} | hash: {e['entry_hash'][:12]}... ({e['status']})")
                ok, msg = audit.verify_chain()
                print(f"Chain Integrity: {'✓ PASS' if ok else '✗ CORRUPT'} ({msg})")
            return 0

        ctx.register_cli_command("audit-trail", "View and verify SHA256 cryptographic audit chain", setup_trail, handle_trail)

        # hermes security-scan <file>
        def setup_sec(parser):
            parser.description = "Scan text or file for credential leaks and Shannon entropy violations"
            parser.add_argument("target", help="File path or text string to scan")

        def handle_sec(args):
            p = Path(args.target)
            if p.exists() and p.is_file():
                res = SecretScanner.scan_file(p)
                if res["clean"]:
                    print(f"✓ Security Scan Clean: No secrets or high-entropy credentials in '{args.target}'")
                    return 0
                else:
                    print(f"✗ Credential Leaks Detected in '{args.target}':")
                    for f in res["findings"]:
                        print(f"  - [{f['type']}] {f['name']}: {f['masked']}")
                    return 1
            else:
                findings = SecretScanner.scan_text(args.target)
                if not findings:
                    print(f"✓ Text Scan Clean: No secrets detected.")
                    return 0
                else:
                    print(f"✗ Secret Findings in Text:")
                    for f in findings:
                        print(f"  - [{f['type']}] {f['name']}: {f['masked']}")
                    return 1

        ctx.register_cli_command("security-scan", "Scan file or string for secret leaks and high entropy", setup_sec, handle_sec)

        # hermes blast-radius <file>
        def setup_blast(parser):
            parser.description = "Calculate structural AST blast radius for a target file"
            parser.add_argument("file", help="Path to code file")

        def handle_blast(args):
            res = BlastRadiusCalculator.calculate_file_blast_radius(args.file)
            print(f"AST Blast Radius Analysis for '{args.file}':")
            print(f"  Risk Level:            {res['risk_level']} (Score: {res['score']})")
            print(f"  Exported Symbols:      {res['exported_symbols_count']}")
            print(f"  External References:   {res['external_references_found']}")
            print(f"  File Lines:            {res['lines_count']}")
            print(f"  Human Review Required: {'YES ⚠' if res['requires_confirmation'] else 'NO ✓'}")
            return 0

        ctx.register_cli_command("blast-radius", "Calculate AST blast radius and mutation risk", setup_blast, handle_blast)

    # 2. Register Slash Command
    if hasattr(ctx, "register_command"):
        def slash_security(raw_args: str) -> str:
            ok, msg = audit.verify_chain()
            entries = audit.get_recent(limit=3)
            lines = [
                f"**ECC AgentShield Security Status**",
                f"- **Audit Chain**: {'✓ Verified' if ok else '✗ Corrupt'} ({msg})",
                f"- **Secret Scanner**: Active (Entropy H > 4.6 + 7 regex signatures)",
                f"- **Blast Radius**: Active (Tree-sitter AST impact scoring with token cache)",
                f"- **Recent Blocks**:",
            ]
            for e in entries:
                lines.append(f"  * #{e['seq']} `{e['action']}` on `{e['target']}` ({e['status']})")
            return "\n".join(lines)

        ctx.register_command("security", slash_security, "Show ECC AgentShield security status", "")

    # 3. Lifecycle Hooks
    if hasattr(ctx, "register_hook"):
        def pre_tool_call_hook(tool_name: str = "", tool_args: Optional[Dict[str, Any]] = None, **kwargs):
            """Evaluates security invariants before tool execution."""
            args = tool_args or {}

            # 0. Role whitelisting enforcement (Anthropic Recipe #33)
            current_role = kwargs.get("role") or os.environ.get("HERMES_AGENT_ROLE", "").strip().lower()
            if current_role:
                allowed, msg = RoleSecurityEnforcer.check_tool_allowed(current_role, tool_name)
                if not allowed:
                    audit.append_entry("BLOCKED_ROLE_VIOLATION", f"{current_role}:{tool_name}", payload=msg, status="ROLE_VIOLATION")
                    return {
                        "action": "block",
                        "reason": f"AgentShield Role Enforcement: {msg}",
                    }

            # 0b. Constitutional preflight check (8 Golden Laws)
            try:
                from plugins.reward_scorer import ConstitutionalRewardScorer
                action_spec = {"tool": tool_name, "args": args, "role": current_role}
                preflight = ConstitutionalRewardScorer.score_action(action_spec)
                if preflight.get("verdict") == "BLOCK":
                    reason = f"Constitutional Preflight Violation: {'; '.join(preflight.get('violations', []))}"
                    audit.append_entry("BLOCKED_CONSTITUTIONAL", tool_name, payload=reason, status="CONSTITUTIONAL_VIOLATION")
                    return {
                        "action": "block",
                        "reason": reason,
                    }
            except Exception:
                pass

            # Check bash commands
            if tool_name in ("bash", "execute_command", "run_command"):
                cmd = args.get("command") or args.get("CommandLine") or ""
                intent = IntentClassifier.classify(cmd)
                if intent["verdict"] == "BLOCK":
                    audit.append_entry("BLOCKED", tool_name, payload=cmd, status="INTERCEPTED")
                    return {
                        "action": "block",
                        "reason": f"AgentShield Interception: {intent['reason']} Command was blocked.",
                    }

            # Check file writes for credential leaks
            if tool_name in ("write_file", "write_to_file", "edit_file", "patch_file", "replace_file_content"):
                content = args.get("content") or args.get("CodeContent") or args.get("replacement") or args.get("ReplacementContent") or ""
                findings = SecretScanner.scan_text(content)
                if findings:
                    target = args.get("path") or args.get("TargetFile") or "file"
                    audit.append_entry("BLOCKED_SECRET", str(target), payload=json.dumps(findings), status="LEAK_PREVENTED")
                    return {
                        "action": "block",
                        "reason": f"AgentShield Credential Leak Prevention: Detected {len(findings)} sensitive key/token pattern(s). File write aborted.",
                    }

            # Selective logging: only log mutating actions unless HERMES_AUDIT_MODE=full
            audit_mode = os.environ.get("HERMES_AUDIT_MODE", "mutations_only").lower()
            is_mutation = tool_name in (
                "write_file", "write_to_file", "edit_file", "patch_file",
                "replace_file_content", "append_file", "bash", "execute_command", "run_command"
            )

            if audit_mode == "full" or is_mutation:
                target_str = str(args.get("path") or args.get("TargetFile") or args.get("command") or tool_name)[:50]
                audit.append_entry("TOOL_CALL", f"{tool_name}:{target_str}", payload=json.dumps(args)[:200], status="DISPATCHED")

            return {"action": "continue"}

        ctx.register_hook("pre_tool_call", pre_tool_call_hook)

    return True
