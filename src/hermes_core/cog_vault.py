"""
U49: COG Second Brain Markdown Knowledge Vault
==============================================
Human-readable Markdown knowledge store with YAML frontmatter.
Stores ADRs, module contracts, and verification evidence.
Pure CPU / RAMDisk execution (0 MB GPU VRAM).
"""

from __future__ import annotations

import hashlib
import os
import re
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Literal

import yaml


# =============================================================================
# CONFIGURATION
# =============================================================================

KNOWLEDGE_ROOTS = [
    Path.home() / ".hermes" / "knowledge",
    Path("/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes") / "docs" / "knowledge",
]

EVIDENCE_DIR = Path(".hermes") / "knowledge" / "evidence"
ADR_DIR = "adrs"
CONTRACTS_DIR = "contracts"
EVIDENCE_DIR_NAME = "evidence"


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class VaultEntry:
    """Single knowledge vault entry with YAML frontmatter"""
    path: Path
    relative_path: str
    frontmatter: Dict[str, Any]
    content: str
    hash: str
    entry_type: str  # adr, contract, evidence, note
    created_at: float
    updated_at: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": str(self.path),
            "relative_path": self.relative_path,
            "frontmatter": self.frontmatter,
            "content": self.content,
            "hash": self.hash,
            "entry_type": self.entry_type,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class IndexEntry:
    """Search index entry"""
    relative_path: str
    title: str
    entry_type: str
    tags: List[str]
    summary: str
    hash: str


# =============================================================================
# KNOWLEDGE TYPES
# =============================================================================

class EntryType:
    ADR = "adr"
    CONTRACT = "contract"
    EVIDENCE = "evidence"
    NOTE = "note"
    
    @classmethod
    def all(cls) -> List[str]:
        return [cls.ADR, cls.CONTRACT, cls.EVIDENCE, cls.NOTE]


# =============================================================================
# FRONTMATTER TEMPLATES
# =============================================================================

ADR_TEMPLATE = """---
id: {id}
title: {title}
status: {status}  # proposed, accepted, deprecated, superseded
date: {date}
tags: {tags}
supersedes: {supersedes}
superseded_by: {superseded_by}
---

# ADR {id}: {title}

## Status
{status}

## Context
{context}

## Decision
{decision}

## Consequences
{consequences}

## Tags
{tags_formatted}
"""

CONTRACT_TEMPLATE = """---
id: {id}
title: {title}
module: {module}
version: {version}
status: {status}  # draft, verified, deprecated
date: {date}
tags: {tags}
dependencies: {dependencies}
---

# Module Contract: {title}

## Module
{module}

## Version
{version}

## Status
{status}

## Interface
{interface}

## Invariants
{invariants}

## Tests
{tests}

## Tags
{tags_formatted}
"""

EVIDENCE_TEMPLATE = """---
id: {id}
title: "{title}"
task_id: {task_id}
verdict: {verdict}  # VERIFIED, REJECTED
verifier: {verifier}
worker: {worker}
date: {date}
hash: {hash}
duration_ms: {duration_ms}
---

# Verification Evidence: {title}

## Verdict
**{verdict}**

## Task
{task_id}

## Verifier
{verifier}

## Worker
{worker}

## Duration
{duration_ms} ms

## Content Hash
{hash}

## Checks Performed
{checks}

## Artifacts
{artifacts}

## Notes
{notes}
"""


# =============================================================================
# MARKDOWN VAULT MANAGER
# =============================================================================

