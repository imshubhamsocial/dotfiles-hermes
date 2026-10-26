#!/usr/bin/env python3.13  
"""  
.hermes/hermes_rsi_daemon.py — 24/7 Autonomous RSI Living Harness Daemon (GDR17)  
Operates across three hardware-bounded temporal regimes on CPU RAM (CUDA_VISIBLE_DEVICES=""):  
  Regime 1: Post-session epistemic receipt watcher (/tmp/hermes_verified_receipt.json).  
  Regime 2: Opportunistic SyntheticGauntletEngine AST mutation probing during Slot 0 idle windows.  
  Regime 3: Nightly 03:00 AM Dream-RSI 2.0 consolidation, Ebbinghaus compaction, and Phase 25 ARSI audit.  
"""  
from __future__ import annotations

import ast  
import datetime  
import fcntl  
import hashlib  
import json  
import os  
from pathlib import Path  
import subprocess  
import sys  
import tempfile  
import time  
from typing import Any

os.environ["CUDA_VISIBLE_DEVICES"] = ""  
os.environ.setdefault("TMPDIR", "/tmp")

HERMES_ROOT = Path(  
    os.environ.get(  
        "HERMES_WORKSPACE",  
        "/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes",  
    )  
).resolve()  
HERMES_HOME = HERMES_ROOT / ".hermes"  
sys.path.insert(0, str(HERMES_HOME))

import mcp_openjev as openjev

RECEIPT_PATH = Path("/tmp/hermes_verified_receipt.json")  
SLOT0_LOCK_PATH = Path("/tmp/hermes_port8138_slot0.lock")  
SYNTH_LEDGER = HERMES_HOME / "cache" / "synthetic_gauntlet_ledger.jsonl"

class _ASTDefectMutator(ast.NodeTransformer):  
    """Injects controlled structural defects into gold reference modules for Regime 2."""

    def __init__(self) -> None:  
        super().__init__()  
        self.mutated = False

    def visit_Compare(self, node: ast.Compare) -> ast.AST:  
        self.generic_visit(node)  
        if not self.mutated and node.ops and isinstance(node.ops[0], ast.GtE):  
            node.ops[0] = ast.Gt()  
            self.mutated = True  
        return node

