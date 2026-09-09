"""Fail-closed freeze and preflight for the approved post-Q2 scheduler switch."""
from __future__ import annotations

import datetime
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.protocol import ROOT, save_json


SCIENTIFIC = ["core/engine.py", "core/protocol.py", "core/models.py", "core/joint_dag.py"]
EXECUTION_ONLY = [
    "scripts/formal_parallel.py",
    "scripts/formal_workload_worker.py",
    "scripts/executor_switch_freeze.py",
    "scripts/resume_after_q2_parallel.py",
    "scripts/final_reproducibility_audit_parallel.py",
    "scripts/launch_post_q2_queue.py",
]
Q2_RECOVERY_FILES = [
    "scripts/run_heldout.py", "core/status.py", "scripts/q2_manifest.py",
    "scripts/audit_q2_integrity.py", "scripts/resume_q2_after_crash.py",
]


def hash_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_sha():
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def tree_manifest(directory):
    files = sorted(Path(directory).glob("*.csv"))
    aggregate = hashlib.sha256()
    total = 0
    for path in files:
        digest = hash_file(path)
        size = path.stat().st_size
        total += size
        aggregate.update(path.name.encode())
        aggregate.update(str(size).encode())
        aggregate.update(digest.encode())
    return {"files": len(files), "bytes": total, "sha256": aggregate.hexdigest()}


def _scientific_hashes():
    values = {name: hash_file(ROOT / name) for name in SCIENTIFIC}
    aggregate = hashlib.sha256(json.dumps(values, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return values, aggregate


def audit_and_freeze():
    p7 = json.loads((ROOT / "audits" / "final_freeze.json").read_text(encoding="utf-8"))
    recovery = json.loads((ROOT / "audits" / "q2_recovery_implementation.json").read_text(encoding="utf-8"))
    benchmark = json.loads((ROOT / "audits" / "post_q2_execution_benchmark.json").read_text(encoding="utf-8"))
    scientific_hashes, scientific_aggregate = _scientific_hashes()
    p7_mismatches = []
    for relative, expected in p7["files"].items():
        if relative == "scripts/run_heldout.py":
            continue
        if hash_file(ROOT / relative) != expected:
            p7_mismatches.append(relative)
    recovery_mismatches = [name for name in Q2_RECOVERY_FILES
                           if recovery["execution_only_sha256"].get(name) != hash_file(ROOT / name)]
    q1 = tree_manifest(ROOT / "results" / "q1_overall")
    q2 = tree_manifest(ROOT / "results" / "q2_security")
    before = benchmark["boundary_audit"]["formal_after"]
    b_cases = [case for case in benchmark["scientific_equivalence"]["cases"] if case["comparison"] == "A_vs_B"]
    scratch_csv = list((ROOT / "scratch" / "post_q2_executor_benchmark" / "outputs").glob("*/*.csv"))
    later_dirs = ["q3_benign_drift", "q4_ablation", "q5_sensitivity_cost", "q5_generality",
                  "q5_runtime", "q6_alibaba", "alibaba_calibration"]
    later_counts = {name: len(list((ROOT / "results" / name).glob("*"))) if (ROOT / "results" / name).exists() else 0
                    for name in later_dirs}
    config_hashes = {name: hash_file(ROOT / "configs" / name) for name in [
        "frozen_candidate_config.yaml", "frozen_commit_config.yaml", "frozen_baseline_config.yaml"]}
    checks = {
        "q1_complete": q1["files"] == 1620,
        "q2_complete": q2["files"] == 7680,
        "q1_q2_unchanged_since_benchmark": q1 == before["q1_overall"] and q2 == before["q2_security"],
        "q3_and_later_formal_outputs_zero": all(value == 0 for value in later_counts.values()),
        "benchmark_scientific_csv_only_in_scratch": len(scratch_csv) >= 16,
        "p7_hashes_unchanged_except_recorded_q2_execution_file": not p7_mismatches,
        "q2_recovery_execution_hashes_unchanged": not recovery_mismatches,
        "scientific_core_matches_q2_recovery": scientific_aggregate == recovery["scientific_core_sha256"],
        "B_equivalence_pass": len(b_cases) == 16 and all(case["status"] == "passed" for case in b_cases),
        "B_max_float_difference_zero": max(case["max_abs_float_diff"] for case in b_cases) == 0,
        "benchmark_recommends_B": benchmark["recommended_executor"] == "B",
    }
    status = "passed" if all(checks.values()) else "failed"
    report = {
        "status": status, "created_at": datetime.datetime.now().isoformat(), "checks": checks,
        "git_sha": git_sha(), "scientific_implementation": "unchanged",
        "change_scope": "execution scheduling only", "workers": 2,
        "partition_unit": "complete center x condition x seed x method lifecycle",
        "stages_within_lifecycle": "strictly serial 1-24", "scientific_core_hashes": scientific_hashes,
        "scientific_core_aggregate_sha256": scientific_aggregate,
        "p7_final_freeze_sha256": hash_file(ROOT / "audits" / "final_freeze.json"),
        "p7_frozen_config_sha256": config_hashes,
        "pool_manifest_sha256": hash_file(ROOT / "pool_manifest.json"),
        "q1_manifest": q1, "q2_manifest": q2, "later_formal_counts": later_counts,
        "p7_mismatches": p7_mismatches, "q2_recovery_mismatches": recovery_mismatches,
        "B_equivalence_cases": len(b_cases), "B_speedup_range": benchmark["robustness_assessment"]["B_speedup_range_across_valid_cuda_passes"],
    }
    save_json(ROOT / "audits" / "q3_executor_switch_preflight.json", report)
    if status != "passed":
        raise RuntimeError(report)
    freeze = {
        **report, "status": "approved_for_q3_and_later",
        "execution_only_sha256": {name: hash_file(ROOT / name) for name in EXECUTION_ONLY},
    }
    save_json(ROOT / "audits" / "q3_executor_freeze.json", freeze)
    return freeze


def require_executor_switch_freeze():
    freeze = json.loads((ROOT / "audits" / "q3_executor_freeze.json").read_text(encoding="utf-8"))
    assert freeze["status"] == "approved_for_q3_and_later"
    assert freeze["git_sha"] == git_sha(), "execution-only commit changed"
    scientific_hashes, aggregate = _scientific_hashes()
    assert aggregate == freeze["scientific_core_aggregate_sha256"]
    assert scientific_hashes == freeze["scientific_core_hashes"]
    for name, expected in freeze["p7_frozen_config_sha256"].items():
        assert hash_file(ROOT / "configs" / name) == expected, name
    assert hash_file(ROOT / "pool_manifest.json") == freeze["pool_manifest_sha256"]
    for name, expected in freeze["execution_only_sha256"].items():
        assert hash_file(ROOT / name) == expected, name
    return freeze


if __name__ == "__main__":
    print(json.dumps(audit_and_freeze(), indent=2), flush=True)
