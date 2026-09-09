"""Detach the approved post-Q2 queue while preserving append-only formal logs."""
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.protocol import ROOT, save_json


def main():
    assert not (ROOT / "runner.pid").exists()
    python = Path(sys.executable)
    assert "rcf-dti-py311" in str(python) and __import__("torch").cuda.is_available()
    console = (ROOT / "logs" / "full_console.log").open("ab", buffering=0)
    stderr = (ROOT / "logs" / "full_stderr.log").open("ab", buffering=0)
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    process = subprocess.Popen(
        [str(python), "-u", str(ROOT / "scripts" / "resume_after_q2_parallel.py")],
        cwd=ROOT, stdout=console, stderr=stderr, stdin=subprocess.DEVNULL,
        creationflags=creationflags, close_fds=True,
    )
    save_json(ROOT / "logs" / "post_q2_launch.json", {
        "launcher_pid": os.getpid(), "runner_pid": process.pid, "python": str(python),
        "script": "scripts/resume_after_q2_parallel.py",
    })
    print(json.dumps({"runner_pid": process.pid, "python": str(python)}), flush=True)


if __name__ == "__main__":
    main()
