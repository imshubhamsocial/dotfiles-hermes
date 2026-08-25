#!/usr/bin/env python3
"""
Auto-install pytest for TDD workflow verification.
"""

import os
import subprocess
import sys

PROJECT_ROOT = sys.argv[1] if len(sys.argv) > 1 else '.'

VENV_PATH = os.path.join(PROJECT_ROOT, '.venv')
PYTHON_PATH = os.path.join(VENV_PATH, 'bin', 'python')

def main():
    """Create venv and install pytest."""
    print("Creating virtual environment at:", VENV_PATH)
    
    if not os.path.exists(VENV_PATH):
        result = subprocess.run([sys.executable, '-m', 'venv', VENV_PATH],
                               cwd=PROJECT_ROOT,
                               capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print("Failed to create venv:", result.stderr)
            sys.exit(1)
    
    result = subprocess.run([PYTHON_PATH, '-c', 'import pytest'],
                           cwd=PROJECT_ROOT,
                           capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        print("pytest is already installed.")
        return
    
    print("Installing pytest...")
    result = subprocess.run([PYTHON_PATH, '-m', 'pip', 'install', 'pytest'],
                           cwd=PROJECT_ROOT,
                           capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print("Failed to install pytest:", result.stderr)
        sys.exit(1)
    
    print("pytest installation complete.")

if __name__ == '__main__':
    main()