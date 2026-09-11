"""Freeze the minimal V2 final method, execution manifest, and analysis plan pre-access."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import torch

from core.protocol import ROOT


SCIENTIFIC_COMMIT = "7ae7fabd9a4e335e774fbcba2f38dfa8827bb8f3"
V1_COMMIT = "0a21cf6f7bdf068ab64b8e5ef0f5e2e8bfb95e2e"
V21_PROTOCOL_SHA = "dacef8ac0081b7ace6e6c12ffb26fb98fa931ec498a62cf9620021d95d684b78"
POOL_SEAL_SHA = "6883504751748ea38a3399986ebe3b527ff0f0624dd69e468a93fcebe9d683c6"
CORE_SHA = "f27d0abb6fabb50453cb4e04684b8e7b5f99d27aca7ae1f1755990640f3ce024"
CENTERS = list(range(14000, 14030))
SEEDS = [7311, 7312, 7313]
REGIMES = ["stationary", "gradual", "abrupt", "recurring"]
METHODS = ["Final_V2_SP_ShortDual", "V1_LegacyFull"]
STREAMS = [
    {"scenario_id": "clean", "kind": "clean", "alpha": 0.0, "attack_location": "both"},
    {"scenario_id": "mixed_a010_both", "kind": "mixed", "alpha": 0.1, "attack_location": "both"},
    {"scenario_id": "persistent_a010_verification_only", "kind": "persistent_bias", "alpha": 0.1, "attack_location": "verification_only"},
    {"scenario_id": "replay_a010_verification_only", "kind": "replay", "alpha": 0.1, "attack_location": "verification_only"},
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    os.replace(tmp, path)


def git_blob_sha256(revision: str, path: str) -> str:
    payload = subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=ROOT)
    return hashlib.sha256(payload).hexdigest()


def runtime() -> dict:
    available = bool(torch.cuda.is_available())
    return {
        "sys_executable": str(Path(sys.executable).resolve()), "python_version": platform.python_version(),
        "torch_version": torch.__version__, "torch_cuda_version": torch.version.cuda,
        "torch_cuda_available": available, "gpu_name": torch.cuda.get_device_name(0) if available else None,
        "platform": platform.platform(),
    }


def write_artifact(path: Path, value: dict) -> str:
    atomic_json(path, value)
    digest = sha256(path)
    path.with_suffix(path.suffix + ".sha256").write_text(digest + "\n", encoding="ascii")
    return digest


def main() -> None:
    out = ROOT / "configs_v2_final"
    audit_dir = ROOT / "audits_v2_final"
    out.mkdir(exist_ok=True)
    audit_dir.mkdir(exist_ok=True)
    sealed = json.loads((ROOT / "configs_v2_dev/v2_confirmatory_pool_manifest.json").read_text(encoding="utf-8"))
    v21 = json.loads((ROOT / "audits_v2_dev/v2_1_security_aware_calibration.json").read_text(encoding="utf-8"))
    selected = v21["selection"]["selected"]
    original_config = json.loads((ROOT / "configs_v2_dev/frozen_v2_commit_config.yaml").read_text(encoding="utf-8"))
    dev = json.loads((ROOT / "audits_v2_dev/v2_development_integrity.json").read_text(encoding="utf-8"))
    calibration = json.loads((ROOT / "audits_v2_dev/v2_calibration_final_integrity.json").read_text(encoding="utf-8"))
    post_go5 = json.loads((ROOT / "audits_v2_dev/v2_post_calibration_go5_audit.json").read_text(encoding="utf-8"))
    v21_complete = json.loads((ROOT / "audits_v2_dev/v2_1_security_aware_calibration_execution_complete.json").read_text(encoding="utf-8"))
    v1_manifest = json.loads((ROOT / "configs_v2_dev/v1_frozen_artifact_manifest.json").read_text(encoding="utf-8"))
    env = runtime()
    materialized = [center for center in CENTERS if (ROOT / "data" / f"center_{center}.npz").exists()]
    existing_results = list((ROOT / "results_v2_final").rglob("*.csv")) if (ROOT / "results_v2_final").exists() else []
    gates = v21["mechanical_go_recheck"]
    checks = {
        "development_4800_pass": dev["status"] == "PASS" and dev["trajectory_files"] == 4800,
        "original_calibration_1920_pass": calibration["status"] == "PASS" and calibration["valid"] == 1920,
        "post_calibration_go5_provenance_preserved": post_go5["status"] == "PASS" and post_go5["resulting_overall_verdict"] == "NO-GO",
        "v21_execution_2040_pass": v21_complete["status"] == "PASS" and v21_complete["new_v2_expected"] == 1920 and v21_complete["v0_reference_expected"] == 120,
        "v21_decision_go": v21["status"] == "PASS" and v21["decision"] == "V2_1_CALIBRATION_GO",
        "go1_through_go6_pass": set(gates) == {"GO-1", "GO-2", "GO-3", "GO-4", "GO-5", "GO-6"} and all(value == "PASS" for value in gates.values()),
        "selected_structure_exact": selected["arm_id"] == "kr0_kh0.5" and selected["kappa_rec"] == 0.0 and selected["kappa_hist"] == 0.5,
        "selected_config_exact": original_config["kappa_rec"] == 0.0 and original_config["kappa_hist"] == 0.5 and original_config["delta_imp"] == 2.8018237766243602e-05 and original_config["delta_ret"] == 0.0,
        "scientific_core_unchanged": sha256(ROOT / "core/v2_engine.py") == CORE_SHA == git_blob_sha256(SCIENTIFIC_COMMIT, "core/v2_engine.py"),
        "v1_commit_and_tag_exact": v1_manifest["v1_final_commit"] == V1_COMMIT and subprocess.check_output(["git", "rev-list", "-n", "1", "v1-final-frozen"], cwd=ROOT, text=True).strip() == V1_COMMIT,
        "v1_frozen_config_hashes_exact": sha256(ROOT / "configs/frozen_candidate_config.yaml") == "4a9655cf427f41bb321dc5237008fa795f1fb3437c979206fd4784810bca74ea" and sha256(ROOT / "configs/frozen_commit_config.yaml") == "1da5f249d1a8c41afcc7d49f2bd30d288e2cdabd220b7840cfc0a3903bc9bf3a",
        "runtime_exact": env["python_version"] == "3.11.15" and env["torch_version"] == "2.5.1+cu121" and env["torch_cuda_version"] == "12.1" and env["torch_cuda_available"] and env["gpu_name"] == "NVIDIA GeForce RTX 3060 Laptop GPU",
        "pool_manifest_sealed": sealed["status"] == "SEALED_NOT_MATERIALIZED" and sha256(ROOT / "configs_v2_dev/v2_confirmatory_pool_manifest.json") == POOL_SEAL_SHA,
        "fresh_data_absent": not materialized,
        "fresh_results_absent": not existing_results,
        "v21_protocol_hash_exact": sha256(ROOT / "configs_v2_dev/v2_1_security_aware_calibration_protocol.json") == V21_PROTOCOL_SHA,
    }
    if not all(checks.values()):
        atomic_json(audit_dir / "final_method_freeze_audit.json", {"status": "FINAL_FREEZE_PRECHECK_FAILED", "checks": checks, "heldout_accessed": False, "heldout_materialized": False})
        atomic_json(ROOT / "results_v2_dev/execution_status.json", {"status": "FINAL_FREEZE_PRECHECK_FAILED", "failed_checks": [key for key, value in checks.items() if not value], "heldout_accessed": False, "heldout_materialized": False})
        raise SystemExit(2)

    created = dt.datetime.now(dt.timezone.utc).isoformat()
    method = {
        "schema": "ravm-dt-v2-final-method-v1", "status": "FINAL_METHOD_FROZEN",
        "created_at": created, "method_id": "Final_V2_SP_ShortDual", "structure": "V2_SP_ShortDual",
        "candidate": "SinglePath", "adaptation_steps": 50, "adaptation_loss": "mse", "history_capacity": 12,
        "backbone": "GRU", "forecast_horizon": 1, "scientific_implementation_commit": SCIENTIFIC_COMMIT,
        "scientific_core_sha256": CORE_SHA, "no_further_scientific_modification": True,
    }
    commit_config = {
        "schema": "ravm-dt-v2-final-commit-config-v1", "status": "FINAL_CONFIG_FROZEN",
        "created_at": created, "kappa_rec": 0.0, "kappa_hist": 0.5,
        "delta_imp": 2.8018237766243602e-05, "delta_ret": 0.0,
        "rho": 0.05, "epsilon": 5.6036475532487204e-05,
        "selection_source": "V2_1_CALIBRATION_GO", "selection_audit_sha256": sha256(ROOT / "audits_v2_dev/v2_1_security_aware_calibration.json"),
    }
    environment = {"schema": "ravm-dt-v2-final-environment-v1", "status": "FROZEN", "created_at": created, **env}
    provenance = {
        "schema": "ravm-dt-v2-final-provenance-v1", "status": "FROZEN_PRE_HELDOUT", "created_at": created,
        "freeze_source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "scientific_implementation_commit": SCIENTIFIC_COMMIT, "v1_final_commit": V1_COMMIT,
        "v1_artifact_aggregate_sha256": v1_manifest["aggregate_sha256"],
        "v21_protocol_sha256": V21_PROTOCOL_SHA, "v21_decision_audit_sha256": sha256(ROOT / "audits_v2_dev/v2_1_security_aware_calibration.json"),
        "confirmatory_pool_seal_sha256": POOL_SEAL_SHA, "model_seeds": SEEDS,
        "lifecycle_stages": 24, "window_length": 96, "data_seed": 7311, "attack_seed": 9417,
        "source_checkpoints": {str(seed): {"path": f"checkpoints/source_GRU_H1_{seed}.pt", "sha256": sha256(ROOT / f"checkpoints/source_GRU_H1_{seed}.pt")} for seed in SEEDS},
        "heldout_accessed": False, "heldout_materialized": False,
    }
    method_sha = write_artifact(out / "frozen_v2_final_method.yaml", method)
    config_sha = write_artifact(out / "frozen_v2_final_commit_config.yaml", commit_config)
    env_sha = write_artifact(out / "frozen_v2_final_environment.json", environment)
    provenance_sha = write_artifact(out / "frozen_v2_final_provenance.json", provenance)

    center_regimes = {str(center): REGIMES[(center - CENTERS[0]) % 4] for center in CENTERS}
    jobs = []
    for center in CENTERS:
        for seed in SEEDS:
            for stream in STREAMS:
                for method_id in METHODS:
                    jobs.append({
                        "method_id": method_id, "center_id": center, "model_seed": seed,
                        "stream": stream, "analysis_scenario": center_regimes[str(center)] if stream["scenario_id"] == "clean" else stream["scenario_id"],
                        "stages": 24,
                        "filename": f"{method_id}__{stream['scenario_id']}__{center}__{seed}.csv",
                    })
    assert len(jobs) == 720
    manifest = {
        "schema": "ravm-dt-v2-minimal-confirmatory-manifest-v1", "status": "MINIMAL_CONFIRMATORY_MANIFEST_FROZEN",
        "created_at": created, "methods": METHODS, "centers": CENTERS, "model_seeds": SEEDS,
        "center_regime_assignment": center_regimes, "assignment_rule": "REGIMES[(center_id-14000) % 4]",
        "streams": STREAMS, "expected_trajectories": 720, "stages_per_trajectory": 24,
        "scientific_key": ["method_id", "center_id", "model_seed", "scenario_id"],
        "method_sha256": method_sha, "config_sha256": config_sha, "environment_sha256": env_sha, "provenance_sha256": provenance_sha,
        "pool_generator": sealed["generator"], "jobs": jobs,
        "heldout_accessed": False, "heldout_materialized": False,
    }
    manifest_sha = write_artifact(out / "frozen_v2_minimal_confirmatory_manifest.json", manifest)
    plan = {
        "schema": "ravm-dt-v2-minimal-analysis-plan-v1", "status": "ANALYSIS_PLAN_FROZEN", "created_at": created,
        "evidence_pools_separate": True, "statistical_unit": "center", "paired": True,
        "bootstrap": {"replicates": 4000, "seed": 2904, "interval": "percentile 95%", "seed_handling": "average seeds within center"},
        "primary_endpoint": {
            "metric": "balanced lifecycle MSE", "scenarios_equal_weight": ["stationary", "gradual", "abrupt", "recurring", "mixed_a010_both"],
            "implementation": "scripts/v2_go_no_go.py::stratified_paired_ci", "implementation_sha256": sha256(ROOT / "scripts/v2_go_no_go.py"),
            "success": "paired CI upper bound < 0",
        },
        "scenario_metrics": ["lifecycle_mse", "lifecycle_mae", "harmful_commit_rate", "average_downside", "conditional_harmful_rate", "beneficial_commit_recall", "commit_rate", "maximum_retain_streak"],
        "benign_additional_metrics": ["post_drift_excess_loss_area_relative_to_v1", "recovery_time_to_within_105pct_v1_for_two_stages", "censored_recovery"],
        "recovery_scope_note": "Minimal two-method design cannot reproduce the earlier Frozen/Always-FT reference envelope. Fresh recovery is frozen here as a V2-to-V1 relative diagnostic and is never pooled with development recovery estimates.",
        "absolute_risk": {"scenarios": ["mixed_a010_both", "persistent_a010_verification_only", "replay_a010_verification_only"], "harmful_rho": 0.05, "downside_epsilon": 5.6036475532487204e-05},
        "relative_verification_safety": "persistent/replay harmful and downside paired CIs must not be wholly above zero",
        "benign_regression": "no stationary/gradual/abrupt/recurring lifecycle-MSE paired CI wholly above zero",
        "plasticity_success": "at least one of beneficial recall CI wholly above zero, relative excess-loss-area CI wholly below zero, censored-recovery CI wholly below zero, or recovery-time CI wholly below zero",
        "verdicts": {
            "CONFIRMED": "primary CI upper<0; all absolute risks pass; verification relative safety passes; no benign-regime adverse MSE CI; at least one plasticity endpoint clearly favorable",
            "PARTIALLY_CONFIRMED": "all absolute risks pass, primary point is favorable, but a required relative/plasticity/regime condition is inconclusive or locally adverse",
            "NOT_CONFIRMED": "any absolute risk fails; primary MSE CI wholly adverse; or at least two benign-regime lifecycle-MSE CIs are wholly adverse while the primary point estimate is non-favorable (>=0)",
        },
        "replay_discordance": {"development": "adverse harmful/downside paired CI", "calibration": "acceptable relative safety", "fresh_rule": "A if either fresh harmful/downside CI is wholly adverse; B if neither is wholly adverse and both point differences are <=0; C otherwise"},
        "no_partial_analysis": True, "no_heldout_tuning": True, "other_baselines": "prior/development/V1 evidence only; no fresh paired claims",
    }
    plan_sha = write_artifact(out / "frozen_v2_minimal_analysis_plan.json", plan)
    freeze_audit = {
        "status": "PASS", "state": "ANALYSIS_PLAN_FROZEN", "created_at": created, "checks": checks,
        "artifact_hashes": {
            "frozen_v2_final_method.yaml": method_sha, "frozen_v2_final_commit_config.yaml": config_sha,
            "frozen_v2_final_environment.json": env_sha, "frozen_v2_final_provenance.json": provenance_sha,
            "frozen_v2_minimal_confirmatory_manifest.json": manifest_sha, "frozen_v2_minimal_analysis_plan.json": plan_sha,
        },
        "heldout_accessed": False, "heldout_materialized": False, "existing_fresh_results": [],
    }
    atomic_json(audit_dir / "final_method_freeze_audit.json", freeze_audit)
    atomic_json(audit_dir / "final_manifest_freeze_audit.json", {
        "status": "PASS", "expected": 720, "unique_keys": len({(j["method_id"], j["center_id"], j["model_seed"], j["stream"]["scenario_id"]) for j in jobs}),
        "methods": METHODS, "center_regime_assignment": center_regimes,
        "manifest_sha256": manifest_sha, "analysis_plan_sha256": plan_sha,
        "heldout_accessed": False, "heldout_materialized": False,
    })
    atomic_json(ROOT / "results_v2_dev/execution_status.json", {
        "status": "ANALYSIS_PLAN_FROZEN", "phase": "v2_final_preheldout_freeze", "expected": 720,
        "manifest_sha256": manifest_sha, "analysis_plan_sha256": plan_sha,
        "heldout_accessed": False, "heldout_materialized": False,
    })
    print(json.dumps({"status": "PASS", "manifest_sha256": manifest_sha, "analysis_plan_sha256": plan_sha, "heldout_accessed": False}, indent=2))


if __name__ == "__main__":
    main()
