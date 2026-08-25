"""amd_memory.py — Agent Memory Distillation (AMD) 3-tier memory rail (core).

Canonical repo source for CP-3 (CONVERGENCE_PLAN_2026-08-13 §9 CP-3; Batch-H
#34 + Batch-I run-2 R8 — DOUBLE-CONFIRMED, training-free, +27.2 pp AppWorld
@4B, dense > BM25 by up to 9.7 pp). The Hermes middleware twin lives at
plugins/amd_memory.py (installed into the lever profiles by
bin/sync_lever_plugins.sh); this module is the offline/build-side core: the
3-tier memory bank, the deterministic extraction pipeline (from OUR OWN
successful HILO trajectories), k=1 retrieval (BM25 stdlib default with a
dense backend when sentence-transformers is available), and the Text/Code/Code
injection renderers.

The AMD recipe this implements (Batch-H GDR answer §1, verified):
- Workflow memory — task-level strategy, TEXT format (natural-language prose),
  typed placeholders (<ID>, <EMAIL>) masking runtime values; injected
  PROACTIVELY at task start (system-prompt prefix).
- Subtask memory — intermediate behavioral examples, CODE format (executable
  code + the environment observation); injected PROACTIVELY, retrieved
  dynamically from the student's own decomposition labels.
- Function memory — per-function calling conventions + pitfalls, CODE format,
  indexed by function name; injected REACTIVELY on tool-calling errors ONLY.
- Retrieval count = EXACTLY ONE (k=1): k>1 collapses accuracy 49.4% -> 33.3%.
- Text/Code/Code format is mandatory (49.40% vs Text/Text/Text 26.19%).
- Built EXCLUSIVELY from successful trajectories. Our e24 15/15 runs are the
  teacher corpus (the same 4B under the thinking+2400s harness = the harness
  IS the teacher; the paper's capability-gap caveat applies to zero-shot
  4B trajectories, not harness-scored successes).

Honest scope note: the extraction below is the deterministic first-cut (no LLM
in the loop — fully offline + testable). The paper's teacher-LLM distillation
prompts (Figures 13/14/15) are a later T1/P5 enhancement on the real stack;
the rail, store, retrieval, and injection mechanics are exactly what the
recipe requires and are validated by the offline suite.
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

# ── constants ────────────────────────────────────────────────────────────────
TIERS = ("workflow", "subtask", "function")
TIER_FORMAT = {"workflow": "text", "subtask": "code", "function": "code"}
MAX_EXCERPT_CHARS = 900          # per-entry code excerpt budget (context care)
MAX_WORKFLOW_CHARS = 700         # workflow prose budget
RETRIEVE_K = 1                   # HARD: AMD ablation — k=1 or nothing
_PLACEHOLDER_RE = re.compile(r"(/[\w.\-/]+\.\w+|\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\b|"
                             r"\b[A-Za-z0-9_]{16,}\b|ports?\s+[0-9]{2,5})")


class MemoryBank:
    """Project-scoped 3-tier memory store on disk (JSON entries + MD views).

    Layout (created by bin/project_init.py and bin/extract_amd_memory.py):
        <project>/memory-bank/
            workflow.md     — prose strategies (one block per entry)
            subtask.json    — [{label, desc, code, source, ts}]
            function.json   — [{name, convention, pitfall, example, source, ts}]
            corrections.md  — per-project human-correction ledger (CP-3 init)
    All writes are atomic (tmp + os.replace); every entry carries source+ts.
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.dir = self.root / "memory-bank"
        self.dir.mkdir(parents=True, exist_ok=True)

    # ── paths ──────────────────────────────────────────────────────────────
    @property
    def workflow_path(self): return self.dir / "workflow.md"

    @property
    def subtask_path(self): return self.dir / "subtask.json"

    @property
    def function_path(self): return self.dir / "function.json"

    @property
    def corrections_path(self): return self.dir / "corrections.md"

    # ── loaders (fail-open: missing/corrupt = empty) ───────────────────────
    def workflow_entries(self):
        out = []
        if self.workflow_path.exists():
            for block in self.workflow_path.read_text(encoding="utf-8").split("---"):
                block = block.strip()
                if block:
                    out.append(block)
        return out

    def subtask_entries(self):
        return self._load_json(self.subtask_path, "subtasks")

    def function_entries(self):
        return self._load_json(self.function_path, "functions")

    def _load_json(self, path: Path, key: str):
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
            return list(d.get(key, [])) if isinstance(d, dict) else []
        except Exception:
            return []

    # ── mutators (idempotent merge by source/id, atomic write) ─────────────
    def add_workflow(self, block: str, source: str):
        blocks = self.workflow_entries()
        new = f"## {source}\n\n{block.strip()}\n"
        blocks = [b for b in blocks if source not in b.splitlines()[0]]
        blocks.append(new)
        self._atomic_text(self.workflow_path, "---\n".join(blocks) + "\n---\n")

    def add_subtask(self, entry: dict):
        entries = self.subtask_entries()
        entries = [e for e in entries if e.get("source") != entry.get("source")]
        entries.append(entry)
        self._atomic_json(self.subtask_path, {"subtasks": entries})

    def add_function(self, entry: dict):
        entries = self.function_entries()
        entries = [e for e in entries if e.get("name") != entry.get("name")
                   or e.get("source") != entry.get("source")]
        entries.append(entry)
        self._atomic_json(self.function_path, {"functions": entries})

    def add_correction(self, line: str):
        with open(self.corrections_path, "a", encoding="utf-8") as f:
            f.write(line.rstrip() + "\n")

    def _atomic_text(self, path: Path, text: str):
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)

    def _atomic_json(self, path: Path, data: dict):
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, path)

    # ── retrieval (k=1 enforced) ───────────────────────────────────────────
    def retrieve(self, tier: str, query: str, k: int = RETRIEVE_K,
                 backend: str = "auto"):
        """Return up to k=1 best entry for tier+query.

        backend: auto -> dense when sentence-transformers is importable and
        a model is available (HILO_AMD_EMBED_MODEL), else BM25; 'dense' forces
        dense (falls back to BM25 on import error); 'bm25' forces BM25.
        k is HARD-clamped to 1 (AMD ablation)."""
        k = min(int(k), RETRIEVE_K) if k else RETRIEVE_K
        if tier == "workflow":
            entries = [{"id": f"w{i}", "text": b} for i, b in
                       enumerate(self.workflow_entries())]
            if not entries:
                return None
            if backend == "dense" or (backend == "auto" and _dense_available()):
                idx = _dense_top(entries, "text", query)
            else:
                idx = _bm25_top([e["text"] for e in entries], query)
            return {"tier": tier, "k": k, "entry": entries[idx], "backend":
                    "dense" if (backend != "bm25" and _dense_available()) else "bm25"}
        if tier == "subtask":
            entries = self.subtask_entries()
            if not entries:
                return None
            texts = [f"{e.get('label', '')} {e.get('desc', '')}" for e in entries]
            if backend == "dense" or (backend == "auto" and _dense_available()):
                idx = _dense_top(entries, None, query, key=lambda e:
                                 f"{e.get('label','')} {e.get('desc','')}")
            else:
                idx = _bm25_top(texts, query)
            return {"tier": tier, "k": k, "entry": entries[idx], "backend":
                    "dense" if (backend != "bm25" and _dense_available()) else "bm25"}
        if tier == "function":
            entries = self.function_entries()
            if not entries:
                return None
            texts = [f"{e.get('name', '')} {e.get('convention', '')} "
                     f"{e.get('pitfall', '')}" for e in entries]
            if backend == "dense" or (backend == "auto" and _dense_available()):
                idx = _dense_top(entries, None, query, key=lambda e:
                                 f"{e.get('name','')} {e.get('convention','')} "
                                 f"{e.get('pitfall','')}")
            else:
                idx = _bm25_top(texts, query)
            return {"tier": tier, "k": k, "entry": entries[idx], "backend":
                    "dense" if (backend != "bm25" and _dense_available()) else "bm25"}
        return None

    # ── injection renderers (Text/Code/Code) ───────────────────────────────
    def render_workflow(self, max_chars: int = MAX_WORKFLOW_CHARS) -> str | None:
        blocks = self.workflow_entries()
        if not blocks:
            return None
        text = "\n\n".join(b.split("\n", 1)[1].strip() if "\n" in b else b
                           for b in blocks)
        return _truncate(text, max_chars)

    def render_subtask(self, entry: dict, max_chars: int = MAX_EXCERPT_CHARS) -> str:
        code = _truncate(entry.get("code", ""), max_chars)
        return (f"[Subtask {entry.get('label', '?')}] — {entry.get('desc', '')}\n"
                f"```\n{code}\n```")

    def render_function(self, entry: dict, max_chars: int = MAX_EXCERPT_CHARS) -> str:
        return (f"[Function {entry.get('name', '?')}] convention: "
                f"{entry.get('convention', '')}\n"
                f"pitfall: {entry.get('pitfall', '')}\n"
                f"```\n{_truncate(entry.get('example', ''), max_chars)}\n```")


