# Layer 3 Factory Rule: Hardware & 128K VRAM Invariants (hardware_vram_invariants.md)

> Layer 3 Reference Contract: Physical Hardware Boundaries & Verification Gates.
> Rule: File must remain strictly under 200 lines.

---

## 1. Dedicated Physical GPU Envelope

* **GPU**: NVIDIA GeForce RTX 3050 Laptop GPU (6,144 MiB physical GDDR6).
* **Display Isolation (Disp.A: Off)**: Wayland compositor (`kwin_wayland`) runs on the integrated AMD Radeon GPU, using only 6 MiB on the NVIDIA card. Full 6,138 MiB is dedicated to compute.
* **Hard NVML Ceiling**: Active GPU VRAM must never exceed **5,800.0 MiB** (`nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits`), guaranteeing >= 344 MiB physical safety margin.

---

## 2. Canonical 128K Engine & KV Cache Invariant (Port 8138)

* **Context Window**: `-c 131072` (`context_length: 131072`), satisfying upstream `MINIMUM_CONTEXT_LENGTH = 64000` (`agent/model_metadata.py`) and optimal `ContextCompressor` thresholds.
* **KV Cache Quantization**: Google TurboQuant 4-bit KV cache (`-ctk q4_0 -ctv q4_0 -fa 1`), keeping the 128K KV buffer at ~1,075 MiB.
* **CPU & Swap Isolation**: Port 8138 inference pinned to cores 0–5 (`taskset -c 0-5 -t 6 -tb 6`); cores 6–11 reserved for host OS, Port 8139 CPU embeddings, and Port 1933 OpenViking; backed by 15.3 GiB zram + 2,048 MiB btrfs NOCOW swapfile (`/var/swap/swapfile`).

---

## 3. Candidate Model Footprint Envelopes (at -c 131072 -ctk q4_0 -ctv q4_0)

* **Baseline (`google/gemma-4-E4B-it-qat` + MTP)**: 5,201–5,239 MiB measured active (905 MiB free).
* **Tier 1A (`xbill9/gemma-4-E4B-it-qat-exact` + Assistant)**: 5,128 MiB projected active (1,016 MiB free).
* **Tier 1B (`unsloth/nemotron-3.5-bolt-e4b` + DFlash)**: 5,554 MiB projected active (590 MiB free).

---

## 4. Live NVML Verification Gate

Any execution stage mutating or testing models must verify live VRAM using:
```bash
VRAM_USED=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -n1 | tr -d ' ')
test "$VRAM_USED" -le 5800
```
If VRAM exceeds 5,800.0 MiB, halt execution immediately.
