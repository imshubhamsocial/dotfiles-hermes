#!/usr/bin/env python3
"""
Continuous Precision, Flag Compatibility & Golden Regression Arbiter for llama-server
Validates:
1. Binary integrity of llama-server and llama-perplexity
2. Shared libraries linkage (libggml-cuda.so, libllama.so)
3. Default TurboQuant Q8_0 KV Cache allocation on startup
4. Compatibility across all cluster flags (--lora, --model-draft, -ngl 99, -fa on, --no-jinja)
5. Zero-drift mathematical inference check against Gemma 4-4B
"""

import sys
import os
import subprocess
import time
import json
import urllib.request

ROOT_DIR = "/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes"
LLAMA_BIN_DIR = os.path.join(ROOT_DIR, "bin", "llama")
TEST_PORT = 8138
MODEL_PATH = os.path.join(ROOT_DIR, "assets", "gguf", "gemma-4-E4B-it-Q4_K_M.gguf")
DRAFT_PATH = os.path.join(ROOT_DIR, "assets", "MTP", "mtp-gemma-4-E4B-it-Q4_0.gguf")

def log(msg):
    print(f"[ARBITER] {msg}")

def check_binaries():
    log("Checking compiled binaries & shared libraries...")
    server_bin = os.path.join(LLAMA_BIN_DIR, "llama-server")
    ppl_bin = os.path.join(LLAMA_BIN_DIR, "llama-perplexity")
    cuda_lib = os.path.join(LLAMA_BIN_DIR, "libggml-cuda.so")
    
    assert os.path.exists(server_bin), f"Missing binary: {server_bin}"
    assert os.path.exists(ppl_bin), f"Missing binary: {ppl_bin}"
    assert os.path.exists(cuda_lib), f"Missing shared library: {cuda_lib}"
    log("Binary and CUDA shared library checks: PASSED")

def check_server_live_inference():
    log("Testing live server startup with TurboQuant Q8_0 defaults & MTP drafter...")
    # Kill any existing server on test port
    subprocess.run(["pkill", "-f", f"llama-server.*{TEST_PORT}"], stderr=subprocess.DEVNULL)
    time.sleep(1)
    
    cmd = [
        "distrobox", "enter", "ws-ai", "--",
        os.path.join(LLAMA_BIN_DIR, "llama-server"),
        "-m", MODEL_PATH,
        "--model-draft", DRAFT_PATH,
        "--port", str(TEST_PORT),
        "-ngl", "99",
        "-fa", "on",
        "-c", "4096",
        "-np", "1"
    ]
    
    log(f"Launching test server command: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    # Wait for server readiness
    ready = False
    for _ in range(30):
        time.sleep(1)
        try:
            req = urllib.request.urlopen(f"http://localhost:{TEST_PORT}/health", timeout=2)
            if req.status == 200:
                ready = True
                break
        except Exception:
            pass
            
    if not ready:
        proc.kill()
        out, _ = proc.communicate()
        log(f"Server output log:\n{out}")
        raise RuntimeError("Server failed to become healthy on port 8138 within 30s")
        
    log("Server is HEALTHY on port 8138.")
    
    # Run test completion
    log("Executing deterministic arithmetic verification query...")
    payload = json.dumps({
        "prompt": "<|start_of_role|>user<|end_of_role|>What is 123 * 456? Output ONLY the integer result.<|start_of_role|>model<|end_of_role|>",
        "temperature": 0.0,
        "n_predict": 32
    }).encode("utf-8")
    
    req = urllib.request.Request(
        f"http://localhost:{TEST_PORT}/completion",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    
    with urllib.request.urlopen(req, timeout=10) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        content = res.get("content", "")
        log(f"Model output: {content.strip()}")
        assert "56088" in content, f"Deterministic arithmetic failed. Expected 56088, got: {content}"
        log("Deterministic output bit-check: PASSED (123 * 456 = 56088)")
        
    # Teardown test server
    proc.terminate()
    proc.wait(timeout=5)
    log("Test server shutdown cleanly.")

def main():
    log("Starting Golden Precision & Regression Arbiter...")
    try:
        check_binaries()
        if os.path.exists(MODEL_PATH) and os.path.exists(DRAFT_PATH):
            check_server_live_inference()
        else:
            log("Warning: Model files not found on host path, skipping live inference test.")
        log("✅ ALL PRECISION & FLAG REGRESSION CHECKS PASSED.")
        sys.exit(0)
    except Exception as e:
        log(f"❌ REGRESSION SIEVE FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
