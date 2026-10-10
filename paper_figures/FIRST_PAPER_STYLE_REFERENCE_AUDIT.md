# First-Paper Style Reference Audit

## Resolution

**PASS.** The user-supplied PDFs match the current local repository for *Adaptation-Aware Model Selection for Few-Shot Digital Twin Instantiation under Deployment Limits*. The repository contains maintained plotting code and final plot-ready assets, so no external repository lookup was needed and no ambiguous older candidate was selected.

## Authoritative references

- Main manuscript PDF: `C:\Users\92487\Desktop\JNCA新论文\初稿.pdf`
- Supplementary-material PDF: `C:\Users\92487\Desktop\JNCA新论文\补充.pdf`
- Current first-paper repository: `D:\dt-talk\repository`
- Main baseline plotting source: `D:\dt-talk\repository\reporting\overall_performance.py`
- Maintained Fig. 6--12 plotting source: `D:\dt-talk\repository\reporting\final_figures.py`
- Reproduction entrypoints: `D:\dt-talk\repository\scripts\generate_paper_outputs.py`, `derive_reproducible_figure_data.py`, and `plot_reproducible_figures.py`
- Reproduction documentation: `D:\dt-talk\repository\docs\FIGURE_REPRODUCTION.md`
- Current raster/vector assets: `D:\dt-talk\repository\outputs\paper_outputs\figures`

The visual inspection used main-paper Fig. 5 and Supplementary Figs. S1--S4. The first paper is used only as a style reference; no value from it enters any RAVM-DT scientific estimate.

## Extracted visual system

| Property | Verified first-paper treatment | RAVM-DT adaptation |
|---|---|---|
| Font | Current maintained figures use DejaVu Serif, Tinos, then Times New Roman fallback; the accepted baseline script uses DejaVu Sans for its older fixed layout | DejaVu Serif/Tinos/Times New Roman hierarchy, matching the current maintained figure system |
| Base sizes | 9 pt base/axes/title, 8 pt ticks, 7.7 pt legend in `final_figures.py`; compact 8/8.5/7.5 pt hierarchy in the baseline panel | 8 pt base, 8.5 pt axes/title, 7.2 pt ticks, 7 pt legend |
| Axes | 0.8 pt spines, outward ticks, white background | 0.8 pt axes; top/right removed where they do not carry information |
| Grid | Very light gray dotted grid, about 0.45--0.55 pt | `#D7D7D7`, 0.5 pt, short dotted pattern |
| Error bars | Thin strokes, small caps, open markers where useful | 0.60--0.75 pt, caps about 1.6--2.0 pt |
| Baseline bars | Horizontal, compact height 0.68, thin dark-gray edge, values at bar ends, “ours” bold and hatched | Fig. 2 uses height 0.62, thin edge, end labels, bold/hatched RAVM-DT |
| Stacked outcomes | Blue beneficial/non-harmful, rust harmful, light gray retained; numbers centered in sufficiently wide segments | Same semantic order and low-saturation mapping in Fig. 5(c) |
| Scatter | Open/filled markers, restrained edges, sparse labels, light reference grid | Open architecture markers, horizon encoded by shape, no connecting or fitted lines |
| Multi-panel layout | Compact full-width canvases with shared legends and consistent panel captions | Shared legends and matched panel geometry; chart grammar changes with the scientific question |

## Palette

The categorical colors are taken from the first-paper main baseline source:

- `#6E8FB3` muted blue
- `#8DB8B0` muted teal
- `#C6C2BD` light gray
- `#D9A25F` muted orange
- `#C77979` muted rust
- `#B39BBC` muted mauve
- `#8F99A6` blue-gray

RAVM-DT uses muted blue as the principal color. Always-FT uses muted orange, ER muted teal, EWC muted mauve, ValidationCommit blue-gray, and Frozen light gray. Condition panels use condition colors rather than method colors. RAVM-DT is emphasized through weight, edge, or hatch rather than saturation.

## Figure-specific observations

- Main Fig. 5: 2x2 horizontal bars, identical method order, compact legends, value labels, light x-grid, and restrained “ours” emphasis.
- Supplementary Fig. S1: horizontal 100% outcome logic, blue/rust/gray semantics, centered counts, and a compact category legend.
- Supplementary Fig. S2: marker area and shape encode distinct quantities; annotations are sparse and whitespace is deliberate.
- Supplementary Fig. S3: sensitivity panels use light grids, small open markers, thin reference lines, and consistent axes.
- Supplementary Fig. S4: confidence bands/error bars and distributions remain visually subordinate to estimates; the multi-panel layout stays compact.

## Boundary

Only visual properties were transferred. RAVM-DT plot-ready CSVs, aggregation, paired center-cluster bootstrap, frozen method definitions, and scientific conclusions remain unchanged.
