"""Execution-only recovery preflight for the V2 calibration environment incident."""
from __future__ import annotations

import concurrent.futures as cf
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.protocol import ROOT
from core.v2_engine import V1_GATE, run_v2
from scripts.v2_runner import make_jobs, output_name, runtime_provenance, scientific_manifest_view, sha256


EXPECTED_INTERPRETER = Path(r"C:\Users\92487\anaconda3\envs\rcf-dti-py311\python.exe").resolve()
EXPECTED_TORCH = "2.5.1+cu121"
EXPECTED_CUDA = "12.1"
EXPECTED_GPU = "NVIDIA GeForce RTX 3060 Laptop GPU"
SCIENTIFIC_IMPLEMENTATION_COMMIT = "7ae7fabd9a4e335e774fbcba2f38dfa8827bb8f3"
ARCHIVE = ROOT / "archive_v2" / "invalid_calibration_cpu_env_20260910_233929"
FLOAT_TOLERANCE = 1e-12
NONSCIENTIFIC_COLUMNS = {
    "run_id",
    "candidate_update_time_s",
    "verification_time_s",
    "maintenance_time_s",
    "peak_gpu_memory_bytes",
}


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(payload, encoding="utf-8")
    os.replace(tmp, path)


def aggregate_files(paths: list[Path], base: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: item.relative_to(base).as_posix()):
        rel = path.relative_to(base).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def git_blob_sha256(revision: str, path: str) -> str:
    payload = subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=ROOT)
    return hashlib.sha256(payload).hexdigest()


def probe_worker(_: int) -> dict:
    time.sleep(1.0)
    return runtime_provenance()


def runtime_is_expected(value: dict) -> bool:
    return (
        Path(value["sys_executable"]).resolve() == EXPECTED_INTERPRETER
        and value["python_version"] == platform.python_version()
        and value["torch_version"] == EXPECTED_TORCH
        and value["torch_cuda_version"] == EXPECTED_CUDA
        and value["torch_cuda_available"] is True
        and value["gpu_name"] == EXPECTED_GPU
    )


def compare_frames(left: pd.DataFrame, right: pd.DataFrame) -> dict:
    columns = [column for column in left.columns if column not in NONSCIENTIFIC_COLUMNS]
    if columns != [column for column in right.columns if column not in NONSCIENTIFIC_COLUMNS]:
        return {"status": "FAIL", "reason": "scientific columns differ"}
    if len(left) != len(right):
        return {"status": "FAIL", "reason": "row counts differ"}

    max_abs_diff = 0.0
    mismatches: list[dict] = []
    exact_columns = []
    float_columns = []
    for column in columns:
        a = left[column]
        b = right[column]
        if pd.api.types.is_float_dtype(a.dtype) or pd.api.types.is_float_dtype(b.dtype):
            av = pd.to_numeric(a, errors="coerce").to_numpy(dtype=np.float64)
            bv = pd.to_numeric(b, errors="coerce").to_numpy(dtype=np.float64)
            finite = np.isfinite(av) & np.isfinite(bv)
            diff = float(np.max(np.abs(av[finite] - bv[finite]))) if finite.any() else 0.0
            max_abs_diff = max(max_abs_diff, diff)
            equal = bool(np.allclose(av, bv, rtol=0.0, atol=FLOAT_TOLERANCE, equal_nan=True))
            float_columns.append(column)
        else:
            equal = bool(a.fillna("<NA>").astype(str).equals(b.fillna("<NA>").astype(str)))
            exact_columns.append(column)
        if not equal:
            mismatches.append({"column": column})
    return {
        "status": "PASS" if not mismatches else "FAIL",
        "rows": len(left),
        "exact_columns": exact_columns,
        "float_columns": float_columns,
        "max_abs_diff": max_abs_diff,
        "tolerance": FLOAT_TOLERANCE,
        "mismatches": mismatches,
    }


