"""Idempotent two-worker runner for V2 development and calibration only."""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import hashlib
import itertools
import json
import os
import platform
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import torch

from core.protocol import ROOT
from core.v2_engine import V1_GATE, run_v2


SEEDS = [7311, 7312, 7313]
DEVELOPMENT_CENTERS = list(range(11000, 11020))
CALIBRATION_CENTERS = list(range(12000, 12020))
SCENARIOS = [
    {"scenario_id": "clean", "kind": "clean", "alpha": 0.0, "location": "both"},
    {"scenario_id": "mixed_a010_both", "kind": "mixed", "alpha": 0.1, "location": "both"},
    {"scenario_id": "persistent_a010_verification_only", "kind": "persistent_bias", "alpha": 0.1, "location": "verification_only"},
    {"scenario_id": "replay_a010_verification_only", "kind": "replay", "alpha": 0.1, "location": "verification_only"},
]
CALIBRATION_SCENARIOS = SCENARIOS[:2]


def runtime_provenance() -> dict:
    cuda_available = bool(torch.cuda.is_available())
    return {
        "pid": os.getpid(),
        "sys_executable": str(Path(sys.executable).resolve()),
        "python_version": platform.python_version(),
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
        "torch_cuda_available": cuda_available,
        "gpu_name": torch.cuda.get_device_name(0) if cuda_available else None,
    }


def structural_grid() -> list[dict]:
    values = [
        {"structure_id": "V0_LegacyFull", "family": "V0_LegacyFull"},
        {"structure_id": "V1_SP_StaticDual", "family": "V1_SP_StaticDual"},
        {"structure_id": "V2_SP_ShortDual", "family": "V2_SP_ShortDual"},
    ]
    for family in ["V3_SP_AdaptiveDual", "V4_SP_AdaptiveDual_NoRealign"]:
        for h_short, numerator, r_persist in itertools.product([6, 12], [4, 5], [2, 3]):
            values.append(
                {
                    "structure_id": f"{family}_hs{h_short}_sup{numerator}of6_r{r_persist}",
                    "family": family,
                    "h_short": h_short,
                    "support_min": numerator / 6,
                    "support_min_fraction": f"{numerator}/6",
                    "r_persist": r_persist,
                }
            )
    values.append({"structure_id": "D0_SP_RecentOnly", "family": "D0_SP_RecentOnly", "diagnostic_only": True})
    assert len(values) == 20
    return values


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(8 * 1024 * 1024):
            h.update(block)
    return h.hexdigest()


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(payload, encoding="utf-8")
    delays = [0.05, 0.1, 0.2, 0.4, 0.8]
    for attempt in range(len(delays) + 1):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            if attempt == len(delays):
                raise
            time.sleep(delays[attempt])


def worker_initializer(phase: str, provenance_dir: str) -> None:
    provenance = runtime_provenance() | {"phase": phase, "role": "worker"}
    atomic_json(Path(provenance_dir) / f"worker_{os.getpid()}.json", provenance)


def output_name(job: dict) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", job["structure"]["structure_id"])
    gate = job["gate"]
    gate_part = ""
    if job["phase"] == "calibration":
        gate_part = f"__kr{gate['kappa_rec']:g}_kh{gate['kappa_hist']:g}"
    return f"{safe}{gate_part}__{job['scenario']['scenario_id']}__{job['center']}__{job['seed']}.csv"


def valid_output(path: Path, job: dict) -> bool:
    try:
        data = pd.read_csv(path)
        return (
            len(data) == 24
            and set(data.stage) == set(range(1, 25))
            and data.stage.is_unique
            and data.center_id.nunique() == 1
            and int(data.center_id.iloc[0]) == job["center"]
            and data.model_seed.nunique() == 1
            and int(data.model_seed.iloc[0]) == job["seed"]
            and data.structure_id.nunique() == 1
            and data.structure_id.iloc[0] == job["structure"]["structure_id"]
            and data.scenario_id.nunique() == 1
            and data.scenario_id.iloc[0] == job["scenario"]["scenario_id"]
        )
    except Exception:
        return False


