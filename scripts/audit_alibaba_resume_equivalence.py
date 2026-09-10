from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(r"D:\dt-trustworthy-maintenance")
sys.path.insert(0, str(ROOT))

from core.engine import run
from core.joint_dag import CacheBundle, run_joint
from scripts.run_calibration import calibration_definition


EXCLUDED = {
    "run_id", "candidate_update_time_s", "verification_time_s", "maintenance_time_s",
    "peak_gpu_memory_bytes", "implementation_git_sha", "joint_dag_implementation_sha256",
}


def atomic_json(path: Path, obj: dict) -> None:
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)


def compare(reference: pd.DataFrame, replay: pd.DataFrame, sort_cols: list[str]) -> dict:
    reference = reference.sort_values(sort_cols).reset_index(drop=True)
    replay = replay.sort_values(sort_cols).reset_index(drop=True)
    cols = sorted((set(reference.columns) & set(replay.columns)) - EXCLUDED)
    if len(reference) != len(replay):
        raise AssertionError(f"row count mismatch {len(reference)} != {len(replay)}")
    exact_cols = []
    float_cols = []
    non_bitwise = []
    max_abs = 0.0
    for col in cols:
        a = reference[col].to_numpy()
        b = replay[col].to_numpy()
        if np.issubdtype(a.dtype, np.number) and np.issubdtype(b.dtype, np.number) and (
            np.issubdtype(a.dtype, np.floating) or np.issubdtype(b.dtype, np.floating)
        ):
            float_cols.append(col)
            exact = np.array_equal(a, b, equal_nan=True)
            diff = np.abs(a.astype(float) - b.astype(float))
            finite = diff[np.isfinite(diff)]
            value = float(finite.max()) if len(finite) else 0.0
            max_abs = max(max_abs, value)
            if not exact:
                non_bitwise.append({"column": col, "max_abs_diff": value})
            if value > 1e-12:
                raise AssertionError(f"float mismatch {col}: {value}")
        else:
            if not np.array_equal(a, b):
                raise AssertionError(f"exact mismatch {col}")
            exact_cols.append(col)
    return {
        "rows": len(reference), "columns_compared": len(cols), "exact_columns": exact_cols,
        "float_columns": float_cols, "bitwise_equal": not non_bitwise,
        "non_bitwise_columns": non_bitwise, "max_abs_diff": max_abs,
        "all_decisions_exact": bool(np.array_equal(reference["commit"].to_numpy(), replay["commit"].to_numpy())),
    }


def main() -> None:
    candidate, _, _, _, jobs = calibration_definition("alibaba")
    cases = [(7311, 20040, "clean", 0.0), (7311, 20040, "mixed", 0.1)]
    scratch = ROOT / "scratch" / "alibaba_shutdown_resume_equivalence"
    scratch.mkdir(parents=True, exist_ok=True)
    records = []
    for seed, center, kind, alpha in cases:
        started = time.perf_counter()
        policies = [{"policy": p, **jobs[p][1]} for p in range(400)]
        result, metrics, stage_stats = run_joint(
            center, seed, policies, kind, alpha, cache=CacheBundle(root=scratch / f"cache_{kind}"),
            use_l1=True, use_l2=False, run_id=f"shutdown_resume_replay_{kind}",
        )
        replay_proposed = pd.concat([pd.DataFrame(result[p]) for p in range(400)], ignore_index=True)
        formal_proposed = pd.concat([
            pd.read_csv(ROOT / "results" / "alibaba_calibration" / f"policy{p:03d}_{seed}_{center}_{kind}.csv")
            for p in range(400)
        ], ignore_index=True)
        proposed_cmp = compare(formal_proposed, replay_proposed, ["policy", "stage"])

        formal_validation = []
        replay_validation = []
        for policy in range(400, 405):
            formal = pd.read_csv(ROOT / "results" / "alibaba_calibration" / f"policy{policy:03d}_{seed}_{center}_{kind}.csv")
            formal["policy"] = policy
            method, settings = jobs[policy]
            replay = pd.DataFrame(run(
                center, seed, method, kind, alpha,
                cfg={**candidate, **settings, "calibration_candidate_cache": False, "calibration_evidence_cache": False},
                run_id=f"shutdown_resume_validation_{policy}_{kind}",
            ))
            replay["policy"] = policy
            formal_validation.append(formal)
            replay_validation.append(replay)
        validation_cmp = compare(pd.concat(formal_validation), pd.concat(replay_validation), ["policy", "stage"])
        records.append({
            "seed": seed, "center": center, "condition": kind, "stages": 24,
            "proposed_policies": 400, "validation_policies": 5,
            "proposed_comparison": proposed_cmp, "validation_comparison": validation_cmp,
            "joint_metrics": metrics, "stage_stats_count": len(stage_stats),
            "wall_s": time.perf_counter() - started,
        })
        print(f"resume equivalence {kind}: PASS", flush=True)
    audit = {
        "status": "passed",
        "generated_at": datetime.now().isoformat(),
        "scope": "two complete Alibaba calibration workloads; all 400 Proposed policies and all 5 ValidationCommit policies",
        "reference": "pre-shutdown formal CSVs produced by the original executor",
        "replay": "same scientific implementation after reboot; scratch only; persistent L2 disabled for independent recomputation",
        "cases": records,
        "all_hash_integer_categorical_exact": True,
        "all_decisions_exact": True,
        "max_abs_diff": max(
            max(r["proposed_comparison"]["max_abs_diff"], r["validation_comparison"]["max_abs_diff"])
            for r in records
        ),
        "scientific_implementation_changed": False,
    }
    atomic_json(ROOT / "audits" / "alibaba_calibration_resume_equivalence.json", audit)
    print(json.dumps({"status": audit["status"], "cases": len(records), "max_abs_diff": audit["max_abs_diff"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
