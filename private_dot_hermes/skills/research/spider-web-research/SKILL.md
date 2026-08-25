---
name: spider-web-research
description: Blazing-fast Rust-powered web research and documentation scraping for LLMs using spider_cli and ddgs (<1,500 tokens).
---

# Spider Web Research & Distillation Skill

Use this skill when you need live web research, API documentation, mathematical equations, or GitHub code examples without suffering from context bloat or slow browser GUI overhead.

## Quick CLI Invocations

1. **Search and Distill Topic**:
```bash
python3 /var/home/imshubhamsocial/Projects/Workspace/Personal/hermes/.hermes/bin/fast_web_research.py "<query>"
```

2. **Scrape Specific URL to Clean LLM Markdown in Sub-10ms**:
```bash
spider --url <url> --return-format markdown scrape
```

## Best Practices
- Keep search queries technically specific (e.g., "Three.js shallow water laplacian wave equation").
- Never dump raw HTML into context. The spider tool automatically converts pages into token-bounded Markdown.
