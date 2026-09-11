"""Low-frequency fail-closed companion for the already running master process.

It only preserves the authorized Phase-C/D consolidation if Alibaba execution or
its audit fails.  It never retries science and never starts Phase E after such a
failure.
"""
from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.protocol import ROOT
from scripts.v2_runner import atomic_json

PYTHON = Path(r"C:\Users\92487\anaconda3\envs\rcf-dti-py311\python.exe")


def main() -> None:
    status_path = ROOT / "results_v2_master/execution_status.json"
    failure_path = ROOT / "results_v2_master/execution_failure.json"
    while True:
        if status_path.exists():
            state = json.loads(status_path.read_text(encoding="utf-8"))
            if state.get("state") == "V2_FINAL_EXPERIMENT_PACKAGE_WITH_GENERALITY_COMPLETE":
                return
            if state.get("state") == "V2_FINAL_EXPERIMENT_MASTER_RUN_STOPPED":
                failure = json.loads(failure_path.read_text(encoding="utf-8")) if failure_path.exists() else {}
                failed_phase = str(failure.get("phase", ""))
                if failed_phase in {"phase_b_execution", "phase_b_audit"}:
                    result = subprocess.run([str(PYTHON), str(ROOT / "scripts/v2_remaining_reports.py")], cwd=ROOT)
                    atomic_json(status_path, {"state": "V2_FINAL_EXPERIMENT_MASTER_RUN_STOPPED_AFTER_PHASE_C_D", "phase": "phase_b_failure_consolidation_complete" if result.returncode == 0 else "phase_c_d_failure", "original_failure": failure, "phase_e_started": False, "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(), "warning": "Alibaba execution/integrity failed; no scientific retry; Phase C/D attempted; Phase E not started."})
                return
        time.sleep(60)


if __name__ == "__main__":
    main()