# ── deterministic extraction from HILO checkpoints ─────────────────────────
def extract_from_hilo(checkpoint: dict, corpus_dir: str | Path | None = None):
    """Build 3-tier memory entries from a HILO run checkpoint (pass cells).

    checkpoint: the driver checkpoint.json dict (cells: {task_id: cell}).
    corpus_dir: optional path to tasks_hilo.json to enrich workflow text with
    the task title/spec (falls back to task id only).
    Returns {"workflow": [str], "subtask": [dict], "function": [dict]}.
    """
    titles = {}
    if corpus_dir:
        try:
            d = json.loads(Path(corpus_dir).read_text(encoding="utf-8"))
            for t in d.get("tasks", []):
                titles[t["id"]] = t.get("title", "")
        except Exception:
            pass
    cells = (checkpoint or {}).get("cells", {}) if isinstance(checkpoint, dict) else {}
    workflow, subtask, functions = [], [], []
    for tid, cell in cells.items():
        if not isinstance(cell, dict) or cell.get("status") != "pass":
            continue
        attempts = cell.get("attempts") or []
        ok = [a for a in attempts if isinstance(a, dict) and a.get("rc") == 0]
        if not ok:
            continue
        best = ok[-1]
        title = titles.get(tid, tid)
        # Workflow: generalized strategy prose with placeholders (Text tier).
        note = (best.get("note") or "").strip()
        wf = (f"Strategy for {title}: a working solution exists — the final "
              f"attempt ({best.get('class') or 'pass'}) succeeded after "
              f"{len(attempts)} attempt(s), {int(best.get('latency_s') or 0)}s.")
        if note:
            wf += " Key evidence: " + _mask_placeholders(_truncate(note, 240))
        workflow.append((tid, wf))
        # Subtask: per successful attempt, CODE format (label/desc/code).
        code = _mask_placeholders(_truncate(best.get("output_excerpt") or "", MAX_EXCERPT_CHARS))
        subtask.append({
            "label": f"{tid}-{best.get('n', 1)}",
            "desc": _one_sentence(note or f"successful attempt for {title}"),
            "code": code or "return 0  # (no excerpt recorded)",
            "source": tid,
            "ts": _ts(),
        })
        # Function: conventions/pitfalls keyed by detected callables.
        functions.extend(_extract_functions(best, tid))
    return {"workflow": workflow, "subtask": subtask, "function": functions}


