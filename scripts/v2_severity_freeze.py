"""Freeze and audit the Final-V2 robustness-severity execution matrix."""
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

import pandas as pd
import torch

from core.protocol import ROOT
from scripts.v2_runner import atomic_json

CENTERS = list(range(14000, 14030))
SEEDS = [7311, 7312, 7313]
METHODS = ["Proposed", "Always-FT", "ER", "Huber-FT"]
BASELINES = METHODS[1:]
NEW_ALPHAS = [0.05, 0.20]
STREAM_TEMPLATES = [
    ("mixed", "both"),
    ("persistent_bias", "verification_only"),
    ("replay", "verification_only"),
]
EXPECTED_NEW = 2160
V2_CORE_SHA = "f27d0abb6fabb50453cb4e04684b8e7b5f99d27aca7ae1f1755990640f3ce024"
V1_CORE_SHA = "b143046aac84e62ab098c5cb5f1666dafe4fe24419ea8b164acdf2c8cbee23a6"
FINAL_CONFIG_SHA = "7275a287ee4a1f4602ed0a10a67362a1a61ffa398848d4529669b0584a127d13"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def runtime() -> dict:
    available = bool(torch.cuda.is_available())
    return {
        "sys_executable": str(Path(sys.executable).resolve()),
        "python_version": platform.python_version(),
        "torch_version": torch.__version__,
        "torch_cuda_version": torch.version.cuda,
        "torch_cuda_available": available,
        "gpu_name": torch.cuda.get_device_name(0) if available else None,
    }


def scenario(kind: str, alpha: float, location: str) -> dict:
    short = f"a{int(round(alpha * 100)):03d}"
    prefix = "persistent" if kind == "persistent_bias" else kind
    return {"scenario_id": f"{prefix}_{short}_{location}", "kind": kind, "alpha": alpha, "attack_location": location}


def source_path(method: str, center: int, seed: int, scenario_id: str) -> Path:
    if method == "Proposed":
        return ROOT / "results_v2_final/trajectories" / f"Final_V2_SP_ShortDual__{scenario_id}__{center}__{seed}.csv"
    return ROOT / "results_v2_final_baselines/trajectories" / f"{method}__{scenario_id}__{center}__{seed}.csv"


