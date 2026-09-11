"""Reconstruct and freeze the existing Alibaba external evaluation protocol."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import torch

from core.protocol import ROOT, digest
from scripts.v2_runner import atomic_json

CENTERS = list(range(20060, 20100))
SEEDS = [7311, 7312, 7313]
METHODS = ["Proposed", "Always-FT", "ER", "Huber-FT", "Frozen"]
STREAMS = [
    {"scenario_id": "clean", "kind": "clean", "alpha": 0.0, "attack_location": "both"},
    {"scenario_id": "mixed_a010_both", "kind": "mixed", "alpha": 0.1, "attack_location": "both"},
]
EXPECTED = 1200
V2_CORE_SHA = "f27d0abb6fabb50453cb4e04684b8e7b5f99d27aca7ae1f1755990640f3ce024"
V1_CORE_SHA = "b143046aac84e62ab098c5cb5f1666dafe4fe24419ea8b164acdf2c8cbee23a6"
POOL_SHA = "55918806ab6b71d206a944415465d449a2d0463a5befaa8adb06c90508df5d89"
PREPARE_SHA = "a102cace8dd79aba18bae57f2288de54d8f96e61826a4d830faa95fad1ad9075"
FINAL_CONFIG_SHA = "7275a287ee4a1f4602ed0a10a67362a1a61ffa398848d4529669b0584a127d13"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def runtime() -> dict:
    available = bool(torch.cuda.is_available())
    return {"sys_executable": str(Path(sys.executable).resolve()), "python_version": platform.python_version(), "torch_version": torch.__version__, "torch_cuda_version": torch.version.cuda, "torch_cuda_available": available, "gpu_name": torch.cuda.get_device_name(0) if available else None}


def main() -> None:
    audit_dir = ROOT / "audits_v2_alibaba"
    audit_dir.mkdir(exist_ok=True)
    old_manifest = json.loads((ROOT / "audits/execution_manifests/Q6_Alibaba_direct.json").read_text(encoding="utf-8"))
    old_jobs = sum(old_manifest["assignments"].values(), [])
    pool_path = ROOT / "alibaba_pool_manifest.json"
    pool = json.loads(pool_path.read_text(encoding="utf-8"))
    heldout = [item for item in pool["machines"] if item["pool"] == "heldout"]
    archive = json.loads((ROOT / "audits/alibaba_archive.json").read_text(encoding="utf-8"))
    rt = runtime()
    data_files = {}
    data_errors = []
    for item in heldout:
        center = int(item["center_id"])
        path = ROOT / "data" / f"center_{center}.npz"
        try:
            with np.load(path, allow_pickle=False) as z:
                meta = json.loads(str(z["meta"]))
                clean_hash = digest(z["x"], z["y"], z["ts"])
            if meta != item or clean_hash != item["clean_hash"]:
                data_errors.append(center)
            data_files[str(center)] = {"sha256": sha(path), "clean_hash": clean_hash, "machine_id_hash": item["machine_id_hash"]}
        except Exception:
            data_errors.append(center)
    checkpoint_files = {}
    checkpoint_errors = []
    for center in CENTERS:
        for seed in SEEDS:
            pt = ROOT / "checkpoints" / f"M0_GRU_H1_{seed}_{center}.pt"
            sidecar = pt.with_suffix(".json")
            if not pt.exists() or not sidecar.exists():
                checkpoint_errors.append(f"{seed}:{center}")
            else:
                checkpoint_files[f"{seed}:{center}"] = {"checkpoint_sha256": sha(pt), "sidecar_sha256": sha(sidecar), **json.loads(sidecar.read_text(encoding="utf-8"))}
    old_factorization = {
        "centers": sorted({int(j["center"]) for j in old_jobs}), "seeds": sorted({int(j["seed"]) for j in old_jobs}),
        "methods": sorted({j["method"] for j in old_jobs}), "streams": sorted({(j["kind"], float(j["alpha"]), j["location"]) for j in old_jobs}),
    }
    expected_streams = [("clean", 0.0, "both"), ("mixed", 0.1, "both")]
    existing = list((ROOT / "results_v2_alibaba/trajectories").glob("*.csv")) if (ROOT / "results_v2_alibaba/trajectories").exists() else []
    checks = {
        "historical_direct_manifest_complete": old_manifest["expected_trajectories"] == 2160 and len(old_jobs) == 2160,
        "historical_machine_ids_exact": old_factorization["centers"] == CENTERS,
        "historical_seeds_exact": old_factorization["seeds"] == SEEDS,
        "historical_streams_exact": old_factorization["streams"] == expected_streams,
        "pool_manifest_hash_exact": sha(pool_path) == POOL_SHA,
        "prepare_pipeline_hash_exact": sha(ROOT / "scripts/prepare_alibaba.py") == PREPARE_SHA,
        "archive_hash_audit_exact": archive.get("status") == "verified" and archive.get("sha256") == "3e6ee87fd204bb85b9e234c5c75a5096580fdabc8f085b224033080090753a7a",
        "heldout_machine_factorization_exact": len(heldout) == 40 and [int(x["center_id"]) for x in heldout] == CENTERS,
        "data_artifacts_exact": not data_errors and len(data_files) == 40,
        "initial_checkpoints_complete": not checkpoint_errors and len(checkpoint_files) == 120,
        "v2_scientific_core_exact": sha(ROOT / "core/v2_engine.py") == V2_CORE_SHA,
        "v1_scientific_core_exact": sha(ROOT / "core/engine.py") == V1_CORE_SHA,
        "final_v2_config_exact": sha(ROOT / "configs_v2_final/frozen_v2_final_commit_config.yaml") == FINAL_CONFIG_SHA,
        "runtime_exact": rt["python_version"] == "3.11.15" and rt["torch_version"] == "2.5.1+cu121" and rt["torch_cuda_version"] == "12.1" and rt["torch_cuda_available"] and rt["gpu_name"] == "NVIDIA GeForce RTX 3060 Laptop GPU",
        "no_preexisting_new_external_results": not existing,
    }
    cfg = {}
    for name in ["frozen_candidate_config.yaml", "frozen_commit_config.yaml", "frozen_baseline_config.yaml"]:
        cfg.update(json.loads((ROOT / "configs" / name).read_text(encoding="utf-8")))
    gate = json.loads((ROOT / "configs_v2_final/frozen_v2_final_commit_config.yaml").read_text(encoding="utf-8"))
    jobs = []
    for center in CENTERS:
        for seed in SEEDS:
            for stream in STREAMS:
                for method in METHODS:
                    jobs.append({"method": method, "center_id": center, "model_seed": seed, "stream": stream, "stages": 24, "backbone": "GRU", "horizon": 1, "filename": f"{method}__{stream['scenario_id']}__{center}__{seed}.csv"})
    assert len(jobs) == EXPECTED and len({j["filename"] for j in jobs}) == EXPECTED
    provenance = {
        "schema": "ravm-dt-v2-alibaba-provenance-v1", "status": "PASS" if all(checks.values()) else "ALIBABA_PROTOCOL_PROVENANCE_UNRESOLVED",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(), "checks": checks, "failed_checks": [k for k, v in checks.items() if not v],
        "historical_protocol_source": "audits/execution_manifests/Q6_Alibaba_direct.json", "historical_factorization": old_factorization,
        "protocol_conclusion": "Exact V1 external machine split, preprocessing, source initialization, target warmup initialization, lifecycle, seeds, and streams uniquely reconstructed.",
        "terminology": "external-domain evaluation; not fresh external confirmation", "pool_manifest_sha256": sha(pool_path), "prepare_pipeline_sha256": sha(ROOT / "scripts/prepare_alibaba.py"),
        "data_files": data_files, "checkpoint_files": checkpoint_files, "data_errors": data_errors, "checkpoint_errors": checkpoint_errors,
        "runtime": rt, "execution_implementation_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "scientific_hashes": {"core/v2_engine.py": V2_CORE_SHA, "core/engine.py": V1_CORE_SHA, "final_v2_config": FINAL_CONFIG_SHA},
        "methods": METHODS, "centers": CENTERS, "seeds": SEEDS, "streams": STREAMS, "expected_trajectories": EXPECTED, "expected_stage_rows": EXPECTED * 24,
        "workers": 2, "partition_unit": "complete machine x scenario x seed x method lifecycle", "stages_per_trajectory": 24,
        "final_v2_gate": gate, "frozen_baseline_config": cfg,
        "analysis_plan": {"unit": "machine", "seed_handling": "average within machine", "paired_on": ["center_id", "model_seed", "scenario_id"], "bootstrap_replicates": 4000, "bootstrap_seed": 2904, "interval": "percentile 95%", "rho": 0.05, "epsilon": 5.6036475532487204e-05},
        "jobs": jobs,
    }
    path = audit_dir / "alibaba_protocol_provenance_audit.json"
    atomic_json(path, provenance)
    path.with_suffix(".json.sha256").write_text(sha(path) + "\n", encoding="ascii")
    atomic_json(audit_dir / "alibaba_environment_audit.json", {"schema": "ravm-dt-v2-alibaba-environment-v1", "status": "PASS" if checks["runtime_exact"] else "FAIL", "runtime": rt})
    if provenance["status"] != "PASS":
        atomic_json(ROOT / "results_v2_alibaba/execution_status.json", {"state": "ALIBABA_PROTOCOL_PROVENANCE_UNRESOLVED", "failed_checks": provenance["failed_checks"]})
        raise SystemExit(2)
    atomic_json(ROOT / "results_v2_alibaba/execution_status.json", {"state": "ALIBABA_PROTOCOL_FROZEN", "completed": 0, "expected": EXPECTED, "protocol_sha256": sha(path), "warning": None})
    print(json.dumps({"status": "PASS", "expected": EXPECTED, "protocol_sha256": sha(path)}, indent=2))


if __name__ == "__main__":
    main()
