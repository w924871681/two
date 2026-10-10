# Paper Figure Scientific Audit

## Overall verdict

**PASS** — all figures and tables were produced by deterministic read-only aggregation of frozen results. No model training, scientific trajectory execution, threshold selection, configuration change, outlier deletion, smoothing, or result-dependent cell removal occurred.

## Figure-by-figure provenance

### Fig. 2

- Source files: `results_v2_final_baselines/baseline_center_level_summary.csv`, `results_v2_final_baselines/baseline_trajectory_index.csv`, `results_v2_final/final_trajectory_index.csv`.
- Filters: five primary lifecycle conditions only: stationary, gradual, abrupt, recurring, mixed alpha=0.10 both.
- Included methods: RAVM-DT, Always-FT, ER, EWC, Huber-FT, ValidationCommit, Frozen.
- Aggregation: seed mean within center; equal-weight scenario mean; every bootstrap replicate recomputes all five scenario means.
- Confidence interval: center-cluster percentile bootstrap, 4000 replicates, seed 2904.
- Sample/center count: 30 centers total; regime-specific clean subsets of 7/8 centers; mixed uses 30 centers.
- Plot-ready data: fig2_overall_baseline.csv.
- PDF: `paper_figures\pdf\fig2_overall_baseline.pdf`; SHA-256 `f1582ffeba4bd5f091a8e879e26915bd2f692d84b1ab1aa553d1ce9cf111df35`.
- PNG: `paper_figures\png\fig2_overall_baseline.png`; SHA-256 `1dffac0f9eb56d9bcc6a570db249158b753c20ce3cd6be4a8af44dd5ffbb7f60`; 3981x2740 pixels at 600 dpi.
- Missing/duplicate plot rows: 0/0.
- Report/raw discrepancy: none detected; upstream report and result hashes match the authoritative completion handoff.

### Fig. 3

- Source files: `results_v2_severity/severity_scenario_summary.csv`.
- Filters: RAVM-DT only; mixed, persistent bias, replay; alpha 0.05/0.10/0.20.
- Included methods: RAVM-DT.
- Aggregation: trajectory metric, seeds averaged within center, mean across centers; grouped bars preserve the nine categorical corruption cells.
- Confidence interval: center-cluster percentile bootstrap, 4000 replicates, seed 2904; thin error bars show intervals.
- Sample/center count: 30 centers, 3 seeds per cell.
- Plot-ready data: fig3_corruption_severity.csv.
- PDF: `paper_figures\pdf\fig3_corruption_severity.pdf`; SHA-256 `f51cf1e7538c6f7a93be2b7adb4619f67e0dc6db143b2cf198d0b19701b8e518`.
- PNG: `paper_figures\png\fig3_corruption_severity.png`; SHA-256 `933f310f94b511ca6f84c3a3c88aed4f350723b91dc24b74a1d7c5fa97103db2`; 4223x2610 pixels at 600 dpi.
- Missing/duplicate plot rows: 0/0.
- Report/raw discrepancy: none detected; upstream report and result hashes match the authoritative completion handoff.

### Fig. 4

- Source files: `results_v2_final_baselines/baseline_scenario_summary.csv`.
- Filters: stationary, gradual, abrupt, recurring.
- Included methods: RAVM-DT, Always-FT, Frozen.
- Aggregation: trajectory metric, seeds averaged within center.
- Confidence interval: center-cluster percentile bootstrap, 4000 replicates, seed 2904.
- Sample/center count: 7 or 8 centers per regime, 3 seeds.
- Plot-ready data: fig4_benign_evolution.csv.
- PDF: `paper_figures\pdf\fig4_benign_evolution.pdf`; SHA-256 `d5c73d4162eeb1db101b572cba51a540c00df028cd15189e00e7cb1368f9fcd1`.
- PNG: `paper_figures\png\fig4_benign_evolution.png`; SHA-256 `670ec62b7bdd05e3dc2f1269bb83ec71a6c5d3d86e7ea26a58c135122616fe7c`; 4245x1479 pixels at 600 dpi.
- Missing/duplicate plot rows: 0/0.
- Report/raw discrepancy: none detected; upstream report and result hashes match the authoritative completion handoff.

