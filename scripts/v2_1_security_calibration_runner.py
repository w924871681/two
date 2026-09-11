"""Execute the frozen V2.1 security-aware calibration extension."""
from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.protocol import ROOT
from scripts.v2_runner import (
    SEEDS, atomic_json, execute_job, output_name, runtime_provenance, sha256,
    valid_output, worker_initializer,
)


SCIENTIFIC_COMMIT = "7ae7fabd9a4e335e774fbcba2f38dfa8827bb8f3"
CORE_SHA256 = "f27d0abb6fabb50453cb4e04684b8e7b5f99d27aca7ae1f1755990640f3ce024"
CALIBRATION_MANIFEST_SHA256 = "acec81a765610dad089066f74984366f8cc4295c2ae0bc94e0ae6c01d87d8fa0"
CONFIRMATORY_SEAL_SHA256 = "6883504751748ea38a3399986ebe3b527ff0f0624dd69e468a93fcebe9d683c6"
CENTERS = list(range(12000, 12020))
KAPPAS = [0.0, 0.5, 1.0, 1.5]
SCENARIOS = [
    {"scenario_id": "persistent_a010_verification_only", "kind": "persistent_bias", "alpha": 0.1, "location": "verification_only"},
    {"scenario_id": "replay_a010_verification_only", "kind": "replay", "alpha": 0.1, "location": "verification_only"},
]
EXPECTED_RUNTIME = {
    "sys_executable": r"C:\Users\92487\anaconda3\envs\rcf-dti-py311\python.exe",
    "python_version": "3.11.15",
    "torch_version": "2.5.1+cu121",
    "torch_cuda_version": "12.1",
    "torch_cuda_available": True,
    "gpu_name": "NVIDIA GeForce RTX 3060 Laptop GPU",
}


def aggregate_files(paths: list[Path], base: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: item.relative_to(base).as_posix()):
        relative = path.relative_to(base).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def git_blob_sha256(revision: str, path: str) -> str:
    payload = subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=ROOT)
    return hashlib.sha256(payload).hexdigest()


def runtime_matches(value: dict) -> bool:
    return all(value.get(key) == expected for key, expected in EXPECTED_RUNTIME.items())


def make_jobs(out_root: Path, structure: dict, base_gate: dict) -> list[dict]:
    reference = [
        {
            "phase": "v2_1_security_reference", "structure": {"structure_id": "V0_LegacyFull", "family": "V0_LegacyFull"},
            "gate": {**base_gate, "kappa_rec": 0.5, "kappa_hist": 0.0},
            "center": center, "seed": seed, "scenario": scenario,
            "out_dir": str(out_root / "v0_reference/trajectories"),
        }
        for center in CENTERS for seed in SEEDS for scenario in SCENARIOS
    ]
    grid = [
        {
            "phase": "calibration", "structure": structure,
            "gate": {**base_gate, "kappa_rec": kappa_rec, "kappa_hist": kappa_hist},
            "center": center, "seed": seed, "scenario": scenario,
            "out_dir": str(out_root / "v2_grid/trajectories"),
        }
        for kappa_rec in KAPPAS for kappa_hist in KAPPAS
        for center in CENTERS for seed in SEEDS for scenario in SCENARIOS
    ]
    assert len(reference) == 120 and len(grid) == 1920
    return reference + grid


