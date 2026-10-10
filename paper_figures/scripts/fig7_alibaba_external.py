from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

from paper_figures.scripts.paper_common import load_csv, save, style


METHODS = ["RAVM-DT", "Always-FT", "ER", "Huber-FT", "Frozen"]
CONDITION_STYLE = {
    "Clean": {"facecolor": "#E7EDF1", "edgecolor": "#8193A0"},
    "Mixed": {"facecolor": "#6E8FB3", "edgecolor": "#4F6F90"},
}


def main() -> None:
    style()
    data = load_csv("fig7_alibaba_external.csv")
    panels = [
        ("lifecycle_mse", "Lifecycle MSE", "Lifecycle MSE ($\\times10^{-3}$)", 1e3),
        ("harmful_commit_rate", "Harmful-transition frequency", "Harmful transitions (%)", 100),
        ("average_downside", "Harmful-transition downside", "Average downside ($\\times10^{-5}$)", 1e5),
        ("commit_rate", "Commit rate", "Commit rate (%)", 100),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(7.25, 4.65))
    fig.subplots_adjust(left=0.145, right=0.985, bottom=0.11, top=0.90, wspace=0.42, hspace=0.50)
    y = np.arange(len(METHODS))
    height = 0.31

    for i, (ax, (metric, title, xlabel, scale)) in enumerate(zip(axes.flat, panels)):
        for condition, offset in [("Clean", -height / 2), ("Mixed", height / 2)]:
            rows = data[data.condition == condition].set_index("method").loc[METHODS]
            values = rows[metric].to_numpy(float) * scale
            lo = rows[f"{metric}_ci_low"].to_numpy(float) * scale
            hi = rows[f"{metric}_ci_high"].to_numpy(float) * scale
            style_args = CONDITION_STYLE[condition]
            for j, method in enumerate(METHODS):
                is_ravm = method == "RAVM-DT"
                ax.barh(
                    j + offset,
                    values[j],
                    height=height * 0.86,
                    color=style_args["facecolor"],
                    edgecolor="#2F526F" if is_ravm else style_args["edgecolor"],
                    linewidth=1.0 if is_ravm else 0.55,
                    hatch="//" if is_ravm and condition == "Clean" else "",
                    zorder=2,
                )
                ax.errorbar(values[j], j + offset, xerr=[[values[j] - lo[j]], [hi[j] - values[j]]], fmt="none", ecolor="#3F3F3F", elinewidth=0.62, capsize=1.7, capthick=0.62, zorder=3)
        if metric == "harmful_commit_rate":
            ax.axvline(5.0, color="#666666", lw=0.7, ls=(0, (3, 2)), zorder=1)
            ax.text(5.15, 0.98, "Synthetic-domain calibration criterion", transform=ax.get_xaxis_transform(), va="top", ha="left", fontsize=5.9, color="#555555")
        ax.set_yticks(y, METHODS)
        ax.invert_yaxis()
        for tick in ax.get_yticklabels():
            if tick.get_text() == "RAVM-DT":
                tick.set_fontweight("bold")
        ax.set_xlabel(xlabel)
        ax.set_title(f"({chr(97 + i)}) {title}", pad=5)
        ax.set_xlim(left=0)
        ax.xaxis.grid(True, color="#D7D7D7", linewidth=0.5, alpha=0.65, linestyle=(0, (1.5, 2.2)), zorder=0)
        ax.yaxis.grid(False)
        ax.tick_params(direction="out", length=3.5, width=0.7)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    handles = [
        Patch(facecolor=CONDITION_STYLE[c]["facecolor"], edgecolor=CONDITION_STYLE[c]["edgecolor"], linewidth=0.6, label=c)
        for c in ["Clean", "Mixed"]
    ]
    fig.legend(handles=handles, frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, 0.985), handlelength=1.3, columnspacing=1.4)
    save(fig, "fig7_alibaba_external")


if __name__ == "__main__":
    main()
