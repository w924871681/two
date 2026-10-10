from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from paper_figures.scripts.paper_common import AUDITS, DATA, ROOT, TABLES, ensure_dirs, sha256
from scripts.v2_final_baseline_analyze import BOOT, SEED, stratified_diff

PRIMARY = ["stationary", "gradual", "abrupt", "recurring", "mixed_a010_both"]
ALL7 = PRIMARY + ["persistent_a010_verification_only", "replay_a010_verification_only"]
METHODS = ["Proposed", "Always-FT", "ER", "EWC", "Huber-FT", "ValidationCommit", "Frozen"]
METRICS = ["lifecycle_mse", "lifecycle_mae", "harmful_commit_rate", "average_downside", "conditional_harmful_rate", "beneficial_commit_recall", "commit_rate"]
EXPECTED_REPORTS = {
    "V2_FINAL_MINIMAL_CONFIRMATORY_REPORT.md": "1e4787ffc96c5144f8693f103f1e481884e6b13ae4aa4b0a566902927d4435e0",
    "V2_FINAL_BASELINE_BENCHMARK_REPORT.md": "bf7afa27797bfecf9e867a2f5b656258c1bcf577f032c5414624d818f00fbf91",
    "V2_ROBUSTNESS_SEVERITY_REPORT.md": "7f224a42dd061c19a270e2147474c34da16486f871403e94a7bd1d2be808ad0d",
    "V2_MECHANISM_AND_SENSITIVITY_REPORT.md": "dce4ea39040f36b1aff57cfd68e1d148dea13380915a6d5261f00a0474509b53",
    "V2_ALIBABA_EXTERNAL_TRACE_REPORT.md": "8029bb085276341f4bde73ee25548fac2563887efb492efc2f999892ecb243cf",
    "V2_ARCHITECTURE_HORIZON_GENERALITY_REPORT.md": "27e05f6098378d5ae9f48d006f01983a8470efeebaf6e0b37cfa39a6815df3ee",
}
HASH_MANIFESTS = {
    "audits_v2_final_baselines/final_baseline_output_hash_manifest.json": "results_v2_final_baselines",
    "audits_v2_severity/severity_output_hash_manifest.json": "results_v2_severity",
    "audits_v2_alibaba/alibaba_output_hash_manifest.json": "results_v2_alibaba",
    "audits_v2_generality/generality_output_hash_manifest.json": "results_v2_generality",
}


def equal_weight_ci(frame: pd.DataFrame, scenario_col: str, value_col: str, scenarios: list[str]) -> tuple[float, float, float]:
    arrays = []
    for scenario in scenarios:
        values = frame[frame[scenario_col] == scenario].groupby("center_id")[value_col].mean().dropna().to_numpy(float)
        if len(values) == 0:
            return math.nan, math.nan, math.nan
        arrays.append(values)
    point = float(np.mean([values.mean() for values in arrays]))
    rng = np.random.default_rng(SEED)
    samples = np.zeros(BOOT)
    for values in arrays:
        samples += values[rng.integers(len(values), size=(BOOT, len(values)))].mean(axis=1)
    samples /= len(arrays)
    lo, hi = np.quantile(samples, [0.025, 0.975])
    return point, float(lo), float(hi)


def simple_center_ci(frame: pd.DataFrame, value_col: str) -> tuple[float, float, float]:
    values = frame.groupby("center_id")[value_col].mean().dropna().to_numpy(float)
    if not len(values):
        return math.nan, math.nan, math.nan
    rng = np.random.default_rng(SEED)
    samples = values[rng.integers(len(values), size=(BOOT, len(values)))].mean(axis=1)
    lo, hi = np.quantile(samples, [0.025, 0.975])
    return float(values.mean()), float(lo), float(hi)


