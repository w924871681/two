"""Two-worker idempotent executor for the frozen robustness-severity matrix."""
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

EXPECTED = 2160
CENTERS = frozenset(range(14000, 14030))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def runtime() -> dict:
    available = bool(torch.cuda.is_available())
    return {"pid": os.getpid(), "sys_executable": str(Path(sys.executable).resolve()), "python_version": platform.python_version(), "torch_version": torch.__version__, "torch_cuda_version": torch.version.cuda, "torch_cuda_available": available, "gpu_name": torch.cuda.get_device_name(0) if available else None}


def valid(path: Path, job: dict) -> bool:
    try:
        f = pd.read_csv(path)
        col = "method_id" if job["method"] == "Proposed" else "method"
        value = "Proposed" if job["method"] == "Proposed" else job["method"]
        return len(f) == 24 and f.stage.tolist() == list(range(1, 25)) and f[col].nunique() == 1 and f[col].iloc[0] == value and int(f.center_id.iloc[0]) == job["center_id"] and int(f.model_seed.iloc[0]) == job["model_seed"] and f.scenario_id.nunique() == 1 and f.scenario_id.iloc[0] == job["stream"]["scenario_id"]
    except Exception:
        return False


def worker_init(provenance_dir: str) -> None:
    import core.v2_engine as engine
    engine.ALLOWED_CENTERS = engine.ALLOWED_CENTERS | CENTERS
    atomic_json(Path(provenance_dir) / f"worker_{os.getpid()}.json", runtime() | {"role": "severity_worker"})


def execute(job: dict, baseline_cfg: dict, gate: dict) -> dict:
    out = ROOT / "results_v2_severity/trajectories" / job["filename"]
    if out.exists() and valid(out, job):
        return {"status": "skipped", "pid": os.getpid(), "runtime": runtime()}
    if out.exists():
        raise RuntimeError(f"invalid pre-existing trajectory: {out}")
    stream = job["stream"]
    started = time.perf_counter()
    if job["method"] == "Proposed":
        import core.v2_engine as engine
        rows = engine.run_v2(job["center_id"], job["model_seed"], {"structure_id": "Proposed", "family": "V2_SP_ShortDual"}, stream["kind"], stream["alpha"], stream["attack_location"], {k: gate[k] for k in ["kappa_rec", "kappa_hist", "delta_imp", "delta_ret"]}, stages=24, backbone="GRU", horizon=1, run_id=out.stem)
        for row in rows:
            row["method_id"] = "Proposed"
    else:
        rows = run(job["center_id"], job["model_seed"], job["method"], stream["kind"], stream["alpha"], stream["attack_location"], baseline_cfg, stages=24, backbone="GRU", H=1, run_id=out.stem)
    for row in rows:
        row.update({"scenario_id": stream["scenario_id"], "analysis_scenario": stream["scenario_id"], "execution_phase": "v2_robustness_severity", "scientific_implementation_commit": "7ae7fabd9a4e335e774fbcba2f38dfa8827bb8f3" if job["method"] == "Proposed" else None})
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + f".{os.getpid()}.tmp")
    pd.DataFrame(rows).to_csv(tmp, index=False, na_rep="NA")
    os.replace(tmp, out)
    if not valid(out, job):
        raise RuntimeError(f"published trajectory invalid: {out}")
    return {"status": "completed", "pid": os.getpid(), "runtime": runtime(), "wall_s": time.perf_counter() - started}


