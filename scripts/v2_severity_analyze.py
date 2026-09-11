"""Integrity, pairing, leakage, and frozen statistical analysis for severity."""
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

METHODS = ["Proposed", "Always-FT", "ER", "Huber-FT"]
BASELINES = METHODS[1:]
KINDS = ["mixed", "persistent_bias", "replay"]
ALPHAS = [0.05, 0.10, 0.20]
BOOT = 4000
SEED = 2904
METRICS = ["lifecycle_mse", "lifecycle_mae", "harmful_commit_rate", "average_downside", "conditional_harmful_rate", "beneficial_commit_recall", "commit_rate", "maximum_retain_streak"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def longest(values) -> int:
    best = current = 0
    for value in values.astype(int):
        current = 0 if value else current + 1
        best = max(best, current)
    return best


def center_ci(frame: pd.DataFrame, column: str) -> tuple[float, float, float]:
    values = frame.groupby("center_id")[column].mean().dropna().to_numpy(float)
    if not len(values):
        return math.nan, math.nan, math.nan
    rng = np.random.default_rng(SEED)
    sampled = values[rng.integers(len(values), size=(BOOT, len(values)))].mean(axis=1)
    lo, hi = np.quantile(sampled, [0.025, 0.975])
    return float(values.mean()), float(lo), float(hi)


def scientific_chain_errors(frame: pd.DataFrame) -> int:
    errors = 0
    for _, group in frame.sort_values("stage").groupby(["method_id", "center_id", "model_seed", "scenario_id"]):
        rows = list(group.itertuples())
        for left, right in zip(rows, rows[1:]):
            expected = left.candidate_state_hash if int(left.commit) else left.parent_state_hash
            errors += int(right.parent_state_hash != expected)
    return errors


def trajectory(raw: pd.DataFrame) -> pd.DataFrame:
    rows = []
    keys = ["method_id", "attack_family", "attack_alpha", "attack_location", "scenario_id", "center_id", "model_seed", "evidence_origin"]
    for values, group in raw.sort_values("stage").groupby(keys):
        item = dict(zip(keys, values))
        commits = int(group.commit.sum())
        beneficial = int(group.beneficial_candidate.sum())
        rows.append({
            **item,
            "lifecycle_mse": float(group.deployed_service_mse.mean()),
            "lifecycle_mae": float(group.deployed_service_mae.mean()),
            "harmful_commit_rate": float(group.harmful_commit.mean()),
            "average_downside": float(group.downside.mean()),
            "conditional_harmful_rate": float(group.harmful_commit.sum() / commits) if commits else math.nan,
            "beneficial_commit_recall": float((group.commit * group.beneficial_candidate).sum() / beneficial) if beneficial else math.nan,
            "commit_rate": float(group.commit.mean()),
            "maximum_retain_streak": longest(group.commit),
            "mean_maintenance_time_s": float(group.maintenance_time_s.mean()),
            "peak_gpu_memory_bytes": float(group.peak_gpu_memory_bytes.max()),
            "persistent_buffer_bytes": float(group.persistent_buffer_bytes.max()),
            "source_file": group.source_file.iloc[0],
            "source_file_sha256": group.source_file_sha256.iloc[0],
        })
    return pd.DataFrame(rows)


def load_one(path: Path, method: str, origin: str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["method_id"] = method
    frame["attack_family"] = frame.attack_type
    frame["attack_alpha"] = frame.attack_alpha.astype(float)
    frame["evidence_origin"] = origin
    frame["source_file"] = str(path.relative_to(ROOT))
    frame["source_file_sha256"] = sha(path)
    return frame


def main() -> None:
    audit_dir = ROOT / "audits_v2_severity"
    out = ROOT / "results_v2_severity"
    manifest_path = audit_dir / "severity_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    complete = json.loads((audit_dir / "severity_execution_complete.json").read_text(encoding="utf-8"))
    reuse = json.loads((audit_dir / "alpha010_reuse_audit.json").read_text(encoding="utf-8"))
    if complete.get("status") != "PASS" or complete.get("completed") != 2160 or reuse.get("status") != "PASS":
        raise RuntimeError("severity execution or alpha=.10 reuse is incomplete")

    expected = {job["filename"]: job for job in manifest["jobs"]}
    paths = {path.name: path for path in (out / "trajectories").glob("*.csv")}
    missing = sorted(set(expected) - set(paths))
    unexpected = sorted(set(paths) - set(expected))
    invalid = []
    new_frames = []
    required = {"center_id", "model_seed", "stage", "commit", "parent_state_hash", "candidate_state_hash", "initial_state_hash", "update_end_ts", "verification_start_ts", "verification_end_ts", "decision_ts", "service_start_ts", "update_data_hash", "verification_data_hash", "service_data_hash", "attack_mask_hash", "deployed_service_mse", "deployed_service_mae", "harmful_commit", "downside", "beneficial_candidate", "maintenance_time_s", "attack_alpha", "attack_type", "attack_location"}
    for name in sorted(set(expected) & set(paths)):
        job = expected[name]
        try:
            frame = load_one(paths[name], job["method"], "new_execution")
            method_col = "method_id" if job["method"] == "Proposed" else "method"
            expected_method = "Proposed" if job["method"] == "Proposed" else job["method"]
            ok = required <= set(frame) and len(frame) == 24 and frame.stage.tolist() == list(range(1, 25)) and frame[method_col].nunique() == 1 and frame[method_col].iloc[0] == expected_method and int(frame.center_id.iloc[0]) == job["center_id"] and int(frame.model_seed.iloc[0]) == job["model_seed"] and frame.scenario_id.nunique() == 1 and frame.scenario_id.iloc[0] == job["stream"]["scenario_id"]
            if not ok:
                invalid.append(name)
            else:
                new_frames.append(frame)
        except Exception as exc:
            invalid.append(f"{name}: {type(exc).__name__}: {exc}")
    new_raw = pd.concat(new_frames, ignore_index=True) if new_frames else pd.DataFrame()
    new_duplicate = int(new_raw.duplicated(["method_id", "center_id", "model_seed", "scenario_id", "stage"]).sum()) if len(new_raw) else 0
    new_ordering = int((~((new_raw.update_end_ts < new_raw.verification_start_ts) & (new_raw.verification_end_ts == new_raw.decision_ts) & (new_raw.decision_ts < new_raw.service_start_ts))).sum()) if len(new_raw) else 0
    new_chain = scientific_chain_errors(new_raw) if len(new_raw) else 0
    integrity = {
        "schema": "ravm-dt-v2-severity-integrity-v1", "status": "PASS", "expected_new": 2160,
        "valid_new": len(new_frames), "missing": len(missing), "duplicate": new_duplicate, "unexpected": len(unexpected),
        "partial_invalid": len(invalid), "stage_rows": len(new_raw), "expected_stage_rows": 51840,
        "decision_ordering_errors": new_ordering, "state_chain_errors": new_chain,
        "missing_files": missing, "unexpected_files": unexpected, "invalid_files": invalid,
    }
    integrity["status"] = "PASS" if len(new_frames) == 2160 and len(new_raw) == 51840 and not missing and not unexpected and not invalid and not new_duplicate and not new_ordering and not new_chain else "FAIL"
    atomic_json(audit_dir / "severity_execution_integrity_audit.json", integrity)
    if integrity["status"] != "PASS":
        atomic_json(out / "execution_status.json", {"state": "SEVERITY_SWEEP_INCOMPLETE", "integrity": integrity})
        raise RuntimeError("severity integrity failed")

    reused_frames = []
    reuse_hash_failures = []
    for item in reuse["artifacts"]:
        path = ROOT / item["source_file"]
        if not path.exists() or sha(path) != item["source_file_sha256"]:
            reuse_hash_failures.append(item["source_file"])
            continue
        reused_frames.append(load_one(path, item["method"], "reused_alpha010"))
    if reuse_hash_failures or len(reused_frames) != 1080:
        raise RuntimeError(f"alpha=.10 artifacts changed after freeze: {reuse_hash_failures[:5]}")
    reused_raw = pd.concat(reused_frames, ignore_index=True)
    raw = pd.concat([new_raw, reused_raw], ignore_index=True)
    all_duplicate = int(raw.duplicated(["method_id", "center_id", "model_seed", "scenario_id", "stage"]).sum())

    pair_keys = ["center_id", "model_seed", "scenario_id", "stage"]
    ref = raw[raw.method_id == "Proposed"][pair_keys + ["update_data_hash", "verification_data_hash", "service_data_hash", "attack_mask_hash", "initial_state_hash"]]
    other = raw[raw.method_id != "Proposed"]
    paired = other.merge(ref, on=pair_keys, suffixes=("_method", "_proposed"), validate="many_to_one")
    fields = ["update_data_hash", "verification_data_hash", "service_data_hash", "attack_mask_hash", "initial_state_hash"]
    mismatch = {field: int((paired[field + "_method"].astype(str) != paired[field + "_proposed"].astype(str)).sum()) for field in fields}
    expected_paired_stage_rows = len(BASELINES) * len(KINDS) * len(ALPHAS) * 30 * 3 * 24
    pairing = {"schema": "ravm-dt-v2-severity-pairing-v1", "status": "PASS" if len(paired) == expected_paired_stage_rows and not any(mismatch.values()) and all_duplicate == 0 else "INVALID_SEVERITY_PAIRING", "paired_stage_rows": len(paired), "expected_paired_stage_rows": expected_paired_stage_rows, "expected_factorization": {"baselines": len(BASELINES), "attack_families": len(KINDS), "alpha_levels": len(ALPHAS), "centers": 30, "seeds": 3, "stages": 24}, "duplicate_combined_stage_keys": all_duplicate, "mismatch_rows": mismatch, "pairing_unit": "center x seed x alpha x scenario x stage"}
    atomic_json(audit_dir / "severity_pairing_audit.json", pairing)
    combined_ordering = int((~((raw.update_end_ts < raw.verification_start_ts) & (raw.verification_end_ts == raw.decision_ts) & (raw.decision_ts < raw.service_start_ts))).sum())
    leakage = {"schema": "ravm-dt-v2-severity-leakage-v1", "status": "PASS" if pairing["status"] == "PASS" and combined_ordering == 0 else "FAIL", "decision_ordering_errors": combined_ordering, "final_test_centers_already_opened": True, "fresh_or_unseen_claim": False, "service_data_post_decision_only": True, "scientific_core_hashes_unchanged": sha(ROOT / "core/v2_engine.py") == manifest["scientific_hashes"]["core/v2_engine.py"] and sha(ROOT / "core/engine.py") == manifest["scientific_hashes"]["core/engine.py"], "severity_results_not_used_for_tuning": True}
    atomic_json(audit_dir / "severity_leakage_audit.json", leakage)
    if pairing["status"] != "PASS" or leakage["status"] != "PASS":
        atomic_json(out / "execution_status.json", {"state": "SEVERITY_SWEEP_INCOMPLETE", "pairing": pairing["status"], "leakage": leakage["status"]})
        raise RuntimeError("severity pairing/leakage failed")

    traj = trajectory(raw)
    summary_rows = []
    for (method, family, alpha), group in traj.groupby(["method_id", "attack_family", "attack_alpha"]):
        row = {"method": method, "attack_type": family, "alpha": alpha, "attack_location": group.attack_location.iloc[0], "centers": group.center_id.nunique(), "seeds": group.model_seed.nunique(), "trajectories": len(group)}
        for metric in METRICS:
            point, lo, hi = center_ci(group, metric)
            row.update({metric: point, metric + "_ci_low": lo, metric + "_ci_high": hi})
        row["harmful_absolute_pass"] = bool(row["harmful_commit_rate"] <= manifest["analysis_plan"]["rho"])
        row["downside_absolute_pass"] = bool(row["average_downside"] <= manifest["analysis_plan"]["epsilon"])
        summary_rows.append(row)
    summary = pd.DataFrame(summary_rows).sort_values(["attack_type", "alpha", "method"])

    pair_rows = []
    for baseline in BASELINES:
        for family in KINDS:
            for alpha in ALPHAS:
                proposed = traj[(traj.method_id == "Proposed") & (traj.attack_family == family) & np.isclose(traj.attack_alpha, alpha)]
                base = traj[(traj.method_id == baseline) & (traj.attack_family == family) & np.isclose(traj.attack_alpha, alpha)]
                merged = proposed.merge(base, on=["attack_family", "attack_alpha", "attack_location", "center_id", "model_seed"], suffixes=("_p", "_b"), validate="one_to_one")
                for metric in METRICS:
                    merged["difference"] = merged[metric + "_p"] - merged[metric + "_b"]
                    point, lo, hi = center_ci(merged, "difference")
                    pv = float(proposed.groupby("center_id")[metric].mean().mean())
                    bv = float(base.groupby("center_id")[metric].mean().mean())
                    pair_rows.append({"comparison": f"Proposed - {baseline}", "baseline": baseline, "attack_type": family, "alpha": alpha, "metric": metric, "proposed_estimate": pv, "baseline_estimate": bv, "difference": point, "ci_low": lo, "ci_high": hi, "relative_percent": (pv / bv - 1) * 100 if np.isfinite(bv) and bv != 0 else math.nan, "bootstrap_replicates": BOOT, "bootstrap_seed": SEED, "unit": "center"})
    comparisons = pd.DataFrame(pair_rows)
    trend = summary[["method", "attack_type", "alpha", "lifecycle_mse", "lifecycle_mae", "harmful_commit_rate", "average_downside", "conditional_harmful_rate", "beneficial_commit_recall", "commit_rate", "maximum_retain_streak", "harmful_absolute_pass", "downside_absolute_pass"]].copy()
    trend["delta_lifecycle_mse_from_previous_alpha"] = trend.sort_values("alpha").groupby(["method", "attack_type"])["lifecycle_mse"].diff()
    trend["delta_harmful_from_previous_alpha"] = trend.sort_values("alpha").groupby(["method", "attack_type"])["harmful_commit_rate"].diff()
    trend["delta_downside_from_previous_alpha"] = trend.sort_values("alpha").groupby(["method", "attack_type"])["average_downside"].diff()

    out.mkdir(exist_ok=True)
    traj_path = out / "severity_trajectory_index.csv"
    summary_path = out / "severity_scenario_summary.csv"
    pairs_path = out / "severity_paired_comparisons.csv"
    trend_path = out / "severity_trend_table.csv"
    traj.to_csv(traj_path, index=False, na_rep="NA")
    summary.to_csv(summary_path, index=False, na_rep="NA")
    comparisons.to_csv(pairs_path, index=False, na_rep="NA")
    trend.to_csv(trend_path, index=False, na_rep="NA")

    def f(value) -> str:
        return "NA" if pd.isna(value) else f"{float(value):.6g}"

    lines = [
        "# V2 Robustness Severity Report", "",
        "## Material Passport", "",
        "- Evidence class: frozen Final V2 final-test severity extension plus exact reuse of prior alpha=0.10 final-test trajectories.",
        "- Final-test centers 14000–14029 were already opened on 2026-09-11; this report makes no fresh/unseen claim.",
        f"- Frozen Final V2 config SHA-256: `{manifest['scientific_hashes']['final_v2_config']}`.",
        f"- New execution: 2160 complete trajectories / 51840 stage rows. Reused alpha=0.10: 1080 trajectories. Combined: {len(traj)} trajectories.",
        "- Statistical unit: center; seeds averaged within center; paired center-cluster percentile bootstrap, 4000 replicates, seed 2904.", "",
        "## Integrity and provenance", "",
        f"Execution integrity: **{integrity['status']}**. Pairing: **{pairing['status']}**. Leakage: **{leakage['status']}**. Alpha=0.10 reuse: **{reuse['status']}**.",
        "No alpha=0.10 trajectory was rerun. No severity result was used for parameter selection or to modify Final V2.", "",
        "## Scenario estimates", "",
        "| Attack | Alpha | Method | Lifecycle MSE (95% CI) | Harmful rate (95% CI) | Downside (95% CI) | Conditional harmful | Beneficial recall | Commit rate | Absolute safety |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in summary.itertuples():
        absolute = "PASS" if row.harmful_absolute_pass and row.downside_absolute_pass else "FAIL"
        lines.append(f"| {row.attack_type} | {row.alpha:.2f} | {row.method} | {f(row.lifecycle_mse)} [{f(row.lifecycle_mse_ci_low)}, {f(row.lifecycle_mse_ci_high)}] | {f(row.harmful_commit_rate)} [{f(row.harmful_commit_rate_ci_low)}, {f(row.harmful_commit_rate_ci_high)}] | {f(row.average_downside)} [{f(row.average_downside_ci_low)}, {f(row.average_downside_ci_high)}] | {f(row.conditional_harmful_rate)} | {f(row.beneficial_commit_recall)} | {f(row.commit_rate)} | {absolute} |")
    lines += ["", "## Proposed paired differences", "", "Negative differences favor Proposed for lifecycle MSE, harmful rate, and downside. All estimates below preserve favorable, adverse, and inconclusive findings.", "", "| Attack | Alpha | Baseline | Metric | Difference (95% CI) | Relative change |", "|---|---:|---|---|---:|---:|"]
    focus = comparisons[comparisons.metric.isin(["lifecycle_mse", "harmful_commit_rate", "average_downside", "beneficial_commit_recall", "commit_rate"])]
    for row in focus.itertuples():
        lines.append(f"| {row.attack_type} | {row.alpha:.2f} | {row.baseline} | {row.metric} | {f(row.difference)} [{f(row.ci_low)}, {f(row.ci_high)}] | {f(row.relative_percent)}% |")
    lines += ["", "## Severity interpretation boundary", "", "The alpha sequence is a predeclared descriptive robustness sweep. It does not fit or select a new threshold. A confidence interval crossing zero is recorded as inconclusive rather than treated as equivalence. Any absolute safety failure or wholly adverse paired interval remains visible in the tables and is not removed from the report.", "", "## Output hashes", ""]
    for path in [traj_path, summary_path, pairs_path, trend_path]:
        lines.append(f"- `{path.relative_to(ROOT)}`: `{sha(path)}`")
    report = ROOT / "V2_ROBUSTNESS_SEVERITY_REPORT.md"
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    report_hash = sha(report)
    report.with_suffix(report.suffix + ".sha256").write_text(report_hash + "\n", encoding="ascii")
    audit_hashes = {path.name: sha(path) for path in audit_dir.glob("*.json")}
    atomic_json(audit_dir / "severity_output_hash_manifest.json", {"status": "PASS", "report_sha256": report_hash, "result_hashes": {path.name: sha(path) for path in [traj_path, summary_path, pairs_path, trend_path]}, "audit_hashes": audit_hashes})
    atomic_json(out / "execution_status.json", {"state": "SEVERITY_SWEEP_COMPLETE", "phase": "robustness_severity", "completed": 2160, "expected": 2160, "reused_alpha010": 1080, "integrity": "PASS", "pairing": "PASS", "leakage": "PASS", "report": str(report), "report_sha256": report_hash, "warning": None, "updated_at": now()})
    print(json.dumps({"state": "SEVERITY_SWEEP_COMPLETE", "combined_trajectories": len(traj), "report": str(report)}, indent=2))


if __name__ == "__main__":
    main()
