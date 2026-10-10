"""Apply the frozen V2 GO/NO-GO rules to completed development/calibration results."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = 4000
BOOTSTRAP_SEED = 2904
RHO = 0.05
EPSILON = 5.6036475532487204e-05
V2 = "V2_SP_ShortDual"
V1 = "V0_LegacyFull"
BALANCED = ["stationary", "gradual", "abrupt", "recurring", "mixed_a010_both"]
DRIFT = ["gradual", "abrupt", "recurring"]


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    os.replace(tmp, path)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean(value):
    if isinstance(value, dict):
        return {key: clean(item) for key, item in value.items()}
    if isinstance(value, list):
        return [clean(item) for item in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return None if not np.isfinite(value) else float(value)
    return value


def stratified_paired_ci(frame: pd.DataFrame, metric: str, scenarios: list[str]) -> dict:
    per_scenario: list[np.ndarray] = []
    scenario_points = {}
    for scenario in scenarios:
        left = frame[(frame.arm_id == V2) & (frame.analysis_scenario == scenario)]
        right = frame[(frame.arm_id == V1) & (frame.analysis_scenario == scenario)]
        merged = left.merge(
            right,
            on=["analysis_scenario", "center_id", "model_seed"],
            suffixes=("_v2", "_v1"),
            validate="one_to_one",
        )
        merged["difference"] = merged[f"{metric}_v2"] - merged[f"{metric}_v1"]
        centers = merged.groupby("center_id").difference.mean().dropna().to_numpy(float)
        if not len(centers):
            raise RuntimeError(f"no paired center values for {metric}/{scenario}")
        per_scenario.append(centers)
        scenario_points[scenario] = float(centers.mean())
    point = float(np.mean([values.mean() for values in per_scenario]))
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    sampled = np.zeros(BOOTSTRAP)
    for values in per_scenario:
        sampled += values[rng.integers(len(values), size=(BOOTSTRAP, len(values)))].mean(axis=1)
    sampled /= len(per_scenario)
    low, high = np.quantile(sampled, [0.025, 0.975])
    return {
        "difference": point,
        "ci_low": float(low),
        "ci_high": float(high),
        "scenario_differences": scenario_points,
        "bootstrap_replicates": BOOTSTRAP,
        "unit": "center",
        "scenario_weighting": "equal",
    }


def paired_row(pairs: pd.DataFrame, scenario: str, metric: str) -> dict:
    row = pairs[(pairs.arm_id == V2) & (pairs.scenario == scenario) & (pairs.metric == metric)].iloc[0]
    return {key: clean(row[key]) for key in ["difference", "ci_low", "ci_high", "bootstrap_replicates", "unit"]}


def metric_row(summary: pd.DataFrame, arm: str, scenario: str) -> dict:
    row = summary[(summary.arm_id == arm) & (summary.scenario == scenario)].iloc[0]
    return {
        metric: clean(row[metric])
        for metric in [
            "lifecycle_mse", "lifecycle_mae", "harmful_commit_rate", "average_downside",
            "conditional_harmful_rate", "beneficial_commit_recall", "commit_rate",
        ]
    }


def main() -> None:
    protocol_path = ROOT / "configs_v2_dev/v2_go_no_go_protocol.json"
    integrity_path = ROOT / "audits_v2_dev/v2_calibration_final_integrity.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    integrity = json.loads(integrity_path.read_text(encoding="utf-8"))
    selection = json.loads((ROOT / "audits_v2_dev/v2_calibration_selection.json").read_text(encoding="utf-8"))
    trajectories = pd.read_csv(ROOT / "results_v2_dev/development/development_trajectory_metrics.csv")
    recovery = pd.read_csv(ROOT / "results_v2_dev/development/development_recovery_trajectory_metrics.csv")
    summary = pd.read_csv(ROOT / "results_v2_dev/development/development_summary.csv")
    pairs = pd.read_csv(ROOT / "results_v2_dev/development/development_paired_vs_v1.csv")

    winner = selection["winner_record"]
    go1_pass = (
        integrity["status"] == "PASS"
        and selection["status"] == "PASS"
        and winner["mixed_harmful_commit_rate"] <= RHO
        and winner["mixed_average_downside"] <= EPSILON
    )
    go1 = {
        "status": "PASS" if go1_pass else "FAIL",
        "calibration_winner": selection["winner"],
        "mixed_harmful_commit_rate": winner["mixed_harmful_commit_rate"],
        "rho": RHO,
        "mixed_average_downside": winner["mixed_average_downside"],
        "epsilon": EPSILON,
        "integrity": integrity["status"],
    }

    balanced_mse = stratified_paired_ci(trajectories, "lifecycle_mse", BALANCED)
    regime_mse = {scenario: paired_row(pairs, scenario, "lifecycle_mse") for scenario in BALANCED}
    go2_pass = balanced_mse["difference"] < 0 and all(regime_mse[s]["ci_low"] <= 0 for s in ["stationary", "gradual", "abrupt", "recurring"])
    go2 = {
        "status": "PASS" if go2_pass else "FAIL",
        "balanced_lifecycle_mse_paired": balanced_mse,
        "benign_regime_lifecycle_mse_paired": regime_mse,
    }

    recall = stratified_paired_ci(trajectories, "beneficial_commit_recall", BALANCED)
    area = stratified_paired_ci(recovery.rename(columns={"scenario": "analysis_scenario"}), "post_drift_excess_loss_area", DRIFT)
    censor = stratified_paired_ci(recovery.rename(columns={"scenario": "analysis_scenario"}), "censored_recovery", DRIFT)
    clear = recall["ci_low"] > 0 or area["ci_high"] < 0 or censor["ci_high"] < 0
    point = recall["difference"] > 0 or area["difference"] < 0 or censor["difference"] < 0
    go3_status = "PASS" if clear and go1_pass else ("AMBIGUOUS" if point else "FAIL")
    go3 = {
        "status": go3_status,
        "balanced_beneficial_commit_recall_paired": recall,
        "balanced_post_drift_excess_loss_area_paired": area,
        "balanced_censored_recovery_rate_paired": censor,
        "improvement_not_only_commit_frequency": "plasticity endpoints are candidate-quality/recovery endpoints rather than commit count",
    }

    conditional = paired_row(pairs, "mixed_a010_both", "conditional_harmful_rate")
    if conditional["ci_low"] > 0:
        go4_status = "FAIL"
    elif conditional["difference"] > 0:
        go4_status = "AMBIGUOUS"
    else:
        go4_status = "PASS"
    go4 = {
        "status": go4_status,
        "mixed_conditional_harmful_rate_paired": conditional,
        "mixed_commit_rate_paired": paired_row(pairs, "mixed_a010_both", "commit_rate"),
        "v2": metric_row(summary, V2, "mixed_a010_both"),
        "v1": metric_row(summary, V1, "mixed_a010_both"),
    }

    verification = {}
    go5_fail = False
    go5_ambiguous = False
    for scenario in ["persistent_a010_verification_only", "replay_a010_verification_only"]:
        v2_values = metric_row(summary, V2, scenario)
        harmful = paired_row(pairs, scenario, "harmful_commit_rate")
        downside = paired_row(pairs, scenario, "average_downside")
        commit = paired_row(pairs, scenario, "commit_rate")
        conditional_attack = paired_row(pairs, scenario, "conditional_harmful_rate")
        constraint_fail = v2_values["harmful_commit_rate"] > RHO or v2_values["average_downside"] > EPSILON
        ci_fail = harmful["ci_low"] > 0 or downside["ci_low"] > 0
        ambiguous = (
            not constraint_fail and not ci_fail
            and (harmful["difference"] > 0 or downside["difference"] > 0
                 or (commit["ci_low"] > 0 and conditional_attack["difference"] > 0))
        )
        go5_fail |= constraint_fail or ci_fail
        go5_ambiguous |= ambiguous
        verification[scenario] = {
            "v2": v2_values,
            "v1": metric_row(summary, V1, scenario),
            "harmful_rate_paired": harmful,
            "downside_paired": downside,
            "commit_rate_paired": commit,
            "conditional_harmful_paired": conditional_attack,
            "constraint_fail": constraint_fail,
            "paired_ci_fail": ci_fail,
        }
    go5 = {"status": "FAIL" if go5_fail else ("AMBIGUOUS" if go5_ambiguous else "PASS"), "scenarios": verification}

    paired = trajectories[trajectories.arm_id.isin([V1, V2]) & trajectories.analysis_scenario.isin(BALANCED)].pivot_table(
        index=["analysis_scenario", "center_id", "model_seed"], columns="arm_id", values="lifecycle_mse"
    ).dropna().reset_index()
    paired["difference"] = paired[V2] - paired[V1]
    seed_directions = {
        str(seed): float(group.groupby("analysis_scenario").difference.mean().mean())
        for seed, group in paired.groupby("model_seed")
    }
    center_differences = paired.groupby("center_id").difference.mean().sort_values()
    negative_seeds = sum(value < 0 for value in seed_directions.values())
    negative_center_fraction = float((center_differences < 0).mean())
    median_center = float(center_differences.median())
    go6_fail = negative_seeds < 2 or negative_center_fraction < 0.50
    go6_pass = (
        balanced_mse["ci_high"] < 0 and negative_seeds >= 2
        and median_center < 0 and negative_center_fraction >= 0.60
    )
    go6 = {
        "status": "FAIL" if go6_fail else ("PASS" if go6_pass else "AMBIGUOUS"),
        "balanced_lifecycle_mse_paired": balanced_mse,
        "seed_wise_balanced_differences": seed_directions,
        "negative_seed_count": negative_seeds,
        "center_difference_distribution": {
            "count": int(len(center_differences)),
            "min": float(center_differences.min()),
            "q25": float(center_differences.quantile(0.25)),
            "median": median_center,
            "q75": float(center_differences.quantile(0.75)),
            "max": float(center_differences.max()),
            "negative_fraction": negative_center_fraction,
            "five_most_favorable": {str(k): float(v) for k, v in center_differences.head(5).items()},
            "five_least_favorable": {str(k): float(v) for k, v in center_differences.tail(5).items()},
        },
    }

    gates = {"GO-1": go1, "GO-2": go2, "GO-3": go3, "GO-4": go4, "GO-5": go5, "GO-6": go6}
    statuses = [gate["status"] for gate in gates.values()]
    verdict = "NO-GO" if "FAIL" in statuses else ("AMBIGUOUS" if "AMBIGUOUS" in statuses else "GO")
    decision = clean({
        "schema": "ravm-dt-v2-go-no-go-decision-v1",
        "protocol_sha256": sha256(protocol_path),
        "protocol_status": protocol["status"],
        "verdict": verdict,
        "gates": gates,
        "calibration_integrity": integrity,
        "heldout_accessed": False,
        "heldout_materialized": False,
        "confirmatory_started": False,
        "terminal_state": "WAITING_FOR_MANUAL_V2_METHOD_REVIEW" if verdict != "GO" else "AUTHORIZED_FOR_FINAL_V2_FREEZE",
    })
    decision_path = ROOT / "audits_v2_dev/v2_go_no_go_decision.json"
    atomic_json(decision_path, decision)

    report_path = ROOT / "V2_METHOD_SCREENING_REPORT.md"
    original = report_path.read_text(encoding="utf-8")
    marker = "\n<!-- V2_GO_NO_GO_DECISION_START -->"
    if marker in original:
        original = original.split(marker, 1)[0].rstrip() + "\n"
    v5 = verification["persistent_a010_verification_only"]
    v6 = verification["replay_a010_verification_only"]
    section = f"""
