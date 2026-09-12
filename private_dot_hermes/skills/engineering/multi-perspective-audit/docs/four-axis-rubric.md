# Four-Axis Adversarial Audit Rubric

1. **Correctness**: Does the patch satisfy stated completion criteria with zero test regressions?
2. **Security & OWASP**: Are inputs sanitized? Any path traversal, secret leaks, or command injection?
3. **Hardware Bounds**: Does peak active VRAM remain <= 4,812 MiB?
4. **Portability & YAGNI**: No hardcoded paths (`$HOME` / relative only), no extraneous wrapper classes.