def main() -> None:
    audit_dir = ROOT / "audits_v2_severity"
    audit_dir.mkdir(exist_ok=True)
    results = ROOT / "results_v2_severity"
    old = list((results / "trajectories").glob("*.csv")) if (results / "trajectories").exists() else []
    rt = runtime()
    final_integrity = json.loads((ROOT / "audits_v2_final/final_execution_integrity_audit.json").read_text(encoding="utf-8"))
    baseline_integrity = json.loads((ROOT / "audits_v2_final_baselines/baseline_execution_integrity_audit.json").read_text(encoding="utf-8"))
    frozen_cfg = ROOT / "configs_v2_final/frozen_v2_final_commit_config.yaml"
    checks = {
        "final_confirmatory_integrity_pass": final_integrity.get("status") == "PASS" and final_integrity.get("valid") == 720,
        "final_baseline_integrity_pass": baseline_integrity.get("status") == "PASS" and baseline_integrity.get("valid") == 2160,
        "v2_scientific_core_exact": sha(ROOT / "core/v2_engine.py") == V2_CORE_SHA,
        "v1_baseline_core_exact": sha(ROOT / "core/engine.py") == V1_CORE_SHA,
        "final_v2_config_exact": sha(frozen_cfg) == FINAL_CONFIG_SHA,
        "runtime_exact": rt["python_version"] == "3.11.15" and rt["torch_version"] == "2.5.1+cu121" and rt["torch_cuda_version"] == "12.1" and rt["torch_cuda_available"] and rt["gpu_name"] == "NVIDIA GeForce RTX 3060 Laptop GPU",
        "final_test_centers_present": all((ROOT / "data" / f"center_{c}.npz").exists() for c in CENTERS),
        "no_preexisting_new_severity_results": not old,
    }

    reuse = []
    missing = []
    invalid = []
    hash_mismatch = []
    for center in CENTERS:
        for seed in SEEDS:
            for kind, location in STREAM_TEMPLATES:
                stream = scenario(kind, 0.10, location)
                group = []
                for method in METHODS:
                    path = source_path(method, center, seed, stream["scenario_id"])
                    if not path.exists():
                        missing.append(str(path.relative_to(ROOT)))
                        continue
                    try:
                        frame = pd.read_csv(path)
                        method_col = "method_id" if method == "Proposed" else "method"
                        expected_method = "Final_V2_SP_ShortDual" if method == "Proposed" else method
                        ok = (
                            len(frame) == 24 and frame.stage.tolist() == list(range(1, 25))
                            and frame[method_col].nunique() == 1 and frame[method_col].iloc[0] == expected_method
                            and int(frame.center_id.iloc[0]) == center and int(frame.model_seed.iloc[0]) == seed
                            and frame.scenario_id.nunique() == 1 and frame.scenario_id.iloc[0] == stream["scenario_id"]
                            and set(frame.attack_alpha.astype(float)) == {0.1}
                        )
                        if not ok:
                            invalid.append(str(path.relative_to(ROOT)))
                            continue
                        group.append((method, frame))
                        reuse.append({"method": method, "center_id": center, "model_seed": seed, "scenario_id": stream["scenario_id"], "source_file": str(path.relative_to(ROOT)), "source_file_sha256": sha(path)})
                    except Exception as exc:
                        invalid.append(f"{path.relative_to(ROOT)}: {type(exc).__name__}: {exc}")
                if len(group) == 4:
                    ref = group[0][1]
                    cols = ["update_data_hash", "verification_data_hash", "service_data_hash", "attack_mask_hash", "initial_state_hash"]
                    for method, frame in group[1:]:
                        for col in cols:
                            if not frame[col].astype(str).equals(ref[col].astype(str)):
                                hash_mismatch.append({"center_id": center, "model_seed": seed, "scenario_id": stream["scenario_id"], "method": method, "field": col})
    checks["alpha010_exact_count"] = len(reuse) == 1080
    checks["alpha010_artifacts_valid"] = not missing and not invalid
    checks["alpha010_pairing_hashes_exact"] = not hash_mismatch
    reuse_audit = {
        "schema": "ravm-dt-v2-severity-alpha010-reuse-v1",
        "status": "PASS" if checks["alpha010_exact_count"] and checks["alpha010_artifacts_valid"] and checks["alpha010_pairing_hashes_exact"] else "ALPHA_010_REUSE_AUDIT_FAILED",
        "expected_trajectories": 1080, "valid_trajectories": len(reuse), "missing": missing, "invalid": invalid,
        "pairing_hash_mismatches": hash_mismatch, "reuse_only": True, "rerun_alpha010": False, "artifacts": reuse,
    }
    atomic_json(audit_dir / "alpha010_reuse_audit.json", reuse_audit)
    checks["alpha010_reuse_pass"] = reuse_audit["status"] == "PASS"
    preflight = {"schema": "ravm-dt-v2-severity-preflight-v1", "status": "PASS" if all(checks.values()) else "FAIL", "created_at": dt.datetime.now(dt.timezone.utc).isoformat(), "checks": checks, "failed_checks": [k for k, v in checks.items() if not v], "runtime": rt}
    atomic_json(audit_dir / "severity_preflight_audit.json", preflight)
    if preflight["status"] != "PASS":
        raise SystemExit(2)

    cfg = {}
    for name in ["frozen_candidate_config.yaml", "frozen_commit_config.yaml", "frozen_baseline_config.yaml"]:
        cfg.update(json.loads((ROOT / "configs" / name).read_text(encoding="utf-8")))
    jobs = []
    for center in CENTERS:
        for seed in SEEDS:
            for alpha in NEW_ALPHAS:
                for kind, location in STREAM_TEMPLATES:
                    stream = scenario(kind, alpha, location)
                    for method in METHODS:
                        jobs.append({"method": method, "center_id": center, "model_seed": seed, "stream": stream, "stages": 24, "filename": f"{method}__{stream['scenario_id']}__{center}__{seed}.csv"})
    assert len(jobs) == EXPECTED_NEW and len({j["filename"] for j in jobs}) == EXPECTED_NEW
    manifest = {
        "schema": "ravm-dt-v2-severity-manifest-v1", "status": "FROZEN_BEFORE_EXECUTION",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "execution_implementation_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "scientific_implementation_commit": "7ae7fabd9a4e335e774fbcba2f38dfa8827bb8f3",
        "scientific_hashes": {"core/v2_engine.py": V2_CORE_SHA, "core/engine.py": V1_CORE_SHA, "final_v2_config": FINAL_CONFIG_SHA},
        "methods": METHODS, "centers": CENTERS, "seeds": SEEDS, "new_alphas": NEW_ALPHAS,
        "reused_alpha": 0.10, "streams": [scenario(k, a, loc) for a in NEW_ALPHAS for k, loc in STREAM_TEMPLATES],
        "expected_new_trajectories": EXPECTED_NEW, "expected_new_stage_rows": EXPECTED_NEW * 24,
        "expected_reused_trajectories": 1080, "expected_combined_trajectories": 3240,
        "stages_per_trajectory": 24, "workers": 2,
        "partition_unit": "complete center x scenario x seed x method lifecycle",
        "scientific_key": ["method", "center_id", "model_seed", "scenario_id"],
        "final_v2_gate": json.loads(frozen_cfg.read_text(encoding="utf-8")), "frozen_baseline_config": cfg,
        "analysis_plan": {"statistical_unit": "center", "seed_handling": "average within center", "paired_on": ["center_id", "model_seed", "scenario_id"], "bootstrap_replicates": 4000, "bootstrap_seed": 2904, "interval": "percentile 95%", "rho": 0.05, "epsilon": 5.6036475532487204e-05, "no_threshold_fitting": True},
        "alpha010_reuse_audit_sha256": sha(audit_dir / "alpha010_reuse_audit.json"), "jobs": jobs,
    }
    path = audit_dir / "severity_manifest.json"
    atomic_json(path, manifest)
    path.with_suffix(".json.sha256").write_text(sha(path) + "\n", encoding="ascii")
    atomic_json(results / "execution_status.json", {"state": "SEVERITY_MANIFEST_FROZEN", "completed": 0, "expected": EXPECTED_NEW, "manifest_sha256": sha(path), "warning": None})
    print(json.dumps({"status": "PASS", "alpha010_reused": len(reuse), "expected_new": EXPECTED_NEW, "manifest_sha256": sha(path)}, indent=2))


if __name__ == "__main__":
    main()