### Fig. 5

- Source files: `results/q4_ablation/raw_episode_results.csv`, `results/q4_ablation/summary.csv`, `results_v2_dev/development/development_trajectory_metrics.csv`.
- Filters: method-development/mechanism pools only; clean/mixed for candidate and selective-commit panels; seven frozen development scenarios for balanced MSE; mixed_a010_both only for temporal-evidence harmful risk.
- Included methods: mechanism variants only; V1 LegacyFull is not presented as a main baseline.
- Aggregation: stage mean to trajectory; seeds averaged within center; paired differences, equal-weight seven-scenario MSE, mixed-only harmful risk, and exact 100% outcome decomposition as specified per panel.
- Confidence interval: center-cluster percentile bootstrap, 4000 replicates, seed 2904.
- Sample/center count: Q4: 10 centers x 3 seeds; V2 development: 20 centers x 3 seeds for mixed safety and the frozen development subsets for balanced utility.
- Plot-ready data: fig5a_candidate_complexity.csv; fig5b_temporal_tradeoff.csv; fig5c_selective_commit.csv.
- PDF: `paper_figures\pdf\fig5_mechanism_analysis.pdf`; SHA-256 `038d8ce56bf4d40288d7a3153de5048d9f819543d60ffc79ec57b9be3c3e6da4`.
- PNG: `paper_figures\png\fig5_mechanism_analysis.png`; SHA-256 `2054a953a29a6fb0925ba6356365d3943f6bd75000a19548e83bc3609c6e52d9`; 4546x1673 pixels at 600 dpi.
- Missing/duplicate plot rows: 0/0.
- Report/raw discrepancy: none detected; upstream report and result hashes match the authoritative completion handoff.

### Fig. 6

- Source files: `results_v2_dev/v2_1_security_calibration/security_pareto_table.csv`, `results_v2_generality/generality_paired_comparisons.csv`.
- Filters: all 16 frozen kappa cells; all 3 architectures x 2 horizons x 2 conditions.
- Included methods: RAVM-DT paired with Always-FT in the generality effect scatter.
- Aggregation: frozen calibration summaries; paired center differences merged by architecture-horizon-condition.
- Confidence interval: center-cluster percentile bootstrap, 4000 replicates, seed 2904 for paired effects.
- Sample/center count: 16 kappa cells; 12 generality cells, each 20 centers x 3 seeds.
- Plot-ready data: fig6a_kappa_frontier.csv; fig6bc_generality_effects.csv; fig6c_generality_effect_scatter.csv.
- PDF: `paper_figures\pdf\fig6_sensitivity_generality.pdf`; SHA-256 `a9ae82ba5ca199b253df5b48bd640ee3a80893a6a5278f87d193426cc59b5e08`.
- PNG: `paper_figures\png\fig6_sensitivity_generality.png`; SHA-256 `7a64be3b6c6f0526af20f359e04fe31f2330c72e3adabfe88515b1030830d6e9`; 4281x2708 pixels at 600 dpi.
- Missing/duplicate plot rows: 0/0.
- Report/raw discrepancy: none detected; upstream report and result hashes match the authoritative completion handoff.

### Fig. 7

- Source files: `results_v2_alibaba/alibaba_scenario_summary.csv`.
- Filters: exact prior 40-machine split; clean and mixed alpha=0.10; no Alibaba recalibration.
- Included methods: RAVM-DT, Always-FT, ER, Huber-FT, Frozen.
- Aggregation: seeds averaged within machine, mean across machines.
- Confidence interval: machine-cluster percentile bootstrap, 4000 replicates, seed 2904.
- Sample/center count: 40 machines x 3 seeds per method-condition cell.
- Plot-ready data: fig7_alibaba_external.csv.
- PDF: `paper_figures\pdf\fig7_alibaba_external.pdf`; SHA-256 `f8488651629c9aa545547345403b126dd0195aa0089a376c8bc89d6a0d5b25c5`.
- PNG: `paper_figures\png\fig7_alibaba_external.png`; SHA-256 `62c653c68dee4abc2b39cc25bf48927d76b7410e0fe5babdc98fea47b2f65832`; 4080x2683 pixels at 600 dpi.
- Missing/duplicate plot rows: 0/0.
- Report/raw discrepancy: none detected; upstream report and result hashes match the authoritative completion handoff.

