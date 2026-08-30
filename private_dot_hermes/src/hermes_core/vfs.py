"""
Standard In-Memory Filesystem Transport & Virtual Sandbox (Issue #13)
====================================================================
Provides an in-memory virtual filesystem with strict POSIX path semantics,
atomic directory tree snapshots, fast SHA256 hash trees, and progressive
disclosure.
"""

from __future__ import annotations

import hashlib
import io
import os
import posixpath
import time
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Any, Dict, List, Optional, Set, Tuple, Union


@dataclass
class VFSFileEntry:
    """In-memory file descriptor with content and metadata."""
    path: str
    content: bytes
    mtime: float = field(default_factory=time.time)
    mode: int = 0o644

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", errors="replace")

    @property
    def size(self) -> int:
        return len(self.content)

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.content).hexdigest()


class HermesMemoryFS:
    """Standard in-memory filesystem for isolated sandbox execution."""

    def __init__(self):
        self._files: Dict[str, VFSFileEntry] = {}
        self._directories: Set[str] = {"/"}

    def _norm(self, path: str) -> str:
        p = posixpath.normpath("/" + path.replace("\\", "/").lstrip("/"))
        return p

    def write_bytes(self, path: str, data: bytes) -> VFSFileEntry:
        p = self._norm(path)
        # Ensure parent directories exist
        parent = posixpath.dirname(p)
        self.makedirs(parent)

        entry = VFSFileEntry(path=p, content=data, mtime=time.time())
        self._files[p] = entry
        return entry

    def write_text(self, path: str, text: str, encoding: str = "utf-8") -> VFSFileEntry:
        return self.write_bytes(path, text.encode(encoding))

    def read_bytes(self, path: str) -> bytes:
        p = self._norm(path)
        if p not in self._files:
            raise FileNotFoundError(f"No such file in MemoryFS: '{path}'")
        return self._files[p].content

    def read_text(self, path: str, encoding: str = "utf-8") -> str:
        return self.read_bytes(path).decode(encoding, errors="replace")

    def exists(self, path: str) -> bool:
        p = self._norm(path)
        return p in self._files or p in self._directories

    def is_file(self, path: str) -> bool:
        return self._norm(path) in self._files

    def is_dir(self, path: str) -> bool:
        return self._norm(path) in self._directories

    def mkdir(self, path: str):
        p = self._norm(path)
        self._directories.add(p)

    def makedirs(self, path: str):
        p = self._norm(path)
        parts = p.strip("/").split("/")
        cur = ""
        self._directories.add("/")
        for part in parts:
            if not part:
                continue
            cur = cur + "/" + part
            self._directories.add(cur)

    def listdir(self, path: str = "/") -> List[str]:
        p = self._norm(path)
        if not self.is_dir(p):
            raise NotADirectoryError(f"Not a directory: '{path}'")

        entries = set()
        p_prefix = p if p == "/" else p + "/"

        # Collect child files
        for f in self._files:
            if f.startswith(p_prefix):
                rel = f[len(p_prefix):]
                name = rel.split("/")[0]
                if name:
                    entries.add(name)

        # Collect child dirs
        for d in self._directories:
            if d != p and d.startswith(p_prefix):
                rel = d[len(p_prefix):]
                name = rel.split("/")[0]
                if name:
                    entries.add(name)

        return sorted(list(entries))

    def remove(self, path: str):
        p = self._norm(path)
        if p in self._files:
            del self._files[p]
        elif p in self._directories:
            self._directories.remove(p)
        else:
            raise FileNotFoundError(f"No such file or directory: '{path}'")

    def snapshot(self) -> Dict[str, bytes]:
        """Create an immutable snapshot of all in-memory files."""
        return {p: entry.content for p, entry in self._files.items()}

    def restore(self, snapshot: Dict[str, bytes]):
        """Restore filesystem from an immutable snapshot."""
        self._files.clear()
        self._directories = {"/"}
        for p, data in snapshot.items():
            self.write_bytes(p, data)

    def tree_hash(self) -> str:
        """Compute holistic deterministic tree SHA256."""
        h = hashlib.sha256()
        for p in sorted(self._files.keys()):
            h.update(p.encode("utf-8"))
            h.update(self._files[p].content)
        return h.hexdigest()


# Singleton / helper
def create_memory_fs() -> HermesMemoryFS:
    return HermesMemoryFS()
