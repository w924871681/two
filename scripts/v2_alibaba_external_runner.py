"""Two-worker executor for the frozen Final-V2 Alibaba external evaluation."""
from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import torch

from core.engine import run
from core.protocol import ROOT
from scripts.v2_runner import atomic_json

EXPECTED = 1200
CENTERS = frozenset(range(20060, 20100))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def runtime() -> dict:
    available = bool(torch.cuda.is_available())
    return {"pid": os.getpid(), "sys_executable": str(Path(sys.executable).resolve()), "python_version": platform.python_version(), "torch_version": torch.__version__, "torch_cuda_version": torch.version.cuda, "torch_cuda_available": available, "gpu_name": torch.cuda.get_device_name(0) if available else None}


def valid(path: Path, job: dict) -> bool:
    try:
        frame = pd.read_csv(path)
        col = "method_id" if job["method"] == "Proposed" else "method"
        return len(frame) == 24 and frame.stage.tolist() == list(range(1, 25)) and frame[col].nunique() == 1 and frame[col].iloc[0] == job["method"] and int(frame.center_id.iloc[0]) == job["center_id"] and int(frame.model_seed.iloc[0]) == job["model_seed"] and frame.scenario_id.nunique() == 1 and frame.scenario_id.iloc[0] == job["stream"]["scenario_id"]
    except Exception:
        return False


def worker_init(provenance_dir: str) -> None:
    import core.v2_engine as engine
    engine.ALLOWED_CENTERS = engine.ALLOWED_CENTERS | CENTERS
    atomic_json(Path(provenance_dir) / f"worker_{os.getpid()}.json", runtime() | {"role": "alibaba_external_worker"})


def execute(job: dict, cfg: dict, gate: dict) -> dict:
    out = ROOT / "results_v2_alibaba/trajectories" / job["filename"]
    if out.exists() and valid(out, job):
        return {"status": "skipped", "pid": os.getpid(), "runtime": runtime()}
    if out.exists():
        raise RuntimeError(f"invalid pre-existing Alibaba trajectory: {out}")
    stream = job["stream"]
    started = time.perf_counter()
    if job["method"] == "Proposed":
        import core.v2_engine as engine
        rows = engine.run_v2(job["center_id"], job["model_seed"], {"structure_id": "Proposed", "family": "V2_SP_ShortDual"}, stream["kind"], stream["alpha"], stream["attack_location"], {k: gate[k] for k in ["kappa_rec", "kappa_hist", "delta_imp", "delta_ret"]}, stages=24, backbone="GRU", horizon=1, run_id=out.stem)
        for row in rows:
            row["method_id"] = "Proposed"
    else:
        rows = run(job["center_id"], job["model_seed"], job["method"], stream["kind"], stream["alpha"], stream["attack_location"], cfg, stages=24, backbone="GRU", H=1, run_id=out.stem)
    for row in rows:
        row.update({"scenario_id": stream["scenario_id"], "analysis_scenario": stream["scenario_id"], "execution_phase": "v2_alibaba_external_trace", "scientific_implementation_commit": "7ae7fabd9a4e335e774fbcba2f38dfa8827bb8f3" if job["method"] == "Proposed" else None})
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + f".{os.getpid()}.tmp")
    pd.DataFrame(rows).to_csv(tmp, index=False, na_rep="NA")
    os.replace(tmp, out)
    if not valid(out, job):
        raise RuntimeError(f"published Alibaba trajectory invalid: {out}")
    return {"status": "completed", "pid": os.getpid(), "runtime": runtime(), "wall_s": time.perf_counter() - started}


