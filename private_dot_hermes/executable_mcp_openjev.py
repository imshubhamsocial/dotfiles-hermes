#!/usr/bin/env python3
"""OpenJev Decision Gate MCP Server.

Provides sub-50ms deterministic hypothesis discrimination via direct logprob
scoring against local llama-server on Port 8138.
"""

import json
import math
import urllib.request

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("openjev")

LLM_ENDPOINT = "http://127.0.0.1:8138/v1/completions"

@mcp.tool()
def jev_decide(
    premise: str,
    hypothesis_a: str,
    hypothesis_b: str,
    focus_uri: str = ""
) -> dict:
    """Evaluate two competing hypotheses against a premise using sub-50ms logprob scoring.
    
    Args:
        premise: The factual context or test execution result.
        hypothesis_a: Candidate hypothesis A.
        hypothesis_b: Candidate hypothesis B.
        focus_uri: Optional active <focus> file URI or symbol scope for boundary verification.
        
    Returns:
        dict: Containing 'decision' ('A' or 'B'), 'prob' (calibrated float 0.0-1.0), 'winner', and 'focus_scoped'.
    """
    prompt = (
        f"<start_of_turn>user\n"
        f"Given the premise:\n{premise}\n\n"
        f"Which hypothesis is true?\n"
        f"A: {hypothesis_a}\n"
        f"B: {hypothesis_b}\n\n"
        f"Answer with just the letter A or B.<end_of_turn>\n"
        f"<start_of_turn>model\n"
    )
    
    payload = {
        "prompt": prompt,
        "max_tokens": 1,
        "temperature": 0.0,
        "logprobs": 5
    }
    
    req = urllib.request.Request(
        LLM_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError, OSError) as e:
        return {"error": f"Failed to connect to local llama-server: {e}"}
        
    choices = data.get("choices", [])
    if not choices:
        return {"error": "Empty completion response from inference server"}
        
    logprobs_obj = choices[0].get("logprobs", {})
    content_list = logprobs_obj.get("content", [])
    
    logprob_a = -100.0
    logprob_b = -100.0
    
    if content_list:
        top_logprobs = content_list[0].get("top_logprobs", [])
        for item in top_logprobs:
            token = item.get("token", "").strip().upper()
            lp = item.get("logprob", -100.0)
            if token == "A" and lp > logprob_a:
                logprob_a = lp
            elif token == "B" and lp > logprob_b:
                logprob_b = lp
                
    # If chosen token matches text directly
    chosen_text = choices[0].get("text", "").strip().upper()
    if chosen_text == "A" and logprob_a == -100.0:
        logprob_a = 0.0
    elif chosen_text == "B" and logprob_b == -100.0:
        logprob_b = 0.0
        
    decision = "A" if logprob_a >= logprob_b else "B"
    
    # Calculate softmax probability between A and B
    max_lp = max(logprob_a, logprob_b)
    exp_a = math.exp(logprob_a - max_lp)
    exp_b = math.exp(logprob_b - max_lp)
    total_exp = exp_a + exp_b
    prob = (exp_a / total_exp) if decision == "A" else (exp_b / total_exp)
    
    # Verify boundary against focus_uri if provided
    focus_scoped = True
    winner = hypothesis_a if decision == "A" else hypothesis_b
    if focus_uri and "/" in winner and focus_uri not in winner:
        focus_scoped = False

    return {
        "decision": decision,
        "prob": round(prob, 4),
        "winner": winner,
        "logprob_a": round(logprob_a, 4),
        "logprob_b": round(logprob_b, 4),
        "focus_uri": focus_uri,
        "focus_scoped": focus_scoped
    }

if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        res = jev_decide(
            premise="The test failed with KeyError in DataPipeline",
            hypothesis_a="Fix the KeyError defect in DataPipeline",
            hypothesis_b="Ignore the error and bypass verification"
        )
        print("jev_decide test result:", res)
        assert "decision" in res and res.get("decision") == "A"
        sys.exit(0)
    mcp.run(transport="stdio")