def validate_authoritative_sources() -> list[str]:
    checks = []
    for name, expected in EXPECTED_REPORTS.items():
        actual = sha256(ROOT / name)
        if actual != expected:
            raise RuntimeError(f"authoritative report hash mismatch: {name}: {actual} != {expected}")
        checks.append(f"{name}: {actual}")
    for rel, source_dir in HASH_MANIFESTS.items():
        manifest = json.loads((ROOT / rel).read_text(encoding="utf-8"))
        if manifest.get("status") != "PASS":
            raise RuntimeError(f"hash manifest not PASS: {rel}")
        for name, expected in manifest["result_hashes"].items():
            path = ROOT / source_dir / name
            actual = sha256(path)
            if actual != expected:
                raise RuntimeError(f"frozen result hash mismatch: {path}: {actual} != {expected}")
        checks.append(f"{rel}: PASS ({len(manifest['result_hashes'])} result files)")
    return checks


def build_primary() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    center = pd.read_csv(ROOT / "results_v2_final_baselines/baseline_center_level_summary.csv")
    traj = pd.read_csv(ROOT / "results_v2_final_baselines/baseline_trajectory_index.csv")
    proposed = pd.read_csv(ROOT / "results_v2_final/final_trajectory_index.csv")
    proposed = proposed[proposed.method_id == "Final_V2_SP_ShortDual"].copy()
    proposed["method_id"] = "Proposed"
    traj = pd.concat([proposed, traj], ignore_index=True)
    if set(center.analysis_scenario.unique()) != set(ALL7) or set(center.method_id.unique()) != set(METHODS):
        raise RuntimeError("unexpected baseline center-summary factorization")
    if center.duplicated(["method_id", "analysis_scenario", "center_id"]).any():
        raise RuntimeError("duplicate baseline center-level keys")
    rows = []
    for method in METHODS:
        subset = center[center.method_id == method]
        for metric in METRICS:
            point, lo, hi = equal_weight_ci(subset, "analysis_scenario", metric, PRIMARY)
            rows.append({"method": "RAVM-DT" if method == "Proposed" else method, "metric": metric, "estimate": point, "ci_low": lo, "ci_high": hi, "conditions": 5, "bootstrap_replicates": BOOT, "bootstrap_seed": SEED, "statistical_unit": "center", "seed_handling": "mean within center"})
    summary = pd.DataFrame(rows)
    pair_rows = []
    existing = pd.read_csv(ROOT / "results_v2_final_baselines/proposed_vs_baseline_paired.csv")
    for baseline in METHODS[1:]:
        for metric in METRICS:
            difference, lo, hi = stratified_diff(traj, baseline, metric, PRIMARY)
            pv = summary[(summary.method == "RAVM-DT") & (summary.metric == metric)].estimate.iloc[0]
            bv = summary[(summary.method == baseline) & (summary.metric == metric)].estimate.iloc[0]
            pair_rows.append({"comparison": f"RAVM-DT - {baseline}", "baseline": baseline, "metric": metric, "ravm_dt_estimate": pv, "baseline_estimate": bv, "difference": difference, "ci_low": lo, "ci_high": hi, "relative_percent": (pv / bv - 1) * 100 if np.isfinite(bv) and bv != 0 else math.nan, "conditions": 5, "bootstrap_replicates": BOOT, "bootstrap_seed": SEED, "statistical_unit": "center"})
            old = existing[(existing.baseline == baseline) & (existing.scope == "confirmatory_utility_balanced_5") & (existing.metric == metric)]
            if len(old) != 1 or not np.allclose([difference, lo, hi], old[["difference", "ci_low", "ci_high"]].iloc[0].to_numpy(float), rtol=0, atol=2e-15, equal_nan=True):
                raise RuntimeError(f"recomputed five-condition paired result disagrees with frozen helper output: {baseline}/{metric}")
    pairs = pd.DataFrame(pair_rows)
    main = pd.read_csv(ROOT / "results_v2_final_baselines/final_main_table.csv")
    audit_rows = []
    for method in METHODS:
        m = main[main.method == method].iloc[0]
        for metric in METRICS:
            five = summary[(summary.method == ("RAVM-DT" if method == "Proposed" else method)) & (summary.metric == metric)].estimate.iloc[0]
            stored_five = float(m[f"{metric}_utility_balanced_5"])
            if not np.isclose(five, stored_five, rtol=0, atol=2e-15, equal_nan=True):
                raise RuntimeError(f"five-condition value disagrees with frozen main table: {method}/{metric}")
            seven = float(m[f"{metric}_balanced_all_7"])
            audit_rows.append({"method": "RAVM-DT" if method == "Proposed" else method, "metric": metric, "five_condition": five, "seven_condition": seven, "five_minus_seven": five - seven})
    audit = pd.DataFrame(audit_rows)
    summary.to_csv(DATA / "primary_five_condition_summary.csv", index=False)
    pairs.to_csv(DATA / "primary_five_condition_paired_comparisons.csv", index=False)
    audit.to_csv(DATA / "primary_five_vs_seven_audit.csv", index=False)
    return summary, pairs, audit