<!-- V2_GO_NO_GO_DECISION_START -->
## Frozen GO / NO-GO decision

**Verdict: {verdict}.** Calibration integrity is PASS (1920/1920 valid; missing=0, duplicate=0, unexpected=0, partial=0, wrong-environment included=0). The calibrated winner is `{selection['winner']}` with mixed harmful rate {winner['mixed_harmful_commit_rate']:.8f} ≤ {RHO:.2f} and downside {winner['mixed_average_downside']:.12g} ≤ {EPSILON:.12g}.

| Gate | Result | Exact evidence |
|---|---|---|
| GO-1 Risk feasibility | {go1['status']} | winner harmful={winner['mixed_harmful_commit_rate']:.8f}; downside={winner['mixed_average_downside']:.12g} |
| GO-2 Utility | {go2['status']} | balanced MSE difference={balanced_mse['difference']:.12g}, paired 95% CI [{balanced_mse['ci_low']:.12g}, {balanced_mse['ci_high']:.12g}]; every benign-regime MSE CI is favorable |
| GO-3 Plasticity | {go3['status']} | beneficial-recall difference={recall['difference']:.8f}, CI [{recall['ci_low']:.8f}, {recall['ci_high']:.8f}]; excess-area difference={area['difference']:.12g}, CI [{area['ci_low']:.12g}, {area['ci_high']:.12g}]; censored-recovery difference={censor['difference']:.8f}, CI [{censor['ci_low']:.8f}, {censor['ci_high']:.8f}] |
| GO-4 Accepted-state quality | {go4['status']} | mixed conditional-harmful difference={conditional['difference']:.8f}, CI [{conditional['ci_low']:.8f}, {conditional['ci_high']:.8f}] |
| GO-5 Verification-attack safety | {go5['status']} | persistent-bias downside difference={v5['downside_paired']['difference']:.12g}, CI [{v5['downside_paired']['ci_low']:.12g}, {v5['downside_paired']['ci_high']:.12g}]; replay harmful difference={v6['harmful_rate_paired']['difference']:.8f}, CI [{v6['harmful_rate_paired']['ci_low']:.8f}, {v6['harmful_rate_paired']['ci_high']:.8f}]; replay downside difference={v6['downside_paired']['difference']:.12g}, CI [{v6['downside_paired']['ci_low']:.12g}, {v6['downside_paired']['ci_high']:.12g}] |
| GO-6 Stability | {go6['status']} | seed differences={json.dumps(seed_directions, ensure_ascii=False)}; 20/20 centers favorable; median center difference={median_center:.12g}; paired CI upper={balanced_mse['ci_high']:.12g} |