def main() -> None:
    protocol_path = ROOT / "configs_v2_dev/v2_1_security_aware_calibration_protocol.json"
    structure_path = ROOT / "configs_v2_dev/frozen_v2_structure.yaml"
    frozen_gate_path = ROOT / "configs_v2_dev/frozen_v2_commit_config.yaml"
    calibration_manifest_path = ROOT / "audits_v2_dev/v2_calibration_execution_manifest.json"
    calibration_dir = ROOT / "results_v2_dev/calibration/trajectories"
    seal_path = ROOT / "configs_v2_dev/v2_confirmatory_pool_manifest.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    structure = json.loads(structure_path.read_text(encoding="utf-8"))
    frozen_gate = json.loads(frozen_gate_path.read_text(encoding="utf-8"))
    original_integrity = json.loads((ROOT / "audits_v2_dev/v2_calibration_final_integrity.json").read_text(encoding="utf-8"))
    original_decision = json.loads((ROOT / "audits_v2_dev/v2_go_no_go_decision.json").read_text(encoding="utf-8"))
    post_go5 = json.loads((ROOT / "audits_v2_dev/v2_post_calibration_go5_audit.json").read_text(encoding="utf-8"))
    materialized = [center for center in range(14000, 14030) if (ROOT / "data" / f"center_{center}.npz").exists()]
    calibration_paths = sorted(calibration_dir.glob("*.csv"))
    calibration_aggregate = aggregate_files(calibration_paths, calibration_dir)
    current_runtime = runtime_provenance()
    checks = {
        "protocol_frozen_before_execution": protocol["status"] == "FROZEN_BEFORE_V2_1_EXECUTION",
        "scientific_structure_fixed": structure["structure_id"] == structure["family"] == "V2_SP_ShortDual",
        "scientific_core_unchanged": sha256(ROOT / "core/v2_engine.py") == CORE_SHA256 == git_blob_sha256(SCIENTIFIC_COMMIT, "core/v2_engine.py"),
        "grid_exact": protocol["grid"]["kappa_rec"] == KAPPAS and protocol["grid"]["kappa_hist"] == KAPPAS,
        "risk_constants_exact": protocol["scientific_structure"]["rho"] == 0.05 and protocol["scientific_structure"]["epsilon"] == 5.6036475532487204e-05,
        "original_calibration_integrity_pass": original_integrity["status"] == "PASS" and original_integrity["valid"] == 1920,
        "original_calibration_manifest_unchanged": sha256(calibration_manifest_path) == CALIBRATION_MANIFEST_SHA256,
        "original_calibration_file_count": len(calibration_paths) == 1920,
        "post_calibration_no_go_preserved": original_decision["verdict"] == "NO-GO" and post_go5["resulting_overall_verdict"] == "NO-GO",
        "runtime_exact": runtime_matches(current_runtime),
        "confirmatory_seal_unchanged": sha256(seal_path) == CONFIRMATORY_SEAL_SHA256,
        "heldout_not_materialized": not materialized,
    }
    preflight = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "protocol_sha256": sha256(protocol_path),
        "scientific_implementation_commit": SCIENTIFIC_COMMIT,
        "scientific_core_sha256": sha256(ROOT / "core/v2_engine.py"),
        "existing_clean_mixed_trajectory_count": len(calibration_paths),
        "existing_clean_mixed_aggregate_sha256": calibration_aggregate,
        "existing_calibration_manifest_sha256": sha256(calibration_manifest_path),
        "runner_runtime": current_runtime,
        "heldout_accessed": False,
        "heldout_materialized": False,
    }
    preflight_path = ROOT / "audits_v2_dev/v2_1_security_aware_calibration_preflight.json"
    atomic_json(preflight_path, preflight)
    if preflight["status"] != "PASS":
        raise RuntimeError(f"V2.1 preflight failed: {[key for key, value in checks.items() if not value]}")

    base_gate = {key: frozen_gate[key] for key in ["delta_imp", "delta_ret"]}
    out_root = ROOT / "results_v2_dev/v2_1_security_calibration"
    jobs = make_jobs(out_root, structure, base_gate)
    manifest = {
        "schema": "ravm-dt-v2.1-security-calibration-execution-v1",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "protocol_sha256": sha256(protocol_path),
        "scientific_implementation_commit": SCIENTIFIC_COMMIT,
        "execution_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "workers": 2,
        "new_v2_expected": 1920,
        "v0_reference_expected": 120,
        "total_jobs": 2040,
        "stage_count": 24,
        "existing_clean_mixed_aggregate_sha256": calibration_aggregate,
        "confirmatory_seal_sha256": sha256(seal_path),
        "heldout_accessed": False,
        "heldout_materialized": False,
        "jobs": [
            {key: value for key, value in job.items() if key != "out_dir"}
            | {"output_group": "v0_reference" if job["structure"]["structure_id"] == "V0_LegacyFull" else "v2_grid", "filename": output_name(job)}
            for job in jobs
        ],
    }
    manifest_path = ROOT / "audits_v2_dev/v2_1_security_aware_calibration_execution_manifest.json"
    if manifest_path.exists():
        frozen = json.loads(manifest_path.read_text(encoding="utf-8"))
        comparable = lambda value: {key: value[key] for key in value if key != "created_at"}
        if comparable(frozen) != comparable(manifest):
            raise RuntimeError("frozen V2.1 execution manifest differs")
        manifest = frozen
    else:
        atomic_json(manifest_path, manifest)

    existing = sum(valid_output(Path(job["out_dir"]) / output_name(job), job) for job in jobs)
    pending = [job for job in jobs if not valid_output(Path(job["out_dir"]) / output_name(job), job)]
    completed = existing
    pids: set[int] = set()
    worker_runtimes: dict[str, dict] = {}
    started = time.time()
    status_path = ROOT / "results_v2_dev/execution_status.json"
    provenance_dir = out_root / "provenance"
    provenance_dir.mkdir(parents=True, exist_ok=True)

    def status(state: str, warning: str | None = None) -> None:
        elapsed = max(time.time() - started, 1e-9)
        new = completed - existing
        rate = new / elapsed * 3600 if new else None
        remaining = len(jobs) - completed
        atomic_json(status_path, {
            "state": state, "phase": "v2_1_security_aware_calibration",
            "completed": completed, "expected": len(jobs), "remaining": remaining,
            "new_v2_expected": 1920, "v0_reference_expected": 120,
            "throughput_trajectories_per_hour": rate,
            "eta_seconds": remaining / rate * 3600 if rate else None,
            "worker_pids": sorted(pids), "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "warning": warning, "heldout_accessed": False, "heldout_materialized": False,
            "runner_runtime": current_runtime, "worker_runtimes": worker_runtimes,
        })

    status("running")
    print(f"V2.1 security calibration: existing={existing} pending={len(pending)} expected=2040", flush=True)
    try:
        with cf.ProcessPoolExecutor(max_workers=2, initializer=worker_initializer, initargs=("v2_1_security_calibration", str(provenance_dir))) as executor:
            futures = [executor.submit(execute_job, job) for job in pending]
            for future in cf.as_completed(futures):
                result = future.result()
                completed += 1
                pids.add(int(result["pid"]))
                worker_runtimes[str(result["pid"])] = result["runtime"]
                if completed % 50 == 0 or completed == len(jobs):
                    status("running")
                    elapsed = max(time.time() - started, 1e-9)
                    rate = (completed - existing) / elapsed * 3600
                    eta = (len(jobs) - completed) / rate if rate else float("inf")
                    print(f"progress {completed}/2040 rate={rate:.1f}/h eta={eta:.3f}h pids={sorted(pids)}", flush=True)
        status("phase_complete")
        atomic_json(ROOT / "audits_v2_dev/v2_1_security_aware_calibration_execution_complete.json", {
            "status": "PASS", "completed": completed, "expected": 2040,
            "new_v2_expected": 1920, "v0_reference_expected": 120,
            "workers": 2, "worker_pids": sorted(pids), "elapsed_s": time.time() - started,
            "manifest_sha256": sha256(manifest_path), "protocol_sha256": sha256(protocol_path),
            "runner_runtime": current_runtime, "worker_runtimes": worker_runtimes,
            "heldout_accessed": False, "heldout_materialized": False,
        })
    except Exception as exc:
        status("failed", f"{type(exc).__name__}: {exc}")
        atomic_json(ROOT / "audits_v2_dev/v2_1_security_aware_calibration_execution_failure.json", {
            "status": "FAIL", "error": f"{type(exc).__name__}: {exc}",
            "completed": completed, "expected": 2040, "heldout_accessed": False,
        })
        raise


if __name__ == "__main__":
    main()
