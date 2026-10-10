"""Analyze V2 development/calibration outputs and apply frozen selection rules."""
from __future__ import annotations

import argparse
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
from scripts.v2_runner import V1_GATE, structural_grid


BOOTSTRAP = 4000
BOOTSTRAP_SEED = 2904
RHO = 0.05
EPSILON = 5.6036475532487204e-05


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


def json_record(series: pd.Series) -> dict:
    """Convert a pandas row to strict JSON without changing numeric CSV outputs."""
    return {key: (None if pd.isna(value) else value) for key, value in series.to_dict().items()}


def ci_mean(values: pd.DataFrame, value: str) -> tuple[float, float, float]:
    center_values = values.groupby("center_id")[value].mean().dropna().to_numpy(dtype=float)
    if not len(center_values):
        return math.nan, math.nan, math.nan
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    samples = center_values[rng.integers(len(center_values), size=(BOOTSTRAP, len(center_values)))].mean(axis=1)
    return float(center_values.mean()), *map(float, np.quantile(samples, [0.025, 0.975]))


def ci_ratio(values: pd.DataFrame, numerator: str, denominator: str) -> tuple[float, float, float]:
    centers = values.groupby("center_id")[[numerator, denominator]].sum().to_numpy(dtype=float)
    if not len(centers) or centers[:, 1].sum() <= 0:
        return math.nan, math.nan, math.nan
    point = float(centers[:, 0].sum() / centers[:, 1].sum())
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    sampled = centers[rng.integers(len(centers), size=(BOOTSTRAP, len(centers)))]
    den = sampled[:, :, 1].sum(axis=1)
    num = sampled[:, :, 0].sum(axis=1)
    ratios = np.divide(num, den, out=np.full_like(num, np.nan), where=den > 0)
    return point, *map(float, np.nanquantile(ratios, [0.025, 0.975]))


def longest_retain(values: pd.Series) -> int:
    best = current = 0
    for committed in values.astype(int):
        current = 0 if committed else current + 1
        best = max(best, current)
    return best


def read_phase(phase: str) -> pd.DataFrame:
    folder = ROOT / "results_v2_dev" / phase / "trajectories"
    paths = sorted(folder.glob("*.csv"))
    if not paths:
        raise RuntimeError(f"no {phase} trajectories")
    frames = [pd.read_csv(path) for path in paths]
    data = pd.concat(frames, ignore_index=True)
    data["analysis_scenario"] = np.where(data.scenario_id == "clean", data.drift_regime, data.scenario_id)
    if phase == "development":
        data["arm_id"] = data.structure_id
    else:
        data["arm_id"] = data.apply(lambda r: f"kr{r.kappa_rec:g}_kh{r.kappa_hist:g}", axis=1)
    return data


def integrity(data: pd.DataFrame, phase: str, files: int) -> dict:
    key = ["arm_id", "analysis_scenario", "center_id", "model_seed", "stage"]
    duplicates = int(data.duplicated(key).sum())
    groups = data.groupby(key[:-1]).stage.agg(["count", "nunique", "min", "max"])
    invalid = int(((groups["count"] != 24) | (groups["nunique"] != 24) | (groups["min"] != 1) | (groups["max"] != 24)).sum())
    forbidden = sorted(set(data.center_id).difference(range(11000, 11020) if phase == "development" else range(12000, 12020)))
    expected_trajectories = 4800 if phase == "development" else 1920
    report = {
        "status": "PASS" if not duplicates and not invalid and not forbidden and len(groups) == expected_trajectories else "FAIL",
        "phase": phase,
        "trajectory_files": files,
        "trajectory_groups": len(groups),
        "expected_trajectories": expected_trajectories,
        "stage_rows": len(data),
        "duplicate_scientific_keys": duplicates,
        "invalid_stage_sequences": invalid,
        "forbidden_centers": forbidden,
        "service_access": "evaluation-only after decision token, enforced by core.v2_engine",
        "v2_confirmatory_heldout_accessed": False,
    }
    if report["status"] != "PASS":
        raise RuntimeError(f"V2 {phase} integrity failed: {report}")
    return report


