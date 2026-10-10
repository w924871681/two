from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

from paper_figures.scripts.paper_common import COLORS, MECHANISM_COLORS, clean_axes, load_csv, panel_label, point_range, save, style


def main() -> None:
    style()
    fig, axes = plt.subplots(1, 3, figsize=(7.45, 2.95), gridspec_kw={"width_ratios": [1.16, 1.02, 1.28]})
    fig.subplots_adjust(left=0.13, right=0.99, bottom=0.19, top=0.78, wspace=0.62)

    a = load_csv("fig5a_candidate_complexity.csv")
    order = [
        ("Block consensus - SinglePath", "Clean"),
        ("Block consensus - SinglePath", "Mixed"),
        ("Trimmed aggregation - Mean", "Clean"),
        ("Trimmed aggregation - Mean", "Mixed"),
    ]
    labels = ["Block vs single\n(clean)", "Block vs single\n(mixed)", "Trimmed vs mean\n(clean)", "Trimmed vs mean\n(mixed)"]
    for y, (key, condition) in enumerate(order):
        row = a[(a.comparison == key) & (a.condition == condition)].iloc[0]
        color, marker = (COLORS["RAVM-DT"], "o") if condition == "Clean" else (COLORS["Always-FT"], "s")
        point_range(axes[0], row.difference * 1e3, y, row.ci_low * 1e3, row.ci_high * 1e3, color, marker, horizontal=True)
    axes[0].axvline(0, color="#666666", lw=0.7, ls=(0, (3, 2)))
    axes[0].set_yticks(range(4), labels)
    axes[0].invert_yaxis()
    axes[0].set_xlabel("$\\Delta$ lifecycle MSE ($\\times10^{-3}$)\ncomplex variant $-$ simpler reference")

    b = load_csv("fig5b_temporal_tradeoff.csv")
    specs = {
        "Recent only": (MECHANISM_COLORS["aggressive"], "^", (6, 5)),
        "Long history": (MECHANISM_COLORS["conservative"], "s", (6, -12)),
        "Bounded history": (MECHANISM_COLORS["proposed"], "o", (-72, -13)),
    }
    for label, (color, marker, offset) in specs.items():
        row = b[b.label == label].iloc[0]
        x, y = row.balanced_lifecycle_mse * 1e3, row.mixed_harmful_commit_rate * 100
        axes[1].errorbar(
            x,
            y,
            xerr=[[x - row.balanced_lifecycle_mse_ci_low * 1e3], [row.balanced_lifecycle_mse_ci_high * 1e3 - x]],
            yerr=[[y - row.mixed_harmful_commit_rate_ci_low * 100], [row.mixed_harmful_commit_rate_ci_high * 100 - y]],
            fmt=marker,
            mfc="white",
            mec=color,
            mew=1.0,
            ecolor=color,
            elinewidth=0.75,
            capsize=2,
            ms=4.5,
        )
        axes[1].annotate(label, (x, y), xytext=offset, textcoords="offset points", fontsize=6.4, color=color)
    axes[1].set_xlabel("Balanced lifecycle MSE ($\\times10^{-3}$)")
    axes[1].set_ylabel("Mixed harmful transitions (%)")
    axes[1].set_ylim(bottom=0)

    c = load_csv("fig5c_selective_commit.csv")
    order = [("Clean", "Selective commit"), ("Clean", "Always commit"), ("Mixed", "Selective commit"), ("Mixed", "Always commit")]
    labels = ["Clean · selective", "Clean · always", "Mixed · selective", "Mixed · always"]
    segment_cols = {
        "harmful_committed": MECHANISM_COLORS["harmful"],
        "non_harmful_committed": MECHANISM_COLORS["proposed"],
        "retained": MECHANISM_COLORS["retained"],
    }
    y = np.arange(len(order))
    for j, (condition, method) in enumerate(order):
        row = c[(c.condition == condition) & (c.method == method)].iloc[0]
        left = 0.0
        for key in ["harmful_committed", "non_harmful_committed", "retained"]:
            value = float(row[key]) * 100
            axes[2].barh(j, value, left=left, height=0.52, color=segment_cols[key], edgecolor="#F7F7F7", linewidth=0.55)
            if value >= 10:
                axes[2].text(left + value / 2, j, f"{value:.0f}", ha="center", va="center", fontsize=6.1, color="white" if key != "retained" else "#333333")
            left += value
    axes[2].set_yticks(y, labels)
    axes[2].invert_yaxis()
    axes[2].set_xlim(0, 100)
    axes[2].set_xlabel("Outcome share (%)")
    axes[2].legend(
        handles=[Patch(facecolor=segment_cols[k], edgecolor="white", label=l) for k, l in [("harmful_committed", "Harmful committed"), ("non_harmful_committed", "Non-harmful committed"), ("retained", "Retained")]],
        frameon=False,
        loc="lower center",
        bbox_to_anchor=(0.5, 1.01),
        fontsize=6.0,
        ncol=1,
        handlelength=1.0,
    )

    for i, ax in enumerate(axes):
        clean_axes(ax)
        ax.grid(axis="x", color="#D7D7D7", linewidth=0.5, alpha=0.65, linestyle=(0, (1.5, 2.2)))
        ax.grid(axis="y", visible=False)
        panel_label(ax, f"({chr(97 + i)})")
    save(fig, "fig5_mechanism_analysis")


if __name__ == "__main__":
    main()
