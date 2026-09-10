import sys
from pathlib import Path

plugins_root = Path(__file__).resolve().parent
hermes_root = plugins_root.parent
sys.path.insert(0, str(hermes_root))
sys.path.insert(0, str(hermes_root / "scripts"))
sys.path.insert(0, str(plugins_root))
for p in plugins_root.iterdir():
    if p.is_dir() and not p.name.startswith((".", "_")):
        sys.path.insert(0, str(p))
