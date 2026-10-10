from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

from paper_figures.scripts.paper_common import COLORS, METHOD_ORDER, load_csv, save, style


DISPLAY = {
    "RAVM-DT": "RAVM-DT",
    "Always-FT": "Always-FT",
    "ER": "ER",
    "EWC": "EWC",
    "Huber-FT": "Huber-FT",
    "ValidationCommit": "Val.-Commit",
    "Frozen": "Frozen",
}


def main() -> None:
    style()
    data = load_csv("fig2_overall_baseline.csv")
    panels = [
        ("lifecycle_mse", "Lifecycle MSE", "Lifecycle MSE ($\\times10^{-3}$)", 1e3, 3),
        ("harmful_commit_rate", "Harmful-transition frequency", "Harmful transitions (%)", 100, 1),
        ("average_downside", "Harmful-transition downside", "Average downside ($\\times10^{-5}$)", 1e5, 2),
        ("commit_rate", "Commit rate", "Commit rate (%)", 100, 1),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(7.25, 4.65))
    fig.subplots_adjust(left=0.175, right=0.985, bottom=0.09, top=0.845, wspace=0.55, hspace=0.58)
    y = np.arange(len(METHOD_ORDER))

    for i, (ax, (metric, title, xlabel, scale, decimals)) in enumerate(zip(axes.flat, panels)):
        frame = data[data.metric == metric].set_index("method").loc[METHOD_ORDER]
        values = frame.estimate.to_numpy(float) * scale
        lo = frame.ci_low.to_numpy(float) * scale
        hi = frame.ci_high.to_numpy(float) * scale
        colors = [COLORS[m] for m in METHOD_ORDER]
        bars = ax.barh(y, values, height=0.62, color=colors, edgecolor="#5D5D5D", linewidth=0.5, zorder=2)
        bars[0].set_hatch("//")
        bars[0].set_linewidth(0.9)
        bars[0].set_edgecolor("#3F668D")
        ax.errorbar(values, y, xerr=np.vstack([values - lo, hi - values]), fmt="none", ecolor="#3F3F3F", elinewidth=0.68, capsize=1.9, capthick=0.68, zorder=3)
        finite_high = hi[np.isfinite(hi)]
        upper = max(float(finite_high.max()), float(values.max()))
        upper = upper * 1.28 if upper > 0 else 1.0
        ax.set_xlim(0, upper)
        offset = upper * 0.018
        for yy, value in enumerate(values):
            ax.text(max(value, hi[yy]) + offset, yy, f"{value:.{decimals}f}", va="center", ha="left", fontsize=6.4, fontweight="bold" if yy == 0 else "normal", color="#222222", clip_on=True)
        ax.set_yticks(y, [DISPLAY[m] for m in METHOD_ORDER])
        ax.invert_yaxis()
        for tick in ax.get_yticklabels():
            if tick.get_text() == "RAVM-DT":
                tick.set_fontweight("bold")
        ax.set_xlabel(xlabel, labelpad=4)
        ax.set_title(f"({chr(97 + i)}) {title}", pad=5)
        ax.xaxis.grid(True, color="#D7D7D7", linewidth=0.5, linestyle=(0, (1.5, 2.2)), zorder=0)
        ax.yaxis.grid(False)
        ax.tick_params(direction="out", length=3.5, width=0.7, pad=2)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    handles = [Patch(facecolor=COLORS[m], edgecolor="#5D5D5D", linewidth=0.5, hatch="//" if m == "RAVM-DT" else "", label=DISPLAY[m]) for m in METHOD_ORDER]
    fig.legend(handles=handles, ncol=4, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 0.99), handlelength=1.3, columnspacing=1.25)
    save(fig, "fig2_overall_baseline")


if __name__ == "__main__":
    main()
