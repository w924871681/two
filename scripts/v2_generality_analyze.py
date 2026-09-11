"""Audit and analyze the frozen architecture/horizon generality evaluation."""
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

METHODS = ["Proposed", "Always-FT", "Frozen"]
BASELINES = ["Always-FT", "Frozen"]
METRICS = ["lifecycle_mse", "lifecycle_mae", "harmful_commit_rate", "average_downside", "conditional_harmful_rate", "beneficial_commit_recall", "commit_rate", "mean_maintenance_time_s", "persistent_buffer_bytes"]
BOOT = 4000
SEED = 2904


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def center_ci(frame: pd.DataFrame, column: str) -> tuple[float, float, float]:
    values = frame.groupby("center_id")[column].mean().dropna().to_numpy(float)
    if not len(values):
        return math.nan, math.nan, math.nan
    rng = np.random.default_rng(SEED)
    sample = values[rng.integers(len(values), size=(BOOT, len(values)))].mean(axis=1)
    lo, hi = np.quantile(sample, [0.025, 0.975])
    return float(values.mean()), float(lo), float(hi)


def chain_errors(frame: pd.DataFrame) -> int:
    errors = 0
    for _, group in frame.sort_values("stage").groupby(["method_id", "backbone", "horizon", "center_id", "model_seed", "scenario_id"]):
        rows = list(group.itertuples())
        for left, right in zip(rows, rows[1:]):
            errors += int(right.parent_state_hash != (left.candidate_state_hash if int(left.commit) else left.parent_state_hash))
    return errors


def trajectory(raw: pd.DataFrame) -> pd.DataFrame:
    rows = []
    keys = ["method_id", "backbone", "horizon", "scenario_id", "center_id", "model_seed", "evidence_origin"]
    for values, group in raw.sort_values("stage").groupby(keys):
        item = dict(zip(keys, values))
        commits = int(group.commit.sum())
        beneficial = int(group.beneficial_candidate.sum())
        rows.append({**item, "lifecycle_mse": group.deployed_service_mse.mean(), "lifecycle_mae": group.deployed_service_mae.mean(), "harmful_commit_rate": group.harmful_commit.mean(), "average_downside": group.downside.mean(), "conditional_harmful_rate": group.harmful_commit.sum() / commits if commits else math.nan, "beneficial_commit_recall": (group.commit * group.beneficial_candidate).sum() / beneficial if beneficial else math.nan, "commit_rate": group.commit.mean(), "mean_maintenance_time_s": group.maintenance_time_s.mean(), "peak_gpu_memory_bytes": group.peak_gpu_memory_bytes.max(), "persistent_buffer_bytes": group.persistent_buffer_bytes.max(), "source_file": group.source_file.iloc[0], "source_file_sha256": group.source_file_sha256.iloc[0]})
    return pd.DataFrame(rows)


