"""
Adversarial Security & Containment Test Suite (Roadmap 6 - M1 & M7)
===================================================================
Tries to break agent capability fencing, tamper with transcript integrity hashes,
inject illegal port access, access protected credentials, and forge audit logs.
"""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
BIN_DIR = ROOT / ".hermes/bin"
POLICY_FILE = ROOT / ".hermes/policy/agent_capabilities.yaml"


class TestSecurityFencingAndIntegrity:

    def test_tampered_transcript_detection(self):
        """Adversarial Goal: Modify a single byte in a transcript turn and ensure verify_transcript FAILS."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            transcript_file = tmp / "session_eval.jsonl"
            sidecar_file = tmp / "session_eval.jsonl.integrity"

            # Create legitimate 3-turn transcript
            turns = [
                {"role": "user", "content": "Write an async ringbuffer"},
                {"role": "assistant", "content": "Here is the code: class RingBuffer..."},
                {"role": "tool", "content": "Tests passed: 5/5"}
            ]
            with open(transcript_file, "w") as f:
                for t in turns:
                    f.write(json.dumps(t) + "\n")

            # Generate legitimate integrity sidecar
            with open(transcript_file, "r") as tf, open(sidecar_file, "w") as sf:
                for idx, line in enumerate(tf):
                    h = hashlib.sha256(line.strip().encode("utf-8")).hexdigest()
                    sf.write(f"{idx}:{h}\n")

            # Verify legitimate transcript passes
            res = subprocess.run(
                ["python3.13", str(BIN_DIR / "verify_transcript.py"), str(transcript_file)],
                capture_output=True, text=True
            )
            assert res.returncode == 0, f"Legitimate transcript failed: {res.stderr}"

            # ADVERSARIAL MUTATION: Cover tracks / tamper with Turn 1
            turns_tampered = [
                {"role": "user", "content": "Write an async ringbuffer"},
                {"role": "assistant", "content": "TAMPERED: Erased malicious action trace"},
                {"role": "tool", "content": "Tests passed: 5/5"}
            ]
            with open(transcript_file, "w") as f:
                for t in turns_tampered:
                    f.write(json.dumps(t) + "\n")

            # Test must catch the tampering and exit with code 1
            res_tampered = subprocess.run(
                ["python3.13", str(BIN_DIR / "verify_transcript.py"), str(transcript_file)],
                capture_output=True, text=True
            )
            assert res_tampered.returncode == 1, "SECURITY BREACH: Tampered transcript was NOT detected!"
            assert "TAMPER ALERT" in res_tampered.stdout or "TAMPER ALERT" in res_tampered.stderr

    def test_omitted_turn_detection(self):
        """Adversarial Goal: Delete a turn from the middle of the transcript to conceal an action."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            transcript_file = tmp / "session_prune.jsonl"
            sidecar_file = tmp / "session_prune.jsonl.integrity"

            # Create 4 turns
            turns = [{"turn": i, "content": f"action {i}"} for i in range(4)]
            with open(transcript_file, "w") as f:
                for t in turns:
                    f.write(json.dumps(t) + "\n")

            # Generate sidecar
            with open(transcript_file, "r") as tf, open(sidecar_file, "w") as sf:
                for idx, line in enumerate(tf):
                    h = hashlib.sha256(line.strip().encode("utf-8")).hexdigest()
                    sf.write(f"{idx}:{h}\n")

            # ADVERSARIAL MUTATION: Delete turn 2 (leaving turns 0, 1, 3 shifted to 0, 1, 2)
            del turns[2]
            with open(transcript_file, "w") as f:
                for t in turns:
                    f.write(json.dumps(t) + "\n")

            res = subprocess.run(
                ["python3.13", str(BIN_DIR / "verify_transcript.py"), str(transcript_file)],
                capture_output=True, text=True
            )
            assert res.returncode == 1, "SECURITY BREACH: Omitted turn was not flagged as hash mismatch!"

    def test_policy_yaml_structure_and_invariants(self):
        """Verifies that the capability policy denies dangerous ports, sets credential masks, and protects files."""
        assert POLICY_FILE.exists(), f"Missing policy file: {POLICY_FILE}"
        policy = yaml.safe_load(POLICY_FILE.read_text(encoding="utf-8"))

        # Invariant 1: SSH (22) and DB ports must be explicitly forbidden
        deny_ports = policy.get("network", {}).get("deny_ports", [])
        assert 22 in deny_ports, "Policy flaw: SSH port 22 not in deny_ports"
        assert 3306 in deny_ports, "Policy flaw: MySQL port 3306 not in deny_ports"

        # Invariant 2: Integrity files and git credentials must be in deny_write_paths
        deny_writes = policy.get("filesystem", {}).get("deny_write_paths", [])
        assert any(".integrity" in p for p in deny_writes), "Policy flaw: .integrity not protected from writing"
        assert any(".git-credentials" in p for p in deny_writes), "Policy flaw: .git-credentials not protected"

        # Invariant 3: Credential masking patterns must exist
        masks = policy.get("credentials", {}).get("mask_patterns", [])
        assert len(masks) >= 3, f"Insufficient credential masks in policy: {masks}"
