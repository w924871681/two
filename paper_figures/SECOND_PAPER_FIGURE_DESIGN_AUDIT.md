# Second-Paper Figure Design Audit

## Overall verdict

**PASS.** Fig. 2--Fig. 7 use six scientific chart grammars chosen for their respective questions while sharing the first paper's muted palette, typography, line weights, legends, and spacing. All plotted values remain sourced from the existing frozen RAVM-DT plot-ready CSVs.

| Figure | Scientific question and chart choice | Visual/color encoding | CI encoding | Frozen source data | Change from preceding version |
|---|---|---|---|---|---|
| Fig. 2 | Which method has the best overall lifecycle utility/safety profile? A 2x2 horizontal bar layout accommodates seven long method labels and supports direct baseline ranking. | One muted categorical color per method; RAVM-DT is bold and hatched; ValidationCommit and Frozen remain gray-family controls. | Thin horizontal 95% center-cluster bootstrap intervals with small caps. | `data/fig2_overall_baseline.csv` | Replaced vertical bars with the first-paper-style horizontal baseline layout and added restrained value labels. |
| Fig. 3 | How does each categorical corruption type behave at the three frozen alpha levels? Grouped vertical bars preserve discrete condition identity without implying interpolation. | Mixed blue, persistent bias orange, replay blue-gray; colors encode corruption type. | Thin vertical 95% center-cluster bootstrap intervals. | `data/fig3_corruption_severity.csv` | Replaced heatmaps with 2x2 grouped bars; panel (b) now carries the 5% synthetic calibration criterion. |
| Fig. 4 | How do RAVM-DT, Always-FT, and Frozen compare across benign regimes, and how do commit and recall trade off? Cleveland and dumbbell plots show direct within-row comparisons. | RAVM-DT blue, Always-FT/recall orange, Frozen gray; very light connectors span the estimates. | Horizontal 95% center-cluster bootstrap intervals on every point. | `data/fig4_benign_evolution.csv` | Preserved chart family, tightened spacing, aligned regime rows, and lightened connectors/grid. |
| Fig. 5 | Which candidate/evidence/commit mechanisms drive results? Forest, two-dimensional tradeoff scatter, and 100% outcome bars answer three different mechanism questions. | Clean/proposed blue, mixed/aggressive orange, conservative gray; harmful rust, non-harmful committed blue, retained light gray. | Forest and tradeoff points retain paired 95% center-cluster bootstrap intervals; stacked bars show exact outcome shares. | `data/fig5a_candidate_complexity.csv`, `fig5b_temporal_tradeoff.csv`, `fig5c_selective_commit.csv` | Chart types retained; spacing, legend, saturation, and panel alignment refined. RecentOnly uses the audited mixed harmful rate 12.5694%. |
| Fig. 6 | How sensitive is the frozen decision rule, and does the effect generalize across architectures/horizons? Two heatmaps expose the full 16-cell grid; separate clean/mixed scatters avoid overloading one panel. | Restrained sequential heatmaps use observed-range limits plus a 6% neutral margin. Architecture uses color; H=1/H=4 uses circle/square. | Generality effects show paired 95% center-cluster bootstrap intervals on both axes. | `data/fig6a_kappa_frontier.csv`, `fig6c_generality_effect_scatter.csv` | Expanded from 1x3 to 2x2; split 12 cells into six clean and six mixed cells; removed redundant condition fill; frozen cell labeled only “Frozen setting.” |
| Fig. 7 | Does the frozen method transfer to Alibaba under clean and mixed monitoring? Horizontal grouped bars expose within-method condition differences. | Condition palette only: clean pale blue-gray and mixed muted blue; method identity is carried by row labels. RAVM-DT uses bold label/stronger edge. | Thin horizontal 95% machine-cluster bootstrap intervals. | `data/fig7_alibaba_external.csv` | Removed method-rainbow encoding; panel (b) retains the 5% synthetic-domain criterion and visibly places RAVM-DT mixed above it. |

## Cross-figure checks

- White background, serif publication font, thin spines, outward ticks, and light gray grids are consistent.
- No Matplotlib default categorical palette, rainbow map, heavy outline, 3-D effect, shadow, regression, smoothing, or trend line is used.
- Method colors appear only where method is the variable being encoded. Condition-focused figures encode condition.
- Point estimates remain visually primary; intervals and reference criteria remain subordinate.
- No chart labels a frozen configuration as “optimal.”
- Negative, adverse, and inconclusive cells remain present.

## Scientific invariance

The redesign changes only plotting code, visual encoding, and captions. It does not rerun models or trajectories, alter plot-ready values, change bootstrap settings, remove cells, recalibrate Alibaba, or modify manuscript LaTeX.
