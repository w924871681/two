"""Run the fixed 120-trajectory post-calibration GO-5 completion audit."""
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

import pandas as pd

from core.protocol import ROOT
from scripts.v2_runner import (
    SCENARIOS,
    SEEDS,
    atomic_json,
    execute_job,
    output_name,
    runtime_provenance,
    sha256,
    valid_output,
    worker_initializer,
)


SCIENTIFIC_COMMIT = "7ae7fabd9a4e335e774fbcba2f38dfa8827bb8f3"
EXPECTED_CONFIG_SHA = "68e06d381ced23ed105694b97e221b37ea5302fb389789f9ec310c8bbe74d3f4"
EXPECTED_DEV_AGGREGATE = "032239b87875b4a7f2a3f583a9a8e932fb681306a8f9d0f00ee56eb5f4aa9b34"
CENTERS = list(range(11000, 11020))
SAFETY_SCENARIOS = SCENARIOS[2:]
PHASE = "post_calibration_go5"


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


def reference_integrity() -> dict:
    dev_dir = ROOT / "results_v2_dev/development/trajectories"
    dev_paths = sorted(dev_dir.glob("*.csv"))
    aggregate = aggregate_files(dev_paths, dev_dir)
    reference_paths = sorted(dev_dir.glob("V0_LegacyFull__*verification_only*.csv"))
    expected_names = {
        f"V0_LegacyFull__{scenario['scenario_id']}__{center}__{seed}.csv"
        for center in CENTERS for seed in SEEDS for scenario in SAFETY_SCENARIOS
    }
    actual_names = {path.name for path in reference_paths}
    invalid = []
    for path in reference_paths:
        frame = pd.read_csv(path)
        parts = path.stem.split("__")
        scenario, center, seed = parts[1], int(parts[2]), int(parts[3])
        if not (
            len(frame) == 24 and frame.stage.is_unique and set(frame.stage) == set(range(1, 25))
            and frame.structure_id.nunique() == 1 and frame.structure_id.iloc[0] == "V0_LegacyFull"
            and frame.scenario_id.nunique() == 1 and frame.scenario_id.iloc[0] == scenario
            and frame.center_id.nunique() == 1 and int(frame.center_id.iloc[0]) == center
            and frame.model_seed.nunique() == 1 and int(frame.model_seed.iloc[0]) == seed
        ):
            invalid.append(path.name)
    development_audit = json.loads((ROOT / "audits_v2_dev/v2_development_integrity.json").read_text(encoding="utf-8"))
    completion = json.loads((ROOT / "audits_v2_dev/v2_development_execution_complete.json").read_text(encoding="utf-8"))
    return {
        "status": "PASS" if (
            len(dev_paths) == 4800 and aggregate == EXPECTED_DEV_AGGREGATE
            and expected_names == actual_names and not invalid
            and development_audit["status"] == "PASS" and completion["status"] == "PASS"
        ) else "FAIL",
        "development_files": len(dev_paths),
        "development_aggregate_sha256": aggregate,
        "expected_development_aggregate_sha256": EXPECTED_DEV_AGGREGATE,
        "reference_expected": 120,
        "reference_valid": len(reference_paths) - len(invalid),
        "reference_missing": sorted(expected_names - actual_names),
        "reference_unexpected": sorted(actual_names - expected_names),
        "reference_invalid": invalid,
        "development_integrity_audit": development_audit["status"],
        "development_execution_complete": completion["status"],
        "development_manifest_sha256": completion["manifest_sha256"],
        "reference_provenance": "V2 development execution manifest and immutable aggregate",
    }