def freeze_audit() -> dict:
    structure_path = ROOT / "configs_v2_dev/frozen_v2_structure.yaml"
    selection_path = ROOT / "audits_v2_dev/v2_structural_selection.json"
    development_complete_path = ROOT / "audits_v2_dev/v2_development_execution_complete.json"
    development_manifest_path = ROOT / "audits_v2_dev/v2_development_execution_manifest.json"
    calibration_manifest_path = ROOT / "audits_v2_dev/v2_calibration_execution_manifest.json"
    archived_manifest_path = ARCHIVE / "audits_v2_dev/v2_calibration_execution_manifest.json"
    seal_path = ROOT / "configs_v2_dev/v2_confirmatory_pool_manifest.json"
    seal_sha_path = ROOT / "configs_v2_dev/v2_confirmatory_pool_sha256.txt"

    structure = json.loads(structure_path.read_text(encoding="utf-8"))
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    development_complete = json.loads(development_complete_path.read_text(encoding="utf-8"))
    development_manifest = json.loads(development_manifest_path.read_text(encoding="utf-8"))
    calibration_manifest = json.loads(calibration_manifest_path.read_text(encoding="utf-8"))
    seal = json.loads(seal_path.read_text(encoding="utf-8"))

    development_files = list((ROOT / "results_v2_dev/development/trajectories").glob("*.csv"))
    development_hash_before = aggregate_files(development_files, ROOT / "results_v2_dev/development/trajectories")
    current_jobs = make_jobs("calibration", ROOT / "results_v2_dev/calibration/trajectories")
    current_manifest = {
        "schema": calibration_manifest["schema"],
        "phase": "calibration",
        "workers": 2,
        "job_count": len(current_jobs),
        "stage_count": 24,
        "scientific_key": calibration_manifest["scientific_key"],
        "preflight": calibration_manifest["preflight"],
        "jobs": [{k: v for k, v in job.items() if k != "out_dir"} | {"filename": output_name(job)} for job in current_jobs],
    }
    manifest_science_equal = scientific_manifest_view(calibration_manifest) == scientific_manifest_view(current_manifest)

    gate_pairs = sorted({(job["gate"]["kappa_rec"], job["gate"]["kappa_hist"]) for job in calibration_manifest["jobs"]})
    centers = sorted({job["center"] for job in calibration_manifest["jobs"]})
    seeds = sorted({job["seed"] for job in calibration_manifest["jobs"]})
    scenarios = sorted({job["scenario"]["scenario_id"] for job in calibration_manifest["jobs"]})
    confirmatory_materialized = [
        str(ROOT / "data" / f"center_{center}.npz")
        for center in range(14000, 14030)
        if (ROOT / "data" / f"center_{center}.npz").exists()
    ]

    v1_manifest = json.loads((ROOT / "configs_v2_dev/v1_frozen_artifact_manifest.json").read_text(encoding="utf-8"))
    v1_mismatches = []
    for item in v1_manifest["files"]:
        path = ROOT / item["path"]
        if not path.exists() or path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
            v1_mismatches.append(item["path"])

    core_current = sha256(ROOT / "core/v2_engine.py")
    core_frozen = git_blob_sha256(SCIENTIFIC_IMPLEMENTATION_COMMIT, "core/v2_engine.py")
    checks = {
        "structural_winner_unchanged": structure["structure_id"] == selection["winner"] == "V2_SP_ShortDual",
        "development_complete": development_complete["completed"] == development_complete["expected"] == 4800,
        "development_manifest_hash_unchanged": sha256(development_manifest_path) == development_complete["manifest_sha256"],
        "development_file_count_unchanged": len(development_files) == 4800,
        "scientific_core_hash_unchanged": core_current == core_frozen,
        "scientific_implementation_commit_unchanged": calibration_manifest["git_sha"] == SCIENTIFIC_IMPLEMENTATION_COMMIT,
        "calibration_manifest_bytes_unchanged": sha256(calibration_manifest_path) == sha256(archived_manifest_path),
        "calibration_scientific_manifest_unchanged": manifest_science_equal,
        "calibration_grid_unchanged": len(gate_pairs) == 16 and gate_pairs == [(a, b) for a in [0.0, 0.5, 1.0, 1.5] for b in [0.0, 0.5, 1.0, 1.5]],
        "calibration_pool_unchanged": centers == list(range(12000, 12020)),
        "model_seeds_unchanged": seeds == [7311, 7312, 7313],
        "calibration_scenarios_unchanged": scenarios == ["clean", "mixed_a010_both"],
        "calibration_job_count_unchanged": calibration_manifest["job_count"] == len(calibration_manifest["jobs"]) == 1920,
        "rho_unchanged": structure["rho"] == selection["rho"] == 0.05,
        "epsilon_unchanged": structure["epsilon"] == selection["epsilon"] == 5.6036475532487204e-05,
        "v1_frozen_artifacts_unchanged": not v1_mismatches,
        "heldout_access_false": calibration_manifest["preflight"]["heldout_materialized"] is False,
        "heldout_materialized_false": not confirmatory_materialized and seal["status"] == "SEALED_NOT_MATERIALIZED",
        "confirmatory_pool_manifest_hash_unchanged": sha256(seal_path) == seal_sha_path.read_text(encoding="utf-8").strip(),
        "wrong_environment_formal_outputs_absent": not (ROOT / "results_v2_dev/calibration").exists(),
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "development_trajectory_aggregate_sha256": development_hash_before,
        "development_trajectory_files": len(development_files),
        "scientific_core_sha256": core_current,
        "scientific_implementation_commit": SCIENTIFIC_IMPLEMENTATION_COMMIT,
        "calibration_manifest_sha256": sha256(calibration_manifest_path),
        "frozen_structure_sha256": sha256(structure_path),
        "calibration_factorization": {
            "centers": centers,
            "seeds": seeds,
            "scenarios": scenarios,
            "gate_pairs": gate_pairs,
            "expected": len(calibration_manifest["jobs"]),
        },
        "v1_mismatches": v1_mismatches,
        "confirmatory_materialized": confirmatory_materialized,
    }


