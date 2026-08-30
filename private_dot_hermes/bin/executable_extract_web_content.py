#!/usr/bin/env python3.13
"""
Web & HTML Content Extraction Pipeline (Roadmap 6 - Milestone 6b)
================================================================
Extracts clean, boilerplate-free markdown/text from web URLs or local HTML files
using Trafilatura with sub-second token counting via TikToken.

Usage:
    python3.13 bin/extract_web_content.py <url_or_filepath> [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
import tiktoken
import trafilatura


def extract_content(target: str) -> dict:
    html_content = ""
    is_url = target.startswith("http://") or target.startswith("https://")

    if is_url:
        downloaded = trafilatura.fetch_url(target)
        if not downloaded:
            return {"error": f"Failed to fetch URL: {target}", "success": False}
        html_content = downloaded
    else:
        p = Path(target)
        if not p.exists():
            return {"error": f"File not found: {target}", "success": False}
        html_content = p.read_text(encoding="utf-8", errors="replace")

    if is_url or p.suffix.lower() in [".html", ".htm", ".xml"]:
        extracted_text = trafilatura.extract(
            html_content,
            include_links=True,
            include_images=False,
            include_tables=True,
            output_format="txt"
        ) or html_content
        metadata = trafilatura.extract_metadata(html_content)
        title = metadata.title if metadata and metadata.title else (Path(target).stem if not is_url else target)
        author = metadata.author if metadata and metadata.author else "Unknown"
        date = metadata.date if metadata and metadata.date else "Unknown"
    else:
        extracted_text = html_content
        title = p.stem
        author = "Local Author"
        date = "Local File"

    enc = tiktoken.get_encoding("cl100k_base")
    token_count = len(enc.encode(extracted_text))

    return {
        "success": True,
        "source": target,
        "title": title,
        "author": author,
        "date": date,
        "token_count": token_count,
        "char_count": len(extracted_text),
        "text": extracted_text
    }


def main():
    parser = argparse.ArgumentParser(description="Trafilatura Web & HTML Content Extractor")
    parser.add_argument("target", help="URL or local HTML file path")
    parser.add_argument("--json", action="store_true", help="Output full JSON result")
    parser.add_argument("--max-chars", type=int, default=2000, help="Max preview characters when not in JSON mode")
    args = parser.parse_args()

    result = extract_content(args.target)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if not result.get("success"):
            print(f"[-] Error: {result.get('error')}", file=sys.stderr)
            sys.exit(1)
        print(f"Title:       {result['title']}")
        print(f"Author/Date: {result['author']} ({result['date']})")
        print(f"Tokens:      {result['token_count']} (Chars: {result['char_count']})")
        print("-" * 60)
        print(result["text"][:args.max_chars])
        if len(result["text"]) > args.max_chars:
            print(f"\n... [truncated {len(result['text']) - args.max_chars} chars; use --json or --max-chars to expand]")


if __name__ == "__main__":
    main()
