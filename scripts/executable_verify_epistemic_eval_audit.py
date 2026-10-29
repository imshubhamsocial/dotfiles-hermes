#!/usr/bin/env python3
"""
GDR24 Phase 41: Epistemic Scorer Validator & False-Positive Eliminator
Audits UK AISI Inspect AI .eval archives against the 3-Gate Epistemic Invariant:
  Gate 1 (G_persona): Zero role-rejection or generic AI disclaimers.
  Gate 2 (G_read):    At least 1 domain DB read tool call executed before refusal/transfer.
  Gate 3 (G_isolation): Zero out-of-domain web_search / internet scraping invocations.
"""
import json
import re
import sys
import zipfile
from pathlib import Path

ROLE_DISCLAIMER_PATTERNS = [
    re.compile(r"as an ai\b", re.IGNORECASE),
    re.compile(r"i am an ai assistant", re.IGNORECASE),
    re.compile(r"i am an autonomous ai", re.IGNORECASE),
    re.compile(r"do not operate a physical online store", re.IGNORECASE),
    re.compile(r"do not have (?:direct )?access to (?:any )?(?:specific company's )?private", re.IGNORECASE),
    re.compile(r"not a human employee or a customer service representative", re.IGNORECASE),
    re.compile(r"which (?:store|website|retailer) (?:or website )?you (?:purchased|placed)", re.IGNORECASE),
    re.compile(r"what store or website did you place", re.IGNORECASE),
]

WEB_LEAK_PATTERNS = [
    re.compile(r"\bweb_search\b", re.IGNORECASE),
    re.compile(r"\bwebsearch\b", re.IGNORECASE),
    re.compile(r"\bweb_serch\b", re.IGNORECASE),
    re.compile(r"general web search did not return", re.IGNORECASE),
]

DOMAIN_READ_TOOLS = {
    "find_user_id_by_email",
    "find_user_id_by_name_zip",
    "get_user_details",
    "get_order_details",
    "get_product_details",
    "list_all_product_types",
    "calculate",
}

def audit_sample_messages(sample_id: str, messages: list[dict], raw_score_val: str) -> dict:
    disclaimer_hits: list[str] = []
    web_leak_hits: list[str] = []
    read_tool_calls: list[str] = []
    write_tool_calls: list[str] = []

    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if isinstance(content, list):
            content = " ".join(
                c.get("text", "") for c in content if isinstance(c, dict)
            )
        text = str(content)

        if role == "assistant":
            for pat in ROLE_DISCLAIMER_PATTERNS:
                if pat.search(text):
                    disclaimer_hits.append(pat.pattern)
            for wpat in WEB_LEAK_PATTERNS:
                if wpat.search(text):
                    web_leak_hits.append(wpat.pattern)

            for tc in msg.get("tool_calls") or []:
                fn_val = tc.get("function")
                if isinstance(fn_val, str):
                    fn_name = fn_val
                elif isinstance(fn_val, dict):
                    fn_name = fn_val.get("name", "")
                else:
                    fn_name = tc.get("name", "")

                if fn_name in DOMAIN_READ_TOOLS:
                    read_tool_calls.append(fn_name)
                elif fn_name in {"web_search", "bash"}:
                    web_leak_hits.append(fn_name)
                elif fn_name:
                    write_tool_calls.append(fn_name)

    g_persona = len(disclaimer_hits) == 0
    g_read = len(read_tool_calls) >= 1
    g_isolation = len(web_leak_hits) == 0

    naive_pass = str(raw_score_val).upper().startswith("C") or str(raw_score_val) == "1.0"
    epistemic_pass = naive_pass and g_persona and g_read and g_isolation
    is_false_positive = naive_pass and not epistemic_pass

    return {
        "sample_id": str(sample_id),
        "raw_score": raw_score_val,
        "naive_pass": naive_pass,
        "g_persona_pass": g_persona,
        "g_read_pass": g_read,
        "g_isolation_pass": g_isolation,
        "read_tools_called": read_tool_calls,
        "write_tools_called": write_tool_calls,
        "disclaimer_violations": len(disclaimer_hits),
        "web_leak_violations": len(web_leak_hits),
        "epistemic_validated_pass": epistemic_pass,
        "false_positive_detected": is_false_positive,
    }

def audit_eval_archive(eval_path: Path) -> dict:
    results = []
    # Try inspect_ai reader first (handles zstd compressed archives)
    try:
        from inspect_ai.log import read_eval_log
        log = read_eval_log(str(eval_path))
        for s in (log.samples or []):
            sid = str(s.id)
            raw_val = "I"
            if s.scores:
                for _, s_obj in s.scores.items():
                    raw_val = getattr(s_obj, "value", "I")
                    break
            msgs = []
            traj = s.store.get("StoredAgentState:RetailAgent:trajectory", []) if hasattr(s, "store") and s.store else []
            if traj:
                for item in traj:
                    if isinstance(item, dict):
                        m = item.get("message", {})
                    else:
                        m = getattr(item, "message", {})
                    if hasattr(m, "model_dump"):
                        msgs.append(m.model_dump())
                    elif isinstance(m, dict):
                        msgs.append(m)
                    else:
                        msgs.append({"role": getattr(m, "role", ""), "content": getattr(m, "text", "") or getattr(m, "content", ""), "tool_calls": getattr(m, "tool_calls", None)})
            elif s.messages:
                msgs = [m.model_dump() if hasattr(m, "model_dump") else dict(m) for m in s.messages]
            results.append(audit_sample_messages(sid, msgs, raw_val))
    except Exception:
        with zipfile.ZipFile(eval_path, "r") as zf:
            sample_files = [f for f in zf.namelist() if f.startswith("samples/") and f.endswith(".json")]
            for sf in sorted(sample_files):
                data = json.loads(zf.read(sf).decode("utf-8"))
                sid = data.get("id", sf)
                messages = data.get("messages", [])
                scores = data.get("scores", {})
                raw_val = "I"
                for _, s_obj in scores.items():
                    raw_val = s_obj.get("value", "I")
                    break
                results.append(audit_sample_messages(sid, messages, raw_val))

    total = len(results)
    naive_passes = sum(1 for r in results if r["naive_pass"])
    true_passes = sum(1 for r in results if r["epistemic_validated_pass"])
    false_positives = sum(1 for r in results if r["false_positive_detected"])

    return {
        "archive": str(eval_path),
        "total_samples": total,
        "naive_passes": naive_passes,
        "naive_pass_rate": round(naive_passes / max(1, total), 4),
        "epistemic_validated_passes": true_passes,
        "epistemic_validated_pass_rate": round(true_passes / max(1, total), 4),
        "false_positives_eliminated": false_positives,
        "samples": results,
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: verify_epistemic_eval_audit.py <path_to_eval_archive>", file=sys.stderr)
        sys.exit(2)
    report = audit_eval_archive(Path(sys.argv[1]))
    print(json.dumps(report, indent=2))
