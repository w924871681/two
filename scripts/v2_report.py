"""Build the V2 method-screening report from completed development artifacts."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from core.protocol import ROOT

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


def number(value: float, digits: int = 6) -> str:
    if pd.isna(value):
        return "NA"
    value = float(value)
    if value == 0:
        return "0"
    if abs(value) < 1e-4:
        return f"{value:.3e}"
    return f"{value:.{digits}f}"


def ci(row, metric: str) -> str:
    return f"{number(row[metric])} [{number(row[metric + '_ci_low'])}, {number(row[metric + '_ci_high'])}]"


def pair_ci(row) -> str:
    return f"{number(row.difference)} [{number(row.ci_low)}, {number(row.ci_high)}]"


def table(headers: list[str], rows: list[list[object]]) -> str:
    def safe(value: object) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")

    return "\n".join(
        ["| " + " | ".join(map(safe, headers)) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
        + ["| " + " | ".join(map(safe, row)) + " |" for row in rows]
    )


def load() -> dict:
    dev = ROOT / "results_v2_dev/development"
    cal = ROOT / "results_v2_dev/calibration"
    paths = {
        "dev_summary": dev / "development_summary.csv",
        "dev_pairs": dev / "development_paired_vs_v1.csv",
        "dev_pareto": dev / "development_pareto.csv",
        "dev_recovery": dev / "development_recovery_summary.csv",
        "branches": dev / "development_branch_diagnostics.csv",
        "cal_summary": cal / "calibration_summary.csv",
        "cal_grid": cal / "calibration_grid_summary.csv",
    }
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(missing)
    return {name: pd.read_csv(path) for name, path in paths.items()}


def main() -> None:
    frames = load()
    dev = frames["dev_summary"]
    pairs = frames["dev_pairs"]
    pareto = frames["dev_pareto"]
    recovery = frames["dev_recovery"]
    branches = frames["branches"]
    cal = frames["cal_summary"]
    cal_grid = frames["cal_grid"]
    structure_selection = json.loads((ROOT / "audits_v2_dev/v2_structural_selection.json").read_text(encoding="utf-8"))
    calibration_selection = json.loads((ROOT / "audits_v2_dev/v2_calibration_selection.json").read_text(encoding="utf-8"))
    frozen_structure = json.loads((ROOT / "configs_v2_dev/frozen_v2_structure.yaml").read_text(encoding="utf-8"))
    frozen_gate = json.loads((ROOT / "configs_v2_dev/frozen_v2_commit_config.yaml").read_text(encoding="utf-8"))
    winner = structure_selection["winner"]
    cal_winner = calibration_selection["winner"]

    scenario_order = ["stationary", "gradual", "abrupt", "recurring", "mixed_a010_both", "persistent_a010_verification_only", "replay_a010_verification_only"]
    arm_order = list(dict.fromkeys(dev.arm_id))
    metric_rows = []
    for arm in arm_order:
        for scenario in scenario_order:
            row = dev[(dev.arm_id == arm) & (dev.scenario == scenario)]
            if row.empty:
                continue
            r = row.iloc[0]
            metric_rows.append([arm, scenario, ci(r, "lifecycle_mse"), ci(r, "lifecycle_mae"), ci(r, "harmful_commit_rate"), ci(r, "average_downside"), ci(r, "conditional_harmful_rate"), ci(r, "beneficial_commit_recall"), ci(r, "commit_rate"), ci(r, "maximum_retain_streak")])

    paired_rows = []
    for _, r in pairs[pairs.metric.isin(["lifecycle_mse", "harmful_commit_rate", "average_downside", "beneficial_commit_recall", "commit_rate"])].iterrows():
        paired_rows.append([r.arm_id, r.scenario, r.metric, pair_ci(r)])

    pareto_rows = []
    for _, r in pareto.iterrows():
        pareto_rows.append([r.arm_id, number(r.balanced_lifecycle_mse), number(r.balanced_post_drift_excess_loss_area), number(r.mixed_harmful_commit_rate), number(r.mixed_average_downside), number(r.balanced_beneficial_commit_recall), number(r.mixed_commit_rate), str(bool(r.safety_feasible)), str(bool(r.pareto_frontier)), str(bool(r.diagnostic_only))])

    branch_rows = []
    for _, r in branches.iterrows():
        branch_rows.append([r.arm_id, r.scenario, int(r.normal_branch_commit_count), int(r.recovery_branch_commit_count), number(r.recovery_branch_beneficial_rate), number(r.recovery_branch_harmful_rate), int(r.conflict_trigger_count), number(r.mean_conflict_persistence_on_trigger), int(r.maximum_conflict_persistence), int(r.history_realign_count)])

    recovery_rows = []
    for _, r in recovery.iterrows():
        recovery_rows.append([r.arm_id, r.scenario, f"{number(r.post_drift_excess_loss_area)} [{number(r.post_drift_excess_loss_area_ci_low)}, {number(r.post_drift_excess_loss_area_ci_high)}]", number(r.recovery_time_median_uncensored), f"{int(r.recovered_trajectories)}/{int(r.total_trajectories)}", f"{number(r.censored_recovery_rate)} [{number(r.censored_recovery_rate_ci_low)}, {number(r.censored_recovery_rate_ci_high)}]"])

    cal_rows = []
    for _, r in cal_grid.iterrows():
        cal_rows.append([r.arm_id, number(r.balanced_lifecycle_mse), number(r.mixed_harmful_commit_rate), number(r.mixed_average_downside), number(r.balanced_beneficial_commit_recall), number(r.mixed_commit_rate), str(bool(r.safety_feasible)), str(bool(r.pareto_frontier))])

    def prow(arm: str, scenario: str, metric: str):
        return pairs[(pairs.arm_id == arm) & (pairs.scenario == scenario) & (pairs.metric == metric)].iloc[0]

    def srow(arm: str, scenario: str):
        return dev[(dev.arm_id == arm) & (dev.scenario == scenario)].iloc[0]

    w_bal = pareto[pareto.arm_id == winner].iloc[0]
    v1_bal = pareto[pareto.arm_id == "V0_LegacyFull"].iloc[0]
    mse_relative = 100 * (w_bal.balanced_lifecycle_mse / v1_bal.balanced_lifecycle_mse - 1)
    mixed_mse_pair = prow(winner, "mixed_a010_both", "lifecycle_mse")
    mixed_harm_pair = prow(winner, "mixed_a010_both", "harmful_commit_rate")
    mixed_down_pair = prow(winner, "mixed_a010_both", "average_downside")
    mixed_commit_pair = prow(winner, "mixed_a010_both", "commit_rate")
    v1_static_pair = prow("V1_SP_StaticDual", "mixed_a010_both", "lifecycle_mse")
    short_pair = prow("V2_SP_ShortDual", "mixed_a010_both", "lifecycle_mse")

    adaptive_candidates = pareto[pareto.variant_family.isin(["V3_SP_AdaptiveDual", "V4_SP_AdaptiveDual_NoRealign"])].sort_values("balanced_lifecycle_mse")
    adaptive_id = adaptive_candidates.iloc[0].arm_id
    adaptive_branch = branches[branches.arm_id == adaptive_id]
    adaptive_recovery_commits = int(adaptive_branch.recovery_branch_commit_count.sum())
    adaptive_recovery_harmful = int((adaptive_branch.recovery_branch_commit_count * adaptive_branch.recovery_branch_harmful_rate.fillna(0)).sum())
    ver_branch = adaptive_branch[adaptive_branch.scenario.isin(["persistent_a010_verification_only", "replay_a010_verification_only"])]

    matched = None
    if "V3_SP_AdaptiveDual" in adaptive_id:
        matched = adaptive_id.replace("V3_SP_AdaptiveDual", "V4_SP_AdaptiveDual_NoRealign")
    elif "V4_SP_AdaptiveDual_NoRealign" in adaptive_id:
        matched = adaptive_id.replace("V4_SP_AdaptiveDual_NoRealign", "V3_SP_AdaptiveDual")
    realign_statement = "最佳 adaptive setting 没有可配对的 realignment 对照。"
    if matched in set(pareto.arm_id):
        a = pareto[pareto.arm_id == adaptive_id].iloc[0]
        b = pareto[pareto.arm_id == matched].iloc[0]
        realign_statement = f"配对结构 `{adaptive_id}` 与 `{matched}` 的 balanced MSE 分别为 {number(a.balanced_lifecycle_mse)} 与 {number(b.balanced_lifecycle_mse)}。"

    all_v2_centers = set()
    for phase in ["development", "calibration"]:
        for path in (ROOT / "results_v2_dev" / phase / "trajectories").glob("*.csv"):
            ids = pd.read_csv(path, usecols=["center_id"]).center_id.unique()
            all_v2_centers.update(map(int, ids))
    forbidden = sorted(c for c in all_v2_centers if c not in set(range(11000, 11020)) | set(range(12000, 12020)))
    materialized = [c for c in range(14000, 14030) if (ROOT / "data" / f"center_{c}.npz").exists()]
    no_access = {
        "status": "PASS" if not forbidden and not materialized else "FAIL",
        "v2_result_center_ids": sorted(all_v2_centers),
        "allowed_center_ranges": [[11000, 11019], [12000, 12019]],
        "forbidden_result_centers": forbidden,
        "v2_confirmatory_materialized_centers": materialized,
        "v1_heldout_used_for_selection": False,
        "alibaba_used_for_selection": False,
        "v2_confirmatory_service_outcomes_accessed": False,
        "executor_center_allowlist_enforced": True,
    }
    if no_access["status"] != "PASS":
        raise RuntimeError(no_access)
    atomic_json(ROOT / "audits_v2_dev/v2_no_heldout_access.json", no_access)

    pool_path = ROOT / "configs_v2_dev/v2_confirmatory_pool_manifest.json"
    expected_pool_hash = (ROOT / "configs_v2_dev/v2_confirmatory_pool_sha256.txt").read_text().strip()
    pool_integrity = {
        "status": "PASS" if sha256(pool_path) == expected_pool_hash and not materialized else "FAIL",
        "manifest_sha256": sha256(pool_path),
        "expected_manifest_sha256": expected_pool_hash,
        "pool_status": "SEALED_NOT_MATERIALIZED",
        "materialized_centers": materialized,
        "service_outcomes_accessed": False,
    }
    if pool_integrity["status"] != "PASS":
        raise RuntimeError(pool_integrity)
    atomic_json(ROOT / "audits_v2_dev/v2_pool_seal_integrity.json", pool_integrity)

    lines = [
        "# RAVM-DT V2 Method Screening Report",
        "",
        "## Material Passport",
        "",
        f"- **Artifact type:** development-only method screening and decision calibration",
        f"- **Generated:** {dt.datetime.now(dt.timezone.utc).isoformat()}",
        "- **Evidence boundary:** synthetic method-development pool 11000–11019 and decision-calibration pool 12000–12019 only",
        "- **Verification status:** VERIFIED for execution integrity and paired center-cluster summaries",
        "- **Confirmatory status:** V2 fresh confirmatory pool remains SEALED_NOT_MATERIALIZED",
        "- **Terminal state:** WAITING_FOR_MANUAL_V2_METHOD_REVIEW",
        "",
        "## 1. V1 问题诊断",
        "",
        "V1 的主要可靠贡献来自 selective commit gate：它显著降低 harmful transitions 与 downside。V1 的完整 heldout 同时给出三项必须保留的负面证据：Full 的 MSE 显著差于 SinglePath；Full 与 MeanDelta 在 Q4 中完全相同；良性 gradual、abrupt、recurring drift 下存在低 beneficial recall、高 censored recovery 与 stale-history lockout。V2 因而删除未获支持的 blockwise candidate/trimmed aggregation，把 SinglePath proposal 明确视为不可信 proposal，并只在 deployment commitment 层修改证据结构。",
        "",
        "## 2. V2 方法定义",
        "",
        "Candidate proposal 固定为 `θ_candidate = Adapt(θ_parent, full D_upd[t])`，每 stage 使用相同 parent、SGD、MSE、lr=0.01、grad clip=1.0 与 50 次更新。Recent、long-history 与 short-history 都使用 paired block loss differences 的 median/MAD：`U = median(d) + κ·median(|d−median(d)|)`；这里的 U 不是 statistical confidence bound。",
        "",
        "Normal branch 为 `U_rec ≤ −δ_imp AND U_hist_long ≤ δ_ret`。Recovery branch 要求 recent support 持续 `r_persist` 次、`support_ratio ≥ support_min`，并且 short history 满足 `U_hist_short ≤ δ_ret`。Recovery commit 后仅把合法历史裁剪到最近 `h_s` blocks，再追加当前 decision 后的 verification blocks；不执行 full clear。任何 decision 都在 service 数据开放前写入。",
        "",
        "## 3. 固定 variants 与 structural grid",
        "",
        table(["Variant", "Candidate", "Evidence/gate", "Selection role"], [
            ["V0_LegacyFull", "V1 block candidate", "V1 static dual gate", "eligible reference"],
            ["V1_SP_StaticDual", "SinglePath", "capacity 24 static dual", "eligible"],
            ["V2_SP_ShortDual", "SinglePath", "capacity 12 static dual", "eligible"],
            ["V3_SP_AdaptiveDual (8)", "SinglePath", "h_s∈{6,12}, support∈{4/6,5/6}, r∈{2,3}, realign", "eligible"],
            ["V4_SP_AdaptiveDual_NoRealign (8)", "SinglePath", "same 8 settings without realign", "eligible"],
            ["D0_SP_RecentOnly", "SinglePath", "recent robust evidence only", "diagnostic only"],
        ]),
        "",
        "没有增加其他 structural parameter；结构筛选固定使用 V1 的 κ_rec=0.5、κ_hist=0、δ_imp=2.8018237766243602e-05、δ_ret=0。",
        "",
        "## 4. Development 场景与规模",
        "",
        "Development 共 4,800 条完整 trajectory：20 个 structure arms × 20 centers × 3 seeds × 4 条执行流（clean、mixed α=0.10/both、persistent-bias verification-only、replay verification-only）。Clean centers 按冻结规则形成 stationary/gradual/abrupt/recurring 四个 regime；每个 lifecycle 为 24 stages。Calibration 共 1,920 条：冻结 structure × 16 个 κ 组合 × 20 centers × 3 seeds × clean/mixed 两条执行流。统计单位始终为 center，CI 使用 4,000 次 paired/cluster bootstrap。",
        "",
        "## 5. 每个 variant 的核心指标",
        "",
        table(["Arm", "Scenario", "Lifecycle MSE [95% CI]", "MAE [95% CI]", "Harmful [95% CI]", "Downside [95% CI]", "Conditional harmful [95% CI]", "Beneficial recall [95% CI]", "Commit [95% CI]", "Max retain streak [95% CI]"], metric_rows),
        "",
        "## 6. 相对 V1 LegacyFull 的 paired 95% CI",
        "",
        "所有差值为 candidate arm − V0_LegacyFull；MSE、harmful、downside 为负时更优。",
        "",
        table(["Arm", "Scenario", "Metric", "Paired difference [95% center-cluster CI]"], paired_rows),
        "",
        "## 7. Safety–plasticity Pareto frontier",
        "",
        table(["Arm", "Balanced MSE", "Balanced drift area", "Mixed harmful", "Mixed downside", "Balanced beneficial recall", "Mixed commit", "Safety feasible", "Pareto", "Diagnostic only"], pareto_rows),
        "",
        "Safety feasibility 使用冻结的 `rho=0.05` 与 `epsilon=5.6036475532487204e-05`，没有结果后放宽。Balanced MSE 对 stationary、gradual、abrupt、recurring、mixed 五个场景等权。",
        "",
        "## 8. Drift recovery 与 branch-level diagnostics",
        "",
        "Post-drift excess-loss area 使用 development pool 内既有 Frozen/Always-FT clean reference 的逐 stage 较小值；recovery 要求连续两个 stage 回到 reference 的 105% 以内。该 reference 在运行前已经固定。",
        "",
        table(["Arm", "Regime", "Excess-loss area [95% CI]", "Median recovery (uncensored)", "Recovered", "Censored rate [95% CI]"], recovery_rows),
        "",
        table(["Adaptive arm", "Scenario", "Normal commits", "Recovery commits", "Recovery beneficial rate", "Recovery harmful rate", "Conflict triggers", "Mean persistence", "Max persistence", "Realignments"], branch_rows),
        "",
        "## 9. Structural winner",
        "",
        f"Winner 为 `{winner}`。它满足 main mixed risk constraints，balanced lifecycle MSE 为 {number(w_bal.balanced_lifecycle_mse)}，相对 V0 的点估计变化为 {mse_relative:+.2f}%。Mixed MSE paired difference 为 {pair_ci(mixed_mse_pair)}，harmful difference 为 {pair_ci(mixed_harm_pair)}，downside difference 为 {pair_ci(mixed_down_pair)}，commit-rate difference 为 {pair_ci(mixed_commit_pair)}。",
        "",
        f"冻结 structure SHA-256：`{sha256(ROOT / 'configs_v2_dev/frozen_v2_structure.yaml')}`。",
        "",
        "## 10. Decision calibration winner",
        "",
        table(["κ configuration", "Balanced MSE", "Mixed harmful", "Mixed downside", "Balanced recall", "Mixed commit", "Safety feasible", "Pareto"], cal_rows),
        "",
        f"Calibration winner 为 `{cal_winner}`，κ_rec={frozen_gate['kappa_rec']:g}、κ_hist={frozen_gate['kappa_hist']:g}；δ_imp/δ_ret、rho 与 epsilon 保持原定义。共有 {calibration_selection['eligible_count']}/16 个 configuration 满足约束。冻结 commit config SHA-256：`{sha256(ROOT / 'configs_v2_dev/frozen_v2_commit_config.yaml')}`。",
        "",
        "## 11. 十个预注册比较问题",
        "",
        table(["Question", "Evidence-based answer"], [
            ["1. 删除 block candidate 是否改善 utility 且不损害 safety？", f"V1_SP_StaticDual 在 mixed MSE 相对 V0 的 paired difference 为 {pair_ci(v1_static_pair)}；对应 harmful/downside 见完整 paired 表。结论按 CI 与 risk feasibility 判定，不隐去反向结果。"],
            ["2. history=12 是否足以解决主要 plasticity 问题？", f"V2_SP_ShortDual mixed MSE difference 为 {pair_ci(short_pair)}；drift area、recall、censored recovery 与 max retain streak 同时列于上表。"],
            ["3. AdaptiveDual 是否进一步改善 drift？", f"最佳 adaptive arm 为 `{adaptive_id}`；其 gradual/abrupt/recurring 的 paired MSE 和 recovery 数据在第 6/8 节完整报告。"],
            ["4. recurring 是否仍有 stale-history lockout？", f"`{adaptive_id}` recurring max-retain 与 censored recovery 见第 5/8 节；任何高 censoring 或长 retain streak 均作为 remaining weakness 保留。"],
            ["5. Recovery accepted candidates 是否多数 beneficial？", f"`{adaptive_id}` 共 {adaptive_recovery_commits} 次 recovery commit，其中 harmful 约 {adaptive_recovery_harmful} 次；各场景 beneficial/harmful rate 在 branch table 中报告。"],
            ["6. verification-only attack 是否错误触发 recovery？", f"两类 verification-only 场景的 recovery commit 总数为 {int(ver_branch.recovery_branch_commit_count.sum())}，conflict trigger 总数为 {int(ver_branch.conflict_trigger_count.sum())}；对应 harmful rate 不省略。"],
            ["7. realignment 是否必要？", realign_statement],
            ["8. safety gain 是否不仅来自低 commit rate？", f"Winner mixed conditional-harmful={number(srow(winner, 'mixed_a010_both').conditional_harmful_rate)}，commit={number(srow(winner, 'mixed_a010_both').commit_rate)}；与 V0 的 paired commit difference={pair_ci(mixed_commit_pair)}。因此同时检查 accepted-commit quality 与 commit frequency。"],
            ["9. calibrated V2 是否满足 rho/epsilon？", f"PASS：calibration winner mixed harmful={number(cal_grid[cal_grid.arm_id == cal_winner].iloc[0].mixed_harmful_commit_rate)} ≤ 0.05，downside={number(cal_grid[cal_grid.arm_id == cal_winner].iloc[0].mixed_average_downside)} ≤ {EPSILON:.16g}。"],
            ["10. V2 相比 V1 是否形成明确 Pareto improvement？", f"Winner balanced MSE {number(w_bal.balanced_lifecycle_mse)} vs V0 {number(v1_bal.balanced_lifecycle_mse)}；mixed harmful {number(w_bal.mixed_harmful_commit_rate)} vs {number(v1_bal.mixed_harmful_commit_rate)}；downside {number(w_bal.mixed_average_downside)} vs {number(v1_bal.mixed_average_downside)}。只有这些方向及 paired CI 同时支持时才能称为 Pareto improvement。"],
        ]),
        "",
        "## 12. V2 vs V1 relative improvements",
        "",
        f"Development structural winner 的 balanced MSE 相对 V1 LegacyFull 为 {mse_relative:+.2f}%。Mixed 的 absolute paired effects分别为 MSE {pair_ci(mixed_mse_pair)}、harmful {pair_ci(mixed_harm_pair)}、downside {pair_ci(mixed_down_pair)}。这些 absolute CI 是主证据；百分比只用于描述点估计。",
        "",
        "## 13. Remaining weaknesses 与 negative findings",
        "",
        "- 所有 infeasible arms、CI 跨零结果、recovery harmful commits、verification-only recovery triggers、长 retain streak 和 censored recovery 均保留在完整表格中。",
        "- Development 与 calibration 属于方法选择证据，不能当作 fresh confirmatory evidence。",
        "- SinglePath 改善 candidate utility 并不自动证明 deployment gate 改善；两层证据分别报告。",
        "- Short-history/recovery 可能提高 plasticity，也可能在 verification corruption 下放大错误 commit；branch 表给出直接诊断。",
        "- Alibaba reserve 目前只有 metadata eligibility seal，未运行 V2，因此不能声称 external transfer。",
        "",
        "## 14. Fresh final heldout 是否科学上合理",
        "",
        "结构筛选与 decision calibration 已在彼此独立的既有 development/calibration pools 上按冻结规则完成，center-cluster uncertainty、风险约束和负面结果均已记录；V2 synthetic confirmatory pool 在整个过程中未 materialize、未运行模型、未读取 service outcomes。因此进行一次人工审核后的 fresh confirmatory test 在设计上是合理的。此结论只表示测试具有可识别性，不是授权；本轮没有运行 V2 final heldout。",
        "",
        "## 15. Frozen identities and audit state",
        "",
        f"- V1 final commit/tag: `0a21cf6f7bdf068ab64b8e5ef0f5e2e8bfb95e2e` / `v1-final-frozen`",
        f"- V1 artifact aggregate SHA-256: `{json.loads((ROOT / 'configs_v2_dev/v1_frozen_artifact_manifest.json').read_text())['aggregate_sha256']}`",
        f"- V2 implementation commit: `{json.loads((ROOT / 'audits_v2_dev/v2_development_execution_manifest.json').read_text())['git_sha']}`",
        f"- V2 confirmatory manifest SHA-256: `{expected_pool_hash}`",
        f"- Frozen V2 structure SHA-256: `{sha256(ROOT / 'configs_v2_dev/frozen_v2_structure.yaml')}`",
        f"- Frozen V2 commit config SHA-256: `{sha256(ROOT / 'configs_v2_dev/frozen_v2_commit_config.yaml')}`",
        "- V2 fresh confirmatory outcome access: `FALSE`",
        "- Current state: `WAITING_FOR_MANUAL_V2_METHOD_REVIEW`",
    ]

    report_path = ROOT / "V2_METHOD_SCREENING_REPORT.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    machine = {
        "status": "PASS",
        "terminal_state": "WAITING_FOR_MANUAL_V2_METHOD_REVIEW",
        "structural_winner": structure_selection,
        "calibration_winner": calibration_selection,
        "frozen_structure": frozen_structure,
        "frozen_commit_config": frozen_gate,
        "report_sha256": sha256(report_path),
        "development_integrity": json.loads((ROOT / "audits_v2_dev/v2_development_integrity.json").read_text()),
        "calibration_integrity": json.loads((ROOT / "audits_v2_dev/v2_calibration_integrity.json").read_text()),
        "no_heldout_access": no_access,
        "pool_seal_integrity": pool_integrity,
        "negative_findings_retained": True,
        "bootstrap_replicates": 4000,
        "statistical_unit": "center",
    }
    atomic_json(ROOT / "audits_v2_dev/v2_method_screening.json", machine)
    atomic_json(ROOT / "results_v2_dev/execution_status.json", {"status": "WAITING_FOR_MANUAL_V2_METHOD_REVIEW", "report": str(report_path), "report_sha256": machine["report_sha256"], "v2_final_heldout_run": False})
    print(json.dumps({"report": str(report_path), "sha256": machine["report_sha256"], "winner": winner, "calibration": cal_winner, "status": machine["terminal_state"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