def main() -> None:
    runner_runtime = runtime_provenance()
    if not runtime_is_expected(runner_runtime):
        raise RuntimeError(f"wrong preflight runtime: {runner_runtime}")

    frozen = freeze_audit()
    atomic_json(ROOT / "audits_v2_dev/v2_calibration_recovery_freeze_audit.json", frozen)
    if frozen["status"] != "PASS":
        raise RuntimeError("V2 calibration recovery freeze audit failed")

    with cf.ProcessPoolExecutor(max_workers=2) as executor:
        worker_values = list(executor.map(probe_worker, range(2)))
    worker_pids = {value["pid"] for value in worker_values}
    worker_check = len(worker_pids) == 2 and all(runtime_is_expected(value) for value in worker_values)

    structure = json.loads((ROOT / "configs_v2_dev/frozen_v2_structure.yaml").read_text(encoding="utf-8"))
    run_id = "v2_calibration_recovery_preflight_clean_11000_7311"
    rows_a = run_v2(11000, 7311, structure, "clean", 0.0, "both", V1_GATE, stages=24, run_id=run_id)
    rows_b = run_v2(11000, 7311, structure, "clean", 0.0, "both", V1_GATE, stages=24, run_id=run_id)
    frame_a = pd.DataFrame(rows_a)
    frame_b = pd.DataFrame(rows_b)
    for frame in [frame_a, frame_b]:
        frame["scenario_id"] = "clean"
        frame["execution_phase"] = "development"

    scratch_dir = ROOT / "scratch_v2/calibration_recovery_preflight"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    frame_a.to_csv(scratch_dir / "repeat_a.csv", index=False, na_rep="NA")
    frame_b.to_csv(scratch_dir / "repeat_b.csv", index=False, na_rep="NA")
    reference_path = ROOT / "results_v2_dev/development/trajectories/V2_SP_ShortDual__clean__11000__7311.csv"
    reference = pd.read_csv(reference_path)
    repeated = compare_frames(frame_a, frame_b)
    development_consistency = compare_frames(frame_a, reference)

    expected_schema = list(reference.columns)
    schema_ok = list(frame_a.columns) == expected_schema
    development_files_after = list((ROOT / "results_v2_dev/development/trajectories").glob("*.csv"))
    development_hash_after = aggregate_files(development_files_after, ROOT / "results_v2_dev/development/trajectories")
    heldout = [
        str(ROOT / "data" / f"center_{center}.npz")
        for center in range(14000, 14030)
        if (ROOT / "data" / f"center_{center}.npz").exists()
    ]

    checks = {
        "full_24_stage_lifecycle": len(frame_a) == 24 and set(frame_a["stage"]) == set(range(1, 25)) and frame_a["stage"].is_unique,
        "same_key_reproducible": repeated["status"] == "PASS",
        "child_workers_inherit_exact_runtime": worker_check,
        "heldout_access_false": not heldout,
        "scientific_schema_intact": schema_ok,
        "development_implementation_consistency": development_consistency["status"] == "PASS",
        "development_results_unchanged_during_preflight": development_hash_after == frozen["development_trajectory_aggregate_sha256"],
    }
    audit = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "runner_runtime": runner_runtime,
        "worker_runtimes": worker_values,
        "repeat_comparison": repeated,
        "development_consistency": development_consistency,
        "reference_trajectory": str(reference_path.relative_to(ROOT)),
        "scratch_outputs": [
            str((scratch_dir / "repeat_a.csv").relative_to(ROOT)),
            str((scratch_dir / "repeat_b.csv").relative_to(ROOT)),
        ],
        "heldout_materialized": heldout,
        "scientific_implementation_commit": SCIENTIFIC_IMPLEMENTATION_COMMIT,
        "scientific_core_sha256": frozen["scientific_core_sha256"],
    }
    atomic_json(ROOT / "audits_v2_dev/v2_calibration_recovery_preflight.json", audit)
    print(json.dumps(audit, indent=2, ensure_ascii=False, allow_nan=False), flush=True)
    if audit["status"] != "PASS":
        raise RuntimeError("V2 calibration recovery preflight failed")


if __name__ == "__main__":
    main()
