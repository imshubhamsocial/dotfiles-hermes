"""Exam CLI entrypoint."""
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lib"))

from bin.run_final_integration_exam import main

if __name__ == "__main__":
    sys.exit(main())