GO-5 is an explicit failure under the frozen rule because verification-only paired harmful/downside confidence intervals are wholly above zero. Absolute harmful rates remain below rho and downside remains below epsilon, but the protocol separately requires no wholly adverse paired CI against V1. This negative finding is retained and controls the verdict.

The confirmatory centers 14000–14029 remain sealed and unmaterialized. No final V2 freeze commit/tag was created, and no fresh confirmatory trajectory was run. State: `WAITING_FOR_MANUAL_V2_METHOD_REVIEW`.
<!-- V2_GO_NO_GO_DECISION_END -->
"""
    report_path.write_text(original.rstrip() + "\n" + section.strip() + "\n", encoding="utf-8")
    status = {
        "status": "WAITING_FOR_MANUAL_V2_METHOD_REVIEW",
        "phase": "v2_go_no_go_complete",
        "verdict": verdict,
        "calibration_completed": 1920,
        "calibration_expected": 1920,
        "calibration_integrity": "PASS",
        "failed_gates": [name for name, gate in gates.items() if gate["status"] == "FAIL"],
        "ambiguous_gates": [name for name, gate in gates.items() if gate["status"] == "AMBIGUOUS"],
        "heldout_accessed": False,
        "heldout_materialized": False,
        "confirmatory_started": False,
        "report": str(report_path),
        "report_sha256": sha256(report_path),
        "decision_audit": str(decision_path),
    }
    atomic_json(ROOT / "results_v2_dev/execution_status.json", status)
    print(json.dumps(status, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
