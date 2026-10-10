from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

from paper_figures.scripts.paper_common import COLORS, load_csv, save, style


KAPPAS = [0.0, 0.5, 1.0, 1.5]
ARCH_COLORS = {"MLP": COLORS["RAVM-DT"], "TCN": COLORS["ER"], "GRU": COLORS["Always-FT"]}
H_MARKERS = {1: "o", 4: "s"}


def draw_heatmap(fig, ax, data, column, title, cmap, scale, fmt, colorbar_label):
    matrix = np.empty((4, 4))
    selected = None
    for r, kr in enumerate(KAPPAS):
        for c, kh in enumerate(KAPPAS):
            row = data[np.isclose(data.kappa_rec, kr) & np.isclose(data.kappa_hist, kh)]
            if len(row) != 1:
                raise RuntimeError(f"missing/duplicate kappa cell: {kr}/{kh}")
            matrix[r, c] = float(row.iloc[0][column]) * scale
            if bool(row.iloc[0].selected):
                selected = (r, c)
    observed_min, observed_max = float(matrix.min()), float(matrix.max())
    span = max(observed_max - observed_min, abs(observed_max) * 0.02, 1e-12)
    margin = span * 0.06
    vmin, vmax = observed_min - margin, observed_max + margin
    image = ax.pcolormesh(
        np.arange(5) - 0.5,
        np.arange(5) - 0.5,
        matrix,
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        shading="flat",
        edgecolors="none",
    )
    ax.set_xlim(-0.5, 3.5)
    ax.set_ylim(3.5, -0.5)
    ax.set_aspect("equal", adjustable="box")
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    for r in range(4):
        for c in range(4):
            value = matrix[r, c]
            ax.text(c, r, format(value, fmt), ha="center", va="center", fontsize=6.2, color="white" if norm(value) > 0.63 else "#222222")
    if selected is None:
        raise RuntimeError("frozen kappa cell missing")
    r, c = selected
    ax.add_patch(Rectangle((c - 0.47, r - 0.47), 0.94, 0.94, fill=False, edgecolor="#2F526F", linewidth=1.35))
    ax.text(0.5, -0.29, f"Observed: {observed_min:.2f}–{observed_max:.2f} {colorbar_label}; outline: Frozen setting", transform=ax.transAxes, ha="center", va="top", fontsize=5.7, color="#475E73")
    ax.set_xticks(range(4), [f"{v:g}" for v in KAPPAS])
    ax.set_yticks(range(4), [f"{v:g}" for v in KAPPAS])
    ax.set_xlabel("$\\kappa_{hist}$")
    ax.set_ylabel("$\\kappa_{rec}$")
    ax.set_title(title, pad=4)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)


def draw_effect_panel(ax, data, scenario, title):
    subset = data[data.scenario == scenario]
    if len(subset) != 6:
        raise RuntimeError(f"{scenario} generality panel requires six cells, found {len(subset)}")
    for row in subset.itertuples():
        x = row.delta_lifecycle_mse * 1e3
        y = row.delta_harmful_commit_rate * 100
        color = ARCH_COLORS[row.architecture]
        marker = H_MARKERS[int(row.horizon)]
        ax.errorbar(
            x,
            y,
            xerr=[[x - row.delta_lifecycle_mse_ci_low * 1e3], [row.delta_lifecycle_mse_ci_high * 1e3 - x]],
            yerr=[[y - row.delta_harmful_commit_rate_ci_low * 100], [row.delta_harmful_commit_rate_ci_high * 100 - y]],
            fmt=marker,
            ms=4.5,
            mfc="white",
            mec=color,
            mew=0.95,
            ecolor=color,
            elinewidth=0.6,
            capsize=1.6,
            alpha=0.95,
            zorder=3,
        )
    ax.axvline(0, color="#666666", lw=0.65, ls=(0, (3, 2)), zorder=0)
    ax.axhline(0, color="#666666", lw=0.65, ls=(0, (3, 2)), zorder=0)
    ax.set_xlabel("$\\Delta$ lifecycle MSE ($\\times10^{-3}$)")
    ax.set_ylabel("$\\Delta$ harmful transitions (pp)")
    ax.set_title(title, pad=4)
    ax.grid(color="#D7D7D7", linewidth=0.5, alpha=0.65, linestyle=(0, (1.5, 2.2)))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def main() -> None:
    style()
    fig, axes = plt.subplots(2, 2, figsize=(7.35, 4.75))
    fig.subplots_adjust(left=0.09, right=0.985, bottom=0.14, top=0.93, wspace=0.34, hspace=0.62)
    grid = load_csv("fig6a_kappa_frontier.csv")
    draw_heatmap(fig, axes[0, 0], grid, "balanced_mse", "(a) Balanced lifecycle MSE", "Blues", 1e3, ".3f", "$\\times10^{-3}$")
    draw_heatmap(fig, axes[0, 1], grid, "mixed_harmful", "(b) Mixed harmful-transition frequency", "Oranges", 100, ".1f", "%")

    effects = load_csv("fig6c_generality_effect_scatter.csv")
    draw_effect_panel(axes[1, 0], effects, "clean", "(c) Clean generality")
    draw_effect_panel(axes[1, 1], effects, "mixed_a010_both", "(d) Mixed generality")

    architecture_handles = [Line2D([], [], marker="o", ls="none", mfc="white", mec=color, mew=0.95, label=architecture) for architecture, color in ARCH_COLORS.items()]
    horizon_handles = [
        Line2D([], [], marker="o", ls="none", mfc="white", mec="#555555", label="H=1"),
        Line2D([], [], marker="s", ls="none", mfc="white", mec="#555555", label="H=4"),
    ]
    fig.legend(handles=architecture_handles + horizon_handles, ncol=5, frameon=False, loc="lower center", bbox_to_anchor=(0.5, 0.015), handletextpad=0.35, columnspacing=1.15)
    save(fig, "fig6_sensitivity_generality")


if __name__ == "__main__":
    main()
