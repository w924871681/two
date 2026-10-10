from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import matplotlib.pyplot as plt
import numpy as np

from paper_figures.scripts.paper_common import COLORS, MARKERS, clean_axes, load_csv, panel_label, point_range, save, style


REGIMES = ["stationary", "gradual", "abrupt", "recurring"]
LABELS = ["Stationary", "Gradual", "Abrupt", "Recurring"]


def main() -> None:
    style()
    data = load_csv("fig4_benign_evolution.csv")
    fig, axes = plt.subplots(1, 2, figsize=(7.25, 2.85))
    fig.subplots_adjust(left=0.105, right=0.985, bottom=0.18, top=0.80, wspace=0.32)
    y = np.arange(len(REGIMES))

    panel = axes[0]
    frames = {m: data[data.method == m].set_index("scenario").loc[REGIMES] for m in ["Always-FT", "RAVM-DT", "Frozen"]}
    for j in range(len(REGIMES)):
        anchors = [frames[m].iloc[j].lifecycle_mse * 1e3 for m in ["Always-FT", "RAVM-DT", "Frozen"]]
        panel.plot([min(anchors), max(anchors)], [j, j], color="#D9D9D9", lw=0.7, zorder=1)
    offsets = {"Always-FT": -0.12, "RAVM-DT": 0.0, "Frozen": 0.12}
    for method in ["Always-FT", "RAVM-DT", "Frozen"]:
        frame = frames[method]
        for j, row in enumerate(frame.itertuples()):
            point_range(panel, row.lifecycle_mse * 1e3, j + offsets[method], row.lifecycle_mse_ci_low * 1e3, row.lifecycle_mse_ci_high * 1e3, COLORS[method], MARKERS[method], horizontal=True, zorder=4 if method == "RAVM-DT" else 3)
        panel.plot([], [], marker=MARKERS[method], mfc="white", mec=COLORS[method], mew=0.9, ls="none", label=method)
    panel.set_yticks(y, LABELS)
    panel.invert_yaxis()
    panel.set_xlabel("Lifecycle MSE ($\\times10^{-3}$)")
    panel.legend(frameon=False, ncol=3, loc="lower center", bbox_to_anchor=(0.5, 1.015), columnspacing=0.9, handletextpad=0.35)

    panel = axes[1]
    ravm = frames["RAVM-DT"]
    for j, row in enumerate(ravm.itertuples()):
        commit = row.commit_rate * 100
        recall = row.beneficial_commit_recall * 100
        panel.plot([commit, recall], [j, j], color="#D4D4D4", lw=0.75, zorder=1)
        point_range(panel, commit, j, row.commit_rate_ci_low * 100, row.commit_rate_ci_high * 100, COLORS["RAVM-DT"], "o", horizontal=True, zorder=3)
        point_range(panel, recall, j, row.beneficial_commit_recall_ci_low * 100, row.beneficial_commit_recall_ci_high * 100, COLORS["Always-FT"], "s", horizontal=True, zorder=3)
    panel.plot([], [], marker="o", mfc="white", mec=COLORS["RAVM-DT"], ls="none", label="Commit rate")
    panel.plot([], [], marker="s", mfc="white", mec=COLORS["Always-FT"], ls="none", label="Beneficial-commit recall")
    panel.set_yticks(y, LABELS)
    panel.invert_yaxis()
    panel.set_xlim(left=0)
    panel.set_xlabel("Rate (%)")
    panel.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=2, columnspacing=0.9, handletextpad=0.35)

    for i, ax in enumerate(axes):
        clean_axes(ax)
        ax.grid(axis="x", color="#D7D7D7", linewidth=0.5, alpha=0.65, linestyle=(0, (1.5, 2.2)))
        ax.grid(axis="y", visible=False)
        panel_label(ax, f"({chr(97 + i)})")
    save(fig, "fig4_benign_evolution")


if __name__ == "__main__":
    main()
