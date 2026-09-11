"""Run the frozen 720-trajectory V2 minimal final confirmatory matrix."""
from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import torch

from core.engine import initial_model
from core.models import state_hash
from core.protocol import ROOT, REGIMES, digest
from vendor.main_cfg import MainCfg
from vendor.sim import simulate_centers
from scripts.v2_runner import atomic_json


CENTERS = list(range(14000, 14030))
SEEDS = [7311, 7312, 7313]
EXPECTED = 720
SCIENTIFIC_COMMIT = "7ae7fabd9a4e335e774fbcba2f38dfa8827bb8f3"
CORE_SHA = "f27d0abb6fabb50453cb4e04684b8e7b5f99d27aca7ae1f1755990640f3ce024"
EXPECTED_EXE = r"C:\Users\92487\anaconda3\envs\rcf-dti-py311\python.exe"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def runtime() -> dict:
    available = bool(torch.cuda.is_available())
    return {
        "pid": os.getpid(), "sys_executable": str(Path(sys.executable).resolve()),
        "python_version": platform.python_version(), "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda, "torch_cuda_available": available,
        "gpu_name": torch.cuda.get_device_name(0) if available else None,
    }


def runtime_ok(value: dict) -> bool:
    return (
        Path(value["sys_executable"]).resolve() == Path(EXPECTED_EXE).resolve()
        and value["python_version"] == "3.11.15" and value["torch_version"] == "2.5.1+cu121"
        and value["torch_cuda_version"] == "12.1" and value["torch_cuda_available"] is True
        and value["gpu_name"] == "NVIDIA GeForce RTX 3060 Laptop GPU"
    )


def verify_frozen() -> tuple[dict, dict, dict]:
    cfg = ROOT / "configs_v2_final"
    method = json.loads((cfg / "frozen_v2_final_method.yaml").read_text(encoding="utf-8"))
    gate = json.loads((cfg / "frozen_v2_final_commit_config.yaml").read_text(encoding="utf-8"))
    manifest = json.loads((cfg / "frozen_v2_minimal_confirmatory_manifest.json").read_text(encoding="utf-8"))
    plan = json.loads((cfg / "frozen_v2_minimal_analysis_plan.json").read_text(encoding="utf-8"))
    freeze = json.loads((ROOT / "audits_v2_final/final_method_freeze_audit.json").read_text(encoding="utf-8"))
    listed = freeze["artifact_hashes"]
    checks = {
        "method_freeze_pass": freeze["status"] == "PASS",
        "manifest_exact": manifest["expected_trajectories"] == EXPECTED and len(manifest["jobs"]) == EXPECTED,
        "analysis_plan_frozen": plan["status"] == "ANALYSIS_PLAN_FROZEN",
        "artifact_hashes_exact": all(sha256(cfg / name) == value for name, value in listed.items()),
        "core_exact": sha256(ROOT / "core/v2_engine.py") == CORE_SHA,
        "method_exact": method["scientific_implementation_commit"] == SCIENTIFIC_COMMIT,
        "runtime_exact": runtime_ok(runtime()),
        "tag_exists": bool(subprocess.check_output(["git", "rev-list", "-n", "1", "v2-final-minimal-frozen"], cwd=ROOT, text=True).strip()),
    }
    if not all(checks.values()):
        raise RuntimeError(f"final frozen preflight failed: {[k for k,v in checks.items() if not v]}")
    return manifest, gate, checks


def generate_fresh_centers() -> dict:
    existing = [c for c in CENTERS if (ROOT / "data" / f"center_{c}.npz").exists()]
    if existing:
        if existing != CENTERS:
            raise RuntimeError(f"partial fresh pool exists: {existing}")
        return verify_fresh_centers()
    cfg = MainCfg(); cfg.sim.seed = 7311; cfg.sim.n_history = 17000
    for kind in "ABC":
        getattr(cfg.sim, "type_" + kind).drift_prob = 0.0
    centers = simulate_centers(cfg, len(CENTERS), seed_offset=CENTERS[0] * 17, start_center_id=CENTERS[0])
    ROOT.joinpath("data").mkdir(exist_ok=True)
    for i, center in enumerate(centers):
        regime = REGIMES[i % 4]
        t = np.arange(len(center.y)); shift = np.zeros(len(t)); onset = 1400 + 8 * 640
        if regime == "abrupt": shift[t >= onset] = 0.8
        if regime == "gradual": shift = 0.8 * np.clip((t - onset) / (8 * 640), 0, 1)
        if regime == "recurring": shift = 0.8 * (((t >= 1400 + 6 * 640) & (t < 1400 + 12 * 640)) | (t >= 1400 + 18 * 640))
        eps = 1e-5
        logit = lambda a: np.log(np.clip(a, eps, 1-eps) / (1-np.clip(a, eps, 1-eps)))
        sigmoid = lambda a: 1 / (1 + np.exp(-a))
        y = sigmoid(logit(center.y) + shift).astype("float32")
        x = np.zeros_like(center.X)
        for k, gain in enumerate(center.metadata["metric_gains"]):
            delay = center.metadata["metric_delays"][k] // center.dt
            delayed = np.concatenate([np.repeat(shift[0], delay), shift[:len(shift)-delay]]) if delay else shift
            x[:, k] = (sigmoid(logit(center.X[:, k]) + gain * delayed) * center.M[:, k]).astype("float32")
        x = np.concatenate([x, center.M], 1)
        meta = {"center_id": center.center_id, "center_type": center.center_type, "drift_regime": regime,
                "pool": "v2_fresh_confirmatory_heldout", "dt": center.dt, "data_seed": 7311,
                "clean_hash": digest(x, y, center.timestamps), "base_generator": center.metadata}
        path = ROOT / "data" / f"center_{center.center_id}.npz"
        tmp = path.with_name(path.name + f".{os.getpid()}.tmp.npz")
        np.savez_compressed(tmp, x=x, y=y, ts=center.timestamps, meta=json.dumps(meta))
        os.replace(tmp, path)
    return verify_fresh_centers()


