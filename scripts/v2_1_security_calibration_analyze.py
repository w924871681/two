"""Analyze the frozen V2.1 security-aware calibration extension."""
from __future__ import annotations

import datetime as dt
import hashlib
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
from scripts.v2_1_security_calibration_runner import aggregate_files


RHO = 0.05
EPSILON = 5.6036475532487204e-05
V0 = "V0_LegacyFull"
SCENARIOS = ["persistent_a010_verification_only", "replay_a010_verification_only"]
PAIR_METRICS = ["lifecycle_mse", "harmful_commit_rate", "average_downside"]
REPORT_METRICS = ["conditional_harmful_rate", "beneficial_commit_recall", "commit_rate"]


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


def arm(kappa_rec: float, kappa_hist: float) -> str:
    return f"kr{kappa_rec:g}_kh{kappa_hist:g}"


def pair(left: pd.DataFrame, right: pd.DataFrame, metric: str) -> dict:
    merged = left.merge(
        right,
        on=["analysis_scenario", "center_id", "model_seed"],
        suffixes=("_v2", "_v0"),
        validate="one_to_one",
    )
    merged["difference"] = merged[f"{metric}_v2"] - merged[f"{metric}_v0"]
    point, low, high = ci_mean(merged, "difference")
    return {"difference": point, "ci_low": low, "ci_high": high, "unit": "center", "bootstrap_replicates": BOOTSTRAP}


def summary_row(summary: pd.DataFrame, arm_id: str, scenario: str) -> pd.Series:
    return summary[(summary.arm_id == arm_id) & (summary.scenario == scenario)].iloc[0]


def pareto_flags(table: pd.DataFrame) -> list[bool]:
    minimum = [
        "balanced_mse", "mixed_harmful", "mixed_downside", "persistent_harmful",
        "persistent_downside", "replay_harmful", "replay_downside",
    ]
    flags = []
    for index, row in table.iterrows():
        others = table.drop(index=index)
        weak = np.ones(len(others), dtype=bool)
        strict = np.zeros(len(others), dtype=bool)
        for column in minimum:
            weak &= others[column].to_numpy() <= row[column]
            strict |= others[column].to_numpy() < row[column]
        weak &= others["balanced_beneficial_recall"].to_numpy() >= row["balanced_beneficial_recall"]
        strict |= others["balanced_beneficial_recall"].to_numpy() > row["balanced_beneficial_recall"]
        flags.append(not bool(np.any(weak & strict)))
    return flags


def fmt(value: float) -> str:
    return f"{value:.8g}"


def fmt_ci(value: dict) -> str:
    return f"{value['difference']:+.7g} [{value['ci_low']:+.7g}, {value['ci_high']:+.7g}]"


