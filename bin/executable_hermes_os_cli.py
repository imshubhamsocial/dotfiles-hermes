#!/usr/bin/env python3
"""
U37: Hermes OS CLI Entrypoint
=============================
Standalone executable for the unified Hermes CLI.
Usage: hermes_os_cli.py [prompt] | run | doctor | status | onboard | search | sec-audit | lsp-check | replay
"""

import sys
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from hermes_core.cli import main

if __name__ == "__main__":
    sys.exit(main())