def verify_fresh_centers() -> dict:
    files = {}
    for i, center in enumerate(CENTERS):
        path = ROOT / "data" / f"center_{center}.npz"
        with np.load(path, allow_pickle=False) as z:
            meta = json.loads(str(z["meta"])); computed = digest(z["x"], z["y"], z["ts"])
        expected_regime = REGIMES[i % 4]
        if meta["center_id"] != center or meta["drift_regime"] != expected_regime or meta["pool"] != "v2_fresh_confirmatory_heldout" or meta["clean_hash"] != computed:
            raise RuntimeError(f"fresh center validation failed: {center}")
        files[str(center)] = {"sha256": sha256(path), "clean_hash": computed, "regime": expected_regime}
    return files


def init_checkpoint(args: tuple[int, int]) -> dict:
    center, seed = args
    model = initial_model(center, seed, "GRU", 1)
    path = ROOT / "checkpoints" / f"M0_GRU_H1_{seed}_{center}.pt"
    return {"center": center, "seed": seed, "pid": os.getpid(), "state_hash": state_hash(model), "sha256": sha256(path)}


def valid_output(path: Path, job: dict) -> bool:
    try:
        frame = pd.read_csv(path)
        return (
            len(frame) == 24 and frame.stage.is_unique and set(frame.stage) == set(range(1,25))
            and frame.method_id.nunique() == 1 and frame.method_id.iloc[0] == job["method_id"]
            and int(frame.center_id.iloc[0]) == job["center_id"] and int(frame.model_seed.iloc[0]) == job["model_seed"]
            and frame.scenario_id.nunique() == 1 and frame.scenario_id.iloc[0] == job["stream"]["scenario_id"]
        )
    except Exception:
        return False


def worker_init(provenance_dir: str) -> None:
    import core.v2_engine as engine
    engine.ALLOWED_CENTERS = engine.ALLOWED_CENTERS | frozenset(CENTERS)
    atomic_json(Path(provenance_dir) / f"worker_{os.getpid()}.json", runtime() | {"role": "worker", "phase": "v2_final_minimal_confirmatory"})


def execute(job: dict) -> dict:
    import core.v2_engine as engine
    out = ROOT / "results_v2_final/trajectories" / job["filename"]
    if out.exists() and valid_output(out, job):
        return {"pid": os.getpid(), "status": "skipped", "path": str(out), "runtime": runtime()}
    if out.exists():
        raise RuntimeError(f"invalid pre-existing output: {out}")
    if job["method_id"] == "Final_V2_SP_ShortDual":
        structure = {"structure_id": "Final_V2_SP_ShortDual", "family": "V2_SP_ShortDual"}
        gate = {"kappa_rec": 0.0, "kappa_hist": 0.5, "delta_imp": 2.8018237766243602e-05, "delta_ret": 0.0}
    else:
        structure = {"structure_id": "V1_LegacyFull", "family": "V0_LegacyFull"}
        gate = dict(engine.V1_GATE)
    started = time.perf_counter()
    stream = job["stream"]
    rows = engine.run_v2(job["center_id"], job["model_seed"], structure, stream["kind"], stream["alpha"], stream["attack_location"], gate, run_id=out.stem)
    for row in rows:
        row.update({"method_id": job["method_id"], "scenario_id": stream["scenario_id"], "analysis_scenario": job["analysis_scenario"],
                    "execution_phase": "v2_final_minimal_confirmatory", "scientific_implementation_commit": SCIENTIFIC_COMMIT})
    frame = pd.DataFrame(rows)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + f".{os.getpid()}.tmp")
    frame.to_csv(tmp, index=False, na_rep="NA"); os.replace(tmp, out)
    if not valid_output(out, job): raise RuntimeError(f"published output invalid: {out}")
    return {"pid": os.getpid(), "status": "completed", "path": str(out), "wall_s": time.perf_counter()-started, "runtime": runtime()}