## Mandatory boundary checks

| Check | Result | Evidence |
|---|---|---|
| Fig. 2 uses five conditions | PASS | Exactly stationary, gradual, abrupt, recurring, and mixed alpha=0.10 both. |
| Persistent/replay excluded from Fig. 2 | PASS | Both appear only in security/mechanism sources, never `fig2_overall_baseline.csv`. |
| Fig. 3 uses frozen severity results only | PASS | The 3 corruption types x 3 alpha cells are read from the frozen severity scenario summary. |
| Fig. 4 uses benign clean regimes only | PASS | Exactly stationary, gradual, abrupt, and recurring are retained. |
| Fig. 5 uses only development/mechanism pools | PASS | Sources are frozen Q4 ablation and V2 development files; no final heldout result is pooled into mechanism estimates. |
| Fig. 5(b) RecentOnly mixed harmful value | PASS | Frozen development raw summary gives 0.1256944444444444 (12.5694%); the former seven-scenario 4.4841% aggregate is excluded from the y-axis. |
| Fig. 5(c) outcome bars sum to 100% | PASS | Harmful committed + non-harmful committed + retained is checked to equal 1 for every method-condition row. |
| Fig. 6 kappa grid not rerun or retuned | PASS | All 16 rows are copied from the frozen security Pareto table; the selected row remains kappa_rec=0, kappa_hist=0.5. |
| Phase E 12 cells complete | PASS | MLP/TCN/GRU x H=1/4 x clean/mixed = 12 merged paired-effect cells. |
| Fig. 7 has no Alibaba recalibration | PASS | Exact prior 40-machine external-domain split and frozen Final V2 are used. |
| Service data used for a new model decision | PASS (none) | This pipeline reads completed summaries/raw result rows and performs aggregation/plotting only. |
| Scientific values come from frozen results | PASS | Six authoritative report hashes and four machine-readable result hash manifests were verified before aggregation. |
| Models or trajectories rerun | PASS (none) | Entrypoints under `paper_figures/scripts` contain no model/core runner imports except the frozen statistical helper. |
| Adverse/inconclusive cells omitted | PASS (none) | Every specified method, alpha, regime, kappa cell, architecture, horizon, and external condition is retained. |

## Publication-output QA

- All six PNG files pass the strict figure checker at 600 dpi (reported metadata: 599.9988 dpi due to PNG unit conversion).
- All six PDFs are vector outputs. Independent `pdffonts` inspection confirms that all used fonts are embedded and subsetted.
- Color and grayscale renders were inspected for clipping, panel-label placement, legend overlap, marker separation, reference-line occlusion, and manuscript-width readability; no blocking issue remains.
- The six-figure sequence uses distinct scientific chart grammars: horizontal baseline bars; grouped corruption bars; Cleveland/dumbbell; forest/scatter/100% stacked bars; parameter heatmaps/split effect scatters; horizontal grouped external-transfer bars.
- Grayscale review copies are retained under `paper_figures/audits/grayscale/`; they are QA artifacts, not submission figures.

## Primary five-condition cross-check

The recomputed five-condition estimates match the frozen `*_utility_balanced_5` point estimates exactly within 2e-15. All paired point estimates and interval endpoints match the existing frozen bootstrap helper output within the same tolerance. Full values and five-versus-seven differences are in `paper_figures/PRIMARY_FIVE_CONDITION_AUDIT.md`.

## Tables

- Table 1 CSV/LaTeX: `paper_figures\tables\table1_main_experimental_configuration.csv`, `paper_figures\tables\table1_main_experimental_configuration.tex`.
- Table 2 CSV/LaTeX: `paper_figures\tables\table2_maintenance_cost.csv`, `paper_figures\tables\table2_maintenance_cost.tex`.
- Table 2 uses binary units consistently: MiB = bytes / 2^20 and KiB = bytes / 2^10.
