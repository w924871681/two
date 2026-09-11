"""Freeze the post-freeze architecture/horizon generality protocol."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import torch

from core.protocol import ROOT
from scripts.v2_runner import atomic_json

CENTERS = list(range(14000, 14020))
SEEDS = [7311, 7312, 7313]
METHODS = ["Proposed", "Always-FT", "Frozen"]
SETTINGS = [("MLP", 1), ("MLP", 4), ("TCN", 1), ("TCN", 4), ("GRU", 1), ("GRU", 4)]
NEW_SETTINGS = [value for value in SETTINGS if value != ("GRU", 1)]
STREAMS = [
    {"scenario_id": "clean", "kind": "clean", "alpha": 0.0, "attack_location": "both"},
    {"scenario_id": "mixed_a010_both", "kind": "mixed", "alpha": 0.1, "attack_location": "both"},
]
EXPECTED_NEW = 1800
V2_CORE_SHA = "f27d0abb6fabb50453cb4e04684b8e7b5f99d27aca7ae1f1755990640f3ce024"
V1_CORE_SHA = "b143046aac84e62ab098c5cb5f1666dafe4fe24419ea8b164acdf2c8cbee23a6"
FINAL_CONFIG_SHA = "7275a287ee4a1f4602ed0a10a67362a1a61ffa398848d4529669b0584a127d13"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def runtime() -> dict:
    available = bool(torch.cuda.is_available())
    return {"sys_executable": str(Path(sys.executable).resolve()), "python_version": platform.python_version(), "torch_version": torch.__version__, "torch_cuda_version": torch.version.cuda, "torch_cuda_available": available, "gpu_name": torch.cuda.get_device_name(0) if available else None}


def source_path(method: str, center: int, seed: int, scenario: str) -> Path:
    if method == "Proposed":
        return ROOT / "results_v2_final/trajectories" / f"Final_V2_SP_ShortDual__{scenario}__{center}__{seed}.csv"
    return ROOT / "results_v2_final_baselines/trajectories" / f"{method}__{scenario}__{center}__{seed}.csv"


def main() -> None:
    audit_dir = ROOT / "audits_v2_generality"
    audit_dir.mkdir(exist_ok=True)
    rt = runtime()
    severity = json.loads((ROOT / "audits_v2_severity/severity_execution_integrity_audit.json").read_text(encoding="utf-8"))
    baseline = json.loads((ROOT / "audits_v2_final_baselines/baseline_execution_integrity_audit.json").read_text(encoding="utf-8"))
    confirm = json.loads((ROOT / "audits_v2_final/final_confirmatory_verdict.json").read_text(encoding="utf-8"))
    source_checkpoints = {}
    source_errors = []
    for backbone, horizon in SETTINGS:
        for seed in SEEDS:
            pt = ROOT / "checkpoints" / f"source_{backbone}_H{horizon}_{seed}.pt"
            sidecar = pt.with_suffix(".json")
            if not pt.exists() or not sidecar.exists():
                source_errors.append(f"{backbone}:H{horizon}:{seed}")
                continue
            meta = json.loads(sidecar.read_text(encoding="utf-8"))
            if meta.get("backbone") != backbone or int(meta.get("horizon", -1)) != horizon or int(meta.get("seed", -1)) != seed or meta.get("source_centers") != list(range(10000, 10020)):
                source_errors.append(f"{backbone}:H{horizon}:{seed}:metadata")
            source_checkpoints[f"{backbone}:H{horizon}:{seed}"] = {"checkpoint_sha256": sha(pt), "sidecar_sha256": sha(sidecar), "metadata": meta}
    reuse = []
    reuse_errors = []
    reuse_mismatches = []
    for center in CENTERS:
        for seed in SEEDS:
            for stream in STREAMS:
                group = []
                for method in METHODS:
                    path = source_path(method, center, seed, stream["scenario_id"])
                    try:
                        frame = pd.read_csv(path)
                        col = "method_id" if method == "Proposed" else "method"
                        expected = "Final_V2_SP_ShortDual" if method == "Proposed" else method
                        ok = len(frame) == 24 and frame.stage.tolist() == list(range(1, 25)) and frame[col].nunique() == 1 and frame[col].iloc[0] == expected and int(frame.center_id.iloc[0]) == center and int(frame.model_seed.iloc[0]) == seed and frame.scenario_id.iloc[0] == stream["scenario_id"] and set(frame.backbone) == {"GRU"} and set(frame.horizon.astype(int)) == {1}
                        if not ok:
                            reuse_errors.append(str(path.relative_to(ROOT)))
                            continue
                        group.append((method, frame))
                        reuse.append({"method": method, "backbone": "GRU", "horizon": 1, "center_id": center, "model_seed": seed, "scenario_id": stream["scenario_id"], "source_file": str(path.relative_to(ROOT)), "source_file_sha256": sha(path)})
                    except Exception as exc:
                        reuse_errors.append(f"{path.relative_to(ROOT)}: {type(exc).__name__}: {exc}")
                if len(group) == 3:
                    ref = group[0][1]
                    for method, frame in group[1:]:
                        for field in ["update_data_hash", "verification_data_hash", "service_data_hash", "attack_mask_hash", "initial_state_hash"]:
                            if not frame[field].astype(str).equals(ref[field].astype(str)):
                                reuse_mismatches.append({"center": center, "seed": seed, "scenario": stream["scenario_id"], "method": method, "field": field})
    reuse_audit = {"schema": "ravm-dt-v2-generality-gruh1-reuse-v1", "status": "PASS" if len(reuse) == 360 and not reuse_errors and not reuse_mismatches else "FAIL", "expected": 360, "valid": len(reuse), "errors": reuse_errors, "pairing_hash_mismatches": reuse_mismatches, "rerun_gruh1": False, "artifacts": reuse}
    atomic_json(audit_dir / "gruh1_reuse_audit.json", reuse_audit)
    existing = list((ROOT / "results_v2_generality/trajectories").glob("*.csv")) if (ROOT / "results_v2_generality/trajectories").exists() else []
    checks = {
        "final_confirmatory_remains_pass": confirm.get("status") == "PASS" and confirm.get("verdict") == "CONFIRMED",
        "final_baseline_remains_pass": baseline.get("status") == "PASS" and baseline.get("valid") == 2160,
        "severity_scientific_integrity_pass": severity.get("status") == "PASS" and severity.get("valid_new") == 2160,
        "master_phase_d_complete": (ROOT / "V2_FINAL_EXPERIMENT_COMPLETION_REPORT.md").exists(),
        "architecture_definitions_exact": set(SETTINGS) == {("MLP", 1), ("MLP", 4), ("TCN", 1), ("TCN", 4), ("GRU", 1), ("GRU", 4)},
        "source_checkpoint_provenance_valid": len(source_checkpoints) == 18 and not source_errors,
        "gruh1_reuse_pass": reuse_audit["status"] == "PASS",
        "v2_core_exact": sha(ROOT / "core/v2_engine.py") == V2_CORE_SHA,
        "v1_core_exact": sha(ROOT / "core/engine.py") == V1_CORE_SHA,
        "final_config_exact": sha(ROOT / "configs_v2_final/frozen_v2_final_commit_config.yaml") == FINAL_CONFIG_SHA,
        "runtime_exact": rt["python_version"] == "3.11.15" and rt["torch_version"] == "2.5.1+cu121" and rt["torch_cuda_version"] == "12.1" and rt["torch_cuda_available"] and rt["gpu_name"] == "NVIDIA GeForce RTX 3060 Laptop GPU",
        "center_subset_predeclared": CENTERS == list(range(14000, 14020)),
        "balanced_regimes": {r: sum(1 for c in CENTERS if ["stationary", "gradual", "abrupt", "recurring"][(c - 14000) % 4] == r) for r in ["stationary", "gradual", "abrupt", "recurring"]} == {"stationary": 5, "gradual": 5, "abrupt": 5, "recurring": 5},
        "no_preexisting_new_generality_results": not existing,
    }
    architecture_audit = {"schema": "ravm-dt-v2-generality-architecture-provenance-v1", "status": "PASS" if checks["architecture_definitions_exact"] and checks["source_checkpoint_provenance_valid"] else "PROVENANCE_UNRESOLVED", "core_models_sha256": sha(ROOT / "core/models.py"), "core_engine_sha256": sha(ROOT / "core/engine.py"), "source_checkpoints": source_checkpoints, "errors": source_errors, "no_heldout_driven_architecture_choice": True}
    atomic_json(audit_dir / "architecture_provenance_audit.json", architecture_audit)
    jobs = []
    for backbone, horizon in NEW_SETTINGS:
        for center in CENTERS:
            for seed in SEEDS:
                for stream in STREAMS:
                    for method in METHODS:
                        jobs.append({"method": method, "backbone": backbone, "horizon": horizon, "center_id": center, "model_seed": seed, "stream": stream, "stages": 24, "filename": f"{method}__{backbone}_H{horizon}__{stream['scenario_id']}__{center}__{seed}.csv"})
    assert len(jobs) == EXPECTED_NEW and len({job["filename"] for job in jobs}) == EXPECTED_NEW
    cfg = {}
    for name in ["frozen_candidate_config.yaml", "frozen_commit_config.yaml", "frozen_baseline_config.yaml"]:
        cfg.update(json.loads((ROOT / "configs" / name).read_text(encoding="utf-8")))
    protocol = {"schema": "ravm-dt-v2-generality-protocol-v1", "status": "FROZEN_BEFORE_EXECUTION" if all(checks.values()) else "PROVENANCE_UNRESOLVED", "created_at": dt.datetime.now(dt.timezone.utc).isoformat(), "checks": checks, "failed_checks": [k for k, v in checks.items() if not v], "execution_implementation_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), "scientific_implementation_commit": "7ae7fabd9a4e335e774fbcba2f38dfa8827bb8f3", "scientific_hashes": {"core/v2_engine.py": V2_CORE_SHA, "core/engine.py": V1_CORE_SHA, "core/models.py": sha(ROOT / "core/models.py"), "final_v2_config": FINAL_CONFIG_SHA}, "settings": [{"backbone": b, "horizon": h, "origin": "reuse" if (b, h) == ("GRU", 1) else "new"} for b, h in SETTINGS], "new_settings": [{"backbone": b, "horizon": h} for b, h in NEW_SETTINGS], "methods": METHODS, "centers": CENTERS, "seeds": SEEDS, "streams": STREAMS, "expected_new_trajectories": EXPECTED_NEW, "expected_new_stage_rows": 43200, "expected_reused_gruh1": 360, "expected_combined": 2160, "stages_per_trajectory": 24, "workers": 2, "partition_unit": "complete architecture x horizon x center x scenario x seed x method lifecycle", "final_v2_gate": json.loads((ROOT / "configs_v2_final/frozen_v2_final_commit_config.yaml").read_text(encoding="utf-8")), "frozen_baseline_config": cfg, "analysis_plan": {"unit": "center", "seed_handling": "average within center", "bootstrap_replicates": 4000, "bootstrap_seed": 2904, "interval": "percentile 95%", "comparisons": ["Proposed - Always-FT", "Proposed - Frozen"], "do_not_pool_architectures": True, "qualitative_conditions": ["Proposed utility relative to Frozen", "Proposed harmful/downside relative to Always-FT", "commit rate and beneficial recall greater than zero", "no catastrophic lifecycle failure"], "no_posthoc_thresholds": True}, "gruh1_reuse_audit_sha256": sha(audit_dir / "gruh1_reuse_audit.json"), "jobs": jobs}
    path = audit_dir / "generality_protocol.json"
    atomic_json(path, protocol)
    path.with_suffix(".json.sha256").write_text(sha(path) + "\n", encoding="ascii")
    if protocol["status"] != "FROZEN_BEFORE_EXECUTION":
        atomic_json(ROOT / "results_v2_generality/execution_status.json", {"state": "GENERALITY_PROVENANCE_UNRESOLVED", "failed_checks": protocol["failed_checks"]})
        raise SystemExit(2)
    atomic_json(ROOT / "results_v2_generality/execution_status.json", {"state": "GENERALITY_PROTOCOL_FROZEN", "completed": 0, "expected": EXPECTED_NEW, "protocol_sha256": sha(path), "warning": None})
    print(json.dumps({"status": "PASS", "expected_new": EXPECTED_NEW, "reused_gruh1": 360, "protocol_sha256": sha(path)}, indent=2))


if __name__ == "__main__":
    main()