def main() -> None:
    manifest_path = ROOT / "audits_v2_severity/severity_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    reuse = json.loads((ROOT / "audits_v2_severity/alpha010_reuse_audit.json").read_text(encoding="utf-8"))
    rt = runtime()
    checks = {
        "manifest_frozen": manifest["status"] == "FROZEN_BEFORE_EXECUTION" and len(manifest["jobs"]) == EXPECTED,
        "reuse_pass": reuse["status"] == "PASS",
        "v2_core_exact": sha(ROOT / "core/v2_engine.py") == manifest["scientific_hashes"]["core/v2_engine.py"],
        "v1_core_exact": sha(ROOT / "core/engine.py") == manifest["scientific_hashes"]["core/engine.py"],
        "final_config_exact": sha(ROOT / "configs_v2_final/frozen_v2_final_commit_config.yaml") == manifest["scientific_hashes"]["final_v2_config"],
        "runtime_exact": rt["python_version"] == "3.11.15" and rt["torch_version"] == "2.5.1+cu121" and rt["torch_cuda_version"] == "12.1" and rt["torch_cuda_available"] and rt["gpu_name"] == "NVIDIA GeForce RTX 3060 Laptop GPU",
    }
    if not all(checks.values()):
        raise RuntimeError(f"severity runner preflight failed: {checks}")
    jobs = manifest["jobs"]
    folder = ROOT / "results_v2_severity/trajectories"
    existing = sum(valid(folder / j["filename"], j) for j in jobs)
    pending = [j for j in jobs if not valid(folder / j["filename"], j)]
    completed = existing
    started = time.time()
    pids: set[int] = set()
    worker_runtimes = {}
    status_path = ROOT / "results_v2_severity/execution_status.json"
    failure_path = ROOT / "results_v2_severity/execution_failure.json"
    failure_path.unlink(missing_ok=True)
    provenance = ROOT / "results_v2_severity/provenance"
    provenance.mkdir(parents=True, exist_ok=True)

    def status(state: str, warning=None) -> None:
        elapsed = max(time.time() - started, 1e-9)
        new = completed - existing
        rate = new / elapsed * 3600 if new else None
        remaining = EXPECTED - completed
        atomic_json(status_path, {"state": state, "phase": "robustness_severity_new_alpha005_alpha020", "completed": completed, "expected": EXPECTED, "remaining": remaining, "throughput_trajectories_per_hour": rate, "eta_seconds": remaining / rate * 3600 if rate else None, "runner_pid": os.getpid(), "worker_pids": sorted(pids), "updated_at": now(), "warning": warning, "runtime": rt, "worker_runtimes": worker_runtimes, "partial_scientific_analysis": False})

    status("SEVERITY_SWEEP_RUNNING")
    try:
        with cf.ProcessPoolExecutor(max_workers=2, initializer=worker_init, initargs=(str(provenance),)) as pool:
            futures = [pool.submit(execute, j, manifest["frozen_baseline_config"], manifest["final_v2_gate"]) for j in pending]
            for future in cf.as_completed(futures):
                result = future.result()
                completed += 1
                pids.add(int(result["pid"]))
                worker_runtimes[str(result["pid"])] = result["runtime"]
                if completed % 20 == 0 or completed == EXPECTED:
                    status("SEVERITY_SWEEP_RUNNING" if completed < EXPECTED else "SEVERITY_EXECUTION_COMPLETE_PENDING_AUDIT")
                    rate = (completed - existing) / max(time.time() - started, 1e-9) * 3600 if completed > existing else 0
                    print(f"severity {completed}/{EXPECTED} rate={rate:.1f}/h workers={sorted(pids)}", flush=True)
        status("SEVERITY_EXECUTION_COMPLETE_PENDING_AUDIT")
        atomic_json(ROOT / "audits_v2_severity/severity_execution_complete.json", {"status": "PASS", "completed": completed, "expected": EXPECTED, "existing_valid": existing, "executed_now": completed - existing, "elapsed_s": time.time() - started, "runner_pid": os.getpid(), "worker_pids": sorted(pids), "manifest_sha256": sha(manifest_path), "runtime": rt})
    except Exception as exc:
        message = f"{type(exc).__name__}: {exc}"
        status("SEVERITY_EXECUTION_FAILURE", message)
        atomic_json(failure_path, {"status": "FAIL", "error": message, "completed": completed, "expected": EXPECTED, "at": now()})
        raise


if __name__ == "__main__":
    main()