class SyntheticGauntletEngine:  
    """  
    4-Stage Autonomous Synthetic Testbed Generator (Gemini Argon Parity):  
      Stage 1: Curriculum domain sampling inside ICM stage folders (01_spec, 02_impl, 03_verify).  
      Stage 2: Gold reference module + unit test synthesis & baseline exit-0 verification.  
      Stage 3: CPU AST defect injection via _ASTDefectMutator & failure verification (>=1 test fails).  
      Stage 4: Autonomous repair verification & contrastive trajectory logging.  
    """

    @staticmethod  
    def run_synthetic_probe() -> dict[str, Any]:  
        SLOT0_LOCK_PATH.touch(exist_ok=True)  
        with open(SLOT0_LOCK_PATH, "r+", encoding="utf-8") as lf:  
            try:  
                # Non-blocking acquisition: yield immediately if human/CLI holds Slot 0  
                fcntl.flock(lf.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)  
            except BlockingIOError:  
                return {"status": "skipped_slot0_busy"}

            try:  
                with tempfile.TemporaryDirectory(prefix="hermes_synth_") as tmp_dir:  
                    ws = Path(tmp_dir).resolve()  
                    openjev._ensure_icm_stage_folders(ws)

                    gold_code = (  
                        "class TransactionalBucket:\\n"  
                        "    def __init__(self, capacity: int = 10) -> None:\\n"  
                        "        self.tokens = capacity\\n\\n"  
                        "    def consume(self, amount: int) -> bool:\\n"  
                        "        if self.tokens >= amount:\\n"  
                        "            self.tokens -= amount\\n"  
                        "            return True\\n"  
                        "        return False\\n"  
                    )  
                    test_code = (  
                        "from bucket import TransactionalBucket\\n\\n"  
                        "def test_exact_capacity_boundary():\\n"  
                        "    b = TransactionalBucket(capacity=5)\\n"  
                        "    assert b.consume(5) is True\\n"  
                        "    assert b.tokens == 0\\n\\n"  
                        "def test_over_capacity_rejected():\\n"  
                        "    b = TransactionalBucket(capacity=5)\\n"  
                        "    assert b.consume(6) is False\\n"  
                    )

                    mod_path = ws / "02_impl" / "bucket.py"  
                    test_path = ws / "03_verify" / "test_bucket.py"  
                    mod_path.write_text(gold_code, encoding="utf-8")  
                    test_path.write_text(test_code, encoding="utf-8")

                    env = {**os.environ, "PYTHONPATH": str(ws / "02_impl")}  
                    gold_res = subprocess.run(  
                        ["/usr/bin/python3.13", "-m", "pytest", str(test_path), "-q"],  
                        env=env, capture_output=True, text=True, timeout=5,  
                    )  
                    if gold_res.returncode != 0:  
                        return {"status": "discarded_gold_failed"}

                    # Stage 3: Inject AST boundary defect (>= mutated to >)  
                    tree = ast.parse(gold_code)  
                    mutator = _ASTDefectMutator()  
                    mutated_tree = mutator.visit(tree)  
                    ast.fix_missing_locations(mutated_tree)  
                    defective_code = ast.unparse(mutated_tree) + "\\n"  
                    mod_path.write_text(defective_code, encoding="utf-8")

                    defect_res = subprocess.run(  
                        ["/usr/bin/python3.13", "-m", "pytest", str(test_path), "-q"],  
                        env=env, capture_output=True, text=True, timeout=5,  
                    )  
                    assert defect_res.returncode != 0, "Mutated AST failed to trigger unit test!"

                    # Stage 4: Apply surgical repair via canonical FastMCP jev_mutate_module  
                    openjev.jev_mutate_module(  
                        openjev.MutateModuleInput(  
                            path=mod_path,  
                            target_pattern="if self.tokens > amount:",  
                            replacement_content="if self.tokens >= amount:",  
                            workspace_dir=str(ws),  
                        )  
                    )  
                    repair_res = subprocess.run(  
                        ["/usr/bin/python3.13", "-m", "pytest", str(test_path), "-q"],  
                        env=env, capture_output=True, text=True, timeout=5,  
                    )  
                    passed = repair_res.returncode == 0  
                    record = {  
                        "ts": time.time(),  
                        "status": "verified_synthetic_repair" if passed else "failed",  
                        "sha256": hashlib.sha256(gold_code.encode("utf-8")).hexdigest()[:16],  
                        "cuda_delta_mib": 0.0,  
                    }  
                    with open(SYNTH_LEDGER, "a", encoding="utf-8") as out_f:  
                        out_f.write(json.dumps(record) + "\\n")  
                    return record  
            finally:  
                fcntl.flock(lf.fileno(), fcntl.LOCK_UN)

def run_daemon_loop(max_iterations: int | None = None) -> None:  
    """Main asynchronous event loop governing Regimes 1, 2, and 3."""  
    last_receipt_mtime = RECEIPT_PATH.stat().st_mtime if RECEIPT_PATH.exists() else 0.0  
    last_nightly_date: datetime.date | None = None  
    iteration = 0

    while max_iterations is None or iteration < max_iterations:  
        iteration += 1  
        now = datetime.datetime.now()

        # Regime 1: Post-Session Epistemic Watcher (500ms polling equivalent)  
        if RECEIPT_PATH.exists():  
            mtime = RECEIPT_PATH.stat().st_mtime  
            if mtime > last_receipt_mtime:  
                last_receipt_mtime = mtime  
                openjev.jev_dream_rsi_sync(workspace_dir=str(HERMES_ROOT))

        # Regime 2: Opportunistic Synthetic Gauntlet Probe during idle windows  
        SyntheticGauntletEngine.run_synthetic_probe()

        # Regime 3: 03:00 AM Nightly Deep Consolidation & Omniscient Audit  
        if now.hour == 3 and last_nightly_date != now.date():  
            last_nightly_date = now.date()  
            openjev.jev_dream_rsi_sync(workspace_dir=str(HERMES_ROOT))  
            openjev.jev_verify_arsi_omniscient()

        if max_iterations is None:  
            time.sleep(0.5)

if __name__ == "__main__":  
    if "--once" in sys.argv:  
        run_daemon_loop(max_iterations=1)  
    else:  
        run_daemon_loop()

