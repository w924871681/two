import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import q2_recovery_freeze


class Q2RecoveryFreezeTests(unittest.TestCase):
    def test_recovery_gate_keeps_p7_files_and_checks_execution_allowlist(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "audits").mkdir()
            (root / "scripts").mkdir()
            (root / "core").mkdir()
            (root / "configs").mkdir()
            frozen = root / "core/engine.py"
            frozen.write_text("science")
            execution = {
                relative: root / relative for relative in q2_recovery_freeze.APPROVED_EXECUTION_ONLY
            }
            for path in execution.values():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("execution")
            p7 = {"files": {"core/engine.py": q2_recovery_freeze._hash_file(frozen), "scripts/run_heldout.py": "old"}}
            recovery = {
                "status": "approved_for_q2_recovery", "recovery_git_sha": "new",
                "execution_only_sha256": {name: q2_recovery_freeze._hash_file(path) for name, path in execution.items()},
            }
            (root / "audits/final_freeze.json").write_text(json.dumps(p7))
            (root / "audits/q2_recovery_implementation.json").write_text(json.dumps(recovery))
            with patch.object(q2_recovery_freeze, "ROOT", root), patch("scripts.q2_recovery_freeze.subprocess.check_output", return_value="new\n"):
                q2_recovery_freeze.require_q2_recovery_freeze()
                frozen.write_text("changed")
                with self.assertRaisesRegex(AssertionError, "P7 frozen file changed"):
                    q2_recovery_freeze.require_q2_recovery_freeze()


if __name__ == "__main__":
    unittest.main(verbosity=2)