def execute_job(job: dict) -> dict:
    out_dir = Path(job["out_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / output_name(job)
    if path.exists() and valid_output(path, job):
        return {"status": "skipped", "path": str(path), "pid": os.getpid(), "runtime": runtime_provenance()}
    if path.exists():
        raise RuntimeError(f"invalid pre-existing V2 output: {path}")
    started = time.perf_counter()
    rows = run_v2(
        job["center"],
        job["seed"],
        job["structure"],
        job["scenario"]["kind"],
        job["scenario"]["alpha"],
        job["scenario"]["location"],
        job["gate"],
        run_id=path.stem,
    )
    for row in rows:
        row["scenario_id"] = job["scenario"]["scenario_id"]
        row["execution_phase"] = job["phase"]
    frame = pd.DataFrame(rows)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    frame.to_csv(tmp, index=False, na_rep="NA")
    os.replace(tmp, path)
    if not valid_output(path, job):
        raise RuntimeError(f"published V2 output failed validation: {path}")
    return {
        "status": "completed",
        "path": str(path),
        "pid": os.getpid(),
        "runtime": runtime_provenance(),
        "wall_s": time.perf_counter() - started,
    }


def scientific_manifest_view(manifest: dict) -> dict:
    return {
        key: manifest[key]
        for key in ["schema", "phase", "workers", "job_count", "stage_count", "scientific_key", "preflight", "jobs"]
    }


def preflight(phase: str) -> dict:
    seal_path = ROOT / "configs_v2_dev/v2_confirmatory_pool_manifest.json"
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    if seal["status"] != "SEALED_NOT_MATERIALIZED":
        raise RuntimeError("V2 confirmatory pool is not sealed")
    materialized = [str(ROOT / "data" / f"center_{center}.npz") for center in range(14000, 14030) if (ROOT / "data" / f"center_{center}.npz").exists()]
    if materialized:
        raise RuntimeError(f"sealed V2 centers unexpectedly materialized: {materialized}")
    final_audit = json.loads((ROOT / "audits/final_reproducibility_audit.json").read_text(encoding="utf-8"))
    if final_audit["status"] != "passed":
        raise RuntimeError("V1 final audit is not PASS")
    return {
        "phase": phase,
        "v2_confirmatory_pool_sha256": sha256(seal_path),
        "v2_confirmatory_pool_status": seal["status"],
        "heldout_materialized": False,
        "v1_final_audit": "passed",
        "v1_frozen_candidate_sha256": sha256(ROOT / "configs/frozen_candidate_config.yaml"),
        "v1_frozen_commit_sha256": sha256(ROOT / "configs/frozen_commit_config.yaml"),
        "v1_frozen_baseline_sha256": sha256(ROOT / "configs/frozen_baseline_config.yaml"),
    }


def make_jobs(phase: str, out_dir: Path) -> list[dict]:
    if phase == "development":
        structures = structural_grid()
        gates = [V1_GATE]
        centers = DEVELOPMENT_CENTERS
        scenarios = SCENARIOS
    else:
        structure = json.loads((ROOT / "configs_v2_dev/frozen_v2_structure.yaml").read_text(encoding="utf-8"))
        structures = [structure]
        gates = [{**V1_GATE, "kappa_rec": kr, "kappa_hist": kh} for kr, kh in itertools.product([0.0, 0.5, 1.0, 1.5], repeat=2)]
        centers = CALIBRATION_CENTERS
        scenarios = CALIBRATION_SCENARIOS
    return [
        {
            "phase": phase,
            "structure": structure,
            "gate": gate,
            "center": center,
            "seed": seed,
            "scenario": scenario,
            "out_dir": str(out_dir),
        }
        for structure, gate, center, seed, scenario in itertools.product(structures, gates, centers, SEEDS, scenarios)
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["development", "calibration"], required=True)
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    pre = preflight(args.phase)
    out_dir = ROOT / "results_v2_dev" / args.phase / "trajectories"
    jobs = make_jobs(args.phase, out_dir)
    manifest = {
        "schema": "ravm-dt-v2-execution-manifest-v1",
        "phase": args.phase,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "git_sha": subprocess_sha(),
        "workers": args.workers,
        "job_count": len(jobs),
        "stage_count": 24,
        "scientific_key": ["structure_id", "kappa_rec", "kappa_hist", "scenario_id", "center_id", "model_seed"],
        "preflight": pre,
        "jobs": [{k: v for k, v in job.items() if k != "out_dir"} | {"filename": output_name(job)} for job in jobs],
    }
    manifest_path = ROOT / "audits_v2_dev" / f"v2_{args.phase}_execution_manifest.json"
    if manifest_path.exists():
        frozen_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if scientific_manifest_view(frozen_manifest) != scientific_manifest_view(manifest):
            raise RuntimeError(f"frozen V2 {args.phase} execution manifest changed")
        manifest = frozen_manifest
    else:
        atomic_json(manifest_path, manifest)

    existing = sum(valid_output(out_dir / output_name(job), job) for job in jobs)
    pending = [job for job in jobs if not valid_output(out_dir / output_name(job), job)]
    start = time.time()
    completed = existing
    pids: set[int] = set()
    worker_runtimes: dict[str, dict] = {}
    status_path = ROOT / "results_v2_dev/execution_status.json"
    provenance_dir = ROOT / "results_v2_dev" / args.phase / "provenance"
    provenance_dir.mkdir(parents=True, exist_ok=True)
    runner_runtime = runtime_provenance()
    execution_provenance_path = ROOT / "audits_v2_dev" / f"v2_{args.phase}_execution_provenance.json"

    def write_execution_provenance(state: str) -> None:
        atomic_json(
            execution_provenance_path,
            {
                "state": state,
                "phase": args.phase,
                "scientific_implementation_commit": manifest["git_sha"],
                "execution_commit": subprocess_sha(),
                "manifest_sha256": sha256(manifest_path),
                "runner": runner_runtime,
                "workers": worker_runtimes,
                "heldout_accessed": False,
            },
        )

    def update_status(state: str, warning: str | None = None) -> None:
        elapsed = max(time.time() - start, 1e-9)
        newly_done = completed - existing
        throughput = newly_done / elapsed * 3600 if newly_done else None
        remaining = len(jobs) - completed
        eta = remaining / throughput * 3600 if throughput else None
        atomic_json(
            status_path,
            {
                "state": state,
                "phase": args.phase,
                "completed": completed,
                "expected": len(jobs),
                "remaining": remaining,
                "throughput_trajectories_per_hour": throughput,
                "eta_seconds": eta,
                "worker_pids": sorted(pids),
                "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "warning": warning,
                "heldout_accessed": False,
                "runner_runtime": runner_runtime,
                "worker_runtimes": worker_runtimes,
            },
        )

    write_execution_provenance("starting")
    update_status("running")
    print(f"V2 {args.phase}: existing={existing} pending={len(pending)} expected={len(jobs)}", flush=True)
    try:
        with cf.ProcessPoolExecutor(
            max_workers=args.workers,
            initializer=worker_initializer,
            initargs=(args.phase, str(provenance_dir)),
        ) as executor:
            futures = [executor.submit(execute_job, job) for job in pending]
            for future in cf.as_completed(futures):
                result = future.result()
                completed += 1
                pids.add(int(result["pid"]))
                worker_runtimes[str(result["pid"])] = result["runtime"]
                if completed % 10 == 0 or completed == len(jobs):
                    write_execution_provenance("running")
                    update_status("running")
                    elapsed = max(time.time() - start, 1e-9)
                    rate = (completed - existing) / elapsed * 3600
                    eta_h = (len(jobs) - completed) / rate if rate else float("inf")
                    print(f"V2 {args.phase} progress {completed}/{len(jobs)} rate={rate:.1f}/h eta={eta_h:.2f}h pids={sorted(pids)}", flush=True)
        update_status("phase_complete")
        write_execution_provenance("phase_complete")
        atomic_json(
            ROOT / "audits_v2_dev" / f"v2_{args.phase}_execution_complete.json",
            {
                "status": "PASS",
                "phase": args.phase,
                "completed": completed,
                "expected": len(jobs),
                "workers": args.workers,
                "worker_pids": sorted(pids),
                "elapsed_s": time.time() - start,
                "heldout_accessed": False,
                "manifest_sha256": sha256(manifest_path),
                "runner_runtime": runner_runtime,
                "worker_runtimes": worker_runtimes,
            },
        )
    except Exception as exc:
        update_status("failed", f"{type(exc).__name__}: {exc}")
        write_execution_provenance("failed")
        atomic_json(ROOT / "audits_v2_dev" / f"v2_{args.phase}_execution_failure.json", {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}", "completed": completed, "expected": len(jobs)})
        raise


def subprocess_sha() -> str:
    import subprocess

    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


if __name__ == "__main__":
    main()