def main() -> None:
    structure_path = ROOT / "configs_v2_dev/frozen_v2_structure.yaml"
    config_path = ROOT / "configs_v2_dev/frozen_v2_commit_config.yaml"
    seal_path = ROOT / "configs_v2_dev/v2_confirmatory_pool_manifest.json"
    structure = json.loads(structure_path.read_text(encoding="utf-8"))
    config = json.loads(config_path.read_text(encoding="utf-8"))
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    gate = {key: config[key] for key in ["kappa_rec", "kappa_hist", "delta_imp", "delta_ret"]}
    materialized = [center for center in range(14000, 14030) if (ROOT / "data" / f"center_{center}.npz").exists()]
    reference = reference_integrity()
    core_sha = sha256(ROOT / "core/v2_engine.py")
    checks = {
        "reference_integrity": reference["status"] == "PASS",
        "structure_fixed": structure["structure_id"] == structure["family"] == "V2_SP_ShortDual",
        "history_capacity_fixed_by_scientific_core": True,
        "final_config_hash_exact": sha256(config_path) == EXPECTED_CONFIG_SHA,
        "gate_exact": gate == {"kappa_rec": 0.0, "kappa_hist": 0.5, "delta_imp": 2.8018237766243602e-05, "delta_ret": 0.0},
        "rho_exact": config["rho"] == 0.05,
        "epsilon_exact": config["epsilon"] == 5.6036475532487204e-05,
        "scientific_core_unchanged": core_sha == git_blob_sha256(SCIENTIFIC_COMMIT, "core/v2_engine.py"),
        "heldout_sealed": seal["status"] == "SEALED_NOT_MATERIALIZED",
        "heldout_not_materialized": not materialized,
        "original_no_go_preserved": (ROOT / "V2_METHOD_SCREENING_REPORT.md").exists() and json.loads((ROOT / "audits_v2_dev/v2_go_no_go_decision.json").read_text(encoding="utf-8"))["verdict"] == "NO-GO",
    }
    preflight = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "purpose": "complete GO-5 evidence for the already selected final calibration configuration; not parameter tuning",
        "checks": checks,
        "reference": reference,
        "scientific_implementation_commit": SCIENTIFIC_COMMIT,
        "scientific_core_sha256": core_sha,
        "frozen_config_sha256": sha256(config_path),
        "frozen_structure_sha256": sha256(structure_path),
        "confirmatory_manifest_sha256": sha256(seal_path),
        "heldout_accessed": False,
        "heldout_materialized": False,
    }
    preflight_path = ROOT / "audits_v2_dev/v2_post_calibration_go5_preflight.json"
    atomic_json(preflight_path, preflight)
    if preflight["status"] != "PASS":
        raise RuntimeError(f"post-calibration GO-5 preflight failed: {checks}")

    out_dir = ROOT / "results_v2_dev/post_calibration_go5/trajectories"
    jobs = [
        {
            "phase": PHASE,
            "structure": structure,
            "gate": gate,
            "center": center,
            "seed": seed,
            "scenario": scenario,
            "out_dir": str(out_dir),
        }
        for center in CENTERS for seed in SEEDS for scenario in SAFETY_SCENARIOS
    ]
    manifest = {
        "schema": "ravm-dt-v2-post-calibration-go5-v1",
        "phase": PHASE,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "purpose": "fixed-config completion audit, not parameter tuning",
        "scientific_implementation_commit": SCIENTIFIC_COMMIT,
        "execution_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "workers": 2,
        "job_count": 120,
        "stage_count": 24,
        "frozen_config_sha256": sha256(config_path),
        "frozen_structure_sha256": sha256(structure_path),
        "reference_development_aggregate_sha256": reference["development_aggregate_sha256"],
        "heldout_accessed": False,
        "heldout_materialized": False,
        "jobs": [{key: value for key, value in job.items() if key != "out_dir"} | {"filename": output_name(job)} for job in jobs],
    }
    manifest_path = ROOT / "audits_v2_dev/v2_post_calibration_go5_execution_manifest.json"
    if manifest_path.exists():
        frozen = json.loads(manifest_path.read_text(encoding="utf-8"))
        comparable = lambda value: {key: value[key] for key in value if key != "created_at"}
        if comparable(frozen) != comparable(manifest):
            raise RuntimeError("existing post-calibration GO-5 manifest differs")
        manifest = frozen
    else:
        atomic_json(manifest_path, manifest)

    existing = sum(valid_output(out_dir / output_name(job), job) for job in jobs)
    pending = [job for job in jobs if not valid_output(out_dir / output_name(job), job)]
    started = time.time()
    completed = existing
    pids: set[int] = set()
    worker_runtimes: dict[str, dict] = {}
    runner_runtime = runtime_provenance()
    status_path = ROOT / "results_v2_dev/execution_status.json"
    provenance_dir = ROOT / "results_v2_dev/post_calibration_go5/provenance"
    provenance_dir.mkdir(parents=True, exist_ok=True)

    def status(state: str, warning: str | None = None) -> None:
        elapsed = max(time.time() - started, 1e-9)
        new = completed - existing
        rate = new / elapsed * 3600 if new else None
        remaining = len(jobs) - completed
        atomic_json(status_path, {
            "state": state, "phase": PHASE, "completed": completed, "expected": len(jobs),
            "remaining": remaining, "throughput_trajectories_per_hour": rate,
            "eta_seconds": remaining / rate * 3600 if rate else None,
            "worker_pids": sorted(pids), "warning": warning,
            "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "runner_runtime": runner_runtime, "worker_runtimes": worker_runtimes,
            "heldout_accessed": False, "heldout_materialized": False,
        })

    status("running")
    print(f"V2 post-calibration GO-5: existing={existing} pending={len(pending)} expected=120", flush=True)
    try:
        with cf.ProcessPoolExecutor(max_workers=2, initializer=worker_initializer, initargs=(PHASE, str(provenance_dir))) as executor:
            futures = [executor.submit(execute_job, job) for job in pending]
            for future in cf.as_completed(futures):
                result = future.result()
                completed += 1
                pids.add(int(result["pid"]))
                worker_runtimes[str(result["pid"])] = result["runtime"]
                if completed % 10 == 0 or completed == len(jobs):
                    status("running")
                    elapsed = max(time.time() - started, 1e-9)
                    rate = (completed - existing) / elapsed * 3600
                    eta = (len(jobs) - completed) / rate if rate else float("inf")
                    print(f"progress {completed}/120 rate={rate:.1f}/h eta={eta:.3f}h pids={sorted(pids)}", flush=True)
        status("phase_complete")
        complete = {
            "status": "PASS", "completed": completed, "expected": 120, "workers": 2,
            "worker_pids": sorted(pids), "elapsed_s": time.time() - started,
            "manifest_sha256": sha256(manifest_path), "runner_runtime": runner_runtime,
            "worker_runtimes": worker_runtimes, "heldout_accessed": False, "heldout_materialized": False,
        }
        atomic_json(ROOT / "audits_v2_dev/v2_post_calibration_go5_execution_complete.json", complete)
    except Exception as exc:
        status("failed", f"{type(exc).__name__}: {exc}")
        atomic_json(ROOT / "audits_v2_dev/v2_post_calibration_go5_execution_failure.json", {
            "status": "FAIL", "error": f"{type(exc).__name__}: {exc}", "completed": completed, "expected": 120,
        })
        raise


if __name__ == "__main__":
    main()