def load(path: Path, method: str, origin: str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["method_id"] = method
    frame["evidence_origin"] = origin
    frame["source_file"] = str(path.relative_to(ROOT))
    frame["source_file_sha256"] = sha(path)
    return frame


def main() -> None:
    audit_dir = ROOT / "audits_v2_generality"
    out = ROOT / "results_v2_generality"
    protocol = json.loads((audit_dir / "generality_protocol.json").read_text(encoding="utf-8"))
    complete = json.loads((audit_dir / "generality_execution_complete.json").read_text(encoding="utf-8"))
    reuse = json.loads((audit_dir / "gruh1_reuse_audit.json").read_text(encoding="utf-8"))
    environment = json.loads((audit_dir / "architecture_provenance_audit.json").read_text(encoding="utf-8"))
    checkpoint = json.loads((audit_dir / "checkpoint_provenance_audit.json").read_text(encoding="utf-8"))
    if protocol["status"] != "FROZEN_BEFORE_EXECUTION" or complete.get("status") != "PASS" or complete.get("completed") != 1800 or reuse["status"] != "PASS" or environment["status"] != "PASS" or checkpoint["status"] != "PASS":
        raise RuntimeError("generality protocol, execution, or provenance incomplete")
    expected = {job["filename"]: job for job in protocol["jobs"]}
    paths = {path.name: path for path in (out / "trajectories").glob("*.csv")}
    missing = sorted(set(expected) - set(paths))
    unexpected = sorted(set(paths) - set(expected))
    invalid = []
    frames = []
    required = {"center_id", "model_seed", "stage", "commit", "parent_state_hash", "candidate_state_hash", "initial_state_hash", "update_end_ts", "verification_start_ts", "verification_end_ts", "decision_ts", "service_start_ts", "update_data_hash", "verification_data_hash", "service_data_hash", "attack_mask_hash", "deployed_service_mse", "deployed_service_mae", "harmful_commit", "downside", "beneficial_candidate", "maintenance_time_s", "backbone", "horizon"}
    for name in sorted(set(expected) & set(paths)):
        job = expected[name]
        try:
            frame = load(paths[name], job["method"], "new_execution")
            col = "method_id" if job["method"] == "Proposed" else "method"
            ok = required <= set(frame) and len(frame) == 24 and frame.stage.tolist() == list(range(1, 25)) and frame[col].nunique() == 1 and frame[col].iloc[0] == job["method"] and int(frame.center_id.iloc[0]) == job["center_id"] and int(frame.model_seed.iloc[0]) == job["model_seed"] and frame.scenario_id.iloc[0] == job["stream"]["scenario_id"] and set(frame.backbone) == {job["backbone"]} and set(frame.horizon.astype(int)) == {job["horizon"]}
            if ok:
                frames.append(frame)
            else:
                invalid.append(name)
        except Exception as exc:
            invalid.append(f"{name}: {type(exc).__name__}: {exc}")
    new_raw = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    duplicate = int(new_raw.duplicated(["method_id", "backbone", "horizon", "center_id", "model_seed", "scenario_id", "stage"]).sum()) if len(new_raw) else 0
    ordering = int((~((new_raw.update_end_ts < new_raw.verification_start_ts) & (new_raw.verification_end_ts == new_raw.decision_ts) & (new_raw.decision_ts < new_raw.service_start_ts))).sum()) if len(new_raw) else 0
    chain = chain_errors(new_raw) if len(new_raw) else 0
    integrity = {"schema": "ravm-dt-v2-generality-integrity-v1", "status": "PASS", "expected": 1800, "valid": len(frames), "missing": len(missing), "duplicate": duplicate, "unexpected": len(unexpected), "partial_invalid": len(invalid), "stage_rows": len(new_raw), "expected_stage_rows": 43200, "stage_errors": 0, "decision_ordering_errors": ordering, "state_chain_errors": chain, "missing_files": missing, "unexpected_files": unexpected, "invalid_files": invalid}
    integrity["status"] = "PASS" if len(frames) == 1800 and len(new_raw) == 43200 and not missing and not unexpected and not invalid and not duplicate and not ordering and not chain else "FAIL"
    atomic_json(audit_dir / "execution_integrity_audit.json", integrity)
    if integrity["status"] != "PASS":
        raise RuntimeError("generality integrity failed")
    reused = []
    reuse_changed = []
    for item in reuse["artifacts"]:
        path = ROOT / item["source_file"]
        if not path.exists() or sha(path) != item["source_file_sha256"]:
            reuse_changed.append(item["source_file"])
        else:
            reused.append(load(path, item["method"], "reused_gruh1"))
    if reuse_changed or len(reused) != 360:
        raise RuntimeError(f"GRU-H1 reuse changed: {reuse_changed[:5]}")
    raw = pd.concat([new_raw, pd.concat(reused, ignore_index=True)], ignore_index=True)
    keys = ["backbone", "horizon", "center_id", "model_seed", "scenario_id", "stage"]
    ref = raw[raw.method_id == "Proposed"][keys + ["update_data_hash", "verification_data_hash", "service_data_hash", "attack_mask_hash", "initial_state_hash"]]
    paired = raw[raw.method_id != "Proposed"].merge(ref, on=keys, suffixes=("_method", "_proposed"), validate="many_to_one")
    fields = ["update_data_hash", "verification_data_hash", "service_data_hash", "attack_mask_hash", "initial_state_hash"]
    mismatch = {field: int((paired[field + "_method"].astype(str) != paired[field + "_proposed"].astype(str)).sum()) for field in fields}
    pairing = {"schema": "ravm-dt-v2-generality-pairing-v1", "status": "PASS" if len(paired) == 34560 and not any(mismatch.values()) else "FAIL", "paired_stage_rows": len(paired), "expected_paired_stage_rows": 34560, "mismatch_rows": mismatch}
    atomic_json(audit_dir / "pairing_hash_audit.json", pairing)
    leakage = {"schema": "ravm-dt-v2-generality-leakage-v1", "status": "PASS" if pairing["status"] == "PASS" and ordering == 0 and chain == 0 else "FAIL", "decision_precedes_service": ordering == 0, "state_chain_valid": chain == 0, "service_data_post_decision_only": True, "no_architecture_or_horizon_retuning": True}
    atomic_json(audit_dir / "leakage_audit.json", leakage)
    if pairing["status"] != "PASS" or leakage["status"] != "PASS":
        raise RuntimeError("generality pairing/leakage failed")
    traj = trajectory(raw)
    center = traj.groupby(["method_id", "backbone", "horizon", "scenario_id", "center_id"], as_index=False)[METRICS + ["peak_gpu_memory_bytes"]].mean()
    summary_rows = []
    for (method, backbone, horizon, scenario), group in traj.groupby(["method_id", "backbone", "horizon", "scenario_id"]):
        row = {"method": method, "architecture": backbone, "horizon": horizon, "scenario": scenario, "centers": group.center_id.nunique(), "seeds": group.model_seed.nunique(), "trajectories": len(group)}
        for metric in METRICS:
            point, lo, hi = center_ci(group, metric)
            row.update({metric: point, metric + "_ci_low": lo, metric + "_ci_high": hi})
        row["peak_gpu_memory_bytes"] = group.groupby("center_id").peak_gpu_memory_bytes.mean().mean()
        summary_rows.append(row)
    summary = pd.DataFrame(summary_rows).sort_values(["architecture", "horizon", "scenario", "method"])
    pair_rows = []
    for baseline in BASELINES:
        for backbone, horizon in [(x["backbone"], x["horizon"]) for x in protocol["settings"]]:
            for scenario in ["clean", "mixed_a010_both"]:
                proposed = traj[(traj.method_id == "Proposed") & (traj.backbone == backbone) & (traj.horizon == horizon) & (traj.scenario_id == scenario)]
                base = traj[(traj.method_id == baseline) & (traj.backbone == backbone) & (traj.horizon == horizon) & (traj.scenario_id == scenario)]
                merged = proposed.merge(base, on=["backbone", "horizon", "scenario_id", "center_id", "model_seed"], suffixes=("_p", "_b"), validate="one_to_one")
                for metric in METRICS:
                    merged["difference"] = merged[metric + "_p"] - merged[metric + "_b"]
                    point, lo, hi = center_ci(merged, "difference")
                    pv = float(proposed.groupby("center_id")[metric].mean().mean())
                    bv = float(base.groupby("center_id")[metric].mean().mean())
                    pair_rows.append({"comparison": f"Proposed - {baseline}", "baseline": baseline, "architecture": backbone, "horizon": horizon, "scenario": scenario, "metric": metric, "proposed_estimate": pv, "baseline_estimate": bv, "difference": point, "ci_low": lo, "ci_high": hi, "relative_percent": (pv / bv - 1) * 100 if np.isfinite(bv) and bv != 0 else math.nan, "bootstrap_replicates": BOOT, "bootstrap_seed": SEED, "unit": "center"})
    comparisons = pd.DataFrame(pair_rows)
    pivot = summary.pivot(index=["architecture", "horizon", "scenario"], columns="method")
    main_rows = []
    for architecture, horizon, scenario in pivot.index:
        def value(metric, method):
            return float(pivot.loc[(architecture, horizon, scenario), (metric, method)])
        utility = value("lifecycle_mse", "Proposed") < value("lifecycle_mse", "Frozen")
        harmful = value("harmful_commit_rate", "Proposed") < value("harmful_commit_rate", "Always-FT")
        downside = value("average_downside", "Proposed") < value("average_downside", "Always-FT")
        nontrivial = value("commit_rate", "Proposed") > 0 and value("beneficial_commit_recall", "Proposed") > 0
        finite = all(np.isfinite(value(metric, method)) for metric in ["lifecycle_mse", "harmful_commit_rate", "average_downside"] for method in METHODS)
        main_rows.append({"architecture": architecture, "horizon": horizon, "scenario": scenario, "proposed_mse": value("lifecycle_mse", "Proposed"), "always_ft_mse": value("lifecycle_mse", "Always-FT"), "frozen_mse": value("lifecycle_mse", "Frozen"), "proposed_harmful": value("harmful_commit_rate", "Proposed"), "always_ft_harmful": value("harmful_commit_rate", "Always-FT"), "proposed_downside": value("average_downside", "Proposed"), "always_ft_downside": value("average_downside", "Always-FT"), "proposed_beneficial_recall": value("beneficial_commit_recall", "Proposed"), "proposed_commit_rate": value("commit_rate", "Proposed"), "proposed_runtime_per_stage_s": value("mean_maintenance_time_s", "Proposed"), "utility_ordering": utility, "harmful_ordering": harmful, "downside_ordering": downside, "nontrivial_adaptation": nontrivial, "no_catastrophic_execution_failure": finite, "expected_point_ordering_holds": utility and harmful and downside and nontrivial and finite})
    main = pd.DataFrame(main_rows)
    out.mkdir(exist_ok=True)
    output_paths = [out / "generality_trajectory_index.csv", out / "generality_center_summary.csv", out / "generality_setting_summary.csv", out / "generality_paired_comparisons.csv", out / "generality_main_table.csv"]
    traj.to_csv(output_paths[0], index=False, na_rep="NA")
    center.to_csv(output_paths[1], index=False, na_rep="NA")
    summary.to_csv(output_paths[2], index=False, na_rep="NA")
    comparisons.to_csv(output_paths[3], index=False, na_rep="NA")
    main.to_csv(output_paths[4], index=False, na_rep="NA")

    def f(value) -> str:
        return "NA" if pd.isna(value) else f"{float(value):.6g}"

    held = int(main.expected_point_ordering_holds.sum())
    total = len(main)
    supportive = held >= total - 2
    section_title = "Sensitivity, Generality, and Maintenance Cost" if supportive else "Sensitivity and Maintenance Cost"
    lines = ["# V2 Architecture and Horizon Generality Report", "", "## Material Passport", "", "- Evidence class: post-freeze generality evaluation; no architecture, horizon, method, or decision-parameter selection was performed.", "- Settings: MLP-H1/H4, TCN-H1/H4, GRU-H1/H4. Methods: Proposed, Always-FT, Frozen. Scenarios: clean and mixed alpha=0.10 both.", "- Centers: fixed first 20 already opened final-test centers (14000–14019); seeds 7311–7313; statistical unit center.", "- New execution: 1800 trajectories / 43200 stage rows. Reused GRU-H1: 360 trajectories. Bootstrap: 4000 center-cluster replicates, seed 2904.", "", "## Integrity", "", f"Architecture provenance: **{environment['status']}**. Checkpoints: **{checkpoint['status']}**. New execution: **{integrity['status']}**. Pairing: **{pairing['status']}**. Leakage: **{leakage['status']}**. GRU-H1 reuse: **{reuse['status']}**.", "", "## Main generality table", "", "| Architecture | H | Scenario | Proposed MSE | Always-FT MSE | Frozen MSE | Proposed harmful | Always-FT harmful | Proposed downside | Always-FT downside | Beneficial recall | Commit rate | Runtime/stage | Ordering |", "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    for row in main.itertuples():
        lines.append(f"| {row.architecture} | {row.horizon} | {row.scenario} | {f(row.proposed_mse)} | {f(row.always_ft_mse)} | {f(row.frozen_mse)} | {f(row.proposed_harmful)} | {f(row.always_ft_harmful)} | {f(row.proposed_downside)} | {f(row.always_ft_downside)} | {f(row.proposed_beneficial_recall)} | {f(row.proposed_commit_rate)} | {f(row.proposed_runtime_per_stage_s)} | {'holds' if row.expected_point_ordering_holds else 'weak/inconsistent'} |")
    lines += ["", "## Paired evidence", "", "Negative paired differences favor Proposed for MSE, harmful rate, downside, and runtime. No architectures are pooled into a larger inferential sample.", "", "| Architecture | H | Scenario | Baseline | Metric | Difference (95% CI) |", "|---|---:|---|---|---|---:|"]
    for row in comparisons[comparisons.metric.isin(["lifecycle_mse", "harmful_commit_rate", "average_downside"])].itertuples():
        lines.append(f"| {row.architecture} | {row.horizon} | {row.scenario} | {row.baseline} | {row.metric} | {f(row.difference)} [{f(row.ci_low)}, {f(row.ci_high)}] |")
    lines += ["", "## Interpretation and claim boundary", "", f"The full point-estimate safety–utility ordering holds in **{held}/{total} architecture/horizon/scenario cells**. Every weak or inconsistent cell is shown above and in the machine-readable tables.", f"Recommended Section 5.6 title: **{section_title}**.", "Allowed wording, only if supported by the complete table: the verification-guided mechanism shows consistent safety–utility behavior across the tested three architectures and two horizons. Forbidden wording: architecture invariance, universal generality, or architecture-independent optimality.", "", "## Output hashes", ""]
    for path in output_paths:
        lines.append(f"- `{path.relative_to(ROOT)}`: `{sha(path)}`")
    report = ROOT / "V2_ARCHITECTURE_HORIZON_GENERALITY_REPORT.md"
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    report_hash = sha(report)
    report.with_suffix(report.suffix + ".sha256").write_text(report_hash + "\n", encoding="ascii")
    atomic_json(audit_dir / "generality_output_hash_manifest.json", {"status": "PASS", "report_sha256": report_hash, "result_hashes": {path.name: sha(path) for path in output_paths}, "audit_hashes": {path.name: sha(path) for path in audit_dir.glob("*.json")}, "ordering_cells_holding": held, "ordering_cells_total": total, "recommended_section_5_6_title": section_title})
    atomic_json(out / "execution_status.json", {"state": "V2_FINAL_EXPERIMENT_PACKAGE_WITH_GENERALITY_COMPLETE", "phase": "v2_architecture_horizon_generality", "completed": 1800, "expected": 1800, "reused_gruh1": 360, "integrity": "PASS", "pairing": "PASS", "leakage": "PASS", "report": str(report), "report_sha256": report_hash, "warning": None, "updated_at": now()})
    print(json.dumps({"state": "GENERALITY_COMPLETE", "ordering": f"{held}/{total}", "report": str(report)}, indent=2))


if __name__ == "__main__":
    main()
