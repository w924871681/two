"""Fail-closed Q2 completeness audit used by the internal phase gate."""
import csv
import datetime
import hashlib
import json
from collections import Counter, defaultdict

from core.protocol import ROOT, save_json
from scripts.q2_manifest import q2_key, q2_key_from_filename, q2_workloads


HASH_COLUMNS = ("update_data_hash", "verification_data_hash", "service_data_hash", "attack_mask_hash")
REQUIRED_COLUMNS = [
    "run_id", "center_id", "center_type", "model_seed", "horizon", "backbone", "stage",
    "drift_regime", "attack_type", "actual_attack_type", "attack_alpha", "attack_location",
    "method", "parent_state_hash", "candidate_state_hash", "initial_state_hash", "commit",
    "current_service_mse", "candidate_service_mse", "deployed_service_mse", "deployed_service_mae",
    "delta_srv", "harmful_commit", "downside", "beneficial_candidate", "U_rec", "U_hist",
    "median_rec", "mad_rec", "median_hist", "mad_hist", "candidate_update_time_s",
    "verification_time_s", "maintenance_time_s", "peak_gpu_memory_bytes", "persistent_buffer_bytes",
    "number_of_forward_passes", "number_of_backward_updates", "number_of_fisher_backward_passes",
    "update_start_ts", "update_end_ts", "verification_start_ts", "verification_end_ts",
    "decision_ts", "service_start_ts", "service_end_ts", "attack_mask_hash", "update_data_hash",
    "verification_data_hash", "service_data_hash",
]
P7_SCIENTIFIC_FILES = [
    "core/engine.py", "core/protocol.py", "core/models.py", "core/joint_dag.py",
    "configs/frozen_candidate_config.yaml", "configs/frozen_commit_config.yaml",
    "configs/frozen_baseline_config.yaml", "pool_manifest.json",
]


def _hash_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audit_q2_integrity(output=None):
    expected = [q2_key(workload) for workload in q2_workloads()]
    expected_set = set(expected)
    paths = sorted((ROOT / "results/q2_security").glob("*.csv"))
    keys = []
    invalid = []
    hash_groups = defaultdict(set)
    for path in paths:
        key = q2_key_from_filename(path.name)
        if key is None or path.stat().st_size == 0:
            invalid.append({"file": path.name, "reason": "invalid_name_or_empty"})
            continue
        with path.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            rows = list(reader)
            fields = reader.fieldnames or []
        if fields != REQUIRED_COLUMNS or len(rows) != 24:
            invalid.append({"file": path.name, "reason": "schema_or_row_count"})
            continue
        stages = [int(row["stage"]) for row in rows]
        if len(set(stages)) != 24 or set(stages) != set(range(1, 25)):
            invalid.append({"file": path.name, "reason": "stage_set"})
            continue
        for row in rows:
            actual = (
                int(row["model_seed"]), int(row["center_id"]), row["attack_type"],
                float(row["attack_alpha"]), row["attack_location"], row["method"],
            )
            if actual != key:
                invalid.append({"file": path.name, "reason": "metadata_mismatch"})
                break
            group = actual[:-1] + (int(row["stage"]),)
            for column in HASH_COLUMNS:
                hash_groups[(group, column)].add(row[column])
        keys.append(key)
    counts = Counter(keys)
    duplicate_excess = sum(value - 1 for value in counts.values() if value > 1)
    unexpected = set(keys) - expected_set
    missing = expected_set - set(keys)
    hash_mismatches = sum(1 for values in hash_groups.values() if len(values) != 1)
    tmp_files = [p.name for p in (ROOT / "results/q2_security").iterdir() if p.is_file() and p.suffix != ".csv"]
    freeze = json.loads((ROOT / "audits/final_freeze.json").read_text())
    freeze_mismatches = [
        name for name in P7_SCIENTIFIC_FILES
        if _hash_file(ROOT / name) != freeze["files"].get(name)
    ]
    q3_files = [str(p.relative_to(ROOT)) for p in (ROOT / "results/q3_benign_drift").rglob("*") if p.is_file()] if (ROOT / "results/q3_benign_drift").exists() else []
    checks = {
        "expected_trajectories": len(expected) == 7680,
        "complete_trajectories": len(paths) == 7680 and len(keys) == 7680,
        "duplicate_keys_zero": duplicate_excess == 0,
        "unexpected_keys_zero": not unexpected,
        "missing_keys_zero": not missing,
        "invalid_files_zero": not invalid,
        "temporary_files_zero": not tmp_files,
        "data_attack_hash_mismatches_zero": hash_mismatches == 0,
        "p7_scientific_and_frozen_hashes_match": not freeze_mismatches,
        "q3_results_absent": not q3_files,
    }
    report = {
        "status": "passed" if all(checks.values()) else "failed",
        "created_at": datetime.datetime.now().isoformat(),
        "checks": checks,
        "counts": {
            "expected": len(expected), "completed": len(paths), "valid_keys": len(keys),
            "duplicate_excess": duplicate_excess, "unexpected": len(unexpected),
            "missing": len(missing), "invalid": len(invalid),
            "hash_mismatches": hash_mismatches,
        },
        "failures": {
            "invalid": invalid[:20], "temporary_files": tmp_files,
            "unexpected": [list(x) for x in sorted(unexpected)[:20]],
            "missing": [list(x) for x in sorted(missing)[:20]],
            "freeze_mismatches": freeze_mismatches, "q3_files": q3_files,
        },
    }
    save_json(output or ROOT / "audits/q2_integrity.json", report)
    return report


if __name__ == "__main__":
    result = audit_q2_integrity()
    print(json.dumps(result, indent=2), flush=True)
    if result["status"] != "passed":
        raise SystemExit(1)