def main() -> None:
    manifest, gate, prechecks = verify_frozen()
    audit_path = ROOT / "audits_v2_final/final_heldout_access_audit.json"
    if audit_path.exists():
        access = json.loads(audit_path.read_text(encoding="utf-8"))
        if not access.get("heldout_accessed"): raise RuntimeError("invalid one-way access audit")
    else:
        access = {"schema": "ravm-dt-v2-final-heldout-access-v1", "status": "HELDOUT_OPENED",
                  "first_heldout_access_utc": now(), "heldout_accessed": True, "heldout_materialized": False,
                  "centers": CENTERS, "pre_access_checks": prechecks}
        atomic_json(audit_path, access)
    fresh_files = generate_fresh_centers()
    if not access.get("heldout_materialized"):
        access.update({"heldout_materialized": True, "first_heldout_materialization_utc": now(), "materialized_files": fresh_files})
        atomic_json(audit_path, access)

    runner_runtime = runtime()
    if not runtime_ok(runner_runtime): raise RuntimeError("runtime changed after heldout materialization")
    provenance = ROOT / "results_v2_final/provenance"; provenance.mkdir(parents=True, exist_ok=True)
    checkpoints = []
    with cf.ProcessPoolExecutor(max_workers=2) as pool:
        for result in pool.map(init_checkpoint, [(c,s) for c in CENTERS for s in SEEDS]): checkpoints.append(result)
    atomic_json(ROOT / "audits_v2_final/final_initial_checkpoint_manifest.json", {"status":"PASS", "expected":90, "checkpoints":checkpoints})

    jobs = manifest["jobs"]
    existing = sum(valid_output(ROOT / "results_v2_final/trajectories" / j["filename"], j) for j in jobs)
    pending = [j for j in jobs if not valid_output(ROOT / "results_v2_final/trajectories" / j["filename"], j)]
    completed = existing; started = time.time(); pids=set(); worker_runtimes={}
    status_path = ROOT / "results_v2_final/execution_status.json"
    failure_path = ROOT / "results_v2_final/execution_failure.json"
    failure_path.unlink(missing_ok=True)
    def status(state: str, warning=None):
        elapsed=max(time.time()-started,1e-9); new=completed-existing; rate=new/elapsed*3600 if new else None; remaining=EXPECTED-completed
        atomic_json(status_path, {"state":state,"phase":"v2_final_minimal_confirmatory","completed":completed,"expected":EXPECTED,
            "remaining":remaining,"throughput_trajectories_per_hour":rate,"eta_seconds":remaining/rate*3600 if rate else None,
            "runner_pid":os.getpid(),"worker_pids":sorted(pids),"updated_at":now(),"warning":warning,
            "heldout_accessed":True,"heldout_materialized":True,"runner_runtime":runner_runtime,"worker_runtimes":worker_runtimes})
    status("720_TRAJECTORIES_RUNNING")
    try:
        with cf.ProcessPoolExecutor(max_workers=2, initializer=worker_init, initargs=(str(provenance),)) as pool:
            futures=[pool.submit(execute,j) for j in pending]
            for future in cf.as_completed(futures):
                result=future.result(); completed+=1; pids.add(int(result["pid"])); worker_runtimes[str(result["pid"])]=result["runtime"]
                if completed % 10 == 0 or completed == EXPECTED:
                    status("720_TRAJECTORIES_RUNNING" if completed < EXPECTED else "EXECUTION_COMPLETE_PENDING_AUDIT")
                    elapsed=max(time.time()-started,1e-9); rate=(completed-existing)/elapsed*3600 if completed>existing else 0
                    print(f"V2 final {completed}/{EXPECTED} rate={rate:.1f}/h workers={sorted(pids)}",flush=True)
        status("EXECUTION_COMPLETE_PENDING_AUDIT")
        atomic_json(ROOT / "audits_v2_final/final_execution_complete.json", {"status":"PASS","completed":completed,"expected":EXPECTED,
            "existing_valid":existing,"executed_now":completed-existing,"runner_pid":os.getpid(),"worker_pids":sorted(pids),
            "elapsed_s":time.time()-started,"manifest_sha256":sha256(ROOT/'configs_v2_final/frozen_v2_minimal_confirmatory_manifest.json'),
            "heldout_accessed":True,"heldout_materialized":True,"runtime":runner_runtime})
    except Exception as exc:
        message=f"{type(exc).__name__}: {exc}"; status("EXECUTION_FAILURE",message)
        atomic_json(failure_path,{"status":"FAIL","error":message,"completed":completed,"expected":EXPECTED,"at":now()})
        raise


if __name__ == "__main__": main()