def trajectory_metrics(data: pd.DataFrame) -> pd.DataFrame:
    keys = ["arm_id", "structure_id", "variant_family", "analysis_scenario", "center_id", "model_seed", "kappa_rec", "kappa_hist"]
    rows = []
    for values, group in data.sort_values("stage").groupby(keys, dropna=False):
        identity = dict(zip(keys, values))
        commits = int(group.commit.sum())
        beneficial = int(group.beneficial_candidate.sum())
        rows.append(
            {
                **identity,
                "lifecycle_mse": float(group.deployed_service_mse.mean()),
                "lifecycle_mae": float(group.deployed_service_mae.mean()),
                "harmful_commit_rate": float(group.harmful_commit.mean()),
                "average_downside": float(group.downside.mean()),
                "conditional_harmful_rate": float(group.harmful_commit.sum() / commits) if commits else math.nan,
                "beneficial_commit_recall": float((group.commit * group.beneficial_candidate).sum() / beneficial) if beneficial else math.nan,
                "commit_rate": float(group.commit.mean()),
                "maximum_retain_streak": longest_retain(group.commit),
                "normal_branch_commits": int(group.normal_branch_commit.sum()),
                "recovery_branch_commits": int(group.recovery_branch_commit.sum()),
                "recovery_branch_beneficial": int((group.recovery_branch_commit * group.beneficial_candidate).sum()),
                "recovery_branch_harmful": int((group.recovery_branch_commit * group.harmful_commit).sum()),
                "conflict_triggers": int(group.conflict_trigger.sum()),
                "max_conflict_persistence": int(group.conflict_persistence_length.max()),
                "history_realignments": int(group.history_realign.sum()),
            }
        )
    return pd.DataFrame(rows)


