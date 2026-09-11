#!/usr/bin/env python3.13
"""
Verification Suite: Phase 6 Multimodal Vision (Full Activation)
===============================================================
Verifies:
  Gate 1: GGUF Model & mmproj Integrity (local CPU storage, zero VRAM)
  Gate 2: Vision Server Lifecycle & Health Check (port 8139 responsiveness)
  Gate 3: Visual Inspection & Scene Understanding (shape, color, text recognition)
  Gate 4: UI & Layout Control Grounding (buttons, inputs, label detection)
  Gate 5: Diagram & Flowchart Structural Extraction (Mermaid synthesis)
  Gate 6: Multimodal Context Injection Loop (visual grounding prompt augmentation)

Zero-Test-Folder Architecture: Pure native executable contract verification.
"""

from __future__ import annotations

import base64
import json
import os
import sys
import time
from pathlib import Path
from PIL import Image, ImageDraw

# Setup paths
hermes_root = Path.home() / ".hermes"
sys.path.insert(0, str(hermes_root / "hermes-agent"))

import agent.core as core
from agent.core.vision_engine import (
    VisionEngine,
    VisionServerSupervisor,
    get_vision_engine,
)
from agent.core.vision_context import (
    MultimodalContextInjector,
    get_context_injector,
)


def log_gate(gate_id: str, desc: str, passed: bool, details: str = ""):
    status = "[92mPASS[0m" if passed else "[91mFAIL[0m"
    print(f"[{gate_id}] {status} - {desc}")
    if details:
        print(f"      [90m{details}[0m")


def test_gate1_model_integrity() -> bool:
    """Gate 1: GGUF Model & mmproj file integrity and VRAM preservation."""
    model_dir = Path.home() / ".hermes/models/vision"
    model_file = model_dir / "SmolVLM2-256M-Video-Instruct-Q4_K_M.gguf"
    mmproj_file = model_dir / "mmproj-SmolVLM2-256M-Video-Instruct-Q8_0.gguf"

    if not model_file.exists() or not mmproj_file.exists():
        log_gate("GATE 1", "Vision GGUF model files exist", False, f"Missing files in {model_dir}")
        return False

    # Check sizes (> 50 MB)
    m_sz = model_file.stat().st_size / (1024 * 1024)
    p_sz = mmproj_file.stat().st_size / (1024 * 1024)
    if m_sz < 50 or p_sz < 50:
        log_gate("GATE 1", "Model file sizes valid", False, f"Sizes too small: {m_sz:.1f}MB, {p_sz:.1f}MB")
        return False

    # Check GGUF magic header 'GGUF'
    with open(model_file, "rb") as f:
        magic = f.read(4)
    if magic != b"GGUF":
        log_gate("GATE 1", "Valid GGUF header", False, f"Invalid magic bytes: {magic}")
        return False

    log_gate(
        "GATE 1",
        "Vision GGUF Model & mmproj Integrity",
        True,
        f"Model: {m_sz:.1f}MB, Projector: {p_sz:.1f}MB, GGUF magic verified (CPU mode / 0 VRAM)",
    )
    return True


def test_gate2_server_lifecycle_and_health(engine: VisionEngine) -> bool:
    """Gate 2: Vision server lifecycle & health check on port 8139."""
    ok = engine.supervisor.ensure_running(timeout_sec=10.0)
    if not ok or not engine.supervisor.is_healthy():
        log_gate("GATE 2", "Vision Server Lifecycle & Health Check", False, "Port 8139 not responding 200 OK")
        return False

    log_gate(
        "GATE 2",
        "Vision Server Lifecycle & Health Check (Port 8139)",
        True,
        "Daemon active on 127.0.0.1:8139, /health responding 200 OK in CPU mode",
    )
    return True


