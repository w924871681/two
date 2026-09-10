"""Detach the audited Alibaba shutdown-recovery queue on Windows."""
from __future__ import annotations

import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.protocol import ROOT, save_json


def pid_alive(pid: int) -> bool:
    try:
        output = subprocess.check_output(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], text=True)
        return not output.lstrip().startswith("INFO:") and f'"{pid}"' in output
    except (OSError, subprocess.CalledProcessError):
        return False


def archive_stale(path: Path, stamp: str) -> str | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8").strip()
    try:
        pid = int(text)
    except ValueError:
        pid = -1
    if pid > 0 and pid_alive(pid):
        raise RuntimeError(f"active runner already owns {path}: PID {pid}")
    target = ROOT / "logs" / f"stale_{path.name.replace('.', '_')}_{stamp}"
    path.replace(target)
    return str(target.relative_to(ROOT)).replace("\\", "/")


def main() -> None:
    python = Path(sys.executable)
    if "rcf-dti-py311" not in str(python) or not __import__("torch").cuda.is_available():
        raise RuntimeError(f"formal CUDA environment required: {python}")
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    archived = [value for value in [archive_stale(ROOT / "runner.pid", stamp),
                                     archive_stale(ROOT / "logs" / "runner.lock", stamp)] if value]
    failure = ROOT / "logs" / "execution_failure.json"
    if failure.exists():
        target = ROOT / "logs" / f"execution_failure_pre_alibaba_recovery_{stamp}.json"
        failure.replace(target)
        archived.append(str(target.relative_to(ROOT)).replace("\\", "/"))
    console = (ROOT / "logs" / "full_console.log").open("ab", buffering=0)
    stderr = (ROOT / "logs" / "full_stderr.log").open("ab", buffering=0)
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    process = subprocess.Popen(
        [str(python), "-u", str(ROOT / "scripts" / "resume_alibaba_after_shutdown.py")],
        cwd=ROOT, stdout=console, stderr=stderr, stdin=subprocess.DEVNULL,
        creationflags=creationflags, close_fds=True,
    )
    record = {
        "launcher_pid": os.getpid(), "runner_pid": process.pid, "python": str(python),
        "script": "scripts/resume_alibaba_after_shutdown.py", "archived_stale_files": archived,
        "launched_at": datetime.datetime.now().isoformat(),
    }
    save_json(ROOT / "logs" / "alibaba_shutdown_recovery_detached_launch.json", record)
    print(json.dumps(record, indent=2), flush=True)


if __name__ == "__main__":
    main()