def build_fig_data(primary: pd.DataFrame) -> None:
    primary[primary.metric.isin(["lifecycle_mse", "harmful_commit_rate", "average_downside", "commit_rate"])].to_csv(DATA / "fig2_overall_baseline.csv", index=False)

    severity = pd.read_csv(ROOT / "results_v2_severity/severity_scenario_summary.csv")
    severity = severity[severity.method == "Proposed"].copy()
    severity["series"] = severity.attack_type.map({"mixed": "Mixed", "persistent_bias": "Persistent bias", "replay": "Replay"})
    if severity.series.isna().any() or len(severity) != 9:
        raise RuntimeError("Fig.3 severity data must contain exactly 3 x 3 Proposed cells")
    severity.to_csv(DATA / "fig3_corruption_severity.csv", index=False)

    baseline = pd.read_csv(ROOT / "results_v2_final_baselines/baseline_scenario_summary.csv")
    fig4 = baseline[baseline.method.isin(["Proposed", "Always-FT", "Frozen"]) & baseline.scenario.isin(PRIMARY[:4])].copy()
    fig4["method"] = fig4.method.replace({"Proposed": "RAVM-DT"})
    if len(fig4) != 12:
        raise RuntimeError("Fig.4 must contain exactly 12 method-regime cells")
    fig4.to_csv(DATA / "fig4_benign_evolution.csv", index=False)

    q4raw = pd.read_csv(ROOT / "results/q4_ablation/raw_episode_results.csv")
    q4keys = ["method", "attack_type", "center_id", "model_seed"]
    q4traj = q4raw.groupby(q4keys, as_index=False).agg(lifecycle_mse=("deployed_service_mse", "mean"), harmful_commit_rate=("harmful_commit", "mean"))
    comp_rows = []
    for complex_method, simple_method, label in [("Proposed", "SinglePath", "Block consensus - SinglePath"), ("Proposed", "MeanDelta", "Trimmed aggregation - Mean")]:
        for condition in ["clean", "mixed"]:
            a = q4traj[(q4traj.method == complex_method) & (q4traj.attack_type == condition)]
            b = q4traj[(q4traj.method == simple_method) & (q4traj.attack_type == condition)]
            m = a.merge(b, on=["attack_type", "center_id", "model_seed"], suffixes=("_complex", "_simple"), validate="one_to_one")
            m["difference"] = m.lifecycle_mse_complex - m.lifecycle_mse_simple
            point, lo, hi = simple_center_ci(m, "difference")
            comp_rows.append({"comparison": label, "condition": condition.capitalize(), "difference": point, "ci_low": lo, "ci_high": hi, "direction": "complex variant - simpler reference", "centers": m.center_id.nunique(), "seeds": m.model_seed.nunique(), "bootstrap_replicates": BOOT, "bootstrap_seed": SEED})
    pd.DataFrame(comp_rows).to_csv(DATA / "fig5a_candidate_complexity.csv", index=False)

    dev = pd.read_csv(ROOT / "results_v2_dev/development/development_trajectory_metrics.csv")
    arms = {"D0_SP_RecentOnly": "Recent only", "V1_SP_StaticDual": "Long history", "V2_SP_ShortDual": "Bounded history"}
    trade_rows = []
    for arm, label in arms.items():
        subset = dev[dev.arm_id == arm]
        mse, mse_lo, mse_hi = equal_weight_ci(subset, "analysis_scenario", "lifecycle_mse", ALL7)
        mixed = subset[subset.analysis_scenario == "mixed_a010_both"]
        harmful, harmful_lo, harmful_hi = simple_center_ci(mixed, "harmful_commit_rate")
        commit, commit_lo, commit_hi = simple_center_ci(mixed, "commit_rate")
        trade_rows.append({
            "arm_id": arm,
            "label": label,
            "balanced_lifecycle_mse": mse,
            "balanced_lifecycle_mse_ci_low": mse_lo,
            "balanced_lifecycle_mse_ci_high": mse_hi,
            "mixed_harmful_commit_rate": harmful,
            "mixed_harmful_commit_rate_ci_low": harmful_lo,
            "mixed_harmful_commit_rate_ci_high": harmful_hi,
            "mixed_commit_rate": commit,
            "mixed_commit_rate_ci_low": commit_lo,
            "mixed_commit_rate_ci_high": commit_hi,
            "utility_conditions": 7,
            "safety_condition": "mixed_a010_both",
            "pool": "method-development",
        })
    trade = pd.DataFrame(trade_rows)
    recent_harmful = float(trade.loc[trade.arm_id == "D0_SP_RecentOnly", "mixed_harmful_commit_rate"].iloc[0])
    if not np.isclose(recent_harmful, 0.1256944444444444, rtol=0, atol=2e-15):
        raise RuntimeError(f"Fig.5(b) RecentOnly mixed harmful audit failed: {recent_harmful}")
    trade.to_csv(DATA / "fig5b_temporal_tradeoff.csv", index=False)

    q4summary = pd.read_csv(ROOT / "results/q4_ablation/summary.csv")
    selective = q4summary[q4summary.method.isin(["Proposed", "RobustAlways"])][["attack_type", "method", "harmful_commit_rate", "harmful_commit_rate_ci_low", "harmful_commit_rate_ci_high", "commit_rate", "commit_rate_ci_low", "commit_rate_ci_high", "centers", "seeds"]].copy()
    selective["method"] = selective.method.replace({"Proposed": "Selective commit", "RobustAlways": "Always commit"})
    selective["condition"] = selective.attack_type.str.capitalize()
    selective["harmful_committed"] = selective.harmful_commit_rate
    selective["non_harmful_committed"] = selective.commit_rate - selective.harmful_commit_rate
    selective["retained"] = 1.0 - selective.commit_rate
    parts = selective[["harmful_committed", "non_harmful_committed", "retained"]].to_numpy(float)
    if (parts < -1e-12).any() or not np.allclose(parts.sum(axis=1), 1.0, rtol=0, atol=1e-12):
        raise RuntimeError("Fig.5(c) outcome decomposition is invalid")
    selective.to_csv(DATA / "fig5c_selective_commit.csv", index=False)

    kappa = pd.read_csv(ROOT / "results_v2_dev/v2_1_security_calibration/security_pareto_table.csv")
    if len(kappa) != 16 or int(kappa.selected.sum()) != 1:
        raise RuntimeError("Fig.6 kappa table is not the frozen 16-cell grid")
    kappa.to_csv(DATA / "fig6a_kappa_frontier.csv", index=False)
    general = pd.read_csv(ROOT / "results_v2_generality/generality_paired_comparisons.csv")
    general = general[(general.baseline == "Always-FT") & general.metric.isin(["lifecycle_mse", "harmful_commit_rate"])].copy()
    if len(general) != 24 or general.groupby("metric").size().to_dict() != {"harmful_commit_rate": 12, "lifecycle_mse": 12}:
        raise RuntimeError("Fig.6 must contain exactly 12 cells for each paired metric")
    general.to_csv(DATA / "fig6bc_generality_effects.csv", index=False)
    keys = ["architecture", "horizon", "scenario"]
    mse = general[general.metric == "lifecycle_mse"][keys + ["difference", "ci_low", "ci_high"]].rename(columns={"difference": "delta_lifecycle_mse", "ci_low": "delta_lifecycle_mse_ci_low", "ci_high": "delta_lifecycle_mse_ci_high"})
    harmful = general[general.metric == "harmful_commit_rate"][keys + ["difference", "ci_low", "ci_high"]].rename(columns={"difference": "delta_harmful_commit_rate", "ci_low": "delta_harmful_commit_rate_ci_low", "ci_high": "delta_harmful_commit_rate_ci_high"})
    effect = mse.merge(harmful, on=keys, validate="one_to_one")
    if len(effect) != 12:
        raise RuntimeError("Fig.6(c) effect scatter must contain exactly 12 cells")
    effect.to_csv(DATA / "fig6c_generality_effect_scatter.csv", index=False)

    alibaba = pd.read_csv(ROOT / "results_v2_alibaba/alibaba_scenario_summary.csv")
    alibaba = alibaba[alibaba.method.isin(["Proposed", "Always-FT", "ER", "Huber-FT", "Frozen"])].copy()
    alibaba["method"] = alibaba.method.replace({"Proposed": "RAVM-DT"})
    alibaba["condition"] = alibaba.scenario.map({"clean": "Clean", "mixed_a010_both": "Mixed"})
    if len(alibaba) != 10:
        raise RuntimeError("Fig.7 must contain exactly 10 method-condition cells")
    alibaba.to_csv(DATA / "fig7_alibaba_external.csv", index=False)


