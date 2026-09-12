"""
Hermes Plugin: cog_verifier
===========================
Verifies and indexes the COG Second Brain knowledge vault (.hermes/knowledge/concepts/).
Enforces YAML frontmatter schema (id/title, tags/category, status/verified).
Provides native CLI and slash commands for vault inspection.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from hermes_constants import get_hermes_home


def get_concepts_dir() -> Path:
    """Returns the default concept vault directory."""
    home = get_hermes_home()
    c = home / "memories" / "knowledge" / "concepts"
    if not c.exists() and (home / "knowledge" / "concepts").exists():
        c = home / "knowledge" / "concepts"
    return c


def parse_frontmatter(content: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """Extracts YAML frontmatter and body from a markdown document."""
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, content

    for idx, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            fm_text = "\n".join(lines[1:idx])
            body_text = "\n".join(lines[idx + 1:]).strip()
            try:
                data = yaml.safe_load(fm_text)
                return (data if isinstance(data, dict) else None), body_text
            except Exception:
                return None, body_text

    return None, content


def verify_concept(filepath: str | Path) -> Dict[str, Any]:
    """
    Verifies a concept markdown document against the COG knowledge schema.
    Required frontmatter fields: title (or id), tags (or category).
    Valid status values: active, partial, deprecated, or verified: bool.
    """
    path = Path(filepath).expanduser().resolve()
    if not path.exists():
        return {
            "passed": False,
            "verdict": "REJECTED",
            "message": f"Concept file does not exist: {filepath}",
            "path": str(path),
            "metadata": {},
        }

    raw_text = path.read_text(encoding="utf-8", errors="replace")
    fm, body = parse_frontmatter(raw_text)

    if fm is None:
        return {
            "passed": False,
            "verdict": "REJECTED",
            "message": f"Missing or invalid YAML frontmatter delimiters in {path.name}",
            "path": str(path),
            "metadata": {},
        }

    # Validate essential schema fields
    has_identifier = bool(fm.get("title") or fm.get("id"))
    has_category = bool(fm.get("tags") or fm.get("category"))
    has_body = len(body.strip()) > 0

    issues = []
    if not has_identifier:
        issues.append("Missing required field: 'title' or 'id'")
    if not has_category:
        issues.append("Missing required field: 'tags' or 'category'")
    if not has_body:
        issues.append("Concept markdown body is empty")

    passed = len(issues) == 0
    return {
        "passed": passed,
        "verdict": "APPROVED" if passed else "REJECTED",
        "message": "Valid concept schema" if passed else "; ".join(issues),
        "path": str(path),
        "metadata": fm,
        "body_length": len(body),
    }


def list_concepts(vault_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Lists and verifies all concept files in the vault."""
    v_dir = vault_dir or get_concepts_dir()
    if not v_dir.exists():
        return []

    results = []
    for md_file in sorted(v_dir.glob("*.md")):
        res = verify_concept(md_file)
        results.append({
            "name": md_file.name,
            "path": str(md_file),
            "title": res["metadata"].get("title", res["metadata"].get("id", md_file.stem)),
            "status": res["metadata"].get("status", "active" if res["metadata"].get("verified") else "unverified"),
            "tags": res["metadata"].get("tags", res["metadata"].get("category", [])),
            "passed": res["passed"],
            "verdict": res["verdict"],
        })
    return results


def register(ctx=None):
    """Registers cog_verifier into Hermes runtime."""
    if not ctx:
        return True

    # 1. Native CLI command: hermes concepts [list | verify <file>]
    if hasattr(ctx, "register_cli_command"):
        def setup_concepts(parser):
            parser.description = "Inspect and verify COG Second Brain concepts vault"
            subparsers = parser.add_subparsers(dest="subcommand", help="Concepts actions")
            
            subparsers.add_parser("list", help="List all concepts in the vault")
            
            verify_parser = subparsers.add_parser("verify", help="Verify a concept frontmatter schema")
            verify_parser.add_argument("path", help="Path to the concept markdown file")
            verify_parser.add_argument("--json", action="store_true", help="Output verification as JSON")

        def handle_concepts(args):
            subcmd = getattr(args, "subcommand", None) or "list"
            if subcmd == "list":
                concepts = list_concepts()
                print(f"COG Concepts Vault ({len(concepts)} concepts):")
                for c in concepts:
                    mark = "✓" if c["passed"] else "✗"
                    tags_str = f"[{', '.join(c['tags'])}]" if isinstance(c['tags'], list) else str(c['tags'])
                    print(f"  [{mark}] {c['name']:<25} | {c['title']:<30} | {c['status']:<10} | {tags_str}")
                return 0
            elif subcmd == "verify":
                res = verify_concept(args.path)
                if getattr(args, "json", False):
                    print(json.dumps(res, indent=2))
                else:
                    mark = "✓" if res["passed"] else "✗"
                    print(f"Concept: {res['verdict']} {mark} — {res['path']}")
                    print(f"  Details: {res['message']}")
                    if res["metadata"]:
                        print(f"  Metadata: {json.dumps(res['metadata'])}")
                return 0 if res["passed"] else 1
            return 0

        ctx.register_cli_command("concepts", "Inspect and verify COG concepts vault", setup_concepts, handle_concepts)

    # 2. Native Slash command: /concepts [list | <filename>]
    if hasattr(ctx, "register_command"):
        def slash_concepts(raw_args: str) -> str:
            arg = raw_args.strip()
            if not arg or arg == "list":
                concepts = list_concepts()
                lines = [f"**COG Concepts Vault** ({len(concepts)} concepts):"]
                for c in concepts:
                    mark = "✓" if c["passed"] else "✗"
                    lines.append(f"- [{mark}] **{c['title']}** (`{c['name']}`) — {c['status']}")
                return "\n".join(lines)
            else:
                target = Path(arg)
                if not target.is_absolute():
                    target = get_concepts_dir() / target
                res = verify_concept(target)
                mark = "✓" if res["passed"] else "✗"
                return f"**Concept Verification**: {res['verdict']} {mark}\n- Path: `{res['path']}`\n- Status: {res['message']}"

        ctx.register_command("concepts", slash_concepts, "Inspect or verify COG concepts vault", "[list|<file>]")

    # 3. Lifecycle hook: on_session_start
    if hasattr(ctx, "register_hook"):
        def on_session_start_hook(**kwargs):
            concepts = list_concepts()
            invalid = [c["name"] for c in concepts if not c["passed"]]
            if invalid:
                print(f"[COG Verifier] Warning: {len(invalid)} invalid concepts detected: {', '.join(invalid)}")
            return {"action": "continue"}

        ctx.register_hook("on_session_start", on_session_start_hook)

    return True


__all__ = [
    "verify_concept",
    "list_concepts",
    "parse_frontmatter",
    "get_concepts_dir",
    "register",
]
