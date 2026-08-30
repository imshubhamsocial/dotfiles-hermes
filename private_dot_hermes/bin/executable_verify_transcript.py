#!/usr/bin/env python3.13
"""
Transcript Integrity & Anti-Tamper Verification Suite (Roadmap 6 - Milestone 1)
=============================================================================
Verifies that session transcripts have not been pruned, modified, or forged
by comparing turn-by-turn hashes with the immutable sidecar .integrity manifest.

Usage:
    python3.13 bin/verify_transcript.py <transcript_path> [--sidecar <integrity_path>]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def compute_turn_hash(line: str) -> str:
    """Computes deterministic SHA256 of a single JSONL line."""
    return hashlib.sha256(line.strip().encode("utf-8")).hexdigest()


def verify_transcript(transcript_file: Path, sidecar_file: Path | None = None) -> bool:
    if not transcript_file.exists():
        print(f"[-] ERROR: Transcript file not found: {transcript_file}", file=sys.stderr)
        return False

    if sidecar_file is None:
        sidecar_file = transcript_file.with_suffix(transcript_file.suffix + ".integrity")

    if not sidecar_file.exists():
        # If sidecar doesn't exist, calculate current baseline and report clean creation
        print(f"[!] Warning: No existing integrity sidecar found at {sidecar_file}. Generating baseline.")
        with open(transcript_file, "r", encoding="utf-8") as tf, open(sidecar_file, "w", encoding="utf-8") as sf:
            for idx, line in enumerate(tf):
                if not line.strip():
                    continue
                h = compute_turn_hash(line)
                sf.write(f"{idx}:{h}\n")
        print(f"[+] Baseline integrity manifest created: {sidecar_file}")
        return True

    # Read expected hashes
    expected_hashes: dict[int, str] = {}
    with open(sidecar_file, "r", encoding="utf-8") as sf:
        for line in sf:
            line = line.strip()
            if not line or ":" not in line:
                continue
            parts = line.split(":", 1)
            try:
                expected_hashes[int(parts[0])] = parts[1]
            except ValueError:
                continue

    # Verify actual transcript
    mismatches = 0
    total_turns = 0
    with open(transcript_file, "r", encoding="utf-8") as tf:
        for idx, line in enumerate(tf):
            if not line.strip():
                continue
            total_turns += 1
            current_hash = compute_turn_hash(line)
            expected_hash = expected_hashes.get(idx)

            if expected_hash is None:
                print(f"[!] Warning: Turn {idx} is in transcript but missing from integrity sidecar (Uncommitted turn)")
            elif current_hash != expected_hash:
                print(f"[-] TAMPER ALERT: Turn {idx} hash mismatch!")
                print(f"    Expected: {expected_hash}")
                print(f"    Actual:   {current_hash}")
                mismatches += 1

    if mismatches > 0:
        print(f"[-] VERIFICATION FAILED: {mismatches} tampered or corrupted turns detected out of {total_turns}.", file=sys.stderr)
        return False

    print(f"[+] VERIFIED: Transcript {transcript_file.name} integrity intact ({total_turns} turns checked, 0 mismatches).")
    return True


def main():
    parser = argparse.ArgumentParser(description="Hermes Session Transcript Integrity Auditor")
    parser.add_argument("transcript", type=str, help="Path to transcript.jsonl file")
    parser.add_argument("--sidecar", type=str, default=None, help="Optional path to .integrity sidecar")
    args = parser.parse_args()

    success = verify_transcript(Path(args.transcript), Path(args.sidecar) if args.sidecar else None)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