def main() -> None:
    protocol_path = ROOT / "configs_v2_dev/v2_1_security_aware_calibration_protocol.json"
    manifest_path = ROOT / "audits_v2_dev/v2_1_security_aware_calibration_execution_manifest.json"
    preflight = json.loads((ROOT / "audits_v2_dev/v2_1_security_aware_calibration_preflight.json").read_text(encoding="utf-8"))
    complete = json.loads((ROOT / "audits_v2_dev/v2_1_security_aware_calibration_execution_complete.json").read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    original_decision = json.loads((ROOT / "audits_v2_dev/v2_go_no_go_decision.json").read_text(encoding="utf-8"))

    grid_dir = ROOT / "results_v2_dev/v2_1_security_calibration/v2_grid/trajectories"
    ref_dir = ROOT / "results_v2_dev/v2_1_security_calibration/v0_reference/trajectories"
    grid_paths = sorted(grid_dir.glob("*.csv"))
    ref_paths = sorted(ref_dir.glob("*.csv"))
    expected_grid = {job["filename"]: job for job in manifest["jobs"] if job["output_group"] == "v2_grid"}
    expected_ref = {job["filename"]: job for job in manifest["jobs"] if job["output_group"] == "v0_reference"}
    actual_grid = {path.name: path for path in grid_paths}
    actual_ref = {path.name: path for path in ref_paths}
    missing_grid = sorted(set(expected_grid) - set(actual_grid))
    missing_ref = sorted(set(expected_ref) - set(actual_ref))
    unexpected_grid = sorted(set(actual_grid) - set(expected_grid))
    unexpected_ref = sorted(set(actual_ref) - set(expected_ref))
    invalid = []
    metadata = []
    grid_frames = []
    ref_frames = []

    for group, expected, actual, destination in [
        ("grid", expected_grid, actual_grid, grid_frames),
        ("reference", expected_ref, actual_ref, ref_frames),
    ]:
        for name in sorted(set(expected) & set(actual)):
            job = expected[name]
            try:
                frame = pd.read_csv(actual[name])
            except Exception as exc:
                invalid.append({"file": name, "reason": f"{type(exc).__name__}: {exc}"})
                continue
            if len(frame) != 24 or not frame.stage.is_unique or set(frame.stage) != set(range(1, 25)):
                invalid.append({"file": name, "reason": "stage sequence"})
                continue
            expected_values = {
                "structure_id": job["structure"]["structure_id"], "center_id": job["center"],
                "model_seed": job["seed"], "scenario_id": job["scenario"]["scenario_id"],
                "kappa_rec": job["gate"]["kappa_rec"], "kappa_hist": job["gate"]["kappa_hist"],
                "delta_imp": job["gate"]["delta_imp"], "delta_ret": job["gate"]["delta_ret"],
            }
            bad = {}
            for column, expected_value in expected_values.items():
                values = frame[column].drop_duplicates().tolist()
                same = len(values) == 1
                if same and isinstance(expected_value, float):
                    same = math.isclose(float(values[0]), expected_value, rel_tol=0.0, abs_tol=1e-15)
                elif same:
                    same = values[0] == expected_value
                if not same:
                    bad[column] = {"expected": expected_value, "actual": values}
            if bad:
                metadata.append({"file": name, "fields": bad})
            frame = frame.copy()
            frame["analysis_scenario"] = frame.scenario_id
            frame["arm_id"] = V0 if group == "reference" else frame.apply(lambda row: arm(row.kappa_rec, row.kappa_hist), axis=1)
            destination.append(frame)

    grid_stage = pd.concat(grid_frames, ignore_index=True) if grid_frames else pd.DataFrame()
    ref_stage = pd.concat(ref_frames, ignore_index=True) if ref_frames else pd.DataFrame()
    grid_key = ["arm_id", "analysis_scenario", "center_id", "model_seed", "stage"]
    ref_key = ["analysis_scenario", "center_id", "model_seed", "stage"]
    duplicate_grid = int(grid_stage.duplicated(grid_key).sum()) if len(grid_stage) else 0
    duplicate_ref = int(ref_stage.duplicated(ref_key).sum()) if len(ref_stage) else 0
    hash_columns = ["attack_mask_hash", "update_data_hash", "verification_data_hash", "service_data_hash"]
    combined = pd.concat([grid_stage, ref_stage], ignore_index=True)
    hash_mismatch_groups = int(
        (combined.groupby(ref_key)[hash_columns].nunique(dropna=False) > 1).any(axis=1).sum()
    ) if len(combined) else 0

    current_calibration_paths = sorted((ROOT / "results_v2_dev/calibration/trajectories").glob("*.csv"))
    current_calibration_aggregate = aggregate_files(current_calibration_paths, ROOT / "results_v2_dev/calibration/trajectories")
    materialized = [center for center in range(14000, 14030) if (ROOT / "data" / f"center_{center}.npz").exists()]
    checks = {
        "preflight_pass": preflight["status"] == "PASS",
        "execution_complete_2040": complete["status"] == "PASS" and complete["completed"] == complete["expected"] == 2040,
        "new_v2_expected_valid_1920": len(expected_grid) == len(grid_paths) == len(grid_frames) == 1920,
        "reference_expected_valid_120": len(expected_ref) == len(ref_paths) == len(ref_frames) == 120,
        "missing_zero": not missing_grid and not missing_ref,
        "duplicate_zero": duplicate_grid == 0 and duplicate_ref == 0,
        "unexpected_zero": not unexpected_grid and not unexpected_ref,
        "partial_invalid_zero": not invalid,
        "metadata_consistent": not metadata,
        "each_trajectory_24_stages": len(grid_stage) == 1920 * 24 and len(ref_stage) == 120 * 24,
        "data_attack_hashes_match_across_all_configs_and_v0": hash_mismatch_groups == 0,
        "existing_clean_mixed_results_unchanged": current_calibration_aggregate == manifest["existing_clean_mixed_aggregate_sha256"] == preflight["existing_clean_mixed_aggregate_sha256"],
        "protocol_hash_unchanged": sha256(protocol_path) == manifest["protocol_sha256"] == complete["protocol_sha256"],
        "scientific_implementation_unchanged": manifest["scientific_implementation_commit"] == "7ae7fabd9a4e335e774fbcba2f38dfa8827bb8f3" and preflight["checks"]["scientific_core_unchanged"],
        "heldout_access_false": complete["heldout_accessed"] is False,
        "heldout_materialized_false": not materialized,
    }
    integrity = "PASS" if all(checks.values()) else "FAIL"

    grid_trajectory = trajectory_metrics(grid_stage)
    ref_trajectory = trajectory_metrics(ref_stage)
    security_summary = summarize(pd.concat([grid_trajectory, ref_trajectory], ignore_index=True))
    primary_summary = pd.read_csv(ROOT / "results_v2_dev/calibration/calibration_summary.csv")
    primary_grid = pd.read_csv(ROOT / "results_v2_dev/calibration/calibration_grid_summary.csv").set_index("arm_id")
    primary_scenarios = ["stationary", "gradual", "abrupt", "recurring", "mixed_a010_both"]
    clean_scenarios = ["stationary", "gradual", "abrupt", "recurring"]
    configurations = []
    detailed = {}
    for kappa_rec in [0.0, 0.5, 1.0, 1.5]:
        for kappa_hist in [0.0, 0.5, 1.0, 1.5]:
            arm_id = arm(kappa_rec, kappa_hist)
            primary_rows = primary_summary[(primary_summary.arm_id == arm_id) & primary_summary.scenario.isin(primary_scenarios)]
            clean_rows = primary_rows[primary_rows.scenario.isin(clean_scenarios)]
            mixed_row = summary_row(primary_summary, arm_id, "mixed_a010_both")
            persistent_row = summary_row(security_summary, arm_id, SCENARIOS[0])
            replay_row = summary_row(security_summary, arm_id, SCENARIOS[1])
            pairs = {}
            for scenario in SCENARIOS:
                left = grid_trajectory[(grid_trajectory.arm_id == arm_id) & (grid_trajectory.analysis_scenario == scenario)]
                right = ref_trajectory[ref_trajectory.analysis_scenario == scenario]
                pairs[scenario] = {metric: pair(left, right, metric) for metric in PAIR_METRICS}
            main_pass = mixed_row.harmful_commit_rate <= RHO and mixed_row.average_downside <= EPSILON
            persistent_absolute = persistent_row.harmful_commit_rate <= RHO and persistent_row.average_downside <= EPSILON
            replay_absolute = replay_row.harmful_commit_rate <= RHO and replay_row.average_downside <= EPSILON
            persistent_relative = pairs[SCENARIOS[0]]["harmful_commit_rate"]["ci_low"] <= 0 and pairs[SCENARIOS[0]]["average_downside"]["ci_low"] <= 0
            replay_relative = pairs[SCENARIOS[1]]["harmful_commit_rate"]["ci_low"] <= 0 and pairs[SCENARIOS[1]]["average_downside"]["ci_low"] <= 0
            persistent_pass = persistent_absolute and persistent_relative
            replay_pass = replay_absolute and replay_relative
            absolute_pass = main_pass and persistent_absolute and replay_absolute
            feasible = main_pass and persistent_pass and replay_pass
            row = {
                "arm_id": arm_id, "kappa_rec": kappa_rec, "kappa_hist": kappa_hist,
                "clean_mse": float(clean_rows.lifecycle_mse.mean()), "mixed_mse": float(mixed_row.lifecycle_mse),
                "balanced_mse": float(primary_grid.loc[arm_id, "balanced_lifecycle_mse"]),
                "mixed_harmful": float(mixed_row.harmful_commit_rate), "mixed_downside": float(mixed_row.average_downside),
                "persistent_harmful": float(persistent_row.harmful_commit_rate), "persistent_downside": float(persistent_row.average_downside),
                "replay_harmful": float(replay_row.harmful_commit_rate), "replay_downside": float(replay_row.average_downside),
                "balanced_beneficial_recall": float(primary_rows.beneficial_commit_recall.mean()),
                "balanced_commit_rate": float(primary_rows.commit_rate.mean()),
                "verification_downside": float((persistent_row.average_downside + replay_row.average_downside) / 2),
                "absolute_risk_pass": bool(absolute_pass), "go5_persistent_pass": bool(persistent_pass),
                "go5_replay_pass": bool(replay_pass), "security_feasible": bool(feasible),
            }
            configurations.append(row)
            detailed[arm_id] = {"summary": row, "paired_vs_calibration_pool_v0": pairs}
    table = pd.DataFrame(configurations)
    table["pareto"] = pareto_flags(table)
    feasible = table[table.security_feasible].copy().sort_values(
        ["balanced_mse", "mixed_downside", "balanced_beneficial_recall", "verification_downside", "kappa_rec", "kappa_hist"],
        ascending=[True, True, False, True, True, True],
    )
    selected = None if feasible.empty else feasible.iloc[0]
    table["selected"] = False
    if selected is not None:
        table.loc[table.arm_id == selected.arm_id, "selected"] = True

    other_gates = {gate: original_decision["gates"][gate]["status"] for gate in ["GO-2", "GO-3", "GO-4", "GO-6"]}
    gate_recheck = {
        "GO-1": "PASS" if selected is not None and selected.mixed_harmful <= RHO and selected.mixed_downside <= EPSILON else "FAIL",
        **other_gates,
        "GO-5": "PASS" if selected is not None and selected.go5_persistent_pass and selected.go5_replay_pass else "FAIL",
    }
    decision = "V2_1_CALIBRATION_GO" if integrity == "PASS" and selected is not None and all(value == "PASS" for value in gate_recheck.values()) else "V2_1_CALIBRATION_NO_FEASIBLE_CONFIG"
    terminal = "WAITING_FOR_MANUAL_V2_1_CALIBRATION_REVIEW" if decision == "V2_1_CALIBRATION_GO" else "WAITING_FOR_MANUAL_V2_1_CALIBRATION_REVIEW"

    dev_pareto = pd.read_csv(ROOT / "results_v2_dev/development/development_pareto.csv").set_index("arm_id")
    dev_v2 = float(dev_pareto.loc["V2_SP_ShortDual", "balanced_lifecycle_mse"])
    dev_v0 = float(dev_pareto.loc[V0, "balanced_lifecycle_mse"])
    dev_relative = (dev_v2 / dev_v0 - 1) * 100
    audit = clean({
        "schema": "ravm-dt-v2.1-security-aware-calibration-audit-v1",
        "status": integrity,
        "decision": decision,
        "terminal_state": terminal,
        "purpose": "security-aware calibration coverage extension before fresh heldout; not heldout tuning and not a scientific-structure change",
        "selection_rules_frozen_before_execution": True,
        "protocol_sha256": sha256(protocol_path),
        "scientific_implementation_commit": manifest["scientific_implementation_commit"],
        "checks": checks,
        "integrity": {
            "new_expected": 1920, "new_valid": len(grid_frames), "reference_expected": 120,
            "reference_valid": len(ref_frames), "missing": len(missing_grid) + len(missing_ref),
            "duplicate": duplicate_grid + duplicate_ref, "unexpected": len(unexpected_grid) + len(unexpected_ref),
            "partial_invalid": len(invalid), "new_stage_rows": len(grid_stage), "reference_stage_rows": len(ref_stage),
            "hash_mismatch_groups": hash_mismatch_groups, "metadata_mismatches": metadata, "invalid_files": invalid,
        },
        "selection": {
            "security_feasible_count": int(table.security_feasible.sum()),
            "selected": None if selected is None else selected.to_dict(),
            "primary_objective": "minimum original equal-scenario balanced lifecycle MSE across stationary, gradual, abrupt, recurring, and mixed among SECURITY_FEASIBLE configurations",
            "tie_breaks": ["lower mixed downside", "higher balanced beneficial recall", "lower verification-only downside"],
        },
        "configurations": {row.arm_id: {**detailed[row.arm_id], "summary": row.to_dict()} for _, row in table.iterrows()},
        "mechanical_go_recheck": gate_recheck,
        "development_v2_vs_v1_legacy_context": {
            "scope": "previous frozen GO-2 structural evidence; no calibration-pool V0 clean/mixed trajectories were added",
            "v2_balanced_mse": dev_v2, "v1_balanced_mse": dev_v0, "relative_change_percent": dev_relative,
            "paired_difference": original_decision["gates"]["GO-2"]["balanced_lifecycle_mse_paired"],
        },
        "heldout_accessed": False, "heldout_materialized": False, "confirmatory_started": False,
    })
    audit_path = ROOT / "audits_v2_dev/v2_1_security_aware_calibration.json"
    atomic_json(audit_path, audit)
    table.to_csv(ROOT / "results_v2_dev/v2_1_security_calibration/security_pareto_table.csv", index=False)

    rows = []
    for _, row in table.iterrows():
        pairs = detailed[row.arm_id]["paired_vs_calibration_pool_v0"]
        rows.append(
            f"| {row.arm_id} | {fmt(row.clean_mse)} | {fmt(row.mixed_mse)} | {fmt(row.balanced_mse)} | "
            f"{fmt(row.mixed_harmful)} / {fmt(row.mixed_downside)} | {fmt(row.persistent_harmful)} / {fmt(row.persistent_downside)} | "
            f"{fmt(row.replay_harmful)} / {fmt(row.replay_downside)} | {fmt(row.balanced_beneficial_recall)} | {fmt(row.balanced_commit_rate)} | "
            f"{fmt_ci(pairs[SCENARIOS[0]]['lifecycle_mse'])} | {fmt_ci(pairs[SCENARIOS[0]]['harmful_commit_rate'])} | {fmt_ci(pairs[SCENARIOS[0]]['average_downside'])} | "
            f"{fmt_ci(pairs[SCENARIOS[1]]['lifecycle_mse'])} | {fmt_ci(pairs[SCENARIOS[1]]['harmful_commit_rate'])} | {fmt_ci(pairs[SCENARIOS[1]]['average_downside'])} | "
            f"{'PASS' if row.absolute_risk_pass else 'FAIL'} | {'PASS' if row.go5_persistent_pass else 'FAIL'} | {'PASS' if row.go5_replay_pass else 'FAIL'} | "
            f"{'TRUE' if row.security_feasible else 'FALSE'} | {'TRUE' if row.pareto else 'FALSE'} | {'TRUE' if row.selected else 'FALSE'} |"
        )
    if selected is None:
        selected_text = "No configuration satisfies all frozen absolute and relative security constraints."
    else:
        selected_pairs = detailed[selected.arm_id]["paired_vs_calibration_pool_v0"]
        selected_text = (
            f"Selected `{selected.arm_id}` (`kappa_rec={selected.kappa_rec:g}`, `kappa_hist={selected.kappa_hist:g}`). "
            f"Balanced clean/mixed MSE={selected.balanced_mse:.12g}; development structural V2 vs V1 Legacy balanced-MSE change={dev_relative:+.3f}%. "
            f"Mixed risk={selected.mixed_harmful:.8f}/{selected.mixed_downside:.12g}; "
            f"persistent risk={selected.persistent_harmful:.8f}/{selected.persistent_downside:.12g}; "
            f"replay risk={selected.replay_harmful:.8f}/{selected.replay_downside:.12g}."
        )
    report = f"""# V2.1 Security-Aware Calibration Report

Generated: {dt.datetime.now(dt.timezone.utc).isoformat()}

## Scope and frozen provenance

This stage extends calibration safety coverage after the development-stage replay weakness while fresh heldout centers 14000–14029 remain sealed and unmaterialized. It is not heldout tuning. The scientific structure remains `V2_SP_ShortDual` with SinglePath 50-step adaptation, history capacity 12, unchanged delta/rho/epsilon, and scientific implementation commit `{manifest['scientific_implementation_commit']}`.

All 16 existing κ combinations and every selection rule were frozen before execution in `configs_v2_dev/v2_1_security_aware_calibration_protocol.json` (SHA-256 `{sha256(protocol_path)}`). Existing clean/mixed calibration results were reused after integrity/hash/provenance checks and were not rerun.

## Integrity

- New V2 safety streams: **{integrity}**, expected=1920, valid={len(grid_frames)}, missing={len(missing_grid)}, duplicate={duplicate_grid}, unexpected={len(unexpected_grid)}, partial={len(invalid)}.
- Calibration-pool V0 reference: expected=120, valid={len(ref_frames)}, missing={len(missing_ref)}, duplicate={duplicate_ref}, unexpected={len(unexpected_ref)}.
- Every trajectory has 24 unique stages; data and attack hashes match across all 16 configurations and V0 (`hash_mismatch_groups={hash_mismatch_groups}`).
- Environment: Python {complete['runner_runtime']['python_version']}, PyTorch {complete['runner_runtime']['torch_version']}, CUDA available={str(complete['runner_runtime']['torch_cuda_available']).lower()}, GPU={complete['runner_runtime']['gpu_name']}.
- heldout_accessed=false; heldout_materialized=false.

## Full security/Pareto table

Values `harmful/downside` are absolute risks. Paired entries are `V2 configuration - calibration-pool V0_LegacyFull`, with paired center-cluster bootstrap 95% CI (4,000 replicates, seed 2904).

| κ config | Clean MSE | Mixed MSE | Balanced MSE | Mixed harm/down | Persistent harm/down | Replay harm/down | Balanced recall | Commit rate | Persistent ΔMSE | Persistent Δharm | Persistent Δdown | Replay ΔMSE | Replay Δharm | Replay Δdown | ABSOLUTE_RISK_PASS | GO5_PERSISTENT_PASS | GO5_REPLAY_PASS | SECURITY_FEASIBLE | PARETO | SELECTED |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|---|
{chr(10).join(rows)}

## Selection and decision

{selected_text}

Security-feasible configurations: **{int(table.security_feasible.sum())}/16**. Mechanical gate recheck: `{json.dumps(gate_recheck, ensure_ascii=False)}`.

**Decision: {decision}.** State: `{terminal}`. No fresh heldout was opened, materialized, or executed. Manual V2.1 calibration review is required before any further action.

The V1-relative number above is the already frozen development structural comparison used by GO-2. This extension did not add calibration-pool V0 clean/mixed trajectories, so it does not mislabel a cross-pool quantity as a new calibration-pool paired utility estimate.
"""
    report_path = ROOT / "V2_1_SECURITY_AWARE_CALIBRATION_REPORT.md"
    report_path.write_text(report, encoding="utf-8")
    status = {
        "status": terminal, "phase": "v2_1_security_aware_calibration_complete",
        "decision": decision, "new_completed": 1920, "new_expected": 1920,
        "reference_completed": 120, "reference_expected": 120, "integrity": integrity,
        "security_feasible_count": int(table.security_feasible.sum()),
        "selected": None if selected is None else selected.arm_id,
        "heldout_accessed": False, "heldout_materialized": False, "confirmatory_started": False,
        "report": str(report_path), "report_sha256": sha256(report_path),
        "audit": str(audit_path), "audit_sha256": sha256(audit_path),
    }
    atomic_json(ROOT / "results_v2_dev/execution_status.json", status)
    print(json.dumps(status, indent=2, ensure_ascii=False))
    if integrity != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
