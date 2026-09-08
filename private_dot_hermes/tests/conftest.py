import sys
from pathlib import Path

# Inject .hermes/src and .hermes/bin into sys.path for Agent OS internal test suites
hermes_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hermes_root / "src"))
sys.path.insert(0, str(hermes_root / "bin"))
sys.path.insert(0, str(hermes_root.parent))
