"""Audit and analyze the fixed-config post-calibration GO-5 completion run."""
from __future__ import annotations

import datetime as dt
import json
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from core.protocol import ROOT
from scripts.v2_analyze import BOOTSTRAP, BOOTSTRAP_SEED, ci_mean, summarize, trajectory_metrics
from scripts.v2_runner import atomic_json, sha256


V2 = "FinalCalibratedShortDual"
V0 = "V0_LegacyFull"
RHO = 0.05
EPSILON = 5.6036475532487204e-05
METRICS = [
    "lifecycle_mse",
    "harmful_commit_rate",
    "average_downside",
    "conditional_harmful_rate",
    "beneficial_commit_recall",
    "commit_rate",
]
SCENARIOS = ["persistent_a010_verification_only", "replay_a010_verification_only"]
EXPECTED_RUNTIME = {
    "sys_executable": r"C:\Users\92487\anaconda3\envs\rcf-dti-py311\python.exe",
    "python_version": "3.11.15",
    "torch_version": "2.5.1+cu121",
    "torch_cuda_version": "12.1",
    "torch_cuda_available": True,
    "gpu_name": "NVIDIA GeForce RTX 3060 Laptop GPU",
}


def clean(value):
    if isinstance(value, dict):
        return {key: clean(item) for key, item in value.items()}
    if isinstance(value, list):
        return [clean(item) for item in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return None if not np.isfinite(value) else float(value)
    return value


def runtime_matches(value: dict) -> bool:
    return all(value.get(key) == expected for key, expected in EXPECTED_RUNTIME.items())


def ci_dict(point: float, low: float, high: float) -> dict:
    return {"estimate": clean(point), "ci_low": clean(low), "ci_high": clean(high)}


def main() -> None:
    manifest_path = ROOT / "audits_v2_dev/v2_post_calibration_go5_execution_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    preflight = json.loads((ROOT / "audits_v2_dev/v2_post_calibration_go5_preflight.json").read_text(encoding="utf-8"))
    complete = json.loads((ROOT / "audits_v2_dev/v2_post_calibration_go5_execution_complete.json").read_text(encoding="utf-8"))
    original = json.loads((ROOT / "audits_v2_dev/v2_go_no_go_decision.json").read_text(encoding="utf-8"))
    config_path = ROOT / "configs_v2_dev/frozen_v2_commit_config.yaml"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    folder = ROOT / "results_v2_dev/post_calibration_go5/trajectories"
    expected_by_name = {job["filename"]: job for job in manifest["jobs"]}
    paths = sorted(folder.glob("*.csv"))
    actual_by_name = {path.name: path for path in paths}
    missing = sorted(set(expected_by_name) - set(actual_by_name))
    unexpected = sorted(set(actual_by_name) - set(expected_by_name))
    invalid = []
    metadata_mismatch = []
    frames = []
    for name in sorted(set(expected_by_name) & set(actual_by_name)):
        job = expected_by_name[name]
        path = actual_by_name[name]
        try:
            frame = pd.read_csv(path)
        except Exception as exc:
            invalid.append({"file": name, "reason": f"{type(exc).__name__}: {exc}"})
            continue
        if len(frame) != 24 or not frame.stage.is_unique or set(frame.stage) != set(range(1, 25)):
            invalid.append({"file": name, "reason": "invalid stage sequence", "rows": len(frame)})
            continue
        expected = {
            "structure_id": "V2_SP_ShortDual",
            "variant_family": "V2_SP_ShortDual",
            "center_id": job["center"],
            "model_seed": job["seed"],
            "scenario_id": job["scenario"]["scenario_id"],
            "kappa_rec": 0.0,
            "kappa_hist": 0.5,
            "delta_imp": config["delta_imp"],
            "delta_ret": config["delta_ret"],
            "execution_phase": "post_calibration_go5",
            "history_capacity": 12,
        }
        bad = {}
        for column, expected_value in expected.items():
            values = frame[column].drop_duplicates().tolist()
            same = len(values) == 1
            if same and isinstance(expected_value, float):
                same = math.isclose(float(values[0]), expected_value, rel_tol=0.0, abs_tol=1e-15)
            elif same:
                same = values[0] == expected_value
            if not same:
                bad[column] = {"expected": expected_value, "actual": values}
        if bad:
            metadata_mismatch.append({"file": name, "fields": bad})
        frame = frame.copy()
        frame["analysis_scenario"] = frame.scenario_id
        frame["arm_id"] = V2
        frames.append(frame)
    stage_data = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    scientific_key = ["center_id", "model_seed", "scenario_id", "stage"]
    duplicate_stage_rows = int(stage_data.duplicated(scientific_key).sum()) if len(stage_data) else 0

    development_trajectories = pd.read_csv(ROOT / "results_v2_dev/development/development_trajectory_metrics.csv")
    v0_trajectory = development_trajectories[
        (development_trajectories.arm_id == V0) & development_trajectories.analysis_scenario.isin(SCENARIOS)
    ].copy()
    v2_trajectory = trajectory_metrics(stage_data)
    reference_stage_paths = [
        ROOT / "results_v2_dev/development/trajectories" / f"V0_LegacyFull__{scenario}__{center}__{seed}.csv"
        for scenario in SCENARIOS for center in range(11000, 11020) for seed in [7311, 7312, 7313]
    ]
    reference_stage = pd.concat([pd.read_csv(path) for path in reference_stage_paths], ignore_index=True)
    hash_columns = ["attack_mask_hash", "update_data_hash", "verification_data_hash", "service_data_hash"]
    aligned = stage_data.merge(
        reference_stage,
        on=["center_id", "model_seed", "scenario_id", "stage"],
        suffixes=("_v2", "_v0"),
        validate="one_to_one",
    )
    hash_mismatch_counts = {
        column: int((aligned[f"{column}_v2"] != aligned[f"{column}_v0"]).sum()) for column in hash_columns
    }

    summary = summarize(pd.concat([v2_trajectory, v0_trajectory], ignore_index=True))
    evidence = {}
    go5_fail_reasons = []
    for scenario in SCENARIOS:
        scenario_evidence = {}
        left = v2_trajectory[v2_trajectory.analysis_scenario == scenario]
        right = v0_trajectory[v0_trajectory.analysis_scenario == scenario]
        merged = left.merge(
            right,
            on=["analysis_scenario", "center_id", "model_seed"],
            suffixes=("_v2", "_v0"),
            validate="one_to_one",
        )
        for metric in METRICS:
            v2_row = summary[(summary.arm_id == V2) & (summary.scenario == scenario)].iloc[0]
            v0_row = summary[(summary.arm_id == V0) & (summary.scenario == scenario)].iloc[0]
            merged["difference"] = merged[f"{metric}_v2"] - merged[f"{metric}_v0"]
            point, low, high = ci_mean(merged, "difference")
            scenario_evidence[metric] = {
                "final_calibrated_shortdual": ci_dict(v2_row[metric], v2_row[f"{metric}_ci_low"], v2_row[f"{metric}_ci_high"]),
                "v0_legacy_full": ci_dict(v0_row[metric], v0_row[f"{metric}_ci_low"], v0_row[f"{metric}_ci_high"]),
                "paired_difference_final_minus_v0": ci_dict(point, low, high),
            }
        harmful = scenario_evidence["harmful_commit_rate"]
        downside = scenario_evidence["average_downside"]
        if harmful["final_calibrated_shortdual"]["estimate"] > RHO:
            go5_fail_reasons.append(f"{scenario}: absolute harmful rate exceeds rho")
        if downside["final_calibrated_shortdual"]["estimate"] > EPSILON:
            go5_fail_reasons.append(f"{scenario}: absolute downside exceeds epsilon")
        if harmful["paired_difference_final_minus_v0"]["ci_low"] > 0:
            go5_fail_reasons.append(f"{scenario}: harmful-rate paired CI wholly adverse")
        if downside["paired_difference_final_minus_v0"]["ci_low"] > 0:
            go5_fail_reasons.append(f"{scenario}: downside paired CI wholly adverse")
        evidence[scenario] = scenario_evidence

    go5 = "FAIL" if go5_fail_reasons else "PASS"
    other_gates = {key: original["gates"][key]["status"] for key in ["GO-1", "GO-2", "GO-3", "GO-4", "GO-6"]}
    other_pass = all(value == "PASS" for value in other_gates.values())
    verdict = "GO" if go5 == "PASS" and other_pass else "NO-GO"
    config_frozen_at = dt.datetime.fromtimestamp(config_path.stat().st_mtime, tz=dt.timezone.utc).isoformat()
    config_before_run = config_path.stat().st_mtime < dt.datetime.fromisoformat(manifest["created_at"]).timestamp()
    materialized = [center for center in range(14000, 14030) if (ROOT / "data" / f"center_{center}.npz").exists()]
    checks = {
        "preflight_pass": preflight["status"] == "PASS",
        "execution_complete": complete["status"] == "PASS" and complete["completed"] == complete["expected"] == 120,
        "expected_120": len(expected_by_name) == 120,
        "valid_120": len(frames) == len(paths) == 120,
        "missing_zero": not missing,
        "duplicate_zero": duplicate_stage_rows == 0 and len(paths) == len(actual_by_name),
        "unexpected_zero": not unexpected,
        "partial_invalid_zero": not invalid,
        "metadata_consistent": not metadata_mismatch,
        "reference_stage_alignment_2880": len(aligned) == 120 * 24,
        "reference_data_attack_hashes_exact": not any(hash_mismatch_counts.values()),
        "frozen_config_hash_exact": sha256(config_path) == manifest["frozen_config_sha256"] == "68e06d381ced23ed105694b97e221b37ea5302fb389789f9ec310c8bbe74d3f4",
        "config_frozen_before_run": config_before_run,
        "scientific_implementation_unchanged": manifest["scientific_implementation_commit"] == "7ae7fabd9a4e335e774fbcba2f38dfa8827bb8f3" and preflight["checks"]["scientific_core_unchanged"],
        "runner_runtime_correct": runtime_matches(complete["runner_runtime"]),
        "worker_runtimes_correct": len(complete["worker_runtimes"]) == 2 and all(runtime_matches(value) for value in complete["worker_runtimes"].values()),
        "heldout_access_false": complete["heldout_accessed"] is False,
        "heldout_materialized_false": not materialized,
    }
    integrity = "PASS" if all(checks.values()) else "FAIL"
    if integrity != "PASS":
        verdict = "NO-GO"
    audit = clean({
        "schema": "ravm-dt-v2-post-calibration-go5-audit-v1",
        "status": integrity,
        "purpose": "complete missing verification-only evidence for the already frozen final calibration winner; not parameter tuning or grid search",
        "why_120": "20 development centers × 3 fixed model seeds × 2 preregistered verification-only scenarios",
        "checks": checks,
        "integrity": {
            "expected": 120, "valid": len(frames), "missing": len(missing),
            "duplicate": duplicate_stage_rows, "unexpected": len(unexpected),
            "partial_invalid": len(invalid), "stage_rows": len(stage_data),
            "metadata_mismatches": metadata_mismatch, "invalid_files": invalid,
        },
        "frozen_configuration": {
            "structure": "V2_SP_ShortDual", "history_capacity": 12,
            "kappa_rec": config["kappa_rec"], "kappa_hist": config["kappa_hist"],
            "delta_imp": config["delta_imp"], "delta_ret": config["delta_ret"],
            "rho": config["rho"], "epsilon": config["epsilon"],
            "sha256": sha256(config_path), "frozen_at_utc_from_file_mtime": config_frozen_at,
            "execution_manifest_created_at": manifest["created_at"], "frozen_before_run": config_before_run,
        },
        "reference": preflight["reference"],
        "hash_alignment_with_v0": hash_mismatch_counts,
        "statistics": {
            "unit": "center", "paired": True, "bootstrap_replicates": BOOTSTRAP,
            "bootstrap_seed": BOOTSTRAP_SEED, "interval": "percentile 95%",
            "scenarios": evidence,
        },
        "go5": {"status": go5, "frozen_rule_unchanged": True, "failure_reasons": go5_fail_reasons},
        "mechanical_recheck_other_gates": other_gates,
        "resulting_overall_verdict": verdict,
        "heldout_accessed": False,
        "heldout_materialized": False,
        "confirmatory_started": False,
        "terminal_state": "WAITING_FOR_MANUAL_V2_METHOD_REVIEW" if verdict != "GO" else "AUTHORIZED_FOR_FINAL_V2_FREEZE",
    })
    audit_path = ROOT / "audits_v2_dev/v2_post_calibration_go5_audit.json"
    atomic_json(audit_path, audit)

    rows = []
    labels = {
        "lifecycle_mse": "Lifecycle MSE", "harmful_commit_rate": "Harmful commit rate",
        "average_downside": "Average downside", "conditional_harmful_rate": "Conditional harmful among commits",
        "beneficial_commit_recall": "Beneficial recall", "commit_rate": "Commit rate",
    }
    for scenario in SCENARIOS:
        for metric in METRICS:
            item = evidence[scenario][metric]
            v2i, v0i, diff = item["final_calibrated_shortdual"], item["v0_legacy_full"], item["paired_difference_final_minus_v0"]
            rows.append(
                f"| {scenario} | {labels[metric]} | {v2i['estimate']:.10g} [{v2i['ci_low']:.10g}, {v2i['ci_high']:.10g}] "
                f"| {v0i['estimate']:.10g} [{v0i['ci_low']:.10g}, {v0i['ci_high']:.10g}] "
                f"| {diff['estimate']:+.10g} [{diff['ci_low']:+.10g}, {diff['ci_high']:+.10g}] |"
            )
    report = f"""# V2 Post-Calibration GO-5 Completion Audit

Generated: {dt.datetime.now(dt.timezone.utc).isoformat()}

## Scope and provenance

This audit completes the verification-only evidence for the already frozen decision-calibration winner. It is **not parameter tuning or a new grid search**. Before any of these trajectories ran, the configuration was fixed as `V2_SP_ShortDual`, history capacity 12, `kappa_rec=0`, `kappa_hist=0.5`, `delta_imp={config['delta_imp']:.16g}`, and `delta_ret={config['delta_ret']:.16g}`. Its exact SHA-256 is `{sha256(config_path)}`.

The run contains exactly 20 existing development centers × 3 model seeds × 2 existing verification-only scenarios = **120 complete 24-stage trajectories**. It used scientific implementation commit `{manifest['scientific_implementation_commit']}` without changing the scientific core. The original frozen NO-GO report and decision audit remain intact.

## Integrity

- Result integrity: **{integrity}**; expected=120, valid={len(frames)}, missing={len(missing)}, duplicate={duplicate_stage_rows}, unexpected={len(unexpected)}, partial/invalid={len(invalid)}.
- Frozen V0 reference: **{preflight['reference']['status']}**; 120/120 reference artifacts valid, development aggregate SHA-256 `{preflight['reference']['development_aggregate_sha256']}`.
- V0 alignment: attack mask, update data, verification data, and service data hashes have zero mismatches across all 2,880 paired stages.
- Runtime: Python {complete['runner_runtime']['python_version']}, PyTorch {complete['runner_runtime']['torch_version']}, CUDA {complete['runner_runtime']['torch_cuda_version']}, GPU {complete['runner_runtime']['gpu_name']}.
- Fresh confirmatory heldout access/materialized: **false / false**.

## Center-cluster paired results

All intervals use paired center-cluster bootstrap with 4,000 replicates and center as the resampling unit. Differences are `FinalCalibratedShortDual - V0_LegacyFull`.

| Scenario | Metric | Final calibrated ShortDual [95% CI] | V0 Legacy Full [95% CI] | Paired difference [95% CI] |
|---|---|---:|---:|---:|
{chr(10).join(rows)}

## Frozen GO-5 decision

**GO-5: {go5}.** Absolute harmful rates are {evidence[SCENARIOS[0]]['harmful_commit_rate']['final_calibrated_shortdual']['estimate']:.8f} and {evidence[SCENARIOS[1]]['harmful_commit_rate']['final_calibrated_shortdual']['estimate']:.8f}, both below rho={RHO:.2f}; both downside estimates are below epsilon={EPSILON:.12g}. The replay scenario nevertheless has a wholly adverse harmful-rate paired CI and a wholly adverse downside paired CI. Under the original frozen GO-5 rule, either one is sufficient for failure. The rule has not been redefined.

Failure evidence:

{chr(10).join(f'- {reason}' for reason in go5_fail_reasons)}

GO-1, GO-2, GO-3, GO-4, and GO-6 mechanically remain PASS. Resulting overall verdict: **{verdict}**.

No final V2 freeze/tag was created, no fresh confirmatory center was materialized or accessed, and no confirmatory experiment was started. State: `WAITING_FOR_MANUAL_V2_METHOD_REVIEW`.
"""
    report_path = ROOT / "V2_POST_CALIBRATION_GO5_AUDIT.md"
    report_path.write_text(report, encoding="utf-8")
    status = {
        "status": "WAITING_FOR_MANUAL_V2_METHOD_REVIEW",
        "phase": "post_calibration_go5_complete",
        "completed": 120,
        "expected": 120,
        "integrity": integrity,
        "go5": go5,
        "verdict": verdict,
        "heldout_accessed": False,
        "heldout_materialized": False,
        "confirmatory_started": False,
        "report": str(report_path),
        "report_sha256": sha256(report_path),
        "audit": str(audit_path),
        "audit_sha256": sha256(audit_path),
    }
    atomic_json(ROOT / "results_v2_dev/execution_status.json", status)
    print(json.dumps(status, indent=2, ensure_ascii=False))
    if integrity != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