def main() -> None:
    protocol_path = ROOT / "audits_v2_alibaba/alibaba_protocol_provenance_audit.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    rt = runtime()
    checks = {"protocol_pass": protocol["status"] == "PASS" and len(protocol["jobs"]) == EXPECTED, "v2_core_exact": sha(ROOT / "core/v2_engine.py") == protocol["scientific_hashes"]["core/v2_engine.py"], "v1_core_exact": sha(ROOT / "core/engine.py") == protocol["scientific_hashes"]["core/engine.py"], "final_config_exact": sha(ROOT / "configs_v2_final/frozen_v2_final_commit_config.yaml") == protocol["scientific_hashes"]["final_v2_config"], "runtime_exact": rt["python_version"] == "3.11.15" and rt["torch_version"] == "2.5.1+cu121" and rt["torch_cuda_version"] == "12.1" and rt["torch_cuda_available"] and rt["gpu_name"] == "NVIDIA GeForce RTX 3060 Laptop GPU"}
    if not all(checks.values()):
        raise RuntimeError(f"Alibaba runner preflight failed: {checks}")
    folder = ROOT / "results_v2_alibaba/trajectories"
    jobs = protocol["jobs"]
    existing = sum(valid(folder / job["filename"], job) for job in jobs)
    pending = [job for job in jobs if not valid(folder / job["filename"], job)]
    completed = existing
    started = time.time()
    pids: set[int] = set()
    worker_runtimes = {}
    status_path = ROOT / "results_v2_alibaba/execution_status.json"
    failure_path = ROOT / "results_v2_alibaba/execution_failure.json"
    failure_path.unlink(missing_ok=True)
    provenance_dir = ROOT / "results_v2_alibaba/provenance"
    provenance_dir.mkdir(parents=True, exist_ok=True)

    def status(state: str, warning=None) -> None:
        new = completed - existing
        rate = new / max(time.time() - started, 1e-9) * 3600 if new else None
        remaining = EXPECTED - completed
        atomic_json(status_path, {"state": state, "phase": "v2_alibaba_external_trace", "completed": completed, "expected": EXPECTED, "remaining": remaining, "throughput_trajectories_per_hour": rate, "eta_seconds": remaining / rate * 3600 if rate else None, "runner_pid": os.getpid(), "worker_pids": sorted(pids), "updated_at": now(), "warning": warning, "runtime": rt, "worker_runtimes": worker_runtimes, "partial_scientific_analysis": False})

    status("ALIBABA_EXTERNAL_RUNNING")
    try:
        with cf.ProcessPoolExecutor(max_workers=2, initializer=worker_init, initargs=(str(provenance_dir),)) as pool:
            futures = [pool.submit(execute, job, protocol["frozen_baseline_config"], protocol["final_v2_gate"]) for job in pending]
            for future in cf.as_completed(futures):
                result = future.result()
                completed += 1
                pids.add(int(result["pid"]))
                worker_runtimes[str(result["pid"])] = result["runtime"]
                if completed % 20 == 0 or completed == EXPECTED:
                    status("ALIBABA_EXTERNAL_RUNNING" if completed < EXPECTED else "ALIBABA_EXECUTION_COMPLETE_PENDING_AUDIT")
                    rate = (completed - existing) / max(time.time() - started, 1e-9) * 3600 if completed > existing else 0
                    print(f"Alibaba external {completed}/{EXPECTED} rate={rate:.1f}/h workers={sorted(pids)}", flush=True)
        status("ALIBABA_EXECUTION_COMPLETE_PENDING_AUDIT")
        atomic_json(ROOT / "audits_v2_alibaba/alibaba_execution_complete.json", {"status": "PASS", "completed": completed, "expected": EXPECTED, "existing_valid": existing, "executed_now": completed - existing, "elapsed_s": time.time() - started, "runner_pid": os.getpid(), "worker_pids": sorted(pids), "protocol_sha256": sha(protocol_path), "runtime": rt})
    except Exception as exc:
        message = f"{type(exc).__name__}: {exc}"
        status("ALIBABA_EXTERNAL_EXECUTION_FAILURE", message)
        atomic_json(failure_path, {"status": "FAIL", "error": message, "completed": completed, "expected": EXPECTED, "at": now()})
        raise


if __name__ == "__main__":
    main()
