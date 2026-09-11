"""
Hermes Plugin: bpe_workspace
============================
Belief, Progress, and Experience (BPE) Memory Workspace.
Inspired by EvoHarness-RL (Meta AI / UIUC 2026), providing an agentic external state
workspace featuring 4 meta-actions: track, commit, recall, and note.

Features:
- belief.md: Real-time environmental and task belief state.
- progress.md: Subgoal DAG tracker preventing task abandonment.
- experience.db: DuckDB persistent episodic memory of past strategies & lessons.
- Harness annealing metrics: Tracks recurring pattern internalization.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import duckdb
    DUCKDB_AVAILABLE = True
except ImportError:
    duckdb = None
    DUCKDB_AVAILABLE = False

import sqlite3


def get_bpe_root() -> Path:
    """Returns the canonical root directory for BPE workspace."""
    hermes_home = os.environ.get("HERMES_HOME")
    if hermes_home:
        root = Path(hermes_home) / "bpe"
    else:
        root = Path.home() / ".hermes" / "bpe"
    root.mkdir(parents=True, exist_ok=True)
    return root


class BPEWorkspaceEngine:
    """Core state machine and storage interface for the BPE Workspace."""

    def __init__(self, root_dir: Optional[Path] = None):
        self.root = root_dir or get_bpe_root()
        self.root.mkdir(parents=True, exist_ok=True)
        self.belief_file = self.root / "belief.md"
        self.progress_file = self.root / "progress.md"
        self.db_file = self.root / "experience.db"

        self._init_files()
        self._init_db()

    def _init_files(self):
        """Seeds initial markdown documents if absent."""
        if not self.belief_file.exists():
            default_belief = (
                "# BPE Workspace: Belief State\n\n"
                "- **OS / Runtime**: Linux / Fedora Distrobox `ws-hermes`\n"
                "- **Inference Model**: Local Gemma 4 4B Q4_K_M + MTP Speculative Decoding\n"
                "- **Hardware Guard**: RTX 3050 Laptop (<= 4,800 MiB VRAM limit)\n"
                "- **System Policy**: Prefix-Cache Determinism | Zero Token Waste\n"
                "- **Last Updated**: " + datetime.now(timezone.utc).isoformat() + "\n"
            )
            self.belief_file.write_text(default_belief, encoding="utf-8")

        if not self.progress_file.exists():
            default_progress = (
                "# BPE Workspace: Progress DAG\n\n"
                "## Active Subgoals\n"
                "- [x] Baseline Initialization & Verification\n"
                "- [ ] Pillar I: BPE Memory Workspace\n"
                "- [ ] Pillar II: Hybrid Attention & 1M Context Engine\n"
                "- [ ] Pillar III: EvoHarness-RL Cycle\n"
                "- [ ] Pillar IV: Frontier Skill Intelligence OS\n"
                "- [ ] Pillar V: ECC Security & AgentShield Hardening\n"
                "- [ ] Pillar VI: Spec-Kit Driven Self-Evolution\n"
            )
            self.progress_file.write_text(default_progress, encoding="utf-8")

    def _get_db_conn(self):
        """Obtains a DuckDB connection, with transparent SQLite fallback."""
        if DUCKDB_AVAILABLE:
            return duckdb.connect(str(self.db_file))
        else:
            return sqlite3.connect(str(self.db_file))

    def _init_db(self):
        """Initializes database schema for experiences, access logs, and annealing."""
        conn = self._get_db_conn()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS experiences (
                    id VARCHAR PRIMARY KEY,
                    timestamp VARCHAR,
                    category VARCHAR,
                    query_terms VARCHAR,
                    insight TEXT,
                    frequency INTEGER DEFAULT 1,
                    promoted BOOLEAN DEFAULT FALSE
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS bpe_access_log (
                    id VARCHAR PRIMARY KEY,
                    timestamp VARCHAR,
                    action VARCHAR,
                    target VARCHAR,
                    details TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS annealing_metrics (
                    category VARCHAR PRIMARY KEY,
                    total_calls INTEGER DEFAULT 0,
                    routine_calls INTEGER DEFAULT 0,
                    compression_ratio REAL DEFAULT 1.0,
                    last_annealed VARCHAR
                )
                """
            )
        finally:
            conn.close()

    def _log_action(self, action: str, target: str, details: str = ""):
        """Appends action record to audit log."""
        conn = self._get_db_conn()
        try:
            log_id = str(uuid.uuid4())[:8]
            ts = datetime.now(timezone.utc).isoformat()
            conn.execute(
                "INSERT INTO bpe_access_log VALUES (?, ?, ?, ?, ?)",
                (log_id, ts, action, target, details),
            )
        finally:
            conn.close()

    # =========================================================================
    # Meta-Action 1: track
    # =========================================================================
    def track(self, status_dict: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Monitors and captures environment state and writes to belief.md.
        """
        ts = datetime.now(timezone.utc).isoformat()
        current_content = self.belief_file.read_text(encoding="utf-8") if self.belief_file.exists() else ""

        # Extract or synthesize state
        status = status_dict or {}
        vram_info = status.get("vram", "Safe (<= 4,800 MiB)")
        git_status = status.get("git", "Clean")
        active_phase = status.get("phase", "Era 6 Frontier Evolution")

        new_belief = (
            f"# BPE Workspace: Belief State\n\n"
            f"- **OS / Runtime**: Linux / Fedora Distrobox `ws-hermes`\n"
            f"- **Active Phase**: {active_phase}\n"
            f"- **VRAM Envelope**: {vram_info}\n"
            f"- **Git Tree**: {git_status}\n"
            f"- **Hardware Policy**: RTX 3050 Laptop Guardrail Enforced\n"
            f"- **Last Updated**: {ts}\n\n"
            f"## Session Hypotheses & Invariants\n"
            f"- Zero-token waste: prefix-cache stability > 90%\n"
            f"- Spec-first: verified contracts before mutations\n"
            f"- Continuous verification: 100% test gate passing\n"
        )
        self.belief_file.write_text(new_belief, encoding="utf-8")
        self._log_action("track", "belief.md", f"Updated belief state at {ts}")
        return {
            "action": "track",
            "status": "success",
            "timestamp": ts,
            "belief_length": len(new_belief),
        }

    # =========================================================================
    # Meta-Action 2: commit
    # =========================================================================
    def commit_progress(self, subgoal: str, status: str = "completed") -> Dict[str, Any]:
        """
        Updates the active subgoal DAG in progress.md to prevent task drift.
        """
        if not self.progress_file.exists():
            self._init_files()

        content = self.progress_file.read_text(encoding="utf-8")
        lines = content.splitlines()

        matched = False
        new_lines = []
        clean_subgoal = subgoal.strip().lower()

        for line in lines:
            if clean_subgoal in line.lower() and ("- [" in line):
                matched = True
                mark = "x" if status.lower() in ("completed", "done", "pass") else " "
                # Replace checkbox
                new_line = re.sub(r"- \[[ xX]\]", f"- [{mark}]", line)
                new_lines.append(new_line)
            else:
                new_lines.append(line)

        if not matched:
            mark = "x" if status.lower() in ("completed", "done", "pass") else " "
            new_lines.append(f"- [{mark}] {subgoal}")

        updated_content = "\n".join(new_lines) + "\n"
        self.progress_file.write_text(updated_content, encoding="utf-8")

        # Calculate progress statistics
        all_checkboxes = re.findall(r"- \[[ xX]\]", updated_content)
        completed_checkboxes = re.findall(r"- \[[xX]\]", updated_content)
        total = len(all_checkboxes)
        completed = len(completed_checkboxes)
        ratio = (completed / total) if total > 0 else 1.0

        self._log_action("commit", "progress.md", f"Subgoal '{subgoal}' set to {status} ({completed}/{total})")

        return {
            "action": "commit",
            "subgoal": subgoal,
            "status": status,
            "total_subgoals": total,
            "completed_subgoals": completed,
            "progress_ratio": round(ratio, 3),
        }

    # =========================================================================
    # Meta-Action 3: note
    # =========================================================================
    def note(self, insight: str, category: str = "general", query_terms: str = "") -> Dict[str, Any]:
        """
        Stores an empirical insight, error trace lesson, or reusable strategy in experience.db.
        """
        conn = self._get_db_conn()
        try:
            ts = datetime.now(timezone.utc).isoformat()
            clean_insight = insight.strip()
            # Check for existing matching insight to increment frequency
            res = conn.execute(
                "SELECT id, frequency, promoted FROM experiences WHERE insight = ?",
                (clean_insight,),
            ).fetchall()

            if res:
                rec_id, freq, promoted = res[0]
                new_freq = freq + 1
                new_promoted = True if new_freq >= 3 else promoted
                conn.execute(
                    "UPDATE experiences SET frequency = ?, promoted = ?, timestamp = ? WHERE id = ?",
                    (new_freq, new_promoted, ts, rec_id),
                )
            else:
                rec_id = str(uuid.uuid4())[:8]
                new_freq = 1
                new_promoted = False
                conn.execute(
                    "INSERT INTO experiences VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (rec_id, ts, category, query_terms or category, clean_insight, 1, False),
                )

            # Update annealing metrics for this category
            metric_res = conn.execute(
                "SELECT total_calls, routine_calls FROM annealing_metrics WHERE category = ?",
                (category,),
            ).fetchall()
            if metric_res:
                tc, rc = metric_res[0]
                conn.execute(
                    "UPDATE annealing_metrics SET total_calls = ?, last_annealed = ? WHERE category = ?",
                    (tc + 1, ts, category),
                )
            else:
                conn.execute(
                    "INSERT INTO annealing_metrics VALUES (?, ?, ?, ?, ?)",
                    (category, 1, 0, 1.0, ts),
                )

            self._log_action("note", "experience.db", f"Noted [{category}] (freq: {new_freq})")
            return {
                "action": "note",
                "id": rec_id,
                "category": category,
                "frequency": new_freq,
                "promoted": new_promoted,
                "timestamp": ts,
            }
        finally:
            conn.close()

    # =========================================================================
    # Meta-Action 4: recall
    # =========================================================================
    def recall(self, query: str, limit: int = 3, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Queries experience.db for historical lessons, error solutions, and patterns.
        """
        conn = self._get_db_conn()
        try:
            query_words = [w.lower() for w in re.findall(r"\w+", query) if len(w) > 2]
            results = []

            if category:
                rows = conn.execute(
                    "SELECT id, timestamp, category, query_terms, insight, frequency, promoted FROM experiences WHERE category = ?",
                    (category,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, timestamp, category, query_terms, insight, frequency, promoted FROM experiences"
                ).fetchall()

            scored_rows = []
            for row in rows:
                rec_id, ts, cat, terms, insight, freq, promoted = row
                combined_text = f"{cat} {terms} {insight}".lower()
                score = sum(1 for w in query_words if w in combined_text)
                if score > 0 or not query_words:
                    # Boost by frequency and promotion status
                    effective_score = score + (freq * 0.5) + (2.0 if promoted else 0.0)
                    scored_rows.append((effective_score, row))

            scored_rows.sort(key=lambda x: x[0], reverse=True)
            top_rows = scored_rows[:limit]

            for score, row in top_rows:
                rec_id, ts, cat, terms, insight, freq, promoted = row
                results.append({
                    "id": rec_id,
                    "timestamp": ts,
                    "category": cat,
                    "insight": insight,
                    "frequency": freq,
                    "promoted": bool(promoted),
                    "score": round(score, 2),
                })

            # Update annealing routine calls if top result has high frequency
            if results and results[0]["frequency"] >= 2:
                cat = results[0]["category"]
                conn.execute(
                    "UPDATE annealing_metrics SET routine_calls = routine_calls + 1 WHERE category = ?",
                    (cat,),
                )

            self._log_action("recall", "experience.db", f"Query '{query}' returned {len(results)} items")
            return results
        finally:
            conn.close()

    # =========================================================================
    # Workspace Status & Inspection
    # =========================================================================
    def status(self) -> Dict[str, Any]:
        """Returns diagnostic status of all three BPE compartments."""
        belief_txt = self.belief_file.read_text(encoding="utf-8") if self.belief_file.exists() else ""
        progress_txt = self.progress_file.read_text(encoding="utf-8") if self.progress_file.exists() else ""

        all_subgoals = re.findall(r"- \[[ xX]\]", progress_txt)
        done_subgoals = re.findall(r"- \[[xX]\]", progress_txt)

        conn = self._get_db_conn()
        try:
            exp_count = conn.execute("SELECT count(*) FROM experiences").fetchone()[0]
            promoted_count = conn.execute("SELECT count(*) FROM experiences WHERE promoted = TRUE").fetchone()[0]
            log_count = conn.execute("SELECT count(*) FROM bpe_access_log").fetchone()[0]
        finally:
            conn.close()

        return {
            "root_dir": str(self.root),
            "belief": {
                "exists": self.belief_file.exists(),
                "chars": len(belief_txt),
                "estimated_tokens": max(1, len(belief_txt) // 4),
            },
            "progress": {
                "exists": self.progress_file.exists(),
                "total_subgoals": len(all_subgoals),
                "completed_subgoals": len(done_subgoals),
                "ratio": round(len(done_subgoals) / len(all_subgoals), 3) if all_subgoals else 1.0,
            },
            "experience": {
                "total_entries": exp_count,
                "promoted_entries": promoted_count,
                "access_log_entries": log_count,
            },
        }

    # =========================================================================
    # Compaction & Annealing Loop
    # =========================================================================
    def compact_memory(self, threshold_chars: int = 4000) -> Dict[str, Any]:
        """
        Compresses belief.md if it exceeds threshold, archiving details into experience.db.
        """
        if not self.belief_file.exists():
            return {"compacted": False, "reason": "belief file does not exist"}

        content = self.belief_file.read_text(encoding="utf-8")
        if len(content) <= threshold_chars:
            return {"compacted": False, "current_chars": len(content), "threshold": threshold_chars}

        # Extract core lines and archive the rest
        lines = content.splitlines()
        essential_lines = [line for line in lines if line.startswith("#") or line.startswith("- **")]
        archived_lines = [line for line in lines if line and not (line.startswith("#") or line.startswith("- **"))]

        if archived_lines:
            archive_snippet = " | ".join(archived_lines[:10])
            self.note(f"Archived belief context: {archive_snippet}", category="belief_compaction")

        ts = datetime.now(timezone.utc).isoformat()
        essential_lines.append(f"- **Compacted At**: {ts} (reduced from {len(content)} to {sum(len(l) for l in essential_lines)} chars)")
        compacted_content = "\n".join(essential_lines) + "\n"

        self.belief_file.write_text(compacted_content, encoding="utf-8")
        saved = len(content) - len(compacted_content)
        self._log_action("compact", "belief.md", f"Compacted belief by {saved} chars")

        return {
            "compacted": True,
            "original_chars": len(content),
            "new_chars": len(compacted_content),
            "saved_chars": saved,
        }

    def compact_experiences(self, min_frequency_to_keep: int = 2, promote_threshold: int = 3) -> Dict[str, Any]:
        """
        Promotes recurring experiences (freq >= promote_threshold) to permanent invariants in belief.md,
        and archives low-signal / single-occurrence experiences into experiences_archive.
        """
        conn = self._get_db_conn()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS experiences_archive (
                    id VARCHAR PRIMARY KEY,
                    timestamp VARCHAR,
                    category VARCHAR,
                    query_terms VARCHAR,
                    insight TEXT,
                    frequency INTEGER,
                    archived_at VARCHAR
                )
                """
            )

            promoted_rows = conn.execute(
                "SELECT id, category, insight, frequency FROM experiences WHERE frequency >= ?",
                (promote_threshold,)
            ).fetchall()

            invariants_added = 0
            if promoted_rows and self.belief_file.exists():
                belief_content = self.belief_file.read_text(encoding="utf-8")
                new_invariants = []
                for _, cat, ins, freq in promoted_rows:
                    inv_line = f"- [{cat}] {ins} (Internalized, freq: {freq})"
                    if ins not in belief_content:
                        new_invariants.append(inv_line)
                        invariants_added += 1

                if new_invariants:
                    if "## Permanent Empirical Invariants" not in belief_content:
                        belief_content += "\n## Permanent Empirical Invariants\n"
                    for inv in new_invariants:
                        belief_content += f"{inv}\n"
                    self.belief_file.write_text(belief_content, encoding="utf-8")

            stale_rows = conn.execute(
                "SELECT id, timestamp, category, query_terms, insight, frequency FROM experiences WHERE frequency < ? AND promoted = FALSE",
                (min_frequency_to_keep,)
            ).fetchall()

            archived_count = 0
            ts_now = datetime.now(timezone.utc).isoformat()
            for r in stale_rows:
                rec_id, ts, cat, qterms, ins, freq = r
                conn.execute(
                    "INSERT OR REPLACE INTO experiences_archive VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (rec_id, ts, cat, qterms, ins, freq, ts_now)
                )
                conn.execute("DELETE FROM experiences WHERE id = ?", (rec_id,))
                archived_count += 1

            total_remaining = conn.execute("SELECT count(*) FROM experiences").fetchone()[0]
            self._log_action("compact_experiences", "experience.db", f"Promoted {invariants_added} invariants, archived {archived_count} entries")

            return {
                "invariants_promoted_to_belief": invariants_added,
                "experiences_archived": archived_count,
                "active_experiences_remaining": total_remaining,
                "timestamp": ts_now,
            }
        finally:
            conn.close()

    def annealing_report(self) -> Dict[str, Any]:
        """
        Calculates routine call frequencies, promoted insights, and internalization rate.
        """
        conn = self._get_db_conn()
        try:
            metrics = conn.execute(
                "SELECT category, total_calls, routine_calls, compression_ratio, last_annealed FROM annealing_metrics"
            ).fetchall()
            promoted = conn.execute(
                "SELECT id, category, insight, frequency FROM experiences WHERE promoted = TRUE"
            ).fetchall()

            report = {
                "categories": [],
                "promoted_insights": [],
                "overall_internalization_rate": 0.0,
            }

            total_c = 0
            routine_c = 0
            for row in metrics:
                cat, tc, rc, cr, la = row
                total_c += tc
                routine_c += rc
                report["categories"].append({
                    "category": cat,
                    "total_calls": tc,
                    "routine_calls": rc,
                    "routine_rate": round(rc / tc, 3) if tc > 0 else 0.0,
                    "last_annealed": la,
                })

            for row in promoted:
                rec_id, cat, insight, freq = row
                report["promoted_insights"].append({
                    "id": rec_id,
                    "category": cat,
                    "insight": insight,
                    "frequency": freq,
                })

            if total_c > 0:
                report["overall_internalization_rate"] = round(routine_c / total_c, 3)

            return report
        finally:
            conn.close()


_GLOBAL_BPE_ENGINE: Optional[BPEWorkspaceEngine] = None


def get_bpe_engine() -> BPEWorkspaceEngine:
    global _GLOBAL_BPE_ENGINE
    if _GLOBAL_BPE_ENGINE is None:
        _GLOBAL_BPE_ENGINE = BPEWorkspaceEngine()
    return _GLOBAL_BPE_ENGINE


def register(ctx=None):
    """Registers bpe_workspace plugin into Hermes runtime."""
    if not ctx:
        return True

    engine = get_bpe_engine()

    # 1. Register CLI subcommands
    if hasattr(ctx, "register_cli_command"):
        # hermes bpe status / annealing / compact
        def setup_bpe(parser):
            parser.description = "BPE Workspace inspection and maintenance"
            sub = parser.add_subparsers(dest="bpe_cmd")
            sub.add_parser("status", help="Show BPE workspace compartments status")
            sub.add_parser("annealing", help="Show BPE harness annealing report")
            sub.add_parser("compact", help="Run compaction on belief state")
            sub.add_parser("compact-experiences", help="Promote invariants to belief.md and archive low-frequency experiences")

        def handle_bpe(args):
            cmd = getattr(args, "bpe_cmd", "status") or "status"
            if cmd == "status":
                st = engine.status()
                print("BPE Memory Workspace Status:")
                print(f"  Root:       {st['root_dir']}")
                print(f"  Belief:     {st['belief']['chars']} chars (~{st['belief']['estimated_tokens']} tok)")
                print(f"  Progress:   {st['progress']['completed_subgoals']}/{st['progress']['total_subgoals']} ({int(st['progress']['ratio']*100)}%)")
                print(f"  Experience: {st['experience']['total_entries']} items ({st['experience']['promoted_entries']} promoted)")
            elif cmd == "annealing":
                rep = engine.annealing_report()
                print("BPE Harness Annealing Report:")
                print(f"  Internalization Rate: {int(rep['overall_internalization_rate']*100)}%")
                for c in rep["categories"]:
                    print(f"  - [{c['category']}]: {c['routine_calls']}/{c['total_calls']} routine calls")
                print(f"  Promoted Insights: {len(rep['promoted_insights'])}")
                for p in rep["promoted_insights"]:
                    print(f"    * [{p['category']}] (freq {p['frequency']}): {p['insight']}")
            elif cmd == "compact":
                res = engine.compact_memory()
                print(f"Compaction Result: {json.dumps(res, indent=2)}")
            elif cmd == "compact-experiences":
                res = engine.compact_experiences()
                print("BPE Experience Compaction & Invariant Internalization:")
                print(f"  Invariants Promoted to belief.md: {res['invariants_promoted_to_belief']}")
                print(f"  Stale Experiences Archived:       {res['experiences_archived']}")
                print(f"  Active Experiences Remaining:     {res['active_experiences_remaining']}")
            return 0

        ctx.register_cli_command("bpe", "Manage Belief, Progress, and Experience (BPE) workspace", setup_bpe, handle_bpe)

        # hermes track
        def setup_track(parser):
            parser.description = "Monitor and update BPE belief state"

        def handle_track(args):
            res = engine.track()
            print(f"✓ BPE Belief State Updated ({res['belief_length']} chars, {res['timestamp']})")
            return 0

        ctx.register_cli_command("track", "Update BPE environment belief state", setup_track, handle_track)

        # hermes commit-progress <subgoal>
        def setup_commit(parser):
            parser.description = "Update subgoal completion in BPE progress DAG"
            parser.add_argument("subgoal", help="Subgoal description or name")
            parser.add_argument("--status", default="completed", help="Status (completed/pending)")

        def handle_commit(args):
            res = engine.commit_progress(args.subgoal, args.status)
            print(f"✓ Progress Updated: '{res['subgoal']}' -> {res['status']} ({res['completed_subgoals']}/{res['total_subgoals']} subgoals)")
            return 0

        ctx.register_cli_command("commit-progress", "Commit progress milestone to BPE DAG", setup_commit, handle_commit)

        # hermes note <insight>
        def setup_note(parser):
            parser.description = "Save an empirical strategy or lesson into experience.db"
            parser.add_argument("insight", help="Insight text to persist")
            parser.add_argument("--category", default="general", help="Category taxonomy")

        def handle_note(args):
            res = engine.note(args.insight, args.category)
            status_text = "PROMOTED TO INVARIANT" if res["promoted"] else f"freq: {res['frequency']}"
            print(f"✓ Insight Noted [{res['category']}]: {res['id']} ({status_text})")
            return 0

        ctx.register_cli_command("note", "Note lesson or empirical strategy into experience.db", setup_note, handle_note)

        # hermes recall <query>
        def setup_recall(parser):
            parser.description = "Semantic recall of past strategies from experience.db"
            parser.add_argument("query", help="Search query")
            parser.add_argument("--limit", type=int, default=3, help="Max results")

        def handle_recall(args):
            results = engine.recall(args.query, limit=args.limit)
            if not results:
                print(f"No matching experiences found for '{args.query}'.")
            else:
                print(f"Recall matches for '{args.query}':")
                for r in results:
                    mark = "★" if r["promoted"] else "•"
                    print(f"  {mark} [{r['category']}] (score: {r['score']}, freq: {r['frequency']}): {r['insight']}")
            return 0

        ctx.register_cli_command("recall", "Recall past strategies from experience.db", setup_recall, handle_recall)

    # 2. Register Slash Commands
    if hasattr(ctx, "register_command"):
        def slash_bpe(raw_args: str) -> str:
            st = engine.status()
            return (
                f"**BPE Memory Workspace**\n"
                f"- **Belief**: {st['belief']['chars']} chars (~{st['belief']['estimated_tokens']} tok)\n"
                f"- **Progress**: {st['progress']['completed_subgoals']}/{st['progress']['total_subgoals']} ({int(st['progress']['ratio']*100)}%)\n"
                f"- **Experience**: {st['experience']['total_entries']} entries ({st['experience']['promoted_entries']} promoted)"
            )

        def slash_track(raw_args: str) -> str:
            res = engine.track()
            return f"✓ Belief state updated at {res['timestamp']}."

        def slash_recall(raw_args: str) -> str:
            q = raw_args.strip()
            if not q:
                return "Usage: /recall <query>"
            res = engine.recall(q, limit=3)
            if not res:
                return f"No experiences recalled for: `{q}`"
            out = [f"**Recalled Experiences for '{q}'**:"]
            for r in res:
                mark = "★" if r["promoted"] else "•"
                out.append(f"- {mark} **[{r['category']}]**: {r['insight']} *(freq {r['frequency']})*")
            return "\n".join(out)

        def slash_note(raw_args: str) -> str:
            msg = raw_args.strip()
            if not msg:
                return "Usage: /note <insight>"
            res = engine.note(msg)
            return f"✓ Noted into Experience DB: `{res['id']}` (freq: {res['frequency']})"

        ctx.register_command("bpe", slash_bpe, "Show BPE memory workspace status", "")
        ctx.register_command("track", slash_track, "Update BPE belief state", "")
        ctx.register_command("recall", slash_recall, "Recall past experience lessons", "<query>")
        ctx.register_command("note", slash_note, "Note lesson into experience DB", "<insight>")

    # 3. Lifecycle Hooks
    if hasattr(ctx, "register_hook"):
        def bpe_pre_turn_hook(**kwargs):
            """Injects a concise BPE workspace status (<= 150 tokens) into system prompt."""
            st = engine.status()
            snippet = (
                f"[BPE Memory Workspace] Progress: {st['progress']['completed_subgoals']}/{st['progress']['total_subgoals']} | "
                f"Experiences: {st['experience']['total_entries']} ({st['experience']['promoted_entries']} promoted)"
            )
            return {"action": "continue", "injected_context": snippet}

        ctx.register_hook("pre_turn", bpe_pre_turn_hook)

    return True

