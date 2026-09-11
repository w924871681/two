"""Unattended, gated orchestration for Final-V2 remaining phases A through E."""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.protocol import ROOT
from scripts.v2_runner import atomic_json

PYTHON = Path(r"C:\Users\92487\anaconda3\envs\rcf-dti-py311\python.exe")
STATUS = ROOT / "results_v2_master/execution_status.json"
FAILURE = ROOT / "results_v2_master/execution_failure.json"
CONSOLE = ROOT / "results_v2_master/full_console.log"
STDERR = ROOT / "results_v2_master/full_stderr.log"


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def status(state: str, phase: str, warning=None, **extra) -> None:
    atomic_json(STATUS, {"state": state, "phase": phase, "runner_pid": os.getpid(), "updated_at": now(), "warning": warning, **extra})


def alive(pid: int) -> bool:
    if os.name == "nt":
        import ctypes
        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if not handle:
            return False
        try:
            code = ctypes.c_ulong()
            return bool(ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))) and code.value == 259
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def run_script(name: str, *args: str, allow_provenance_stop: bool = False) -> int:
    command = [str(PYTHON), str(ROOT / "scripts" / name), *args]
    with CONSOLE.open("a", encoding="utf-8") as stdout, STDERR.open("a", encoding="utf-8") as stderr:
        stdout.write(f"[{now()}] RUN {' '.join(command)}\n")
        stdout.flush()
        result = subprocess.run(command, cwd=ROOT, stdout=stdout, stderr=stderr)
        stdout.write(f"[{now()}] EXIT {name} code={result.returncode}\n")
        stdout.flush()
    if result.returncode and not (allow_provenance_stop and result.returncode == 2):
        raise RuntimeError(f"{name} failed with exit code {result.returncode}")
    return result.returncode


def wait_for_severity(pid: int) -> None:
    source = ROOT / "results_v2_severity/execution_status.json"
    last_record = 0.0
    while True:
        payload = json.loads(source.read_text(encoding="utf-8"))
        state = payload.get("state", "UNKNOWN")
        if state == "SEVERITY_EXECUTION_COMPLETE_PENDING_AUDIT":
            return
        if "FAIL" in state or payload.get("warning"):
            raise RuntimeError(f"Phase A stopped before audit: {payload}")
        if not alive(pid):
            payload = json.loads(source.read_text(encoding="utf-8"))
            if payload.get("state") == "SEVERITY_EXECUTION_COMPLETE_PENDING_AUDIT":
                return
            raise RuntimeError(f"Phase A runner {pid} died: {payload}")
        current = time.time()
        if current - last_record >= 1800:
            status("MASTER_WAITING_FOR_PHASE_A", "robustness_severity", severity_status={key: payload.get(key) for key in ["completed", "expected", "throughput_trajectories_per_hour", "eta_seconds", "runner_pid", "worker_pids", "warning"]})
            last_record = current
        time.sleep(60)


def main() -> None:
    FAILURE.unlink(missing_ok=True)
    CONSOLE.parent.mkdir(parents=True, exist_ok=True)
    severity_pid = int((ROOT / "results_v2_severity/runner.pid").read_text().strip())
    status("MASTER_RUNNING", "waiting_for_phase_a", severity_runner_pid=severity_pid)
    alibaba_state = "NOT_STARTED"
    try:
        wait_for_severity(severity_pid)
        status("MASTER_RUNNING", "phase_a_audit")
        run_script("v2_severity_analyze.py")
        severity_audit = json.loads((ROOT / "audits_v2_severity/severity_execution_integrity_audit.json").read_text(encoding="utf-8"))
        if severity_audit.get("status") != "PASS":
            raise RuntimeError("Phase A scientific integrity failed")

        status("MASTER_RUNNING", "phase_b_provenance")
        code = run_script("v2_alibaba_external_freeze.py", allow_provenance_stop=True)
        if code == 2:
            alibaba_state = "NOT_EXECUTED_PROVENANCE_UNRESOLVED"
        else:
            try:
                status("MASTER_RUNNING", "phase_b_execution")
                run_script("v2_alibaba_external_runner.py")
                status("MASTER_RUNNING", "phase_b_audit")
                run_script("v2_alibaba_external_analyze.py")
                ali_audit = json.loads((ROOT / "audits_v2_alibaba/alibaba_execution_integrity_audit.json").read_text(encoding="utf-8"))
                alibaba_state = "PASS" if ali_audit.get("status") == "PASS" else "EXECUTION_INTEGRITY_FAILED"
            except Exception as exc:
                alibaba_state = "EXECUTION_INTEGRITY_FAILED"
                atomic_json(ROOT / "audits_v2_alibaba/alibaba_master_failure_record.json", {"status": alibaba_state, "error": f"{type(exc).__name__}: {exc}", "scientific_auto_repair": False, "continue_to_phase_c_d_only": True, "at": now()})

        status("MASTER_RUNNING", "phase_c_d_reports", alibaba_state=alibaba_state)
        run_script("v2_remaining_reports.py")
        if alibaba_state == "EXECUTION_INTEGRITY_FAILED":
            raise RuntimeError("Phase B scientific integrity failed; Phase C/D completed, Phase E forbidden")

        status("MASTER_RUNNING", "phase_e_protocol", alibaba_state=alibaba_state)
        run_script("v2_generality_freeze.py")
        status("MASTER_RUNNING", "phase_e_execution", alibaba_state=alibaba_state)
        run_script("v2_generality_runner.py")
        status("MASTER_RUNNING", "phase_e_audit", alibaba_state=alibaba_state)
        run_script("v2_generality_analyze.py")
        status("MASTER_RUNNING", "phase_e_final_handoff", alibaba_state=alibaba_state)
        run_script("v2_remaining_reports.py", "--with-generality")
        status("V2_FINAL_EXPERIMENT_PACKAGE_WITH_GENERALITY_COMPLETE", "complete", alibaba_state=alibaba_state, report=str(ROOT / "V2_FINAL_EXPERIMENT_COMPLETION_REPORT.md"), warning=None)
    except Exception as exc:
        message = f"{type(exc).__name__}: {exc}"
        trace = traceback.format_exc()
        with STDERR.open("a", encoding="utf-8") as stream:
            stream.write(f"[{now()}] {trace}\n")
        atomic_json(FAILURE, {"status": "FAIL", "error": message, "traceback": trace, "phase": json.loads(STATUS.read_text(encoding="utf-8")).get("phase") if STATUS.exists() else None, "at": now(), "scientific_auto_repair": False})
        status("V2_FINAL_EXPERIMENT_MASTER_RUN_STOPPED", "failure", warning=message, alibaba_state=alibaba_state)
        raise


if __name__ == "__main__":
    main()