def summarize(trajectories: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (arm, scenario), group in trajectories.groupby(["arm_id", "analysis_scenario"]):
        entry = {
            "arm_id": arm,
            "structure_id": group.structure_id.iloc[0],
            "variant_family": group.variant_family.iloc[0],
            "kappa_rec": float(group.kappa_rec.iloc[0]),
            "kappa_hist": float(group.kappa_hist.iloc[0]),
            "scenario": scenario,
            "centers": int(group.center_id.nunique()),
            "seeds": int(group.model_seed.nunique()),
        }
        for metric in ["lifecycle_mse", "lifecycle_mae", "harmful_commit_rate", "average_downside", "commit_rate", "maximum_retain_streak"]:
            point, low, high = ci_mean(group, metric)
            entry[metric] = point
            entry[metric + "_ci_low"] = low
            entry[metric + "_ci_high"] = high
        for metric in ["conditional_harmful_rate", "beneficial_commit_recall"]:
            point, low, high = ci_mean(group, metric)
            entry[metric] = point
            entry[metric + "_ci_low"] = low
            entry[metric + "_ci_high"] = high
        rows.append(entry)
    return pd.DataFrame(rows)


def development_recovery(stage_data: pd.DataFrame) -> pd.DataFrame:
    reference_frames = []
    for prefix, method in [("reference_frozen", "Frozen"), ("reference_ft", "Always-FT")]:
        for path in sorted((ROOT / "results/development").glob(prefix + "_*_clean.csv")):
            frame = pd.read_csv(path, usecols=["center_id", "model_seed", "stage", "deployed_service_mse"])
            frame["reference_method"] = method
            reference_frames.append(frame)
    reference = pd.concat(reference_frames, ignore_index=True)
    reference = reference.groupby(["center_id", "model_seed", "stage"]).deployed_service_mse.min().rename("observed_reference_mse").reset_index()
    clean = stage_data[stage_data.scenario_id == "clean"].merge(reference, on=["center_id", "model_seed", "stage"], validate="many_to_one")
    rows = []
    for keys, group in clean.groupby(["arm_id", "structure_id", "variant_family", "analysis_scenario", "center_id", "model_seed"]):
        arm, structure, family, regime, center, seed = keys
        if regime == "stationary":
            continue
        onset = 7 if regime == "recurring" else 9
        group = group[group.stage >= onset].sort_values("stage")
        excess = np.maximum(group.deployed_service_mse.to_numpy() - group.observed_reference_mse.to_numpy(), 0)
        within = group.deployed_service_mse.to_numpy() <= 1.05 * group.observed_reference_mse.to_numpy()
        hits = np.flatnonzero(within[:-1] & within[1:])
        rows.append(
            {
                "arm_id": arm,
                "structure_id": structure,
                "variant_family": family,
                "scenario": regime,
                "center_id": center,
                "model_seed": seed,
                "post_drift_excess_loss_area": float(excess.sum()),
                "recovery_time": float(hits[0] + 1) if len(hits) else math.nan,
                "censored_recovery": int(not len(hits)),
            }
        )
    return pd.DataFrame(rows)


def recovery_summary(recovery: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (arm, scenario), group in recovery.groupby(["arm_id", "scenario"]):
        area = ci_mean(group, "post_drift_excess_loss_area")
        censored = ci_mean(group, "censored_recovery")
        recovered = group.recovery_time.dropna()
        rows.append(
            {
                "arm_id": arm,
                "scenario": scenario,
                "post_drift_excess_loss_area": area[0],
                "post_drift_excess_loss_area_ci_low": area[1],
                "post_drift_excess_loss_area_ci_high": area[2],
                "recovery_time_median_uncensored": float(recovered.median()) if len(recovered) else math.nan,
                "recovered_trajectories": int(len(recovered)),
                "total_trajectories": int(len(group)),
                "censored_recovery_rate": censored[0],
                "censored_recovery_rate_ci_low": censored[1],
                "censored_recovery_rate_ci_high": censored[2],
            }
        )
    return pd.DataFrame(rows)


def paired_to_v1(trajectories: pd.DataFrame) -> pd.DataFrame:
    baseline = trajectories[trajectories.arm_id == "V0_LegacyFull"]
    rows = []
    metrics = ["lifecycle_mse", "lifecycle_mae", "harmful_commit_rate", "average_downside", "conditional_harmful_rate", "beneficial_commit_recall", "commit_rate", "maximum_retain_streak"]
    for arm in sorted(set(trajectories.arm_id) - {"V0_LegacyFull"}):
        for scenario in sorted(set(trajectories.analysis_scenario)):
            left = trajectories[(trajectories.arm_id == arm) & (trajectories.analysis_scenario == scenario)]
            right = baseline[baseline.analysis_scenario == scenario]
            merged = left.merge(right, on=["center_id", "model_seed", "analysis_scenario"], suffixes=("_v2", "_v1"), validate="one_to_one")
            for metric in metrics:
                merged["difference"] = merged[metric + "_v2"] - merged[metric + "_v1"]
                point, low, high = ci_mean(merged, "difference")
                rows.append({"arm_id": arm, "reference": "V0_LegacyFull", "scenario": scenario, "metric": metric, "difference": point, "ci_low": low, "ci_high": high, "bootstrap_replicates": BOOTSTRAP, "unit": "center"})
    return pd.DataFrame(rows)


def branch_diagnostics(stage_data: pd.DataFrame) -> pd.DataFrame:
    adaptive = stage_data[stage_data.variant_family.isin(["V3_SP_AdaptiveDual", "V4_SP_AdaptiveDual_NoRealign"])]
    rows = []
    for (arm, scenario), group in adaptive.groupby(["arm_id", "analysis_scenario"]):
        recovery = int(group.recovery_branch_commit.sum())
        rows.append(
            {
                "arm_id": arm,
                "scenario": scenario,
                "normal_branch_commit_count": int(group.normal_branch_commit.sum()),
                "recovery_branch_commit_count": recovery,
                "recovery_branch_beneficial_rate": float((group.recovery_branch_commit * group.beneficial_candidate).sum() / recovery) if recovery else math.nan,
                "recovery_branch_harmful_rate": float((group.recovery_branch_commit * group.harmful_commit).sum() / recovery) if recovery else math.nan,
                "conflict_trigger_count": int(group.conflict_trigger.sum()),
                "mean_conflict_persistence_on_trigger": float(group.loc[group.conflict_trigger == 1, "conflict_persistence_length"].mean()) if group.conflict_trigger.sum() else math.nan,
                "maximum_conflict_persistence": int(group.conflict_persistence_length.max()),
                "history_realign_count": int(group.history_realign.sum()),
            }
        )
    return pd.DataFrame(rows)


def balanced_table(summary: pd.DataFrame, recovery: pd.DataFrame | None = None) -> pd.DataFrame:
    balanced = ["stationary", "gradual", "abrupt", "recurring", "mixed_a010_both"]
    rows = []
    for arm, group in summary.groupby("arm_id"):
        chosen = group[group.scenario.isin(balanced)]
        if set(chosen.scenario) != set(balanced):
            raise RuntimeError(f"balanced scenarios missing for {arm}")
        mixed = group[group.scenario == "mixed_a010_both"].iloc[0]
        area = math.nan
        if recovery is not None:
            rg = recovery[(recovery.arm_id == arm) & recovery.scenario.isin(["gradual", "abrupt", "recurring"])]
            area = float(rg.post_drift_excess_loss_area.mean())
        family = chosen.variant_family.iloc[0]
        rows.append(
            {
                "arm_id": arm,
                "variant_family": family,
                "balanced_lifecycle_mse": float(chosen.lifecycle_mse.mean()),
                "balanced_post_drift_excess_loss_area": area,
                "balanced_beneficial_commit_recall": float(chosen.beneficial_commit_recall.mean()),
                "mixed_harmful_commit_rate": float(mixed.harmful_commit_rate),
                "mixed_average_downside": float(mixed.average_downside),
                "mixed_commit_rate": float(mixed.commit_rate),
                "rho": RHO,
                "epsilon": EPSILON,
                "safety_feasible": bool(mixed.harmful_commit_rate <= RHO and mixed.average_downside <= EPSILON),
                "diagnostic_only": bool(family == "D0_SP_RecentOnly"),
            }
        )
    table = pd.DataFrame(rows)
    table["pareto_frontier"] = False
    for idx, row in table.iterrows():
        competitors = table.drop(index=idx)
        dominates = (
            (competitors.balanced_lifecycle_mse <= row.balanced_lifecycle_mse)
            & (competitors.mixed_harmful_commit_rate <= row.mixed_harmful_commit_rate)
            & (competitors.mixed_average_downside <= row.mixed_average_downside)
            & (competitors.balanced_beneficial_commit_recall >= row.balanced_beneficial_commit_recall)
            & (
                (competitors.balanced_lifecycle_mse < row.balanced_lifecycle_mse)
                | (competitors.mixed_harmful_commit_rate < row.mixed_harmful_commit_rate)
                | (competitors.mixed_average_downside < row.mixed_average_downside)
                | (competitors.balanced_beneficial_commit_recall > row.balanced_beneficial_commit_recall)
            )
        )
        table.loc[idx, "pareto_frontier"] = not bool(dominates.any())
    return table.sort_values(["safety_feasible", "balanced_lifecycle_mse"], ascending=[False, True])


def analyze_development(data: pd.DataFrame, trajectories: pd.DataFrame, summary: pd.DataFrame, out: Path) -> None:
    recovery = development_recovery(data)
    rec_summary = recovery_summary(recovery)
    pairs = paired_to_v1(trajectories)
    branches = branch_diagnostics(data)
    balanced = balanced_table(summary, rec_summary)
    eligible = balanced[(balanced.safety_feasible) & (~balanced.diagnostic_only)].copy()
    if eligible.empty:
        selection = {"status": "FAIL", "reason": "NO_STRUCTURE_SATISFIED_RHO_AND_EPSILON", "rho": RHO, "epsilon": EPSILON}
        atomic_json(ROOT / "audits_v2_dev/v2_structural_selection.json", selection)
        raise RuntimeError(selection["reason"])
    eligible = eligible.sort_values(["balanced_lifecycle_mse", "balanced_post_drift_excess_loss_area", "balanced_beneficial_commit_recall", "mixed_average_downside"], ascending=[True, True, False, True])
    winner_id = eligible.iloc[0].arm_id
    structure = next(item for item in structural_grid() if item["structure_id"] == winner_id)
    frozen = {
        **structure,
        "status": "FROZEN_AFTER_DEVELOPMENT_SCREENING",
        "selection_rule": "safety feasible on mixed alpha=0.10/both, then minimum equal-scenario balanced lifecycle MSE; fixed secondary tie-breakers",
        "rho": RHO,
        "epsilon": EPSILON,
        "development_pool": [11000, 11019],
        "v1_gate_used_for_structure_screening": V1_GATE,
    }
    frozen_path = ROOT / "configs_v2_dev/frozen_v2_structure.yaml"
    frozen_path.write_text(json.dumps(frozen, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    selection = {
        "status": "PASS",
        "winner": winner_id,
        "winner_record": eligible.iloc[0].to_dict(),
        "eligible_count": len(eligible),
        "candidate_count_excluding_diagnostic": int((~balanced.diagnostic_only).sum()),
        "rho": RHO,
        "epsilon": EPSILON,
        "frozen_structure_sha256": sha256(frozen_path),
        "selection_used_v1_heldout": False,
        "selection_used_v2_confirmatory_heldout": False,
        "selection_used_alibaba": False,
    }
    atomic_json(ROOT / "audits_v2_dev/v2_structural_selection.json", selection)
    recovery.to_csv(out / "development_recovery_trajectory_metrics.csv", index=False, na_rep="NA")
    rec_summary.to_csv(out / "development_recovery_summary.csv", index=False, na_rep="NA")
    pairs.to_csv(out / "development_paired_vs_v1.csv", index=False, na_rep="NA")
    branches.to_csv(out / "development_branch_diagnostics.csv", index=False, na_rep="NA")
    balanced.to_csv(out / "development_pareto.csv", index=False, na_rep="NA")


def analyze_calibration(summary: pd.DataFrame, out: Path) -> None:
    balanced = balanced_table(summary)
    eligible = balanced[balanced.safety_feasible].copy().sort_values("balanced_lifecycle_mse")
    if eligible.empty:
        selection = {"status": "FAIL", "reason": "NO_CALIBRATION_CONFIGURATION_SATISFIED_RHO_AND_EPSILON", "rho": RHO, "epsilon": EPSILON}
        atomic_json(ROOT / "audits_v2_dev/v2_calibration_selection.json", selection)
        raise RuntimeError(selection["reason"])
    winner = eligible.iloc[0]
    match = summary[summary.arm_id == winner.arm_id].iloc[0]
    frozen = {
        "status": "FROZEN_AFTER_DECISION_CALIBRATION",
        "structure_id": match.structure_id,
        "kappa_rec": float(match.kappa_rec) if "kappa_rec" in match else float(winner.arm_id.split("_")[0][2:]),
        "kappa_hist": float(match.kappa_hist) if "kappa_hist" in match else float(winner.arm_id.split("_")[1][2:]),
        "delta_imp": V1_GATE["delta_imp"],
        "delta_ret": V1_GATE["delta_ret"],
        "rho": RHO,
        "epsilon": EPSILON,
        "decision_calibration_pool": [12000, 12019],
        "selection_rule": "minimum equal-scenario balanced lifecycle MSE among configurations satisfying mixed rho and epsilon",
    }
    # Summary rows do not retain gate columns; decode the exact grid label.
    frozen["kappa_rec"] = float(winner.arm_id.split("_")[0].replace("kr", ""))
    frozen["kappa_hist"] = float(winner.arm_id.split("_")[1].replace("kh", ""))
    path = ROOT / "configs_v2_dev/frozen_v2_commit_config.yaml"
    path.write_text(json.dumps(frozen, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    selection = {
        "status": "PASS",
        "winner": winner.arm_id,
        "winner_record": json_record(winner),
        "eligible_count": len(eligible),
        "grid_count": len(balanced),
        "rho": RHO,
        "epsilon": EPSILON,
        "frozen_commit_config_sha256": sha256(path),
        "selection_used_v1_heldout": False,
        "selection_used_v2_confirmatory_heldout": False,
        "selection_used_alibaba": False,
    }
    atomic_json(ROOT / "audits_v2_dev/v2_calibration_selection.json", selection)
    balanced.to_csv(out / "calibration_grid_summary.csv", index=False, na_rep="NA")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["development", "calibration"], required=True)
    args = parser.parse_args()
    folder = ROOT / "results_v2_dev" / args.phase
    paths = sorted((folder / "trajectories").glob("*.csv"))
    data = read_phase(args.phase)
    check = integrity(data, args.phase, len(paths))
    trajectories = trajectory_metrics(data)
    summary = summarize(trajectories)
    trajectories.to_csv(folder / f"{args.phase}_trajectory_metrics.csv", index=False, na_rep="NA")
    summary.to_csv(folder / f"{args.phase}_summary.csv", index=False, na_rep="NA")
    if args.phase == "development":
        analyze_development(data, trajectories, summary, folder)
    else:
        analyze_calibration(summary, folder)
    atomic_json(ROOT / "audits_v2_dev" / f"v2_{args.phase}_integrity.json", check)
    print(json.dumps(check, indent=2), flush=True)


if __name__ == "__main__":
    main()
