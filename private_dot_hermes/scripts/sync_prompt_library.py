#!/usr/bin/env python3
"""
Hermes Agent OS: Weekly Autonomous Prompt Library Sync Script
Fetches upstream Claude Code & Gemini prompt guidelines, diffs against local skills,
and outputs a structured audit report to .hermes/evolution/.
"""

import re
import sys
import asyncio
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
CLAUDE_SKILL_PATH = WORKSPACE / "skills" / "engineering" / "claude-prompt-library" / "SKILL.md"
EVOLUTION_DIR = (
    WORKSPACE / "memories" / "evolution"
    if (WORKSPACE / "memories" / "evolution").exists()
    else WORKSPACE / "evolution"
)

CLAUDE_URL = "https://code.claude.com/docs/en/prompt-library"
GEMINI_URL = "https://ai.google.dev/gemini-api/prompts"

KNOWN_CATEGORIES = [
    "Understand", "Plan", "Prototype", "Build", "Test", "Refactor",
    "Review", "Steer", "Debug", "Git", "Release", "Data", "Automate",
    "Product Design", "Docs", "Marketing", "Security", "On-call"
]


async def fetch_url_content(url: str) -> str:
    """Fetch URL markdown using crawl4ai or fallback to httpx."""
    # 1. Try Crawl4AI
    try:
        from crawl4ai import AsyncWebCrawler
        async with AsyncWebCrawler() as crawler:
            res = await crawler.arun(url=url)
            if res.markdown:
                return res.markdown
    except Exception:
        pass

    # 2. Fallback to httpx
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"})
            if resp.status_code == 200:
                return resp.text
    except Exception as e:
        return f"Fetch error: {e}"

    return "No content retrieved"


def extract_categories(text: str) -> list[str]:
    """Scan retrieved content for candidate engineering prompt categories."""
    found = set()
    for cat in KNOWN_CATEGORIES:
        pattern = rf"\b{re.escape(cat)}\b"
        if re.search(pattern, text, re.IGNORECASE):
            found.add(cat)
    return sorted(list(found))


def main():
    print(f"[Prompt-Sync] Initiating weekly prompt library audit at {datetime.now().isoformat()}...")
    EVOLUTION_DIR.mkdir(parents=True, exist_ok=True)
    today_str = datetime.now().strftime("%Y%m%d")
    diff_report_path = EVOLUTION_DIR / f"prompt_library_diff_{today_str}.md"

    # Fetch URLs
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        claude_content = loop.run_until_complete(fetch_url_content(CLAUDE_URL))
        gemini_content = loop.run_until_complete(fetch_url_content(GEMINI_URL))
    finally:
        loop.close()

    claude_fetched = len(claude_content) > 100
    gemini_fetched = len(gemini_content) > 100

    print(f"[Prompt-Sync] Claude Prompt Library: {'Fetched (' + str(len(claude_content)) + ' bytes)' if claude_fetched else 'Offline/Unreachable'}")
    print(f"[Prompt-Sync] Gemini Prompt Guidelines: {'Fetched (' + str(len(gemini_content)) + ' bytes)' if gemini_fetched else 'Offline/Unreachable'}")

    # Inspect current local skill
    local_cats = []
    if CLAUDE_SKILL_PATH.exists():
        content = CLAUDE_SKILL_PATH.read_text(encoding="utf-8")
        local_cats = [c for c in KNOWN_CATEGORIES if "## " in content and c.lower() in content.lower()]

    discovered_claude = extract_categories(claude_content) if claude_fetched else KNOWN_CATEGORIES

    # Compute diffs
    new_categories = [c for c in discovered_claude if c not in local_cats]
    missing_categories = [c for c in KNOWN_CATEGORIES if c not in local_cats]

    # Generate Report
    report = f"""# Weekly Prompt Library Autonomous Sync Report

**Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Claude Code URL**: {CLAUDE_URL} ({'Available' if claude_fetched else 'Offline'})  
**Gemini API URL**: {GEMINI_URL} ({'Available' if gemini_fetched else 'Offline'})  
**Local Skill**: `{CLAUDE_SKILL_PATH}`  

---

## 1. Upstream Synchronization Status

| Target Source | Status | Payload Size |
|:---|:---:|:---|
| Claude Code Prompt Library | {'ACTIVE' if claude_fetched else 'FALLBACK_OFFLINE'} | {len(claude_content)} bytes |
| Gemini API PTCF Framework | {'ACTIVE' if gemini_fetched else 'FALLBACK_OFFLINE'} | {len(gemini_content)} bytes |

---

## 2. Category Parity Matrix

- **Active Categories in Local Skill**: {len(local_cats)} / 18
- **Upstream Categories Identified**: {len(discovered_claude)}
- **New Upstream Categories Found**: {len(new_categories)} ({', '.join(new_categories) if new_categories else 'None - Full Parity'})
- **Missing Local Categories**: {len(missing_categories)} ({', '.join(missing_categories) if missing_categories else 'None - 100% Complete'})

---

## 3. Decision
{'[PARITY MAINTAINED] Local prompt skills match upstream taxonomy. No updates required.' if not new_categories else '[DIFF DETECTED] New categories discovered. Awaiting user confirmation before mutating SKILL.md.'}
"""

    diff_report_path.write_text(report, encoding="utf-8")
    print(f"[Prompt-Sync] Report written to: {diff_report_path}")
    
    # Mirror to home ~/.hermes/
    home_diff_dir = (
        Path.home() / ".hermes" / "memories" / "evolution"
        if (Path.home() / ".hermes" / "memories" / "evolution").exists()
        else Path.home() / ".hermes" / "evolution"
    )
    home_diff = home_diff_dir / f"prompt_library_diff_{today_str}.md"
    if home_diff.parent.exists():
        home_diff.write_text(report, encoding="utf-8")

    return 0


if __name__ == "__main__":
    sys.exit(main())
