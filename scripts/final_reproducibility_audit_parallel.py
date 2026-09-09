"""Run the unchanged P16 checks through the approved execution-only freeze gate."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import scripts.final_reproducibility_audit as original
from scripts.executor_switch_freeze import require_executor_switch_freeze


if __name__ == "__main__":
    original.require_frozen = require_executor_switch_freeze
    original.main()