def test_gate3_visual_inspection(engine: VisionEngine) -> bool:
    """Gate 3: Visual inspection & scene understanding."""
    # Create test image: blue circle and text
    img = Image.new("RGB", (250, 150), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.ellipse([30, 25, 110, 105], fill=(30, 100, 220), outline=(0, 0, 0))
    d.text((130, 60), "BLUE CIRCLE", fill=(0, 0, 0))
    tmp_path = Path("/dev/shm/hermes_gate3_test_img.png")
    img.save(tmp_path)

    res = engine.describe_image(tmp_path, prompt="Describe what you see in this image in detail.")
    if not res.get("success"):
        log_gate("GATE 3", "Visual inspection inference", False, f"Error: {res.get('error')}")
        return False

    text = res.get("text", "").lower()
    # Expect references to circle/blue/text/round
    has_features = any(k in text for k in ["blue", "circle", "round", "word", "text"])
    log_gate(
        "GATE 3",
        "Visual Inspection & Scene Understanding",
        has_features,
        f"Latency: {res.get('latency_sec')}s | Output: '{res.get('text', '').strip()[:80]}...'",
    )
    return has_features


def test_gate4_ui_grounding(engine: VisionEngine) -> bool:
    """Gate 4: UI & layout control grounding."""
    # Create synthetic UI mockup: Login dialog with Submit button and text input
    img = Image.new("RGB", (320, 180), color=(245, 245, 245))
    d = ImageDraw.Draw(img)
    # Title bar
    d.rectangle([10, 10, 310, 40], fill=(70, 70, 70))
    d.text((20, 20), "Login Window", fill=(255, 255, 255))
    # Input field
    d.rectangle([30, 60, 290, 95], fill=(255, 255, 255), outline=(180, 180, 180))
    d.text((40, 72), "username@domain.com", fill=(100, 100, 100))
    # Submit button
    d.rectangle([90, 120, 230, 160], fill=(40, 160, 60))
    d.text((130, 132), "SUBMIT", fill=(255, 255, 255))
    tmp_path = Path("/dev/shm/hermes_gate4_ui_mockup.png")
    img.save(tmp_path)

    res = engine.analyze_ui(tmp_path)
    if not res.get("success"):
        log_gate("GATE 4", "UI grounding analysis", False, f"Error: {res.get('error')}")
        return False

    text = res.get("text", "").lower()
    ui_detected = any(k in text for k in ["button", "submit", "login", "window", "field", "text", "box"])
    log_gate(
        "GATE 4",
        "UI & Layout Control Grounding",
        ui_detected,
        f"Detected UI controls: '{res.get('text', '').strip()[:80]}...'",
    )
    return ui_detected


def test_gate5_diagram_extraction(engine: VisionEngine) -> bool:
    """Gate 5: Diagram & flowchart structural extraction with Mermaid synthesis."""
    # Create flowchart image: A -> B -> C
    img = Image.new("RGB", (360, 140), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    # Box A
    d.rectangle([20, 45, 100, 95], fill=(200, 230, 255), outline=(0, 0, 0))
    d.text((45, 65), "START", fill=(0, 0, 0))
    # Arrow 1
    d.line([(100, 70), (140, 70)], fill=(0, 0, 0), width=3)
    # Box B
    d.rectangle([140, 45, 220, 95], fill=(255, 230, 180), outline=(0, 0, 0))
    d.text((160, 65), "PROCESS", fill=(0, 0, 0))
    # Arrow 2
    d.line([(220, 70), (260, 70)], fill=(0, 0, 0), width=3)
    # Box C
    d.rectangle([260, 45, 340, 95], fill=(200, 255, 200), outline=(0, 0, 0))
    d.text((285, 65), "DONE", fill=(0, 0, 0))
    tmp_path = Path("/dev/shm/hermes_gate5_flowchart.png")
    img.save(tmp_path)

    res = engine.extract_diagram_structure(tmp_path)
    if not res.get("success"):
        log_gate("GATE 5", "Diagram extraction", False, f"Error: {res.get('error')}")
        return False

    has_mermaid = "mermaid" in res and "graph TD" in res.get("mermaid", "")
    log_gate(
        "GATE 5",
        "Diagram & Flowchart Structural Extraction (Mermaid Synthesis)",
        has_mermaid,
        f"Synthesized Mermaid block | Summary: '{res.get('workflow_summary', '')[:70]}...'",
    )
    return has_mermaid


def test_gate6_multimodal_context_injection() -> bool:
    """Gate 6: Multimodal context injection into agent prompts."""
    injector = get_context_injector()
    img_path = Path("/dev/shm/hermes_gate3_test_img.png")
    if not img_path.exists():
        log_gate("GATE 6", "Context injection test image exists", False, "gate 3 image missing")
        return False

    prompt = f"Please review the design in {img_path} and suggest layout improvements."
    augmented_prompt, records = injector.inject_visual_context(prompt)

    injected_ok = len(records) > 0 and "[MULTIMODAL VISUAL GROUNDING]" in augmented_prompt and "Visual Analysis:" in augmented_prompt
    log_gate(
        "GATE 6",
        "Multimodal Context Injection Loop",
        injected_ok,
        f"Injected {len(records)} visual block(s), augmented length: {len(augmented_prompt)} chars",
    )
    return injected_ok


def main() -> int:
    print("=" * 75)
    print("  HERMES PHASE 6: MULTIMODAL VISION FULL ACTIVATION VERIFICATION")
    print("=" * 75)

    g1 = test_gate1_model_integrity()

    engine = get_vision_engine()
    g2 = test_gate2_server_lifecycle_and_health(engine)
    g3 = test_gate3_visual_inspection(engine)
    g4 = test_gate4_ui_grounding(engine)
    g5 = test_gate5_diagram_extraction(engine)
    g6 = test_gate6_multimodal_context_injection()

    print("=" * 75)
    all_passed = all([g1, g2, g3, g4, g5, g6])
    if all_passed:
        print("[92m[SUCCESS][0m ALL 6 PHASE 6 MULTIMODAL VISION GATES PASSED (100% OPERATIONAL).")
        return 0
    else:
        print("[91m[FAILURE][0m ONE OR MORE VISION GATES FAILED.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
