# Hermes OS Core Invariants (L0 Pinned)
- §1 Hardware: Port 8138 Gemma-4-E4B (-np 1, <= 4,812 MiB VRAM). Port 8139 Vision & Port 1933 OpenViking 100% CPU RAM.
- §2 Entry: Native hermes CLI & profiles only. Zero synthetic wrappers in .local/bin/.
- §3 Home: .hermes/ is the sole runtime state directory, synced via Chezmoi.
- §4 Verification: Non-vacuous pytest -q (N >= 1) + /tmp/hermes_verified_receipt.json.
- §5 Overflow: Dynamic session lessons live in EXPERIENCE.md and OpenViking Port 1933.
