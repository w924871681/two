"""Fail-closed Q2-only recovery orchestrator."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.protocol import ROOT, save_json
from core.status import save_execution_status


def git_sha():
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def main():
    preflight = json.loads((ROOT / "audits/q2_crash_recovery.json").read_text())
    equivalence = json.loads((ROOT / "audits/q2_resume_executor_equivalence.json").read_text())
    implementation = json.loads((ROOT / "audits/q2_recovery_implementation.json").read_text())
    assert preflight["status"] == "passed"
    assert preflight["counts"]["trajectory_csv"] == 6421
    assert preflight["counts"]["remaining_expected_scientific_keys"] == 1259
    assert equivalence["status"] == "passed"
    assert implementation["status"] == "approved_for_q2_recovery"
    assert implementation["recovery_git_sha"] == git_sha()
    assert not (ROOT / "results/q3_benign_drift").exists()

    lock = ROOT / "logs/runner.lock"
    with lock.open("x") as stream:
        stream.write(str(os.getpid()))
    (ROOT / "runner.pid").write_text(str(os.getpid()))
    console = (ROOT / "logs/full_console.log").open("a", encoding="utf-8", buffering=1)
    stderr = (ROOT / "logs/full_stderr.log").open("a", encoding="utf-8", buffering=1)
    try:
        old_failure = ROOT / "logs/execution_failure.json"
        if old_failure.exists():
            archived = ROOT / "logs" / f"execution_failure_pre_q2_recovery_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            old_failure.replace(archived)
        save_execution_status(ROOT / "logs/execution_status.json", {
            "phase": "Q2 crash recovery", "completed": 6421, "expected": 7680,
            "remaining": 1259, "heldout_started": True, "recovery_git_sha": git_sha(),
        })
        print("START Q2-ONLY RECOVERY", datetime.datetime.now().isoformat(), file=console, flush=True)
        env = dict(os.environ)
        env["RESUME_FROM_PHASE"] = "Q2"
        env["STOP_AFTER_PHASE"] = "Q2"
        subprocess.run(
            [sys.executable, str(ROOT / "scripts/run_heldout.py")], cwd=ROOT,
            env=env, check=True, stdout=console, stderr=stderr,
        )
        audit = json.loads((ROOT / "audits/q2_integrity.json").read_text())
        assert audit["status"] == "passed" and audit["counts"]["completed"] == 7680
        save_execution_status(ROOT / "logs/execution_status.json", {
            "phase": "WAITING_FOR_MANUAL_POST_Q2_BENCHMARK_APPROVAL",
            "phase_complete": "Q2", "completed": 7680, "expected": 7680,
            "heldout_started": True, "recovery_git_sha": git_sha(), "remaining": [],
        })
        print("Q2 RECOVERY COMPLETE; STOPPED BEFORE Q3", datetime.datetime.now().isoformat(), file=console, flush=True)
    except Exception:
        error = traceback.format_exc()
        print(error, file=stderr, flush=True)
        save_json(ROOT / "logs/execution_failure.json", {
            "time": datetime.datetime.now().isoformat(), "error": error,
            "status": "STOPPED_NO_AUTOMATIC_RETRY", "phase": "Q2 crash recovery",
        })
        raise
    finally:
        console.close()
        stderr.close()
        lock.unlink(missing_ok=True)
        (ROOT / "runner.pid").unlink(missing_ok=True)


if __name__ == "__main__":
    main()