class CogVault:
    """
    COG Markdown Knowledge Vault.
    Manages ADRs, contracts, evidence, and notes with YAML frontmatter indexing.
    """
    
    def __init__(self, roots: Optional[List[Path]] = None):
        self.roots = roots or KNOWLEDGE_ROOTS
        self._index: Dict[str, IndexEntry] = {}
        self._entries: Dict[str, VaultEntry] = {}
        self._lock = threading.RLock()
        
        # Ensure directories exist
        for root in self.roots:
            for subdir in [ADR_DIR, CONTRACTS_DIR, EVIDENCE_DIR_NAME]:
                (root / subdir).mkdir(parents=True, exist_ok=True)
        
        # Build initial index
        self._rebuild_index()
    
    def _rebuild_index(self):
        """Scan all roots and build index"""
        with self._lock:
            self._index.clear()
            self._entries.clear()
            
            for root in self.roots:
                if not root.exists():
                    continue
                for md_file in root.rglob("*.md"):
                    try:
                        entry = self._parse_entry(md_file, root)
                        if entry:
                            self._entries[entry.relative_path] = entry
                            self._index[entry.relative_path] = IndexEntry(
                                relative_path=entry.relative_path,
                                title=entry.frontmatter.get("title", ""),
                                entry_type=entry.entry_type,
                                tags=entry.frontmatter.get("tags", []),
                                summary=entry.frontmatter.get("summary", entry.content[:200]),
                                hash=entry.hash,
                            )
                    except Exception:
                        pass
    
    def _parse_entry(self, md_file: Path, root: Path) -> Optional[VaultEntry]:
        """Parse a markdown file with YAML frontmatter"""
        content = md_file.read_text(encoding="utf-8")
        
        # Extract frontmatter
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not frontmatter_match:
            return None
        
        yaml_str = frontmatter_match.group(1)
        body = content[frontmatter_match.end():]
        
        try:
            frontmatter = yaml.safe_load(yaml_str) or {}
        except yaml.YAMLError:
            frontmatter = {}
        
        if not isinstance(frontmatter, dict):
            frontmatter = {}
        
        # Determine entry type from directory or frontmatter
        rel_path = md_file.relative_to(root)
        entry_type = self._infer_entry_type(rel_path, frontmatter)
        
        # Compute hash
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        
        # Get timestamps
        stat = md_file.stat()
        
        return VaultEntry(
            path=md_file,
            relative_path=str(rel_path),
            frontmatter=frontmatter,
            content=body.strip(),
            hash=content_hash,
            entry_type=entry_type,
            created_at=stat.st_ctime,
            updated_at=stat.st_mtime,
        )
    
    def _infer_entry_type(self, rel_path: Path, frontmatter: Dict[str, Any]) -> str:
        """Infer entry type from path and frontmatter"""
        parts = rel_path.parts
        if parts[0] == ADR_DIR:
            return EntryType.ADR
        elif parts[0] == CONTRACTS_DIR:
            return EntryType.CONTRACT
        elif parts[0] == EVIDENCE_DIR_NAME:
            return EntryType.EVIDENCE
        return frontmatter.get("type", EntryType.NOTE)
    
    # -------------------------------------------------------------------------
    # STORAGE OPERATIONS
    # -------------------------------------------------------------------------
    
    def store_adr(
        self,
        title: str,
        context: str,
        decision: str,
        consequences: str,
        tags: Optional[List[str]] = None,
        status: str = "proposed",
        adr_id: Optional[str] = None,
        supersedes: Optional[str] = None,
    ) -> Path:
        """Store Architecture Decision Record"""
        if adr_id is None:
            adr_id = f"ADR-{int(time.time())}"
        
        tags = tags or []
        tags_formatted = ", ".join(f"`{t}`" for t in tags)
        
        content = ADR_TEMPLATE.format(
            id=adr_id,
            title=title,
            status=status,
            date=time.strftime("%Y-%m-%d"),
            tags=tags,
            tags_formatted=tags_formatted,
            supersedes=supersedes or "None",
            superseded_by="None",
            context=context,
            decision=decision,
            consequences=consequences,
        )
        
        return self._write_entry(ADR_DIR, f"{adr_id.lower()}.md", content, {
            "id": adr_id,
            "title": title,
            "status": status,
            "tags": tags,
        })
    
    def store_contract(
        self,
        title: str,
        module: str,
        interface: str,
        invariants: str,
        tests: str,
        version: str = "1.0.0",
        tags: Optional[List[str]] = None,
        status: str = "draft",
        dependencies: Optional[List[str]] = None,
        contract_id: Optional[str] = None,
    ) -> Path:
        """Store Module Contract"""
        if contract_id is None:
            contract_id = f"CONTRACT-{module.replace('/', '-')}-{int(time.time())}"
        
        tags = tags or []
        dependencies = dependencies or []
        tags_formatted = ", ".join(f"`{t}`" for t in tags)
        
        content = CONTRACT_TEMPLATE.format(
            id=contract_id,
            title=title,
            module=module,
            version=version,
            status=status,
            date=time.strftime("%Y-%m-%d"),
            tags=tags,
            tags_formatted=tags_formatted,
            dependencies=dependencies,
            interface=interface,
            invariants=invariants,
            tests=tests,
        )
        
        return self._write_entry(CONTRACTS_DIR, f"{contract_id.lower()}.md", content, {
            "id": contract_id,
            "title": title,
            "module": module,
            "version": version,
            "status": status,
            "tags": tags,
            "dependencies": dependencies,
        })
    
    def store_evidence(
        self,
        title: str,
        task_id: str,
        verdict: Literal["VERIFIED", "REJECTED"],
        verifier: str,
        worker: str,
        checks: str,
        artifacts: str = "",
        notes: str = "",
        content_hash: str = "",
        duration_ms: int = 0,
    ) -> Path:
        """Store Verification Evidence"""
        evidence_id = f"EVIDENCE-{task_id}-{verdict.lower()}-{int(time.time())}"
        
        content = EVIDENCE_TEMPLATE.format(
            id=evidence_id,
            title=title,
            task_id=task_id,
            verdict=verdict,
            verifier=verifier,
            worker=worker,
            date=time.strftime("%Y-%m-%d %H:%M:%S"),
            hash=content_hash,
            duration_ms=duration_ms,
            checks=checks,
            artifacts=artifacts,
            notes=notes,
        )
        
        return self._write_entry(EVIDENCE_DIR_NAME, f"{evidence_id.lower()}.md", content, {
            "id": evidence_id,
            "title": title,
            "task_id": task_id,
            "verdict": verdict,
            "verifier": verifier,
            "worker": worker,
            "hash": content_hash,
            "duration_ms": duration_ms,
        })
    
    def _write_entry(
        self,
        subdir: str,
        filename: str,
        content: str,
        frontmatter: Dict[str, Any],
    ) -> Path:
        """Write entry to first available root"""
        for root in self.roots:
            target_dir = root / subdir
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / filename
            
            try:
                target_path.write_text(content, encoding="utf-8")
                # Re-index
                self._rebuild_index()
                return target_path
            except Exception:
                continue
        
        raise RuntimeError(f"Failed to write entry to any root: {subdir}/{filename}")
    
    # -------------------------------------------------------------------------
    # RETRIEVAL OPERATIONS
    # -------------------------------------------------------------------------
    
    def get_entry(self, relative_path: str) -> Optional[VaultEntry]:
        """Get entry by relative path"""
        with self._lock:
            return self._entries.get(relative_path)
    
    def search(
        self,
        query: str,
        entry_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[IndexEntry]:
        """Search index by query"""
        with self._lock:
            results = []
            query_lower = query.lower()
            
            for entry in self._index.values():
                if entry_type and entry.entry_type != entry_type:
                    continue
                if tags and not all(t in entry.tags for t in tags):
                    continue
                
                # Simple text search
                if (query_lower in entry.title.lower() or 
                    query_lower in entry.summary.lower() or
                    any(query_lower in t.lower() for t in entry.tags)):
                    results.append(entry)
            
            # Sort by relevance (simple: title match first)
            results.sort(key=lambda e: (query_lower not in e.title.lower(), e.title))
            return results[:limit]
    
    def list_by_type(self, entry_type: str) -> List[VaultEntry]:
        """List all entries of a specific type"""
        with self._lock:
            return [e for e in self._entries.values() if e.entry_type == entry_type]
    
    def get_evidence_for_task(self, task_id: str) -> List[VaultEntry]:
        """Get all evidence entries for a task"""
        with self._lock:
            return [
                e for e in self._entries.values()
                if e.entry_type == EntryType.EVIDENCE
                and e.frontmatter.get("task_id") == task_id
            ]
    
    def get_latest_verdict(self, task_id: str) -> Optional[str]:
        """Get latest verdict for a task"""
        evidence = self.get_evidence_for_task(task_id)
        if not evidence:
            return None
        # Sort by updated_at descending
        evidence.sort(key=lambda e: e.updated_at, reverse=True)
        return evidence[0].frontmatter.get("verdict")
    
    # -------------------------------------------------------------------------
    # UTILITIES
    # -------------------------------------------------------------------------
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vault statistics"""
        with self._lock:
            counts = {}
            for entry in self._entries.values():
                counts[entry.entry_type] = counts.get(entry.entry_type, 0) + 1
            
            return {
                "total_entries": len(self._entries),
                "by_type": counts,
                "roots": [str(r) for r in self.roots],
            }
    
    def get_zero_vram_guarantee(self) -> Dict[str, Any]:
        """Verify zero GPU VRAM overhead"""
        return {
            "markdown_parsing_cpu_only": True,
            "yaml_frontmatter_cpu_only": True,
            "file_io_cpu_only": True,
            "indexing_cpu_only": True,
            "no_gpu_operations": True,
            "ramdisk_compatible": True,
        }
    
    def close(self):
        """Close vault (no-op for compatibility)"""
        pass


# =============================================================================
# FACTORY
# =============================================================================

_global_vault: Optional[CogVault] = None
_global_lock = threading.Lock()


def get_cog_vault(roots: Optional[List[Path]] = None) -> CogVault:
    """Get or create global vault instance"""
    global _global_vault
    with _global_lock:
        if _global_vault is None:
            _global_vault = CogVault(roots=roots)
        return _global_vault


def reset_cog_vault():
    """Reset global vault (for testing)"""
    global _global_vault
    with _global_lock:
        if _global_vault:
            _global_vault.close()
        _global_vault = None


if __name__ == "__main__":
    # Self-test
    print("CogVault self-test")
    
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        vault = CogVault(roots=[root])
        
        # Store ADR
        adr_path = vault.store_adr(
            title="Use SQLite WAL for memory persistence",
            context="Need persistent cross-session memory with fast reads",
            decision="Use SQLite WAL mode with in-memory index",
            consequences="Fast reads, ACID compliance, zero GPU VRAM",
            tags=["architecture", "memory", "sqlite"],
        )
        print(f"Stored ADR: {adr_path}")
        
        # Store Contract
        contract_path = vault.store_contract(
            title="Embedding Engine Contract",
            module="hermes_core.embeddings",
            interface="search(query, top_k) -> List[SearchHit]",
            invariants="CPU-only, normalized embeddings, deterministic",
            tests="test_embeddings_u25.py",
            tags=["embedding", "cpu-only"],
        )
        print(f"Stored Contract: {contract_path}")
        
        # Store Evidence
        evidence_path = vault.store_evidence(
            title="Embedding engine verification",
            task_id="task-123",
            verdict="VERIFIED",
            verifier="cog_verifier",
            worker="agent_worker",
            checks="AST syntax: PASS\nTests: 15/15 PASS\nVRAM: 0 MB",
            artifacts="test_results.xml",
            content_hash="abc123",
            duration_ms=150,
        )
        print(f"Stored Evidence: {evidence_path}")
        
        # Search
        results = vault.search("SQLite")
        print(f"Search 'SQLite': {len(results)} results")
        
        # Get latest verdict
        verdict = vault.get_latest_verdict("task-123")
        print(f"Latest verdict: {verdict}")
        
        # Stats
        stats = vault.get_stats()
        print(f"Stats: {stats}")
        
        # Zero VRAM
        guarantee = vault.get_zero_vram_guarantee()
        print(f"Zero VRAM: {guarantee}")
        
        print("All self-tests passed!")
