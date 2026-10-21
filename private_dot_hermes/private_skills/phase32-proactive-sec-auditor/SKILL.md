---
name: proactive-sec-auditor
description: AST taint, OSV & entropy security audit
---

# Proactive Security Auditor

## When to Use
Use for auditing repositories for SQLi, command injection, leaked secrets, vulnerable dependencies, and prompt injection payloads.

## Quick Reference
* Input & Entropy Gate: `mcp_openjev(sanitize_and_audit_input)`
* AST Taint Scan: `semgrep scan --config auto` & `npx ast-grep`
* Audit Ledger: `.hermes/cache/tool_invocation_ledger.jsonl`

## Procedure
1. Run `jev_compile_intent` and `sanitize_and_audit_input` on Turn 1 to verify Shannon entropy (H <= 4.6) and zero privilege escalation.
2. Execute `extract_workspace_ast`, `semgrep`, and `ast-grep` on CPU RAM to detect unparameterized SQL queries, `shell=True`, or path traversals.
3. Remediation patches must use parameterized bindings and canonical `Path.resolve()` checks within Karpathy U12 bounds (<= 15 lines).
4. Run security regression tests (`pytest -q`) and verify sealed cryptographic receipt at `/tmp/hermes_verified_receipt.json`.
