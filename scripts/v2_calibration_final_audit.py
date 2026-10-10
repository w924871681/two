"""Final integrity audit for the completed V2 decision-calibration outputs."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.protocol import ROOT
from scripts.v2_runner import output_name, sha256


EXPECTED_SCIENTIFIC_COMMIT = "7ae7fabd9a4e335e774fbcba2f38dfa8827bb8f3"
EXPECTED_RECOVERY_COMMIT = "5e455455884d6db42f3bfa2e3a8c43eb0032b621"
EXPECTED_CORE_SHA256 = "f27d0abb6fabb50453cb4e04684b8e7b5f99d27aca7ae1f1755990640f3ce024"
EXPECTED_RUNTIME = {
    "sys_executable": r"C:\Users\92487\anaconda3\envs\rcf-dti-py311\python.exe",
    "python_version": "3.11.15",
    "torch_version": "2.5.1+cu121",
    "torch_cuda_version": "12.1",
    "torch_cuda_available": True,
    "gpu_name": "NVIDIA GeForce RTX 3060 Laptop GPU",
}
REQUIRED_COLUMNS = {
    "run_id", "structure_id", "variant_family", "center_id", "model_seed",
    "stage", "drift_regime", "attack_type", "actual_attack_type",
    "attack_alpha", "attack_location", "parent_state_hash",
    "candidate_state_hash", "initial_state_hash", "commit", "harmful_commit",
    "downside", "beneficial_candidate", "deployed_service_mse",
    "deployed_service_mae", "attack_mask_hash", "update_data_hash",
    "verification_data_hash", "service_data_hash", "kappa_rec", "kappa_hist",
    "delta_imp", "delta_ret", "scenario_id", "execution_phase",
}


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    os.replace(tmp, path)


def git_blob_sha256(revision: str, path: str) -> str:
    payload = subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=ROOT)
    return hashlib.sha256(payload).hexdigest()


def runtime_matches(value: dict) -> bool:
    return all(value.get(key) == expected for key, expected in EXPECTED_RUNTIME.items())


def main() -> None:
    manifest_path = ROOT / "audits_v2_dev/v2_calibration_execution_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    complete = json.loads((ROOT / "audits_v2_dev/v2_calibration_execution_complete.json").read_text(encoding="utf-8"))
    provenance = json.loads((ROOT / "audits_v2_dev/v2_calibration_execution_provenance.json").read_text(encoding="utf-8"))
    recovery = json.loads((ROOT / "audits_v2_dev/v2_calibration_recovery_freeze_audit.json").read_text(encoding="utf-8"))
    seal_path = ROOT / "configs_v2_dev/v2_confirmatory_pool_manifest.json"
    seal_sha_path = ROOT / "configs_v2_dev/v2_confirmatory_pool_sha256.txt"
    folder = ROOT / "results_v2_dev/calibration/trajectories"

    expected_by_name = {output_name(job): job for job in manifest["jobs"]}
    paths = sorted(folder.glob("*.csv"))
    actual_by_name = {path.name: path for path in paths}
    missing = sorted(set(expected_by_name) - set(actual_by_name))
    unexpected = sorted(set(actual_by_name) - set(expected_by_name))
    duplicates = len(paths) - len(actual_by_name)
    invalid: list[dict] = []
    metadata_mismatches: list[dict] = []
    frames: list[pd.DataFrame] = []

    for name in sorted(set(expected_by_name) & set(actual_by_name)):
        path = actual_by_name[name]
        job = expected_by_name[name]
        if path.stat().st_size == 0:
            invalid.append({"file": name, "reason": "empty"})
            continue
        try:
            data = pd.read_csv(path)
        except Exception as exc:
            invalid.append({"file": name, "reason": f"parse: {type(exc).__name__}: {exc}"})
            continue
        if not REQUIRED_COLUMNS.issubset(data.columns):
            invalid.append({"file": name, "reason": "schema", "missing_columns": sorted(REQUIRED_COLUMNS - set(data.columns))})
            continue
        stages = data.stage.tolist()
        if len(data) != 24 or len(set(stages)) != 24 or sorted(stages) != list(range(1, 25)):
            invalid.append({"file": name, "reason": "stage_sequence", "rows": len(data), "stages": stages})
            continue
        expected = {
            "structure_id": job["structure"]["structure_id"],
            "variant_family": job["structure"]["family"],
            "center_id": job["center"],
            "model_seed": job["seed"],
            "scenario_id": job["scenario"]["scenario_id"],
            "kappa_rec": job["gate"]["kappa_rec"],
            "kappa_hist": job["gate"]["kappa_hist"],
            "execution_phase": "calibration",
        }
        bad = {}
        for column, expected_value in expected.items():
            values = data[column].drop_duplicates().tolist()
            if len(values) != 1 or values[0] != expected_value:
                bad[column] = {"expected": expected_value, "actual": values}
        if bad:
            metadata_mismatches.append({"file": name, "fields": bad})
        data = data.copy()
        data["_filename"] = name
        frames.append(data)

    all_rows = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    scientific_key = ["structure_id", "kappa_rec", "kappa_hist", "scenario_id", "center_id", "model_seed", "stage"]
    duplicate_rows = int(all_rows.duplicated(scientific_key).sum()) if len(all_rows) else 0
    immutable_hash_mismatches = 0
    if len(all_rows):
        identity = ["scenario_id", "center_id", "model_seed", "stage"]
        hash_columns = ["attack_mask_hash", "update_data_hash", "verification_data_hash", "service_data_hash"]
        immutable_hash_mismatches = int(
            (all_rows.groupby(identity)[hash_columns].nunique(dropna=False) > 1).any(axis=1).sum()
        )

    materialized = [
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

    archived = ROOT / "archive_v2/invalid_calibration_cpu_env_20260910_233929"
    archived_formal_paths = list(archived.rglob("*.csv")) if archived.exists() else []
    formal_resolved = {path.resolve() for path in paths}
    archive_overlap = [str(path) for path in archived_formal_paths if path.resolve() in formal_resolved]
    current_core = sha256(ROOT / "core/v2_engine.py")
    checks = {
        "expected_trajectory_count": len(expected_by_name) == 1920,
        "valid_trajectory_count": len(paths) == len(frames) == 1920,
        "missing_zero": not missing,
        "duplicate_zero": duplicates == 0 and duplicate_rows == 0,
        "unexpected_zero": not unexpected,
        "partial_invalid_zero": not invalid,
        "metadata_consistent": not metadata_mismatches,
        "immutable_data_and_attack_hashes_consistent_across_gate_configs": immutable_hash_mismatches == 0,
        "wrong_environment_outputs_not_in_formal_directory": not archive_overlap,
        "runner_runtime_correct": runtime_matches(complete["runner_runtime"]),
        "all_worker_runtimes_correct": len(complete["worker_runtimes"]) == 2 and all(runtime_matches(v) for v in complete["worker_runtimes"].values()),
        "scientific_implementation_commit_exact": provenance["scientific_implementation_commit"] == EXPECTED_SCIENTIFIC_COMMIT == manifest["git_sha"],
        "execution_recovery_commit_present": subprocess.check_output(["git", "cat-file", "-t", EXPECTED_RECOVERY_COMMIT], cwd=ROOT, text=True).strip() == "commit",
        "scientific_core_hash_unchanged": current_core == EXPECTED_CORE_SHA256 == git_blob_sha256(EXPECTED_SCIENTIFIC_COMMIT, "core/v2_engine.py"),
        "calibration_manifest_hash_unchanged": sha256(manifest_path) == complete["manifest_sha256"] == recovery["calibration_manifest_sha256"],
        "v1_frozen_artifacts_unchanged": not v1_mismatches,
        "confirmatory_manifest_hash_unchanged": sha256(seal_path) == seal_sha_path.read_text(encoding="utf-8").strip(),
        "heldout_access_false": provenance.get("heldout_accessed") is False,
        "heldout_materialized_false": not materialized,
    }
    report = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "expected": 1920,
        "valid": len(frames),
        "missing": len(missing),
        "duplicate": duplicates + duplicate_rows,
        "unexpected": len(unexpected),
        "partial_invalid": len(invalid),
        "wrong_environment_included": len(archive_overlap),
        "stage_rows": len(all_rows),
        "metadata_mismatches": metadata_mismatches[:20],
        "invalid_files": invalid[:20],
        "missing_files": missing[:20],
        "unexpected_files": unexpected[:20],
        "immutable_hash_mismatch_groups": immutable_hash_mismatches,
        "scientific_implementation_commit": EXPECTED_SCIENTIFIC_COMMIT,
        "execution_only_recovery_commit": EXPECTED_RECOVERY_COMMIT,
        "scientific_core_sha256": current_core,
        "calibration_manifest_sha256": sha256(manifest_path),
        "frozen_structure_sha256": recovery["frozen_structure_sha256"],
        "confirmatory_materialized": materialized,
        "heldout_accessed": False,
        "runner_runtime": complete["runner_runtime"],
        "worker_runtimes": complete["worker_runtimes"],
    }
    atomic_json(ROOT / "audits_v2_dev/v2_calibration_final_integrity.json", report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if report["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
