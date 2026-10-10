from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

from paper_figures.scripts.paper_common import SCENARIO_COLORS, load_csv, save, style


SERIES = ["Mixed", "Persistent bias", "Replay"]
ALPHAS = [0.05, 0.10, 0.20]
HATCHES = {"Mixed": "", "Persistent bias": "//", "Replay": ".."}


def main() -> None:
    style()
    data = load_csv("fig3_corruption_severity.csv")
    panels = [
        ("lifecycle_mse", "Lifecycle MSE", "Lifecycle MSE ($\\times10^{-3}$)", 1e3),
        ("harmful_commit_rate", "Harmful-transition frequency", "Harmful transitions (%)", 100),
        ("average_downside", "Harmful-transition downside", "Average downside ($\\times10^{-5}$)", 1e5),
        ("commit_rate", "Commit rate", "Commit rate (%)", 100),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(7.25, 4.55))
    fig.subplots_adjust(left=0.085, right=0.985, bottom=0.115, top=0.88, wspace=0.34, hspace=0.52)
    x = np.arange(len(ALPHAS))
    width = 0.23

    for i, (ax, (metric, title, ylabel, scale)) in enumerate(zip(axes.flat, panels)):
        for j, series in enumerate(SERIES):
            rows = data[data.series == series].set_index("alpha").loc[ALPHAS]
            values = rows[metric].to_numpy(float) * scale
            lo = rows[f"{metric}_ci_low"].to_numpy(float) * scale
            hi = rows[f"{metric}_ci_high"].to_numpy(float) * scale
            pos = x + (j - 1) * width
            ax.bar(pos, values, width=width * 0.9, color=SCENARIO_COLORS[series], edgecolor="#5D5D5D", linewidth=0.5, hatch=HATCHES[series], zorder=2)
            ax.errorbar(pos, values, yerr=np.vstack([values - lo, hi - values]), fmt="none", ecolor="#3F3F3F", elinewidth=0.65, capsize=1.8, capthick=0.65, zorder=3)
        if metric == "harmful_commit_rate":
            ax.axhline(5.0, color="#666666", lw=0.7, linestyle=(0, (3, 2)), zorder=1)
            ax.text(0.03, 5.0, "Synthetic calibration criterion", transform=ax.get_yaxis_transform(), ha="left", va="bottom", fontsize=6.1, color="#555555")
        ax.set_xticks(x, [f"{alpha:.2f}" for alpha in ALPHAS])
        ax.set_xlabel("Corruption fraction $\\alpha$")
        ax.set_ylabel(ylabel)
        ax.set_title(f"({chr(97 + i)}) {title}", pad=5)
        ax.set_ylim(bottom=0)
        ax.yaxis.grid(True, color="#D7D7D7", linewidth=0.5, linestyle=(0, (1.5, 2.2)), zorder=0)
        ax.xaxis.grid(False)
        ax.tick_params(direction="out", length=3.5, width=0.7)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    handles = [Patch(facecolor=SCENARIO_COLORS[s], edgecolor="#5D5D5D", linewidth=0.5, hatch=HATCHES[s], label=s) for s in SERIES]
    fig.legend(handles=handles, ncol=3, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 0.985), handlelength=1.3, columnspacing=1.5)
    save(fig, "fig3_corruption_severity")


if __name__ == "__main__":
    main()
