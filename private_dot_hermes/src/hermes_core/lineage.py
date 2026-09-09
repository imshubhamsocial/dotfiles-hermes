"""
U17 AVO Lineage Search & Supervisory Recovery Engine (Phase 4.3)
=================================================================
NVIDIA AVO pattern (roadmap §4.3): long-horizon agents get trapped in
local minima — repeatedly tweaking the same broken candidate instead of
branching from a high-fitness ancestor.

Two components:

  1. Agentic Variation Operators loop:
     - `LineageTree`: evolutionary tree of candidate versions built from
       the U6 trajectory dialect. `select_branch_point()` returns the
       highest-fitness known-good ancestor so the agent can explicitly
       branch from it instead of the immediate previous turn.
     - Tree persists to RAMDisk (`/dev/shm/hermes_lineage/`) per the
       Btrfs zero-wear law; canonical name `.hermes/lineage_tree.json`
       is reserved for milestone flushes.

  2. Out-of-Band Supervisor (`OutOfBandSupervisor` / `supervisory_scan`):
     deterministic offline monitor over rolling windows of MUTATING tool
     attempts:
       - STALL          : full window with 0% successes -> ROLLBACK_TO_ANCESTOR
       - FIXATION       : >=3 consecutive failures on the SAME target file
                          -> SWITCH_OPERATOR + ancestor branch swap
       - PRUNE          : >prune_limit consecutive failures after a good node
                          -> PRUNE_BRANCH

All verdicts are derived deterministically from recorded events — no LLM
self-grading.
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    from .trajectory import load_events, verify_chain
except ImportError:  # packageless loaders (integrity probes)
    from hermes_core.trajectory import load_events, verify_chain

RAMDISK_DIR = Path("/dev/shm/hermes_lineage")
CANONICAL_RELATIVE = Path(".hermes") / "lineage_tree.json"
MUTATING_TOOLS = ("write_file", "patch_file")

STALL_WINDOW = 5
FIXATION_LIMIT = 3
PRUNE_LIMIT = 6


# ─── Lineage tree ────────────────────────────────────────────────────────────

@dataclass
class LineageNode:
    node_id: int
    parent_id: Optional[int]
    seq: int
    turn: Any
    role: str
    tool: str
    filepath: str
    result_ok: bool
    fitness: float
    children: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = vars(self).copy()
        return d


def _target_filepath(args_head: str) -> str:
    try:
        args = json.loads(args_head) if args_head else {}
        return str(args.get("filepath", "")) if isinstance(args, dict) else ""
    except json.JSONDecodeError:
        return ""


def build_lineage_tree(events: List[Dict[str, Any]]) -> List[LineageNode]:
    """Derive candidate nodes from mutating attempts in stream order.
    Call metadata (role, args_head) lives on the paired tool_call event."""
    nodes: List[LineageNode] = []
    last_any: Optional[LineageNode] = None
    pending_calls: Dict[tuple, Dict[str, Any]] = {}
    for ev in events:
        etype = ev.get("event")
        key = (ev.get("turn"), ev.get("tool"))
        if etype == "tool_call":
            pending_calls[key] = ev
            continue
        if etype != "tool_result" or ev.get("tool") not in MUTATING_TOOLS:
            continue
        call_ev = pending_calls.pop(key, {})
        ok = bool(ev.get("result_ok"))
        node = LineageNode(
            node_id=len(nodes),
            parent_id=(last_any.node_id if last_any else None),
            seq=ev.get("seq"), turn=ev.get("turn"),
            role=call_ev.get("role", ev.get("role", "")),
            tool=ev.get("tool", ""),
            filepath=_target_filepath(call_ev.get("args_head", "")),
            result_ok=ok, fitness=1.0 if ok else 0.0,
        )
        if last_any is not None:
            last_any.children.append(node.node_id)
        nodes.append(node)
        last_any = node
    return nodes


def select_branch_point(nodes: List[LineageNode],
                         exclude_node_ids: Optional[set] = None) -> Optional[LineageNode]:
    """Highest-fitness ancestor, latest on ties (most recent known-good).
    Banned subtrees (excluded ids and their descendants) are skipped."""
    banned = set(exclude_node_ids or set())

    def in_banned_subtree(node: LineageNode) -> bool:
        cur = node
        while cur is not None:
            if cur.node_id in banned:
                return True
            cur = nodes[cur.parent_id] if cur.parent_id is not None else None
        return False

    best = None
    for n in nodes:
        if n.fitness <= 0 or in_banned_subtree(n):
            continue
        if best is None or (n.fitness, n.seq) >= (best.fitness, best.seq):
            best = n
    return best


def save_tree(nodes: List[LineageNode], path: Optional[Path] = None) -> Path:
    target = Path(path) if path else RAMDISK_DIR / "lineage_tree.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "nodes": [n.to_dict() for n in nodes],
        "best_branch_point": (select_branch_point(nodes).node_id
                              if select_branch_point(nodes) else None),
    }
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return target


def load_tree(path: Path) -> List[LineageNode]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return [LineageNode(**n) for n in payload["nodes"]]


# ─── Out-of-Band Supervisor ──────────────────────────────────────────────────

@dataclass
class Intervention:
    kind: str                 # ROLLBACK_TO_ANCESTOR | SWITCH_OPERATOR | PRUNE_BRANCH | CLARIFY_OR_HALT
    at_seq: Optional[int]
    reason: str
    branch_to_node: Optional[int] = None
    detail: str = ""
    clarification_questions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return vars(self)


def supervisory_scan(
    trajectory_path: Union[str, Path],
    detector: Optional[Any] = None,
) -> List[Intervention]:
    """Deterministic out-of-band scan of a full U6 trajectory stream with Cactus Hybrid Uncertainty."""
    src = Path(trajectory_path)
    ok_chain, chain_detail = verify_chain(src)
    if not ok_chain:
        raise ValueError(f"refusing supervisory scan: {chain_detail}")

    # Graceful loader for CactusHybridDetector
    if detector is None:
        try:
            from .cactus import CactusHybridDetector
            detector = CactusHybridDetector()
        except ImportError:
            try:
                from hermes_core.cactus import CactusHybridDetector
                detector = CactusHybridDetector()
            except ImportError:
                detector = None

    events = load_events(src)
    attempts: List[Dict[str, Any]] = [
        ev for ev in events
        if ev.get("event") == "tool_result" and ev.get("tool") in MUTATING_TOOLS
    ]
    interventions: List[Intervention] = []
    if not attempts:
        return interventions

    tree = build_lineage_tree(events)
    args_head_by_key = {
        (ev.get("turn"), ev.get("tool")): ev.get("args_head", "")
        for ev in events if ev.get("event") == "tool_call"
    }

    # Rolling window stall detection.
    window: List[Dict[str, Any]] = []
    fixation_file: Optional[str] = None
    fixation_run = 0
    consec_fail_since_good = 0

    for ev in attempts:
        ok = bool(ev.get("result_ok"))
        fp = _target_filepath(
            args_head_by_key.get((ev.get("turn"), ev.get("tool")), ""))
        window.append(ev)
        if len(window) > STALL_WINDOW:
            window.pop(0)

        # Fixation trap: same-file failure streak.
        if not ok and fp and fp == fixation_file:
            fixation_run += 1
        else:
            fixation_file = fp if not ok else None
            fixation_run = 1 if (not ok and fp) else 0
        if fixation_run >= FIXATION_LIMIT:
            bp = select_branch_point(tree, exclude_node_ids={
                n.node_id for n in tree if not n.result_ok})
            interventions.append(Intervention(
                kind="SWITCH_OPERATOR", at_seq=ev.get("seq"),
                reason=f"{fixation_run} consecutive failed mutations on '{fp}' "
                       f"(local-minimum fixation)",
                branch_to_node=(bp.node_id if bp else None),
                detail="alternate variation operator suggested "
                       "(write_file <-> patch_file) from high-fitness ancestor",
            ))
            fixation_run = 0  # one intervention per fixation episode

        # Consecutive-failure counters.
        if ok:
            consec_fail = 0
            consec_fail_since_good = 0
        else:
            consec_fail += 1
            consec_fail_since_good += 1

        # Cactus Hybrid Uncertainty Scan (Phase 4.1)
        if detector is not None:
            explicit_unc = ev.get("uncertainty_score")
            call_ev_obj = next(
                (c for c in events if c.get("event") == "tool_call"
                 and c.get("turn") == ev.get("turn")
                 and c.get("tool") == ev.get("tool")),
                {}
            )
            if explicit_unc is None:
                explicit_unc = call_ev_obj.get("uncertainty_score")

            thought_text = (
                call_ev_obj.get("thought")
                or call_ev_obj.get("rationale")
                or ev.get("thought")
                or ""
            )
            args_raw = args_head_by_key.get((ev.get("turn"), ev.get("tool")), "")
            try:
                args_dict = json.loads(args_raw) if args_raw else {}
            except Exception:
                args_dict = {"filepath": fp}

            conf_val = None
            if explicit_unc is not None and isinstance(explicit_unc, (int, float)):
                conf_val = 1.0 - float(explicit_unc)

            unc_eval = detector.evaluate_action(
                tool=ev.get("tool", ""),
                args=args_dict,
                thought=thought_text,
                verbalized_confidence=conf_val,
                consecutive_failures=consec_fail_since_good,
            )

            if unc_eval.is_uncertain and unc_eval.is_destructive:
                bp = select_branch_point(
                    tree,
                    exclude_node_ids={n.node_id for n in tree if not n.result_ok},
                )
                interventions.append(Intervention(
                    kind="CLARIFY_OR_HALT",
                    at_seq=ev.get("seq"),
                    reason=(
                        f"Cactus hybrid uncertainty detected ({unc_eval.score:.2f} >= "
                        f"{detector.uncertainty_threshold}) before mutating '{fp}'"
                    ),
                    branch_to_node=(bp.node_id if bp else None),
                    detail=f"Autonomous halt: {unc_eval.recommendation}",
                    clarification_questions=unc_eval.clarification_questions,
                ))

        # Full-window zero-progress stall.
        if len(window) == STALL_WINDOW and all(
                not a.get("result_ok") for a in window):
            bp = select_branch_point(tree, exclude_node_ids={
                n.node_id for n in tree if not n.result_ok})
            interventions.append(Intervention(
                kind="ROLLBACK_TO_ANCESTOR", at_seq=ev.get("seq"),
                reason=f"{STALL_WINDOW}-window with 0% mutating success",
                branch_to_node=(bp.node_id if bp else None),
                detail=f"stall window@{ev.get('seq')}",
            ))
            window.clear()  # re-arm after intervention

        # Deep prune after prolonged divergence.
        if consec_fail_since_good > PRUNE_LIMIT and not any(
                i.kind == "PRUNE_BRANCH" and i.at_seq == ev.get("seq")
                for i in interventions):
            interventions.append(Intervention(
                kind="PRUNE_BRANCH", at_seq=ev.get("seq"),
                reason=f"{consec_fail_since_good} consecutive failures since "
                       f"last good candidate",
                detail="abandon active subtree; restart from lineage root",
            ))

    return interventions
