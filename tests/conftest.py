import sys
import os
from pathlib import Path

# Inject .hermes/bin, .hermes/src, and local test paths into sys.path
hermes_root = Path(__file__).resolve().parent.parent
dot_hermes = hermes_root / ".hermes"
chezmoi_src = Path.home() / ".local/share/chezmoi/private_dot_hermes/src"
chezmoi_bin = Path.home() / ".local/share/chezmoi/private_dot_hermes/bin"

for p in [
    str(dot_hermes / "bin"),
    str(dot_hermes / "src"),
    str(chezmoi_src),
    str(chezmoi_bin),
    str(Path.home() / ".hermes/bin"),
    str(Path.home() / ".hermes/src"),
]:
    if p not in sys.path:
        sys.path.insert(0, p)
