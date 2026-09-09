import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.status import save_execution_status


def sharing_violation():
    error = PermissionError(13, "sharing violation")
    error.winerror = 5
    return error


class ExecutionStatusWindowsRetryTests(unittest.TestCase):
    def test_retries_transient_windows_replace_and_publishes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "execution_status.json"
            real_replace = __import__("os").replace
            calls = {"count": 0}

            def flaky_replace(source, target):
                calls["count"] += 1
                if calls["count"] <= 3:
                    raise sharing_violation()
                return real_replace(source, target)

            with patch("core.status.os.replace", side_effect=flaky_replace), patch("core.status.time.sleep") as sleep:
                self.assertTrue(save_execution_status(path, {"phase": "q2"}))
            self.assertEqual(json.loads(path.read_text()), {"phase": "q2"})
            self.assertEqual(calls["count"], 4)
            self.assertEqual([call.args[0] for call in sleep.call_args_list], [0.05, 0.1, 0.2])

    def test_persistent_replace_failure_is_warning_not_scientific_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "execution_status.json"
            warning = Path(directory) / "warnings.log"
            path.write_text('{"phase":"old"}', encoding="utf-8")
            with patch("core.status.os.replace", side_effect=sharing_violation()), patch("core.status.time.sleep"):
                self.assertFalse(save_execution_status(path, {"phase": "new"}, retry_delays=(0.05, 0.1), warning_path=warning))
            self.assertEqual(json.loads(path.read_text()), {"phase": "old"})
            record = json.loads(warning.read_text().strip())
            self.assertEqual(record["event"], "execution_status_publish_failed")
            self.assertTrue(record["scientific_trajectory_preserved"])
            self.assertFalse(any(Path(directory).glob("execution_status.json.*.tmp")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
