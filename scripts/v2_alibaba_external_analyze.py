"""Audit and analyze the frozen Final-V2 Alibaba external evaluation."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from core.protocol import ROOT
from scripts.v2_runner import atomic_json

METHODS = ["Proposed", "Always-FT", "ER", "Huber-FT", "Frozen"]
BASELINES = METHODS[1:]
SCENARIOS = ["clean", "mixed_a010_both"]
METRICS = ["lifecycle_mse", "lifecycle_mae", "harmful_commit_rate", "average_downside", "conditional_harmful_rate", "beneficial_commit_recall", "commit_rate", "mean_maintenance_time_s"]
BOOT = 4000
SEED = 2904


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def machine_ci(frame: pd.DataFrame, column: str) -> tuple[float, float, float]:
    values = frame.groupby("center_id")[column].mean().dropna().to_numpy(float)
    if not len(values):
        return math.nan, math.nan, math.nan
    rng = np.random.default_rng(SEED)
    sample = values[rng.integers(len(values), size=(BOOT, len(values)))].mean(axis=1)
    lo, hi = np.quantile(sample, [0.025, 0.975])
    return float(values.mean()), float(lo), float(hi)


def chain_errors(frame: pd.DataFrame) -> int:
    errors = 0
    for _, group in frame.sort_values("stage").groupby(["method_id", "center_id", "model_seed", "scenario_id"]):
        rows = list(group.itertuples())
        for left, right in zip(rows, rows[1:]):
            errors += int(right.parent_state_hash != (left.candidate_state_hash if int(left.commit) else left.parent_state_hash))
    return errors


def trajectory(raw: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for values, group in raw.sort_values("stage").groupby(["method_id", "scenario_id", "center_id", "model_seed", "machine_id_hash"]):
        method, scenario, center, seed, machine_hash = values
        commits = int(group.commit.sum())
        beneficial = int(group.beneficial_candidate.sum())
        rows.append({"method_id": method, "scenario_id": scenario, "center_id": center, "model_seed": seed, "machine_id_hash": machine_hash, "lifecycle_mse": group.deployed_service_mse.mean(), "lifecycle_mae": group.deployed_service_mae.mean(), "harmful_commit_rate": group.harmful_commit.mean(), "average_downside": group.downside.mean(), "conditional_harmful_rate": group.harmful_commit.sum() / commits if commits else math.nan, "beneficial_commit_recall": (group.commit * group.beneficial_candidate).sum() / beneficial if beneficial else math.nan, "commit_rate": group.commit.mean(), "mean_maintenance_time_s": group.maintenance_time_s.mean(), "peak_gpu_memory_bytes": group.peak_gpu_memory_bytes.max(), "persistent_buffer_bytes": group.persistent_buffer_bytes.max(), "source_file": group.source_file.iloc[0], "source_file_sha256": group.source_file_sha256.iloc[0]})
    return pd.DataFrame(rows)


def main() -> None:
    audit_dir = ROOT / "audits_v2_alibaba"
    out = ROOT / "results_v2_alibaba"
    protocol = json.loads((audit_dir / "alibaba_protocol_provenance_audit.json").read_text(encoding="utf-8"))
    complete = json.loads((audit_dir / "alibaba_execution_complete.json").read_text(encoding="utf-8"))
    if protocol["status"] != "PASS" or complete.get("status") != "PASS" or complete.get("completed") != 1200:
        raise RuntimeError("Alibaba external protocol/execution incomplete")
    expected = {job["filename"]: job for job in protocol["jobs"]}
    paths = {path.name: path for path in (out / "trajectories").glob("*.csv")}
    missing = sorted(set(expected) - set(paths))
    unexpected = sorted(set(paths) - set(expected))
    invalid = []
    frames = []
    required = {"center_id", "model_seed", "stage", "commit", "parent_state_hash", "candidate_state_hash", "initial_state_hash", "update_end_ts", "verification_start_ts", "verification_end_ts", "decision_ts", "service_start_ts", "update_data_hash", "verification_data_hash", "service_data_hash", "attack_mask_hash", "deployed_service_mse", "deployed_service_mae", "harmful_commit", "downside", "beneficial_candidate", "maintenance_time_s"}
    for name in sorted(set(expected) & set(paths)):
        job = expected[name]
        path = paths[name]
        try:
            frame = pd.read_csv(path)
            method_col = "method_id" if job["method"] == "Proposed" else "method"
            ok = required <= set(frame) and len(frame) == 24 and frame.stage.tolist() == list(range(1, 25)) and frame[method_col].nunique() == 1 and frame[method_col].iloc[0] == job["method"] and int(frame.center_id.iloc[0]) == job["center_id"] and int(frame.model_seed.iloc[0]) == job["model_seed"] and frame.scenario_id.nunique() == 1 and frame.scenario_id.iloc[0] == job["stream"]["scenario_id"]
            if not ok:
                invalid.append(name)
                continue
            frame["method_id"] = job["method"]
            frame["machine_id_hash"] = protocol["data_files"][str(job["center_id"])]["machine_id_hash"]
            frame["source_file"] = name
            frame["source_file_sha256"] = sha(path)
            frames.append(frame)
        except Exception as exc:
            invalid.append(f"{name}: {type(exc).__name__}: {exc}")
    raw = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    duplicate = int(raw.duplicated(["method_id", "center_id", "model_seed", "scenario_id", "stage"]).sum()) if len(raw) else 0
    ordering = int((~((raw.update_end_ts < raw.verification_start_ts) & (raw.verification_end_ts == raw.decision_ts) & (raw.decision_ts < raw.service_start_ts))).sum()) if len(raw) else 0
    chain = chain_errors(raw) if len(raw) else 0
    integrity = {"schema": "ravm-dt-v2-alibaba-integrity-v1", "status": "PASS", "expected": 1200, "valid": len(frames), "missing": len(missing), "duplicate": duplicate, "unexpected": len(unexpected), "partial_invalid": len(invalid), "stage_rows": len(raw), "expected_stage_rows": 28800, "decision_ordering_errors": ordering, "state_chain_errors": chain, "missing_files": missing, "unexpected_files": unexpected, "invalid_files": invalid}
    integrity["status"] = "PASS" if len(frames) == 1200 and len(raw) == 28800 and not missing and not unexpected and not invalid and not duplicate and not ordering and not chain else "FAIL"
    atomic_json(audit_dir / "alibaba_execution_integrity_audit.json", integrity)
    if integrity["status"] != "PASS":
        atomic_json(out / "execution_status.json", {"state": "ALIBABA_EXTERNAL_EXECUTION_INCOMPLETE", "integrity": integrity})
        raise RuntimeError("Alibaba integrity failed")
    keys = ["center_id", "model_seed", "scenario_id", "stage"]
    ref = raw[raw.method_id == "Proposed"][keys + ["update_data_hash", "verification_data_hash", "service_data_hash", "attack_mask_hash", "initial_state_hash"]]
    paired = raw[raw.method_id != "Proposed"].merge(ref, on=keys, suffixes=("_method", "_proposed"), validate="many_to_one")
    fields = ["update_data_hash", "verification_data_hash", "service_data_hash", "attack_mask_hash", "initial_state_hash"]
    mismatch = {field: int((paired[field + "_method"].astype(str) != paired[field + "_proposed"].astype(str)).sum()) for field in fields}
    pairing = {"schema": "ravm-dt-v2-alibaba-pairing-v1", "status": "PASS" if len(paired) == 23040 and not any(mismatch.values()) else "FAIL", "paired_stage_rows": len(paired), "expected_paired_stage_rows": 23040, "mismatch_rows": mismatch, "unit": "natural machine"}
    atomic_json(audit_dir / "alibaba_pairing_audit.json", pairing)
    leakage = {"schema": "ravm-dt-v2-alibaba-leakage-v1", "status": "PASS" if pairing["status"] == "PASS" and ordering == 0 and chain == 0 else "FAIL", "decision_precedes_service": ordering == 0, "state_chain_valid": chain == 0, "service_data_post_decision_only": True, "no_alibaba_recalibration": True, "terminology": "external-domain evaluation; not fresh confirmation"}
    atomic_json(audit_dir / "alibaba_leakage_audit.json", leakage)
    if pairing["status"] != "PASS" or leakage["status"] != "PASS":
        atomic_json(out / "execution_status.json", {"state": "ALIBABA_EXTERNAL_EXECUTION_INCOMPLETE", "pairing": pairing["status"], "leakage": leakage["status"]})
        raise RuntimeError("Alibaba pairing/leakage failed")
    traj = trajectory(raw)
    machine = traj.groupby(["method_id", "scenario_id", "center_id", "machine_id_hash"], as_index=False)[METRICS + ["peak_gpu_memory_bytes", "persistent_buffer_bytes"]].mean()
    summary_rows = []
    for (method, scenario), group in traj.groupby(["method_id", "scenario_id"]):
        row = {"method": method, "scenario": scenario, "machines": group.center_id.nunique(), "seeds": group.model_seed.nunique(), "trajectories": len(group)}
        for metric in METRICS:
            point, lo, hi = machine_ci(group, metric)
            row.update({metric: point, metric + "_ci_low": lo, metric + "_ci_high": hi})
        row["peak_gpu_memory_bytes"] = group.groupby("center_id").peak_gpu_memory_bytes.mean().mean()
        row["persistent_buffer_bytes"] = group.groupby("center_id").persistent_buffer_bytes.mean().mean()
        row["harmful_absolute_pass"] = bool(row["harmful_commit_rate"] <= protocol["analysis_plan"]["rho"])
        row["downside_absolute_pass"] = bool(row["average_downside"] <= protocol["analysis_plan"]["epsilon"])
        summary_rows.append(row)
    summary = pd.DataFrame(summary_rows).sort_values(["scenario", "method"])
    pair_rows = []
    for baseline in BASELINES:
        for scenario in SCENARIOS:
            proposed = traj[(traj.method_id == "Proposed") & (traj.scenario_id == scenario)]
            base = traj[(traj.method_id == baseline) & (traj.scenario_id == scenario)]
            merged = proposed.merge(base, on=["scenario_id", "center_id", "model_seed", "machine_id_hash"], suffixes=("_p", "_b"), validate="one_to_one")
            for metric in METRICS:
                merged["difference"] = merged[metric + "_p"] - merged[metric + "_b"]
                point, lo, hi = machine_ci(merged, "difference")
                pv = float(proposed.groupby("center_id")[metric].mean().mean())
                bv = float(base.groupby("center_id")[metric].mean().mean())
                pair_rows.append({"comparison": f"Proposed - {baseline}", "baseline": baseline, "scenario": scenario, "metric": metric, "proposed_estimate": pv, "baseline_estimate": bv, "difference": point, "ci_low": lo, "ci_high": hi, "relative_percent": (pv / bv - 1) * 100 if np.isfinite(bv) and bv != 0 else math.nan, "bootstrap_replicates": BOOT, "bootstrap_seed": SEED, "unit": "machine"})
    comparisons = pd.DataFrame(pair_rows)
    out.mkdir(exist_ok=True)
    paths_out = [out / "alibaba_trajectory_index.csv", out / "alibaba_machine_level_summary.csv", out / "alibaba_scenario_summary.csv", out / "alibaba_paired_comparisons.csv"]
    traj.to_csv(paths_out[0], index=False, na_rep="NA")
    machine.to_csv(paths_out[1], index=False, na_rep="NA")
    summary.to_csv(paths_out[2], index=False, na_rep="NA")
    comparisons.to_csv(paths_out[3], index=False, na_rep="NA")

    def f(value) -> str:
        return "NA" if pd.isna(value) else f"{float(value):.6g}"

    lines = ["# V2 Alibaba External Trace Report", "", "## Material Passport", "", "- Evidence class: post-freeze external-domain evaluation on the exact previously used Alibaba 40-machine heldout split; it is not a fresh external confirmation.", "- No Alibaba-specific calibration, threshold, kappa, or machine selection was performed.", "- Matrix: 40 machines × 3 seeds × 2 scenarios × 5 methods = 1200 complete trajectories.", "- Statistical unit: machine; seeds averaged within machine; paired machine-cluster percentile bootstrap, 4000 replicates, seed 2904.", "", "## Protocol and integrity", "", f"Protocol provenance: **{protocol['status']}**. Integrity: **{integrity['status']}**. Pairing: **{pairing['status']}**. Leakage: **{leakage['status']}**.", "", "## External-domain estimates", "", "| Scenario | Method | Lifecycle MSE (95% CI) | MAE | Harmful rate (95% CI) | Downside (95% CI) | Conditional harmful | Beneficial recall | Commit rate | Runtime/stage (s) |", "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for row in summary.itertuples():
        lines.append(f"| {row.scenario} | {row.method} | {f(row.lifecycle_mse)} [{f(row.lifecycle_mse_ci_low)}, {f(row.lifecycle_mse_ci_high)}] | {f(row.lifecycle_mae)} | {f(row.harmful_commit_rate)} [{f(row.harmful_commit_rate_ci_low)}, {f(row.harmful_commit_rate_ci_high)}] | {f(row.average_downside)} [{f(row.average_downside_ci_low)}, {f(row.average_downside_ci_high)}] | {f(row.conditional_harmful_rate)} | {f(row.beneficial_commit_recall)} | {f(row.commit_rate)} | {f(row.mean_maintenance_time_s)} |")
    lines += ["", "## Proposed paired differences", "", "Negative values favor Proposed for lifecycle MSE, harmful rate, downside, and runtime. All unfavorable and inconclusive comparisons are retained.", "", "| Scenario | Baseline | Metric | Difference (95% CI) | Relative change |", "|---|---|---|---:|---:|"]
    for row in comparisons[comparisons.metric.isin(["lifecycle_mse", "harmful_commit_rate", "average_downside", "beneficial_commit_recall", "commit_rate"])].itertuples():
        lines.append(f"| {row.scenario} | {row.baseline} | {row.metric} | {f(row.difference)} [{f(row.ci_low)}, {f(row.ci_high)}] | {f(row.relative_percent)}% |")
    lines += ["", "## Claim boundary", "", "This experiment can support a conditional external-domain transfer claim. It cannot establish fresh confirmation, architecture invariance, or universal superiority. Any clean/mixed tradeoff and every confidence interval crossing zero remain part of the scientific conclusion.", "", "## Output hashes", ""]
    for path in paths_out:
        lines.append(f"- `{path.relative_to(ROOT)}`: `{sha(path)}`")
    report = ROOT / "V2_ALIBABA_EXTERNAL_TRACE_REPORT.md"
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    report_hash = sha(report)
    report.with_suffix(report.suffix + ".sha256").write_text(report_hash + "\n", encoding="ascii")
    atomic_json(audit_dir / "alibaba_output_hash_manifest.json", {"status": "PASS", "report_sha256": report_hash, "result_hashes": {path.name: sha(path) for path in paths_out}, "audit_hashes": {path.name: sha(path) for path in audit_dir.glob("*.json")}})
    atomic_json(out / "execution_status.json", {"state": "ALIBABA_EXTERNAL_COMPLETE", "phase": "v2_alibaba_external_trace", "completed": 1200, "expected": 1200, "integrity": "PASS", "pairing": "PASS", "leakage": "PASS", "report": str(report), "report_sha256": report_hash, "warning": None, "updated_at": now()})
    print(json.dumps({"state": "ALIBABA_EXTERNAL_COMPLETE", "report": str(report)}, indent=2))


if __name__ == "__main__":
    main()