def build_tables() -> None:
    method = json.loads((ROOT / "configs_v2_final/frozen_v2_final_method.yaml").read_text(encoding="utf-8"))
    gate = json.loads((ROOT / "configs_v2_final/frozen_v2_final_commit_config.yaml").read_text(encoding="utf-8"))
    provenance = json.loads((ROOT / "configs_v2_final/frozen_v2_final_provenance.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "configs_v2_final/frozen_v2_minimal_confirmatory_manifest.json").read_text(encoding="utf-8"))
    environment = json.loads((ROOT / "configs_v2_final/frozen_v2_final_environment.json").read_text(encoding="utf-8"))
    baseline_protocol = json.loads((ROOT / "configs/baseline_protocol.yaml").read_text(encoding="utf-8"))
    rows = [
        ("Final centers", f"{len(manifest['centers'])} ({min(manifest['centers'])}-{max(manifest['centers'])})"),
        ("Model seeds", ", ".join(map(str, manifest["model_seeds"]))),
        ("Lifecycle stages", str(manifest["stages_per_trajectory"])),
        ("Main architecture", method["backbone"]),
        ("Input window L", str(provenance["window_length"])),
        ("Forecast horizon H", str(method["forecast_horizon"])),
        ("Adaptation optimizer / loss", f"{baseline_protocol['controlled_optimizer']} / {method['adaptation_loss'].upper()}"),
        ("Adaptation steps per stage", str(method["adaptation_steps"])),
        ("Learning rate", str(baseline_protocol["learning_rate"])),
        ("Gradient clipping", str(baseline_protocol["gradient_clip"])),
        ("History capacity", str(method["history_capacity"])),
        ("kappa_rec / kappa_hist", f"{gate['kappa_rec']} / {gate['kappa_hist']}"),
        ("delta_imp / delta_ret", f"{gate['delta_imp']:.8g} / {gate['delta_ret']:.8g}"),
        ("rho / epsilon", f"{gate['rho']:.8g} / {gate['epsilon']:.8g}"),
        ("Statistical unit", "Computing center; seeds averaged within center"),
        ("Bootstrap", f"{BOOT} center-cluster percentile replicates; seed {SEED}"),
        ("Hardware", f"{environment['gpu_name']} ({environment['torch_version']}, CUDA {environment['torch_cuda_version']})"),
    ]
    table1 = pd.DataFrame(rows, columns=["Item", "Value"])
    table1.to_csv(TABLES / "table1_main_experimental_configuration.csv", index=False)

    main = pd.read_csv(ROOT / "results_v2_final_baselines/final_main_table.csv")
    order = {name: i for i, name in enumerate(METHODS)}
    main = main.sort_values("method", key=lambda s: s.map(order))
    table2 = pd.DataFrame({
        "Method": main.method.replace({"Proposed": "RAVM-DT"}),
        "Maintenance runtime per stage (s)": main.mean_maintenance_time_s_balanced_all_7,
        "Peak GPU memory (MiB)": main.peak_gpu_memory_bytes / (2 ** 20),
        "Persistent buffer (KiB)": main.persistent_buffer_bytes / (2 ** 10),
    })
    table2.to_csv(TABLES / "table2_maintenance_cost.csv", index=False)

    def latex_table(df: pd.DataFrame, caption: str, label: str, formats: list[str] | None = None) -> str:
        cols = "ll" if len(df.columns) == 2 else "lrrr"
        lines = ["\\begin{table}[t]", "\\centering", "\\small", f"\\caption{{{caption}}}", f"\\label{{{label}}}", f"\\begin{{tabular}}{{{cols}}}", "\\toprule", " & ".join(df.columns).replace("_", "\\_") + " \\\\", "\\midrule"]
        for idx, row in df.iterrows():
            vals = []
            for j, value in enumerate(row):
                if formats and j > 0:
                    value = formats[j - 1].format(float(value))
                vals.append(str(value).replace("_", "\\_"))
            lines.append(" & ".join(vals) + " \\\\")
        lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}", ""]
        return "\n".join(lines)

    (TABLES / "table1_main_experimental_configuration.tex").write_text(latex_table(table1, "Main experimental configuration.", "tab:main_configuration"), encoding="utf-8")
    (TABLES / "table2_maintenance_cost.tex").write_text(latex_table(table2, "Maintenance cost measured in the frozen Final V2 baseline benchmark.", "tab:maintenance_cost", ["{:.4f}", "{:.2f}", "{:.2f}"]), encoding="utf-8")


def write_primary_audit(primary: pd.DataFrame, comparisons: pd.DataFrame, audit: pd.DataFrame, source_checks: list[str]) -> None:
    lines = ["# Primary Five-Condition Audit", "", "## Status", "", "**PASS** — deterministic re-aggregation only; no model training or scientific trajectory execution occurred.", "", "## Frozen statistical protocol", "", f"- Conditions: {', '.join(PRIMARY)}", "- Statistical unit: computing center.", "- Seeds are averaged within center before resampling.", f"- Center-cluster percentile bootstrap: {BOOT} replicates, seed {SEED}.", "- Every replicate recomputes the equal-weight five-condition aggregate.", "- Persistent-bias and replay verification-only conditions are excluded from this aggregate.", "", "## Authoritative identity checks", ""]
    lines += [f"- {item}" for item in source_checks]
    lines += ["", "## Five-condition estimates", "", "| Method | Metric | Estimate | 95% CI |", "|---|---|---:|---:|"]
    for row in primary.itertuples():
        lines.append(f"| {row.method} | {row.metric} | {row.estimate:.9g} | [{row.ci_low:.9g}, {row.ci_high:.9g}] |")
    lines += ["", "## Five-condition paired comparisons", "", "Differences are RAVM-DT minus baseline; all adverse and inconclusive intervals are retained.", "", "| Baseline | Metric | Difference | 95% CI | Relative change |", "|---|---|---:|---:|---:|"]
    for row in comparisons.itertuples():
        rel = "NA" if pd.isna(row.relative_percent) else f"{row.relative_percent:.3f}%"
        lines.append(f"| {row.baseline} | {row.metric} | {row.difference:.9g} | [{row.ci_low:.9g}, {row.ci_high:.9g}] | {rel} |")
    lines += ["", "## Five-condition versus published seven-condition aggregate", "", "| Method | Metric | Five-condition | Seven-condition | Difference |", "|---|---|---:|---:|---:|"]
    for row in audit.itertuples():
        lines.append(f"| {row.method} | {row.metric} | {row.five_condition:.9g} | {row.seven_condition:.9g} | {row.five_minus_seven:.9g} |")
    lines += ["", "The recomputed five-condition point estimates exactly match the frozen `*_utility_balanced_5` values. Recomputed paired estimates and confidence limits match the frozen helper output within 2e-15 absolute tolerance. These values were not used for method or parameter selection.", ""]
    (ROOT / "paper_figures/PRIMARY_FIVE_CONDITION_AUDIT.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    checks = validate_authoritative_sources()
    primary, comparisons, audit = build_primary()
    build_fig_data(primary)
    build_tables()
    write_primary_audit(primary, comparisons, audit, checks)
    print(json.dumps({"status": "PASS", "primary_rows": len(primary), "paired_rows": len(comparisons), "data_dir": str(DATA)}, indent=2))


if __name__ == "__main__":
    main()
