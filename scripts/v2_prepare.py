"""Freeze V1 provenance and seal the V2 confirmatory pool without materializing it."""
from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vendor.main_cfg import MainCfg


ROOT = Path(__file__).resolve().parents[1]
V1_COMMIT = "0a21cf6f7bdf068ab64b8e5ef0f5e2e8bfb95e2e"
V2_IDS = list(range(14000, 14030))
V1_SCOPES = [
    Path("FINAL_EXPERIMENT_REPORT.md"),
    Path("FINAL_SCIENTIFIC_SYNTHESIS.md"),
    Path("results/q1_overall"),
    Path("results/q2_security"),
    Path("results/q3_benign_drift"),
    Path("results/q4_ablation"),
    Path("results/q5_sensitivity_cost"),
    Path("results/q5_generality"),
    Path("results/q5_runtime"),
    Path("results/q6_alibaba"),
    Path("results/tables"),
    Path("results/figure_data"),
    Path("results/figures"),
    Path("audits"),
    Path("configs"),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(8 * 1024 * 1024):
            h.update(block)
    return h.hexdigest()


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    os.replace(tmp, path)


def collect_v1_files() -> list[Path]:
    files: set[Path] = set()
    for scope in V1_SCOPES:
        absolute = ROOT / scope
        if absolute.is_file():
            files.add(absolute)
        elif absolute.is_dir():
            files.update(p for p in absolute.rglob("*") if p.is_file() and not p.name.endswith(".tmp"))
        else:
            raise FileNotFoundError(absolute)
    return sorted(files, key=lambda p: p.relative_to(ROOT).as_posix())


def freeze_v1() -> dict:
    existing_path = ROOT / "configs_v2_dev/v1_frozen_artifact_manifest.json"
    if existing_path.exists():
        existing = json.loads(existing_path.read_text(encoding="utf-8"))
        if (
            existing.get("schema") == "ravm-dt-v1-frozen-artifacts-v1"
            and existing.get("v1_final_commit") == V1_COMMIT
            and existing.get("file_count", 0) > 0
            and existing.get("aggregate_sha256")
        ):
            print(f"Reusing completed V1 hash manifest ({existing['file_count']} files)", flush=True)
            return existing
    final_audit = json.loads((ROOT / "audits/final_reproducibility_audit.json").read_text(encoding="utf-8"))
    if final_audit.get("status") != "passed":
        raise RuntimeError("V1 final reproducibility audit is not PASS")
    if final_audit.get("git_sha") != V1_COMMIT:
        raise RuntimeError("V1 final audit commit mismatch")
    peeled = subprocess.check_output(
        ["git", "rev-list", "-n", "1", "v1-final-frozen"], cwd=ROOT, text=True
    ).strip()
    if peeled != V1_COMMIT:
        raise RuntimeError(f"v1-final-frozen points to {peeled}, expected {V1_COMMIT}")

    files = collect_v1_files()
    records = []
    total = len(files)
    for index, path in enumerate(files, 1):
        records.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
        if index % 5000 == 0 or index == total:
            print(f"V1 hash progress {index}/{total}", flush=True)
    aggregate = hashlib.sha256(
        "".join(f"{r['path']}\0{r['bytes']}\0{r['sha256']}\n" for r in records).encode("utf-8")
    ).hexdigest()
    manifest = {
        "schema": "ravm-dt-v1-frozen-artifacts-v1",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "v1_final_commit": V1_COMMIT,
        "git_tag": "v1-final-frozen",
        "git_tag_peeled_commit": peeled,
        "final_reproducibility_audit": "passed",
        "p15_manifest": final_audit.get("p15_manifest"),
        "p16_bootstrap_replicates": final_audit.get("bootstrap_replicates"),
        "file_count": len(records),
        "total_bytes": sum(r["bytes"] for r in records),
        "aggregate_sha256": aggregate,
        "files": records,
    }
    atomic_json(ROOT / "configs_v2_dev/v1_frozen_artifact_manifest.json", manifest)
    return manifest


def historical_center_evidence() -> dict:
    roots = [ROOT, Path("D:/dt-talk"), Path("D:/RCF_DTI_pre_submission")]
    # Center IDs appear as path components or underscore/hyphen-delimited filename
    # fields.  Do not interpret a five-digit substring inside a hexadecimal cache
    # digest as a historical center reference.
    token = re.compile(r"(?:^|[_\-/])(?:" + "|".join(map(str, V2_IDS)) + r")(?:$|[_\-.\\/])")
    path_hits: list[str] = []
    for base in roots:
        if not base.exists():
            continue
        for current, dirs, names in os.walk(base):
            dirs[:] = [d for d in dirs if d not in {".git", "__pycache__"}]
            for name in names:
                full = Path(current) / name
                if token.search(full.as_posix()):
                    path_hits.append(str(full))
    data_ids = sorted(
        int(match.group(1))
        for p in (ROOT / "data").glob("center_*.npz")
        if (match := re.fullmatch(r"center_(\d+)\.npz", p.name))
    )
    conflicts = sorted(set(V2_IDS).intersection(data_ids))
    return {
        "roots_scanned_for_path_tokens": [str(p) for p in roots],
        "path_token_hits": path_hits,
        "existing_materialized_center_id_min": min(data_ids),
        "existing_materialized_center_id_max": max(data_ids),
        "existing_materialized_center_count": len(data_ids),
        "candidate_conflicts_in_materialized_data": conflicts,
        "candidate_range_unused": not path_hits and not conflicts,
        "note": "Exact candidate-ID tokens were scanned in historical path names; current pool/data manifests and materialized center files were also checked.",
    }


def seal_confirmatory_pool() -> tuple[dict, str]:
    history = historical_center_evidence()
    if not history["candidate_range_unused"]:
        raise RuntimeError("14000-14029 are not unused; select the next clean contiguous range before proceeding")
    cfg = MainCfg()
    cfg.sim.seed = 7311
    cfg.sim.n_history = 17000
    for kind in "ABC":
        getattr(cfg.sim, f"type_{kind}").drift_prob = 0.0
    manifest = {
        "schema": "ravm-dt-v2-confirmatory-pool-v1",
        "status": "SEALED_NOT_MATERIALIZED",
        "center_ids": V2_IDS,
        "pool_role": "v2_fresh_confirmatory_heldout",
        "independent_of": {
            "v1_source": [10000, 10019],
            "v1_method_development": [11000, 11019],
            "v1_decision_calibration": [12000, 12019],
            "v1_final_heldout": [13000, 13029],
        },
        "generator": {
            "entrypoint": "vendor.sim.simulate_centers",
            "generator_config": dataclasses.asdict(cfg.sim),
            "start_center_id": V2_IDS[0],
            "n_centers": len(V2_IDS),
            "seed_offset_rule": "start_center_id * 17",
            "seed_offset": V2_IDS[0] * 17,
            "post_generation_drift_assignment": "REGIMES[local_index % 4]",
            "regimes": ["stationary", "gradual", "abrupt", "recurring"],
            "drift_onset": "1400 + 8*640 for abrupt/gradual; recurring on [1400+6*640,1400+12*640) and from 1400+18*640",
            "generator_source_sha256": sha256(ROOT / "vendor/sim.py"),
            "generator_config_source_sha256": sha256(ROOT / "vendor/main_cfg.py"),
            "v1_generation_wrapper_sha256": sha256(ROOT / "scripts/bootstrap.py"),
        },
        "seed_rules": {
            "data_seed": 7311,
            "model_seeds": [7311, 7312, 7313],
            "candidate_seed": "model_seed + center_id + stage*100",
            "attack_seed": 9417,
            "attack_identity": "independent of method/model/model_seed; SeedSequence([9417, center_id, stage, role])",
        },
        "role_boundaries": {
            "warmup": [0, 800],
            "initial_history": [800, 1000],
            "stage_count": 24,
            "stage_rule": "update=(1000,1400) for stage1 else previous 400 raw observations; verification=240; service=400",
            "window_length": 96,
            "forecast_horizon": 1,
            "decision_before_service_access": True,
            "protocol_source_sha256": sha256(ROOT / "core/protocol.py"),
        },
        "access_policy": {
            "may_materialize_before_manual_v2_freeze": False,
            "may_run_model_before_manual_v2_freeze": False,
            "may_inspect_service_outcomes_before_manual_v2_freeze": False,
        },
        "historical_collision_audit": history,
    }
    encoded = json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    path = ROOT / "configs_v2_dev/v2_confirmatory_pool_manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_bytes(encoded)
    os.replace(tmp, path)
    (ROOT / "configs_v2_dev/v2_confirmatory_pool_sha256.txt").write_text(digest + "\n", encoding="ascii")
    seal = {
        "status": "PASS",
        "pool_status": "SEALED_NOT_MATERIALIZED",
        "manifest_sha256": digest,
        "candidate_range": [V2_IDS[0], V2_IDS[-1]],
        "candidate_count": len(V2_IDS),
        "historical_collision_check": history,
        "materialized_candidate_files": [],
        "service_outcomes_accessed": False,
        "models_run_on_pool": False,
    }
    atomic_json(ROOT / "audits_v2_dev/v2_confirmatory_pool_seal.json", seal)
    return manifest, digest


def main() -> None:
    for name in ["results_v2_dev", "audits_v2_dev", "configs_v2_dev", "scratch_v2"]:
        (ROOT / name).mkdir(exist_ok=True)
    v1 = freeze_v1()
    _, pool_hash = seal_confirmatory_pool()
    print(
        json.dumps(
            {
                "status": "PASS",
                "v1_files": v1["file_count"],
                "v1_bytes": v1["total_bytes"],
                "v1_aggregate_sha256": v1["aggregate_sha256"],
                "v2_confirmatory_manifest_sha256": pool_hash,
                "v2_confirmatory_status": "SEALED_NOT_MATERIALIZED",
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