def _extract_functions(attempt: dict, source: str):
    """Heuristic function-memory extraction from one attempt's note/excerpt."""
    out = []
    blob = " ".join([str(attempt.get("note") or ""),
                     str(attempt.get("output_excerpt") or "")])
    seen = set()
    for m in re.finditer(r"\b(def\s+([A-Za-z_]\w*)|([A-Za-z_]\w*)\([^)]{0,60}\))", blob):
        name = m.group(2) or m.group(3)
        if not name or name in ("if", "for", "while", "return", "print", "not", "and"):
            continue
        if name in seen:
            continue
        seen.add(name)
        err = (attempt.get("class") or "") if isinstance(attempt, dict) else ""
        out.append({
            "name": name,
            "convention": f"{name}(...) called in the successful attempt",
            "pitfall": f"error class observed: {err or 'none'}; check args/imports",
            "example": _mask_placeholders(_truncate(attempt.get("output_excerpt") or "", 200)),
            "source": source,
            "ts": _ts(),
        })
    return out[:6]  # cap per attempt


# ── retrieval backends ──────────────────────────────────────────────────────
def _bm25_top(texts, query):
    """Deterministic stdlib BM25-ish ranking (token overlap × IDF-ish)."""
    import math
    qtoks = _tokens(query)
    if not qtoks or not texts:
        return 0
    n = len(texts)
    doc_toks = [_tokens(t) for t in texts]
    scores = []
    for toks in doc_toks:
        if not toks:
            scores.append(0.0)
            continue
        s = 0.0
        for q in qtoks:
            if q in toks:
                s += 1.0 + math.log((n + 1) / (1 + sum(1 for d in doc_toks if q in d)))
        scores.append(s / len(toks))
    return max(range(n), key=lambda i: scores[i])


def _dense_available():
    try:
        import sentence_transformers  # noqa: F401
        return True
    except Exception:
        return False


def _dense_top(entries, text_key, query, key=None):
    """Top-1 by cosine similarity (sentence-transformers, CPU-friendly small
    model HILO_AMD_EMBED_MODEL, default all-MiniLM-L6-v2). Falls back to BM25
    on any import/model error (never raises)."""
    try:
        from sentence_transformers import SentenceTransformer
        model_name = os.environ.get("HILO_AMD_EMBED_MODEL", "all-MiniLM-L6-v2")
        model = SentenceTransformer(model_name)
        texts = [key(e) if key else e.get(text_key or "text", "") for e in entries]
        emb = model.encode([query] + texts, normalize_embeddings=True)
        import numpy as np
        sims = np.dot(emb[1:], emb[0])
        return int(np.argmax(sims))
    except Exception:
        texts = [key(e) if key else e.get(text_key or "text", "") for e in entries]
        return _bm25_top(texts, query)


# ── helpers ─────────────────────────────────────────────────────────────────
def _tokens(text: str):
    return re.findall(r"[a-z0-9_]{2,}", (text or "").lower())


def _mask_placeholders(text: str):
    """Replace runtime values (paths, emails, long ids) with typed tags."""
    text = _PLACEHOLDER_RE.sub("<ID>", text or "")
    return text


def _one_sentence(text: str):
    t = (text or "").strip().splitlines()[0][:180]
    return t + ("…" if len(text or "") > 180 else "")


def _truncate(text: str, n: int):
    t = (text or "").strip()
    return t[:n] + ("…" if len(t) > n else "")


def _ts():
    return time.strftime("%Y-%m-%dT%H:%M:%S")
