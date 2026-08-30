#!/usr/bin/env python3.13
"""
Generative UI Offline Asset Cache Manager (Roadmap 6 - Milestone 4)
==================================================================
Caches minimal JS libraries (Chart.js, Three.js, D3, KaTeX) in ~/.hermes/assets/js/
for zero-dependency, fully-offline interactive HTML artifact generation.
"""

from __future__ import annotations

import argparse
import urllib.request
from pathlib import Path

ASSETS = {
    "chart.umd.min.js": "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js",
    "three.min.js": "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js",
    "d3.min.js": "https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js",
    "katex.min.js": "https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.js",
}


def cache_assets(target_dir: Path | None = None) -> bool:
    if target_dir is None:
        target_dir = Path.home() / ".hermes/assets/js"
    target_dir.mkdir(parents=True, exist_ok=True)

    print(f"[*] Caching UI assets into: {target_dir}")
    success = True
    for filename, url in ASSETS.items():
        dest = target_dir / filename
        if dest.exists() and dest.stat().st_size > 1024:
            print(f"  [✓] {filename} already cached ({dest.stat().st_size} bytes)")
            continue
        try:
            print(f"  [↓] Downloading {filename} from {url}...")
            urllib.request.urlretrieve(url, dest)
            print(f"  [✓] Successfully cached {filename} ({dest.stat().st_size} bytes)")
        except Exception as e:
            print(f"  [!] Failed to download {filename}: {e}")
            success = False
    return success


def main():
    parser = argparse.ArgumentParser(description="Cache offline assets for Generative UI Artifacts")
    parser.add_argument("--dir", type=str, default=None, help="Target asset directory")
    args = parser.parse_args()

    cache_assets(Path(args.dir) if args.dir else None)


if __name__ == "__main__":
    main()
